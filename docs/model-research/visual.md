# Visual Modality

## Goal

Describe the people, objects, environment, and actions visible in each shared video segment.

Suggested evidence classifications:

- `scene_description`
- `person_or_role`
- `object`
- `vehicle`
- `human_action`
- `time_of_day`

These classifications aid filtering; the open-ended `content` description remains the primary input to semantic search.

## Initial choice: Gemini 3.7 Flash

`google/gemini-3.7-flash` accepts video input, returns text, and supports JSON-schema structured output. It can describe video events and reason over actions rather than treating the segment as unrelated frames. It is available through OpenRouter, so local segments can be submitted as compressed base64 MP4 files.

References: [Google model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash), [Gemini video understanding](https://ai.google.dev/gemini-api/docs/video-understanding), [OpenRouter model page](https://openrouter.ai/google/gemini-3.7-flash).

## Alternatives

| Classification | Model | Strengths | Why not the initial default |
| --- | --- | --- | --- |
| Hosted video-language model | `qwen/qwen3.8-flash` | Video input, structured output, low cost, long-video focus | Extremely new and currently less operationally proven; no audio input |
| Open-weight video-language model | Qwen3-VL | Strong video dynamics, OCR, and timestamp-aware modeling | Local deployment introduces PyTorch/video-decoding/GPU setup |
| Video foundation model | InternVideo | Designed for video retrieval, actions, and temporal understanding | More research and deployment work than the take-home warrants |
| Fixed-label video classifier | VideoMAE | Useful when fine-tuned for a known action taxonomy | Closed-label classification does not naturally support open-ended queries |

References: [Qwen3.8 Flash](https://openrouter.ai/qwen/qwen3.8-flash), [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL), [InternVideo](https://github.com/OpenGVLab/InternVideo), [VideoMAE](https://huggingface.co/docs/transformers/model_doc/videomae).

## Decision

Use Gemini first because it gives strong open-vocabulary video understanding with minimal setup. Test Qwen3.8 Flash on the same labeled segments before claiming Gemini is superior. Do not select a newly released model solely because it is newest.

