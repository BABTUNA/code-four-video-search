"""Score the system against the labeled query set.

A prediction hits a truth span at tIoU >= 0.3, or when its midpoint falls
inside the truth. Metrics follow the long-form grounding literature's advice:
Hit@k over a ranked shortlist, plus abstention accuracy on no-answer queries.
"""

from dataclasses import dataclass


@dataclass
class QueryResult:
    query: str
    kind: str            # "direct" | "cross_modal" | "no_answer"
    hit_rank: int | None  # rank of first prediction hitting truth, else None
    abstained: bool


def tiou(a: tuple[float, float], b: tuple[float, float]) -> float:
    intersection = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return intersection / union if union > 0 else 0.0


def is_hit(prediction: dict, truths: list[dict]) -> bool:
    span = (prediction["t_start"], prediction["t_end"])
    midpoint = (span[0] + span[1]) / 2
    for truth in truths:
        if truth["video"] != prediction["video"]:
            continue
        truth_span = (truth["start"], truth["end"])
        if tiou(span, truth_span) >= 0.3:
            return True
        if truth_span[0] <= midpoint <= truth_span[1]:
            return True
    return False


def score_query(query: dict, predictions: list[dict]) -> QueryResult:
    truths = query.get("truth", [])
    abstained = not predictions
    hit_rank = None
    for rank, prediction in enumerate(predictions, 1):
        if is_hit(prediction, truths):
            hit_rank = rank
            break
    return QueryResult(query["query"], query.get("type", "direct"), hit_rank, abstained)


def summarize(results: list[QueryResult]) -> dict:
    answerable = [r for r in results if r.kind != "no_answer"]
    no_answer = [r for r in results if r.kind == "no_answer"]

    def rate(rows, predicate):
        return round(sum(predicate(r) for r in rows) / len(rows), 3) if rows else None

    summary = {
        "queries": len(results),
        "hit@1": rate(answerable, lambda r: r.hit_rank == 1),
        "hit@5": rate(answerable, lambda r: r.hit_rank is not None and r.hit_rank <= 5),
        "false_abstain": sum(r.abstained for r in answerable),
        "abstention_acc": rate(no_answer, lambda r: r.abstained),
    }
    for kind in ("direct", "cross_modal"):
        rows = [r for r in answerable if r.kind == kind]
        summary[f"hit@1_{kind}"] = rate(rows, lambda r: r.hit_rank == 1)
    return summary
