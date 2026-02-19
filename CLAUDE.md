# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

easybib is a CLI tool that scans LaTeX `.tex` files for citation keys (INSPIRE texkeys and ADS bibcodes), fetches BibTeX entries from the INSPIRE and NASA/ADS APIs, and writes a `.bib` file. It supports configurable source preference, author truncation, incremental updates, and persistent config via `~/.easybib.config`.

## Commands

```bash
# Install for development
pip install -e ".[test]"

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=easybib --cov-report=xml

# Run the tool
easybib /path/to/latex/project
easybib paper.tex
```

## Architecture

The source lives in `src/easybib/` with four modules:

- **core.py** — Parsing and key detection: citation key extraction from `.tex` files (regex-based), existing `.bib` key extraction, and key format detection (INSPIRE vs ADS bibcode). Imports only `re`.
- **api.py** — API access (network I/O): BibTeX fetching from INSPIRE, NASA/ADS, and Semantic Scholar APIs with multi-source fallback chains (ADS→INSPIRE→SS, INSPIRE→ADS→SS, SS→INSPIRE→ADS, with arXiv as intermediary). Imports `requests` and key detection from `core`.
- **conversions.py** — BibTeX string transformations: citation key replacement and author truncation. Imports only `re`.
- **cli.py** — Argument parsing with two-pass config loading (first pass extracts `--config` path, second pass applies config file defaults before CLI flags), `.tex` file discovery, incremental update logic (skips keys already in existing `.bib`), and orchestration of the fetch loop.

Key patterns:
- Functions return tuples: `(result, source_info)` or `(keys, warnings)` for composability
- Multi-source fallback: each fetch strategy tries primary source, then cross-references via INSPIRE's JSON API to find arXiv IDs, then searches the alternate source
- Config precedence: CLI flags > config file > built-in defaults

## Testing

Three test files in `tests/`:
- **test_core.py** — Unit tests for pure functions (extraction, key detection, truncation, key replacement)
- **test_cli.py** — CLI integration tests using `sys.argv` patching and tmpdir fixtures
- **test_fetch.py** — API fetch tests with `unittest.mock.patch` on `requests.get`/`requests.post`

CI runs on Python 3.9 and 3.12 via GitHub Actions.

## Dependencies

- Runtime: `requests`
- Test: `pytest`, `pytest-cov`
- Python >= 3.9
