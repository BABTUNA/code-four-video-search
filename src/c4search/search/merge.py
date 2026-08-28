"""Merge timestamped hits from all modalities into candidate segments.

Per sub-query, hits paint weight onto a per-second track on each video's
timeline; the smoothed track is thresholded into spans; required sub-queries
intersect (AND on the timeline); overlapping proposals merge.
"""

from dataclasses import dataclass, field

import numpy as np

from c4search.models import Doc


@dataclass
class Candidate:
    video_id: str
    t_start: float
    t_end: float
    score: float
    evidence: list[int] = field(default_factory=list)


def hit_weight(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


def score_track(hits: list[tuple[int, float]], docs: dict[int, Doc],
                duration_s: float, pad: float = 1.0) -> np.ndarray:
    """Paint each hit's weight over the seconds its span (padded) covers."""
    track = np.zeros(int(duration_s) + 1)
    for doc_id, weight in hits:
        doc = docs[doc_id]
        start = max(0, int(doc.t_start - pad))
        end = min(len(track) - 1, int(doc.t_end + pad))
        track[start:end + 1] += weight
    return track


def smooth(track: np.ndarray, sigma_s: float = 3.0) -> np.ndarray:
    radius = int(3 * sigma_s)
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-x**2 / (2 * sigma_s**2))
    return np.convolve(track, kernel / kernel.sum(), mode="same")


def spans_from_track(track: np.ndarray, rel_threshold: float = 0.35,
                     gap_s: float = 8.0, min_s: float = 2.0,
                     pad_s: float = 2.0) -> list[tuple[float, float]]:
    if track.max() <= 0:
        return []
    above = np.where(track >= rel_threshold * track.max())[0]
    spans: list[list[float]] = []
    for second in above:
        if spans and second - spans[-1][1] <= gap_s:
            spans[-1][1] = second
        else:
            spans.append([float(second), float(second)])
    limit = len(track) - 1
    sized = [
        (max(0.0, start - pad_s), min(float(limit), end + pad_s))
        for start, end in spans if end - start + 1 >= min_s
    ]
    return sized


def intersect_spans(a: list[tuple[float, float]],
                    b: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for a_start, a_end in a:
        for b_start, b_end in b:
            start, end = max(a_start, b_start), min(a_end, b_end)
            if end > start:
                out.append((start, end))
    return out


def merge_overlaps(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def candidate_segments(
    tracks_by_subquery: dict[str, dict[str, np.ndarray]],  # sq_id -> video -> track
    required: list[str],
    hits_by_video: dict[str, list[tuple[int, float]]],
    docs: dict[int, Doc],
    top: int = 10,
    params: dict | None = None,
) -> list[Candidate]:
    """Intersect required sub-query spans per video; score by track mass."""
    params = params or {}
    sigma = params.get("sigma_s", 3.0)

    def to_spans(track: np.ndarray) -> list[tuple[float, float]]:
        return spans_from_track(
            smooth(track, sigma),
            rel_threshold=params.get("rel_threshold", 0.35),
            gap_s=params.get("gap_s", 8.0),
            min_s=params.get("min_s", 2.0),
            pad_s=params.get("pad_s", 2.0),
        )

    videos = {video for tracks in tracks_by_subquery.values() for video in tracks}
    candidates = []
    for video in videos:
        if required:
            # AND on the timeline: every required sub-query must cover the span.
            spans = None
            for sq_id in required:
                track = tracks_by_subquery.get(sq_id, {}).get(video)
                sq_spans = to_spans(track) if track is not None else []
                spans = sq_spans if spans is None else intersect_spans(spans, sq_spans)
        else:
            # Only supporting sub-queries: union their spans instead - a
            # supporting stream should never veto another stream's evidence.
            spans = []
            for tracks in tracks_by_subquery.values():
                track = tracks.get(video)
                if track is not None:
                    spans.extend(to_spans(track))
        for start, end in merge_overlaps(spans or []):
            evidence = [
                doc_id for doc_id, _ in hits_by_video.get(video, [])
                if docs[doc_id].t_start <= end and docs[doc_id].t_end >= start
            ]
            score = sum(
                float(smooth(tracks_by_subquery[sq_id][video], sigma)[int(start):int(end) + 1].mean())
                for sq_id in tracks_by_subquery if video in tracks_by_subquery[sq_id]
            )
            candidates.append(Candidate(video, start, end, round(score, 5), evidence))
    candidates.sort(key=lambda c: -c.score)
    return candidates[:top]
