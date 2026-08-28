# Code Four Video Search

This project processes body-camera videos into shared, fixed-time segments and produces inspectable visual, audio, transcript, and OCR evidence. Semantic search is added in Phase 2.

## Setup

Requirements: Homebrew FFmpeg, `uv`, Node.js, and npm.

```bash
cp .env.example .env
make setup
```

The app defaults to fake modality processors, so an OpenRouter key is not required for local UI testing.

## Run

Start the backend:

```bash
make backend
```

Start the frontend in a second terminal:

```bash
make frontend
```

Open [http://localhost:3000](http://localhost:3000).

## Use real modality processors

Set these values in `.env` and restart the backend:

```dotenv
PROCESSOR_BACKEND=openrouter
OPENROUTER_API_KEY=your-key
```

The visual, acoustic, transcription, and OCR processors can each use a different model through the model variables in `.env`. New processing runs default to one segment as a cost guard; increase **Maximum segments** in the UI when you are ready. Segment duration is capped at 60 seconds.

Each evidence card records processor latency and OpenRouter's reported usage and cost. The selected segment shows the combined elapsed time and model cost.

## Extract one segment

Create the video, audio, and OCR-frame assets for the first 30 seconds of `video_1`:

```bash
cd backend
uv run python -m app.cli extract-segment video_1 \
  --start-seconds 0 \
  --duration-seconds 30
```

Assets are cached under `data/derived/video_1/0-30000/`. Add `--force` to replace them.

## Test

```bash
make test
```

Videos belong in `c4-videos/`. Generated metadata and evidence are stored under `data/`; neither directory is committed to Git.

## Design

- [Phase 1: video and modality processing](docs/01-video-modality-processing.md)
- [Phase 2: semantic indexing and querying](docs/02-semantic-querying.md)
- [Model research](docs/model-research/README.md)
