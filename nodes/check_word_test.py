from gen.messages_pb2 import SpellQuery
from nodes.check_word import check_word
from nodes.testkit import StubContext

AX = StubContext()


def test_known_word_is_known_with_positive_frequency():
    r = check_word(AX, SpellQuery(text="the"))
    assert r.error == ""
    assert r.word == "the"
    assert r.known is True
    assert r.frequency > 0


def test_misspelled_word_is_unknown_with_zero_frequency():
    r = check_word(AX, SpellQuery(text="hte"))
    assert r.error == ""
    assert r.word == "hte"
    assert r.known is False
    assert r.frequency == 0


def test_nonsense_word_is_unknown():
    r = check_word(AX, SpellQuery(text="zzxxqqxyzzyplugh"))
    assert r.error == ""
    assert r.known is False


def test_case_insensitive_membership_original_casing_echoed():
    r = check_word(AX, SpellQuery(text="The"))
    assert r.error == ""
    assert r.known is True
    assert r.frequency > 0
    # word field echoes the input exactly as given, not the lowercased form
    assert r.word == "The"


def test_blank_text_is_structured_error():
    r = check_word(AX, SpellQuery(text=""))
    assert r.error != ""

    r2 = check_word(AX, SpellQuery(text="   "))
    assert r2.error != ""


def test_multi_word_text_is_structured_error():
    r = check_word(AX, SpellQuery(text="the quick"))
    assert r.error != ""


def test_oversized_text_is_structured_error():
    r = check_word(AX, SpellQuery(text="a" * 101))
    assert r.error != ""


def test_deterministic_across_repeated_invocations():
    r1 = check_word(AX, SpellQuery(text="the"))
    r2 = check_word(AX, SpellQuery(text="the"))
    assert r1.known == r2.known
    assert r1.frequency == r2.frequency
