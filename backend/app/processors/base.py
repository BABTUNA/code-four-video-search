from typing import Protocol

from app.models import Modality, ProcessorOutput, Segment, SegmentAssets


class ModalityProcessor(Protocol):
    modality: Modality

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        ...
