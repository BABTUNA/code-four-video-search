import asyncio
from datetime import UTC, datetime

from app.database import Database
from app.models import (
    MediaRecord,
    Modality,
    ProcessorOutput,
    ProcessingConfiguration,
    RunStatus,
    SegmentAssets,
)
from app.processing import ProcessingService
from app.processors.fake import FakeProcessor
from app.repositories import Repository


class FakeAssetExtractor:
    def __init__(self, directory):
        self.directory = directory

    def extract(self, media, segment, force=False) -> SegmentAssets:
        return SegmentAssets(
            segment_id=segment.segment_id,
            video_path=self.directory / "segment.mp4",
            audio_path=self.directory / "audio.wav",
            frame_paths=[self.directory / "frame.jpg"],
            video_height=720,
            frame_interval_seconds=5,
            source_size_bytes=1,
            source_modified_ns=1,
        )


class FailingProcessor:
    modality = Modality.AUDIO

    async def process(self, segment, assets) -> ProcessorOutput:
        raise RuntimeError("Audio model unavailable")


def test_processes_every_modality_on_shared_segments(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    repository = Repository(database)
    repository.save_media(
        MediaRecord(
            media_id="video_1",
            filename="video_1.mp4",
            path="/videos/video_1.mp4",
            duration_ms=70_000,
            created_at=datetime.now(UTC),
        )
    )

    modalities = [Modality.VISUAL, Modality.AUDIO]
    run = repository.create_run(
        media_id="video_1",
        configuration=ProcessingConfiguration(
            modalities=modalities,
            max_segments=None,
        ),
    )
    service = ProcessingService(
        repository=repository,
        processors={modality: FakeProcessor(modality) for modality in modalities},
        asset_extractor=FakeAssetExtractor(tmp_path),
    )

    asyncio.run(service.process(run.run_id))

    completed_run = repository.get_run(run.run_id)
    assert completed_run is not None
    assert completed_run.status == RunStatus.COMPLETED
    assert completed_run.total_items == 6
    assert completed_run.completed_items == 6

    segment_results = repository.list_segment_results(run.run_id)
    assert len(segment_results) == 3
    assert all(len(result.evidence) == 2 for result in segment_results)
    assert all(
        evidence.attributes["metrics"]["processor_seconds"] >= 0
        for result in segment_results
        for evidence in result.evidence
    )
    assert {
        evidence.modality
        for result in segment_results
        for evidence in result.evidence
    } == set(modalities)


def test_records_processor_errors_without_stopping_other_modalities(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    repository = Repository(database)
    repository.save_media(
        MediaRecord(
            media_id="video_1",
            filename="video_1.mp4",
            path="/videos/video_1.mp4",
            duration_ms=30_000,
            created_at=datetime.now(UTC),
        )
    )

    run = repository.create_run(
        media_id="video_1",
        configuration=ProcessingConfiguration(
            modalities=[Modality.VISUAL, Modality.AUDIO],
        ),
    )
    service = ProcessingService(
        repository=repository,
        processors={
            Modality.VISUAL: FakeProcessor(Modality.VISUAL),
            Modality.AUDIO: FailingProcessor(),
        },
        asset_extractor=FakeAssetExtractor(tmp_path),
    )

    asyncio.run(service.process(run.run_id))

    completed_run = repository.get_run(run.run_id)
    assert completed_run is not None
    assert completed_run.status == RunStatus.COMPLETED_WITH_ERRORS
    assert completed_run.completed_items == 1
    assert completed_run.failed_items == 1
    errors = repository.list_processing_errors(run.run_id)
    assert len(errors) == 1
    assert errors[0].modality == Modality.AUDIO
    assert errors[0].message == "Audio model unavailable"
