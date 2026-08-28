import numpy as np

from c4search.models import Doc
from c4search.search.merge import (
    candidate_segments,
    intersect_spans,
    merge_overlaps,
    score_track,
    smooth,
    spans_from_track,
)


def test_score_track_paints_weight_over_spans():
    docs = {1: Doc("v", 10.0, 12.0, "transcript", "x")}
    track = score_track([(1, 1.0)], docs, duration_s=20.0, pad=1.0)
    assert track[9] == 1.0 and track[13] == 1.0
    assert track[5] == 0.0 and track[15] == 0.0


def test_spans_threshold_relative_to_peak():
    track = np.zeros(60)
    track[10:15] = 1.0
    track[40] = 0.1  # noise well below the peak
    spans = spans_from_track(track, rel_threshold=0.35, pad_s=0.0)
    assert len(spans) == 1
    assert spans[0][0] <= 10 and spans[0][1] >= 14


def test_intersect_and_merge():
    assert intersect_spans([(0, 10)], [(5, 20)]) == [(5, 10)]
    assert intersect_spans([(0, 4)], [(5, 20)]) == []
    assert merge_overlaps([(5, 10), (0, 6), (20, 25)]) == [(0, 10), (20, 25)]


def test_candidate_segments_require_all_required_subqueries():
    track_a = np.zeros(100)
    track_a[10:30] = 1.0
    track_b = np.zeros(100)
    track_b[25:40] = 1.0
    docs = {1: Doc("v", 26.0, 28.0, "transcript", "x")}
    candidates = candidate_segments(
        {"sq0": {"v": track_a}, "sq1": {"v": track_b}},
        required=["sq0", "sq1"],
        hits_by_video={"v": [(1, 1.0)]},
        docs=docs,
    )
    assert len(candidates) == 1
    start, end = candidates[0].t_start, candidates[0].t_end
    assert 20 <= start <= 27 and 28 <= end <= 45  # around the 25-30 overlap
    assert candidates[0].evidence == [1]


def test_smooth_preserves_mass_location():
    track = np.zeros(50)
    track[20] = 1.0
    smoothed = smooth(track, sigma_s=3.0)
    assert smoothed.argmax() == 20
