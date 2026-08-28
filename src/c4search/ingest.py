import json
from dataclasses import asdict
from pathlib import Path

from c4search.cache import StageCache
from c4search.extractors.diarize import speaker_for
from c4search.media import MediaAssets, prepare, probe
from c4search.models import Doc
from c4search.registry import build_extractors
from c4search.store import Store


def annotate_speakers(store: Store, video_id: str) -> None:
    """Copy speaker id and role onto each transcript Doc by turn overlap."""
    turns = [
        {"start": doc.t_start, "end": doc.t_end, **doc.extra}
        for _, doc in store.docs(video_id, "speaker_turn")
    ]
    if not turns:
        return
    for doc_id, doc in store.docs(video_id, "transcript"):
        turn = speaker_for(doc.t_start, doc.t_end, turns)
        if turn:
            store.update_extra(doc_id, doc.extra | {
                "speaker": turn["speaker"], "role": turn["role"],
            })


def load_assets(workdir: Path, frame_fps: float) -> MediaAssets:
    """Rebuild the asset paths for a media dir that prepare() already filled."""
    return MediaAssets(
        proxy=workdir / "proxy.mp4",
        audio=workdir / "audio.wav",
        frames_dir=workdir / "frames",
        frame_fps=frame_fps,
        loudness=workdir / "loudness.json",
    )


def ingest_video(source: Path, config: dict) -> dict[str, int]:
    """Prepare media, run each configured extractor (cached), index the Docs."""
    data_dir = Path(config.get("data_dir", "data"))
    cache = StageCache(data_dir / "cache")
    store = Store(data_dir / "index")

    video = probe(source)
    media_config = config.get("media", {})
    frame_fps = media_config.get("frame_fps", 0.5)
    media_dir = cache.dir_for("media", source, media_config)
    if cache.is_done(media_dir):
        assets = load_assets(media_dir, frame_fps)
    else:
        assets = prepare(
            source, media_dir,
            frame_fps=frame_fps,
            proxy_height=media_config.get("proxy_height", 480),
        )
        cache.mark_done(media_dir)

    counts = {}
    entries = config.get("extractors", [])
    for entry, extractor in zip(entries, build_extractors(config)):
        stage_dir = cache.dir_for(extractor.name, source, entry)
        docs_file = stage_dir / "docs.json"
        if cache.is_done(stage_dir):
            docs = [Doc(**fields) for fields in json.loads(docs_file.read_text())]
        else:
            docs = extractor.run(video, assets, stage_dir)
            docs_file.write_text(json.dumps([asdict(doc) for doc in docs]))
            cache.mark_done(stage_dir)

        for modality in {doc.modality for doc in docs}:
            store.delete_docs(video.video_id, modality)
        store.add_docs(docs)
        counts[extractor.name] = len(docs)

    annotate_speakers(store, video.video_id)
    return counts
