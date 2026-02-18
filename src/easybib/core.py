"""Core parsing and key detection for easybib."""

import re


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
            elif ":" not in key:
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
