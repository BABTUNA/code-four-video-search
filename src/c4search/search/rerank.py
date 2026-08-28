"""Cross-encoder rerank between cheap retrieval and expensive verification.

Cross-encoders are also the only retrieval architecture above random on
negation (NevIR), so this is where planner-extracted constraints first bite.
"""


from c4search.search.retrieve import cached


class Reranker:
    def __init__(self, config: dict):
        self.model_id = config.get("rerank_model", "BAAI/bge-reranker-v2-m3")

    def rerank(self, query: str, candidates: list[tuple[int, str]],
               keep: int) -> list[int]:
        """candidates are (doc_id, text); returns the top doc_ids by score."""
        if not candidates:
            return []
        from sentence_transformers import CrossEncoder
        model = cached(f"ce:{self.model_id}", lambda: CrossEncoder(self.model_id))
        scores = model.predict(
            [(query, text) for _, text in candidates], show_progress_bar=False)
        ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])
        return [doc_id for (doc_id, _), _ in ranked[:keep]]
