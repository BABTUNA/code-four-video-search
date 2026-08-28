# Implementation plan

Build order for the pipeline in [pipeline.md](pipeline.md). Each phase is one focused
commit (or two), lands with its own verification, and leaves the repo runnable. Coding
rules throughout: as short and easy to understand as possible; never shorter at the
cost of clarity. No component imports another component — everything communicates
through `Doc` records and the store.

## Layout

```
src/c4search/
  config.py        # YAML config load; the config is the wiring diagram
  models.py        # Doc, Hit, Segment, Verdict — the only shared types
  store.py         # SQLite doc store + numpy vector arrays
  cache.py         # content-hash stage caching (~40 lines)
  registry.py      # name -> implementation lookup per seam
  media.py         # ffmpeg: proxy, audio, frames, loudness
  ingest.py        # runs registered extractors over videos
  extractors/      # transcribe, diarize, frames, caption, audio_events,
                   # arousal, detect, clock_ocr, motion
  search/          # plan, retrieve (bm25/dense/frames), fuse, rerank,
                   # merge, verify, abstain
  cli.py           # c4 ingest / c4 search / c4 eval
tests/             # contract tests parametrized over the registry + unit tests
configs/           # default.yaml + ablation configs
eval/              # queries.yaml, expand_queries.py, audit-sheet generation
```

## Phases

**0. Scaffolding** — remove the Phase-1 backend/frontend (preserved in git history);
create the package, `pyproject.toml` (uv), `models.py`, `store.py`, `cache.py`,
`registry.py`, `config.py`, and contract tests that every registered extractor/
retriever must pass. *Verify: `uv run pytest` green on an empty registry + a fake
extractor.*

**1. Media prep** — `media.py`: 480p proxy, 16 kHz mono wav, frames @0.5 fps, ebur128
loudness, all via ffmpeg with VideoToolbox. *Verify: run on one video, spot-check
outputs and timestamps.*

**2. Transcriber** — mlx-whisper large-v3-turbo with the three decode-failure
thresholds, VAD gating, stock-hallucination blocklist; word-timestamped utterance
Docs. *Verify: transcribe video_1, read the output against the audio; confirm no
hallucinated text over the music-heavy opening.*

**3. Diarization + speaker merge** — senko; label transcript Docs with speaker ids and
an officer/civilian heuristic. *Verify: spot-check speaker attribution on a traffic
stop.*

**4. Visual indexes** — SigLIP 2 frame embeddings; scene attributes (day/night,
indoor/outdoor) from the same vectors + luma; YOLO-World detections. *Verify: query a
few frames by text ("police car at night") and eyeball the top hits.*

**5. Audio indexes** — CLAP window embeddings, PANNs fixed-vocabulary tags, arousal
series, motion series, clock OCR. These are five small extractors sharing the pattern
from phases 2–4; grouped into one phase because each is <100 lines. *Verify: known
sirens/shouting in the corpus surface as events; clock OCR matches the overlay.*

**6. Captioner** — flash-tier VLM per 5-min 480p chunk via OpenRouter, policing
ontology prompt, transcript as temporal anchor, chunk-offset arithmetic. The one paid
stage; test on one chunk before batch. *Verify: captions for one video read correctly
against the footage; cost per chunk logged and within estimate.*

**7. Retrieval + fusion** — BM25 (bm25s), dense text (bge), frame similarity; RRF
k=60; `c4 search --no-verify` returns raw fused hits. *Verify: the six example queries
from the challenge return plausible top-10 hits on 2–3 indexed videos.*

**8. Planner** — LLM query plan (sub-queries, modalities, polarity, temporal
constraints, lexical variants); raw query always retained as a safety stream.
*Verify: unit-test the schema on the six example queries + negation and
temporal-anchor cases.*

**9. Rerank + temporal merge** — bge-reranker-v2-m3 on MPS; timeline projection,
smoothing, threshold-connect, gap-merge, AND-intersection, NMS. *Verify: candidate
segments for the example queries are tight and sensible before any verification.*

**10. Verifier + abstention** — local Qwen2.5-VL-7B (mlx-vlm), describe-first
checklist JSON, dark-frame rule, agreement-based confidence, API escalation on
"unclear"; three-tier output with evidence citations. *Verify: end-to-end `c4 search`
on all six example queries; verify rejects at least one plausible-but-wrong retrieval
candidate.*

**11. Evaluation** — bootstrap the labeled set (regex scan over transcripts+captions →
audit sheet → human tick-through), `c4 eval` computing Hit@1/Hit@5/abstention
accuracy; conformal calibration of the abstention threshold from the labeled pairs.
*Verify: metrics reproduce across two runs; ablation configs (transcript-only,
no-verify) run.*

**12. Scale + polish** — index the full chosen subset (~10–15 h), re-run eval,
ablation table into README, cost/time actuals, Loom script outline.

## Scope decisions

- **Corpus**: develop on 3 videos (~2 h); scale to ~10–15 h at phase 12. The challenge
  explicitly allows a subset.
- **Interface**: CLI only (`c4 ingest / search / eval`) — the challenge says a CLI is
  perfectly fine, and results are inspectable as formatted terminal output plus the
  cited evidence files. No frontend for this project.
- **Budget**: captioning the full subset ≈ $2–5; verification escalations pennies.
  Everything else local. Total well under $15 on the shared key.
- **The eval set doubles as the dev set** at this scale; stated openly in the README
  rather than pretending there is a held-out split.

## Commit discipline

One phase, one commit, present-tense subject, body says what and why. Failures and
reversals get committed too (e.g. the fixed-grid rejection already in history) — the
history is part of the submission narrative.
