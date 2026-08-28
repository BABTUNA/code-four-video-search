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
) -> None:
    """Search the indexed corpus with a natural-language query."""
    typer.echo("search lands with the retrieval phase", err=True)
    raise typer.Exit(code=1)


@app.command()
def eval(
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
) -> None:
    """Score the system against the labeled query set."""
    typer.echo("eval lands with the evaluation phase", err=True)
    raise typer.Exit(code=1)
