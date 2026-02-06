# easybib

Automatically fetch BibTeX entries from [INSPIRE](https://inspirehep.net/) and [NASA/ADS](https://ui.adsabs.harvard.edu/) for LaTeX projects.

easybib scans your `.tex` files for citation keys, looks them up on INSPIRE and/or ADS, and writes a `.bib` file with the results. It handles INSPIRE texkeys (e.g. `Author:2020abc`) and ADS bibcodes (e.g. `2016PhRvL.116f1102A`).

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
| `-s`, `--source` | Preferred source: `ads` (default), `inspire`, or `auto` |
| `-a`, `--max-authors` | Truncate author lists (default: 3, use 0 for no limit) |
| `-l`, `--list-keys` | List found citation keys and exit (no fetching) |
| `--fresh` | Ignore existing output file and start from scratch |

### Examples

```bash
# Scan a directory
easybib ./paper -s inspire

# Scan a single file
easybib paper.tex

# Use a custom output file
easybib ./paper -o paper.bib

# List citation keys without fetching
easybib ./paper -l

# Keep all authors
easybib ./paper -a 0
```

### ADS API key

When using ADS as the source (the default), set your API key:

```bash
export ADS_API_KEY="your-key-here"
```

Get one from https://ui.adsabs.harvard.edu/user/settings/token.

## How it works

1. Scans `.tex` files for `\cite{...}`, `\citep{...}`, `\citet{...}`, and related commands
2. Filters for keys containing `:` (INSPIRE/ADS format)
3. Fetches BibTeX from the preferred source, with automatic fallback
4. Replaces citation keys to match those used in your `.tex` files
5. Truncates long author lists
6. Skips keys already present in the output file (use `--fresh` to override)
