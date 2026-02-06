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
        with (
            patch("sys.argv", ["easybib", str(tex)]),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "ADS_API_KEY" in captured.out

    def test_inspire_source_no_api_key_ok(self, tmp_path, capsys):
        """Using --source inspire should not require an ADS API key."""
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with (
            patch("sys.argv", ["easybib", str(tex), "--source", "inspire"]),
            patch.dict("os.environ", {}, clear=True),
            patch("easybib.cli.fetch_bibtex", return_value=(None, None)),
        ):
            result = main()
        # Should not return 1 for missing API key
        assert result is None


class TestAdsApiKeyOverride:
    def test_flag_overrides_env(self, tmp_path, capsys):
        tex = tmp_path / "test.tex"
        tex.write_text(r"\cite{Author:2020abc}")
        with (
            patch(
                "sys.argv",
                ["easybib", str(tex), "--ads-api-key", "flag-key"],
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
