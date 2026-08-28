"""The query funnel: plan -> retrieve -> fuse -> rerank -> merge -> verify."""

import json

from c4search.search.fuse import rrf
from c4search.search.merge import Candidate, candidate_segments, hit_weight, score_track
from c4search.search.plan import doc_modalities, plan_query
from c4search.search.rerank import Reranker
from c4search.search.retrieve import Retrievers
from c4search.store import Store


def media_info(store: Store, video_id: str) -> dict:
    return json.loads((store.root / f"{video_id}.media.json").read_text())


def retrieve_subquery(retrievers: Retrievers, sub_query: dict, depth: int) -> list[int]:
    """Fused hits for one positive sub-query, filtered to its modalities."""
    queries = [sub_query["text"], *sub_query.get("variants", [])[:3]]
    rankings = {}
    for index, text in enumerate(queries):
        rankings[f"bm25_{index}"] = retrievers.bm25(text, depth)
    rankings["dense"] = retrievers.dense_text(sub_query["text"], depth)
    rankings["frames"] = retrievers.frames(sub_query["text"], depth)
    rankings["audio"] = retrievers.audio(sub_query["text"], depth)

    allowed = doc_modalities(sub_query)
    fused = [doc_id for doc_id, _ in rrf(rankings)]
    docs = retrievers.store.get_docs(fused)
    return [doc_id for doc_id in fused if docs[doc_id].modality in allowed]


def run_search(query: str, store: Store, config: dict, verify: bool = True,
               use_planner: bool = True, top: int = 5) -> dict:
    retrieval_config = config.get("retrieval", {})
    depth = retrieval_config.get("depth", 100)
    keep = retrieval_config.get("rerank_keep", 20)

    plan = (plan_query(query, config.get("planner", {}))
            if use_planner else plan_query(query, {"enabled": False}))
    positives = [sq for sq in plan["sub_queries"] if sq["polarity"] == "positive"]
    negatives = [sq for sq in plan["sub_queries"] if sq["polarity"] == "negative"]

    retrievers = Retrievers(store, retrieval_config)
    reranker = Reranker(retrieval_config)
    durations = {
        name.removesuffix(".media.json"): None
        for name in [p.name for p in store.root.glob("*.media.json")]
    }
    for video_id in durations:
        durations[video_id] = media_info(store, video_id)["duration_s"]

    tracks: dict[str, dict] = {}
    hits_by_video: dict[str, list] = {}
    all_docs: dict = {}
    required: list[str] = []
    for index, sub_query in enumerate(positives):
        sq_id = f"sq{index}"
        if sub_query["role"] == "required":
            required.append(sq_id)
        hit_ids = retrieve_subquery(retrievers, sub_query, depth)
        docs = store.get_docs(hit_ids)
        all_docs.update(docs)

        # Rerank the text-bearing hits; vector-only hits keep fused ranks.
        text_hits = [(doc_id, docs[doc_id].text) for doc_id in hit_ids
                     if docs[doc_id].text]
        reranked = reranker.rerank(sub_query["text"], text_hits, keep)
        vector_hits = [doc_id for doc_id in hit_ids if not docs[doc_id].text]
        weighted = (
            [(doc_id, hit_weight(rank)) for rank, doc_id in enumerate(reranked, 1)]
            + [(doc_id, hit_weight(rank))
               for rank, doc_id in enumerate(vector_hits[:keep], 1)]
        )

        tracks[sq_id] = {}
        for doc_id, weight in weighted:
            video_id = docs[doc_id].video_id
            hits_by_video.setdefault(video_id, []).append((doc_id, weight))
        for video_id, duration in durations.items():
            video_hits = [(doc_id, weight) for doc_id, weight in weighted
                          if docs[doc_id].video_id == video_id]
            if video_hits:
                tracks[sq_id][video_id] = score_track(video_hits, docs, duration)

    candidates = candidate_segments(tracks, required, hits_by_video, all_docs, top=top)
    candidates = apply_scene_filter(candidates, plan.get("scene_filter", ""), store)
    candidates = apply_anchor(candidates, plan, store, config)

    results = []
    if verify and candidates:
        from c4search.search.verify import Verifier
        verifier = Verifier(config.get("verifier", {}))
        elements = [sq["text"] for sq in positives if sq["role"] == "required"] or [query]
        elements += [f"NOT: {sq['text']}" for sq in negatives]
        for candidate in candidates:
            verdict = verifier.verify(
                candidate, elements, store, media_info(store, candidate.video_id))
            results.append({"candidate": candidate, "verdict": verdict})
    else:
        results = [{"candidate": c, "verdict": {"tier": "unverified"}}
                   for c in candidates]
    return {"plan": plan, "results": results, "docs": all_docs}


def apply_scene_filter(candidates: list[Candidate], scene: str,
                       store: Store) -> list[Candidate]:
    if not scene:
        return candidates
    keyword = {"night": "night", "daylight": "daylight", "indoors": "indoors"}[scene]
    kept = []
    for candidate in candidates:
        scenes = store.docs(candidate.video_id, "scene")
        if any(keyword in doc.text
               and doc.t_start <= candidate.t_end and doc.t_end >= candidate.t_start
               for _, doc in scenes):
            kept.append(candidate)
    return kept


def apply_anchor(candidates: list[Candidate], plan: dict, store: Store,
                 config: dict) -> list[Candidate]:
    """Two-hop: ground the anchor event, then keep candidates on one side."""
    anchor_text, relation = plan.get("anchor_text"), plan.get("anchor_relation")
    if not anchor_text or not relation:
        return candidates
    anchored = run_search(anchor_text, store, config, verify=False,
                          use_planner=False, top=1)
    if not anchored["results"]:
        return candidates
    anchor = anchored["results"][0]["candidate"]
    if relation == "after":
        return [c for c in candidates
                if c.video_id != anchor.video_id or c.t_start >= anchor.t_start]
    return [c for c in candidates
            if c.video_id != anchor.video_id or c.t_end <= anchor.t_end]
