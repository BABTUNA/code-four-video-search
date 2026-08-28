# Research review: what the literature says about searching hours of video

A survey of the temporal-search, video-RAG, moment-retrieval, audio, OCR, and
bodycam-domain literature, with judgments on what transfers to continuous
body-worn-camera footage and what is hype. Citations are to primary sources;
arXiv IDs verified. This review drives the decisions in [design.md](design.md).

## 1. The core problem is search, not perception

- **LongVideoBench** ([2407.15754](https://arxiv.org/abs/2407.15754)): even frontier
  models struggle at hour scale, and accuracy improves mainly with more frames
  processed — evidence that the frame budget, not reasoning, is the binding
  constraint on long video.
- **T\* / LV-Haystack** ([2504.02259](https://arxiv.org/abs/2504.02259)): frames the task
  as finding 1–5 needle frames among tens of thousands; existing temporal-search methods
  achieve **2.1% temporal F1** on the LongVideoBench subset. Under a fixed 32-frame
  budget, adding a search stage lifts GPT-4o and LLaVA-OneVision more than model
  upgrades do — better search beats more frames.
- Agentic systems confirm the same economics: **VideoAgent**
  ([2403.10517](https://arxiv.org/abs/2403.10517)) hits competitive long-video QA
  accuracy inspecting **~8 frames on average**; **TraveLER**
  ([2404.01476](https://arxiv.org/abs/2404.01476)) and **DrVideo**
  ([2406.12846](https://arxiv.org/abs/2406.12846)) report the advantage *widens* with
  video length.

Implication: treat localization as the hard problem, perception as commodity. Spend
compute on indexes and candidate selection, not on watching everything with a big model.

## 2. The architecture pattern the field converged on

Retrieval-augmented and agentic long-video systems from 2024–2026 independently converge
on the same shape — cheap text/embedding indexes first, vision second:

- **Video-RAG** ([2411.13093](https://arxiv.org/abs/2411.13093), NeurIPS 2025):
  training-free; extracts ASR + OCR + detection text, retrieves relevant snippets into
  an LVLM prompt; +8.1% avg on Video-MME — a 72B open model with it surpasses
  Gemini-1.5-Pro. ASR is lighting-invariant, which matters for night footage.
- **LLoVi** ([2312.17235](https://arxiv.org/abs/2312.17235)): caption short clips, let an
  LLM reason over the caption stream; +18 points absolute over prior SOTA on EgoSchema.
  The strongest published validation of captions-as-index for egocentric-style video.
- **Goldfish** ([2407.12679](https://arxiv.org/abs/2407.12679)): fixed-time clip windows
  (no shot detection), captions fused with subtitles, retrieve top-k then answer —
  structurally identical to what bodycam needs, since continuous footage has no shots.
- **Deep Video Discovery** ([2505.18079](https://arxiv.org/abs/2505.18079), NeurIPS
  2025): agentic tool-use over a multi-granular index; 74.2% on LVBench **rising to 76.0
  with transcripts** — transcripts measurably help even the strongest visual systems.
- **VideoExplorer** ([2506.10821](https://arxiv.org/abs/2506.10821)): a text-only
  reasoning LLM orchestrating subtitle-retriever + clip-retriever + visual-perceiver
  tools beats GPT-4o/Gemini pipelines on MLVU/LVBench — the subtitles-first,
  look-to-confirm division of labor.
- **TVR** ([2001.09099](https://arxiv.org/abs/2001.09099)) established early that
  dialogue/subtitle text carries a large share of the retrieval signal in realistic
  corpora — consistent with the incumbent bodycam industry (Axon, Truleo) being
  transcript-first.

## 3. What we deliberately skip, and why

- **The supervised moment-retrieval lineage** (Moment-DETR/QVHighlights
  [2107.09609](https://arxiv.org/abs/2107.09609), CG-DETR, UVCOM): every strong result
  is fine-tuned on curated 2–3 min web video with CLIP+SlowFast feature pipelines. The
  one zero-shot attempt, **UniVTG** ([2307.16715](https://arxiv.org/abs/2307.16715)),
  drops to ~11 avg mAP off-distribution (mIoU 7.9 on egocentric Ego4D NLQ) — predicting
  failure on bodycam with no training data. Zero-shot LLM-based moment retrieval
  (VTG-GPT [2403.02076](https://arxiv.org/abs/2403.02076), TFVTG
  [2408.16219](https://arxiv.org/abs/2408.16219), Moment-GPT
  [2501.07972](https://arxiv.org/abs/2501.07972)) is the active replacement — and is
  the caption+LLM pattern we implement, not a model we deploy.
- **Video-native embeddings as the retrieval backbone** (VideoPrism
  [2402.13217](https://arxiv.org/abs/2402.13217), InternVideo2
  [2403.15377](https://arxiv.org/abs/2403.15377)): win on trimmed-clip benchmarks, but
  no published head-to-head beats frame-level embeddings on *untrimmed* continuous
  video — and the MAD long-form benchmark found zero-shot frame-level CLIP beating a
  trained grounding model ([2112.00431](https://arxiv.org/abs/2112.00431)). Frame-level
  SigLIP with temporal pooling is the evidence-backed default; a per-chunk video encoder
  is an upgrade path for motion-defined queries, not a prerequisite.
- **Categorical emotion recognition**: on spontaneous real-world audio the Odyssey 2024
  SER Challenge best systems reach ~0.34 macro-F1 on 8-class emotion — not
  product-grade. Dimensional **arousal** from a wav2vec2 model
  ([2203.07378](https://arxiv.org/abs/2203.07378), trained on naturalistic MSP-Podcast)
  is the reliable proxy for vocal escalation, alongside CLAP for overt sound events.

## 4. Per-stage evidence

**ASR.** Whisper hallucination is documented and domain-critical: ~1% of transcriptions
contain fabricated phrases and **38% of those carry explicit harms** — fabricated
violence included — concentrated around pauses and non-speech
(["Careless Whisper", FAccT 2024, 2402.08021](https://arxiv.org/abs/2402.08021)). A
hallucinated violent phrase in a police transcript that matches a query is a precision
disaster and a legal hazard. Mitigations, all adopted: the canonical thresholds from the
Whisper paper itself ([2212.04356](https://arxiv.org/abs/2212.04356) §4.5 —
compression-ratio > 2.4, avg logprob < −1.0, no-speech > 0.6), VAD pre-segmentation as
in WhisperX ([2303.00747](https://arxiv.org/abs/2303.00747)), and a blocklist of
Whisper's recurring stock hallucinations
([2501.11378](https://arxiv.org/abs/2501.11378)).

**Audio events.** CLAP ([LAION, 2211.06687](https://arxiv.org/abs/2211.06687); original
Microsoft CLAP [2206.04769](https://arxiv.org/abs/2206.04769)) supports zero-shot
text-to-audio retrieval of concrete events (siren, gunshot, shouting, glass breaking) —
the channel transcripts cannot carry, since ASR strips prosody. Conflict detection on
actual police body-worn audio has direct precedent
([1711.05355](https://arxiv.org/abs/1711.05355), ICASSP 2018).

**OCR / license plates.** VLMs are measurably weak on non-semantic strings — exactly
what plates are (OCRBench, [2305.07895](https://arxiv.org/abs/2305.07895)). The ALPR
literature's answer is temporal redundancy: per-character **majority voting across the
frames of a tracked plate** lifts accuracy dramatically (e.g. 29% single-frame → 69%
multi-frame; Laroca et al. [1802.09567](https://arxiv.org/abs/1802.09567); Gonçalves et
al., IEEE ITSC 2016). We aggregate OCR reads across frames rather than trusting any
single read.

**Fusion.** Reciprocal rank fusion (Cormack et al., SIGIR 2009) remains the robust
default for combining BM25 and dense retrievers without score calibration; recent
multimodal video retrieval still builds on modality-aware RRF
([2503.20698](https://arxiv.org/abs/2503.20698)).

**Verification.** Embeddings provably fail on negation — chance-level on negated
queries (NegBench, [2501.09425](https://arxiv.org/abs/2501.09425)) — and attribute
binding — near bag-of-words on relations (ARO,
[2210.01936](https://arxiv.org/abs/2210.01936)). Both are resolved only by a stage that
actually looks at candidate evidence, which is also where hierarchical searchers put
their gains (TimeSearch's reflection stage, 41.8%→51.5% on LVBench,
[2504.01407](https://arxiv.org/abs/2504.01407)).

## 5. Domain literature (bodycam specifically)

- The Stanford lineage established bodycam NLP: computational respect measures over
  Oakland PD transcripts (Voigt et al., PNAS 2017), prosodic disparities ("The Thin
  Blue Waveform", JPSP 2021), and escalation detectable in an officer's first 45 words
  (Rho et al., PNAS 2023). Transcript and prosody both carry real signal in this domain.
- Commercial systems index less than one might assume: Axon publicly ships transcript
  search; Truleo adds audio-only event classifiers (use-of-force, pursuits,
  professionalism); none publicly claim natural-language search over fused
  audio+visual evidence. That gap is this project.
- **No public bodycam dataset with temporal annotations exists** (multiple 2024–2026
  papers state their BWC data cannot be released) — which is why we bootstrap our own
  labeled eval set from ingest artifacts plus human audit (see design.md).

## 6. Calibrating expectations — and what "good" means here

The long-form benchmarks are sobering: on MAD (1.2K hours of movies), the best trained
systems reach **R1@0.5 ≈ 5.5%** (SnAG, [2404.02257](https://arxiv.org/abs/2404.02257));
Ego4D NLQ winners sit at 23–33% R@1 after in-domain pretraining. Strict
top-1 localization on hour-scale video is unsolved even with supervision. Recall-at-k
over candidate windows, however, is respectable everywhere.

Design consequences: (a) the product surface is a **ranked, evidence-bearing shortlist
for a human reviewer**, not a single oracle answer; (b) evaluation emphasizes Hit@5 and
precision-on-hard-queries with tIoU-based matching, plus abstention accuracy — because
in an evidence context a confident empty answer beats a confident wrong one.
