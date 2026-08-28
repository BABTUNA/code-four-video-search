import json
from pathlib import Path
from statistics import median

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor


def officer_speaker(turns: list[dict], loudness: list[list[float]]) -> str | None:
    """Guess which diarized speaker is the camera-wearing officer.

    The wearer's mouth is closest to the mic, so their turns should carry the
    highest momentary loudness. Only a guess when two or more speakers exist.
    """
    by_speaker: dict[str, list[float]] = {}
    for turn in turns:
        samples = [lufs for t, lufs in loudness if turn["start"] <= t <= turn["end"]]
        if samples:
            by_speaker.setdefault(turn["speaker"], []).extend(samples)
    if len(by_speaker) < 2:
        return None
    return max(by_speaker, key=lambda speaker: median(by_speaker[speaker]))


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def speaker_for(t_start: float, t_end: float, turns: list[dict]) -> dict | None:
    """The turn overlapping this span the most, or None if nothing overlaps."""
    best = None
    best_overlap = 0.0
    for turn in turns:
        amount = overlap(t_start, t_end, turn["start"], turn["end"])
        if amount > best_overlap:
            best, best_overlap = turn, amount
    return best


@register_extractor("diarize")
class DiarizeExtractor:
    name = "diarize"

    def __init__(self, options: dict):
        self.device = options.get("device", "auto")

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        import senko  # deferred so the test suite never loads the models

        diarizer = senko.Diarizer(device=self.device, warmup=False, quiet=True)
        result = diarizer.diarize(str(assets.audio), generate_colors=False)
        turns = [
            {"start": float(s["start"]), "end": float(s["end"]),
             "speaker": str(s["speaker"])}
            for s in result["merged_segments"]
        ]

        loudness = json.loads(assets.loudness.read_text())
        officer = officer_speaker(turns, loudness)

        docs = []
        for turn in turns:
            # Only the mic wearer is identifiable from loudness; a scene can
            # hold several officers, so non-wearers are "other", not civilian.
            if officer is None:
                role = "unknown"
            else:
                role = "officer" if turn["speaker"] == officer else "other"
            docs.append(Doc(
                video_id=video.video_id,
                t_start=round(turn["start"], 2),
                t_end=round(max(turn["end"], turn["start"]), 2),
                modality="speaker_turn",
                text=f"{role} speaking",
                extra={"speaker": turn["speaker"], "role": role},
            ))
        return docs
