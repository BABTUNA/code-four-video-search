"""Importing this package registers every extractor with the registry."""

from c4search.extractors import (  # noqa: F401
    arousal,
    audio_events,
    audio_tags,
    clock_ocr,
    detect,
    diarize,
    frames,
    motion,
    transcribe,
)
