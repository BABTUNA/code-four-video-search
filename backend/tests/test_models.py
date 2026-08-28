import pytest
from pydantic import ValidationError

from app.models import ProcessingConfiguration


def test_rejects_overlap_equal_to_duration() -> None:
    with pytest.raises(ValidationError):
        ProcessingConfiguration(
            segment_duration_ms=30_000,
            segment_overlap_ms=30_000,
        )


def test_rejects_empty_modalities() -> None:
    with pytest.raises(ValidationError):
        ProcessingConfiguration(modalities=[])


def test_defaults_to_one_segment_as_a_cost_guard() -> None:
    configuration = ProcessingConfiguration()
    assert configuration.max_segments == 1


def test_rejects_segments_longer_than_one_minute() -> None:
    with pytest.raises(ValidationError):
        ProcessingConfiguration(segment_duration_ms=60_001)
