"""API access functions for fetching BibTeX from INSPIRE and ADS."""

import requests

from easybib.core import is_ads_bibcode


def get_inspire_bibtex(key):
    """Fetch BibTeX directly from INSPIRE for a given INSPIRE key."""
    url = f"https://inspirehep.net/api/literature?q=texkeys:{key}"
    headers = {"Accept": "application/x-bibtex"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.text.strip():
        return response.text.strip()
    return None


def get_ads_info_from_inspire(key):
    """Fetch ADS bibcode and arXiv ID from INSPIRE for a given INSPIRE key.

    Returns a tuple of (ads_bibcode, arxiv_id), either may be None.
    """
    # Use texkeys field to avoid colon being interpreted as field operator
    url = f"https://inspirehep.net/api/literature?q=texkeys:{key}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    ads_bibcode = None
    arxiv_id = None

    if response.status_code == 200:
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        if hits:
            metadata = hits[0].get("metadata", {})

            # Try to get ADS bibcode
            external_ids = metadata.get("external_system_identifiers", [])
            for ext_id in external_ids:
                if ext_id.get("schema") == "ADS":
                    ads_bibcode = ext_id.get("value")
                    break

            # Get arXiv ID as fallback
            arxiv_eprints = metadata.get("arxiv_eprints", [])
            if arxiv_eprints:
                arxiv_id = arxiv_eprints[0].get("value")

    return ads_bibcode, arxiv_id


def search_ads_by_arxiv(arxiv_id, api_key):
    """Search ADS for a paper by arXiv ID and return its bibcode."""
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"q": f"arXiv:{arxiv_id}", "fl": "bibcode"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        docs = result.get("response", {}).get("docs", [])
        if docs:
            return docs[0].get("bibcode")
    return None


def get_ads_bibtex(bibcode, api_key):
    """Fetch BibTeX from ADS for a given bibcode."""
    url = "https://api.adsabs.harvard.edu/v1/export/bibtex"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"bibcode": [bibcode]}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        export = result.get("export", "").strip()
        if export and not export.startswith("No records"):
            return export
    return None


def fetch_bibtex_ads_preferred(key, api_key):
    """Fetch BibTeX preferring ADS, with INSPIRE as fallback."""
    # First check if it's already an ADS bibcode
    if is_ads_bibcode(key):
        bibtex = get_ads_bibtex(key, api_key)
        if bibtex:
            return bibtex, "ADS (direct)"

    # Try to get ADS bibcode or arXiv ID from INSPIRE
    ads_bibcode, arxiv_id = get_ads_info_from_inspire(key)

    # Try ADS bibcode first
    if ads_bibcode:
        bibtex = get_ads_bibtex(ads_bibcode, api_key)
        if bibtex:
            return bibtex, f"ADS via INSPIRE ({ads_bibcode})"

    # Fall back to arXiv ID search on ADS
    if arxiv_id:
        ads_bibcode = search_ads_by_arxiv(arxiv_id, api_key)
        if ads_bibcode:
            bibtex = get_ads_bibtex(ads_bibcode, api_key)
            if bibtex:
                return bibtex, f"ADS via arXiv ({arxiv_id})"

    # Try the key directly as ADS bibcode
    bibtex = get_ads_bibtex(key, api_key)
    if bibtex:
        return bibtex, "ADS (direct fallback)"

    # Final fallback: fetch BibTeX directly from INSPIRE
    bibtex = get_inspire_bibtex(key)
    if bibtex:
        return bibtex, "INSPIRE (fallback)"

    return None, None


def fetch_bibtex_inspire_preferred(key, api_key):
    """Fetch BibTeX preferring INSPIRE, with ADS as fallback."""
    # Try INSPIRE first
    bibtex = get_inspire_bibtex(key)
    if bibtex:
        return bibtex, "INSPIRE"

    # Fall back to ADS
    if is_ads_bibcode(key):
        bibtex = get_ads_bibtex(key, api_key)
        if bibtex:
            return bibtex, "ADS (fallback, direct)"

    # Try to get ADS bibcode from INSPIRE metadata
    ads_bibcode, arxiv_id = get_ads_info_from_inspire(key)
    if ads_bibcode:
        bibtex = get_ads_bibtex(ads_bibcode, api_key)
        if bibtex:
            return bibtex, "ADS (fallback, via INSPIRE)"

    if arxiv_id:
        ads_bibcode = search_ads_by_arxiv(arxiv_id, api_key)
        if ads_bibcode:
            bibtex = get_ads_bibtex(ads_bibcode, api_key)
            if bibtex:
                return bibtex, "ADS (fallback, via arXiv)"

    return None, None


def fetch_bibtex_auto(key, api_key):
    """Fetch BibTeX using the source that matches the key format."""
    if is_ads_bibcode(key):
        # Key looks like ADS bibcode, prefer ADS
        bibtex = get_ads_bibtex(key, api_key)
        if bibtex:
            return bibtex, "ADS (auto)"
        # Fallback to INSPIRE
        bibtex = get_inspire_bibtex(key)
        if bibtex:
            return bibtex, "INSPIRE (fallback)"
    else:
        # Key looks like INSPIRE key, prefer INSPIRE
        bibtex = get_inspire_bibtex(key)
        if bibtex:
            return bibtex, "INSPIRE (auto)"
        # Fallback to ADS via INSPIRE cross-reference
        ads_bibcode, arxiv_id = get_ads_info_from_inspire(key)
        if ads_bibcode:
            bibtex = get_ads_bibtex(ads_bibcode, api_key)
            if bibtex:
                return bibtex, "ADS (fallback, via INSPIRE)"
        if arxiv_id:
            ads_bibcode = search_ads_by_arxiv(arxiv_id, api_key)
            if ads_bibcode:
                bibtex = get_ads_bibtex(ads_bibcode, api_key)
                if bibtex:
                    return bibtex, "ADS (fallback, via arXiv)"

    return None, None


def fetch_bibtex(key, api_key, source="ads"):
    """Fetch BibTeX using the specified source preference."""
    if source == "ads":
        return fetch_bibtex_ads_preferred(key, api_key)
    elif source == "inspire":
        return fetch_bibtex_inspire_preferred(key, api_key)
    elif source == "auto":
        return fetch_bibtex_auto(key, api_key)
    else:
        return fetch_bibtex_ads_preferred(key, api_key)
