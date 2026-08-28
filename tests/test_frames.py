import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.extractors.frames import merge_runs, scene_label


def test_merge_runs_collapses_consecutive_labels():
    labels = ["night", "night", "day", "day", "day"]
    times = [0.0, 2.0, 4.0, 6.0, 8.0]
    assert merge_runs(labels, times, gap=4.0) == [
        (0.0, 2.0, "night"),
        (4.0, 8.0, "day"),
    ]


def test_merge_runs_splits_on_time_gaps():
    labels = ["night", "night"]
    times = [0.0, 30.0]
    assert merge_runs(labels, times, gap=4.0) == [
        (0.0, 0.0, "night"),
        (30.0, 30.0, "night"),
    ]


def test_dark_frames_override_daylight_calls():
    assert scene_label("outdoors in daylight", luma=20.0) == "outdoors at night"
    assert scene_label("outdoors in daylight", luma=120.0) == "outdoors in daylight"
    assert scene_label("indoors", luma=20.0) == "indoors"
