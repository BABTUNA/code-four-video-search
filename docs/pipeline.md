# Pipeline: extraction and querying, end to end

The operational blueprint. [design.md](design.md) carries the rationale,
[research.md](research.md) the literature. Everything below runs locally on Apple
Silicon; **ingest costs $0 in API calls**, and a typical query costs $0 too — the paid
API is an escalation path, not a dependency.

---

## Section 1 — Extraction (once per video, local, cached)

One pass per stage over each video; every stage emits the same canonical record —
`Doc {video_id, t_start, t_end, modality, text, extra}` on the video's absolute
timeline — into SQLite (+ numpy arrays for vectors). Stages are keyed by content hash
of (input, config), so swapping one re-runs only that one.

```
video.mp4
  └─ ffmpeg (VideoToolbox): 480p proxy, 16kHz mono wav, frames @0.5fps, loudness (ebur128)
       ├─ AUDIO PIPE (CPU/ANE)                    ├─ VISION PIPE (GPU/MPS)
       │  transcriber   mlx-whisper turbo         │  frame embedder  SigLIP 2 @0.5fps
       │  diarizer      senko (CoreML)            │  captioner       Qwen2.5-VL-3B (mlx-vlm)
       │  audio events  CLAP + PANNs CNN14        │  detector        YOLO-World @0.5fps
       │  vocal arousal wav2vec2 (audeering)      │  scene attrs     SigLIP zero-shot + luma
       │                                          │  clock OCR       ocrmac on overlay crop
       └─ motion        optical-flow magnitude series (CPU)
                                ↓
                Doc store (SQLite) + vector arrays, one shared timeline
```

| Stage | Model / tool | What it emits | Why it earns its place |
|---|---|---|---|
| Transcriber | `mlx-whisper` large-v3-turbo (~10x realtime) | word-timestamped utterances | dominant signal; hardened with the Whisper paper's own thresholds (compression > 2.4, logprob < −1.0, no-speech > 0.6), VAD gating, and a stock-hallucination blocklist — hallucinated text matching a query is a precision disaster |
| Diarizer | `senko` (CoreML; ~8s per audio-hour), pyannote fallback | speaker turns | "who said it" — officer vs civilian, mapped heuristically (mic proximity, speech share); powers queries like "civilian says X" |
| Captioner | **Qwen2.5-VL-3B 4-bit via `mlx-vlm`**, 1 frame/10s, conservative "describe only what is clearly visible" prompt | scene descriptions | the index whose vocabulary we control (policing ontology); local VLM captions-as-index has direct precedent (NarVid, VideoAgent found caption source matters less than expected) — and it removes the only paid ingest stage |
| Frame embedder | SigLIP 2 @0.5fps (MPS) | image vectors | catches what captions omit; frame-level is the evidence-backed baseline for continuous footage |
| Scene attributes | same SigLIP embeddings, zero-shot prompts + mean-luma check | day/night, indoor/outdoor tags | answers "at night" as a *filter*, nearly free — reuses existing vectors |
| Audio events | CLAP (open-vocab) + PANNs CNN14 (fixed AudioSet head) | event spans: shouting, siren, gunshot, glass... | prosody is invisible to transcripts; PANNs' supervised head is more reliable than CLAP prompts on the high-stakes fixed vocabulary (gunshot/siren/scream), so both run |
| Vocal arousal | audeering wav2vec2 (dimensional, trained on naturalistic audio) on speech windows | arousal time series | graded vocal escalation — categorical emotion is unreliable in the wild (~0.34 F1), arousal is the defensible signal |
| Detector | YOLO-World @0.5fps (MPS), fixed vocab: person, vehicle, weapon, flashlight, handcuffs, dog... | object spans | structured object evidence; night/shaky false negatives expected — indexed, never trusted alone |
| Clock OCR | `ocrmac` (Apple Vision) on the burned-in timestamp crop, regex + monotonicity filter | wall-clock anchors | absolute time ("what happened at 11:42 PM") and cross-video alignment, ~150ms/crop |
| Motion | optical-flow magnitude per second (OpenCV, CPU) | high-motion tags | foot pursuits/struggles from camera motion — precedent in bodycam activity recognition (arXiv 1904.09062), no model needed |
| Loudness | ffmpeg ebur128 | loudness envelope | free ranking prior for shouting/impacts |

Budget: ~35–65 min per video-hour, dominated by captioning; audio and vision pipes
contend little and run concurrently, so effective wall ≈ max(pipes) ≈ 30–45 min/hour.
Indexing 12 hours overnight is comfortable. API cost: **$0**.

---

## Section 2 — Querying (per query, local; API only as escalation)

```
query ──> Planner (JSON plan) ──> per-sub-query retrieval ──> RRF fusion (k=60)
             │                        BM25 + dense + frames
             │                              ↓
             │                   Cross-encoder rerank (bge-reranker-v2-m3, top→10)
             │                              ↓
             │                   Temporal aggregation → candidate segments (top 5–10)
             │                              ↓
             └──────────────────> Verifier (local Qwen2.5-VL-7B; API on "unclear")
                                            ↓
                        confirmed / unverified-candidate / no confident match
```

**1. Planner** — one LLM call emits a JSON plan: ≤4 sub-queries, each tagged with
target modalities, `required|supporting` role, and polarity. Rules with teeth:
- *Negation never reaches a retriever.* Bi-encoders rank negated pairs at or below
  random (NevIR); negations are extracted here and enforced at rerank/verify.
- *Temporal constraints split in two*: attribute-like ("at night") become filters over
  scene-attribute tags; event-anchored ("after the arrest") ground the anchor first,
  then restrict the search interval (two-hop, capped at 2 iterations — 2 iterations
  capture ~95% of the benefit of 5).
- The raw query always rides along as a safety-net retrieval stream, so planning can
  never do worse than not planning.

**2. Retrieval** (recall-oriented, free) — per sub-query: BM25 (`bm25s`, plus ≤3
planner-emitted lexical variants to bridge query↔spoken vocabulary, e.g. "breathalyzer"
↔ "point two four nine") + dense text (bge) over transcript/caption/detection docs +
SigLIP text-to-frame similarity. Top-100 per list, fused by RRF with k=60 (the flat
optimum; not tuned). HyDE expansion only when dense scores come back weak.

**3. Rerank** (precision, local) — `bge-reranker-v2-m3` cross-encoder on MPS scores the
top ~100 fused hits against the sub-query text; keep ~10. Worth +10–30% relative
nDCG@10 over first-stage retrieval, and cross-encoders are the only architecture above
random on negation — this is where "NOT handcuffed" bites.

**4. Temporal aggregation** — project every hit onto the timeline (frame hits get ±
half the sampling interval); Gaussian-smooth a fused per-second score track (σ≈3s);
threshold-connect into proposals; merge gaps <5–10s; enforce minimum width ~2s and pad
±2–3s; for AND-logic, keep only segments overlapped by *every* required sub-query
(scored by min); NMS at IoU 0.5. Top 5–10 candidates proceed.

**5. Verifier** — local Qwen2.5-VL-7B (4-bit, mlx-vlm) sees 8–16 frames per candidate
(peak-score frame guaranteed) at ~448–768px plus ±20s of transcript. Prompt is
describe-first, then an element checklist, then structured JSON verdict — never told
what the retriever expects (VLMs measurably capitulate to leading framing; VISE). Rules:
- *Dark frames weaken "no".* In low light VLMs predominantly miss present objects
  rather than hallucinate (DarkQA) — dark-segment negatives become "unclear", and
  audio/transcript evidence carries more weight at night.
- *Confidence is not a verbalized number* (VLMs are systematically overconfident);
  it's sample agreement: temperature-0 single shot for clear verdicts, 3-sample vote
  only near threshold, and the agreement rate feeds abstention.
- *Escalation, not dependence*: candidates the local verifier marks "unclear" go to an
  API VLM via OpenRouter — typically a small fraction of candidates, pennies.

**6. Abstention** — the threshold isn't eyeballed: conformal calibration on ~50–100
labeled (query, verdict) pairs from our own eval set gives a threshold with a bounded
false-match rate. Output has three tiers: **confirmed** (verified above threshold),
**candidate — unverified** (strong retrieval, unclear verdict; shown, labeled), and
**no confident match** (with the closest rejected candidate and the verifier's reason,
so the reviewer can judge). A cheap score-distribution pre-gate short-circuits obvious
no-answer queries before verification runs.

**7. Presentation** — each result is `[HH:MM:SS–HH:MM:SS]` (plus wall-clock when the
overlay OCR anchors it), the verifier's cited frame, modality-tagged evidence
(transcript quote with word times, audio-event tag, detection, caption line), the
per-element checklist, and the confidence tier. One claim, all supporting spans merged.

**Cost per query: ~$0** (planner can run on a local LLM or a sub-cent API call;
verification is local) — API spend only on escalated verifications.
