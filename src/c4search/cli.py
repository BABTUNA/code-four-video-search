from pathlib import Path

import typer

import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.config import load_config
from c4search.ingest import ingest_video

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Natural-language search over body-worn camera footage."""


@app.command()
def ingest(
    videos: list[Path],
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
) -> None:
    """Run the configured extractors over videos and index the results."""
    settings = load_config(config)
    if not settings.get("extractors"):
        typer.echo("No extractors configured yet; see configs/default.yaml.", err=True)
        raise typer.Exit(code=1)
    for video in videos:
        typer.echo(f"{video.stem}:")
        for stage, count in ingest_video(video, settings).items():
            typer.echo(f"  {stage}: {count} docs")


def clock_label(store, candidate) -> str:
    """Wall-clock time for a span when the overlay OCR anchored it."""
    anchors = store.docs(candidate.video_id, "wall_clock")
    for _, doc in anchors:
        if abs(doc.t_start - candidate.t_start) <= 60:
            from c4search.extractors.clock_ocr import clock_text
            offset = candidate.t_start - doc.t_start
            return f"  (wall clock ~{clock_text(doc.extra['clock_s'] + offset)})"
    return ""


def hms(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@app.command()
def search(
    query: str,
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    top: int = typer.Option(5, help="How many candidate segments to consider"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip VLM verification"),
    no_plan: bool = typer.Option(False, "--no-plan", help="Skip the query planner"),
) -> None:
    """Search the indexed corpus with a natural-language query."""
    from c4search.search.pipeline import run_search
    from c4search.store import Store

    settings = load_config(config)
    store = Store(Path(settings.get("data_dir", "data")) / "index")
    outcome = run_search(query, store, settings, verify=not no_verify,
                         use_planner=not no_plan, top=top)

    shown = 0
    for rank, result in enumerate(outcome["results"], 1):
        candidate, verdict = result["candidate"], result["verdict"]
        if verdict["tier"] == "rejected" and shown:
            continue
        shown += 1
        typer.echo(
            f"\n#{rank}  {candidate.video_id}  "
            f"{hms(candidate.t_start)}-{hms(candidate.t_end)}  "
            f"[{verdict['tier'].upper()}]{clock_label(store, candidate)}"
        )
        if verdict.get("reason"):
            typer.echo(f"    verifier ({verdict.get('verifier', '?')}): {verdict['reason']}")
        evidence = outcome["docs"]
        for doc_id in candidate.evidence[:6]:
            doc = evidence[doc_id]
            label = doc.text or doc.extra.get("top_event", "")
            typer.echo(f"    {doc.modality:12s} [{hms(doc.t_start)}] {label[:76]}")
    if shown == 0:
        typer.echo("no confident match")


@app.command()
def eval(
    queries: Path = typer.Option(Path("eval/queries.yaml"), help="Labeled query set"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Ablation: skip verification"),
) -> None:
    """Score the system against the labeled query set."""
    import json
    import yaml

    from c4search.evaluate import score_query, summarize
    from c4search.search.pipeline import run_search
    from c4search.store import Store

    settings = load_config(config)
    store = Store(Path(settings.get("data_dir", "data")) / "index")
    query_set = yaml.safe_load(queries.read_text())["queries"]

    results = []
    for entry in query_set:
        outcome = run_search(entry["query"], store, settings,
                             verify=not no_verify, top=5)
        predictions = [
            {"video": r["candidate"].video_id, "t_start": r["candidate"].t_start,
             "t_end": r["candidate"].t_end}
            for r in outcome["results"]
            if r["verdict"]["tier"] in ("confirmed", "candidate", "unverified")
        ]
        result = score_query(entry, predictions)
        results.append(result)
        marker = "ABSTAIN" if result.abstained else f"hit@{result.hit_rank or '-'}"
        typer.echo(f"  [{result.kind:9s}] {marker:8s} {entry['query'][:60]}")

    typer.echo(json.dumps(summarize(results), indent=2))
