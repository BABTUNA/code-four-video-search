import asyncio
import json

import typer

from app.config import settings
from app.database import Database
from app.media.assets import AssetExtractionError, SegmentAssetExtractor
from app.media.catalog import refresh_media_catalog
from app.models import Modality, ProcessingConfiguration, Segment
from app.processing import ProcessingService
from app.processors.registry import build_processors
from app.repositories import Repository


cli = typer.Typer(no_args_is_help=True)


@cli.callback()
def main() -> None:
    """Developer commands for the Code Four processing pipeline."""


@cli.command()
def extract_segment(
    media_id: str = typer.Argument(help="Video identifier, such as video_1"),
    start_seconds: float = typer.Option(
        default=0,
        min=0,
        help="Segment start time in seconds",
    ),
    duration_seconds: float = typer.Option(
        default=30,
        min=0.001,
        help="Segment duration in seconds",
    ),
    force: bool = typer.Option(
        default=False,
        help="Replace previously extracted assets",
    ),
) -> None:
    """Extract a video clip, mono WAV, and OCR frames for one segment."""
    database = Database(settings.database_path)
    database.initialize()
    repository = Repository(database)
    refresh_media_catalog(settings.video_directory, repository)

    media = repository.get_media(media_id)
    if media is None:
        typer.echo(f"Video not found: {media_id}", err=True)
        raise typer.Exit(code=1)

    start_ms = round(start_seconds * 1000)
    requested_end_ms = start_ms + round(duration_seconds * 1000)
    end_ms = min(requested_end_ms, media.duration_ms)
    if start_ms >= media.duration_ms:
        typer.echo("Start time must be before the end of the video", err=True)
        raise typer.Exit(code=1)

    segment = Segment(
        segment_id=f"{media.media_id}:{start_ms}-{end_ms}",
        media_id=media.media_id,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    extractor = SegmentAssetExtractor(
        derived_directory=settings.derived_directory,
        video_height=settings.segment_video_height,
        frame_interval_seconds=settings.ocr_frame_interval_seconds,
    )

    typer.echo(f"Extracting {segment.segment_id}...")
    try:
        assets = extractor.extract(media, segment, force=force)
    except (AssetExtractionError, ValueError) as error:
        typer.echo(f"Extraction failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(json.dumps(assets.model_dump(mode="json"), indent=2))


@cli.command()
def benchmark_segment(
    media_id: str = typer.Argument(help="Video identifier, such as video_1"),
    duration_seconds: int = typer.Option(
        default=30,
        min=1,
        max=60,
        help="Length of the first segment",
    ),
) -> None:
    """Process one segment and report latency, cost, and evidence."""
    if settings.processor_backend != "openrouter":
        typer.echo("Set PROCESSOR_BACKEND=openrouter in .env", err=True)
        raise typer.Exit(code=1)

    database = Database(settings.database_path)
    database.initialize()
    repository = Repository(database)
    refresh_media_catalog(settings.video_directory, repository)
    if repository.get_media(media_id) is None:
        typer.echo(f"Video not found: {media_id}", err=True)
        raise typer.Exit(code=1)

    extractor = SegmentAssetExtractor(
        derived_directory=settings.derived_directory,
        video_height=settings.segment_video_height,
        frame_interval_seconds=settings.ocr_frame_interval_seconds,
    )
    service = ProcessingService(
        repository,
        build_processors(settings),
        extractor,
        max_concurrent_segments=settings.max_concurrent_segments,
    )
    run = repository.create_run(
        media_id,
        ProcessingConfiguration(
            segment_duration_ms=duration_seconds * 1000,
            segment_overlap_ms=0,
            modalities=list(Modality),
            max_segments=1,
        ),
    )

    typer.echo(f"Processing one {duration_seconds}-second segment as {run.run_id}...")
    asyncio.run(service.process(run.run_id))

    completed_run = repository.get_run(run.run_id)
    segment_results = repository.list_segment_results(run.run_id)
    errors = repository.list_processing_errors(run.run_id)
    evidence = segment_results[0].evidence if segment_results else []
    total_cost = sum(
        item.attributes.get("metrics", {}).get("cost_usd") or 0
        for item in evidence
    )
    report = {
        "run_id": run.run_id,
        "status": completed_run.status if completed_run else "missing",
        "total_cost_usd": total_cost,
        "evidence": [
            {
                "modality": item.modality,
                "model": item.processor.model,
                "content": item.content,
                "metrics": item.attributes.get("metrics", {}),
                "usage": item.attributes.get("usage", {}),
            }
            for item in evidence
        ],
        "errors": [error.model_dump(mode="json") for error in errors],
    }
    typer.echo(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    cli()
