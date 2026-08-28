from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor

# Concrete, AudioSet-style event phrases; abstract labels degrade CLAP fast.
EVENTS = [
    "a person shouting",
    "a person screaming",
    "a police siren",
    "a gunshot",
    "glass breaking",
    "a dog barking",
    "a car engine revving",
    "a vehicle horn honking",
    "police radio chatter",
    "a person crying",
    "music playing",
]


@register_extractor("audio_events")
class AudioEventsExtractor:
    """CLAP embeddings over fixed windows: vectors for open-vocabulary audio
    search, plus text labels for events scoring above the threshold."""

    name = "audio_events"

    def __init__(self, options: dict):
        self.model_id = options.get("model", "laion/clap-htsat-unfused")
        self.window_s = options.get("window_s", 10.0)
        self.threshold = options.get("threshold", 0.35)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path, store=None) -> list[Doc]:
        import numpy as np
        import soundfile
        import torch
        from scipy.signal import resample_poly
        from transformers import ClapModel, ClapProcessor

        waveform, rate = soundfile.read(assets.audio, dtype="float32")
        waveform = resample_poly(waveform, 48_000, rate)  # CLAP expects 48 kHz
        samples_per_window = int(self.window_s * 48_000)

        model = ClapModel.from_pretrained(self.model_id).eval()
        processor = ClapProcessor.from_pretrained(self.model_id)

        def as_tensor(features):
            # Some transformers versions return a ModelOutput here, not a tensor.
            return features if torch.is_tensor(features) else features.pooler_output

        with torch.no_grad():
            text_inputs = processor(text=EVENTS, return_tensors="pt", padding=True)
            text_vectors = torch.nn.functional.normalize(
                as_tensor(model.get_text_features(**text_inputs)), dim=-1).numpy()

            windows, times = [], []
            for start in range(0, len(waveform), samples_per_window):
                chunk = waveform[start:start + samples_per_window]
                if len(chunk) < 48_000:  # skip trailing sub-second remainder
                    continue
                inputs = processor(
                    audio=chunk, sampling_rate=48_000, return_tensors="pt")
                features = as_tensor(model.get_audio_features(**inputs))
                windows.append(torch.nn.functional.normalize(features, dim=-1).numpy()[0])
                times.append(start / 48_000)

        vectors = np.array(windows, dtype=np.float32)
        np.save(workdir / "vectors.npy", vectors)

        similarity = vectors @ text_vectors.T
        docs = []
        for time, row in zip(times, similarity):
            above = [EVENTS[i] for i in np.where(row >= self.threshold)[0]]
            docs.append(Doc(
                video.video_id, time, time + self.window_s, "audio_window",
                ", ".join(above),
                {"top_event": EVENTS[int(row.argmax())],
                 "top_score": round(float(row.max()), 3)},
            ))
        return docs
