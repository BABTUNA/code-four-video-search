# End-to-end pipeline example

This shortened example uses real indexed evidence from `video_16`. Planner and
candidate outputs are abbreviated for readability.

## 1. Extract

Every modality uses the same timestamped fields. Model-specific details stay in
`extra`.

```json
[
  {"video_id": "video_16", "t_start": 180.3, "t_end": 182.4, "modality": "transcript",
   "text": "I need you to step out the car.", "extra": {"role": "officer"}},
  {"video_id": "video_16", "t_start": 180.0, "t_end": 180.0, "modality": "object",
   "text": "car, person", "extra": {"detections": ["car", "person"]}},
  {"video_id": "video_16", "t_start": 180.0, "t_end": 205.0, "modality": "vocal_arousal",
   "text": "raised voice, elevated vocal arousal", "extra": {"peak_arousal": 0.703}},
  {"video_id": "video_16", "t_start": 180.0, "t_end": 240.0, "modality": "caption",
   "text": "The driver is instructed to exit the vehicle and is handcuffed.",
   "extra": {"tags": ["handcuffing", "detention"]}},
  {"video_id": "video_16", "t_start": 191.0, "t_end": 194.0, "modality": "motion",
   "text": "high camera motion, running or struggle", "extra": {"mean_energy": 0.1068}}
]
```

These records cover the diagram's five groups: speech, captions, visual, audio, and
domain signals. The stored `modality` values are more specific. A query only uses
records relevant to what it asks.

## 2. Plan the query

Query: `officer orders the driver to step out of the vehicle`

```json
{
  "sub_queries": [
    {"text": "step out of the vehicle", "modalities": ["speech"],
     "role": "required", "polarity": "positive",
     "variants": ["get out of the car", "exit the vehicle"]},
    {"text": "police officer giving orders to a driver", "modalities": ["visual"],
     "role": "supporting", "polarity": "positive",
     "variants": ["officer talking to driver"]}
  ]
}
```

The original query also remains a supporting retrieval stream.

## 3. Retrieve and fuse

BM25 and dense search find the transcript and caption. SigLIP finds nearby frames,
while object and audio indexes add supporting evidence. Reciprocal rank fusion
combines ranks, the reranker keeps the strongest text hits, and their timestamps
merge into one candidate around the shared interval:

```json
{"video_id": "video_16", "t_start": 180.0, "t_end": 190.0,
 "evidence": ["transcript", "caption", "object", "vocal_arousal"]}
```

## 4. Verify and return

The VLM receives the original query, sampled frames, and nearby transcript. It can
confirm, reject, or keep the segment as uncertain.

```json
{"tier": "confirmed", "reason": "The officer tells the driver to exit the car.",
 "video_id": "video_16", "start_s": 180.0, "end_s": 190.0}
```
