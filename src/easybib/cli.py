"""Command-line interface for easybib."""

import os
import argparse
from pathlib import Path

from easybib.core import (
    extract_cite_keys,
    extract_existing_bib_keys,
    fetch_bibtex,
    replace_bibtex_key,
    truncate_authors,
)


def main():
    parser = argparse.ArgumentParser(
        description="Extract citations and download BibTeX from NASA/ADS"
    )
    parser.add_argument("directory", help="Directory containing LaTeX files")
    parser.add_argument(
        "-o", "--output", default="references.bib", help="Output BibTeX file (existing entries are retained)"
    )
    parser.add_argument(
        "-a",
        "--max-authors",
        type=int,
        default=3,
        help="Maximum number of authors before truncating with 'and others' (default: 3, use 0 for no limit)",
    )
    parser.add_argument(
        "-l",
        "--list-keys",
        action="store_true",
        help="List citation keys found in LaTeX files and exit (no lookup)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start from scratch, ignoring existing output file",
    )
    parser.add_argument(
        "-s",
        "--source",
        choices=["ads", "inspire", "auto"],
        default="ads",
        help="Preferred BibTeX source: 'ads' (default), 'inspire', or 'auto' (based on key format)",
    )
    args = parser.parse_args()

    # Collect all citation keys
    tex_dir = Path(args.directory)
    all_keys = set()
    all_warnings = []
    for tex_file in tex_dir.glob("**/*.tex"):
        keys, warnings = extract_cite_keys(tex_file)
        all_keys.update(keys)
        all_warnings.extend(warnings)

    # Print warnings for invalid keys
    if all_warnings:
        print("Warnings:")
        for warning in all_warnings:
            print(f"  {warning}")
        print()

    print(f"Found {len(all_keys)} unique citation keys")

    # If --list-keys, print keys and exit
    if args.list_keys:
        for key in sorted(all_keys):
            print(key)
        return 0

    # Check for ADS API key (not required if using --source inspire)
    api_key = os.getenv("ADS_API_KEY")
    if not api_key and args.source != "inspire":
        print("Error: ADS_API_KEY environment variable not set")
        print("Get your API key from: https://ui.adsabs.harvard.edu/user/settings/token")
        print("(Or use --source inspire to fetch from INSPIRE without an ADS key)")
        return 1

    # Check for existing bib file and determine which keys to fetch
    output_path = Path(args.output)
    existing_content = ""
    if not args.fresh and output_path.exists():
        existing_keys = extract_existing_bib_keys(output_path)
        keys_to_fetch = all_keys - existing_keys
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read().strip()
        print(f"Found {len(existing_keys)} existing entries in {args.output}")
        print(f"Fetching {len(keys_to_fetch)} new keys")
    else:
        keys_to_fetch = all_keys
        if args.fresh and output_path.exists():
            print(f"Starting fresh (ignoring existing {args.output})")

    # Download BibTeX entries
    bibtex_entries = []
    not_found = []
    for key in sorted(keys_to_fetch):
        print(f"Fetching {key}...", end=" ")
        bibtex, source = fetch_bibtex(key, api_key, args.source)
        if bibtex:
            bibtex = replace_bibtex_key(bibtex, key)
            bibtex = truncate_authors(bibtex, args.max_authors)
            bibtex_entries.append(bibtex)
            print(f"\u2713 {source}")
        else:
            not_found.append(key)
            print("\u2717 Not found")

    # Write output (append new entries to existing content)
    with open(args.output, "w", encoding="utf-8") as f:
        if existing_content and bibtex_entries:
            f.write(existing_content + "\n\n" + "\n\n".join(bibtex_entries))
        elif existing_content:
            f.write(existing_content)
        else:
            f.write("\n\n".join(bibtex_entries))

    print(f"\nWrote {len(bibtex_entries)} new entries to {args.output}")

    if not_found:
        print(f"\nCould not find {len(not_found)} keys:")
        for key in not_found:
            print(f"  - {key}")
