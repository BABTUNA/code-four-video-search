# Loom walkthrough script (~12-15 min)

Have ready: the repo README open, a terminal at the repo root, and
eval/queries.yaml visible in an editor tab.

## 1. The one idea (2 min)

- "Searching hours of bodycam video fails at *finding* moments, not recognizing
  them - models describe a 30-second clip fine, but existing temporal search hits
  ~2% F1 on hour-scale video."
- "So the system is a precision funnel: nine cheap local indexes propose, rank
  fusion and a cross-encoder narrow, temporal merging forms candidate segments,
  and a VLM inspects only the finalists - where it's allowed to say no."
- "Timestamps always come from our own bookkeeping - ASR word times, frame
  indexes, chunk offsets. No model is ever asked to remember when something
  happened."

## 2. Live queries (5 min) - run these, talk over the output

```
uv run c4 search "officer orders the driver to step out of the vehicle"
```
- Point at: three trust tiers, the transcript evidence with speaker roles, the
  wall-clock label from the burned-in overlay OCR.

```
uv run c4 search "a vehicle stopped by police at night"
```
- Point at: the planner turning "at night" into a scene *filter* rather than a
  search term - and why (attribute words flood retrieval; we measured it).

```
uv run c4 search "an officer reads someone their Miranda rights"
```
- The abstention story: "attorney" and "court date" are spoken in this corpus,
  but no rights reading exists - retrieval proposes, the verifier refuses, and
  the output shows the closest rejected candidate with the stated reason.
  "In an evidence context, a confident empty answer beats a confident wrong one."

## 3. The evaluation (4 min) - README section 6 on screen

- How labels were made without a labeled dataset: scan our own indexes for
  candidates, audit by frames + transcript, document every rejected candidate
  inline (show queries.yaml comments - cuffs being REMOVED, the stay-in-the-car
  exchange).
- The build-up ladder table: "each row is one config file" - captions double
  hit@1 for $0.25 of one-time cost; frame/audio retrieval added noise *on this
  query set* (say the bias caveat out loud); verification buys 3/3 abstention
  for ~14s and a cent per query.
- The best moment: "the eval caught my labels being wrong - the system outranked
  them. Video_11's fire was real and unlabeled. That's how I know the harness
  works."

## 4. Tradeoffs and honesty (2 min)

- What I'd do next (README failure taxonomy): peak-frame guarantee in the
  verifier sample; transcript-only verification for mention-style queries;
  frame-only eval queries to remove the label bias.
- What's deliberately absent: prosody truth (auditing needs listening),
  conformal abstention (needs a bigger labeled set - rule-based tiers today),
  license-plate voting (designed, cited, not built).
- Cost recap: ~$0.25 to index 2.5 hours, ~a cent per verified query, everything
  else local on Apple Silicon.
