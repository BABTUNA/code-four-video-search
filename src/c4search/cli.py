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
    playlist = []
    for rank, result in enumerate(outcome["results"], 1):
        candidate, verdict = result["candidate"], result["verdict"]
        if verdict["tier"] == "rejected" and shown:
            continue
        shown += 1
        playlist.append({"rank": rank, "video": candidate.video_id,
                         "t_start": candidate.t_start, "t_end": candidate.t_end})
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
    else:
        import json
        store.root.joinpath("last_search.json").write_text(
            json.dumps({"query": query, "results": playlist}))
        typer.echo("\nwatch a result at its timestamp: c4 play <rank>")
    telemetry = outcome["telemetry"]
    typer.echo(
        f"\n[{telemetry['total_s']}s"
        f" | plan {telemetry['stage_s']['plan']}s"
        f" · retrieve+rerank {telemetry['stage_s']['retrieve_rerank']}s"
        f" · merge {telemetry['stage_s']['merge']}s"
        f" · verify {telemetry['stage_s']['verify']}s"
        f" | API ${telemetry['cost_usd']}]"
    )


@app.command()
def play(
    rank: int = typer.Argument(1, help="Result number from the last search"),
    before: float = typer.Option(3.0, help="Seconds of context before the span"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
) -> None:
    """Open a video player at the timestamp of a result from the last search."""
    import json
    import shutil
    import subprocess

    from c4search.store import Store

    settings = load_config(config)
    store = Store(Path(settings.get("data_dir", "data")) / "index")
    state_file = store.root / "last_search.json"
    if not state_file.exists():
        typer.echo("no previous search - run c4 search first", err=True)
        raise typer.Exit(code=1)

    state = json.loads(state_file.read_text())
    entry = next((r for r in state["results"] if r["rank"] == rank), None)
    if entry is None:
        typer.echo(f"no result #{rank} in the last search", err=True)
        raise typer.Exit(code=1)

    media = json.loads((store.root / f"{entry['video']}.media.json").read_text())
    start = max(0.0, entry["t_start"] - before)
    player = shutil.which("mpv") or shutil.which("ffplay")
    if player is None:
        typer.echo("needs mpv or ffplay on PATH", err=True)
        raise typer.Exit(code=1)

    title = f"{entry['video']}  {hms(entry['t_start'])}-{hms(entry['t_end'])}"
    if player.endswith("mpv"):
        arguments = [player, f"--start={start}", f"--title={title}", media["source"]]
    else:
        arguments = [player, "-ss", str(start), "-window_title", title,
                     "-loglevel", "error", media["source"]]
    typer.echo(f"opening {title} (from {hms(start)})")
    subprocess.Popen(arguments)


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

    results, per_query = [], []
    total_cost = total_s = 0.0
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
        telemetry = outcome["telemetry"]
        total_cost += telemetry["cost_usd"]
        total_s += telemetry["total_s"]
        per_query.append({"query": entry["query"], "kind": result.kind,
                          "hit_rank": result.hit_rank,
                          "abstained": result.abstained, **telemetry})
        marker = "ABSTAIN" if result.abstained else f"hit@{result.hit_rank or '-'}"
        typer.echo(f"  [{result.kind:11s}] {marker:8s} "
                   f"{telemetry['total_s']:6.1f}s  ${telemetry['cost_usd']:.4f}  "
                   f"{entry['query'][:52]}")

    summary = summarize(results)
    summary["total_s"] = round(total_s, 1)
    summary["total_cost_usd"] = round(total_cost, 4)
    summary["s_per_query"] = round(total_s / max(1, len(results)), 1)
    summary["cost_per_query_usd"] = round(total_cost / max(1, len(results)), 4)
    typer.echo(json.dumps(summary, indent=2))

    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_file = Path("eval") / f"results-{stamp}.json"
    results_file.write_text(json.dumps({
        "config": str(config), "no_verify": no_verify,
        "summary": summary, "per_query": per_query,
    }, indent=2))
    typer.echo(f"written: {results_file}")
