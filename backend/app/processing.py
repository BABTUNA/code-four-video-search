import asyncio
from datetime import UTC, datetime
from time import perf_counter

from app.media.assets import AssetExtractor
from app.media.segmenter import create_segments
from app.models import (
    Evidence,
    Modality,
    ProcessorOutput,
    ProcessingError,
    ProcessingRun,
    RunStatus,
    Segment,
    SegmentAssets,
)
from app.processors.base import ModalityProcessor
from app.repositories import Repository


class ProcessingService:
    def __init__(
        self,
        repository: Repository,
        processors: dict[Modality, ModalityProcessor],
        asset_extractor: AssetExtractor,
        max_concurrent_segments: int = 4,
    ):
        self.repository = repository
        self.processors = processors
        self.asset_extractor = asset_extractor
        self.max_concurrent_segments = max_concurrent_segments

    async def process(self, run_id: str) -> None:
        run = self.repository.get_run(run_id)
        if run is None:
            return

        try:
            await self._process_run(run)
        except Exception as error:
            self.repository.update_run(
                run_id,
                status=RunStatus.FAILED,
                error=self._error_message(error, "Processing run failed"),
            )

    async def _process_run(self, run: ProcessingRun) -> None:
        media = self.repository.get_media(run.media_id)
        if media is None:
            raise ValueError(f"Unknown media: {run.media_id}")

        configuration = run.configuration
        segments = create_segments(
            media_id=media.media_id,
            media_duration_ms=media.duration_ms,
            segment_duration_ms=configuration.segment_duration_ms,
            segment_overlap_ms=configuration.segment_overlap_ms,
        )
        if configuration.max_segments is not None:
            segments = segments[: configuration.max_segments]
        self.repository.save_segments(segments)

        total_items = len(segments) * len(configuration.modalities)
        self.repository.update_run(
            run.run_id,
            status=RunStatus.RUNNING,
            total_items=total_items,
        )

        progress = {"completed": 0, "failed": 0}
        segment_slots = asyncio.Semaphore(self.max_concurrent_segments)

        def save_progress() -> None:
            self.repository.update_run(
                run.run_id,
                completed_items=progress["completed"],
                failed_items=progress["failed"],
                total_items=total_items,
            )

        async def process_modality(
            segment: Segment,
            modality: Modality,
            assets: SegmentAssets,
            extraction_seconds: float,
        ) -> None:
            processor_started_at = perf_counter()
            try:
                processor = self.processors[modality]
                output = await processor.process(segment, assets)
                output = self._add_metrics(
                    output,
                    extraction_seconds=extraction_seconds,
                    processor_seconds=perf_counter() - processor_started_at,
                )
                self.repository.save_evidence(
                    Evidence(
                        run_id=run.run_id,
                        segment_id=segment.segment_id,
                        media_id=segment.media_id,
                        start_ms=segment.start_ms,
                        end_ms=segment.end_ms,
                        modality=modality,
                        **output.model_dump(),
                    )
                )
                progress["completed"] += 1
            except Exception as error:
                self._record_error(
                    run,
                    segment.segment_id,
                    modality,
                    self._error_message(error, "Processor failed"),
                )
                progress["failed"] += 1
            save_progress()

        async def process_segment(segment: Segment) -> None:
            async with segment_slots:
                extraction_started_at = perf_counter()
                try:
                    assets = await asyncio.to_thread(
                        self.asset_extractor.extract,
                        media,
                        segment,
                    )
                    extraction_seconds = perf_counter() - extraction_started_at
                except Exception as error:
                    message = self._error_message(error, "Asset extraction failed")
                    for modality in configuration.modalities:
                        self._record_error(run, segment.segment_id, modality, message)
                        progress["failed"] += 1
                    save_progress()
                    return

                await asyncio.gather(
                    *(
                        process_modality(segment, modality, assets, extraction_seconds)
                        for modality in configuration.modalities
                    )
                )

        await asyncio.gather(*(process_segment(segment) for segment in segments))

        final_status = (
            RunStatus.COMPLETED
            if progress["failed"] == 0
            else RunStatus.COMPLETED_WITH_ERRORS
        )
        self.repository.update_run(
            run.run_id,
            status=final_status,
            completed_items=progress["completed"],
            failed_items=progress["failed"],
            total_items=total_items,
        )

    def _record_error(
        self,
        run: ProcessingRun,
        segment_id: str,
        modality: Modality,
        message: str,
    ) -> None:
        self.repository.save_processing_error(
            ProcessingError(
                run_id=run.run_id,
                segment_id=segment_id,
                modality=modality,
                message=message,
                created_at=datetime.now(UTC),
            )
        )

    @staticmethod
    def _error_message(error: Exception, fallback: str) -> str:
        message = str(error).strip()
        return (message or fallback)[:500]

    @staticmethod
    def _add_metrics(
        output: ProcessorOutput,
        *,
        extraction_seconds: float,
        processor_seconds: float,
    ) -> ProcessorOutput:
        attributes = dict(output.attributes)
        usage = attributes.get("usage", {})
        cost = usage.get("cost") if isinstance(usage, dict) else None
        attributes["metrics"] = {
            "asset_extraction_seconds": round(extraction_seconds, 3),
            "processor_seconds": round(processor_seconds, 3),
            "cost_usd": cost if isinstance(cost, int | float) else None,
        }
        return output.model_copy(update={"attributes": attributes})
