from gen.messages_pb2 import SpellQuery, WordCheck
from gen.axiom_context import AxiomContext
from nodes.lib import RequestError, check_single_token, get_symspell


def check_word(ax: AxiomContext, input: SpellQuery) -> WordCheck:
    """Check whether a single word (`text` — no whitespace) exists verbatim
    in the bundled dictionary, and if so, its corpus frequency. This is a
    fast, exact existence check — no fuzzy matching, no candidate search —
    distinct from CorrectWord, which searches for near-miss suggestions
    whether or not the word is known. The membership check is
    case-insensitive (the bundled dictionary is entirely lowercase); `word`
    in the result echoes the input exactly as given. Deterministic; blank or
    multi-word input returns a structured error instead of crashing.
    """
    try:
        text = check_single_token(input.text, "text")
    except RequestError as e:
        return WordCheck(error=str(e))

    sym = get_symspell()
    frequency = sym.words.get(text.lower())
    if frequency is None:
        return WordCheck(word=text, known=False, frequency=0)
    return WordCheck(word=text, known=True, frequency=frequency)
