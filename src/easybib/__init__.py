"""easybib - Automatically fetch BibTeX entries from INSPIRE and ADS for LaTeX projects."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("easybib")
except PackageNotFoundError:
    __version__ = "unknown"

from easybib.api import (
    fetch_bibtex,
    get_ads_bibtex,
    get_inspire_bibtex,
    get_semantic_scholar_bibtex,
)
from easybib.conversions import (
    replace_bibtex_key,
    truncate_authors,
)
from easybib.core import (
    extract_cite_keys,
    extract_existing_bib_keys,
    is_ads_bibcode,
    is_inspire_key,
)

__all__ = [
    "extract_cite_keys",
    "extract_existing_bib_keys",
    "fetch_bibtex",
    "get_ads_bibtex",
    "get_inspire_bibtex",
    "get_semantic_scholar_bibtex",
    "is_ads_bibcode",
    "is_inspire_key",
    "replace_bibtex_key",
    "truncate_authors",
]
