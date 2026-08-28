from dataclasses import dataclass, field
from typing import Any


@dataclass
class VideoMeta:
    video_id: str
    path: str
    duration_s: float
    width: int
    height: int


@dataclass
class Doc:
    """One timestamped piece of evidence on a video's absolute timeline.

    Every extractor emits Docs and every retriever consumes them; this is the
    only contract between components. Times are float seconds from video start.
    """

    video_id: str
    t_start: float
    t_end: float
    modality: str
    text: str
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.t_start < 0 or self.t_end < self.t_start:
            raise ValueError(f"invalid span [{self.t_start}, {self.t_end}]")
