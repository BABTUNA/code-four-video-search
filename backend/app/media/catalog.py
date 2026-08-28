import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.models import MediaRecord
from app.repositories import Repository


def probe_duration_ms(video_path: Path) -> int:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    return round(float(result.stdout.strip()) * 1000)


def refresh_media_catalog(video_directory: Path, repository: Repository) -> None:
    video_directory.mkdir(parents=True, exist_ok=True)

    for video_path in sorted(video_directory.glob("*.mp4")):
        try:
            duration_ms = probe_duration_ms(video_path)
        except (subprocess.CalledProcessError, ValueError):
            continue

        repository.save_media(
            MediaRecord(
                media_id=video_path.stem,
                filename=video_path.name,
                path=str(video_path.resolve()),
                duration_ms=duration_ms,
                created_at=datetime.now(UTC),
            )
        )

