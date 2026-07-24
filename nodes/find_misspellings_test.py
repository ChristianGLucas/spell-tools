from gen.messages_pb2 import SpellQuery
from nodes.find_misspellings import find_misspellings
from nodes.testkit import StubContext

AX = StubContext()


def test_flags_only_misspelled_words_with_correct_indices():
    r = find_misspellings(AX, SpellQuery(text="the qick brown fox"))
    assert r.error == ""
    assert r.word_count == 4
    assert len(r.flagged) == 1
    assert r.flagged[0].word == "qick"
    assert r.flagged[0].index == 1
    assert len(r.flagged[0].suggestions) > 0
    assert r.flagged[0].suggestions[0].word == "quick"


def test_all_correct_phrase_flags_nothing():
    r = find_misspellings(AX, SpellQuery(text="the quick brown fox"))
    assert r.error == ""
    assert r.word_count == 4
    assert len(r.flagged) == 0


def test_multiple_misspellings_each_flagged():
    r = find_misspellings(AX, SpellQuery(text="hte qick"))
    assert r.error == ""
    assert r.word_count == 2
    flagged_words = {f.word for f in r.flagged}
    assert flagged_words == {"hte", "qick"}


def test_punctuation_and_digits_are_not_flagged_as_misspellings():
    # Punctuation/digits are separators, not spelling errors — only
    # alphabetic tokens are checked.
    r = find_misspellings(AX, SpellQuery(text="Hello, world! 2026"))
    assert r.error == ""
    assert r.word_count == 2  # "Hello" and "world"
    assert len(r.flagged) == 0


def test_case_insensitive_known_word_not_flagged():
    r = find_misspellings(AX, SpellQuery(text="The Quick"))
    assert r.error == ""
    assert len(r.flagged) == 0


def test_top_n_limits_suggestions_per_flagged_word():
    r = find_misspellings(AX, SpellQuery(text="hte", top_n=2))
    assert r.error == ""
    assert len(r.flagged) == 1
    assert len(r.flagged[0].suggestions) == 2


def test_blank_text_is_structured_error():
    r = find_misspellings(AX, SpellQuery(text=""))
    assert r.error != ""

    r2 = find_misspellings(AX, SpellQuery(text="   "))
    assert r2.error != ""


def test_large_text_no_crash():
    r = find_misspellings(AX, SpellQuery(text="a " * 1001))
    assert r.error == ""


def test_deterministic_across_repeated_invocations():
    r1 = find_misspellings(AX, SpellQuery(text="the qick brown fox"))
    r2 = find_misspellings(AX, SpellQuery(text="the qick brown fox"))
    assert list(r1.flagged) == list(r2.flagged)
