"""easybib - Automatically fetch BibTeX entries from INSPIRE and ADS for LaTeX projects."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("easybib")
except PackageNotFoundError:
    __version__ = "unknown"

from easybib.api import (
    fetch_bibtex,
    fetch_bibtex_by_arxiv,
    get_ads_bibtex,
    get_inspire_bibtex,
    get_inspire_bibtex_by_arxiv,
    get_semantic_scholar_bibtex,
)
from easybib.conversions import (
    extract_bibtex_fields,
    extract_bibtex_key,
    make_arxiv_crossref_stub,
    replace_bibtex_key,
    truncate_authors,
)
from easybib.core import (
    extract_cite_keys,
    extract_existing_bib_keys,
    is_ads_bibcode,
    is_arxiv_id,
    is_inspire_key,
)

__all__ = [
    "extract_bibtex_fields",
    "extract_bibtex_key",
    "extract_cite_keys",
    "extract_existing_bib_keys",
    "fetch_bibtex",
    "fetch_bibtex_by_arxiv",
    "get_ads_bibtex",
    "get_inspire_bibtex",
    "get_inspire_bibtex_by_arxiv",
    "get_semantic_scholar_bibtex",
    "is_ads_bibcode",
    "is_arxiv_id",
    "is_inspire_key",
    "make_arxiv_crossref_stub",
    "replace_bibtex_key",
    "truncate_authors",
]
