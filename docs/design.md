# Design rationale

Why the system is shaped the way it is. The operational spec lives in
[pipeline.md](pipeline.md); the literature behind each claim in
[research.md](research.md).

## The problem decomposition

The hard part of hour-scale video search is *locating* the moment, not describing it
once found. The benchmark record is stark: methods that search long video for the 1–5
frames that answer a question reach ~2.1% temporal F1
([T*/LV-Haystack, arXiv 2504.02259](https://arxiv.org/abs/2504.02259)), while
question-conditioned selection matches 256-frame dense baselines while actually
inspecting ~8 frames ([VideoAgent, arXiv 2403.10517](https://arxiv.org/abs/2403.10517)).
Perception is close to commodity; localization is the open problem.

That decomposition drives everything here:

- **Ingest builds indexes, not understanding.** Every extractor's job is to make
  moments *findable* — nothing at ingest time tries to answer questions.
- **Precision is bought at the narrow end of a funnel.** Wide, cheap retrieval
  proposes; progressively more expensive stages (rank fusion, a cross-encoder,
  temporal merging) narrow the field; the most expensive judgment — a VLM looking at
  actual frames — happens only for a handful of finalists, and its job includes
  rejecting them.
- **The system owns the clock.** All timestamps derive from bookkeeping the code
  performs: ASR word times, frame indexes, chunk-offset arithmetic. Models describe
  short pieces of media put in front of them; none is asked where in an hour
  something happened.
- **Answers ship with their proof.** A result is a span plus the transcript lines,
  caption events, detections, and frames that produced it, labeled with a trust tier.
  A reviewer can check the system's work — which, for police footage, is the product.

## Why these nine indexes

Each extractor exists because some query class is unanswerable without it:

- **Word-timestamped transcripts** — the dominant evidence stream in this domain, and
  the incumbent industry (Axon, Truleo) is transcript-first. Hardened against
  hallucination with the Whisper paper's own decode-failure thresholds, VAD-style
  gating, and a stock-output blocklist, because a fabricated sentence that matches a
  query becomes false evidence
  ([Careless Whisper, arXiv 2402.08021](https://arxiv.org/abs/2402.08021)).
- **Speaker turns with roles** — "the *civilian* says…" requires knowing who spoke.
  Diarization plus a mic-proximity heuristic (the wearer's voice is loudest) labels
  the officer; other voices are labeled "other", not "civilian", because a scene can
  hold several officers and the heuristic can only identify the wearer.
- **Frame embeddings at 0.5 fps** — visual similarity for what nobody said or
  captioned. Frame-level rather than video-native encoders because on untrimmed
  continuous footage frame-level CLIP remains the winning baseline
  ([MAD, arXiv 2112.00431](https://arxiv.org/abs/2112.00431)) and bodycam has no shot
  structure to exploit.
- **Scene attributes** — day/night/indoors as *filters* (not searches), computed from
  the same frame vectors plus a luminance floor, because streetlights and headlights
  fool CLIP-family classifiers more than a histogram does.
- **VLM chunk captions** — the one index whose vocabulary the system chooses. The
  prompt carries a policing ontology, so "handcuffing" or "field sobriety test" are
  findable even when never spoken. Event times are chunk-local and converted to
  absolute by arithmetic.
- **Audio events (CLAP + a supervised PANNs head)** — a transcript renders shouting
  and calm speech as the same words, so prosody and non-speech sound need their own
  index. The supervised AudioSet head covers the fixed high-stakes vocabulary
  (gunshot, siren, screaming) where zero-shot prompting is least trustworthy.
- **Vocal arousal (dimensional)** — graded escalation. Categorical emotion was
  rejected on evidence (~0.34 macro-F1 on spontaneous audio, Odyssey 2024); a single
  arousal dimension from a model trained on naturalistic speech is the defensible
  signal.
- **Camera motion** — the wearer's movement is global frame motion, so foot pursuits
  and struggles fall out of a frame-difference series with no model at all
  (precedent on real police BWV: [arXiv 1904.09062](https://arxiv.org/abs/1904.09062)).
- **Overlay-clock OCR** — bodycams burn a wall clock into the frame; reading it (with
  a monotonicity filter against misreads) gives absolute time, so results can say
  "~22:53" and multi-camera corpora can align.

All of them emit one record shape onto one absolute timeline, at each modality's
natural granularity — a two-second quote stays two seconds; nothing is snapped to a
grid. We built the fixed-grid version first and discarded it (it is in git history):
bins forced every modality to one granularity and turned precise quotes into
30-second answers.

## Query design

- **Plan, but bound the downside.** An LLM decomposes the query into per-modality
  sub-queries with lexical variants that bridge written to spoken vocabulary
  ("breathalyzer result" → "point two four"). The unmodified query is always one of
  the retrieval streams, so a bad plan can add noise but cannot lose the query.
- **Negation never enters an embedding.** Bi-encoders rank negated queries at or
  below random ([NevIR, arXiv 2305.07614](https://arxiv.org/abs/2305.07614);
  [NegBench, arXiv 2501.09425](https://arxiv.org/abs/2501.09425)). The planner
  extracts explicit negations only — inferring unstated ones is a precision trap —
  and they are enforced by the verifier, which reads whole evidence in context.
- **Fuse by rank.** BM25 scores and cosine similarities are not comparable; ranks
  are. RRF with the standard k=60 ([Cormack et al., SIGIR 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)).
- **A cross-encoder between retrieval and verification.** +10–30% relative nDCG@10
  over first-stage retrieval on BEIR-style benchmarks for a few hundred
  milliseconds — the cheapest precision in the funnel, and it filters the candidate
  set before any VLM spend.
- **Merge on the timeline with AND semantics.** Hits paint weight onto per-second
  score tracks; smoothed tracks become spans; spans from *required* sub-queries must
  intersect. A required stream with zero hits is demoted rather than allowed to veto —
  absence of an index is not evidence of absence of the event.

## Trust design

The verifier is engineered around measured VLM failure modes:

- It **describes the frames before judging** and is never told what retrieval expects
  to find — VLMs capitulate to leading framing
  ([VISE, arXiv 2506.07180](https://arxiv.org/abs/2506.07180)).
- It judges the **user's original query**, not the planner's rephrasings — a spoken
  order satisfies "officer orders the driver out" even if no exit is visible.
- On night footage, a *visibility-limited* rejection is downgraded to "unclear",
  because low-light VLMs mostly miss what is present rather than invent what is not
  ([DarkQA, arXiv 2512.24985](https://arxiv.org/abs/2512.24985)) — but a rejection
  grounded in the transcript stands. Darkness is not a free pass.
- Verdicts are single-shot at temperature 0 (repeatable), mapped to discrete tiers.
  Verbalized confidence numbers are documented as miscalibrated
  ([arXiv 2504.14848](https://arxiv.org/abs/2504.14848)), so the system does not emit
  them; agreement-based confidence with conformal calibration
  ([arXiv 2405.01563](https://arxiv.org/abs/2405.01563)) is the designed upgrade once
  a large-enough labeled set exists, and is not yet implemented.
- Tiers are the interface: **confirmed / candidate (unverified) / no confident
  match** with the closest rejection and its reason. In evidence review, returning
  nothing with reasons beats returning something wrong.

## Swappability

Every extractor sits behind a `Protocol` and a registry; the YAML config chooses
implementations and options, and the stage cache is keyed by (source identity, config
subtree), so changing the detector's vocabulary re-runs detection and nothing else.
Retrievers toggle per config flag, and a modality allow-list makes restricted
configurations (e.g. a transcript-only baseline) pure config files — which is also
how the ablations are run. The reranker, planner, and verifier swap by model id and
tier flags; swapping their *architecture* is a code change, and we say so rather than
overclaim.

## Evaluating without labeled data

No public bodycam dataset with temporal annotations exists, so the labeled set is
bootstrapped: keyword patterns scan every transcript and caption record in the corpus
to propose candidate truth spans, which a human audits by watching ~20 seconds each.
Verifying a candidate takes seconds; only discovery-by-watching would have been
expensive. Two honesty notes carried into the results: at this corpus size the eval
set doubles as the dev set, and proposal-through-our-own-indexes cannot surface
truths every index missed — offset by hand-adding spans found by watching. Scoring is
Hit@1/Hit@5 (tIoU or midpoint), abstention accuracy on no-answer queries, and false
abstains, with per-run wall time and API cost logged.

## Cost model

Ingest: ~15–20 min of local compute per video-hour plus $0.10–0.35 of API captioning;
everything else runs on-device. Queries: cents with API verification, ~$0 with the
local tier. The economics are deliberate: the expensive one-time work (indexing) is
cache-resumable and parallel across videos, while per-query cost is independent of
corpus size because verification only ever touches the finalists.
