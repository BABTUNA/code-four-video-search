# Design: natural-language search over body-worn camera footage

## The core insight

Hour-scale video search fails at *finding* moments, not *recognizing* them. On hour-long
video benchmarks, ~85% of temporal-grounding failures are search failures (the predicted
interval is nowhere near the event), not perception failures — and a simple frame-level
retrieval baseline beats every open Video-LLM at hour scale
([ExtremeWhenBench, arXiv 2606.12300](https://arxiv.org/abs/2606.12300)). Better search
also beats more frames: under a fixed 32-frame budget, a temporal search stage lifts
long-video QA accuracy more than model upgrades do
([T*, arXiv 2504.02259](https://arxiv.org/abs/2504.02259)).

So the system splits recall from precision:

1. **Cheap indexes propose; a VLM disposes.** Local, nearly-free indexes (transcript,
   frame embeddings, audio events, captions) cast a wide recall-oriented net. A paid VLM
   inspects only the top candidates — real frames plus transcript — and can say no.
2. **Timestamps come from our clock, never the model's memory.** ASR word times, frame
   indexes, and chunk offsets are computed by us; VLMs only ever describe short clips.
3. **Every answer carries its evidence** — the transcript lines, caption events, and
   frames that justify it — and the system abstains rather than guess.

Embeddings alone provably cannot carry precision: CLIP-family models score at chance on
negated queries ([NegBench, arXiv 2501.09425](https://arxiv.org/abs/2501.09425)), barely
above bag-of-words on attribute binding — "red shirt" vs "red car"
([ARO, arXiv 2210.01936](https://arxiv.org/abs/2210.01936)) — and transcripts are blind
to prosody: the text of shouting reads like the text of talking. Each failure mode is
handled by a dedicated index (CLAP audio events for prosody) or by the verification
stage (negation, binding), never by hoping the embedding gets it right.

## Ingest (once per video, content-hash cached)

Four independent views, each emitting one canonical record type —
`Doc {video_id, t_start, t_end, modality, text, extra}`, timestamps in float seconds
computed by us. All local/free except captioning.

| Stage | Output | Why |
|---|---|---|
| Transcriber — mlx-whisper large-v3-turbo (local, ~10x realtime on M-series) | word-timestamped utterances, hallucination-filtered via the Whisper paper's own thresholds (compression-ratio > 2.4, avg logprob < −1.0, no-speech > 0.6), VAD gating, and a blocklist of Whisper's known stock hallucinations | speech dominates bodycam evidence; ~1% of Whisper transcriptions contain fabricated phrases and 38% of those are harmful ("Careless Whisper", FAccT 2024) — hallucinated text that matches a query is a precision disaster and, in this domain, a legal hazard |
| Captioner — Gemini flash-lite tier via OpenRouter, one call per 5-min 480p chunk, low media resolution (the only paid ingest stage) | structured events (action, people+clothing, vehicles, plates, lighting, non-speech audio) with chunk-local times we offset to absolute; transcript rides along in-prompt as temporal anchor | the only index whose vocabulary we control — prompted for the policing ontology so "handcuffing" is findable though never spoken |
| FrameEmbedder — SigLIP 2 so400m @ 0.5 fps (local, MPS) | image vectors | catches what the captioner didn't mention; frame-level embeddings remain the strongest practical baseline for continuous single-shot footage ([CLIP4Clip, arXiv 2104.08860](https://arxiv.org/abs/2104.08860); [arXiv 2406.01604](https://arxiv.org/abs/2406.01604)) — bodycam has no shot structure for video-native encoders to exploit |
| AudioTagger — CLAP zero-shot (local) + RMS loudness spikes | audio event spans (shouting, siren, gunshot, glass breaking...) | "raised voice" is unanswerable from a transcript — ASR strips prosody ([CLAP, arXiv 2211.06687](https://arxiv.org/abs/2211.06687)); categorical emotion models are unreliable on real-world audio (~0.34 macro-F1, Odyssey 2024), so we stick to overt events + loudness, with wav2vec2 arousal as an optional upgrade for graded escalation |

Storage: SQLite for Docs + numpy brute-force vectors (~100k vectors at this corpus size;
ANN indexes buy nothing — one matmul per query is milliseconds).

Each modality keeps its natural time granularity (word spans, frame instants, event
spans) on one shared absolute timeline; alignment happens at query time by temporal
merge, not by forcing a fixed segment grid at ingest.

## Query

```
query → Planner → Retrievers (BM25 + dense text + frames) → RRF fusion
      → temporal merge → VLM verify → results + evidence  (or abstain)
```

- **Planner** (cheapest structured-output LLM): decomposes by modality — speech queries
  phrased as words people would say, visual queries as what a frame shows. Two rules:
  *negations never reach an embedding retriever* (they score like their positives —
  NegBench), and *only explicit negations count* — inferred negations reject everything
  in a domain where an officer is always in frame. The raw query always rides along as a
  safety-net retrieval stream, so planning can never do worse than not planning.
- **Retrievers**: BM25 (bm25s) + dense text (bge) over transcript+caption docs, SigLIP
  text-to-frame similarity. Recall-oriented; nearly free.
- **Fusion by rank (RRF), never score** — BM25's unbounded scores and cosine similarities
  are incomparable; ranks fuse with zero calibration
  ([Cormack et al., SIGIR 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)).
- **Temporal merge**: overlapping/nearby hits across modalities combine into candidate
  segments with a minimum width (sliver answers are unreviewable).
- **License plates / on-screen text**: VLMs are measurably weak on non-semantic strings
  (OCRBench), so plate reads are aggregated across frames — per-character majority
  voting over repeated sightings, the standard ALPR trick (29%→69% single- vs
  multi-frame in the literature) — rather than trusting any single read.
- **Verifier** (cheap VLM): sees ~6 real frames + ±20s of transcript per candidate;
  returns match / confidence / reason. This one stage answers every embedding failure
  mode at once — negation, attribute binding, look-alikes (hands behind back ≠
  handcuffed), radio audio vs on-scene shouting. Below-threshold candidates are shown as
  "closest (rejected)" with the reason: in an evidence context, a confident empty answer
  beats a confident wrong one.

## Hotswappability

Every seam is a `typing.Protocol` + a registry entry; a YAML config is the wiring
diagram, so swapping a component is a one-line diff. Contract tests are parametrized
over the registry, so a swap cannot silently break the interface. Content-hash stage
caching keys each stage's output by (input file, config subtree): swapping the captioner
re-runs captioning, not transcription.

## What "good" looks like

Long-form grounding benchmarks calibrate expectations: even fully-supervised SOTA
reaches ~5% strict R@1 on movie-scale corpora (MAD) and 23–33% on egocentric footage
(Ego4D NLQ) — while recall-at-k over candidate windows is respectable everywhere. So the
product surface is a **ranked, evidence-bearing shortlist for a human reviewer**, scored
on Hit@k and precision-on-hard-queries, not a single oracle answer. See
[research.md](research.md) for the full literature review.

## Evaluation without labeled data

Bootstrap labels from our own ingest artifacts — propose cheap, verify by hand, same
pattern as the search system:

1. Write queries against the corpus (easy / hard / deliberate no-answer strata, seeded
   with real distractors).
2. Discover truth-span candidates by exhaustive regex scan over EVERY transcript and
   caption doc — corpus-wide, so no true instance goes unlabeled and labels aren't
   biased toward what the system can find. Merge adjacent matches, pad.
3. Human-audit via a generated sheet: jump to timestamp, watch ~20s, tick. Verifying a
   candidate takes seconds; only discovery-by-watching would have been expensive.
4. Metrics: P@1, Hit@5 (hit = tIoU ≥ 0.3 or midpoint-in-truth), abstention accuracy on
   no-answer queries, false-abstain count. Ablation configs (transcript-only, no-verify)
   quantify what each component buys.

## Cost

Captioning ≈ $0.15–0.35 per video-hour (one-time); planning + verification ≈ $0.01 per
query; everything else local. Indexing a 10–15 hour subset ≈ $2–5 total.
