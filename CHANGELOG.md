# Changelog

All notable changes to easybib are documented here.

## [0.7.0] — 2026-04-17

### Added
- `--refresh-only` flag: re-fetches and updates only entries that already exist
  in the output `.bib` file. Citation keys found in `.tex` files but not present
  in the `.bib` file are silently skipped. Useful for refreshing existing
  references with the latest data without adding new entries.

---

## [0.6.0] — 2026-03-17

### Added
- `--remove-collaborations` flag: strips collaboration author entries (e.g.
  `The LIGO Scientific Collaboration`) from BibTeX author lists, provided at
  least one individual author remains. Settable via `remove-collaborations` in
  the config file.

---

## [0.5.0] — 2026-02-24

### Added
- `--aas-macros` flag: downloads the AAS journal macro definitions and expands
  them inline in the output `.bib` file (e.g. `{\apj}` → `{ApJ}`), making
  entries self-contained for users who do not load `aas_macros.sty`.
- `--bib-source FILE` flag: copies entries from an existing `.bib` file instead
  of fetching them from the API. Keys not present in the source file fall back
  to the normal API lookup. Accepts any citation key format, not just
  INSPIRE/ADS/arXiv identifiers. Settable via `bib-source` in the config file.
- `--prefer-api` flag: when used with `--bib-source`, INSPIRE/ADS/arXiv keys
  are fetched from the API even if they exist in the source file. Keys with
  unrecognised formats (e.g. `einstein1905`) still use the local source.
  Settable via `prefer-api` in the config file.
- `--ascii` flag: replaces Unicode characters in BibTeX entries with
  LaTeX/ASCII equivalents (dashes, Greek letters, accented characters,
  mathematical symbols, astronomical symbols, super/subscripts). Characters
  that cannot be converted are removed. Settable via `ascii` in the config file.

### Fixed
- `--bib-source` keys with non-standard formats were silently discarded by the
  citation key validator before the source lookup could run. The source file is
  now loaded before citation extraction, and its keys are passed as `known_keys`
  so they are always accepted.
- `--aas-macros` originally used `@preamble` to inject macro definitions, which
  is only written to the `.bbl` file if the bibliography style calls the
  `preamble$` built-in (many styles do not). Macros are now expanded inline
  in the field values instead.

---

## [0.4.0] — 2026-02-19

### Added
- `--key-type` flag to enforce that all citation keys in a project use a single
  format (`inspire`, `ads`, or `arxiv`). Exits with a non-zero status and lists
  offending keys without fetching anything. Settable via `key-type` in the
  config file.
- Duplicate detection: easybib now detects when two different citation keys
  refer to the same paper (matched by API-returned key, arXiv eprint ID, or
  DOI). The second entry is skipped and a warning is printed.
- arXiv IDs (`2508.18080`, `hep-ph/9905318`) are now accepted as first-class
  citation keys. easybib fetches the BibTeX entry and writes both the full
  entry under its natural key and a `@misc` crossref stub so that
  `\cite{arxiv_id}` resolves correctly.
- Semantic Scholar (`--preferred-source semantic-scholar`) added as a fetch
  source, with fallback chains covering all combinations of ADS, INSPIRE, and
  Semantic Scholar.
- Warning printed when ADS bibcodes are present in the key list but no
  `ADS_API_KEY` is set.
- `--semantic-scholar-api-key` flag (and `SEMANTIC_SCHOLAR_API_KEY` environment
  variable) for authenticated Semantic Scholar access with higher rate limits.
- Integration tests for INSPIRE, ADS, and Semantic Scholar fetch paths.

### Changed
- `--source` renamed to `--preferred-source` for clarity.
- Internal code split from a single module into `core.py` (parsing),
  `api.py` (network), and `conversions.py` (BibTeX transformations).

### Fixed
- ADS bibcodes were silently skipped by `extract_cite_keys` because they
  contain no `:` and were treated as invalid keys.
- Two bugs affecting ADS bibcodes used directly as citation keys.
- Semantic Scholar 429 rate-limit responses now raise a clear error rather than
  silently returning no result.

---

## [0.3.0] — 2026-02-06

### Added
- `--version` flag.
- Config file support (`~/.easybib.config`): persistent defaults for `output`,
  `max-authors`, `preferred-source`, `ads-api-key`, and
  `semantic-scholar-api-key`. CLI flags override config values, which override
  built-in defaults. A custom config path can be specified with `--config`.

---

## [0.2.0] — 2026-02-06

### Added
- Accept a single `.tex` file as input in addition to a directory.
- `--ads-api-key` flag to pass the ADS API key on the command line (overrides
  the `ADS_API_KEY` environment variable).
- Test suite (`pytest`) covering core functions, fetch logic, and CLI
  integration.
- GitHub Actions CI workflow running tests on Python 3.9 and 3.12.
- Codecov coverage reporting.

---

## [0.1.0] — initial release

- Scans `.tex` files for INSPIRE texkeys and ADS bibcodes in `\cite{}` and
  related commands.
- Fetches BibTeX from NASA/ADS (default) or INSPIRE (`--preferred-source
  inspire`), with cross-referencing fallback between the two.
- Replaces the citation key in fetched entries to match the key used in the
  `.tex` file.
- Truncates long author lists with `--max-authors` (default: 3).
- Incremental updates: skips keys already present in the output file. Use
  `--fresh` to start from scratch.
- `--list-keys` mode to inspect found keys without fetching.
