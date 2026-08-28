# Audio Modality

## Goal

Describe acoustic properties that a transcript misses: speech style, vocal intensity, and environmental sounds.

Suggested evidence classifications:

- `speech_style`: calm, loud, raised voice, whispering
- `interaction_tone`: argument, distressed speech, neutral conversation
- `background_sound`: traffic, siren, radio, crowd, silence
- `sound_event`: impact, glass breaking, alarm, vehicle sound

The audio processor should not duplicate the transcript processor. Spoken words belong in transcript evidence; how the speech sounds belongs here.

## Initial choice: Gemini 3.7 Flash

`google/gemini-3.7-flash` accepts audio and can produce a structured description from a fixed label set plus an open-ended caption. The current processor should leave fields such as `volume_change_db`, `pitch_increase`, and `confidence` as `null` unless a later signal-processing or calibrated classification component computes them.

References: [Gemini audio understanding](https://ai.google.dev/gemini-api/docs/audio), [OpenRouter audio inputs](https://openrouter.ai/docs/guides/overview/multimodal/audio), [OpenRouter model page](https://openrouter.ai/google/gemini-3.7-flash).

## Alternatives

| Classification | Model | Strengths | Why not the initial default |
| --- | --- | --- | --- |
| Open-weight omni model | Qwen3-Omni | Audio, video, text, and a dedicated detailed audio-captioning model | Heavy local/vLLM deployment for a take-home |
| Open-weight audio-language model | Qwen2-Audio | Instruction-based audio analysis and speech-emotion evaluation | Older model and still requires local serving |
| Contrastive audio-text encoder | CLAP | Direct text-to-audio similarity and zero-shot sound classification | Does not generate the evidence descriptions we want |
| Signal processing | RMS/pitch/prosody features | Transparent measurable features | Thresholds are sensitive to body-camera gain, distance, and background noise |

References: [Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni), [Qwen2-Audio](https://github.com/QwenLM/Qwen2-Audio), [CLAP paper](https://arxiv.org/abs/2206.04769).

## Decision

Use an audio-language model to create segment-level acoustic labels and descriptions. Treat numerical acoustic features as reserved optional fields, not fabricated model outputs. Consider CLAP only as a later alternative retrieval experiment.

