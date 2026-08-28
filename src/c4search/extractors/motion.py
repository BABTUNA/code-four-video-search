import subprocess
from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor
from c4search.timeline import merge_runs


def motion_series(proxy: Path, fps: int = 5, width: int = 160, height: int = 90) -> list[float]:
    """Per-second camera-motion energy from tiny grayscale frame differences.

    Bodycam motion is global (the wearer moves), so mean absolute frame
    difference tracks walking/running/struggling without any model.
    """
    import numpy as np

    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(proxy),
         "-vf", f"fps={fps},scale={width}:{height},format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-300:]}")

    frame_bytes = width * height
    count = len(result.stdout) // frame_bytes
    frames = np.frombuffer(
        result.stdout[:count * frame_bytes], dtype=np.uint8,
    ).reshape(count, height, width).astype(np.float32)

    diffs = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2)) / 255.0
    per_second = [float(diffs[i:i + fps].mean()) for i in range(0, len(diffs), fps)]
    return per_second


def high_motion_spans(series: list[float], threshold: float, min_s: float) -> list[tuple[float, float]]:
    labels = ["high" if value >= threshold else "" for value in series]
    times = [float(second) for second in range(len(series))]
    spans = merge_runs(labels, times, gap=2.0)
    return [(start, end + 1.0) for start, end, _ in spans if end + 1.0 - start >= min_s]


@register_extractor("motion")
class MotionExtractor:
    name = "motion"

    def __init__(self, options: dict):
        self.threshold = options.get("threshold", 0.08)
        self.min_s = options.get("min_s", 3.0)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        series = motion_series(assets.proxy)
        return [
            Doc(video.video_id, t_start, t_end, "motion",
                "high camera motion, running or struggle",
                {"mean_energy": round(
                    sum(series[int(t_start):int(t_end)]) / max(1, int(t_end) - int(t_start)), 4)})
            for t_start, t_end in high_motion_spans(series, self.threshold, self.min_s)
        ]
