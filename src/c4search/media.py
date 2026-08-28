import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from c4search.models import VideoMeta


@dataclass
class MediaAssets:
    """Prepared per-video inputs that extractors read instead of the source."""

    proxy: Path          # 480p mp4
    audio: Path          # 16 kHz mono wav
    frames_dir: Path     # jpegs sampled at frame_fps
    frame_fps: float
    loudness: Path       # json [[t_seconds, momentary_lufs], ...]


def run(arguments: list[str]) -> str:
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{arguments[0]} failed: {result.stderr[-500:]}")
    return result.stderr if arguments[0] == "ffmpeg" else result.stdout


def probe(path: Path) -> VideoMeta:
    output = run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json", str(path),
    ])
    info = json.loads(output)
    stream = info["streams"][0]
    return VideoMeta(
        video_id=path.stem,
        path=str(path),
        duration_s=float(info["format"]["duration"]),
        width=stream["width"],
        height=stream["height"],
    )


def frame_time(frame_path: Path, fps: float) -> float:
    """Frames are named by 1-based output index; recover their timestamp."""
    return (int(frame_path.stem) - 1) / fps


def prepare(source: Path, workdir: Path, frame_fps: float = 0.5,
            proxy_height: int = 480) -> MediaAssets:
    """Decode the source once into everything the extractors consume."""
    workdir.mkdir(parents=True, exist_ok=True)
    assets = MediaAssets(
        proxy=workdir / "proxy.mp4",
        audio=workdir / "audio.wav",
        frames_dir=workdir / "frames",
        frame_fps=frame_fps,
        loudness=workdir / "loudness.json",
    )

    run(["ffmpeg", "-y", "-i", str(source),
         "-vf", f"scale=-2:{proxy_height}", "-an",
         "-c:v", "h264_videotoolbox", "-b:v", "1000k", str(assets.proxy)])

    run(["ffmpeg", "-y", "-i", str(source),
         "-ac", "1", "-ar", "16000", str(assets.audio)])

    assets.frames_dir.mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(assets.proxy),
         "-vf", f"fps={frame_fps}", "-q:v", "3",
         str(assets.frames_dir / "%06d.jpg")])

    stderr = run(["ffmpeg", "-nostats", "-i", str(assets.audio),
                  "-af", "ebur128", "-f", "null", "-"])
    assets.loudness.write_text(json.dumps(parse_loudness(stderr)))
    return assets


LOUDNESS_LINE = re.compile(r"t:\s*([\d.]+)\s+.*?M:\s*(-?[\d.]+)")


def parse_loudness(ffmpeg_stderr: str) -> list[list[float]]:
    """Pull [time, momentary LUFS] pairs out of ebur128's progress lines."""
    series = []
    for line in ffmpeg_stderr.splitlines():
        match = LOUDNESS_LINE.search(line)
        if match:
            series.append([float(match.group(1)), float(match.group(2))])
    return series
