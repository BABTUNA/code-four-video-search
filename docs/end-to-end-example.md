# End-to-end pipeline example

This walkthrough follows one real indexed moment from `video_16`. Long arrays and
model outputs are shortened, but the fields and stage boundaries match the code.

Query: `officer orders the driver to step out of the vehicle`

## 1. Prepare and extract the video

Ingestion decodes the source once into a 480p proxy, mono audio, sampled frames, and
a loudness series. Configured extractors then emit the shared record type:

```python
Doc(video_id, t_start, t_end, modality, text, extra)
```

The five boxes in the architecture diagram are groups. Each group can emit several
specific `modality` values:

| Group | Example stored modalities |
|---|---|
| Speech | `transcript`, `speaker_turn` |
| Captions | `caption` |
| Visual | `frame`, `object`, `scene` |
| Audio | `audio_window`, `audio_tag`, `vocal_arousal` |
| Domain signals | `motion`, `wall_clock` |

Records near the answer look like this:

```json
[
  {
    "video_id": "video_16", "t_start": 180.3, "t_end": 182.4,
    "modality": "transcript", "text": "I need you to step out the car.",
    "extra": {"speaker": "SPEAKER_01", "role": "officer"}
  },
  {
    "video_id": "video_16", "t_start": 180.0, "t_end": 180.0,
    "modality": "object", "text": "car, person",
    "extra": {"detections": ["car", "person"]}
  },
  {
    "video_id": "video_16", "t_start": 180.0, "t_end": 205.0,
    "modality": "vocal_arousal", "text": "raised voice, elevated vocal arousal",
    "extra": {"peak_arousal": 0.703}
  },
  {
    "video_id": "video_16", "t_start": 180.0, "t_end": 240.0,
    "modality": "caption",
    "text": "The driver is instructed to exit the vehicle and is handcuffed.",
    "extra": {"tags": ["handcuffing", "detention"]}
  },
  {
    "video_id": "video_16", "t_start": 191.0, "t_end": 194.0,
    "modality": "motion", "text": "high camera motion, running or struggle",
    "extra": {"mean_energy": 0.1068}
  }
]
```

SQLite stores the records. Frame and audio vectors are stored separately and linked
by document ID. Text-bearing records also receive dense-text vectors. Every timestamp
is absolute video time, so the modalities do not need matching chunk sizes.

## 2. Plan the query

One structured LLM call produces modality-scoped retrieval streams. This is the
abbreviated cached plan for the example:

```json
{
  "sub_queries": [
    {
      "text": "step out of the vehicle",
      "modalities": ["speech"], "role": "required", "polarity": "positive",
      "variants": ["get out of the car", "exit the vehicle", "step out"]
    },
    {
      "text": "police officer giving orders to a driver",
      "modalities": ["visual"], "role": "supporting", "polarity": "positive",
      "variants": ["officer talking to driver", "commanding driver"]
    },
    {
      "text": "officer orders the driver to step out of the vehicle",
      "modalities": ["speech", "visual", "audio", "caption"],
      "role": "supporting", "polarity": "positive", "variants": []
    }
  ],
  "scene_filter": "", "anchor_text": "", "anchor_relation": ""
}
```

The original query always remains a supporting stream, limiting the damage from a
bad decomposition. Explicit negative clauses become verifier checks instead of
embedding searches. This query contains no negation, scene filter, or time anchor.

The planner has four search labels rather than five extraction groups. Domain signals
are routed through the relevant path: `audio` includes motion, `visual` includes wall
clock OCR, and scene records act as filters instead of retrieval targets.

## 3. Retrieve each stream

Each positive stream independently runs the enabled retrieval arms:

| Retrieval arm | What it searches |
|---|---|
| BM25 | Exact words plus planner variants |
| Dense text | Semantic matches over every text-bearing record |
| SigLIP | Query text against sampled frame vectors |
| CLAP | Query text against audio-window vectors |

Results are filtered to the stream's allowed modalities. For example, the required
speech stream can retain transcripts and speaker turns but not a visually similar
frame.

Reciprocal rank fusion combines the lists using `1 / (60 + rank)`. It uses rank
because BM25, text cosine, SigLIP, and CLAP scores are not directly comparable. A
cross-encoder then reranks the strongest text records; vector-only frame and audio
hits retain their fused ranks.

## 4. Fuse evidence on the timeline

Every retained hit paints its rank weight over its timestamp. The system smooths
each sub-query track and turns its peaks into spans:

```text
required speech     180.3────182.4   "step out the car"
supporting object   180.0            car + person
supporting caption  180.0────────────────────────240.0
domain motion                    191.0──194.0
```

Required streams intersect on the timeline. Supporting streams can strengthen a
candidate but cannot veto it. Nearby spans merge across small gaps, producing a
simplified candidate such as:

```json
{
  "video_id": "video_16", "t_start": 180.0, "t_end": 190.0,
  "evidence_doc_ids": [14352, 15581, 16096]
}
```

The arousal and motion records exist, but this query does not require them. Extracting
a modality does not force every query to use it.

## 5. Verify and present

The verifier receives the original query, up to eight frames focused around strong
evidence, and transcript context from 20 seconds before and after the candidate. It
describes the evidence before judging each required element.

```json
{
  "description": "An officer is beside a stopped car and speaks to its occupant.",
  "elements": [
    {"name": "officer orders the driver to step out of the vehicle", "present": "yes"}
  ],
  "match": "yes",
  "reason": "The officer transcript contains a direct order to exit the car.",
  "tier": "confirmed"
}
```

`yes`, `unclear`, and `no` map to `confirmed`, `candidate`, and `rejected`. The UI and
CLI return the video, playable timestamps, verdict reason, and supporting records. If
all candidates are rejected, the result is `no confident match`.

## 6. Where components can be replaced

Two boundaries make the pipeline hot-swappable:

1. YAML enables or removes modalities and retrieval arms without changing the other
   stages.
2. Local and API implementations can replace an extractor or verifier as long as
   they preserve the `Doc` or verdict contract.

Stage caching reruns only the replaced extractor. Fusion, verification, and the UI
continue consuming the same normalized records.
