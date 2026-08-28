import os

from c4search.cache import StageCache, stage_key


def test_key_is_stable(tmp_path):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"fake video")
    assert stage_key(source, {"model": "a"}) == stage_key(source, {"model": "a"})


def test_key_changes_with_config_and_source(tmp_path):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"fake video")
    base = stage_key(source, {"model": "a"})

    assert stage_key(source, {"model": "b"}) != base

    os.utime(source, ns=(1, 1))
    assert stage_key(source, {"model": "a"}) != base


def test_done_marker(tmp_path):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"fake video")
    cache = StageCache(tmp_path / "cache")

    directory = cache.dir_for("transcribe", source, {})
    assert not cache.is_done(directory)
    cache.mark_done(directory)
    assert cache.is_done(directory)
