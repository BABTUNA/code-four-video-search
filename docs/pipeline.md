# Pipeline: extraction and querying, as implemented

The operational spec, kept in sync with the code. [design.md](design.md) carries the
rationale, [research.md](research.md) the literature.

---

## Section 1 — Extraction (once per video, cached)

`c4 ingest` decodes each source once (480p proxy via VideoToolbox, 16 kHz mono wav,
0.5 fps frames, an ebur128 loudness series), then runs the configured extractors.
Every extractor emits the canonical record —
`Doc {video_id, t_start, t_end, modality, text, extra}`, float seconds on the video's
absolute timeline — into SQLite, with vectors as numpy arrays alongside. Stages are
cached by (source identity, config subtree); a rerun re-executes only what changed.

| Stage | Model / tool | Emits |
|---|---|---|
| transcribe | mlx-whisper large-v3-turbo; decode-failure thresholds (compression > 2.4, logprob < −1.0, no-speech > 0.6) + stock-output blocklist | word-timestamped transcript Docs |
| diarize | senko (CoreML); mic-proximity officer heuristic | speaker_turn Docs; transcript Docs inherit speaker + role by overlap |
| frames | SigLIP 2 (MPS), batched | frame Docs + vectors; scene Docs (day/night/indoors, zero-shot + luma floor) merged into spans |
| detect | YOLO-World, fixed vocabulary | object Docs per frame with detections |
| audio_events | CLAP on 10 s windows | audio_window Docs + vectors; labels above threshold in text |
| audio_tags | PANNs CNN14, AudioSet alarm subset | audio_tag Docs (gunshot/siren/screaming/…) |
| arousal | wav2vec2 dimensional model over speech-loud windows | vocal_arousal Docs for elevated runs |
| motion | frame-difference energy series (no model) | motion Docs for sustained high-motion spans |
| clock_ocr | Apple Vision OCR on sampled frames; regex + monotonicity filter | wall_clock anchor Docs |
| caption | flash-tier VLM per 5-min 1fps 480p chunk (the one paid stage); transcript in-prompt as temporal anchor; per-chunk response cache so a flaky chunk never re-bills the rest | caption Docs with policing-ontology tags and per-chunk cost |

Ingest ends by embedding all text-bearing Docs for dense retrieval and writing a
`media.json` per video (frame paths, fps, duration) that the verifier later reads.

Budget: ~15–20 min local compute per video-hour + $0.10–0.35 captioning. Captioning
runs sequentially within a video; chunks are cached individually.

---

## Section 2 — Querying (per query)

```
query -> plan -> per-sub-query retrieval -> RRF -> cross-encoder -> temporal merge
      -> scene/anchor filters -> VLM verification -> evidence tiers
```

**1. Plan.** One structured-output LLM call (temperature 0, disk-cached per query
text so ablation rungs and reruns see identical plans) produces ≤4 sub-queries with
target modalities, required/supporting roles, polarity, and up to 3 lexical variants;
plus an optional scene filter and an optional ordering anchor. Explicit negations
only. The unmodified query is always retained as a supporting stream. On API failure
the fallback is the identity plan.

**2. Retrieve** (per positive sub-query; each arm has a config flag). BM25 over the
query and its variants, dense text (bge) over the sub-query, SigLIP text-to-frame,
CLAP text-to-audio — top-100 each, fused by RRF (k=60, rank-based). Fused hits are
filtered to the sub-query's modalities (intersected with the config's global
allow-list, which is how restricted baselines work). Negative sub-queries retrieve
nothing; they become verifier checks.

**3. Rerank.** bge-reranker-v2-m3 cross-encoder scores the top (≤depth) text-bearing
fused hits against the sub-query; the top ~20 survive with rank-based weights.
Vector-only hits (frames, audio windows) keep their fused ranks. Models are loaded
once per process, not per query.

**4. Temporal merge.** Hits paint their weight over the seconds they span (instants
padded ±1 s) onto a per-second track per sub-query per video; tracks are Gaussian
smoothed (σ≈3 s) and thresholded relative to their peak; above-threshold runs connect
across ≤8 s gaps, take a minimum width and ±2 s padding. Spans of *required*
sub-queries intersect (a zero-hit required stream is demoted, not allowed to veto);
supporting-only plans union. Overlapping proposals merge; candidates rank by summed
track mass. Scene filters then drop candidates without a matching scene doc, and an
ordering anchor ("after the arrest") is grounded by an inner search and applied as an
interval restriction.

**5. Verify.** The verifier receives up to 8 frames sampled uniformly across the
candidate plus ±20 s of transcript with speaker roles. The prompt: describe first,
then judge each required element (the user's original query, plus any NOT-elements
from negations), returning structured JSON at temperature 0. Tier mapping: yes →
confirmed, no → rejected, unclear → candidate. On night footage a
*visibility-limited* "no" (one whose element checklist contains "unclear") is
softened to "unclear"; a transcript-grounded "no" stands. Tiers: API-first by
default; with `use_local: true` a local Qwen2.5-VL verdict comes first and only
unclear cases escalate to the API. Per-call cost is accumulated into the query's
telemetry.

**6. Present.** Ranked results with tier, span, wall-clock label when an OCR anchor
is near, the verifier's reason, and up to six evidence Docs (modality, time, text).
If nothing survives: "no confident match", with the closest rejected candidate shown.
Every run reports per-stage wall time and total API cost.

### Roadmap items deliberately not in the code

- Sample-agreement confidence + conformally calibrated abstention (needs a larger
  labeled set; tiers are rule-based today).
- HyDE-style expansion for weak dense retrievals.
- Peak-score frame selection for the verifier (sampling is uniform today).
- License-plate reading via per-character voting over detection crops (designed in
  design.md; not implemented).
