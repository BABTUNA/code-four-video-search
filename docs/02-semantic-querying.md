# Phase 2: Semantic Indexing and Querying

## Goal

Continue from Phase 1 by making the stored modality evidence searchable through natural-language queries.

The completed system will:

1. Embed evidence from completed processing runs.
2. Store vectors in replaceable modality-specific indexes.
3. Convert a natural-language query into a validated query plan.
4. Retrieve candidates for each query clause.
5. Combine candidates by shared `segment_id`.
6. Rank qualifying segments with a relevance score.
7. Show playable search results and supporting evidence in the UI.

This phase extends the Phase 1 contracts. It does not change segmentation or ask modality processors to produce query-specific output.

## Code rules

- Prefer the shortest implementation that is still easy to understand.
- Do not use shorthand when an explicit version is clearer.
- Keep planning, retrieval, Boolean qualification, and scoring as separate steps.
- Use typed contracts at LLM and index boundaries.
- Keep model names and retrieval limits in configuration.
- Begin with deterministic scoring and no reranker.
- Do not call a relevance score a probability or a percentage of correctness.

## User experience

Add a search page containing:

- A natural-language search box
- Search status and understandable errors
- Ranked result cards
- Video filename and segment timestamps
- A relevance score
- Evidence grouped by matched clause and modality
- A video player that starts at the selected segment
- A collapsible view of the generated query plan for demonstration and debugging

Add an indexing section to the existing processing-run page containing:

- Indexed or not indexed status
- Evidence count per modality
- Embedding model name
- A rebuild-index action

The interface should explain why a result matched. Do not expose raw vectors or internal database details.

## System flow

```text
Phase 1 evidence
    ↓
Replaceable embedder
    ↓
Modality-specific vector indexes

Natural-language query
    ↓
Replaceable query planner
    ↓
Validated QueryPlan
    ↓
Per-clause retrieval
    ↓
Combine by segment_id
    ↓
Qualification and score fusion
    ↓
Ranked playable results
```

## Technology additions

- LanceDB as an embedded local vector store
- `qwen/qwen3-embedding-8b` through OpenRouter as the default embedder
- `google/gemini-3.7-flash` structured output as the default query planner

Keep SQLite as the source of truth for media, segments, processing runs, and evidence. LanceDB is a rebuildable derived index.

## Project structure additions

```text
backend/app/
  indexes/
    base.py
    lancedb.py
  query/
    planner.py
    retriever.py
    combiner.py
    scoring.py
    service.py
  embeddings.py

frontend/app/
  search/page.tsx

frontend/components/
  search-form.tsx
  search-result.tsx
  query-plan.tsx
```

`query/service.py` orchestrates the flow but delegates each step. It should read like a short sequence of named operations rather than contain planning, vector math, and scoring inline.

## Query plan contract

The planner converts the original query into searchable clauses and simple `must`/`should` logic:

```json
{
  "original_query": "Find a police officer with a person who is drunk or raising their voice",
  "clauses": [
    {
      "id": "police_officer",
      "search_text": "A police officer is present",
      "modalities": ["visual"]
    },
    {
      "id": "intoxication",
      "search_text": "A person appears or sounds intoxicated",
      "modalities": ["visual", "audio", "transcript"]
    },
    {
      "id": "raised_voice",
      "search_text": "A person is speaking loudly or shouting",
      "modalities": ["audio"]
    }
  ],
  "must": ["police_officer"],
  "should": ["intoxication", "raised_voice"],
  "minimum_should_match": 1
}
```

Meaning:

```text
police_officer AND at least one of (intoxication, raised_voice)
```

Rules:

- Every identifier in `must` and `should` must reference a clause.
- Every `must` clause must match the same segment.
- At least `minimum_should_match` distinct `should` clauses must match.
- If `should` is empty, `minimum_should_match` must be zero.
- Each clause must contain at least one supported modality.
- Arbitrary recursive Boolean trees are intentionally excluded from the MVP.

The planner creates `search_text`; retrieval never invents it. Deterministic Pydantic validation runs before any index search.

## Index records

Create one LanceDB table per modality. Every evidence record becomes one vector record:

```json
{
  "run_id": "run_123",
  "segment_id": "video_1:25000-55000",
  "media_id": "video_1",
  "start_ms": 25000,
  "end_ms": 55000,
  "modality": "audio",
  "content": "A man speaks loudly over traffic noise.",
  "embedding": [0.012, -0.084, 0.031]
}
```

The index is derived data. Rebuilding it never modifies Phase 1 evidence.

Store index metadata so the backend knows:

- Processing run
- Modality
- Evidence count
- Embedding model
- Embedding dimensions
- Build time

Persist this metadata in a small SQLite `index_versions` table. Vectors remain in LanceDB, while SQLite records which index version is ready for each processing run and modality.

Never mix vectors created by different embedding models in the same index version.

## Replaceable query components

Use four narrow boundaries:

```python
class QueryPlanner(Protocol):
    async def plan(self, query: str) -> QueryPlan:
        ...


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class EvidenceIndex(Protocol):
    async def search(
        self,
        run_id: str,
        modality: Modality,
        embedding: list[float],
        limit: int,
    ) -> list[IndexMatch]:
        ...


class ScoreFusion(Protocol):
    def score(self, matches: list[ClauseMatch]) -> float:
        ...
```

The planner, embedder, vector store, and scoring implementation can then be changed independently.

## Index-building behavior

1. Select a completed Phase 1 processing run.
2. Read its evidence from SQLite, grouped by modality.
3. Batch the `content` fields through the configured embedder.
4. Validate the returned vector count and dimensions.
5. Write each modality to its own new index version.
6. Mark the version ready only after the complete build succeeds.
7. Atomically select the completed version as active.

Start with small batches and sequential modality builds. Parallelism can be introduced only if indexing time becomes a demonstrated problem.

## Per-clause retrieval

For every clause:

1. Take the clause's planner-generated `search_text`.
2. Embed it once.
3. Search only the modality indexes listed in that clause.
4. Retrieve the top `K` matches from each selected modality.
5. Normalize scores within each modality to the range `0–1`.
6. If the same segment appears through multiple modalities for one clause, keep its strongest score and preserve all supporting evidence.

Normalized output:

```json
{
  "clause_id": "raised_voice",
  "segment_id": "video_1:25000-55000",
  "score": 0.89,
  "evidence": [
    {
      "modality": "audio",
      "content": "A man speaks loudly and aggressively."
    }
  ]
}
```

Raw similarities from different modality indexes should not be compared directly.

## Segment combination

Group every clause match by `segment_id`, then apply the plan:

1. Reject a segment missing any `must` clause.
2. Count its distinct matching `should` clauses.
3. Reject it if that count is below `minimum_should_match`.
4. Keep its clause and modality evidence for explanation.

All conditions apply to the same shared segment. There is no fine-grained timestamp joining in this take-home.

## Score fusion

Boolean qualification and ranking are separate:

- The query plan decides whether a segment qualifies.
- Score fusion orders the qualifying segments.

For the initial implementation, average the normalized scores of the clauses that matched:

```text
police_officer = 0.82
raised_voice   = 0.90

relevance_score = (0.82 + 0.90) / 2 = 0.86
```

Return the value as `relevance_score`. It is not an `86%` probability that the result is correct.

Keep this formula in one small `ScoreFusion` implementation so rank fusion or calibrated weights can replace it later without changing retrieval.

## Search response

```json
{
  "query": "Find a police officer with someone raising their voice",
  "plan": {},
  "results": [
    {
      "media_id": "video_1",
      "segment_id": "video_1:25000-55000",
      "start_ms": 25000,
      "end_ms": 55000,
      "relevance_score": 0.86,
      "clause_matches": []
    }
  ]
}
```

Returning the plan and clause evidence makes the system explainable and easier to debug during the demonstration.

## API additions

```text
POST /api/processing-runs/{run_id}/indexes
GET  /api/processing-runs/{run_id}/indexes
POST /api/search
```

Search request:

```json
{
  "query": "Find a police officer with someone raising their voice",
  "run_id": "run_123",
  "limit": 10
}
```

Search should only use a ready index built from the requested processing run. Return a clear conflict error if no ready index exists.

## Frontend changes

### Index controls

On the processing-run view:

1. Show index status and evidence counts.
2. Provide one `Build index` or `Rebuild index` button.
3. Poll while the index is building.
4. Link to search when the index is ready.

### Search page

1. Submit the query and selected processing run.
2. Show the generated query plan in a collapsed panel.
3. Render ranked result cards.
4. Show timestamp, relevance score, matched clauses, and evidence.
5. Clicking a result opens the video player at `start_ms`.

The result card should prioritize the evidence explanation over decorative UI.

## Implementation order

1. Define `QueryPlan`, `IndexMatch`, `ClauseMatch`, and `SearchResult` contracts.
2. Implement an in-memory fake planner, embedder, and index for flow tests.
3. Implement deterministic clause combination and score fusion.
4. Build the search API against the fake components.
5. Add LanceDB and the real embedding implementation.
6. Add index status and rebuild controls to the Phase 1 UI.
7. Add the search page and playable result cards.
8. Add the structured-output LLM planner last.
9. Replace fake flow tests with saved planner and index fixtures where appropriate.

Building deterministic retrieval before the LLM planner keeps planner mistakes separate from combination and scoring bugs.

## Tests

- Invalid query plans fail before retrieval.
- Each clause searches only its declared modality indexes.
- One query embedding is created per clause.
- Duplicate segment matches preserve evidence but do not create duplicate results.
- Every `must` clause is required.
- `minimum_should_match` is enforced.
- Score fusion only receives qualifying segments.
- Index builds reject mixed embedding dimensions.
- A search result seeks the video to the correct `start_ms`.

Use fake embeddings with obvious vectors in unit tests. Do not call OpenRouter from the normal test suite.

## Phase 2 acceptance criteria

- A user can build indexes from a completed processing run.
- A natural-language query produces a visible, validated query plan.
- Every clause searches only its selected modality indexes.
- Multimodal conditions combine through the shared `segment_id`.
- `must`, `should`, and `minimum_should_match` behave predictably.
- Results are ranked, playable, and accompanied by supporting evidence.
- Each model-dependent or storage-dependent component can be replaced independently.
- A fresh developer can run processing, indexing, and search from the project README.

## Deferred until the baseline works

- LLM or dedicated reranking
- Planner fallbacks
- Precision@K and Recall@K evaluation harness
- Adjacent-segment result merging
- Calibrated cross-modality scores
- Arbitrary nested Boolean expressions
- Production authentication, distributed queues, and hosted databases
