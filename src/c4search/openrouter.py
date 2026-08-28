"""Minimal OpenRouter client shared by the captioner, planner, and verifier."""

import json
import os
from pathlib import Path


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key and Path(".env").exists():
        for line in Path(".env").read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (env or .env)")
    return key


def chat_json(
    model: str,
    content: list[dict],
    schema: dict,
    schema_name: str,
    base_url: str = "https://openrouter.ai/api/v1",
    timeout: float = 240.0,
) -> tuple[dict, float | None]:
    """One structured-output chat call; returns (parsed JSON, reported cost).

    Retries once - transient drops happen on large uploads.
    """
    import httpx

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": schema_name, "strict": True, "schema": schema}},
        "usage": {"include": True},
        "temperature": 0,  # planning and verification should be repeatable
    }
    headers = {"Authorization": f"Bearer {api_key()}"}

    last_error = None
    for _ in range(2):
        try:
            response = httpx.post(
                f"{base_url}/chat/completions", json=payload,
                headers=headers, timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
            parsed = json.loads(body["choices"][0]["message"]["content"])
            return parsed, body.get("usage", {}).get("cost")
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as error:
            last_error = error
    raise RuntimeError(f"OpenRouter call failed after retry: {last_error}")
