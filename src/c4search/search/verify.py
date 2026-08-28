"""VLM verification: look at real frames + transcript, and be allowed to say no.

Design against measured failure modes: the verifier describes before judging
and is never told what retrieval expects (VLMs capitulate to leading framing);
in dark scenes a "no" is weak evidence (low-light VLMs miss objects rather
than hallucinate), so night negatives become "unclear"; unclear verdicts
escalate to an API model when a key is available.
"""

import base64
import json
import re
from pathlib import Path

from c4search.openrouter import chat_json
from c4search.search.merge import Candidate
from c4search.store import Store

PROMPT = """You are auditing a match from a video search system over police
bodycam footage. You see {n} frames sampled from one candidate segment, plus
the transcript around it.

First, describe what is actually visible in the frames, in 2-3 sentences.
Then decide for each required element whether the frames/transcript show it.
Do not assume the segment matches; wrong candidates are common.

Judging rules:
- The transcript is evidence. An event the transcript supports counts as
  present even when these sampled frames do not show it - frames that
  CONTRADICT the transcript are different from frames that merely miss the
  moment.
- For queries about what people SAY or DISCUSS, the transcript alone can
  fully satisfy the query.

Required elements:
{elements}

Transcript (context):
{transcript}

Answer with ONLY this JSON:
{{"description": "...", "elements": [{{"name": "...", "present": "yes|no|unclear"}}], "match": "yes|no|unclear", "reason": "..."}}"""

VERDICT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["description", "elements", "match", "reason"],
    "properties": {
        "description": {"type": "string"},
        "elements": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "present"],
            "properties": {"name": {"type": "string"},
                           "present": {"type": "string",
                                       "enum": ["yes", "no", "unclear"]}}}},
        "match": {"type": "string", "enum": ["yes", "no", "unclear"]},
        "reason": {"type": "string"},
    },
}


def parse_verdict(output: str) -> dict | None:
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        return None
    try:
        verdict = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    if verdict.get("match") not in {"yes", "no", "unclear"}:
        return None
    return verdict


def pick_frames(frames_dir: Path, frame_fps: float, t_start: float,
                t_end: float, count: int = 8,
                focus_times: list[float] = ()) -> list[Path]:
    """Sample frames across the span, guaranteeing frames nearest the
    strongest evidence - uniform sampling alone misses the event core in a
    long span."""
    paths = sorted(frames_dir.glob("*.jpg"))
    inside = [
        path for path in paths
        if t_start <= (int(path.stem) - 1) / frame_fps <= t_end
    ]
    if len(inside) <= count:
        return inside

    picked = []
    for focus in list(focus_times)[:count // 2]:
        nearest = min(inside, key=lambda p: abs((int(p.stem) - 1) / frame_fps - focus))
        if nearest not in picked:
            picked.append(nearest)
    remaining = [path for path in inside if path not in picked]
    fill = count - len(picked)
    step = len(remaining) / fill
    picked.extend(remaining[int(i * step)] for i in range(fill))
    return sorted(picked)


def adjust_for_darkness(verdict: dict, night: bool) -> dict:
    """In low light VLMs miss present objects rather than hallucinate absent
    ones (DarkQA), so a visibility-limited "no" softens to "unclear". A "no"
    where every element was judged cleanly (the verifier saw enough to be
    sure, e.g. from transcript) stands - darkness is not a free pass."""
    visibility_limited = any(
        element.get("present") == "unclear" for element in verdict.get("elements", []))
    if night and verdict["match"] == "no" and visibility_limited:
        return verdict | {"match": "unclear",
                          "reason": verdict["reason"] + " (dark frames: a visual 'no' is weak evidence)"}
    return verdict


class Verifier:
    def __init__(self, config: dict):
        self.model_id = config.get(
            "model", "mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
        self.escalation_model = config.get(
            "escalation_model", "google/gemini-3.5-flash-lite")
        self.max_frames = config.get("max_frames", 8)
        self.use_local = config.get("use_local", True)
        self.cost_usd = 0.0

    def _local_verdict(self, prompt: str, frame_paths: list[Path]) -> dict | None:
        from mlx_vlm import generate, load
        from mlx_vlm.prompt_utils import apply_chat_template

        from c4search.search.retrieve import cached

        model, processor = cached(f"vlm:{self.model_id}",
                                  lambda: load(self.model_id))
        formatted = apply_chat_template(
            processor, model.config, prompt, num_images=len(frame_paths))
        output = generate(
            model, processor, formatted, [str(p) for p in frame_paths],
            max_tokens=500, temperature=0.0, verbose=False,
        )
        text = output.text if hasattr(output, "text") else str(output)
        return parse_verdict(text)

    def _escalate(self, prompt: str, frame_paths: list[Path]) -> dict | None:
        content = [{"type": "text", "text": prompt}]
        for path in frame_paths:
            image = base64.b64encode(path.read_bytes()).decode()
            content.append({"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image}"}})
        try:
            verdict, cost = chat_json(
                model=self.escalation_model, content=content,
                schema=VERDICT_SCHEMA, schema_name="verdict", timeout=90)
            self.cost_usd += cost or 0.0
            return verdict
        except RuntimeError:
            return None

    def verify(self, candidate: Candidate, elements: list[str],
               store: Store, media: dict, speech_only: bool = False) -> dict:
        """Returns the verdict plus a tier: confirmed / candidate / rejected."""
        evidence_docs = store.get_docs(candidate.evidence[:4])
        focus_times = [
            (doc.t_start + doc.t_end) / 2 for doc in evidence_docs.values()
        ]
        frame_paths = pick_frames(
            Path(media["frames_dir"]), media["frame_fps"],
            candidate.t_start, candidate.t_end, self.max_frames, focus_times)
        transcript = "\n".join(
            f"[{doc.t_start:.0f}s] ({doc.extra.get('role', '?')}) {doc.text}"
            for _, doc in store.docs(candidate.video_id, "transcript")
            if candidate.t_start - 20 <= doc.t_start <= candidate.t_end + 20
        )
        night = any(
            "night" in doc.text
            for _, doc in store.docs(candidate.video_id, "scene")
            if doc.t_start <= candidate.t_end and doc.t_end >= candidate.t_start
        )
        prompt = PROMPT.format(
            n=len(frame_paths),
            elements="\n".join(f"- {element}" for element in elements),
            transcript=transcript or "(no speech in range)",
        )
        if speech_only:
            prompt += ("\nNote: this query asks about something said or "
                       "discussed. The transcript is the primary evidence; "
                       "judge the match from it, with frames as context only.")

        verdict = None
        if frame_paths and self.use_local:
            verdict = self._local_verdict(prompt, frame_paths)
            if verdict:
                verdict = adjust_for_darkness(verdict, night)
                verdict["verifier"] = "local"
        if frame_paths and (verdict is None or verdict["match"] == "unclear"):
            escalated = self._escalate(prompt, frame_paths)
            if escalated:
                verdict = adjust_for_darkness(escalated, night) | {"verifier": "escalated"}
        if verdict is None:
            verdict = {"description": "", "elements": [], "match": "unclear",
                       "reason": "no frames or verifier unavailable",
                       "verifier": "none"}

        tier = {"yes": "confirmed", "no": "rejected",
                "unclear": "candidate"}[verdict["match"]]
        return verdict | {"tier": tier}
