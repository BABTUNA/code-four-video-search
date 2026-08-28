from pathlib import Path

from c4search.media import MediaAssets, frame_time
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor
from c4search.timeline import merge_runs

# Zero-shot scene prompts, classified with the same SigLIP embeddings the
# frames are indexed with - the scene attributes cost no extra model.
SCENE_PROMPTS = {
    "outdoors at night": "a photo taken outdoors at night",
    "outdoors in daylight": "a photo taken outdoors during the day",
    "indoors": "a photo taken indoors",
}

# Mean 8-bit luma below this is night regardless of what the classifier says;
# headlights and streetlamps fool CLIP-family models more than a histogram.
NIGHT_LUMA = 40.0


def scene_label(prompt_label: str, luma: float) -> str:
    if luma < NIGHT_LUMA and "night" not in prompt_label:
        return "outdoors at night" if "outdoors" in prompt_label else prompt_label
    return prompt_label


@register_extractor("frames")
class FramesExtractor:
    name = "frames"

    def __init__(self, options: dict):
        self.model_id = options.get("model", "google/siglip2-base-patch16-256")
        self.batch_size = options.get("batch_size", 32)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path, store=None) -> list[Doc]:
        import numpy as np
        import torch
        from PIL import Image
        from transformers import AutoModel, AutoProcessor

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model = AutoModel.from_pretrained(self.model_id).to(device).eval()
        processor = AutoProcessor.from_pretrained(self.model_id)

        def as_tensor(features):
            # Some transformers versions return a ModelOutput here, not a tensor.
            return features if torch.is_tensor(features) else features.pooler_output

        frame_paths = sorted(assets.frames_dir.glob("*.jpg"))
        vectors, lumas = [], []
        with torch.no_grad():
            for start in range(0, len(frame_paths), self.batch_size):
                batch = frame_paths[start:start + self.batch_size]
                images = [Image.open(path).convert("RGB") for path in batch]
                lumas += [np.asarray(image.convert("L")).mean() for image in images]
                inputs = processor(images=images, return_tensors="pt").to(device)
                features = as_tensor(model.get_image_features(**inputs))
                vectors.append(torch.nn.functional.normalize(features, dim=-1).cpu())

            image_vectors = torch.cat(vectors).numpy()

            text_inputs = processor(
                text=list(SCENE_PROMPTS.values()), padding="max_length",
                return_tensors="pt",
            ).to(device)
            text_features = as_tensor(model.get_text_features(**text_inputs))
            text_vectors = torch.nn.functional.normalize(text_features, dim=-1).cpu().numpy()

        np.save(workdir / "vectors.npy", image_vectors.astype(np.float32))

        # Frame docs first: ingest aligns vectors.npy with the first N docs.
        times = [frame_time(path, assets.frame_fps) for path in frame_paths]
        docs = [
            Doc(video.video_id, t, t, "frame", "", {"frame": path.name})
            for t, path in zip(times, frame_paths)
        ]

        prompt_names = list(SCENE_PROMPTS)
        similarity = image_vectors @ text_vectors.T
        labels = [
            scene_label(prompt_names[row.argmax()], luma)
            for row, luma in zip(similarity, lumas)
        ]
        gap = 2.0 / assets.frame_fps
        for t_start, t_end, label in merge_runs(labels, times, gap):
            docs.append(Doc(video.video_id, t_start, t_end, "scene", label))
        return docs
