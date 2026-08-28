from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Database
from app.media.assets import SegmentAssetExtractor
from app.media.catalog import refresh_media_catalog
from app.models import (
    MediaDetails,
    MediaRecord,
    MediaSummary,
    ProcessingConfiguration,
    ProcessingError,
    ProcessingRun,
    SegmentResult,
)
from app.processing import ProcessingService
from app.processors.registry import build_processors
from app.repositories import Repository


database = Database(settings.database_path)
repository = Repository(database)
asset_extractor = SegmentAssetExtractor(
    derived_directory=settings.derived_directory,
    video_height=settings.segment_video_height,
    frame_interval_seconds=settings.ocr_frame_interval_seconds,
)
processors = build_processors(settings)
processing_service = ProcessingService(
    repository,
    processors,
    asset_extractor,
    max_concurrent_segments=settings.max_concurrent_segments,
)


def media_summary(media: MediaRecord) -> MediaSummary:
    return MediaSummary(
        media_id=media.media_id,
        filename=media.filename,
        duration_ms=media.duration_ms,
        file_url=f"/api/videos/{media.media_id}/file",
    )


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    database.initialize()
    refresh_media_catalog(settings.video_directory, repository)
    yield


app = FastAPI(title="Code Four Video Search", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/videos", response_model=list[MediaSummary])
def list_videos() -> list[MediaSummary]:
    refresh_media_catalog(settings.video_directory, repository)
    return [media_summary(media) for media in repository.list_media()]


@app.get("/api/videos/{media_id}", response_model=MediaDetails)
def get_video(media_id: str) -> MediaDetails:
    media = repository.get_media(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Video not found")

    return MediaDetails(
        **media_summary(media).model_dump(),
        processing_runs=repository.list_runs(media_id),
    )


@app.get("/api/videos/{media_id}/file")
def get_video_file(media_id: str) -> FileResponse:
    media = repository.get_media(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(media.path, media_type="video/mp4")


@app.post(
    "/api/videos/{media_id}/processing-runs",
    response_model=ProcessingRun,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_processing_run(
    media_id: str,
    configuration: ProcessingConfiguration,
    background_tasks: BackgroundTasks,
) -> ProcessingRun:
    if repository.get_media(media_id) is None:
        raise HTTPException(status_code=404, detail="Video not found")

    run = repository.create_run(media_id, configuration)
    background_tasks.add_task(processing_service.process, run.run_id)
    return run


@app.get("/api/processing-runs/{run_id}", response_model=ProcessingRun)
def get_processing_run(run_id: str) -> ProcessingRun:
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Processing run not found")
    return run


@app.get(
    "/api/processing-runs/{run_id}/segments",
    response_model=list[SegmentResult],
)
def get_processing_run_segments(run_id: str) -> list[SegmentResult]:
    if repository.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="Processing run not found")
    return repository.list_segment_results(run_id)


@app.get(
    "/api/processing-runs/{run_id}/errors",
    response_model=list[ProcessingError],
)
def get_processing_run_errors(run_id: str) -> list[ProcessingError]:
    if repository.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="Processing run not found")
    return repository.list_processing_errors(run_id)
