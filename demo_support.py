"""Helpers for demo.ipynb: run searches in-process, render results and clips."""

from pathlib import Path

from IPython.display import HTML, display

from c4search.config import load_config
from c4search.search.pipeline import run_search
from c4search.store import Store

SETTINGS = load_config(Path("configs/recommended.yaml"))
STORE = Store(Path("data/index"))
TIER_COLORS = {"confirmed": "#1a7f37", "candidate": "#9a6700",
               "rejected": "#cf222e", "unverified": "#57606a"}

_last_results = []


def hms(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def search(query: str, top: int = 5, show: int = 2) -> None:
    """Run the full funnel (verifying `top` candidates), show up to `show` cards."""
    global _last_results
    outcome = run_search(query, STORE, SETTINGS, top=top)
    _last_results = []

    parts = [f"<h4 style='margin:4px 0'>{query}</h4>"]
    for result in outcome["results"]:
        candidate, verdict = result["candidate"], result["verdict"]
        if verdict["tier"] == "rejected" and _last_results:
            continue
        if len(_last_results) >= show:
            break
        _last_results.append(candidate)
        color = TIER_COLORS.get(verdict["tier"], "#57606a")
        parts.append(
            f"<div style='margin:10px 0;padding:10px;border-left:5px solid {color};"
            f"background:#f6f8fa;color:#1f2328;border-radius:4px'>"
            f"<b>#{len(_last_results)}&nbsp; {candidate.video_id} &nbsp;"
            f"{hms(candidate.t_start)}&ndash;{hms(candidate.t_end)}</b> "
            f"<span style='color:{color};font-weight:700'>"
            f"[{verdict['tier'].upper()}]</span>"
            f"<div style='color:#57606a;font-size:13px;margin:4px 0'>"
            f"{verdict.get('reason', '')}</div>"
        )
        for doc_id in candidate.evidence[:4]:
            doc = outcome["docs"][doc_id]
            label = doc.text or doc.extra.get("top_event", "")
            parts.append(
                f"<div style='font-family:monospace;font-size:12px'>"
                f"[{hms(doc.t_start)}] {doc.modality}: {label[:90]}</div>")
        parts.append("</div>")
    tiers = {result["verdict"]["tier"] for result in outcome["results"]}
    if not _last_results or tiers <= {"rejected"}:
        parts.insert(1, "<div style='padding:8px;background:#fff1f0;color:#cf222e;"
                        "font-weight:700;border-radius:4px'>NO CONFIDENT MATCH"
                        "<span style='font-weight:400;color:#57606a'> - closest "
                        "rejected candidate shown with the verifier's reason"
                        "</span></div>")
    telemetry = outcome["telemetry"]
    parts.append(f"<div style='color:#8b949e;font-size:12px'>"
                 f"{telemetry['total_s']}s &middot; API ${telemetry['cost_usd']}</div>")
    display(HTML("".join(parts)))


def clip(rank: int = 1, before: float = 3.0) -> None:
    """Embed the video for a result from the last search, cued to its span."""
    candidate = _last_results[rank - 1]
    start = max(0.0, candidate.t_start - before)
    source = f"c4-videos/{candidate.video_id}.mp4#t={start:.0f},{candidate.t_end:.0f}"
    display(HTML(
        f"<video controls preload='metadata' width='640' src='{source}'></video>"
        f"<div style='font-size:12px;color:#57606a'>{candidate.video_id} &middot; "
        f"{hms(candidate.t_start)}&ndash;{hms(candidate.t_end)} "
        f"(player cued {before:.0f}s early)</div>"))
