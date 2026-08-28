import re
import subprocess
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from app.models import MediaRecord, Segment, SegmentAssets


class AssetExtractionError(RuntimeError):
    pass


class AssetExtractor(Protocol):
    def extract(
        self,
        media: MediaRecord,
        segment: Segment,
        force: bool = False,
    ) -> SegmentAssets:
        ...


class SegmentAssetExtractor:
    def __init__(
        self,
        derived_directory: Path,
        video_height: int = 720,
        frame_interval_seconds: float = 5.0,
    ):
        if video_height <= 0 or video_height % 2 != 0:
            raise ValueError("Video height must be a positive even number")
        if frame_interval_seconds <= 0:
            raise ValueError("Frame interval must be greater than zero")

        self.derived_directory = derived_directory
        self.video_height = video_height
        self.frame_interval_seconds = frame_interval_seconds

    def extract(
        self,
        media: MediaRecord,
        segment: Segment,
        force: bool = False,
    ) -> SegmentAssets:
        self._validate_input(media, segment)

        asset_directory = (
            self.derived_directory
            / media.media_id
            / f"{segment.start_ms}-{segment.end_ms}"
        )
        video_path = asset_directory / "segment.mp4"
        audio_path = asset_directory / "audio.wav"
        frame_directory = asset_directory / "frames"
        manifest_path = asset_directory / "assets.json"

        source_path = Path(media.path)
        source_stat = source_path.stat()

        if not force and manifest_path.exists():
            try:
                cached_assets = SegmentAssets.model_validate_json(
                    manifest_path.read_text()
                )
            except (OSError, ValidationError):
                cached_assets = None

            if cached_assets and self._cache_matches(
                cached_assets,
                source_stat.st_size,
                source_stat.st_mtime_ns,
            ):
                return cached_assets

        asset_directory.mkdir(parents=True, exist_ok=True)
        frame_directory.mkdir(parents=True, exist_ok=True)
        manifest_path.unlink(missing_ok=True)
        for old_frame_path in frame_directory.glob("frame_*.jpg"):
            old_frame_path.unlink()

        start_seconds = segment.start_ms / 1000
        duration_seconds = (segment.end_ms - segment.start_ms) / 1000

        self._run_ffmpeg(
            [
                "-ss",
                f"{start_seconds:.3f}",
                "-i",
                media.path,
                "-t",
                f"{duration_seconds:.3f}",
                "-map",
                "0:v:0",
                "-an",
                "-vf",
                f"scale=-2:{self.video_height}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-movflags",
                "+faststart",
                str(video_path),
            ]
        )
        self._run_ffmpeg(
            [
                "-ss",
                f"{start_seconds:.3f}",
                "-i",
                media.path,
                "-t",
                f"{duration_seconds:.3f}",
                "-vn",
                "-af",
                "asetpts=PTS-STARTPTS",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(audio_path),
            ]
        )
        self._run_ffmpeg(
            [
                "-ss",
                f"{start_seconds:.3f}",
                "-i",
                media.path,
                "-t",
                f"{duration_seconds:.3f}",
                "-vf",
                f"fps=1/{self.frame_interval_seconds}",
                "-q:v",
                "2",
                str(frame_directory / "frame_%03d.jpg"),
            ]
        )

        frame_paths = sorted(frame_directory.glob("frame_*.jpg"))
        if not frame_paths:
            raise AssetExtractionError("FFmpeg did not produce any OCR frames")

        assets = SegmentAssets(
            segment_id=segment.segment_id,
            video_path=video_path.resolve(),
            audio_path=audio_path.resolve(),
            frame_paths=[path.resolve() for path in frame_paths],
            video_height=self.video_height,
            frame_interval_seconds=self.frame_interval_seconds,
            source_size_bytes=source_stat.st_size,
            source_modified_ns=source_stat.st_mtime_ns,
        )
        manifest_path.write_text(assets.model_dump_json(indent=2))
        return assets

    def _validate_input(self, media: MediaRecord, segment: Segment) -> None:
        if media.media_id != segment.media_id:
            raise ValueError("Media and segment identifiers must match")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", media.media_id):
            raise ValueError("Media identifier contains unsupported characters")
        if segment.start_ms < 0 or segment.end_ms <= segment.start_ms:
            raise ValueError("Segment timestamps are invalid")
        if segment.end_ms > media.duration_ms:
            raise ValueError("Segment extends beyond the media duration")
        if not Path(media.path).is_file():
            raise ValueError(f"Video file does not exist: {media.path}")

    @staticmethod
    def _assets_exist(assets: SegmentAssets) -> bool:
        paths = [assets.video_path, assets.audio_path, *assets.frame_paths]
        return bool(assets.frame_paths) and all(
            path.is_file() and path.stat().st_size > 0 for path in paths
        )

    def _cache_matches(
        self,
        assets: SegmentAssets,
        source_size_bytes: int,
        source_modified_ns: int,
    ) -> bool:
        return (
            assets.video_height == self.video_height
            and assets.frame_interval_seconds == self.frame_interval_seconds
            and assets.source_size_bytes == source_size_bytes
            and assets.source_modified_ns == source_modified_ns
            and self._assets_exist(assets)
        )

    @staticmethod
    def _run_ffmpeg(arguments: list[str]) -> None:
        command = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *arguments,
        ]
        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or "Unknown FFmpeg error"
            raise AssetExtractionError(message) from error
