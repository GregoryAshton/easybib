# easybib

[![Tests](https://github.com/GregoryAshton/easybib/actions/workflows/tests.yml/badge.svg)](https://github.com/GregoryAshton/easybib/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/GregoryAshton/easybib/branch/main/graph/badge.svg)](https://codecov.io/gh/GregoryAshton/easybib)

Automatically fetch BibTeX entries from [INSPIRE](https://inspirehep.net/), [NASA/ADS](https://ui.adsabs.harvard.edu/), and [Semantic Scholar](https://www.semanticscholar.org/) for LaTeX projects.

easybib scans your `.tex` files for citation keys, looks them up on INSPIRE, ADS, and/or Semantic Scholar, and writes a `.bib` file with the results. It handles INSPIRE texkeys (e.g. `Author:2020abc`), ADS bibcodes (e.g. `2016PhRvL.116f1102A`), and arXiv IDs (e.g. `2508.18080`).

## Installation

```bash
pip install easybib
```

## Usage

```bash
easybib /path/to/latex/project
easybib paper.tex
```

Pass a directory to scan all `.tex` files recursively, or a single `.tex` file. BibTeX entries are fetched and written to `references.bib`.

### Options

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Output BibTeX file (default: `references.bib`) |
| `-s`, `--preferred-source` | Preferred source: `ads` (default), `inspire`, `auto`, or `semantic-scholar` |
| `-a`, `--max-authors` | Truncate author lists (default: 3, use 0 for no limit) |
| `-l`, `--list-keys` | List found citation keys and exit (no fetching) |
| `--fresh` | Ignore existing output file and start from scratch |
| `--key-type` | Enforce a single key format: `inspire`, `ads`, or `arxiv` |
| `--aas-macros` | Embed AAS journal macro definitions in the output `.bib` file |
| `--bib-source` | Existing `.bib` file to copy entries from before falling back to the API |
| `--prefer-api` | With `--bib-source`, fetch INSPIRE/ADS/arXiv keys from the API even if they exist in the source file |
| `--ascii` | Replace Unicode characters in BibTeX entries with LaTeX/ASCII equivalents |
| `--remove-collaborations` | Remove collaboration entries (e.g. `The LIGO Collaboration`) from author lists, provided at least one individual author remains |
| `--ads-api-key` | ADS API key (overrides `ADS_API_KEY` environment variable) |
| `--semantic-scholar-api-key` | Semantic Scholar API key (overrides `SEMANTIC_SCHOLAR_API_KEY` environment variable) |
| `--config` | Path to config file (default: `~/.easybib.config`) |

### Examples

```bash
# Scan a directory
easybib ./paper --preferred-source inspire

# Scan a single file
easybib paper.tex

# Use a custom output file
easybib ./paper -o paper.bib

# List citation keys without fetching
easybib ./paper -l

# Keep all authors
easybib ./paper -a 0
```

### Config file

You can create a config file at `~/.easybib.config` to set persistent defaults, so you don't have to pass the same flags every time:

```ini
[easybib]
output = references.bib
max-authors = 3
preferred-source = ads
ads-api-key = your-key-here
semantic-scholar-api-key = your-key-here
key-type = inspire
aas-macros = true
bib-source = /path/to/master.bib
```

All fields are optional. CLI flags override config file values, which override the built-in defaults.

To use a config file at a different location:

```bash
easybib ./paper --config /path/to/my.config
```

### Source selection

The `--preferred-source` flag controls where BibTeX entries are fetched from. The source determines which service provides the BibTeX data, regardless of the key format used in your `.tex` files.

- **`ads`** (default) — Fetches BibTeX from ADS. If you use an INSPIRE-style key (e.g. `Author:2020abc`), easybib will cross-reference it via INSPIRE to find the corresponding ADS record, then pull the BibTeX from ADS. Falls back to INSPIRE, then Semantic Scholar, if ADS lookup fails.
- **`inspire`** — Fetches BibTeX from INSPIRE. Falls back to ADS, then Semantic Scholar, if the INSPIRE lookup fails. Does not require an ADS API key unless the fallback is triggered.
- **`auto`** — Chooses the source based on the key format: ADS bibcodes (e.g. `2016PhRvL.116f1102A`) are fetched from ADS, while INSPIRE-style keys are fetched from INSPIRE. Falls back to the other source, then Semantic Scholar, if the preferred one fails.
- **`semantic-scholar`** — Fetches BibTeX from Semantic Scholar first, falling back to INSPIRE then ADS. Does not require an ADS API key unless the fallback is triggered.

### arXiv IDs as citation keys

You can cite papers directly by their arXiv ID:

```latex
\cite{2508.18080}
```

easybib fetches the BibTeX entry from your preferred source (searching by arXiv ID) and writes two entries to the `.bib` file: the full entry under its natural citation key, plus a `@misc` stub so that `\cite{2508.18080}` resolves correctly:

```bibtex
@article{LIGOScientific:2025hdt,
  author = {Abbott, R. and others},
  title  = {...},
  ...
}

@misc{2508.18080,
  crossref = {LIGOScientific:2025hdt}
}
```

Both the new-style format (`2508.18080`) and the old-style format (`hep-ph/9905318`) are supported.

### Key type enforcement

If your project uses only one type of citation key, use `--key-type` to catch accidental mixing:

```bash
easybib paper.tex --key-type inspire
```

Accepted values are `inspire`, `ads`, and `arxiv`. If any key doesn't match, easybib prints the offending keys and their detected types, then exits with a non-zero status — without fetching anything:

```
Error: --key-type=inspire but 1 key(s) do not match:
  '2016PhRvL.116f1102A' (detected as: ads)
```

You can also set this in your config file:

```ini
[easybib]
key-type = inspire
```

### AAS journal macros

ADS BibTeX entries use LaTeX macros for journal names (e.g. `\apj` for the Astrophysical Journal, `\mnras` for MNRAS). These macros are defined in the `aas_macros.sty` style file, which must be loaded in your LaTeX document for the `.bib` file to compile correctly.

If you don't use AASTeX or the A&A document class, use `--aas-macros` to make the output `.bib` file self-contained:

```bash
easybib paper.tex --aas-macros
```

easybib downloads the AAS macros file, scans the output for which macros are actually used, and expands them inline in the `.bib` entries. For example, a field value of `{\apj}` becomes `{ApJ}` directly in the file, so no external macro package is needed and the entries compile correctly with any bibliography style.

You can also enable this permanently in your config file:

```ini
[easybib]
aas-macros = true
```

### Local bib source

If you already have a `.bib` file containing some of the entries you need, use `--bib-source` to copy entries from it directly instead of fetching them from the API:

```bash
easybib paper.tex --bib-source master.bib
```

For each citation key found in your `.tex` files, easybib checks the source file first. If the entry is there, it is copied directly (with author truncation applied). Keys not present in the source file are fetched from the API as normal.

This is useful for sharing a master bibliography across projects, or for working offline. The source file accepts any citation key format — keys are not required to be INSPIRE/ADS/arXiv identifiers.

By default the local source always takes priority. To fetch INSPIRE/ADS/arXiv keys from the API regardless of whether they exist in the source file, add `--prefer-api`:

```bash
easybib paper.tex --bib-source master.bib --prefer-api
```

This leaves custom-format keys (e.g. `einstein1905`) still served from the local source, while recognised API keys are always fetched fresh.

You can also set these in your config file:

```ini
[easybib]
bib-source = /path/to/master.bib
prefer-api = true
```

### Unicode sanitisation

ADS BibTeX entries sometimes contain Unicode characters in titles and other fields — for example, a Unicode dash (`─`) in a mass range, Greek letters, or accented characters in journal names. Standard LaTeX requires `\usepackage[utf8]{inputenc}` (or LuaLaTeX/XeLaTeX) to handle these; without it, compilation fails.

Use `--ascii` to convert Unicode to LaTeX/ASCII equivalents automatically:

```bash
easybib paper.tex --ascii
```

Known characters are replaced with LaTeX commands:

| Unicode | Replaced with |
|---------|--------------|
| `─` `–` `—` (dashes) | `--` or `---` |
| `é`, `ü`, `ñ`, … (accented) | `{\'e}`, `{\"u}`, `{\~n}`, … |
| `α`, `β`, `γ`, … (Greek) | `$\alpha$`, `$\beta$`, `$\gamma$`, … |
| `±`, `×`, `∼`, `≤`, … (math) | `$\pm$`, `$\times$`, `$\sim$`, `$\leq$`, … |
| `☉`, `⊕` (astronomical) | `$\odot$`, `$\oplus$` |
| `²`, `³`, `₀`, `₁`, … (super/subscripts) | `$^2$`, `$^3$`, `$_0$`, `$_1$`, … |

Characters that cannot be converted are removed. This flag applies to the entire output file, including any entries carried over from a previous run.

You can also enable it permanently in your config file:

```ini
[easybib]
ascii = true
```

### Removing collaboration authors

Large experimental collaborations often list a collaboration name as an author entry alongside the individual authors — for example, `The LIGO Scientific Collaboration` appearing in the author list in addition to `Abbott, R.` and others. This can inflate formatted references or trigger errors in some bibliography styles.

Use `--remove-collaborations` to strip these entries from all author lists:

```bash
easybib paper.tex --remove-collaborations
```

Any author entry matching common collaboration patterns (e.g. `The ... Collaboration`, `... Team`, `... Consortium`) is removed. The flag only removes a collaboration entry if at least one individual author remains; if the collaboration is the sole author, it is kept.

You can also enable this permanently in your config file:

```ini
[easybib]
remove-collaborations = true
```

### Duplicate detection

easybib detects when two different citation keys in your `.tex` files refer to the same paper — for example, citing both `LIGOScientific:2016aoc` and `2016PhRvL.116f1102A`. Detection is based on:

- The citation key returned by the API (before any key replacement)
- The arXiv eprint ID in the BibTeX entry
- The DOI in the BibTeX entry

When a duplicate is found, the second entry is skipped and a warning is printed at the end of the run:

```
Warning: 1 key(s) skipped — they refer to the same paper as an earlier key.
Please use a single key per paper in your .tex files:
  '2016PhRvL.116f1102A' duplicates 'LIGOScientific:2016aoc' (source key 'LIGOScientific:2016aoc')
```

### ADS API key

When using ADS as the source (the default), provide your API key either via the command line:

```bash
easybib ./paper --ads-api-key your-key-here
```

Or as an environment variable:

```bash
export ADS_API_KEY="your-key-here"
```

Get a key from https://ui.adsabs.harvard.edu/user/settings/token.

### Semantic Scholar API key

Semantic Scholar's API works without a key but is rate-limited. For heavier use, provide an API key either via the command line:

```bash
easybib ./paper --semantic-scholar-api-key your-key-here
```

Or as an environment variable:

```bash
export SEMANTIC_SCHOLAR_API_KEY="your-key-here"
```

Get a key from https://www.semanticscholar.org/product/api.

## How it works

1. Scans `.tex` files for `\cite{...}`, `\citep{...}`, `\citet{...}`, and related commands
2. Accepts INSPIRE texkeys (`Author:2020abc`), ADS bibcodes (`2016PhRvL.116f1102A`), and arXiv IDs (`2508.18080` or `hep-ph/9905318`); keys present in a `--bib-source` file are always accepted regardless of format
3. Optionally enforces that all keys are of a single type (`--key-type`)
4. Copies entries found in the local `--bib-source` file directly, without hitting the API
5. Fetches remaining entries from the preferred source, with automatic fallback
6. For INSPIRE/ADS keys: replaces the citation key to match what is in your `.tex` file
7. For arXiv IDs: keeps the entry's natural key and appends a `@misc` crossref stub so `\cite{arxiv_id}` resolves correctly
8. Detects duplicate entries (same paper cited under different keys) and skips them with a warning
9. Truncates long author lists
10. Skips keys already present in the output file (use `--fresh` to override)
11. Optionally prepends `@preamble` macro definitions for any AAS journal macros used in the output (`--aas-macros`)
