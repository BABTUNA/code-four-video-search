# Modality and Model Research

Research snapshot: **2026-08-27**. Model availability and pricing change quickly, so model slugs should remain configuration rather than application code.

## Current recommendation

| Layer | Initial model | Interface |
| --- | --- | --- |
| Visual | `google/gemini-3.7-flash` | OpenRouter video input |
| Audio/acoustics | `google/gemini-3.7-flash` | OpenRouter audio input |
| Transcript | `openai/gpt-4o-mini-transcribe` | OpenRouter transcription endpoint |
| OCR | `google/gemini-3.7-flash` | OpenRouter image input |
| Embeddings | `qwen/qwen3-embedding-8b` | OpenRouter embeddings endpoint |
| Query planning | `google/gemini-3.7-flash` | OpenRouter structured output |

This stack requires one API key and one gateway while keeping a separate processor interface for every modality. Sharing a provider does not mean coupling the processors: each model slug can be replaced independently in configuration.

## Shared evidence contract

Every processor analyzes the same fixed segment and returns segment-level evidence:

```json
{
  "segment_id": "video_1:25000-55000",
  "media_id": "video_1",
  "start_ms": 25000,
  "end_ms": 55000,
  "modality": "visual",
  "type": "scene_description",
  "content": "A uniformed officer stands beside a red vehicle.",
  "attributes": {},
  "confidence": null,
  "processor": {
    "model": "google/gemini-3.7-flash",
    "version": "1"
  }
}
```

The `content` field stays open-ended for semantic search. `type` and `attributes` provide optional classifications and filters. We do not invent confidence or signal measurements when a processor does not provide calibrated values.

## Decision criteria

Models are judged on:

1. Correctness on our labeled body-camera segments
2. Support for the required input modality
3. Reliable structured output
4. Setup and operational complexity
5. Cost and latency
6. Ease of replacement

Public benchmarks inform the shortlist, but a small project-specific comparison should determine the final choice.

## Documents

- [Visual models](visual.md)
- [Audio models](audio.md)
- [Transcription models](transcript.md)
- [OCR models](ocr.md)
- [Retrieval and query models](retrieval-and-query.md)

## OpenRouter references

- [OpenRouter multimodal overview](https://openrouter.ai/docs/guides/overview/multimodal/overview)
- [Video inputs](https://openrouter.ai/docs/guides/overview/multimodal/videos)
- [Audio inputs](https://openrouter.ai/docs/guides/overview/multimodal/audio)
- [Speech-to-text](https://openrouter.ai/docs/guides/overview/multimodal/stt)
- [Embeddings](https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings)

