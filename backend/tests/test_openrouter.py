import asyncio
import json

import httpx

from app.models import Segment, SegmentAssets
from app.openrouter import OpenRouterClient
from app.processors.openrouter import AudioProcessor


def create_assets(tmp_path) -> SegmentAssets:
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"test audio")
    video_path = tmp_path / "segment.mp4"
    video_path.write_bytes(b"test video")
    frame_path = tmp_path / "frame.jpg"
    frame_path.write_bytes(b"test frame")
    return SegmentAssets(
        segment_id="video_1:0-30000",
        video_path=video_path,
        audio_path=audio_path,
        frame_paths=[frame_path],
        video_height=720,
        frame_interval_seconds=5,
        source_size_bytes=1,
        source_modified_ns=1,
    )


def test_audio_processor_maps_mocked_openrouter_response(tmp_path) -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["messages"][0]["content"][1]["type"] == "input_audio"
        assert payload["response_format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json={
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 20,
                    "cost": 0.0012,
                },
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "description": "A raised voice over road noise.",
                                    "speech_style": ["raised"],
                                    "background_sounds": ["road noise"],
                                }
                            )
                        }
                    }
                ]
            },
        )

    async def run_processor():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle_request)
        ) as http_client:
            client = OpenRouterClient(
                api_key="test-key",
                base_url="https://openrouter.test/api/v1",
                http_client=http_client,
            )
            processor = AudioProcessor(client, "test/audio-model")
            return await processor.process(
                Segment(
                    segment_id="video_1:0-30000",
                    media_id="video_1",
                    start_ms=0,
                    end_ms=30_000,
                ),
                create_assets(tmp_path),
            )

    output = asyncio.run(run_processor())
    assert output.content == "A raised voice over road noise."
    assert output.attributes["speech_style"] == ["raised"]
    assert output.attributes["usage"]["cost"] == 0.0012
    assert output.confidence is None


def test_transcription_uses_dedicated_endpoint(tmp_path) -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/api/v1/audio/transcriptions"
        assert payload["input_audio"]["format"] == "wav"
        assert not payload["input_audio"]["data"].startswith("data:")
        return httpx.Response(200, json={"text": "Please step out of the car."})

    async def transcribe():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle_request)
        ) as http_client:
            client = OpenRouterClient(
                api_key="test-key",
                base_url="https://openrouter.test/api/v1",
                http_client=http_client,
            )
            return await client.transcribe(
                model="test/transcription-model",
                audio_path=create_assets(tmp_path).audio_path,
            )

    response = asyncio.run(transcribe())
    assert response["text"] == "Please step out of the car."
