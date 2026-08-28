from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor

# AudioSet class names worth alarming on; a supervised head is more reliable
# than zero-shot prompts for exactly these (PANNs, arXiv 1912.10211).
ALARM_LABELS = {
    "Gunshot, gunfire": "gunshot",
    "Machine gun": "gunshot",
    "Siren": "siren",
    "Police car (siren)": "siren",
    "Ambulance (siren)": "siren",
    "Emergency vehicle": "siren",
    "Screaming": "screaming",
    "Shout": "shouting",
    "Yell": "shouting",
    "Glass": "glass",
    "Shatter": "glass",
    "Vehicle horn, car horn, honking": "vehicle horn",
    "Dog": "dog",
}


@register_extractor("audio_tags")
class AudioTagsExtractor:
    name = "audio_tags"

    def __init__(self, options: dict):
        self.window_s = options.get("window_s", 10.0)
        self.threshold = options.get("threshold", 0.2)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path, store=None) -> list[Doc]:
        import numpy as np
        import soundfile
        from panns_inference import AudioTagging, labels
        from scipy.signal import resample_poly

        waveform, rate = soundfile.read(assets.audio, dtype="float32")
        waveform = resample_poly(waveform, 32_000, rate)  # PANNs expects 32 kHz
        samples_per_window = int(self.window_s * 32_000)

        tagger = AudioTagging(checkpoint_path=None, device="cpu")
        wanted = {labels.index(name): tag for name, tag in ALARM_LABELS.items()
                  if name in labels}

        docs = []
        for start in range(0, len(waveform), samples_per_window):
            chunk = waveform[start:start + samples_per_window]
            if len(chunk) < 32_000:
                continue
            clipwise, _ = tagger.inference(chunk[None, :])
            scores = clipwise[0]
            found = {}
            for index, tag in wanted.items():
                if scores[index] >= self.threshold:
                    found[tag] = max(found.get(tag, 0.0), float(scores[index]))
            if not found:
                continue
            time = start / 32_000
            docs.append(Doc(
                video.video_id, time, time + self.window_s, "audio_tag",
                ", ".join(sorted(found)),
                {"scores": {tag: round(score, 3) for tag, score in found.items()}},
            ))
        return docs
