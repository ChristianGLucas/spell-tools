from gen.messages_pb2 import SpellQuery, PhraseCorrection
from gen.axiom_context import AxiomContext
from nodes.lib import (
    RequestError,
    check_text,
    resolve_max_edit_distance,
    get_symspell,
)


def correct_phrase(ax: AxiomContext, input: SpellQuery) -> PhraseCorrection:
    """Correct an entire phrase or sentence, including compound errors —
    multiple misspelled words, and a single missing/extra space that merges
    or splits exactly two adjacent words (e.g. "the qick brown fox jum ped"
    -> "the quick brown fox jumped"; "whereis the exit" -> "where is the
    exit"). Uses SymSpell's compound-aware lookup, which considers bigram
    frequency (word pairs) from the bundled corpus to pick the contextually
    likeliest correction rather than correcting each word in isolation.
    NOTE: this does not reliably reconstruct a multi-word run-together blob
    (three or more merged words, e.g. "thequickbrown") within
    max_edit_distance — use SegmentText for that; CorrectPhrase's space
    recovery is bounded to a single two-word merge/split per edit-distance
    budget. `max_edit_distance` (0-2, default 2) bounds the per-word
    correction distance; `edit_distance` in the result is the total summed
    across the whole phrase. Casing is preserved from the input (e.g. a
    capitalized sentence-initial word stays capitalized in `corrected`) via
    SymSpell's case-transfer option, so matching is effectively
    case-insensitive without flattening the output to lowercase.
    Deterministic; blank input returns a structured error instead of
    crashing.
    """
    try:
        text = check_text(input.text, "text")
        max_edit_distance = resolve_max_edit_distance(input)
    except RequestError as e:
        return PhraseCorrection(error=str(e))

    sym = get_symspell()
    suggestions = sym.lookup_compound(text, max_edit_distance=max_edit_distance, transfer_casing=True)
    best = suggestions[0]
    return PhraseCorrection(input=text, corrected=best.term, edit_distance=best.distance)
