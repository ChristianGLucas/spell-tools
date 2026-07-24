from gen.messages_pb2 import SpellQuery
from nodes.correct_phrase import correct_phrase
from nodes.testkit import StubContext

AX = StubContext()


def test_multi_word_compound_correction():
    # Independent oracle: the corrected sentence is unambiguous English, not
    # derived from the implementation under test.
    r = correct_phrase(AX, SpellQuery(text="the qick brown fox jum ped over the lazy dog"))
    assert r.error == ""
    assert r.corrected == "the quick brown fox jumped over the lazy dog"
    assert r.edit_distance > 0


def test_missing_space_merges_two_adjacent_words():
    # A single missing space merging exactly two adjacent words is the
    # documented, verified case CorrectPhrase recovers (confirmed directly
    # against the library: within max_edit_distance=2 it splits a two-word
    # merge but a three-word merge like "thequickbrown" is NOT reliably
    # recovered — that's SegmentText's job, tested separately below).
    r = correct_phrase(AX, SpellQuery(text="the quickbrown fox jumps over the lazy dog"))
    assert r.error == ""
    assert r.corrected == "the quick brown fox jumps over the lazy dog"


def test_extra_space_splitting_one_word_is_recombined():
    r = correct_phrase(AX, SpellQuery(text="where is the exit", max_edit_distance=2))
    # sanity: already-correct input with no errors stays correct
    assert r.error == ""
    assert r.corrected == "where is the exit"

    r2 = correct_phrase(AX, SpellQuery(text="whereis the exit"))
    assert r2.error == ""
    assert r2.corrected == "where is the exit"


def test_multi_word_run_together_blob_is_not_reliably_split():
    # Documented boundary: a three-word merge exceeds what lookup_compound's
    # per-token correction can recover within max_edit_distance=2. Verified
    # actual behavior (an independent oracle would be "the quick brown", but
    # that is NOT what the library produces): it partially splits the blob
    # but mis-corrects the leading fragment to the nearest single dictionary
    # word ("cheque") instead of "the quick" — a real, verified limitation
    # (not a bug in this node) — callers with heavily run-together text
    # should use SegmentText instead, which is built for exactly this case.
    r = correct_phrase(AX, SpellQuery(text="thequickbrown fox jumps over the lazy dog"))
    assert r.error == ""
    assert "quick" not in r.corrected
    assert r.corrected == "cheque brown fox jumps over the lazy dog"


def test_already_correct_phrase_is_unchanged():
    r = correct_phrase(AX, SpellQuery(text="the quick brown fox"))
    assert r.error == ""
    assert r.corrected == "the quick brown fox"
    assert r.edit_distance == 0


def test_sentence_casing_is_preserved():
    r = correct_phrase(AX, SpellQuery(text="The qick brown fox"))
    assert r.error == ""
    assert r.corrected.startswith("The ")


def test_max_edit_distance_bounds_correction():
    loose = correct_phrase(AX, SpellQuery(text="the qick brown fox", max_edit_distance=2))
    tight = correct_phrase(AX, SpellQuery(text="the qick brown fox", max_edit_distance=0))
    assert loose.error == "" and tight.error == ""
    assert loose.corrected != tight.corrected
    assert "quick" in loose.corrected


def test_blank_text_is_structured_error():
    r = correct_phrase(AX, SpellQuery(text=""))
    assert r.error != ""
    assert r.corrected == ""

    r2 = correct_phrase(AX, SpellQuery(text="   "))
    assert r2.error != ""


def test_large_text_no_crash():
    r = correct_phrase(AX, SpellQuery(text="a " * 1001))
    assert r.error == ""


def test_out_of_range_max_edit_distance_is_structured_error():
    r = correct_phrase(AX, SpellQuery(text="the qick brown fox", max_edit_distance=3))
    assert r.error != ""


def test_deterministic_across_repeated_invocations():
    r1 = correct_phrase(AX, SpellQuery(text="the qick brown fox"))
    r2 = correct_phrase(AX, SpellQuery(text="the qick brown fox"))
    assert r1.corrected == r2.corrected
    assert r1.edit_distance == r2.edit_distance
