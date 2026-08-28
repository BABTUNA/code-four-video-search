# Transcript Modality

## Goal

Convert speech in each shared segment into searchable text. The stored timestamps remain the shared segment boundaries; word-level localization is outside the initial scope.

Suggested evidence classifications:

- `speech`
- `officer_command`
- `legal_procedure`
- `question_and_answer`
- `identity_or_identifier`

These categories may be assigned after transcription. The complete transcript remains available for semantic and keyword search.

## Initial choice: GPT-4o Mini Transcribe

`openai/gpt-4o-mini-transcribe` is available through OpenRouter's dedicated `/api/v1/audio/transcriptions` endpoint. It offers a simple hosted speech-to-text path without installing or serving Whisper locally.

References: [OpenRouter model page](https://openrouter.ai/openai/gpt-4o-mini-transcribe), [OpenRouter transcription API](https://openrouter.ai/docs/guides/overview/multimodal/stt).

## Alternatives

| Classification | Model | Strengths | Why it might replace the default |
| --- | --- | --- | --- |
| Compact hosted ASR | `qwen/qwen3-asr-0.6b` | Very low cost, multilingual, segment and word timestamps | Attractive candidate if body-camera accuracy is competitive |
| Larger hosted ASR | `qwen/qwen3-asr-1.7b` | More capacity with the same Qwen ASR family | Potential accuracy improvement at higher cost |
| Hosted ASR | `mistralai/voxtral-mini-transcribe` | Simple transcription API and per-minute pricing | Useful independent-provider comparison |
| Established ASR | `openai/whisper-1` | Widely understood baseline | Older than the current transcription models |
| Local ASR | Whisper/faster-whisper | No per-request data transfer and full local control | Adds model downloads, compute requirements, and platform-specific setup |

References: [Qwen3 ASR 0.6B](https://openrouter.ai/qwen/qwen3-asr-0.6b), [Voxtral Mini Transcribe](https://openrouter.ai/mistralai/voxtral-mini-transcribe), [Whisper on OpenRouter](https://openrouter.ai/openai/whisper-1/api).

## Decision

Start with GPT-4o Mini Transcribe, then compare it with Qwen3 ASR 0.6B on noisy and overlapping speech. Choose based on transcript correctness on our segments rather than general speech benchmarks.

