import hashlib
import json
from pathlib import Path


def stage_key(source: Path, config: dict) -> str:
    """Key a stage's output by its input file identity and its config subtree.

    Changing a stage's config re-runs only that stage; touching the source
    video re-runs everything for it.
    """
    stat = source.stat()
    payload = json.dumps(
        {
            "path": str(source.resolve()),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "config": config,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class StageCache:
    def __init__(self, root: Path):
        self.root = Path(root)

    def dir_for(self, stage: str, source: Path, config: dict) -> Path:
        directory = self.root / stage / stage_key(source, config)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def is_done(self, directory: Path) -> bool:
        return (directory / ".done").exists()

    def mark_done(self, directory: Path) -> None:
        (directory / ".done").touch()
