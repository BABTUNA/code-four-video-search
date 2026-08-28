import string
from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor

# Recurring strings Whisper emits over non-speech audio (music, wind, static);
# arXiv 2501.11378 shows these come from a small, enumerable set.
HALLUCINATION_BLOCKLIST = {
    "thank you",
    "thanks for watching",
    "thank you for watching",
    "please subscribe",
    "subscribe to my channel",
    "see you in the next video",
}

PUNCTUATION = str.maketrans("", "", string.punctuation)


def normalized(text: str) -> str:
    return text.lower().translate(PUNCTUATION).strip()


def keep_segment(
    segment: dict,
    no_speech_threshold: float = 0.6,
    logprob_threshold: float = -1.0,
    compression_ratio_threshold: float = 2.4,
) -> bool:
    """The Whisper paper's decode-failure rules (§4.5) plus the blocklist."""
    if (segment["no_speech_prob"] > no_speech_threshold
            and segment["avg_logprob"] < logprob_threshold):
        return False
    if segment["compression_ratio"] > compression_ratio_threshold:
        return False
    if normalized(segment["text"]) in HALLUCINATION_BLOCKLIST:
        return False
    return bool(segment["text"].strip())


@register_extractor("transcribe")
class TranscribeExtractor:
    name = "transcribe"

    def __init__(self, options: dict):
        self.model = options.get("model", "mlx-community/whisper-large-v3-turbo")

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        import mlx_whisper  # deferred so the test suite never loads the model

        result = mlx_whisper.transcribe(
            str(assets.audio),
            path_or_hf_repo=self.model,
            word_timestamps=True,
        )

        docs = []
        for segment in result["segments"]:
            if not keep_segment(segment):
                continue
            words = [
                [word["word"].strip(), round(word["start"], 2), round(word["end"], 2)]
                for word in segment.get("words", [])
            ]
            docs.append(Doc(
                video_id=video.video_id,
                t_start=round(segment["start"], 2),
                t_end=round(max(segment["end"], segment["start"]), 2),
                modality="transcript",
                text=segment["text"].strip(),
                extra={
                    "words": words,
                    "avg_logprob": round(segment["avg_logprob"], 3),
                    "no_speech_prob": round(segment["no_speech_prob"], 3),
                },
            ))
        return docs
