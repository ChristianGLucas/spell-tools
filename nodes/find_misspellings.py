from symspellpy import Verbosity

from gen.messages_pb2 import SpellQuery, MisspellingReport, FlaggedWord
from gen.axiom_context import AxiomContext
from nodes.lib import (
    RequestError,
    check_text,
    resolve_max_edit_distance,
    resolve_top_n,
    get_symspell,
    tokenize,
    to_candidates,
)


def find_misspellings(ax: AxiomContext, input: SpellQuery) -> MisspellingReport:
    """Tokenize a phrase and flag every word not found in the bundled
    dictionary, each with up to `top_n` ranked correction candidates within
    `max_edit_distance` (0-2, default 2) — the "spellcheck as you type"
    shape, as opposed to CorrectPhrase's single committed rewrite. Tokens are
    alphabetic words (letters and apostrophes only); punctuation and digits
    are separators, not spelling errors. `index` on each flagged word is its
    0-based position among the phrase's word tokens. The membership check is
    case-insensitive. Deterministic; blank input returns a structured error
    instead of crashing.
    """
    try:
        text = check_text(input.text, "text")
        max_edit_distance = resolve_max_edit_distance(input)
        top_n = resolve_top_n(input)
    except RequestError as e:
        return MisspellingReport(error=str(e))

    sym = get_symspell()
    tokens = tokenize(text)
    flagged = []
    for i, word in enumerate(tokens):
        if sym.words.get(word.lower()) is not None:
            continue
        suggestions = sym.lookup(word.lower(), Verbosity.ALL, max_edit_distance=max_edit_distance)
        flagged.append(FlaggedWord(word=word, index=i, suggestions=to_candidates(suggestions, top_n)))

    return MisspellingReport(input=text, flagged=flagged, word_count=len(tokens))
