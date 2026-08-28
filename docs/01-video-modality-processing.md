# Phase 1: Video and Modality Processing

## Goal

Build the smallest complete system that can:

1. Discover local videos.
2. Split a selected video into shared, fixed-time segments.
3. Run replaceable visual, audio, transcript, and OCR processors on every segment.
4. Store the resulting segment-level evidence.
5. Let a user inspect the processed data in a simple web UI.

Semantic search is deliberately excluded from this phase. The purpose is to prove that processing, persistence, and inspection work before adding retrieval.

## Code rules

- Prefer the shortest implementation that is still easy to understand.
- Do not use shorthand when an explicit version is clearer.
- Give each function one clear responsibility.
- Use descriptive names such as `segment_duration_ms`, not abbreviations such as `seg_dur`.
- Keep model names, prompts, and segmentation defaults in configuration.
- Add an abstraction only when it creates a real replacement boundary.
- Avoid infrastructure that this dataset does not require.

## User experience

### Video library page

Show every discovered video with:

- Filename
- Duration
- Processing status
- Latest processing configuration
- A link to open the video

### Video detail page

The user can:

- Play the original video.
- Choose segment duration. Default: `30 seconds`.
- Choose segment overlap. Default: `5 seconds`.
- Select the modalities to process.
- Start processing.
- See processing progress and errors.
- Select a completed processing run.
- Browse its segments in chronological order.
- Click a segment to seek the video player to `start_ms`.
- Inspect visual, audio, transcript, and OCR evidence for that segment.

Only expose controls that help demonstrate the architecture. Model overrides and raw prompts can remain in backend configuration instead of cluttering the page.

## System flow

```text
Local videos
    ↓
Media catalog
    ↓
Processing configuration
    ↓
Shared fixed-window segmenter
    ↓
Replaceable modality processors
    ↓
Normalized segment-level evidence
    ↓
SQLite
    ↓
FastAPI
    ↓
Next.js inspection UI
```

## Technology stack

### Backend

- Python
- FastAPI for the HTTP API
- Pydantic for shared data contracts
- FFmpeg and FFprobe for media operations
- OpenRouter through `httpx` for model calls
- SQLite for media metadata, processing runs, segments, and evidence
- Typer for ingestion and processing CLI commands
- pytest for tests

### Frontend

- Next.js with TypeScript
- Tailwind CSS
- A small set of shadcn/ui components

Do not add Postgres, Redis, Celery, or cloud storage in this phase.

## Project structure

```text
backend/
  app/
    api/
    processors/
      visual.py
      audio.py
      transcript.py
      ocr.py
    media/
      catalog.py
      segmenter.py
    repositories/
    config.py
    models.py
    processing.py
  tests/
  pyproject.toml

frontend/
  app/
    page.tsx
    videos/[mediaId]/page.tsx
  components/
  lib/

data/
  app.db
  derived/

c4-videos/
```

Keep orchestration in `processing.py`. Processor files should contain modality-specific behavior, not database or UI logic.

## Core contracts

### Processing configuration

```json
{
  "segment_duration_ms": 30000,
  "segment_overlap_ms": 5000,
  "modalities": ["visual", "audio", "transcript", "ocr"]
}
```

Validation rules:

- Duration must be greater than zero.
- Overlap must be zero or greater.
- Overlap must be smaller than duration.
- At least one modality must be selected.

### Segment

Every modality receives the same segment boundaries.

```json
{
  "segment_id": "video_1:25000-55000",
  "media_id": "video_1",
  "start_ms": 25000,
  "end_ms": 55000
}
```

The segment is the atomic unit for processing, later retrieval, evaluation, and returned timestamps. Processors do not create their own subsegments.

### Segment assets

FFmpeg creates a reusable asset bundle for a segment before real modality processing:

```text
data/derived/video_1/0-30000/
  segment.mp4
  audio.wav
  frames/
    frame_001.jpg
    frame_002.jpg
  assets.json
```

- `segment.mp4` is a compressed, video-only 720p clip for visual analysis.
- `audio.wav` is mono 16 kHz PCM for audio analysis and transcription.
- Full-resolution frames are sampled every five seconds for OCR.
- `assets.json` marks a complete cached extraction. Missing or partial assets are regenerated.

An individual modality asset may be shorter when that stream is absent from part of the source timeline. For example, `video_1` has audio at `0s` but its video stream begins near `3s`. The system keeps the canonical segment boundary at `0–30s` and does not invent visual frames for the missing interval.

### Evidence

```json
{
  "run_id": "run_123",
  "segment_id": "video_1:25000-55000",
  "media_id": "video_1",
  "start_ms": 25000,
  "end_ms": 55000,
  "modality": "audio",
  "type": "acoustic_description",
  "content": "A man speaks loudly over traffic noise.",
  "attributes": {
    "labels": ["raised_voice", "traffic"],
    "volume_change_db": null,
    "pitch_increase": null
  },
  "confidence": null,
  "processor": {
    "model": "google/gemini-3.7-flash",
    "version": "1"
  }
}
```

`content` is the open-ended description that Phase 2 will embed. `type` and `attributes` support inspection and future filtering. Do not invent confidence or numeric measurements that a processor did not actually compute.

## Replaceable processors

Each processor implements one small interface:

```python
class ModalityProcessor(Protocol):
    modality: Modality

    async def process(
        self,
        segment: Segment,
        assets: SegmentAssets,
    ) -> ProcessorOutput:
        ...
```

`ProcessorOutput` contains the modality-specific type, content, attributes, confidence, and processor metadata. The processing runner adds the run, media, and segment identifiers to create the normalized `Evidence` record. This keeps storage concerns out of model adapters.

The processing runner receives processors through a registry:

```python
processors = {
    Modality.VISUAL: VisualProcessor(client, settings.visual_model),
    Modality.AUDIO: AudioProcessor(client, settings.audio_model),
    Modality.TRANSCRIPT: TranscriptProcessor(client, settings.transcript_model),
    Modality.OCR: OcrProcessor(client, settings.ocr_model),
}
```

The runner depends on `ModalityProcessor`, not on Gemini or OpenRouter classes. Replacing one modality therefore changes configuration or one registry entry rather than the orchestration flow.

## Modality responsibilities

| Modality | Input | Output responsibility |
| --- | --- | --- |
| Visual | Segment video or sampled frames | Objects, people, clothing, actions, environment, and scene description |
| Audio | Extracted segment audio | Vocal intensity, speech style, environmental sound, and non-speech events |
| Transcript | Extracted segment audio | Spoken words with no acoustic interpretation |
| OCR | High-resolution sampled frames | Visible text such as signs, plates, and documents |

Audio describes how something sounds; transcript records what was said. This separation avoids duplicating responsibility.

## Processing behavior

1. Register videos from `c4-videos/` with FFprobe metadata.
2. Create a processing run from the selected configuration.
3. Generate fixed overlapping segment records on the canonical source timeline.
4. Extract and cache one shared asset bundle for each segment.
5. Process modalities sequentially at first so behavior and failures are easy to follow.
6. Validate every processor response with Pydantic.
7. Save each evidence record immediately so a partial run remains inspectable.
8. Update the processing run with completed, failed, and total counts.
9. Store extraction time, processor latency, and provider-reported cost with the evidence.

A new configuration creates a new processing run. Previous runs remain available for comparison and are never silently overwritten.

## Storage

Use five small SQLite tables:

```text
media
  media_id, filename, path, duration_ms, created_at

processing_runs
  run_id, media_id, status, configuration_json,
  completed_items, failed_items, total_items, error, created_at

segments
  segment_id, media_id, start_ms, end_ms

evidence
  run_id, segment_id, modality, type, content,
  attributes_json, confidence, processor_json

processing_errors
  run_id, segment_id, modality, message, created_at
```

Important keys:

- `segments.segment_id` is unique.
- `(run_id, segment_id, modality)` is unique in `evidence`.
- `(run_id, segment_id, modality)` is unique in `processing_errors`.
- Index `segments` by `(media_id, start_ms)`.
- Index `evidence` by `(run_id, segment_id)`.

One processing item means one `(segment, modality)` pair. This keeps progress accurate when a run processes several modalities or one processor fails independently.

Use the standard-library `sqlite3` module and clear repository functions. An ORM would add more code than value here.

## API

```text
GET  /api/videos
GET  /api/videos/{media_id}
GET  /api/videos/{media_id}/file
POST /api/videos/{media_id}/processing-runs
GET  /api/processing-runs/{run_id}
GET  /api/processing-runs/{run_id}/segments
GET  /api/processing-runs/{run_id}/errors
```

Create a processing run:

```json
POST /api/videos/video_1/processing-runs

{
  "segment_duration_ms": 30000,
  "segment_overlap_ms": 5000,
  "modalities": ["visual", "audio", "transcript", "ocr"],
  "max_segments": 1
}
```

Return `202 Accepted` with a `run_id`. A lightweight in-process background task calls the same processing runner used by the CLI. Persist status in SQLite and process one video at a time. The limitations of in-process jobs are acceptable for this take-home and should be documented.

## Configuration

Use environment variables for secrets and a typed settings object for defaults:

```text
PROCESSOR_BACKEND=fake
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
VISUAL_MODEL=google/gemini-3.7-flash
AUDIO_MODEL=google/gemini-3.7-flash
TRANSCRIPT_MODEL=openai/gpt-4o-mini-transcribe
OCR_MODEL=google/gemini-3.7-flash
```

Commit `.env.example`, never `.env` or an API key.

## Implementation order

1. Scaffold the Python and Next.js applications.
2. Define Pydantic contracts and the SQLite schema.
3. Build media discovery and FFprobe metadata extraction.
4. Build and test the fixed-window segmenter.
5. Implement the processor interface and one fake processor.
6. Build the processing runner and persistence using the fake processor.
7. Add the video library and detail pages.
8. Connect progress polling and evidence inspection.
9. Replace fake processors one modality at a time with real implementations.
10. Add focused tests and a one-command local setup.

The fake processor is intentional: it proves the complete pipeline before model latency, cost, and response formatting complicate debugging.

## Tests

Prioritize small tests around system boundaries:

- Segment windows are correct at the beginning and end of a video.
- Invalid overlap is rejected.
- Every processor receives identical segment timestamps.
- Malformed model output fails validation without losing earlier evidence.
- Reprocessing creates a new run instead of overwriting an old run.
- API responses match the Pydantic contracts.
- Clicking a segment seeks the player to the expected timestamp.

Do not test model intelligence in unit tests. Save a few representative processor responses as fixtures and test parsing separately.

## Phase 1 acceptance criteria

- A fresh developer can configure and start the project from the README.
- The UI lists the local videos.
- A user can choose segmentation settings and modalities for one video.
- Processing produces shared, timestamp-aligned evidence for every selected modality.
- Progress and processor failures are visible.
- A user can click any processed segment, play it, and inspect all associated evidence.
- Changing one processor does not require changes to the segmenter, runner, API, or UI.

## Deferred until later

- Semantic search and vector indexes
- Query planning and score fusion
- Reranking
- Precision and recall evaluation
- Adjacent-result merging
- Distributed job queues and production authentication
