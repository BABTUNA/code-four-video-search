import json
from pathlib import Path

from c4search.media import MediaAssets
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor
from c4search.timeline import merge_runs

SPEECH_LUFS = -45.0  # windows quieter than this are skipped as non-speech


def speechy_windows(loudness: list[list[float]], window_s: float) -> list[float]:
    """Start times of windows whose momentary loudness suggests speech."""
    starts = []
    if not loudness:
        return starts
    end = loudness[-1][0]
    t = 0.0
    while t + window_s <= end:
        samples = [lufs for time, lufs in loudness if t <= time < t + window_s]
        if samples and max(samples) > SPEECH_LUFS:
            starts.append(t)
        t += window_s
    return starts


@register_extractor("arousal")
class ArousalExtractor:
    """Dimensional vocal arousal (wav2vec2, trained on naturalistic speech):
    a graded escalation signal - categorical emotion is not reliable enough."""

    name = "arousal"

    def __init__(self, options: dict):
        self.model_id = options.get(
            "model", "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
        self.window_s = options.get("window_s", 5.0)
        self.threshold = options.get("threshold", 0.6)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        import soundfile
        import torch
        from transformers import AutoConfig, Wav2Vec2Model, Wav2Vec2Processor

        waveform, rate = soundfile.read(assets.audio, dtype="float32")
        loudness = json.loads(assets.loudness.read_text())
        starts = speechy_windows(loudness, self.window_s)

        processor = Wav2Vec2Processor.from_pretrained(self.model_id)
        backbone = Wav2Vec2Model.from_pretrained(self.model_id).eval()
        head = load_regression_head(self.model_id, AutoConfig.from_pretrained(self.model_id))

        labels, times, scores = [], [], {}
        with torch.no_grad():
            for start in starts:
                chunk = waveform[int(start * rate):int((start + self.window_s) * rate)]
                inputs = processor(chunk, sampling_rate=rate, return_tensors="pt")
                hidden = backbone(inputs.input_values).last_hidden_state.mean(dim=1)
                arousal = float(head(hidden)[0][0])  # model outputs [arousal, dominance, valence]
                times.append(start)
                labels.append("raised" if arousal >= self.threshold else "")
                scores[start] = round(arousal, 3)

        docs = []
        for t_start, t_end, _ in merge_runs(labels, times, gap=self.window_s * 2):
            peak = max(scores[t] for t in scores if t_start <= t <= t_end)
            docs.append(Doc(
                video.video_id, t_start, t_end + self.window_s, "vocal_arousal",
                "raised voice, elevated vocal arousal", {"peak_arousal": peak},
            ))
        return docs


def load_regression_head(model_id: str, config):
    """The audeering checkpoint carries a small regression head on top of
    wav2vec2; transformers has no class for it, so build and load it here."""
    import torch
    from huggingface_hub import hf_hub_download

    head = torch.nn.Sequential(
        torch.nn.Linear(config.hidden_size, config.hidden_size),
        torch.nn.Tanh(),
        torch.nn.Linear(config.hidden_size, 3),
    )
    weights_file = hf_hub_download(model_id, "pytorch_model.bin")
    state = torch.load(weights_file, map_location="cpu", weights_only=True)
    head[0].weight.data = state["classifier.dense.weight"]
    head[0].bias.data = state["classifier.dense.bias"]
    head[2].weight.data = state["classifier.out_proj.weight"]
    head[2].bias.data = state["classifier.out_proj.bias"]
    return head.eval()
