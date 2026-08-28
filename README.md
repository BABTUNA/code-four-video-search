# Code Four Video Search

Natural language search over law enforcement body camera footage.

Ask questions such as:

```text
Find an officer reading someone their Miranda rights.
Show interactions where a person is being handcuffed.
Find a vehicle stopped by police at night.
```

The system returns timestamped video segments with the transcript, visual, and audio
evidence that produced each result.

## How it works

```text
Video
  ↓
Modality extractors
  Transcript | Captions | Frames | Objects | Audio | Motion | OCR
  ↓
Timestamped evidence index
  ↓
Query planner
  Breaks the request into searchable concepts and constraints
  ↓
Multimodal retrieval
  BM25 | Dense text | Frame embeddings | Audio embeddings
  ↓
Rank fusion and temporal merging
  Combines evidence that occurs at the same time
  ↓
VLM verification
  Reviews the strongest candidates using real frames and transcripts
  ↓
Confirmed results, possible candidates, or no confident match
```

The pipeline retrieves broadly first, then applies the more expensive verifier only
to a small number of candidates. This keeps indexing reusable and query costs low.

## Evidence model

Every extractor produces the same small record type:

```python
Doc(
    video_id="video_13",
    t_start=565.0,
    t_end=595.0,
    modality="transcript",
    text="You have the right to remain silent...",
    extra={"speaker": "officer"},
)
```

Each modality keeps its natural timing. A transcript sentence may span several
seconds while a sampled frame represents one instant. Evidence is aligned on the
shared video timeline during search instead of forcing everything into fixed chunks.

## Replaceable components

Extractors and search settings are selected through YAML configuration and a small
registry. A model can be replaced without changing the `Doc` contract or the rest of
the pipeline.

Current extractors include:

* **Speech:** MLX Whisper for transcripts and word timing
* **Speaker turns:** Senko for diarization and speaker hints
* **Captions:** Gemini through OpenRouter for event descriptions
* **Frames:** SigLIP 2 for open vocabulary visual retrieval
* **Objects:** YOLO World for people, vehicles, and other objects
* **Audio:** CLAP and PANNs for events such as shouting or sirens
* **Vocal activity:** wav2vec2 for arousal signals without emotion labels
* **Motion:** OpenCV for camera movement and pursuit evidence
* **Clock:** Apple Vision OCR for burned in wall clock timestamps

The default index uses SQLite for evidence records and NumPy arrays for vectors. At
this corpus size, a separate vector database would add complexity without a useful
speed improvement.

## Quickstart

Requirements:

* Apple Silicon
* Python 3.11
* `ffmpeg`
* [`uv`](https://docs.astral.sh/uv/)
* An OpenRouter API key

```bash
uv sync
```

Create `.env`:

```text
OPENROUTER_API_KEY=your-key
```

Index videos:

```bash
uv run c4 ingest c4-videos/video_1.mp4 c4-videos/video_2.mp4
```

Search:

```bash
uv run c4 search "an officer reads someone their Miranda rights"
```

Run the evaluation:

```bash
uv run c4 eval
```

Processing stages are cached, so an interrupted ingest can resume without repeating
completed work.

## Evaluation

The current evaluation corpus contains:

* 20 videos
* 6.67 hours of footage
* About 39,500 indexed evidence records
* 24 queries
* 18 answerable queries with 72 labeled spans
* 6 no answer queries containing realistic distractors

The recommended configuration from the latest published full run produced:

* Hit at 1: 0.50
* Hit at 5: 0.67
* Correct no answer decisions: 6 of 6
* False abstentions: 3
* Average query time: 12.8 seconds
* Average API cost: $0.014

Captions produced the largest retrieval improvement. Verification correctly rejected
all six no answer traps, but it also rejected three answerable queries. This is the
main precision versus recall tradeoff in the current system.

A prediction is counted as a hit when its temporal intersection over union is at
least 0.3 or its midpoint falls inside a labeled span. This evaluation measures
ranking and abstention. It does not yet provide full segment level precision and
recall.

See [eval/queries.yaml](eval/queries.yaml) for labels and `eval/results-*.json` for
individual runs.

## Important tradeoffs

* Per modality timestamps preserve precise evidence better than fixed ingest chunks.
* Captions make visual events searchable even when nobody names them in speech.
* Embeddings are useful for retrieval but unreliable for negation and attribute
  binding, so final constraints are checked by the verifier.
* VLMs are not trusted to produce timestamps. All timestamps come from media offsets,
  transcript timing, or frame positions.
* The system may return no confident match when evidence is weak. For evidence review,
  a supported refusal is safer than a confident false result.

## Current limitations

* The evaluation set was also used during development.
* Labels were discovered partly through the system's own transcripts and captions.
* Prosody queries require additional listening based labels.
* License plates can be surfaced as candidate segments, but reliable plate reading is
  not implemented.
* Anchor based ordering and negation handling need broader test coverage.
* Evaluation focuses on ranking and abstention rather than complete precision and
  recall.

## Project guide

```text
src/c4search/extractors/  Modality processors
src/c4search/search/      Planning, retrieval, merging, and verification
src/c4search/store.py     Evidence and vector storage
src/c4search/ingest.py    Video processing workflow
src/c4search/evaluate.py  Evaluation metrics
configs/                  Replaceable pipeline configurations
eval/                     Queries, labels, and result files
tests/                    Unit tests
docs/                     Detailed design and research notes
```

More detail:

* [Design rationale](docs/design.md)
* [Pipeline specification](docs/pipeline.md)
* [Research review](docs/research.md)
* [Build plan](docs/plan.md)
