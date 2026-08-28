from pathlib import Path

from c4search.media import MediaAssets, frame_time
from c4search.models import Doc, VideoMeta
from c4search.registry import register_extractor

# Fixed open-vocabulary prompt set for offline indexing. Detections are index
# signals, never trusted alone - night footage misses are expected.
VOCABULARY = [
    "person", "car", "truck", "police car", "bicycle", "motorcycle", "dog",
    "handgun", "rifle", "knife", "flashlight", "handcuffs", "bottle",
]


@register_extractor("detect")
class DetectExtractor:
    name = "detect"

    def __init__(self, options: dict):
        self.model_id = options.get("model", "yolov8s-worldv2.pt")
        self.vocabulary = options.get("vocabulary", VOCABULARY)
        self.confidence = options.get("confidence", 0.35)

    def run(self, video: VideoMeta, assets: MediaAssets, workdir: Path) -> list[Doc]:
        import torch
        from ultralytics import YOLO

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model = YOLO(self.model_id)
        model.set_classes(self.vocabulary)

        docs = []
        results = model.predict(
            source=str(assets.frames_dir), conf=self.confidence,
            device=device, verbose=False, stream=True,
        )
        for result in results:
            if len(result.boxes) == 0:
                continue
            detections = [
                {
                    "label": result.names[int(box.cls)],
                    "confidence": round(float(box.conf), 3),
                }
                for box in result.boxes
            ]
            time = frame_time(Path(result.path), assets.frame_fps)
            labels = sorted({d["label"] for d in detections})
            docs.append(Doc(
                video.video_id, time, time, "object",
                ", ".join(labels), {"detections": detections},
            ))
        return docs
