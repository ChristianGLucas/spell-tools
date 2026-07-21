from symspellpy import Verbosity

from gen.messages_pb2 import SpellQuery, WordCorrection
from gen.axiom_context import AxiomContext
from nodes.lib import (
    RequestError,
    check_single_token,
    resolve_max_edit_distance,
    resolve_top_n,
    get_symspell,
    to_candidates,
)


def correct_word(ax: AxiomContext, input: SpellQuery) -> WordCorrection:
    """Correct a single misspelled word to its most likely intended word(s).
    Looks up `text` (a single token — no whitespace) against the bundled
    SymSpell frequency dictionary and returns up to `top_n` candidates whose
    Damerau-Levenshtein edit distance from the input is at most
    `max_edit_distance` (0-2, default 2), ranked closest-and-most-frequent
    first. A correctly spelled word still returns itself as the first
    (distance-0) candidate, followed by nearby alternatives. Matching is
    case-insensitive (the bundled dictionary is entirely lowercase, and
    matching against it case-sensitively would silently misjudge distances
    for capitalized input — e.g. sentence-initial words); candidate words
    are therefore returned in their canonical lowercase dictionary form.
    Deterministic; blank, multi-word, or oversized input returns a
    structured error instead of crashing.
    """
    try:
        text = check_single_token(input.text, "text")
        max_edit_distance = resolve_max_edit_distance(input)
        top_n = resolve_top_n(input)
    except RequestError as e:
        return WordCorrection(error=str(e))

    sym = get_symspell()
    suggestions = sym.lookup(text.lower(), Verbosity.ALL, max_edit_distance=max_edit_distance)
    return WordCorrection(input=text, candidates=to_candidates(suggestions, top_n))
