"""Tests for easybib.api network functions (mocked)."""

from unittest.mock import MagicMock, patch

from easybib.api import (
    fetch_bibtex,
    get_ads_bibtex,
    get_ads_info_from_inspire,
    get_arxiv_id_from_inspire,
    get_inspire_bibtex,
    get_semantic_scholar_bibtex,
    search_ads_by_arxiv,
)

SAMPLE_BIBTEX = "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}"


# --- get_inspire_bibtex ---


class TestGetInspireBibtex:
    @patch("easybib.api.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text=SAMPLE_BIBTEX)
        result = get_inspire_bibtex("Author:2020abc")
        assert result == SAMPLE_BIBTEX.strip()

    @patch("easybib.api.requests.get")
    def test_empty_response(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text="   ")
        result = get_inspire_bibtex("Author:2020abc")
        assert result is None

    @patch("easybib.api.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404, text="")
        result = get_inspire_bibtex("Author:2020abc")
        assert result is None


# --- get_ads_bibtex ---


class TestGetAdsBibtex:
    @patch("easybib.api.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"export": SAMPLE_BIBTEX}),
        )
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result == SAMPLE_BIBTEX.strip()

    @patch("easybib.api.requests.post")
    def test_no_records(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"export": "No records found"}),
        )
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result is None

    @patch("easybib.api.requests.post")
    def test_non_200(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500)
        result = get_ads_bibtex("2020ApJ...000..000A", "fake-key")
        assert result is None


# --- get_ads_info_from_inspire ---


class TestGetAdsInfoFromInspire:
    @patch("easybib.api.requests.get")
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

    @patch("easybib.api.requests.get")
    def test_no_hits(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"hits": {"hits": []}}),
        )
        bibcode, arxiv_id = get_ads_info_from_inspire("Author:2020abc")
        assert bibcode is None
        assert arxiv_id is None

    @patch("easybib.api.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        bibcode, arxiv_id = get_ads_info_from_inspire("Author:2020abc")
        assert bibcode is None
        assert arxiv_id is None


# --- search_ads_by_arxiv ---


class TestSearchAdsByArxiv:
    @patch("easybib.api.requests.get")
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

    @patch("easybib.api.requests.get")
    def test_empty_docs(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": {"docs": []}}),
        )
        result = search_ads_by_arxiv("2001.12345", "fake-key")
        assert result is None

    @patch("easybib.api.requests.get")
    def test_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=403)
        result = search_ads_by_arxiv("2001.12345", "fake-key")
        assert result is None


# --- fetch_bibtex (source routing) ---


class TestFetchBibtex:
    @patch("easybib.api.get_inspire_bibtex")
    @patch("easybib.api.get_ads_bibtex")
    @patch("easybib.api.get_ads_info_from_inspire")
    def test_ads_source(self, mock_info, mock_ads, mock_inspire):
        """With source='ads', ADS path is tried (via INSPIRE cross-ref)."""
        mock_info.return_value = ("2020ApJ...000..000A", None)
        mock_ads.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="ads")
        assert result == SAMPLE_BIBTEX
        assert "ADS" in source

    @patch("easybib.api.get_inspire_bibtex")
    def test_inspire_source(self, mock_inspire):
        """With source='inspire', INSPIRE is tried first."""
        mock_inspire.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="inspire")
        assert result == SAMPLE_BIBTEX
        assert "INSPIRE" in source

    @patch("easybib.api.get_inspire_bibtex")
    def test_auto_source_inspire_key(self, mock_inspire):
        """With source='auto' and an INSPIRE-style key, INSPIRE is tried first."""
        mock_inspire.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="auto")
        assert result == SAMPLE_BIBTEX
        assert "INSPIRE" in source

    @patch("easybib.api.get_ads_bibtex")
    def test_auto_source_ads_bibcode(self, mock_ads):
        """With source='auto' and an ADS-style key, ADS is tried first."""
        mock_ads.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex(
            "2016PhRvL.116f1102A", "fake-key", source="auto"
        )
        assert result == SAMPLE_BIBTEX
        assert "ADS" in source

    @patch("easybib.api.get_semantic_scholar_bibtex")
    @patch("easybib.api.get_inspire_bibtex")
    @patch("easybib.api.get_ads_bibtex")
    @patch("easybib.api.get_ads_info_from_inspire")
    @patch("easybib.api.search_ads_by_arxiv")
    def test_not_found(self, mock_search, mock_info, mock_ads, mock_inspire, mock_ss):
        """When nothing is found, returns (None, None)."""
        mock_inspire.return_value = None
        mock_ads.return_value = None
        mock_info.return_value = (None, None)
        mock_search.return_value = None
        mock_ss.return_value = None
        result, source = fetch_bibtex("Author:2020abc", "fake-key", source="ads")
        assert result is None
        assert source is None

    @patch("easybib.api.get_semantic_scholar_bibtex")
    def test_semantic_scholar_source(self, mock_ss):
        """With source='semantic-scholar', Semantic Scholar is tried first."""
        mock_ss.return_value = SAMPLE_BIBTEX
        result, source = fetch_bibtex(
            "Author:2020abc", "fake-key", source="semantic-scholar", ss_api_key="ss-key"
        )
        assert result == SAMPLE_BIBTEX
        assert "Semantic Scholar" in source


# --- get_arxiv_id_from_inspire ---


class TestGetArxivIdFromInspire:
    @patch("easybib.api.get_ads_info_from_inspire")
    def test_returns_arxiv_id(self, mock_info):
        mock_info.return_value = ("2020ApJ...000..000A", "2001.12345")
        result = get_arxiv_id_from_inspire("Author:2020abc")
        assert result == "2001.12345"

    @patch("easybib.api.get_ads_info_from_inspire")
    def test_returns_none(self, mock_info):
        mock_info.return_value = (None, None)
        result = get_arxiv_id_from_inspire("Author:2020abc")
        assert result is None


# --- get_semantic_scholar_bibtex ---


SS_SAMPLE_BIBTEX = "@inproceedings{Vaswani2017AttentionIA,\n  title={Attention is All you Need},\n  author={A. Vaswani},\n}"


class TestGetSemanticScholarBibtex:
    @patch("easybib.api.requests.get")
    def test_success_arxiv_id(self, mock_get):
        """Successful lookup via arXiv ID."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={"citationStyles": {"bibtex": SS_SAMPLE_BIBTEX}}
            ),
        )
        result = get_semantic_scholar_bibtex("2106.15928")
        assert result == SS_SAMPLE_BIBTEX.strip()
        # Should have been called with ARXIV: prefix
        call_url = mock_get.call_args[0][0]
        assert "ARXIV:2106.15928" in call_url

    @patch("easybib.api.requests.get")
    def test_success_direct_key(self, mock_get):
        """Falls back to direct key lookup when arXiv fails."""
        # First call (arXiv) fails, second call (direct) succeeds
        mock_get.side_effect = [
            MagicMock(status_code=404, json=MagicMock(return_value={})),
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value={"citationStyles": {"bibtex": SS_SAMPLE_BIBTEX}}
                ),
            ),
        ]
        result = get_semantic_scholar_bibtex("some-ss-id")
        assert result == SS_SAMPLE_BIBTEX.strip()

    @patch("easybib.api.requests.get")
    def test_empty_bibtex(self, mock_get):
        """Returns None when citationStyles.bibtex is empty."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"citationStyles": {"bibtex": "  "}}),
        )
        result = get_semantic_scholar_bibtex("2106.15928")
        assert result is None

    @patch("easybib.api.requests.get")
    def test_non_200(self, mock_get):
        """Returns None on non-200 responses."""
        mock_get.return_value = MagicMock(status_code=404, json=MagicMock(return_value={}))
        result = get_semantic_scholar_bibtex("2106.15928")
        assert result is None

    @patch("easybib.api.requests.get")
    def test_api_key_header(self, mock_get):
        """API key is passed as x-api-key header."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={"citationStyles": {"bibtex": SS_SAMPLE_BIBTEX}}
            ),
        )
        get_semantic_scholar_bibtex("2106.15928", api_key="my-ss-key")
        call_headers = mock_get.call_args[1].get("headers", {})
        assert call_headers.get("x-api-key") == "my-ss-key"

    @patch("easybib.api.requests.get")
    def test_no_api_key_no_header(self, mock_get):
        """Without API key, no x-api-key header is sent."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={"citationStyles": {"bibtex": SS_SAMPLE_BIBTEX}}
            ),
        )
        get_semantic_scholar_bibtex("2106.15928")
        call_headers = mock_get.call_args[1].get("headers", {})
        assert "x-api-key" not in call_headers
