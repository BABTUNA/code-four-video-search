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


@app.command()
def search(
    query: str,
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    top: int = typer.Option(10, help="How many fused hits to show"),
) -> None:
    """Search the indexed corpus with a natural-language query."""
    from c4search.search.fuse import rrf
    from c4search.search.retrieve import Retrievers
    from c4search.store import Store

    settings = load_config(config)
    store = Store(Path(settings.get("data_dir", "data")) / "index")
    retrievers = Retrievers(store, settings.get("retrieval", {}))

    depth = settings.get("retrieval", {}).get("depth", 100)
    rankings = {
        "bm25": retrievers.bm25(query, depth),
        "dense": retrievers.dense_text(query, depth),
        "frames": retrievers.frames(query, depth),
        "audio": retrievers.audio(query, depth),
    }
    fused = rrf(rankings)[:top]
    docs = store.get_docs([doc_id for doc_id, _ in fused])
    for doc_id, score in fused:
        doc = docs[doc_id]
        label = doc.text or doc.extra.get("top_event", "")
        typer.echo(
            f"{score:.4f}  {doc.video_id}  [{doc.t_start:7.1f}-{doc.t_end:7.1f}]"
            f"  {doc.modality:12s}  {label[:80]}"
        )


@app.command()
def eval(
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
) -> None:
    """Score the system against the labeled query set."""
    typer.echo("eval lands with the evaluation phase", err=True)
    raise typer.Exit(code=1)
