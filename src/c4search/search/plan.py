"""LLM query planner: decompose a query into per-modality sub-queries.

Rules with evidence behind them: negations are extracted and never sent to a
retriever (bi-encoders rank negated pairs at or below random - NevIR);
attribute-like constraints ("at night") become filters, not searches; and the
raw query always remains a retrieval stream, so planning cannot do worse than
not planning.
"""

from c4search.openrouter import chat_json

# Plan modalities -> Doc modalities they retrieve against. The burned-in
# clock is on-screen text, so wall_clock rides with visual.
MODALITY_MAP = {
    "speech": ["transcript", "speaker_turn"],
    "visual": ["frame", "caption", "object", "scene", "wall_clock"],
    "audio": ["audio_window", "audio_tag", "vocal_arousal", "motion"],
    "caption": ["caption"],
}

PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sub_queries", "scene_filter", "anchor_text", "anchor_relation"],
    "properties": {
        "sub_queries": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "modalities", "role", "polarity", "variants"],
                "properties": {
                    "text": {"type": "string"},
                    "modalities": {"type": "array", "items": {
                        "type": "string",
                        "enum": list(MODALITY_MAP)}},
                    "role": {"type": "string", "enum": ["required", "supporting"]},
                    "polarity": {"type": "string", "enum": ["positive", "negative"]},
                    "variants": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "scene_filter": {"type": "string",
                         "enum": ["", "night", "daylight", "indoors"]},
        "anchor_text": {"type": "string"},
        "anchor_relation": {"type": "string", "enum": ["", "after", "before"]},
    },
}

PROMPT = """Decompose this video-search query over police bodycam footage into
at most 4 sub-queries for separate retrieval systems.

Modalities: "speech" (what people say), "visual" (what frames show), "audio"
(non-speech sound: shouting, sirens, engine, camera motion), "caption"
(scene descriptions).

Rules:
- Phrase speech sub-queries as words people would actually say; visual ones as
  what a frame shows.
- "variants": up to 3 lexical alternatives bridging query and spoken
  vocabulary (e.g. "breathalyzer result" -> "point two four", "blow into").
- polarity "negative" ONLY for explicit negations in the query ("without",
  "not", "no"). Never infer negations.
- scene_filter only when the query explicitly constrains it ("at night").
- anchor_text/anchor_relation only for explicit ordering ("after the arrest"
  -> anchor_text "the arrest", relation "after"); otherwise empty strings.
- Simple single-concept queries need only one sub-query.

Query: {query}"""


def fallback_plan(query: str) -> dict:
    return {
        "sub_queries": [{"text": query, "modalities": list(MODALITY_MAP),
                         "role": "required", "polarity": "positive",
                         "variants": []}],
        "scene_filter": "", "anchor_text": "", "anchor_relation": "",
    }


def plan_query(query: str, config: dict, meter: dict | None = None) -> dict:
    """One cheap LLM call; identity plan if the call fails or is disabled.

    Plans are disk-cached per query text: ablation rungs and eval reruns then
    see the identical plan, so rung deltas measure the pipeline, not planner
    variance - and repeated runs stop costing API calls.
    """
    if not config.get("enabled", True):
        return fallback_plan(query)

    import hashlib
    import json
    from pathlib import Path

    cache_file = None
    cache_dir = config.get("cache_dir")
    if cache_dir:
        digest = hashlib.sha256(query.lower().encode()).hexdigest()[:16]
        cache_file = Path(cache_dir) / f"plan_{digest}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())

    try:
        plan, cost = chat_json(
            model=config.get("model", "openai/gpt-5-nano"),
            content=[{"type": "text", "text": PROMPT.format(query=query)}],
            schema=PLAN_SCHEMA, schema_name="query_plan", timeout=60,
        )
        if meter is not None:
            meter["cost_usd"] = meter.get("cost_usd", 0.0) + (cost or 0.0)
    except RuntimeError:
        return fallback_plan(query)

    plan["sub_queries"] = plan["sub_queries"][:4]
    positives = [sq for sq in plan["sub_queries"] if sq["polarity"] == "positive"]
    if not positives:
        plan["sub_queries"].append(fallback_plan(query)["sub_queries"][0])
    # The raw query rides along so planning can never lose to not planning.
    if all(sq["text"].lower() != query.lower() for sq in plan["sub_queries"]):
        plan["sub_queries"].append({
            "text": query, "modalities": list(MODALITY_MAP),
            "role": "supporting", "polarity": "positive", "variants": [],
        })
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(plan))
    return plan


def doc_modalities(sub_query: dict) -> set[str]:
    allowed = set()
    for modality in sub_query["modalities"]:
        allowed.update(MODALITY_MAP.get(modality, []))
    return allowed
