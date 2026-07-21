from gen.messages_pb2 import SpellQuery
from nodes.correct_word import correct_word
from nodes.testkit import StubContext

AX = StubContext()


def test_known_typo_corrects_to_expected_word():
    # Independent oracle: "hte" is the textbook SymSpell example and the
    # correct word is unambiguous English-language knowledge, not derived
    # from the implementation under test.
    r = correct_word(AX, SpellQuery(text="hte"))
    assert r.error == ""
    assert r.input == "hte"
    assert len(r.candidates) > 0
    assert r.candidates[0].word == "the"
    assert r.candidates[0].edit_distance == 1
    assert r.candidates[0].frequency > 0
    # Ranked closest-first: no candidate before the first distance-2 entry
    # has a larger distance than a later one.
    distances = [c.edit_distance for c in r.candidates]
    assert distances == sorted(distances)


def test_correctly_spelled_word_returns_itself_first():
    r = correct_word(AX, SpellQuery(text="the"))
    assert r.error == ""
    assert r.candidates[0].word == "the"
    assert r.candidates[0].edit_distance == 0


def test_top_n_limits_candidate_count():
    r = correct_word(AX, SpellQuery(text="hte", top_n=3))
    assert r.error == ""
    assert len(r.candidates) == 3


def test_case_insensitive_matching():
    # "Hte" is case-sensitively 2 edits from "the" (capital H vs lowercase
    # t/h transposition doesn't apply across case) but should still resolve
    # to "the" at distance 1 once case-folded — this is the library's
    # case-sensitivity trap the node guards against.
    r = correct_word(AX, SpellQuery(text="Hte", max_edit_distance=1))
    assert r.error == ""
    assert r.candidates[0].word == "the"
    assert r.candidates[0].edit_distance == 1


def test_max_edit_distance_zero_only_exact_match():
    r = correct_word(AX, SpellQuery(text="the", max_edit_distance=0))
    assert r.error == ""
    assert len(r.candidates) == 1
    assert r.candidates[0].word == "the"
    assert r.candidates[0].edit_distance == 0


def test_no_candidates_within_distance_returns_empty_not_error():
    r = correct_word(AX, SpellQuery(text="the", max_edit_distance=0, top_n=1))
    # a nonsense word far from any dictionary word within distance 0/1
    r2 = correct_word(AX, SpellQuery(text="zzxxqqxyzzyplugh", max_edit_distance=1))
    assert r2.error == ""
    assert len(r2.candidates) == 0


def test_blank_text_is_structured_error():
    r = correct_word(AX, SpellQuery(text=""))
    assert r.error != ""
    assert len(r.candidates) == 0

    r2 = correct_word(AX, SpellQuery(text="   "))
    assert r2.error != ""


def test_multi_word_text_is_structured_error():
    r = correct_word(AX, SpellQuery(text="hello world"))
    assert r.error != ""
    assert "single word" in r.error


def test_oversized_text_is_structured_error():
    r = correct_word(AX, SpellQuery(text="a" * 101))
    assert r.error != ""


def test_out_of_range_max_edit_distance_is_structured_error():
    r = correct_word(AX, SpellQuery(text="hte", max_edit_distance=5))
    assert r.error != ""

    r2 = correct_word(AX, SpellQuery(text="hte", max_edit_distance=-1))
    assert r2.error != ""


def test_out_of_range_top_n_is_structured_error():
    r = correct_word(AX, SpellQuery(text="hte", top_n=0))
    assert r.error != ""

    r2 = correct_word(AX, SpellQuery(text="hte", top_n=21))
    assert r2.error != ""


def test_deterministic_across_repeated_invocations():
    r1 = correct_word(AX, SpellQuery(text="hte"))
    r2 = correct_word(AX, SpellQuery(text="hte"))
    assert list(r1.candidates) == list(r2.candidates)
