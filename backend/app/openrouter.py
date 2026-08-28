import base64
import json
from pathlib import Path
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
    ):
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required for real processors")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client

    async def chat_json(
        self,
        *,
        model: str,
        prompt: str,
        media_items: list[dict[str, Any]],
        response_model: type[ResponseModel],
        schema_name: str,
    ) -> tuple[ResponseModel, dict[str, Any]]:
        schema = response_model.model_json_schema()
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *media_items,
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        response = await self._post("/chat/completions", payload)

        try:
            content = response["choices"][0]["message"]["content"]
            output = response_model.model_validate_json(self._text_content(content))
        except (KeyError, IndexError, TypeError, ValidationError) as error:
            raise OpenRouterError("OpenRouter returned an invalid structured response") from error

        usage = response.get("usage", {})
        return output, usage if isinstance(usage, dict) else {}

    async def transcribe(self, *, model: str, audio_path: Path) -> dict[str, Any]:
        payload = {
            "model": model,
            "input_audio": {
                "data": encode_file(audio_path),
                "format": "wav",
            },
        }
        response = await self._post("/audio/transcriptions", payload)
        if not isinstance(response.get("text"), str):
            raise OpenRouterError("OpenRouter returned an invalid transcription")
        return response

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if self.http_client is not None:
                response = await self.http_client.post(
                    f"{self.base_url}{path}",
                    headers=headers,
                    json=payload,
                )
            else:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self.base_url}{path}",
                        headers=headers,
                        json=payload,
                    )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code
            raise OpenRouterError(
                f"OpenRouter request failed with status {status_code}"
            ) from error
        except (httpx.HTTPError, json.JSONDecodeError) as error:
            raise OpenRouterError("Could not communicate with OpenRouter") from error

        if not isinstance(body, dict):
            raise OpenRouterError("OpenRouter returned an invalid response")
        return body

    @staticmethod
    def _text_content(content: object) -> str:
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
            ).strip()
        else:
            raise TypeError("Message content is not text")

        if text.startswith("```json") and text.endswith("```"):
            return text[7:-3].strip()
        return text


def encode_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def data_url(path: Path, media_type: str) -> str:
    return f"data:{media_type};base64,{encode_file(path)}"
