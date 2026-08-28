from app.models import Segment


def create_segments(
    media_id: str,
    media_duration_ms: int,
    segment_duration_ms: int,
    segment_overlap_ms: int,
) -> list[Segment]:
    step_ms = segment_duration_ms - segment_overlap_ms
    segments = []
    start_ms = 0

    while start_ms < media_duration_ms:
        end_ms = min(start_ms + segment_duration_ms, media_duration_ms)
        segments.append(
            Segment(
                segment_id=f"{media_id}:{start_ms}-{end_ms}",
                media_id=media_id,
                start_ms=start_ms,
                end_ms=end_ms,
            )
        )

        if end_ms == media_duration_ms:
            break

        start_ms += step_ms

    return segments

