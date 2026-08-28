from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Modality(str, Enum):
    VISUAL = "visual"
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    OCR = "ocr"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class ProcessingConfiguration(BaseModel):
    segment_duration_ms: int = Field(default=30_000, gt=0, le=60_000)
    segment_overlap_ms: int = Field(default=5_000, ge=0)
    modalities: list[Modality] = Field(default_factory=lambda: list(Modality))
    max_segments: int | None = Field(default=1, gt=0, le=1_000)

    @model_validator(mode="after")
    def validate_configuration(self) -> "ProcessingConfiguration":
        if self.segment_overlap_ms >= self.segment_duration_ms:
            raise ValueError("Segment overlap must be smaller than segment duration")

        if not self.modalities:
            raise ValueError("Select at least one modality")

        if len(self.modalities) != len(set(self.modalities)):
            raise ValueError("Each modality may only be selected once")

        return self


class MediaRecord(BaseModel):
    media_id: str
    filename: str
    path: str
    duration_ms: int
    created_at: datetime


class MediaSummary(BaseModel):
    media_id: str
    filename: str
    duration_ms: int
    file_url: str


class Segment(BaseModel):
    segment_id: str
    media_id: str
    start_ms: int
    end_ms: int


class SegmentAssets(BaseModel):
    segment_id: str
    video_path: Path
    audio_path: Path
    frame_paths: list[Path]
    video_height: int
    frame_interval_seconds: float
    source_size_bytes: int
    source_modified_ns: int


class ProcessorInformation(BaseModel):
    model: str
    version: str = "1"


class ProcessorOutput(BaseModel):
    type: str
    content: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    processor: ProcessorInformation


class Evidence(BaseModel):
    run_id: str
    segment_id: str
    media_id: str
    start_ms: int
    end_ms: int
    modality: Modality
    type: str
    content: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    processor: ProcessorInformation


class ProcessingRun(BaseModel):
    run_id: str
    media_id: str
    status: RunStatus
    configuration: ProcessingConfiguration
    completed_items: int
    failed_items: int
    total_items: int
    error: str | None
    created_at: datetime


class ProcessingError(BaseModel):
    run_id: str
    segment_id: str
    modality: Modality
    message: str
    created_at: datetime


class MediaDetails(MediaSummary):
    processing_runs: list[ProcessingRun]


class SegmentResult(BaseModel):
    segment: Segment
    evidence: list[Evidence]
