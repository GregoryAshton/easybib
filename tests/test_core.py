"""Tests for easybib.core pure functions."""

import pytest

from easybib.core import (
    extract_cite_keys,
    extract_existing_bib_keys,
    is_ads_bibcode,
    is_inspire_key,
    replace_bibtex_key,
    truncate_authors,
)


# --- extract_cite_keys ---


class TestExtractCiteKeys:
    def test_basic_cite(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        keys, warnings = extract_cite_keys(tex)
        assert keys == ["Author:2020abc"]
        assert warnings == []

    def test_citep_and_citet(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\citep{A:2020abc} and \citet{B:2021xyz}")
        keys, warnings = extract_cite_keys(tex)
        assert set(keys) == {"A:2020abc", "B:2021xyz"}
        assert warnings == []

    def test_capital_citep(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\Citep{Author:2020abc}")
        keys, warnings = extract_cite_keys(tex)
        assert keys == ["Author:2020abc"]

    def test_optional_args(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\citep[e.g.][]{Author:2020abc}")
        keys, warnings = extract_cite_keys(tex)
        assert keys == ["Author:2020abc"]

    def test_multiple_keys_in_single_cite(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{A:2020abc, B:2021xyz}")
        keys, warnings = extract_cite_keys(tex)
        assert set(keys) == {"A:2020abc", "B:2021xyz"}

    def test_empty_key_warning(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{A:2020abc, , B:2021xyz}")
        keys, warnings = extract_cite_keys(tex)
        assert set(keys) == {"A:2020abc", "B:2021xyz"}
        assert len(warnings) == 1
        assert "Empty citation key" in warnings[0]

    def test_key_without_colon_warning(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{nocolon}")
        keys, warnings = extract_cite_keys(tex)
        assert keys == []
        assert len(warnings) == 1
        assert "not an INSPIRE/ADS key" in warnings[0]

    def test_citeauthor_and_citeyear(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\citeauthor{A:2020abc} \citeyear{B:2021xyz}")
        keys, warnings = extract_cite_keys(tex)
        assert set(keys) == {"A:2020abc", "B:2021xyz"}

    def test_no_citations(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"No citations here.")
        keys, warnings = extract_cite_keys(tex)
        assert keys == []
        assert warnings == []

    def test_deduplication_not_applied(self, tmp_path):
        """extract_cite_keys returns all occurrences (dedup is done by the caller)."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{A:2020abc} \cite{A:2020abc}")
        keys, warnings = extract_cite_keys(tex)
        assert keys == ["A:2020abc", "A:2020abc"]


# --- extract_existing_bib_keys ---


class TestExtractExistingBibKeys:
    def test_parse_keys(self, tmp_path):
        bib = tmp_path / "refs.bib"
        bib.write_text(
            "@article{Author:2020abc,\n"
            "  title={Test},\n"
            "}\n\n"
            "@inproceedings{Other:2021xyz,\n"
            "  title={Other},\n"
            "}\n"
        )
        keys = extract_existing_bib_keys(bib)
        assert keys == {"Author:2020abc", "Other:2021xyz"}

    def test_nonexistent_file(self, tmp_path):
        bib = tmp_path / "missing.bib"
        keys = extract_existing_bib_keys(bib)
        assert keys == set()

    def test_empty_file(self, tmp_path):
        bib = tmp_path / "empty.bib"
        bib.write_text("")
        keys = extract_existing_bib_keys(bib)
        assert keys == set()


# --- replace_bibtex_key ---


class TestReplaceBibtexKey:
    def test_simple_replacement(self):
        bibtex = "@article{OldKey:2020abc,\n  title={Test},\n}"
        result = replace_bibtex_key(bibtex, "NewKey:2020xyz")
        assert result.startswith("@article{NewKey:2020xyz,")

    def test_preserves_content(self):
        bibtex = "@article{OldKey:2020abc,\n  title={Test},\n  author={Doe},\n}"
        result = replace_bibtex_key(bibtex, "New:2020xyz")
        assert "title={Test}" in result
        assert "author={Doe}" in result

    def test_only_replaces_first(self):
        bibtex = "@article{A:2020abc,\n  note={See also A:2020abc},\n}"
        result = replace_bibtex_key(bibtex, "B:2020xyz")
        assert result.startswith("@article{B:2020xyz,")
        assert "See also A:2020abc" in result


# --- truncate_authors ---


class TestTruncateAuthors:
    def test_truncation(self):
        bibtex = (
            "@article{Key:2020abc,\n"
            "  author={Alpha, A. and Beta, B. and Gamma, G. and Delta, D. and Epsilon, E.},\n"
            "  title={Test},\n"
            "}"
        )
        result = truncate_authors(bibtex, max_authors=3)
        assert "Alpha, A. and Beta, B. and Gamma, G. and others" in result
        assert "Delta" not in result

    def test_no_truncation_when_within_limit(self):
        bibtex = (
            "@article{Key:2020abc,\n"
            "  author={Alpha, A. and Beta, B.},\n"
            "  title={Test},\n"
            "}"
        )
        result = truncate_authors(bibtex, max_authors=3)
        assert result == bibtex

    def test_max_authors_zero_no_change(self):
        bibtex = (
            "@article{Key:2020abc,\n"
            "  author={Alpha, A. and Beta, B. and Gamma, G. and Delta, D.},\n"
            "  title={Test},\n"
            "}"
        )
        result = truncate_authors(bibtex, max_authors=0)
        assert result == bibtex

    def test_max_authors_none_no_change(self):
        bibtex = (
            "@article{Key:2020abc,\n"
            "  author={Alpha, A. and Beta, B. and Gamma, G. and Delta, D.},\n"
            "  title={Test},\n"
            "}"
        )
        result = truncate_authors(bibtex, max_authors=None)
        assert result == bibtex

    def test_exact_limit(self):
        bibtex = (
            "@article{Key:2020abc,\n"
            "  author={Alpha, A. and Beta, B. and Gamma, G.},\n"
            "  title={Test},\n"
            "}"
        )
        result = truncate_authors(bibtex, max_authors=3)
        assert result == bibtex


# --- is_ads_bibcode ---


class TestIsAdsBibcode:
    def test_positive(self):
        assert is_ads_bibcode("2016PhRvL.116f1102A") is True

    def test_positive_with_ampersand(self):
        assert is_ads_bibcode("2020A&A...641A...6P") is True

    def test_negative_inspire_key(self):
        assert is_ads_bibcode("Abbott:2016blz") is False

    def test_negative_short_string(self):
        assert is_ads_bibcode("2020") is False

    def test_negative_no_leading_year(self):
        assert is_ads_bibcode("PhRvL.116f1102A") is False


# --- is_inspire_key ---


class TestIsInspireKey:
    def test_positive(self):
        assert is_inspire_key("Abbott:2016blz") is True

    def test_positive_hyphenated(self):
        assert is_inspire_key("LIGO-Scientific:2020abc") is True

    def test_negative_ads_bibcode(self):
        assert is_inspire_key("2016PhRvL.116f1102A") is False

    def test_negative_no_colon(self):
        assert is_inspire_key("Abbott2016blz") is False

    def test_negative_missing_letters(self):
        assert is_inspire_key("Abbott:2016") is False
