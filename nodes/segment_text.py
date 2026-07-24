from gen.messages_pb2 import SpellQuery, SegmentationResult
from gen.axiom_context import AxiomContext
from nodes.lib import (
    RequestError,
    check_text,
    resolve_max_edit_distance,
    resolve_max_segment_length,
    get_symspell,
)


def segment_text(ax: AxiomContext, input: SpellQuery) -> SegmentationResult:
    """Segment a run-together string into its constituent words (e.g.
    "thequickbrownfox" -> "the quick brown fox"), correcting spelling errors
    in the individual words along the way. Uses SymSpell's word-segmentation
    algorithm, which finds the split into dictionary words that minimizes
    total edit distance, weighted by word frequency. `max_edit_distance`
    (0-2, default 2) bounds the per-word correction distance;
    `max_segment_length` (default 20) caps how long any single split-out word
    may be. `edit_distance` in the result is the total edit distance summed
    across every segment; `log_probability` is the summed log-likelihood of
    the chosen split (less negative = more probable), useful for comparing
    alternative segmentations. Deterministic; blank input returns a
    structured error instead of crashing (the underlying library raises on
    an empty string — this node guards that boundary itself).
    """
    try:
        text = check_text(input.text, "text")
        max_edit_distance = resolve_max_edit_distance(input)
        max_segment_length = resolve_max_segment_length(input)
    except RequestError as e:
        return SegmentationResult(error=str(e))

    sym = get_symspell()
    result = sym.word_segmentation(
        text,
        max_edit_distance=max_edit_distance,
        max_segmentation_word_length=max_segment_length,
    )
    return SegmentationResult(
        input=text,
        segmented=result.corrected_string,
        edit_distance=result.distance_sum,
        log_probability=result.log_prob_sum,
    )
