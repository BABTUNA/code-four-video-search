from app.models import (
    Modality,
    ProcessorInformation,
    ProcessorOutput,
    Segment,
    SegmentAssets,
)


EXAMPLE_CONTENT = {
    Modality.VISUAL: "Example visual description for this segment.",
    Modality.AUDIO: "Example acoustic description for this segment.",
    Modality.TRANSCRIPT: "Example transcript for this segment.",
    Modality.OCR: "Example visible text for this segment.",
}


class FakeProcessor:
    def __init__(self, modality: Modality):
        self.modality = modality

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        return ProcessorOutput(
            type=f"{self.modality.value}_description",
            content=EXAMPLE_CONTENT[self.modality],
            attributes={"source": "fake_processor"},
            confidence=None,
            processor=ProcessorInformation(model="fake", version="1"),
        )
