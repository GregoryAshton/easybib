"""Command-line interface for easybib."""

import configparser
import os
import argparse
from pathlib import Path

import requests

from easybib import __version__
from easybib.api import fetch_bibtex, fetch_bibtex_by_arxiv, fetch_aas_macros_sty
from easybib.conversions import replace_bibtex_key, truncate_authors, remove_collaboration_authors, extract_bibtex_key, extract_bibtex_fields, make_arxiv_crossref_stub, parse_aas_macros, find_used_macros, expand_aas_macros, sanitise_unicode
from easybib.core import check_key_type, detect_key_type, extract_cite_keys, extract_existing_bib_keys, load_bib_entries, is_ads_bibcode, is_arxiv_id


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
    if "semantic-scholar-api-key" in cfg:
        config_defaults["semantic_scholar_api_key"] = cfg["semantic-scholar-api-key"]
    if "key-type" in cfg:
        config_defaults["key_type"] = cfg["key-type"]
    if "aas-macros" in cfg:
        config_defaults["aas_macros"] = cfg["aas-macros"].lower() in ("true", "1", "yes")
    if "bib-source" in cfg:
        config_defaults["bib_source"] = cfg["bib-source"]
    if "prefer-api" in cfg:
        config_defaults["prefer_api"] = cfg["prefer-api"].lower() in ("true", "1", "yes")
    if "ascii" in cfg:
        config_defaults["ascii"] = cfg["ascii"].lower() in ("true", "1", "yes")
    if "remove-collaborations" in cfg:
        config_defaults["remove_collaborations"] = cfg["remove-collaborations"].lower() in ("true", "1", "yes")

    parser = argparse.ArgumentParser(
        description="Extract citations and download BibTeX from NASA/ADS, INSPIRE, and Semantic Scholar"
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
        choices=["ads", "inspire", "auto", "semantic-scholar"],
        default="ads",
        help="Preferred BibTeX source: 'ads' (default), 'inspire', 'auto' (based on key format), or 'semantic-scholar'",
    )
    parser.add_argument(
        "--ads-api-key",
        help="ADS API key (overrides ADS_API_KEY environment variable)",
    )
    parser.add_argument(
        "--semantic-scholar-api-key",
        help="Semantic Scholar API key (overrides SEMANTIC_SCHOLAR_API_KEY environment variable)",
    )
    parser.add_argument(
        "--key-type",
        choices=["inspire", "ads", "arxiv"],
        default=None,
        help="Enforce that all citation keys are of the given type: 'inspire', 'ads', or 'arxiv'",
    )
    parser.add_argument(
        "--aas-macros",
        action="store_true",
        default=False,
        help="Download AAS journal macros and expand them inline in the .bib file (e.g. {\\apj} becomes {ApJ})",
    )
    parser.add_argument(
        "--bib-source",
        default=None,
        metavar="FILE",
        help="Existing .bib file to copy entries from before falling back to API lookup",
    )
    parser.add_argument(
        "--prefer-api",
        action="store_true",
        default=False,
        help="When using --bib-source, fetch INSPIRE/ADS/arXiv keys from the API even if they exist in the source file",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        default=False,
        help="Replace Unicode characters in BibTeX entries with LaTeX/ASCII equivalents and remove any that cannot be converted",
    )
    parser.add_argument(
        "--remove-collaborations",
        action="store_true",
        default=False,
        help="Remove collaboration entries (e.g. 'The LIGO Collaboration') from author lists, provided at least one individual author remains",
    )

    # Apply config file defaults (CLI flags will still override)
    if config_defaults:
        parser.set_defaults(**config_defaults)

    args = parser.parse_args()

    # Load source bib file early so its keys are accepted during citation extraction
    source_entries = {}
    if args.bib_source:
        source_path = Path(args.bib_source)
        if not source_path.is_file():
            print(f"Error: --bib-source file not found: {args.bib_source}")
            return 1
        source_entries = load_bib_entries(source_path)
        print(f"Loaded {len(source_entries)} entries from {args.bib_source}")

    # Collect all citation keys
    input_path = Path(args.path)
    all_keys = set()
    all_warnings = []
    if input_path.is_file():
        tex_files = [input_path]
    else:
        tex_files = input_path.glob("**/*.tex")
    for tex_file in tex_files:
        keys, warnings = extract_cite_keys(tex_file, known_keys=source_entries.keys() if source_entries else None)
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

    # Enforce key type if requested
    if args.key_type:
        violations = check_key_type(all_keys, args.key_type)
        if violations:
            print(f"Error: --key-type={args.key_type} but {len(violations)} key(s) do not match:")
            for key, detected in sorted(violations):
                print(f"  '{key}' (detected as: {detected})")
            return 1

    # Check for ADS API key (not required if using --preferred-source inspire or semantic-scholar)
    api_key = args.ads_api_key or os.getenv("ADS_API_KEY")
    if not api_key and args.preferred_source not in ("inspire", "semantic-scholar"):
        print("Error: ADS_API_KEY environment variable not set")
        print("Get your API key from: https://ui.adsabs.harvard.edu/user/settings/token")
        print("(Or use --preferred-source inspire or --preferred-source semantic-scholar to fetch without an ADS key)")
        return 1

    # Check for Semantic Scholar API key (optional — API works without it at lower rate limits)
    ss_api_key = args.semantic_scholar_api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")

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

    # Warn if ADS bibcodes are present but no ADS API key is set
    if not api_key:
        ads_keys = [k for k in keys_to_fetch if is_ads_bibcode(k)]
        if ads_keys:
            print(
                f"Warning: {len(ads_keys)} ADS bibcode(s) found but no ADS_API_KEY is set. "
                "These will fall back to Semantic Scholar, which may hit rate limits. "
                "Set ADS_API_KEY for reliable results."
            )
            print()

    # Track identifiers seen this run to detect duplicate papers
    seen_source_keys = {}  # source key returned by API -> cite key that claimed it
    seen_eprints = {}      # arXiv eprint ID -> cite key
    seen_dois = {}         # DOI -> cite key
    duplicates = []        # (new_key, existing_key, reason)

    # Download BibTeX entries
    bibtex_entries = []
    not_found = []
    for key in sorted(keys_to_fetch):
        # Check the local source file first, unless --prefer-api overrides it for API-format keys
        if key in source_entries and not (args.prefer_api and detect_key_type(key) != "unknown"):
            print(f"Fetching {key}...", end=" ")
            bibtex = source_entries[key]
            if args.remove_collaborations:
                bibtex = remove_collaboration_authors(bibtex)
            bibtex = truncate_authors(bibtex, args.max_authors)
            bibtex_entries.append(bibtex)
            print("\u2713 local file")
            continue

        print(f"Fetching {key}...", end=" ")
        try:
            if is_arxiv_id(key):
                bibtex, source = fetch_bibtex_by_arxiv(key, api_key, args.preferred_source, ss_api_key=ss_api_key)
            else:
                bibtex, source = fetch_bibtex(key, api_key, args.preferred_source, ss_api_key=ss_api_key)

            if bibtex:
                source_key = extract_bibtex_key(bibtex)
                fields = extract_bibtex_fields(bibtex, "eprint", "doi")
                eprint = fields.get("eprint")
                doi = fields.get("doi")

                # Check whether this paper has already been fetched under another key
                dup_of = None
                dup_reason = None
                if source_key and source_key in seen_source_keys:
                    dup_of = seen_source_keys[source_key]
                    dup_reason = f"source key '{source_key}'"
                elif eprint and eprint in seen_eprints:
                    dup_of = seen_eprints[eprint]
                    dup_reason = f"arXiv ID '{eprint}'"
                elif doi and doi in seen_dois:
                    dup_of = seen_dois[doi]
                    dup_reason = f"DOI '{doi}'"

                if dup_of:
                    duplicates.append((key, dup_of, dup_reason))
                    print(f"\u26a0 Duplicate of '{dup_of}' ({dup_reason}), skipping")
                else:
                    if source_key:
                        seen_source_keys[source_key] = key
                    if eprint:
                        seen_eprints[eprint] = key
                    if doi:
                        seen_dois[doi] = key

                    if is_arxiv_id(key):
                        if args.remove_collaborations:
                            bibtex = remove_collaboration_authors(bibtex)
                        bibtex = truncate_authors(bibtex, args.max_authors)
                        bibtex_entries.append(bibtex)
                        if source_key:
                            bibtex_entries.append(make_arxiv_crossref_stub(key, source_key))
                    else:
                        bibtex = replace_bibtex_key(bibtex, key)
                        if args.remove_collaborations:
                            bibtex = remove_collaboration_authors(bibtex)
                        bibtex = truncate_authors(bibtex, args.max_authors)
                        bibtex_entries.append(bibtex)
                    print(f"\u2713 {source}")
            else:
                not_found.append(key)
                print("\u2717 Not found")
        except requests.exceptions.HTTPError as e:
            not_found.append(key)
            print(f"\u2717 {e}")

    # Build the full BibTeX content (existing + new)
    if existing_content and bibtex_entries:
        full_bibtex = existing_content + "\n\n" + "\n\n".join(bibtex_entries)
    elif existing_content:
        full_bibtex = existing_content
    else:
        full_bibtex = "\n\n".join(bibtex_entries)

    # Expand AAS journal macros inline if requested
    if args.aas_macros and full_bibtex:
        print("\nExpanding AAS journal macros...", end=" ")
        try:
            sty_content = fetch_aas_macros_sty()
            all_macros = parse_aas_macros(sty_content)
            used_macros = find_used_macros(full_bibtex, all_macros)
            if used_macros:
                full_bibtex = expand_aas_macros(full_bibtex, used_macros)
                print(f"\u2713 Expanded {len(used_macros)} macro(s): {', '.join(f'\\{n}' for n in sorted(used_macros))}")
            else:
                print("\u2713 No AAS macros found in output")
        except Exception as e:
            print(f"\u2717 Failed to fetch AAS macros: {e}")

    # Replace Unicode with LaTeX/ASCII equivalents if requested
    if args.ascii and full_bibtex:
        full_bibtex = sanitise_unicode(full_bibtex)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(full_bibtex)

    print(f"\nWrote {len(bibtex_entries)} new entries to {args.output}")

    if not_found:
        print(f"\nCould not find {len(not_found)} keys:")
        for key in not_found:
            print(f"  - {key}")

    if duplicates:
        print(f"\nWarning: {len(duplicates)} key(s) skipped — they refer to the same paper as an earlier key.")
        print("Please use a single key per paper in your .tex files:")
        for new_key, existing_key, reason in duplicates:
            print(f"  '{new_key}' duplicates '{existing_key}' ({reason})")
