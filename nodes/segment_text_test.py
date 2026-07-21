from gen.messages_pb2 import SpellQuery
from nodes.segment_text import segment_text
from nodes.testkit import StubContext

AX = StubContext()


def test_task_canonical_segmentation_example():
    # Independent oracle: the segmentation is unambiguous English, not
    # derived from the implementation under test.
    r = segment_text(AX, SpellQuery(text="thequickbrownfox"))
    assert r.error == ""
    assert r.segmented == "the quick brown fox"
    assert r.input == "thequickbrownfox"


def test_longer_run_together_sentence():
    r = segment_text(AX, SpellQuery(text="helloworld"))
    assert r.error == ""
    assert r.segmented == "hello world"


def test_casing_is_preserved():
    r = segment_text(AX, SpellQuery(text="Thequickbrownfox"))
    assert r.error == ""
    assert r.segmented == "The quick brown fox"


def test_already_spaced_text_is_unchanged():
    r = segment_text(AX, SpellQuery(text="the quick brown fox", max_edit_distance=0))
    assert r.error == ""
    assert r.segmented == "the quick brown fox"
    assert r.edit_distance == 0


def test_log_probability_is_populated_and_negative():
    r = segment_text(AX, SpellQuery(text="thequickbrownfox"))
    assert r.error == ""
    # log-probabilities of a multi-word split are always <= 0
    assert r.log_probability < 0


def test_blank_text_is_structured_error_not_a_crash():
    # The underlying symspellpy.word_segmentation raises IndexError on an
    # empty string outright (confirmed against the library directly) — this
    # is the exact case the node must guard before calling into it.
    r = segment_text(AX, SpellQuery(text=""))
    assert r.error != ""
    assert r.segmented == ""

    r2 = segment_text(AX, SpellQuery(text="   "))
    assert r2.error != ""


def test_oversized_text_is_structured_error():
    r = segment_text(AX, SpellQuery(text="a" * 1001))
    assert r.error != ""


def test_out_of_range_max_edit_distance_is_structured_error():
    r = segment_text(AX, SpellQuery(text="thequickbrownfox", max_edit_distance=3))
    assert r.error != ""


def test_out_of_range_max_segment_length_is_structured_error():
    r = segment_text(AX, SpellQuery(text="thequickbrownfox", max_segment_length=0))
    assert r.error != ""

    r2 = segment_text(AX, SpellQuery(text="thequickbrownfox", max_segment_length=51))
    assert r2.error != ""


def test_deterministic_across_repeated_invocations():
    r1 = segment_text(AX, SpellQuery(text="thequickbrownfox"))
    r2 = segment_text(AX, SpellQuery(text="thequickbrownfox"))
    assert r1.segmented == r2.segmented
    assert r1.edit_distance == r2.edit_distance
    assert r1.log_probability == r2.log_probability
