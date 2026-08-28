def rrf(rankings: dict[str, list[int]], k: int = 60) -> list[tuple[int, float]]:
    """Reciprocal rank fusion (Cormack et al., SIGIR 2009), k=60.

    Fuses by rank only: BM25 scores and cosine similarities are not
    comparable, ranks always are.
    """
    scores: dict[int, float] = {}
    for ids in rankings.values():
        for rank, doc_id in enumerate(ids, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: -pair[1])
