"""Core parsing and key detection for easybib."""

import re


def is_arxiv_id(key):
    """Check if a key looks like an arXiv ID (new format: 2508.18080, or old: hep-ph/9905318)."""
    return bool(re.match(r'^\d{4}\.\d{4,5}$', key)) or \
           bool(re.match(r'^[a-z][a-z0-9-]*/\d{7}$', key))


def extract_cite_keys(tex_file):
    """Extract all citation keys from a LaTeX file.

    Returns a tuple of (keys, warnings) where keys is a list of valid citation keys
    and warnings is a list of warning messages for invalid keys.
    """
    with open(tex_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Match all citation commands: \cite{}, \citep{}, \citet{}, \citealt{}, \citealp{},
    # \citeauthor{}, \citeyear{}, \Citep{}, \Citet{}, etc.
    # Also handles optional arguments like \citep[e.g.][]{key}
    pattern = r"\\[Cc]ite[a-zA-Z]*(?:\[[^\]]*\])*\{([^}]+)\}"
    matches = re.findall(pattern, content)
    # Split multiple keys in single cite command
    keys = []
    warnings = []
    for match in matches:
        for key in match.split(","):
            key = key.strip()
            if not key:
                warnings.append(f"{tex_file}: Empty citation key found")
            elif ":" not in key and not is_arxiv_id(key) and not is_ads_bibcode(key):
                warnings.append(f"{tex_file}: Skipping key '{key}' (not an INSPIRE/ADS key)")
            else:
                keys.append(key)
    return keys, warnings


def extract_existing_bib_keys(bib_file):
    """Extract citation keys from an existing BibTeX file."""
    if not bib_file.exists():
        return set()
    with open(bib_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Match @type{key,
    pattern = r"@\w+\s*\{\s*([^,\s]+)\s*,"
    return set(re.findall(pattern, content))


def is_ads_bibcode(key):
    """Check if a key looks like an ADS bibcode (e.g., 2016PhRvL.116f1102A)."""
    # ADS bibcodes are typically 19 characters: 4-digit year + journal code + volume + page + author initial
    # Pattern: YYYYJJJJJVVVVMPPPPA where Y=year, J=journal, V=volume, M=section, P=page, A=author
    ads_pattern = r"^\d{4}[A-Za-z&.]+\..*[A-Z]$"
    return bool(re.match(ads_pattern, key)) and len(key) >= 15


def is_inspire_key(key):
    """Check if a key looks like an INSPIRE texkey (e.g., Author:2020abc)."""
    # INSPIRE keys are typically Author:YYYYxxx where xxx is 2-3 lowercase letters
    inspire_pattern = r"^[A-Za-z][A-Za-z0-9-]+:\d{4}[a-z]{2,3}$"
    return bool(re.match(inspire_pattern, key))


def detect_key_type(key):
    """Detect the type of a citation key.

    Returns 'inspire', 'ads', 'arxiv', or 'unknown'.
    """
    if is_inspire_key(key):
        return "inspire"
    elif is_ads_bibcode(key):
        return "ads"
    elif is_arxiv_id(key):
        return "arxiv"
    return "unknown"


def check_key_type(keys, allowed_type):
    """Check that all keys match the allowed type.

    Returns a list of (key, detected_type) tuples for keys that do not match.
    allowed_type must be one of 'inspire', 'ads', or 'arxiv'.
    Raises ValueError for an unrecognised allowed_type.
    """
    checkers = {
        "inspire": is_inspire_key,
        "ads": is_ads_bibcode,
        "arxiv": is_arxiv_id,
    }
    if allowed_type not in checkers:
        raise ValueError(
            f"allowed_type must be one of {list(checkers)}, got {allowed_type!r}"
        )
    check_fn = checkers[allowed_type]
    return [(key, detect_key_type(key)) for key in keys if not check_fn(key)]
