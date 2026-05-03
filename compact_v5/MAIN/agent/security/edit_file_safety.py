"""Block C C-3..C-8 — edit_file safety helpers.

Adapters of Runnable's `FileEditTool/utils.ts` (R1 #115/116/121/122/123)
and `FileEditTool.ts:179-181/289-311` (UNC path skip + Windows
content-fallback staleness). Each helper is small and self-contained
so `tools/edit_file.py` can call them without growing.

Helpers:
  C-3 normalize_quotes          curly→straight quote folding for match
  C-4 preserve_quote_style      re-wrap new_string in the original quote style
  C-5 detect_utf16_bom          recognize Notepad-saved UTF-16 LE files
  C-6 is_unc_path_windows       skip `\\\\server\\share\\...` on Windows
  C-7 normalize_line_endings    \\r\\n → \\n for diff; preserve original on write
  C-8 staleness_check           Windows OneDrive/AV mtime bump → content fallback

PORT_LOG: see #060.
"""
from __future__ import annotations

import os
import sys
from typing import Optional, Tuple


# ============================================================
# C-3 — Quote normalization (curly → straight) for matching
# ============================================================

# Common Unicode "smart quotes" → ASCII equivalents.
_QUOTE_MAP = {
    "‘": "'",  # LEFT SINGLE QUOTATION MARK
    "’": "'",  # RIGHT SINGLE QUOTATION MARK
    "‚": "'",  # SINGLE LOW-9 QUOTATION MARK
    "‛": "'",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    "“": '"',  # LEFT DOUBLE QUOTATION MARK
    "”": '"',  # RIGHT DOUBLE QUOTATION MARK
    "„": '"',  # DOUBLE LOW-9 QUOTATION MARK
    "‟": '"',  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    "«": '"',  # LEFT-POINTING DOUBLE ANGLE
    "»": '"',  # RIGHT-POINTING DOUBLE ANGLE
}


def normalize_quotes(text: str) -> str:
    """Fold curly / Unicode quotes to straight ASCII quotes.

    Per Runnable FileEditTool/utils.ts:73-93 (R1 #115). Used on BOTH
    the haystack and the search needle so a file containing curly
    quotes can be matched by an old_string with straight quotes (the
    common case when models emit edit_file calls).
    """
    if not text:
        return text
    for src, dst in _QUOTE_MAP.items():
        if src in text:
            text = text.replace(src, dst)
    return text


# ============================================================
# C-4 — Re-wrap new_string in the original quote style
# ============================================================

def preserve_quote_style(original: str, new_text: str) -> str:
    """If `original` uses curly quotes, re-wrap `new_text` to match.

    Heuristic: if any curly quote appears in `original` and the
    corresponding straight quote appears in `new_text`, replace one for
    the other. Per Runnable FileEditTool/utils.ts:104-120 (R1 #116).

    Conservative: only flips when `original` has a curly variant we
    know the file uses; otherwise returns `new_text` unchanged.
    """
    if not original or not new_text:
        return new_text
    # Look at curly→straight pairs and determine which (if any) the
    # original prefers.
    flips: list = []
    if "’" in original and "'" in new_text:
        flips.append(("'", "’"))
    if "”" in original and '"' in new_text:
        flips.append(('"', "”"))
    for src, dst in flips:
        new_text = new_text.replace(src, dst)
    return new_text


# ============================================================
# C-5 — UTF-16 LE BOM detection (Notepad-saved files)
# ============================================================

_UTF16_LE_BOM = b"\xff\xfe"
_UTF16_BE_BOM = b"\xfe\xff"
_UTF8_BOM = b"\xef\xbb\xbf"


def detect_utf16_bom(filepath: str) -> Optional[str]:
    """Return 'utf-16-le' / 'utf-16-be' / 'utf-8-sig' / None.

    Files saved with Notepad (Windows) often carry a UTF-16 LE BOM.
    Edit tools must read with the matching encoding or string matching
    silently fails. Per Runnable FileEditTool.ts:208-214 (R1 #121).
    """
    try:
        with open(filepath, "rb") as f:
            head = f.read(3)
    except OSError:
        return None
    if head.startswith(_UTF16_LE_BOM):
        return "utf-16-le"
    if head.startswith(_UTF16_BE_BOM):
        return "utf-16-be"
    if head.startswith(_UTF8_BOM):
        return "utf-8-sig"
    return None


# ============================================================
# C-6 — UNC path skip on Windows (NTLM credential leak)
# ============================================================

def is_unc_path_windows(path: str) -> bool:
    """True iff `path` is a UNC `\\\\server\\share\\...` path on Windows.

    Reading a UNC path causes Windows to authenticate against the
    remote SMB host with the current user's NTLM credentials, which
    leaks them. Edit tools should refuse UNC paths on Windows.
    Per Runnable FileEditTool.ts:179-181 (R1 #123).

    Codex Block-C iter-1 finding #4 (MEDIUM) lock: exclude Windows
    extended/device prefixes `\\\\?\\` and `\\\\.\\` — those are
    namespaced local paths, NOT remote UNC. They route to the local
    NT object manager, not SMB, so they don't leak credentials.
    """
    if sys.platform != "win32" and os.name != "nt":
        return False
    if not path:
        return False
    # Reject only true server-share UNC forms; allow extended-path
    # and device prefixes (\\?\, \\.\) which are local.
    if path.startswith(("\\\\?\\", "\\\\.\\", "//?/", "//./")):
        return False
    return path.startswith(("\\\\", "//"))


# ============================================================
# C-7 — \r\n ↔ \n round-trip preservation
# ============================================================

def normalize_line_endings(text: str) -> Tuple[str, str]:
    """Return (normalized, original_eol) where eol ∈ {'\\n', '\\r\\n', '\\r'}.

    Used to do diff-matching in LF-only space while preserving the
    file's native line-ending on write. Per Runnable FileEditTool/utils
    (R1 #122).
    """
    if "\r\n" in text:
        return text.replace("\r\n", "\n"), "\r\n"
    if "\r" in text and "\n" not in text:
        return text.replace("\r", "\n"), "\r"
    return text, "\n"


def restore_line_endings(text: str, eol: str) -> str:
    """Inverse of normalize_line_endings — write side."""
    if eol == "\n":
        return text
    return text.replace("\n", eol)


# ============================================================
# C-8 — Windows staleness fallback (OneDrive / AV touch mtime)
# ============================================================

def is_staleness_false_positive(
    filepath: str,
    last_read_mtime: float,
    last_read_content: Optional[str] = None,
) -> bool:
    """True iff the file's mtime appears stale but content is unchanged.

    On Windows, OneDrive sync, antivirus scans, and indexers can touch
    a file's mtime without changing its content. A naive staleness gate
    based on mtime alone falsely fails edits on those files. Per
    Runnable FileEditTool.ts:289-311 (R1 #111): if mtime drifted, fall
    back to a content compare against the previously-read snapshot.

    Returns True iff the gate should treat the file as "still fresh".
    """
    if last_read_content is None:
        return False
    try:
        current_mtime = os.path.getmtime(filepath)
    except OSError:
        return False
    if current_mtime == last_read_mtime:
        return True  # not stale at all
    # mtime drifted — content compare.
    enc = detect_utf16_bom(filepath) or "utf-8"
    try:
        with open(filepath, "r", encoding=enc, errors="replace") as f:
            current = f.read()
    except OSError:
        return False
    return current == last_read_content


__all__ = [
    "normalize_quotes",
    "preserve_quote_style",
    "detect_utf16_bom",
    "is_unc_path_windows",
    "normalize_line_endings",
    "restore_line_endings",
    "is_staleness_false_positive",
]
