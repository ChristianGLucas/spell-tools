"""Shared helpers for spell-tools.

Thin, deterministic glue over symspellpy (MIT) — Wolf Garbe's SymSpell
algorithm — loaded once per process against the frequency dictionaries
bundled in this repo's data/ directory (no runtime download). This module
owns the single SymSpell singleton, input-bound validation, and the shared
error contract, so every node shares one vocabulary.

symspellpy is deliberately permissive at its edges (an empty/blank string
handed to `lookup`/`lookup_compound` returns bogus, non-empty results
instead of an error; `word_segmentation("")` raises IndexError outright).
Every node in this package validates its input BEFORE calling into the
library, rather than trusting the library to reject malformed input itself.
"""

import os
import re

from symspellpy import SymSpell, Verbosity

from gen.messages_pb2 import WordCandidate

# SymSpell is initialized with this as its compiled-in maximum; a caller
# cannot request a larger max_edit_distance than this (the library raises
# ValueError "distance too large" if asked to, which we pre-empt). This is
# an algorithm-correctness bound (baked into the SymSpell instance itself
# at construction), not a payload/DoS one, so it stays.
MAX_EDIT_DISTANCE = 2
DEFAULT_EDIT_DISTANCE = 2

DEFAULT_TOP_N = 5

DEFAULT_SEGMENT_WORD_LEN = 20

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_DICT_PATH = os.path.join(_DATA_DIR, "frequency_dictionary_en_82_765.txt")
_BIGRAM_PATH = os.path.join(_DATA_DIR, "frequency_bigramdictionary_en_243_342.txt")

_TOKEN_RE = re.compile(r"[A-Za-z']+")


class RequestError(Exception):
    """Raised for a rejected request; the node turns it into a structured error."""


# ── SymSpell singleton ─────────────────────────────────────────────────────
# Loading the dictionaries takes roughly a second; loaded once per process
# and reused across every invocation the warm container serves.
_symspell_instance = None


def get_symspell() -> SymSpell:
    global _symspell_instance
    if _symspell_instance is None:
        sym = SymSpell(max_dictionary_edit_distance=MAX_EDIT_DISTANCE, prefix_length=7)
        if not sym.load_dictionary(_DICT_PATH, term_index=0, count_index=1):
            raise RuntimeError(f"failed to load bundled dictionary at {_DICT_PATH}")
        if not sym.load_bigram_dictionary(_BIGRAM_PATH, term_index=0, count_index=2):
            raise RuntimeError(f"failed to load bundled bigram dictionary at {_BIGRAM_PATH}")
        _symspell_instance = sym
    return _symspell_instance


# ── Validation ──────────────────────────────────────────────────────────────

def check_text(text: str, label: str = "text") -> str:
    """Reject blank/whitespace-only text. Returns the input unchanged (never
    mutated) so callers can chain this in an expression."""
    if not text or not text.strip():
        raise RequestError(f"{label} must not be blank")
    return text


def check_single_token(text: str, label: str = "text") -> str:
    """Reject text containing whitespace — CorrectWord/CheckWord operate on
    exactly one token; a caller who wants phrase-level correction should use
    CorrectPhrase or FindMisspellings instead."""
    check_text(text, label)
    if re.search(r"\s", text):
        raise RequestError(
            f"{label} must be a single word with no whitespace "
            "(use CorrectPhrase or FindMisspellings for multi-word input)"
        )
    return text


def resolve_max_edit_distance(input_msg) -> int:
    if not input_msg.HasField("max_edit_distance"):
        return DEFAULT_EDIT_DISTANCE
    v = input_msg.max_edit_distance
    if v < 0 or v > MAX_EDIT_DISTANCE:
        raise RequestError(
            f"max_edit_distance must be between 0 and {MAX_EDIT_DISTANCE} (got {v})"
        )
    return v


def resolve_top_n(input_msg) -> int:
    if not input_msg.HasField("top_n"):
        return DEFAULT_TOP_N
    v = input_msg.top_n
    if v < 1:
        raise RequestError(f"top_n must be at least 1 (got {v})")
    return v


def resolve_max_segment_length(input_msg) -> int:
    if not input_msg.HasField("max_segment_length"):
        return DEFAULT_SEGMENT_WORD_LEN
    v = input_msg.max_segment_length
    if v < 1:
        raise RequestError(f"max_segment_length must be at least 1 (got {v})")
    return v


def tokenize(text: str):
    """Alphabetic word tokens (letters and apostrophes only — punctuation and
    digits are separators, not part of a token), used by FindMisspellings to
    report a stable 0-based token index per flagged word without treating
    ordinary sentence punctuation as a spelling error."""
    return [m.group(0) for m in _TOKEN_RE.finditer(text)]


def to_candidates(suggestions, top_n: int):
    return [
        WordCandidate(word=s.term, edit_distance=s.distance, frequency=s.count)
        for s in suggestions[:top_n]
    ]
