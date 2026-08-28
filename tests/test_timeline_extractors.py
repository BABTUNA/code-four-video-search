import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.extractors.arousal import speechy_windows
from c4search.extractors.clock_ocr import clock_seconds, clock_text, monotonic_anchors
from c4search.extractors.motion import high_motion_spans
from c4search.timeline import merge_runs


def test_merge_runs_drops_empty_labels():
    spans = merge_runs(["", "high", "high", ""], [0.0, 1.0, 2.0, 3.0], gap=2.0)
    assert spans == [(1.0, 2.0, "high")]


def test_speechy_windows_skip_quiet_stretches():
    loud = [[float(t) / 10, -30.0 if t < 50 else -60.0] for t in range(0, 100)]
    assert speechy_windows(loud, window_s=5.0) == [0.0]


def test_clock_parsing_handles_24h_and_ampm():
    assert clock_seconds("2023-06-14 23:41:52") == 23 * 3600 + 41 * 60 + 52
    assert clock_seconds("06/14/2023 11:41:52 PM") == 23 * 3600 + 41 * 60 + 52
    assert clock_seconds("AXON Body 3") is None
    assert clock_seconds("99:99:99") is None
    assert clock_text(23 * 3600 + 41 * 60 + 52) == "23:41:52"


def test_monotonic_anchors_drop_misreads():
    readings = [(0.0, 1000.0), (20.0, 1020.0), (40.0, 7777.0), (60.0, 1061.0)]
    anchors = monotonic_anchors(readings)
    assert [clock for _, clock in anchors] == [1000.0, 1020.0, 1061.0]


def test_high_motion_spans_bridge_short_dips_and_need_minimum_length():
    # Seconds 1-3 and 5 are high: the 1s dip at second 4 is bridged into one
    # span. Second 9 is high but isolated and too short, so it is dropped.
    series = [0.01, 0.2, 0.2, 0.2, 0.01, 0.2, 0.01, 0.01, 0.01, 0.2]
    spans = high_motion_spans(series, threshold=0.1, min_s=3.0)
    assert spans == [(1.0, 6.0)]
