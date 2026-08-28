# Retrieval and Query Models

This is not an input modality. It is the shared layer that turns modality evidence into searchable records and converts user queries into retrieval plans.

## Embedding choice: Qwen3 Embedding 8B

All processors produce textual `content`, so the initial system can embed visual, audio, transcript, and OCR evidence with one text embedding model. `qwen/qwen3-embedding-8b` is available through OpenRouter's embeddings endpoint and is designed for text retrieval and ranking.

Alternative: `openai/text-embedding-3-small` is a mature, inexpensive baseline. CLAP is a possible future raw audio-text embedding experiment, but using it would create a second, non-comparable vector space.

References: [Qwen3 Embedding 8B](https://openrouter.ai/qwen/qwen3-embedding-8b/providers), [OpenAI embedding models on OpenRouter](https://openrouter.ai/provider/openai), [OpenRouter embeddings API](https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings).

## Query planner choice: Gemini 3.7 Flash

Use `google/gemini-3.7-flash` structured output to convert a natural-language query into:

- Required clauses
- Relevant modalities
- Search text for each clause
- AND/OR requirements
- Temporal or same-actor relationships

The planner proposes the search plan; deterministic code validates the JSON and performs retrieval.

## Reranking alternatives

| Classification | Model | Use |
| --- | --- | --- |
| General LLM verifier | Gemini 3.7 Flash | Verify the final small candidate set using stored evidence |
| Dedicated text reranker | Qwen3 Reranker 0.6B or 4B | Score query/evidence pairs cheaply and consistently |
| No reranker | Cosine similarity only | Simplest baseline for measuring whether reranking actually helps |

Reference: [Qwen models on OpenRouter](https://openrouter.ai/qwen).

## Decision

Start with Qwen3 Embedding 8B plus cosine similarity and add reranking only after measuring the baseline. Keeping the embedding model, planner, and reranker behind separate interfaces makes every choice independently replaceable.

