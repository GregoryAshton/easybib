"""Integration tests that make real API calls.

Run with:
    pytest tests/test_integration.py -v -m integration
"""

import os

import pytest

from easybib.api import (
    fetch_bibtex,
    get_ads_bibtex,
    get_inspire_bibtex,
)

pytestmark = pytest.mark.integration


# --- INSPIRE ---


class TestInspireIntegration:
    def test_get_inspire_bibtex(self):
        result = get_inspire_bibtex("LIGOScientific:2025hdt")
        assert result is not None, "Expected BibTeX from INSPIRE, got None"
        assert result.startswith("@")
        assert "LIGOScientific:2025hdt" in result

    def test_fetch_bibtex_inspire_preferred(self):
        result, source = fetch_bibtex(
            "LIGOScientific:2025hdt", api_key=None, source="inspire"
        )
        assert result is not None, "Expected BibTeX from INSPIRE, got None"
        assert result.startswith("@")
        assert "INSPIRE" in source


# --- NASA/ADS ---


@pytest.fixture
def ads_api_key():
    key = os.getenv("ADS_API_KEY")
    if not key:
        pytest.skip("ADS_API_KEY not set")
    return key


class TestADSIntegration:
    def test_get_ads_bibtex(self, ads_api_key):
        result = get_ads_bibtex("2025ApJ...995L..18A", ads_api_key)
        assert result is not None, "Expected BibTeX from ADS, got None"
        assert result.startswith("@")
        assert "2025ApJ" in result

    def test_fetch_bibtex_ads_preferred(self, ads_api_key):
        result, source = fetch_bibtex(
            "2025ApJ...995L..18A", api_key=ads_api_key, source="ads"
        )
        assert result is not None, "Expected BibTeX from ADS, got None"
        assert result.startswith("@")
        assert "ADS" in source


# --- Semantic Scholar ---


class TestSemanticScholarIntegration:
    def test_fetch_bibtex_semantic_scholar_preferred(self):
        result, source = fetch_bibtex(
            "2508.18080", api_key=None, source="semantic-scholar"
        )
        assert result is not None, "Expected BibTeX from Semantic Scholar chain, got None"
        assert result.startswith("@")
        assert "Semantic Scholar" in source
