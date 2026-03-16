"""BibTeX string transformations."""

import re
import unicodedata

# Direct Unicode → LaTeX/ASCII replacements
_UNICODE_TO_LATEX = {
    # Dashes
    '\u2010': '-',          # hyphen
    '\u2011': '-',          # non-breaking hyphen
    '\u2012': '--',         # figure dash
    '\u2013': '--',         # en dash
    '\u2014': '---',        # em dash
    '\u2015': '---',        # horizontal bar
    '\u2500': '--',         # box drawings light horizontal
    # Quotation marks
    '\u2018': '`',          # left single quotation mark
    '\u2019': "'",          # right single quotation mark
    '\u201c': '``',         # left double quotation mark
    '\u201d': "''",         # right double quotation mark
    # Spaces
    '\u00a0': ' ',          # non-breaking space
    '\u202f': ' ',          # narrow no-break space
    '\u2009': ' ',          # thin space
    # Common punctuation / symbols
    '\u2026': '{\\ldots}',  # ellipsis …
    '\u2020': '{\\dag}',    # dagger †
    '\u2021': '{\\ddag}',   # double dagger ‡
    '\u00a7': '{\\S}',      # section sign §
    '\u00b6': '{\\P}',      # pilcrow ¶
    '\u00b0': '$^\\circ$',  # degree °
    '\u2032': "$'$",        # prime ′
    '\u2033': "$''$",       # double prime ″
    # Mathematical operators
    '\u00b1': '$\\pm$',
    '\u00d7': '$\\times$',
    '\u00f7': '$\\div$',
    '\u2248': '$\\approx$',
    '\u223c': '$\\sim$',
    '\u2264': '$\\leq$',
    '\u2265': '$\\geq$',
    '\u226a': '$\\ll$',
    '\u226b': '$\\gg$',
    '\u2272': '$\\lesssim$',
    '\u2273': '$\\gtrsim$',
    '\u221e': '$\\infty$',
    '\u2202': '$\\partial$',
    '\u2207': '$\\nabla$',
    '\u221a': '$\\sqrt{}$',
    '\u222b': '$\\int$',
    '\u2211': '$\\sum$',
    '\u220f': '$\\prod$',
    '\u2192': '$\\rightarrow$',
    '\u2190': '$\\leftarrow$',
    '\u2194': '$\\leftrightarrow$',
    '\u21d2': '$\\Rightarrow$',
    '\u2208': '$\\in$',
    '\u2282': '$\\subset$',
    '\u2286': '$\\subseteq$',
    # Superscripts
    '\u00b9': '$^1$',
    '\u00b2': '$^2$',
    '\u00b3': '$^3$',
    '\u2070': '$^0$',
    '\u2074': '$^4$',
    '\u2075': '$^5$',
    '\u2076': '$^6$',
    '\u2077': '$^7$',
    '\u2078': '$^8$',
    '\u2079': '$^9$',
    # Subscripts
    '\u2080': '$_0$',
    '\u2081': '$_1$',
    '\u2082': '$_2$',
    '\u2083': '$_3$',
    '\u2084': '$_4$',
    '\u2085': '$_5$',
    '\u2086': '$_6$',
    '\u2087': '$_7$',
    '\u2088': '$_8$',
    '\u2089': '$_9$',
    # Greek lowercase
    '\u03b1': '$\\alpha$',
    '\u03b2': '$\\beta$',
    '\u03b3': '$\\gamma$',
    '\u03b4': '$\\delta$',
    '\u03b5': '$\\epsilon$',
    '\u03b6': '$\\zeta$',
    '\u03b7': '$\\eta$',
    '\u03b8': '$\\theta$',
    '\u03b9': '$\\iota$',
    '\u03ba': '$\\kappa$',
    '\u03bb': '$\\lambda$',
    '\u03bc': '$\\mu$',
    '\u03bd': '$\\nu$',
    '\u03be': '$\\xi$',
    '\u03c0': '$\\pi$',
    '\u03c1': '$\\rho$',
    '\u03c3': '$\\sigma$',
    '\u03c4': '$\\tau$',
    '\u03c5': '$\\upsilon$',
    '\u03c6': '$\\phi$',
    '\u03c7': '$\\chi$',
    '\u03c8': '$\\psi$',
    '\u03c9': '$\\omega$',
    # Greek uppercase
    '\u0393': '$\\Gamma$',
    '\u0394': '$\\Delta$',
    '\u0398': '$\\Theta$',
    '\u039b': '$\\Lambda$',
    '\u039e': '$\\Xi$',
    '\u03a0': '$\\Pi$',
    '\u03a3': '$\\Sigma$',
    '\u03a5': '$\\Upsilon$',
    '\u03a6': '$\\Phi$',
    '\u03a8': '$\\Psi$',
    '\u03a9': '$\\Omega$',
    # Astronomical symbols
    '\u2609': '$\\odot$',   # ☉ sun
    '\u2299': '$\\odot$',   # ⊙ circled dot operator
    '\u2295': '$\\oplus$',  # ⊕ earth / direct sum
    '\u2297': '$\\otimes$', # ⊗ circled times
}

# Unicode combining characters → LaTeX accent command letter
# Used to convert decomposed accented characters, e.g. e + ́ → {\'e}
_COMBINING_TO_ACCENT = {
    '\u0300': '`',   # grave:      è
    '\u0301': "'",   # acute:      é
    '\u0302': '^',   # circumflex: ê
    '\u0303': '~',   # tilde:      ñ
    '\u0308': '"',   # diaeresis:  ë
    '\u0307': '.',   # dot above:  ż
    '\u0304': '=',   # macron:     ā
    '\u0306': 'u',   # breve:      ă
    '\u030a': 'r',   # ring above: å
    '\u030b': 'H',   # double acute: ő
    '\u030c': 'v',   # caron:      š
    '\u0323': 'd',   # dot below:  ạ
    '\u0327': 'c',   # cedilla:    ç
    '\u0331': 'b',   # macron below
}


def sanitise_unicode(text):
    """Replace non-ASCII characters in a BibTeX string with LaTeX/ASCII equivalents.

    Known characters are converted to LaTeX commands or ASCII. Accented Latin
    characters are converted to LaTeX accent commands (e.g. é → {\\'e}).
    Anything that cannot be converted is removed.
    """
    result = []
    for char in text:
        if ord(char) < 128:
            result.append(char)
        elif char in _UNICODE_TO_LATEX:
            result.append(_UNICODE_TO_LATEX[char])
        else:
            # Try NFD decomposition: base char + combining accent
            nfd = unicodedata.normalize('NFD', char)
            if len(nfd) == 2 and ord(nfd[0]) < 128 and nfd[1] in _COMBINING_TO_ACCENT:
                cmd = _COMBINING_TO_ACCENT[nfd[1]]
                result.append('{\\' + cmd + '{' + nfd[0] + '}}')
            elif len(nfd) >= 1 and ord(nfd[0]) < 128:
                # Keep the base ASCII character, drop the combining mark(s)
                result.append(nfd[0])
            # else: drop the character entirely
    return ''.join(result)


def replace_bibtex_key(bibtex, new_key):
    """Replace the citation key in a BibTeX entry with a new key."""
    # Match the entry type and key: @article{old_key,
    pattern = r"(@\w+\s*\{)\s*([^,\s]+)\s*,"
    return re.sub(pattern, rf"\g<1>{new_key},", bibtex, count=1)


def extract_bibtex_fields(bibtex, *field_names):
    """Extract field values from a BibTeX entry string.

    Returns a dict mapping field name to value for each field found.
    Handles both double-quoted and brace-delimited values.
    """
    result = {}
    for field in field_names:
        pattern = rf'^\s*{re.escape(field)}\s*=\s*(?:"([^"]+)"|\{{([^}}]+)\}})'
        match = re.search(pattern, bibtex, re.MULTILINE | re.IGNORECASE)
        if match:
            result[field] = (match.group(1) or match.group(2)).strip()
    return result


def extract_bibtex_key(bibtex):
    """Extract the citation key from a BibTeX entry string."""
    match = re.search(r'@\w+\s*\{\s*([^,\s]+)\s*,', bibtex)
    if match:
        return match.group(1)
    return None


def make_arxiv_crossref_stub(arxiv_id, bibtex_key):
    """Create a BibTeX @misc entry that cross-references the main entry."""
    return f"@misc{{{arxiv_id},\n  crossref = {{{bibtex_key}}}\n}}"


def parse_aas_macros(sty_content):
    """Parse AAS macro definitions from .sty file content.

    Returns a dict mapping macro name (without backslash) to its journal string.
    For example: {'apj': 'ApJ', 'mnras': 'MNRAS', ...}
    """
    macros = {}

    # Match \def\macroname{\ref@jnl{value}}
    for match in re.finditer(r'\\def\\(\w+)\{\\ref@jnl\{([^}]+)\}\}', sty_content):
        macros[match.group(1)] = match.group(2)

    # Match alias definitions like \def\alias{\original} or \let\alias\original
    for match in re.finditer(r'\\(?:def|let)\\(\w+)[{ \\]\\(\w+)[}]?', sty_content):
        alias, original = match.group(1), match.group(2)
        if alias not in macros and original in macros:
            macros[alias] = macros[original]

    return macros


def find_used_macros(bibtex_text, macros):
    """Find which AAS macros are used in the given BibTeX text.

    macros: dict mapping macro name (without backslash) to journal string.
    Returns a dict of {macro_name: journal_string} for macros that appear in the text.
    """
    used = {}
    for name, value in macros.items():
        # Match \macroname not immediately followed by another word character
        if re.search(r'\\' + re.escape(name) + r'(?!\w)', bibtex_text):
            used[name] = value
    return used


def expand_aas_macros(bibtex, macros):
    """Expand AAS journal macros inline in a BibTeX string.

    Replaces occurrences of \\macroname (not followed by a word character)
    with their plain-text expansion. For example, {\\apj} becomes {ApJ}.
    """
    for name, value in macros.items():
        bibtex = re.sub(r'\\' + re.escape(name) + r'(?!\w)', value, bibtex)
    return bibtex


def remove_collaboration_authors(bibtex):
    """Remove collaboration entries from the author list in a BibTeX entry.

    Only removes collaboration entries (authors whose name contains 'Collaboration',
    case-insensitive) if at least one non-collaboration author remains.
    """
    author_pattern = r"(\s*author\s*=\s*\{)(.+?)(\},?\s*\n)"
    match = re.search(author_pattern, bibtex, re.IGNORECASE | re.DOTALL)

    if not match:
        return bibtex

    prefix = match.group(1)
    authors_str = match.group(2)
    suffix = match.group(3)

    authors = [a.strip() for a in re.split(r"\s+and\s+", authors_str)]
    non_collab = [a for a in authors if not re.search(r'\bcollaboration\b', a, re.IGNORECASE)]

    if not non_collab or len(non_collab) == len(authors):
        return bibtex

    new_authors_str = " and ".join(non_collab)
    new_author_field = f"{prefix}{new_authors_str}{suffix}"
    return bibtex[: match.start()] + new_author_field + bibtex[match.end() :]


def truncate_authors(bibtex, max_authors):
    """Truncate the author list in a BibTeX entry to max_authors.

    If there are more than max_authors, keep the first max_authors and add "and others".
    If max_authors is None or 0, no truncation is performed.
    """
    if not max_authors:
        return bibtex

    # Match the author field (handles multiline author fields)
    author_pattern = r"(\s*author\s*=\s*\{)(.+?)(\},?\s*\n)"
    match = re.search(author_pattern, bibtex, re.IGNORECASE | re.DOTALL)

    if not match:
        return bibtex

    prefix = match.group(1)
    authors_str = match.group(2)
    suffix = match.group(3)

    # Split authors by " and " (BibTeX standard separator)
    authors = [a.strip() for a in re.split(r"\s+and\s+", authors_str)]

    if len(authors) <= max_authors:
        return bibtex

    # Keep first max_authors and add "others"
    truncated_authors = authors[:max_authors] + ["others"]
    new_authors_str = " and ".join(truncated_authors)

    # Replace the author field
    new_author_field = f"{prefix}{new_authors_str}{suffix}"
    return bibtex[: match.start()] + new_author_field + bibtex[match.end() :]
