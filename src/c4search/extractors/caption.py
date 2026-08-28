import base64
import subprocess
from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.openrouter import chat_json
from c4search.registry import register_extractor

PROMPT = """You are indexing police body-worn camera footage for search.
Watch this video chunk and report the observable events with chunk-local
timestamps in seconds. Use precise policing vocabulary where it applies
(traffic stop, field sobriety test, handcuffing, frisk, foot pursuit, radio
call), and note people by appearance/role, vehicles, lighting, and visible
text. Describe only what is clearly visible: do not infer identity, intent,
intoxication, or guilt, and do not guess in poor lighting. The transcript
below is a temporal anchor - do not restate it as events.

Transcript of this chunk:
{transcript}"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["events"],
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["start_s", "end_s", "description", "tags"],
                "properties": {
                    "start_s": {"type": "number"},
                    "end_s": {"type": "number"},
                    "description": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


def chunk_spans(duration_s: float, chunk_s: float) -> list[tuple[float, float]]:
    spans = []
    start = 0.0
    while start < duration_s:
        spans.append((start, min(start + chunk_s, duration_s)))
        start += chunk_s
    return spans


def events_to_docs(events: list[dict], video_id: str, chunk_start: float,
                   chunk_end: float, cost: float | None) -> list[Doc]:
    """Chunk-local event times become absolute by arithmetic - the model is
    never trusted to know absolute time - and are clamped into the chunk."""
    length = chunk_end - chunk_start
    docs = []
    for event in events:
        start = chunk_start + min(max(event["start_s"], 0.0), length)
        end = chunk_start + min(max(event["end_s"], event["start_s"]), length)
        text = event["description"].strip()
        if not text:
            continue
        docs.append(Doc(
            video_id, round(start, 1), round(end, 1), "caption", text,
            {"tags": event.get("tags", []), "chunk_start": chunk_start,
             "cost_usd": cost},
        ))
    return docs


@register_extractor("caption")
class CaptionExtractor:
    """The one paid stage: a flash-tier VLM captions 5-minute chunks.

    Reads transcript Docs from the store as a temporal anchor, so it must be
    configured after `transcribe`.
    """

    name = "caption"

    def __init__(self, options: dict):
        self.model = options.get("model", "google/gemini-3.5-flash-lite")
        self.chunk_s = options.get("chunk_s", 300.0)
        self.base_url = options.get("base_url", "https://openrouter.ai/api/v1")

    def encode_chunk(self, proxy: Path, start: float, length: float, out: Path) -> None:
        result = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", str(length),
             "-i", str(proxy), "-vf", "fps=1", "-b:v", "150k", "-an", str(out)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[-300:]}")

    def caption_chunk(self, chunk_file: Path, transcript: str) -> tuple[list[dict], float | None]:
        video_url = "data:video/mp4;base64," + base64.b64encode(
            chunk_file.read_bytes()).decode()
        parsed, cost = chat_json(
            model=self.model,
            content=[
                {"type": "text",
                 "text": PROMPT.format(transcript=transcript or "(no speech)")},
                {"type": "video_url", "video_url": {"url": video_url}},
            ],
            schema=SCHEMA, schema_name="chunk_events", base_url=self.base_url,
        )
        return parsed["events"], cost

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path, store=None) -> list[Doc]:
        transcript_docs = store.docs(video.video_id, "transcript") if store else []

        docs = []
        for index, (start, end) in enumerate(chunk_spans(video.duration_s, self.chunk_s)):
            transcript = "\n".join(
                f"[{doc.t_start - start:.0f}s] {doc.text}"
                for _, doc in transcript_docs if start <= doc.t_start < end
            )
            chunk_file = workdir / f"chunk_{index:03d}.mp4"
            self.encode_chunk(assets.proxy, start, end - start, chunk_file)
            events, cost = self.caption_chunk(chunk_file, transcript)
            docs.extend(events_to_docs(events, video.video_id, start, end, cost))
            chunk_file.unlink()  # keep the cache dir small
        return docs
