from app.config import Settings
from app.models import Modality
from app.openrouter import OpenRouterClient
from app.processors.base import ModalityProcessor
from app.processors.fake import FakeProcessor
from app.processors.openrouter import (
    AudioProcessor,
    OcrProcessor,
    TranscriptProcessor,
    VisualProcessor,
)


def build_processors(settings: Settings) -> dict[Modality, ModalityProcessor]:
    if settings.processor_backend == "fake":
        return {modality: FakeProcessor(modality) for modality in Modality}

    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    return {
        Modality.VISUAL: VisualProcessor(client, settings.visual_model),
        Modality.AUDIO: AudioProcessor(client, settings.audio_model),
        Modality.TRANSCRIPT: TranscriptProcessor(client, settings.transcript_model),
        Modality.OCR: OcrProcessor(client, settings.ocr_model),
    }
