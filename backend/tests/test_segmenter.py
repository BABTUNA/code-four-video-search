from app.media.segmenter import create_segments


def test_creates_overlapping_segments() -> None:
    segments = create_segments(
        media_id="video_1",
        media_duration_ms=70_000,
        segment_duration_ms=30_000,
        segment_overlap_ms=5_000,
    )

    boundaries = [(segment.start_ms, segment.end_ms) for segment in segments]
    assert boundaries == [
        (0, 30_000),
        (25_000, 55_000),
        (50_000, 70_000),
    ]


def test_stops_after_a_short_final_segment() -> None:
    segments = create_segments(
        media_id="video_1",
        media_duration_ms=31_000,
        segment_duration_ms=30_000,
        segment_overlap_ms=5_000,
    )

    boundaries = [(segment.start_ms, segment.end_ms) for segment in segments]
    assert boundaries == [(0, 30_000), (25_000, 31_000)]

