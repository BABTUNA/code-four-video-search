# OCR Modality

## Goal

Extract visible text such as license plates, street signs, badges, vehicle markings, and documents from frames sampled within each shared segment.

Suggested evidence classifications:

- `license_plate`
- `street_sign`
- `badge_or_unit_number`
- `vehicle_marking`
- `document_text`
- `other_visible_text`

## Initial choice: Gemini 3.7 Flash

Extract several high-resolution frames from each segment and send them as image inputs to `google/gemini-3.7-flash` with a strict OCR schema. Using still frames preserves small text better than relying only on the video model's normal frame sampling. Require agreement across multiple frames before returning a high-confidence license plate.

References: [Google model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash), [OpenRouter multimodal inputs](https://openrouter.ai/docs/guides/overview/multimodal/overview).

## Alternatives

| Classification | Model | Strengths | Why not the initial default |
| --- | --- | --- | --- |
| Specialized OCR toolkit | PaddleOCR / PP-OCRv5 | Detection, recognition, bounding boxes, confidence scores, many languages | Adds local runtime and model dependencies |
| Document vision-language model | PaddleOCR-VL 1.6 | Strong modern document parsing and difficult text recognition | Optimized mainly for documents rather than moving license plates |
| General vision-language model | Qwen3-VL | Strong OCR under blur, tilt, and low light | Local serving is heavier than an OpenRouter call |
| Lightweight OCR toolkit | EasyOCR | Simple API, bounding boxes, and recognition confidence | Older release and PyTorch/model-download setup |

References: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL), [EasyOCR](https://github.com/JaidedAI/EasyOCR).

## Decision

Use Gemini on extracted still frames for the easiest initial setup. Keep OCR as a separate processor so PaddleOCR can replace it if license-plate accuracy is insufficient. Never accept a plate reading from a single uncertain frame without showing the supporting image.

