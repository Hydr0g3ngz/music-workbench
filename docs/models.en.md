# Local models: support and setup

[中文](models.md) · [Documentation](README.en.md)

Models are optional. Sampled instruments, MIDI, recording, arrangement, effects and exports work without neural weights.

| Capability | Backend | Setup | Guide |
| --- | --- | --- | --- |
| Text generation, reference variation, region repaint | ACE-Step 1.5 Turbo | **AI setup** on Windows Home, or a source setup script | [Generation](music-generation.en.md) · [Repaint](volume-and-repaint.md) |
| Vocal/backing separation | Mel-Band RoFormer KJ | Manual isolated environment | [Separation](separation.en.md) |
| Two/four-part separation | Demucs htdemucs | Manual inference environment | [Runtime setup](next-models.en.md) · [Workflow](ai-production-workflow.md) |
| Monophonic MIDI | CREPE | Optional inference environment shared with Demucs | [Workflow](ai-production-workflow.md) · [Evaluation](melody-next.en.md) |
| Transcription and text correction | Whisper small, optional Qwen3-ASR | Compatibility asset editor; separate Qwen runtime | [Editor models](next-models.en.md) |
| Speech denoising | DPDFNet2, experimental GTCRN | Explicit weight download in the compatibility editor; CPU inference | [Speech cleanup](speech-cleanup.en.md) |

## Automatic ACE-Step setup

Open **AI setup** on Home. Follow the hardware checks, environment preparation, model download and generation test. Return to the workstation, generate material, audition and adopt it.

- Windows x64, compatible NVIDIA driver and at least 8 GB VRAM.
- At least 35 GB free space; roughly 8–12 GB of initial downloads with internet access.
- Verified hardware: RTX 4070 Laptop 8 GB with 32 GB RAM. Other configurations can differ in compatibility and speed.
- Pause/retry reuses verified caches. Managed files default to `%LOCALAPPDATA%\MusicWorkbench\AI`.

## Manual setup and compatibility editor

RoFormer, Demucs and CREPE do not all have automatic in-app environment installation yet. Their scripts need a source checkout and Python. Follow the relevant guide and restart the workstation afterwards. Keep incompatible Torch dependencies in separate environments.

`next.html` is the retained single-asset editor for speech processing, transcription and detailed results. Its Next runtime instructions are not prerequisites for the installed app's basic features.

Beat This, Basic Pitch, Transkun, DiffSinger, CLAP and other research/evaluation candidates are not necessarily available from the workstation. See [model research and licenses](local-model-candidates.en.md).

Code and weights have separate license terms. Individual guides record revisions, hashes and measurements. A runtime check or completed download does not establish output quality; audition and review results.
