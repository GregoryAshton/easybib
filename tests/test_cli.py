"""Tests for easybib CLI."""

import subprocess
import sys
from unittest.mock import patch

from easybib.cli import main


class TestListKeys:
    def test_list_keys_single_file(self, tmp_path, capsys):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc} and \citep{Other:2021xyz}")
        with patch("sys.argv", ["easybib", str(tex), "--list-keys"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Author:2020abc" in captured.out
        assert "Other:2021xyz" in captured.out

    def test_list_keys_directory(self, tmp_path, capsys):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "a.tex").write_text(r"\cite{A:2020abc}")
        (sub / "b.tex").write_text(r"\cite{B:2021xyz}")
        with patch("sys.argv", ["easybib", str(tmp_path), "--list-keys"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "A:2020abc" in captured.out
        assert "B:2021xyz" in captured.out


class TestMissingApiKey:
    def test_error_without_api_key(self, tmp_path, capsys):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--config", no_config]),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "ADS_API_KEY" in captured.out

    def test_inspire_source_no_api_key_ok(self, tmp_path, capsys):
        """Using --preferred-source inspire should not require an ADS API key."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", return_value=(None, None)),
        ):
            result = main()
        # Should not return 1 for missing API key
        assert result is None

    def test_ads_bibcode_without_api_key_warns(self, tmp_path, capsys):
        """ADS bibcodes with no API key should print a rate-limit warning."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{2025ApJ...995L..18A}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(tmp_path / "out.bib")]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", return_value=(None, None)),
        ):
            main()
        captured = capsys.readouterr()
        assert "ADS bibcode" in captured.out
        assert "ADS_API_KEY" in captured.out

    def test_semantic_scholar_429_handled_gracefully(self, tmp_path, capsys):
        """A Semantic Scholar 429 during fetching is caught and reported, not raised."""
        import requests as req
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(tmp_path / "out.bib")]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", side_effect=req.exceptions.HTTPError("Semantic Scholar rate limit exceeded (429).")),
        ):
            result = main()
        captured = capsys.readouterr()
        assert "429" in captured.out
        assert result is None  # should not crash

    def test_no_warning_when_api_key_set(self, tmp_path, capsys):
        """No rate-limit warning when an ADS API key is available."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{2025ApJ...995L..18A}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "ads", "--ads-api-key", "mykey", "--config", no_config, "-o", str(tmp_path / "out.bib")]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", return_value=(None, None)),
        ):
            main()
        captured = capsys.readouterr()
        assert "ADS bibcode" not in captured.out


class TestAdsApiKeyOverride:
    def test_flag_overrides_env(self, tmp_path, capsys):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--ads-api-key", "flag-key", "-o", str(tmp_path / "out.bib")],
            ),
            patch.dict("os.environ", {"ADS_API_KEY": "env-key"}, clear=True),
            patch("easybib.cli.fetch_bibtex") as mock_fetch,
        ):
            mock_fetch.return_value = (
                "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}",
                "ADS",
            )
            main()
        # The flag value should be used, not the env var
        call_args = mock_fetch.call_args
        assert call_args[0][1] == "flag-key"


class TestConfigFile:
    def test_config_sets_defaults(self, tmp_path, capsys):
        """Config file values are used when no CLI flags are given."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        cfg = tmp_path / "test.config"
        cfg.write_text(
            "[easybib]\noutput = custom.bib\nmax-authors = 5\npreferred-source = inspire\nads-api-key = cfg-key\n"
        )
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--config", str(cfg), "--list-keys"],
            ),
        ):
            main()
        captured = capsys.readouterr()
        assert "Author:2020abc" in captured.out

    def test_config_values_applied(self, tmp_path):
        """Config file values feed into parsed args."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        cfg = tmp_path / "test.config"
        cfg.write_text(
            "[easybib]\noutput = custom.bib\nmax-authors = 5\npreferred-source = inspire\nads-api-key = cfg-key\n"
        )
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--config", str(cfg), "--list-keys"],
            ),
            patch("easybib.cli.extract_cite_keys", return_value=(set(), [])),
        ):
            # Access the parsed args by patching parse_args
            import easybib.cli as cli_mod

            original_parse = cli_mod.argparse.ArgumentParser.parse_args

            captured_args = {}

            def spy_parse(self_parser, *a, **kw):
                result = original_parse(self_parser, *a, **kw)
                captured_args.update(vars(result))
                return result

            with patch.object(
                cli_mod.argparse.ArgumentParser, "parse_args", spy_parse
            ):
                main()

            assert captured_args["output"] == "custom.bib"
            assert captured_args["max_authors"] == 5
            assert captured_args["preferred_source"] == "inspire"
            assert captured_args["ads_api_key"] == "cfg-key"

    def test_cli_flags_override_config(self, tmp_path):
        """CLI flags take priority over config file values."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        cfg = tmp_path / "test.config"
        cfg.write_text(
            "[easybib]\noutput = config.bib\nmax-authors = 5\npreferred-source = inspire\nads-api-key = cfg-key\n"
        )
        with (
            patch(
                "sys.argv",
                [
                    "easybib",
                    str(tex),
                    "--config",
                    str(cfg),
                    "--list-keys",
                    "-o",
                    "cli.bib",
                    "--max-authors",
                    "10",
                    "--preferred-source",
                    "ads",
                    "--ads-api-key",
                    "cli-key",
                ],
            ),
            patch("easybib.cli.extract_cite_keys", return_value=(set(), [])),
        ):
            import easybib.cli as cli_mod

            original_parse = cli_mod.argparse.ArgumentParser.parse_args
            captured_args = {}

            def spy_parse(self_parser, *a, **kw):
                result = original_parse(self_parser, *a, **kw)
                captured_args.update(vars(result))
                return result

            with patch.object(
                cli_mod.argparse.ArgumentParser, "parse_args", spy_parse
            ):
                main()

            assert captured_args["output"] == "cli.bib"
            assert captured_args["max_authors"] == 10
            assert captured_args["preferred_source"] == "ads"
            assert captured_args["ads_api_key"] == "cli-key"

    def test_missing_config_silently_ignored(self, tmp_path, capsys):
        """A nonexistent config file does not cause an error."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with patch(
            "sys.argv",
            [
                "easybib",
                str(tex),
                "--config",
                str(tmp_path / "nonexistent.config"),
                "--list-keys",
            ],
        ):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Author:2020abc" in captured.out

    def test_custom_config_path(self, tmp_path, capsys):
        """--config flag points to a custom path."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        cfg = custom_dir / "my.config"
        cfg.write_text("[easybib]\npreferred-source = inspire\n")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--config", str(cfg), "--list-keys"],
            ),
        ):
            result = main()
        assert result == 0

    def test_config_ads_api_key_used_for_lookup(self, tmp_path):
        """ads-api-key from config feeds into the API key chain."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        cfg = tmp_path / "test.config"
        cfg.write_text("[easybib]\nads-api-key = config-api-key\n")
        with (
            patch(
                "sys.argv",
                [
                    "easybib",
                    str(tex),
                    "--config",
                    str(cfg),
                    "-o",
                    str(tmp_path / "out.bib"),
                ],
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex") as mock_fetch,
        ):
            mock_fetch.return_value = (
                "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}",
                "ADS",
            )
            main()
        call_args = mock_fetch.call_args
        assert call_args[0][1] == "config-api-key"


class TestSemanticScholarCli:
    def test_semantic_scholar_source_no_ads_key_ok(self, tmp_path, capsys):
        """Using --preferred-source semantic-scholar should not require an ADS API key."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "semantic-scholar", "--config", no_config, "-o", str(tmp_path / "out.bib")]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", return_value=(None, None)),
        ):
            result = main()
        # Should not return 1 for missing API key
        assert result is None

    def test_semantic_scholar_api_key_flag(self, tmp_path):
        """--semantic-scholar-api-key flag is passed to fetch_bibtex."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with (
            patch(
                "sys.argv",
                [
                    "easybib", str(tex),
                    "--preferred-source", "inspire",
                    "--semantic-scholar-api-key", "ss-flag-key",
                    "-o", str(tmp_path / "out.bib"),
                ],
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex") as mock_fetch,
        ):
            mock_fetch.return_value = (
                "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}",
                "INSPIRE",
            )
            main()
        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs.get("ss_api_key") == "ss-flag-key"

    def test_semantic_scholar_api_key_env_var(self, tmp_path):
        """SEMANTIC_SCHOLAR_API_KEY env var is picked up."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with (
            patch(
                "sys.argv",
                [
                    "easybib", str(tex),
                    "--preferred-source", "inspire",
                    "-o", str(tmp_path / "out.bib"),
                ],
            ),
            patch.dict("os.environ", {"SEMANTIC_SCHOLAR_API_KEY": "ss-env-key"}, clear=True),
            patch("easybib.cli.fetch_bibtex") as mock_fetch,
        ):
            mock_fetch.return_value = (
                "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}",
                "INSPIRE",
            )
            main()
        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs.get("ss_api_key") == "ss-env-key"

    def test_config_semantic_scholar_api_key(self, tmp_path):
        """semantic-scholar-api-key from config is used."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        cfg = tmp_path / "test.config"
        cfg.write_text("[easybib]\nsemantic-scholar-api-key = ss-cfg-key\npreferred-source = inspire\n")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--config", str(cfg), "-o", str(tmp_path / "out.bib")],
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex") as mock_fetch,
        ):
            mock_fetch.return_value = (
                "@article{Author:2020abc,\n  title={Test},\n  author={Doe, J.},\n}",
                "INSPIRE",
            )
            main()
        call_kwargs = mock_fetch.call_args[1]
        assert call_kwargs.get("ss_api_key") == "ss-cfg-key"


class TestArxivIdKey:
    def test_arxiv_id_produces_main_and_stub(self, tmp_path):
        """An arXiv ID key writes both the fetched entry and a @misc crossref stub."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{2508.18080}")
        output = tmp_path / "out.bib"
        INSPIRE_BIBTEX = "@article{LIGOScientific:2025hdt,\n  title={Test},\n  author={Abbott, R.},\n}"
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)],
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex_by_arxiv", return_value=(INSPIRE_BIBTEX, "INSPIRE via arXiv")),
        ):
            main()
        content = output.read_text()
        assert "@article{LIGOScientific:2025hdt," in content
        assert "@misc{2508.18080," in content
        assert "crossref = {LIGOScientific:2025hdt}" in content

    def test_arxiv_id_not_found(self, tmp_path, capsys):
        """An arXiv ID that cannot be fetched is reported as not found."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{2508.18080}")
        output = tmp_path / "out.bib"
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)],
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex_by_arxiv", return_value=(None, None)),
        ):
            main()
        captured = capsys.readouterr()
        assert "2508.18080" in captured.out
        assert "Not found" in captured.out


class TestDuplicateDetection:
    # Two entries with the same source key
    BIBTEX_NATURAL = "@article{LIGOScientific:2025hdt,\n    eprint = \"2508.18080\",\n    doi = \"10.3847/abc\",\n    author = {Abbott, R.},\n    title = {Test},\n}\n"
    # Same paper, different source key but same eprint/doi
    BIBTEX_SAME_EPRINT = "@article{DifferentSourceKey,\n    eprint = \"2508.18080\",\n    doi = \"10.3847/abc\",\n    author = {Abbott, R.},\n    title = {Test},\n}\n"
    # Same paper again, but different source key and eprint, only DOI matches
    BIBTEX_SAME_DOI_ONLY = "@article{AnotherSourceKey,\n    eprint = \"9999.99999\",\n    doi = \"10.3847/abc\",\n    author = {Abbott, R.},\n    title = {Test},\n}\n"

    def test_duplicate_by_source_key(self, tmp_path, capsys):
        """Two keys fetching the same source key: second is skipped with warning."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{2508.18080} \cite{LIGOScientific:2025hdt}")
        output = tmp_path / "out.bib"
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex_by_arxiv", return_value=(self.BIBTEX_NATURAL, "INSPIRE via arXiv")),
            patch("easybib.cli.fetch_bibtex", return_value=(self.BIBTEX_NATURAL, "INSPIRE")),
        ):
            main()
        captured = capsys.readouterr()
        assert "Duplicate" in captured.out
        assert "LIGOScientific:2025hdt" in captured.out
        content = output.read_text()
        assert content.count("@article{LIGOScientific:2025hdt") == 1

    def test_duplicate_by_eprint(self, tmp_path, capsys):
        """Two entries with the same arXiv eprint but different source keys: second skipped."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc} \cite{Other:2021xyz}")
        output = tmp_path / "out.bib"
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", side_effect=[
                (self.BIBTEX_NATURAL, "INSPIRE"),
                (self.BIBTEX_SAME_EPRINT, "INSPIRE"),
            ]),
        ):
            main()
        captured = capsys.readouterr()
        assert "Duplicate" in captured.out
        assert "2508.18080" in captured.out

    def test_duplicate_by_doi(self, tmp_path, capsys):
        """Two entries with matching DOI but different source key and eprint: second skipped."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc} \cite{Other:2021xyz}")
        output = tmp_path / "out.bib"
        no_config = str(tmp_path / "nonexistent.config")
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", side_effect=[
                (self.BIBTEX_NATURAL, "INSPIRE"),
                (self.BIBTEX_SAME_DOI_ONLY, "INSPIRE"),
            ]),
        ):
            main()
        captured = capsys.readouterr()
        assert "Duplicate" in captured.out
        assert "10.3847/abc" in captured.out

    def test_no_duplicate_different_papers(self, tmp_path, capsys):
        """Two genuinely different papers produce no duplicate warning."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc} \cite{Other:2021xyz}")
        output = tmp_path / "out.bib"
        no_config = str(tmp_path / "nonexistent.config")
        bibtex_a = "@article{KeyA,\n    doi = \"10.1234/aaa\",\n    author = {A},\n    title = {A},\n}\n"
        bibtex_b = "@article{KeyB,\n    doi = \"10.1234/bbb\",\n    author = {B},\n    title = {B},\n}\n"
        with (
            patch("sys.argv", ["easybib", str(tex), "--preferred-source", "inspire", "--config", no_config, "-o", str(output)]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", side_effect=[(bibtex_a, "INSPIRE"), (bibtex_b, "INSPIRE")]),
        ):
            main()
        captured = capsys.readouterr()
        assert "Duplicate" not in captured.out
        content = output.read_text()
        assert "@article{Author:2020abc" in content
        assert "@article{Other:2021xyz" in content


class TestFileVsDirectory:
    def test_single_file(self, tmp_path, capsys):
        tex = tmp_path / "paper.tex"
        tex.write_text(r"\cite{A:2020abc}")
        with patch("sys.argv", ["easybib", str(tex), "--list-keys"]):
            main()
        captured = capsys.readouterr()
        assert "A:2020abc" in captured.out

    def test_directory_recursive(self, tmp_path, capsys):
        nested = tmp_path / "ch1"
        nested.mkdir()
        (nested / "intro.tex").write_text(r"\cite{A:2020abc}")
        (tmp_path / "main.tex").write_text(r"\cite{B:2021xyz}")
        with patch("sys.argv", ["easybib", str(tmp_path), "--list-keys"]):
            main()
        captured = capsys.readouterr()
        assert "A:2020abc" in captured.out
        assert "B:2021xyz" in captured.out
