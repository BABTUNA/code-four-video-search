import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.extractors.transcribe import keep_segment


def segment(**overrides) -> dict:
    base = {
        "text": "put your hands behind your back",
        "no_speech_prob": 0.05,
        "avg_logprob": -0.3,
        "compression_ratio": 1.4,
    }
    return base | overrides


def test_keeps_ordinary_speech():
    assert keep_segment(segment())


def test_drops_non_speech_with_low_confidence():
    assert not keep_segment(segment(no_speech_prob=0.9, avg_logprob=-1.5))


def test_keeps_confident_text_even_when_no_speech_is_high():
    # The Whisper rule requires BOTH signals: high no-speech alone is not enough.
    assert keep_segment(segment(no_speech_prob=0.9, avg_logprob=-0.2))


def test_drops_repetition_loops():
    assert not keep_segment(segment(compression_ratio=3.1))


def test_drops_stock_hallucinations_regardless_of_punctuation():
    assert not keep_segment(segment(text=" Thanks for watching! "))


def test_drops_empty_text():
    assert not keep_segment(segment(text="   "))
