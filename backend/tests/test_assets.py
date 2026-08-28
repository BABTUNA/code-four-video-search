import subprocess
from datetime import UTC, datetime

from app.media.assets import SegmentAssetExtractor
from app.models import MediaRecord, Segment


def create_test_video(path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-itsoffset",
            "0.3",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x240:rate=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:sample_rate=44100",
            "-t",
            "2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )


def probe_duration(path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def test_extracts_and_caches_segment_assets(tmp_path) -> None:
    video_path = tmp_path / "video_1.mp4"
    create_test_video(video_path)
    media = MediaRecord(
        media_id="video_1",
        filename=video_path.name,
        path=str(video_path),
        duration_ms=2_000,
        created_at=datetime.now(UTC),
    )
    segment = Segment(
        segment_id="video_1:0-1500",
        media_id="video_1",
        start_ms=0,
        end_ms=1_500,
    )
    extractor = SegmentAssetExtractor(
        derived_directory=tmp_path / "derived",
        video_height=120,
        frame_interval_seconds=0.5,
    )

    assets = extractor.extract(media, segment)
    video_modified_at = assets.video_path.stat().st_mtime_ns
    cached_assets = extractor.extract(media, segment)

    assert assets == cached_assets
    assert assets.video_path.stat().st_size > 0
    assert assets.audio_path.stat().st_size > 0
    assert len(assets.frame_paths) >= 2
    assert all(path.stat().st_size > 0 for path in assets.frame_paths)
    assert probe_duration(assets.audio_path) == 1.5
    assert cached_assets.video_path.stat().st_mtime_ns == video_modified_at
