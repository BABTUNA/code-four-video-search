import re
from pathlib import Path

from c4search.media import MediaAssets, frame_time
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor

# Burned-in bodycam overlays: "2023-06-14 23:41:52", "06/14/2023 11:41:52 PM"...
CLOCK = re.compile(
    r"(?P<h>\d{1,2})[:.](?P<m>\d{2})[:.](?P<s>\d{2})\s*(?P<ampm>[AP]M)?",
    re.IGNORECASE,
)


def clock_seconds(text: str) -> float | None:
    """Parse the first wall-clock time in OCR text as seconds since midnight."""
    match = CLOCK.search(text)
    if not match:
        return None
    hours, minutes, seconds = int(match["h"]), int(match["m"]), int(match["s"])
    if hours > 23 or minutes > 59 or seconds > 59:
        return None
    if match["ampm"]:
        hours = hours % 12 + (12 if match["ampm"].upper() == "PM" else 0)
    return hours * 3600.0 + minutes * 60.0 + seconds


def monotonic_anchors(readings: list[tuple[float, float]], drift_s: float = 90.0) -> list[tuple[float, float]]:
    """Keep (video_t, clock_s) pairs consistent with a clock that advances at
    roughly video speed; OCR misreads violate that and get dropped."""
    anchors = []
    for video_t, clock_s in readings:
        if anchors:
            last_video, last_clock = anchors[-1]
            expected = last_clock + (video_t - last_video)
            if abs(clock_s - expected) > drift_s:
                continue
        anchors.append((video_t, clock_s))
    return anchors


def clock_text(clock_s: float) -> str:
    hours, remainder = divmod(int(clock_s), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@register_extractor("clock_ocr")
class ClockOcrExtractor:
    name = "clock_ocr"

    def __init__(self, options: dict):
        self.every_s = options.get("every_s", 20.0)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path, store=None) -> list[Doc]:
        from ocrmac import ocrmac

        frame_paths = sorted(assets.frames_dir.glob("*.jpg"))
        step = max(1, round(self.every_s * assets.frame_fps))

        readings = []
        for path in frame_paths[::step]:
            recognized = ocrmac.OCR(str(path), framework="vision").recognize()
            for text, _confidence, _box in recognized:
                clock_s = clock_seconds(text)
                if clock_s is not None:
                    readings.append((frame_time(path, assets.frame_fps), clock_s))
                    break

        return [
            Doc(video.video_id, video_t, video_t, "wall_clock",
                f"wall clock {clock_text(clock_s)}", {"clock_s": clock_s})
            for video_t, clock_s in monotonic_anchors(readings)
        ]
