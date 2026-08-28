"""Contract tests: every registered extractor must satisfy these.

As real extractors land, each registers a lightweight test double or a
fast-path configuration here so the whole registry stays covered.
"""

from pathlib import Path

import pytest

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import EXTRACTORS, build_extractors, register_extractor

VIDEO = VideoMeta(video_id="video_1", path="video_1.mp4", duration_s=60.0,
                  width=640, height=480)

# Extractors that load real models; their logic is unit-tested in their own
# test modules and their end-to-end behavior verified on real footage.
HEAVY = {"transcribe"}


@register_extractor("fake")
class FakeExtractor:
    name = "fake"

    def __init__(self, options: dict):
        self.options = options

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        return [Doc(video.video_id, 0.0, 2.0, "fake", "hello")]


def validate_docs(docs: list[Doc], video: VideoMeta) -> None:
    assert docs, "extractor produced no docs"
    for doc in docs:
        assert doc.video_id == video.video_id
        assert 0 <= doc.t_start <= doc.t_end <= video.duration_s
        assert doc.modality
        assert isinstance(doc.text, str)


@pytest.mark.parametrize("name", sorted(set(EXTRACTORS) - HEAVY))
def test_extractor_contract(name, tmp_path):
    extractor = EXTRACTORS[name]({})
    assert extractor.name == name
    validate_docs(extractor.run(VIDEO, None, tmp_path), VIDEO)


@pytest.mark.parametrize("name", sorted(HEAVY))
def test_heavy_extractors_construct(name):
    extractor = EXTRACTORS[name]({})
    assert extractor.name == name


def test_build_extractors_uses_config_order_and_options():
    config = {"extractors": [{"impl": "fake", "detail": "high"}]}
    built = build_extractors(config)
    assert [extractor.name for extractor in built] == ["fake"]
    assert built[0].options == {"detail": "high"}


def test_doc_rejects_invalid_span():
    with pytest.raises(ValueError):
        Doc("video_1", 5.0, 1.0, "fake", "backwards")
