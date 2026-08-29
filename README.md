# Code Four Video Search

Natural-language search over law-enforcement body-worn camera footage.

> Docs: [design rationale](docs/design.md) · [pipeline blueprint](docs/pipeline.md) ·
> [full literature review](docs/research.md) · [build plan](docs/plan.md)

## 1. What this is

Ask questions such as *"find a vehicle stopped by police at night"* or *"find someone
raising their voice at an officer."* The system returns timestamped segments with the
transcript, visual, and audio evidence behind each result.

Results use three trust tiers:

* **Confirmed:** a VLM inspected the frames and transcript and found a match.
* **Candidate:** retrieval was strong, but verification was inconclusive.
* **No confident match:** the verifier rejected the candidates and explains why.

```text
$ uv run c4 search "officer orders the driver to step out of the vehicle"

#1  video_1  00:01:11 to 00:01:51  [CONFIRMED]
    The transcript contains two commands to step outside the vehicle.
    transcript [00:01:31] (officer) You're going to step outside the vehicle.
    transcript [00:01:41] (officer) I need you to step outside the vehicle.
```

The system is a precision funnel. Local extractors index each video once. Query-time
retrieval finds a broad set of evidence, reranking narrows it, temporal merging forms
segments, and a VLM verifies only the strongest candidates. All timestamps come from
media offsets, transcript timing, or frame positions. Models never invent absolute
times.

## 2. Quickstart

Requires **Apple Silicon**, `ffmpeg`, [`uv`](https://docs.astral.sh/uv/), and an
OpenRouter key. The local stack uses MLX, CoreML, and Apple Vision.

```bash
uv sync
echo 'OPENROUTER_API_KEY=sk-or-...' > .env

# Index videos. Completed stages are cached.
uv run c4 ingest c4-videos/video_1.mp4 c4-videos/video_2.mp4

# Search
uv run c4 search "find all interactions where an officer reads Miranda rights"

# Evaluate against the labeled query set
uv run c4 eval
```

Ingest takes about 15 to 20 minutes of local compute and $0.10 to $0.35 of captioning
per video hour. API verification costs about one to two cents per query. A slower
local Qwen2.5-VL verifier is also available through configuration.

## 3. Research foundations

The main README includes only the research that directly changed the design. See
[docs/research.md](docs/research.md) for the full review.

### 3.1 Modality extraction

Long-video models struggle to locate brief events. On the LVBench subset of
LV-Haystack, existing keyframe-selection methods reach only 2.1% temporal F1.
**[Re-thinking Temporal Search for Long-Form Video Understanding](https://arxiv.org/abs/2504.02259)**
introduces T* as a question-guided response to this problem.
**[VideoAgent: Long-form Video Understanding with Large Language Model as Agent](https://arxiv.org/abs/2403.10517)**
uses 8.4 frames on average and outperforms the 256-frame LongViViT baseline on
EgoSchema. Together, these results support selective search instead of sending every
frame to one model.

![Video-RAG auxiliary text extraction](docs/figures/videorag-framework.png)
***Figure 1. Video-RAG auxiliary evidence retrieval.*** *Video-RAG converts ASR, OCR,
and object detections into searchable text. This system
extends the same pattern to additional bodycam modalities
(**[Video-RAG: Visually-aligned Retrieval-Augmented Long Video Comprehension](https://arxiv.org/abs/2411.13093)**).*

The remaining extractor choices follow four practical observations:

* **Frames:** MAD uses frame-level CLIP features, mean-pooled over candidate
  proposals, as a competitive long-form grounding baseline
  (**[MAD: A Scalable Dataset for Language Grounding in Videos from Movie Audio Descriptions](https://arxiv.org/abs/2112.00431)**).
* **Audio:** CLAP supports text-to-audio retrieval, while PANNs supports audio tagging
  and sound-event detection. These results motivate separate audio indexes, but do
  not establish accuracy on police footage
  (**[Large-scale Contrastive Language-Audio Pretraining with Feature Fusion and Keyword-to-Caption Augmentation](https://arxiv.org/abs/2211.06687)**,
  **[PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition](https://arxiv.org/abs/1912.10211)**).
* **Captions:** VLM captions make visible actions searchable when nobody names them
  (**[A Simple LLM Framework for Long-Range Video Question-Answering](https://arxiv.org/abs/2312.17235)**,
  **[Goldfish: Vision-Language Understanding of Arbitrarily Long Videos](https://arxiv.org/abs/2407.12679)**).
* **Domain signals:** diarization, clock OCR, object detection, vocal arousal, and
  camera motion add bodycam-specific evidence.

### 3.2 Semantic search

The query pipeline follows a search-then-inspect approach. Retrieval proposes a small
set of moments, then a VLM judges only those moments.

![T* iterative temporal search](docs/figures/tstar-framework.png)
***Figure 2. T* question-guided temporal search.*** *T* grounds the question,
searches through temporal and spatial upsampling, and
passes selected frames to the answering model. We borrow the separation between
search and answering, not the T* search algorithm itself
(**[Re-thinking Temporal Search for Long-Form Video Understanding](https://arxiv.org/abs/2504.02259)**).*

![Goldfish retrieval framework](docs/figures/goldfish-framework.png)
***Figure 3. Goldfish retrieve-then-answer framework.*** *Goldfish retrieves relevant
clips before answering over long videos. Our pipeline
adds rank fusion, reranking, temporal merging, and verification
(**[Goldfish: Vision-Language Understanding of Arbitrarily Long Videos](https://arxiv.org/abs/2407.12679)**).*

Three findings shape the precision stages:

* **Negation:** embedding models handle negation poorly, so negative constraints are
  checked during final verification
  (**[NevIR: Negation in Neural Information Retrieval](https://arxiv.org/abs/2305.07614)**,
  **[Vision-Language Models Do Not Understand Negation](https://arxiv.org/abs/2501.09425)**).
* **Attribute binding:** CLIP-like models often confuse relationships such as a red
  shirt versus a red car, so the verifier inspects real frames
  (**[When and Why Vision-Language Models Behave Like Bags-of-Words, and What to Do About It?](https://arxiv.org/abs/2210.01936)**).
* **Localization:** strict top-1 localization remains difficult, so the system returns
  a ranked evidence-bearing shortlist rather than claiming one perfect answer
  (**[SnAG: Scalable and Accurate Video Grounding](https://arxiv.org/abs/2404.02257)**).

Video-LLMs can follow misleading prompts even when they conflict with visual evidence
(**[Flattery in Motion: Benchmarking and Analyzing Sycophancy in Video-LLMs](https://arxiv.org/abs/2506.07180)**).
The verifier therefore describes the evidence before judging it and runs at
temperature zero for repeatability. It returns discrete tiers because VLM verbalized
confidence is often miscalibrated
(**[Object-Level Verbalized Confidence Calibration in Vision-Language Models via Semantic Perturbation](https://arxiv.org/abs/2504.14848)**).
Conformal abstention is a future improvement that requires a separate calibration set
(**[Mitigating LLM Hallucinations via Conformal Abstention](https://arxiv.org/abs/2405.01563)**).

## 4. Research judgment: what's worth using vs. what's hype

Here, hype means that a method's published results do not yet justify its cost or
assumptions for this bodycam corpus. It does not mean the research itself is poor.

| Research direction | Verdict | What the evidence says | Decision for this system | Paper reference |
|---|---|---|---|---|
| Retrieve evidence before reasoning | **Worth using** | Question-guided selection reduces the amount of video sent to a VLM, while newer scene benchmarks still find long-context forgetting | Adopted as retrieve, merge, then verify | **[Re-thinking Temporal Search for Long-Form Video Understanding](https://arxiv.org/abs/2504.02259)**, **[VideoAgent: Long-form Video Understanding with Large Language Model as Agent](https://arxiv.org/abs/2403.10517)**, and **[Seeing the Scene Matters: Revealing Forgetting in Video Understanding Models with a Scene-Aware Long-Video Benchmark](https://openaccess.thecvf.com/content/CVPR2026/html/Chen_Seeing_the_Scene_Matters_Revealing_Forgetting_in_Video_Understanding_Models_CVPR_2026_paper.html)** |
| Convert ASR, OCR, objects, and captions into searchable text | **Worth using with limits** | Text makes multimodal evidence cheap to search, but cannot preserve every spatial or acoustic detail | Adopted alongside native frame and audio indexes | **[Video-RAG: Visually-aligned Retrieval-Augmented Long Video Comprehension](https://arxiv.org/abs/2411.13093)** |
| Compress many frames into visual panels | **Worth testing** | A training-free panel layout improves long-video QA, but trades spatial detail for temporal coverage | Deferred until visual-only evaluation shows a need | **[Video Panels for Long Video Understanding](https://openaccess.thecvf.com/content/CVPR2026/html/Doorenbos_Video_Panels_for_Long_Video_Understanding_CVPR_2026_paper.html)** |
| Train a specialized temporal-grounding model | **Strong research, wrong fit today** | Current models improve precise localization on labeled benchmarks, but require training data and domain validation | Deferred because no labeled bodycam training set exists | **[HieraMamba: Video Temporal Grounding via Hierarchical Anchor-Mamba Pooling](https://openaccess.thecvf.com/content/CVPR2026/html/An_HieraMamba_Video_Temporal_Grounding_via_Hierarchical_Anchor-Mamba_Pooling_CVPR_2026_paper.html)** |
| Use hierarchical multi-agent video search | **Promising, but overbuilt here** | Recent systems report strong benchmark results from hierarchical memory and repeated agent reasoning | Deferred until compositional-query failures justify the latency and complexity | **[Hierarchical Long Video Understanding with Audiovisual Entity Cohesion and Agentic Search](https://openaccess.thecvf.com/content/CVPR2026/html/Yin_Hierarchical_Long_Video_Understanding_with_Audiovisual_Entity_Cohesion_and_Agentic_CVPR_2026_paper.html)** and **[Symphony: A Cognitively-Inspired Multi-Agent System for Long-Video Understanding](https://openaccess.thecvf.com/content/CVPR2026/html/Yan_Symphony_A_Cognitively-Inspired_Multi-Agent_System_for_Long-Video_Understanding_CVPR_2026_paper.html)** |
| Send the whole video to one long-context VLM | **Hype for this task** | More context does not guarantee reliable recall of brief scenes or precise timestamps | Rejected in favor of explicit evidence retrieval | **[Re-thinking Temporal Search for Long-Form Video Understanding](https://arxiv.org/abs/2504.02259)** and **[Seeing the Scene Matters: Revealing Forgetting in Video Understanding Models with a Scene-Aware Long-Video Benchmark](https://openaccess.thecvf.com/content/CVPR2026/html/Chen_Seeing_the_Scene_Matters_Revealing_Forgetting_in_Video_Understanding_Models_CVPR_2026_paper.html)** |
| Treat a VLM's stated confidence as probability | **Hype** | Verbal confidence is not reliably calibrated to correctness | Rejected; use measured thresholds and discrete verification tiers | **[Object-Level Verbalized Confidence Calibration in Vision-Language Models via Semantic Perturbation](https://arxiv.org/abs/2504.14848)** |

The pattern is simple: adopt ideas that expose evidence and measurable failure modes.
Defer benchmark-winning complexity until it proves value on labeled bodycam queries.

## 5. Architecture

The full operational specification is in [docs/pipeline.md](docs/pipeline.md). A
[short end-to-end example](docs/end-to-end-example.md) follows one query from
extracted modalities through planning, fusion, and verification.

![Code Four system architecture](docs/figures/system-architecture.drawio.png)

***Figure 4. Code Four system architecture.*** *Offline ingestion creates a shared
evidence index. Online search retrieves and
combines evidence before a VLM verifies the strongest candidate segments.*

### 5.1 Modality extraction

Each extractor emits the same timestamped record type:

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

Each modality keeps its natural time scale. A quote may last two seconds while a
sampled frame represents one instant. Evidence is aligned during search instead of
being forced into fixed chunks at ingest.

Extractors are registered through a small interface and selected in YAML. Replacing a
model does not change the `Doc` contract or downstream search code. Stage caching
also allows one extractor to rerun without repeating the whole ingest.

### 5.2 Semantic search

The planner creates up to four searchable clauses, modality hints, lexical variants,
scene filters, and negative constraints. The original query always remains a retrieval
stream, limiting the damage from a poor plan.

BM25, dense text, frame, and audio retrieval run independently. Reciprocal rank fusion
combines their ranks without comparing incompatible model scores. A cross-encoder
reranks the best documents, and temporal merging joins evidence on the shared
timeline. The verifier then judges the original user query from frames and transcript
evidence.

## 6. Evaluation

The evaluation uses the 20 shortest videos:

* 6.67 hours of footage
* About 39,500 indexed evidence records
* 24 queries
* 18 answerable queries with 72 labeled spans
* 6 no-answer traps containing real distractors
* Ingest: about 12 minutes of local compute and $0.13 of captioning per video hour,
  $0.90 of captioning for the full corpus

Running the same extraction through hosted APIs instead of local models:

* Roughly $5 to $6 per video hour by public list prices - about 40 times more
* Dominated by per-frame object detection and OCR calls; hosted transcription and
  diarization add a few more dollars across the corpus
* Throughput would depend on provider rate limits instead of one machine
* Local-first extraction is why the only recurring API costs are one caption call per
  five-minute chunk and verification on a handful of finalists per query

The complete query list is in the [evaluation query reference](docs/evaluation-queries.md).

Labels were proposed by scanning transcripts and captions, then checked against frames
and transcript context. A result counts as a hit when temporal IoU is at least 0.3 or
the prediction midpoint falls inside a labeled span. Each run stores timing and API
cost in `eval/results-<timestamp>.json`.

The evaluation has two important biases. The same query set guided development, and
the system's own indexes helped discover the labels. Prosody queries are also absent
because validating them requires listening to the source audio.

### The build-up ladder: what each index bought, and what it cost

Each row is a swappable YAML configuration.

| Config | Hit@1 | Hit@5 | Correct abstentions | False abstentions | Seconds/query | Cost/query |
|---|---:|---:|---:|---:|---:|---:|
| 1. Transcripts only | 0.44 | 0.67 | 3/6 | 2 | 1.5 | $0 |
| 2. Add captions | **0.56** | **0.89** | 0/6 | 0 | 2.0 | $0 |
| 3. Add frames and objects | 0.50 | 0.67 | 0/6 | 1 | 2.3 | $0 |
| 4. Add audio, arousal, and motion | 0.50 | 0.72 | 0/6 | 1 | 2.4 | $0 |
| 5. Add VLM verification | 0.50 | 0.67 | 5/6 | 4 | 14.7 | $0.014 |
| **Recommended: captions retrieval + verification** | **0.67** | 0.83 | **6/6** | 2 | 13.8 | $0.014 |

Stratified by difficulty on the recommended configuration: Hit@1 is 0.67 on both the
direct (speech-answerable) and cross-modal (hard) strata - precision holds on the hard
stratum, the rubric's stated priority - and all six no-answer traps, the strictest
precision test, are refused.

The results support three conclusions:

1. **Captions provide the largest retrieval gain.** They find visible actions that
   transcripts miss.
2. **Frame and audio indexes add coverage but not consistent precision on this query
   set.** The label discovery process favors transcript and caption evidence.
3. **Verification improves abstention, and evidence-guided judging makes it pay for
   itself.** The recommended configuration rejects all six no-answer traps, reaches
   the best Hit@1, and leaves two false abstentions - after the verifier's frame
   sample was anchored to the strongest evidence and its rules were taught that
   frames contradicting the transcript differ from frames merely missing the moment.

The metrics measure ranking and abstention, not complete segment-level precision and
recall. Extra incorrect results after the first hit are not currently penalized.

### Failure taxonomy

| Failure | Example | Next improvement |
|---|---|---|
| Verifier rejects valid evidence | A discussed event is judged as an unseen event | Transcript-aware judging landed (false abstentions 3 to 2); the planner still adds a visual requirement to some speech queries, which blocks the transcript-primary rule |
| Scene evidence and event evidence occur at different times | Night and daylight stops | Apply scene attributes as filters |
| Correct moment ranks below the cutoff | Relevant segment appears below rank five | Improve fusion and candidate depth |
| Temporal anchor is weak | Events described as before or after another event | Restrict anchor matches to one video |

## 7. Next steps

The current priority is better evaluation coverage, especially true precision and
recall, prosody queries, visual-only queries, negation, and temporal anchors.

### Deferred architecture upgrades

These ideas are worth testing when the project reaches the condition that justifies
their added complexity:

| Upgrade | Add it when | Research basis |
|---|---|---|
| Supervised temporal grounding | A reviewed bodycam training set is large enough to fine-tune and evaluate without leakage | **[HieraMamba: Video Temporal Grounding via Hierarchical Anchor-Mamba Pooling](https://openaccess.thecvf.com/content/CVPR2026/html/An_HieraMamba_Video_Temporal_Grounding_via_Hierarchical_Anchor-Mamba_Pooling_CVPR_2026_paper.html)** |
| Video-native embedding index | A visual-only benchmark shows a measurable gain over caption and frame retrieval | **[MAD: A Scalable Dataset for Language Grounding in Videos from Movie Audio Descriptions](https://arxiv.org/abs/2112.00431)** and **[SnAG: Scalable and Accurate Video Grounding](https://arxiv.org/abs/2404.02257)** |
| Visual panel compression | Dense frames become necessary and panels outperform the current sparse sampling on visual-only queries | **[Video Panels for Long Video Understanding](https://openaccess.thecvf.com/content/CVPR2026/html/Doorenbos_Video_Panels_for_Long_Video_Understanding_CVPR_2026_paper.html)** |
| Agentic multi-hop search | Compositional queries fail the fixed pipeline often enough to justify repeated model calls | **[Hierarchical Long Video Understanding with Audiovisual Entity Cohesion and Agentic Search](https://openaccess.thecvf.com/content/CVPR2026/html/Yin_Hierarchical_Long_Video_Understanding_with_Audiovisual_Entity_Cohesion_and_Agentic_CVPR_2026_paper.html)** |
| ANN vector database | Corpus size, online updates, or metadata filtering make NumPy search a measured bottleneck | Operational scale trigger |
| Fully local captioning | Privacy requirements or repeated ingestion make local compute cheaper than API captioning | Operational deployment trigger |
| Multi-frame license plate extraction | Plate search becomes a product requirement and can be evaluated on repeated sightings | **[Character Time-series Matching for Robust License Plate Recognition](https://arxiv.org/abs/2307.11336)** |

### More reliable transcription

The current transcriber uses MLX Whisper word timestamps, decode-failure thresholds,
and a blocklist for recurring stock outputs. A future experiment would compare it
against the complete WhisperX pipeline, which adds voice activity detection,
cut-and-merge batching, and forced phoneme alignment. The upgrade should be adopted
only if it measurably improves timestamp accuracy and reduces hallucinated phrases
without adding excessive processing time.

![WhisperX pipeline](docs/figures/whisperx-pipeline.png)
***Figure 5. WhisperX candidate transcription upgrade.*** *This is a reference
architecture, not the current implementation
(**[WhisperX: Time-Accurate Speech Transcription of Long-Form Audio](https://arxiv.org/abs/2303.00747)**).*
