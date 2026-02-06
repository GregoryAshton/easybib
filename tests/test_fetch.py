"""Tests for easybib.core network functions (mocked)."""

from unittest.mock import MagicMock, patch

from easybib.core import (
    fetch_bibtex,
    get_ads_bibtex,
    get_ads_info_from_inspire,
    get_inspire_bibtex,
    search_ads_by_arxiv,
)

SAMPLE_BIBTEX = "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}"


# --- get_inspire_bibtex ---


class TestGetInspireBibtex:
    @patch("easybib.core.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text=SAMPLE_BIBTEX)
        result = get_inspire_bibtex("Author:2020abc")
        assert result == SAMPLE_BIBTEX.strip()

    @patch("easybib.core.requests.get")
    def test_empty_response(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text="   ")
        result = get_inspire_bibtex("Author:2020abc")
        assert result is None

    @patch("easybib.core.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404, text="")
        result = get_inspire_bibtex("Author:2020abc")
        assert result is None


# --- get_ads_bibtex ---


class TestGetAdsBibtex:
    @patch("easybib.core.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"export": SAMPLE_BIBTEX}),
        )
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result == SAMPLE_BIBTEX.strip()

    @patch("easybib.core.requests.post")
    def test_no_records(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"export": "No records found"}),
        )
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result is None

    @patch("easybib.core.requests.post")
    def test_non_200(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500)
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result is None


# --- get_ads_info_from_inspire ---


class TestGetAdsInfoFromInspire:
    @patch("easybib.core.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "hits": {
                        "hits": [
                            {
                                "metadata": {
                                    "external_system_identifiers": [
                                        {"schema": "ADS", "value": "2020ApJ...000..000A"}
                                    ],
                                    "arxiv_eprints": [{"value": "2001.12345"}],
                                }
                            }
                        ]
                    }
                }
            ),
        )
        bibcode, arxiv_id = get_ads_info_from_inspire("Author:2020abc")
        assert bibcode == "2020ApJ...000..000A"
        assert arxiv_id == "2001.12345"

    @patch("easybib.core.requests.get")
    def test_no_hits(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"hits": {"hits": []}}),
        )
        bibcode, arxiv_id = get_ads_info_from_inspire("Author:2020abc")
        assert bibcode is None
        assert arxiv_id is None

    @patch("easybib.core.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        bibcode, arxiv_id = get_ads_info_from_inspire("Author:2020abc")
        assert bibcode is None
        assert arxiv_id is None


# --- search_ads_by_arxiv ---


class TestSearchAdsByArxiv:
    @patch("easybib.core.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "response": {"docs": [{"bibcode": "2020ApJ...000..000A"}]}
                }
            ),
        )
        result = search_ads_by_arxiv("2001.12345", "fake-key")
        assert result == "2020ApJ...000..000A"

    @patch("easybib.core.requests.get")
    def test_empty_docs(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": {"docs": []}}),
        )
        result = search_ads_by_arxiv("2001.12345", "fake-key")
        assert result is None

    @patch("easybib.core.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=403)
        result = search_ads_by_arxiv("2001.12345", "fake-key")
        assert result is None


# --- fetch_bibtex (source routing) ---


class TestFetchBibtex:
    @patch("easybib.core.get_inspire_bibtex")
    @patch("easybib.core.get_ads_bibtex")
    @patch("easybib.core.get_ads_info_from_inspire")
    def test_ads_source(self, mock_info, mock_ads, mock_inspire):
        """With source='ads', ADS path is tried (via INSPIRE cross-ref)."""
        mock_info.return_value = ("2020ApJ...000..000A", None)
        mock_ads.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="ads")
        assert result == SAMPLE_BIBTEX
        assert "ADS" in source

    @patch("easybib.core.get_inspire_bibtex")
    def test_inspire_source(self, mock_inspire):
        """With source='inspire', INSPIRE is tried first."""
        mock_inspire.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="inspire")
        assert result == SAMPLE_BIBTEX
        assert "INSPIRE" in source

    @patch("easybib.core.get_inspire_bibtex")
    def test_auto_source_inspire_key(self, mock_inspire):
        """With source='auto' and an INSPIRE-style key, INSPIRE is tried first."""
        mock_inspire.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="auto")
        assert result == SAMPLE_BIBTEX
        assert "INSPIRE" in source

    @patch("easybib.core.get_ads_bibtex")
    def test_auto_source_ads_bibcode(self, mock_ads):
        """With source='auto' and an ADS-style key, ADS is tried first."""
        mock_ads.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex(
            "2016PhRvL.116f1102A", "fake-key", source="auto"
        )
        assert result == SAMPLE_BIBTEX
        assert "ADS" in source

    @patch("easybib.core.get_inspire_bibtex")
    @patch("easybib.core.get_ads_bibtex")
    @patch("easybib.core.get_ads_info_from_inspire")
    @patch("easybib.core.search_ads_by_arxiv")
    def test_not_found(self, mock_search, mock_info, mock_ads, mock_inspire):
        """When nothing is found, returns (None, None)."""
        mock_inspire.return_value = None
        mock_ads.return_value = None
        mock_info.return_value = (None, None)
        mock_search.return_value = None
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="ads")
        assert result is None
        assert source is None
