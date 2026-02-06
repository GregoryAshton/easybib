"""Command-line interface for easybib."""

import configparser
import os
import argparse
from pathlib import Path

from easybib import __version__
from easybib.core import (
    extract_cite_keys,
    extract_existing_bib_keys,
    fetch_bibtex,
    replace_bibtex_key,
    truncate_authors,
)


def load_config(config_path):
    """Read an INI config file and return a dict from the [easybib] section."""
    path = Path(config_path).expanduser()
    if not path.is_file():
        return {}
    config = configparser.ConfigParser()
    config.read(path)
    if "easybib" not in config:
        return {}
    return dict(config["easybib"])


def main():
    # First pass: extract --config so we know which config file to load
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "--config",
        default="~/.easybib.config",
        help="Path to config file (default: ~/.easybib.config)",
    )
    pre_args, _ = pre_parser.parse_known_args()

    # Load config and build defaults
    cfg = load_config(pre_args.config)
    config_defaults = {}
    if "output" in cfg:
        config_defaults["output"] = cfg["output"]
    if "max-authors" in cfg:
        config_defaults["max_authors"] = int(cfg["max-authors"])
    if "preferred-source" in cfg:
        config_defaults["preferred_source"] = cfg["preferred-source"]
    if "ads-api-key" in cfg:
        config_defaults["ads_api_key"] = cfg["ads-api-key"]

    parser = argparse.ArgumentParser(
        description="Extract citations and download BibTeX from NASA/ADS"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("path", help="LaTeX file or directory containing LaTeX files")
    parser.add_argument(
        "--config",
        default="~/.easybib.config",
        help="Path to config file (default: ~/.easybib.config)",
    )
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
        "--preferred-source",
        choices=["ads", "inspire", "auto"],
        default="ads",
        help="Preferred BibTeX source: 'ads' (default), 'inspire', or 'auto' (based on key format)",
    )
    parser.add_argument(
        "--ads-api-key",
        help="ADS API key (overrides ADS_API_KEY environment variable)",
    )

    # Apply config file defaults (CLI flags will still override)
    if config_defaults:
        parser.set_defaults(**config_defaults)

    args = parser.parse_args()

    # Collect all citation keys
    input_path = Path(args.path)
    all_keys = set()
    all_warnings = []
    if input_path.is_file():
        tex_files = [input_path]
    else:
        tex_files = input_path.glob("**/*.tex")
    for tex_file in tex_files:
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

    # Check for ADS API key (not required if using --preferred-source inspire)
    api_key = args.ads_api_key or os.getenv("ADS_API_KEY")
    if not api_key and args.preferred_source != "inspire":
        print("Error: ADS_API_KEY environment variable not set")
        print("Get your API key from: https://ui.adsabs.harvard.edu/user/settings/token")
        print("(Or use --preferred-source inspire to fetch from INSPIRE without an ADS key)")
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
        bibtex, source = fetch_bibtex(key, api_key, args.preferred_source)
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
