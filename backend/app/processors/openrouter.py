from pydantic import BaseModel, ConfigDict

from app.models import (
    Modality,
    ProcessorInformation,
    ProcessorOutput,
    Segment,
    SegmentAssets,
)
from app.openrouter import OpenRouterClient, data_url, encode_file


class VisualObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    people: list[str]
    objects: list[str]
    actions: list[str]


class AudioObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    speech_style: list[str]
    background_sounds: list[str]


class OcrObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    visible_text: list[str]


class VisualProcessor:
    modality = Modality.VISUAL

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        observation, usage = await self.client.chat_json(
            model=self.model,
            prompt=(
                "Describe only what is visibly observable in this silent video segment. "
                "List people by appearance or role only when visually supported, plus "
                "objects and actions. Do not infer identity, intent, intoxication, or guilt."
            ),
            media_items=[
                {
                    "type": "video_url",
                    "video_url": {
                        "url": data_url(assets.video_path, "video/mp4"),
                    },
                }
            ],
            response_model=VisualObservation,
            schema_name="visual_observation",
        )
        return ProcessorOutput(
            type="scene_description",
            content=observation.description,
            attributes={
                "people": observation.people,
                "objects": observation.objects,
                "actions": observation.actions,
                "usage": usage,
            },
            processor=ProcessorInformation(model=self.model),
        )


class AudioProcessor:
    modality = Modality.AUDIO

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        observation, usage = await self.client.chat_json(
            model=self.model,
            prompt=(
                "Describe the acoustic properties of this audio segment. Focus on audible "
                "speech style such as calm, raised, overlapping, or unclear, and on background "
                "sounds. Do not transcribe speech or infer identity, intent, or intoxication."
            ),
            media_items=[
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": encode_file(assets.audio_path),
                        "format": "wav",
                    },
                }
            ],
            response_model=AudioObservation,
            schema_name="audio_observation",
        )
        return ProcessorOutput(
            type="acoustic_description",
            content=observation.description,
            attributes={
                "speech_style": observation.speech_style,
                "background_sounds": observation.background_sounds,
                "usage": usage,
            },
            processor=ProcessorInformation(model=self.model),
        )


class TranscriptProcessor:
    modality = Modality.TRANSCRIPT

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        response = await self.client.transcribe(
            model=self.model,
            audio_path=assets.audio_path,
        )
        attributes = {}
        if response.get("language"):
            attributes["language"] = response["language"]
        if response.get("usage"):
            attributes["usage"] = response["usage"]

        return ProcessorOutput(
            type="transcript",
            content=response["text"],
            attributes=attributes,
            processor=ProcessorInformation(model=self.model),
        )


class OcrProcessor:
    modality = Modality.OCR

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        media_items = [
            {
                "type": "image_url",
                "image_url": {"url": data_url(path, "image/jpeg")},
            }
            for path in assets.frame_paths
        ]
        observation, usage = await self.client.chat_json(
            model=self.model,
            prompt=(
                "Read visible text across these chronological frames. Preserve the text as "
                "shown, omit duplicates, and briefly describe where it appears. Do not guess "
                "characters that are unreadable."
            ),
            media_items=media_items,
            response_model=OcrObservation,
            schema_name="ocr_observation",
        )
        return ProcessorOutput(
            type="visible_text",
            content=observation.description,
            attributes={
                "visible_text": observation.visible_text,
                "usage": usage,
            },
            processor=ProcessorInformation(model=self.model),
        )
