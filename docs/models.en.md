# Local models: support and setup

[中文](models.md) · [Documentation](README.en.md)

Models are optional. Sampled instruments, MIDI, recording, arrangement, effects and exports work without neural weights.

The tool packs below are part of **dev15 development builds**. The published dev14 installer automatically prepares ACE-Step only.

| Capability | Backend | Setup | Guide |
| --- | --- | --- | --- |
| Text generation, reference variation, region repaint | ACE-Step 1.5 Turbo | **AI setup** on Windows Home, or a source setup script | [Generation](music-generation.en.md) · [Repaint](volume-and-repaint.md) |
| Vocal/backing separation | Mel-Band RoFormer KJ | Manual isolated environment | [Separation](separation.en.md) |
| Two/four-part separation | Demucs htdemucs | AI tools → Stems, melody & transcription | [Workflow](ai-production-workflow.md) |
| Monophonic MIDI | CREPE | Shared automatic tool pack with Demucs | [Workflow](ai-production-workflow.md) · [Evaluation](melody-next.en.md) |
| Transcription and text correction | Whisper small | Stems, melody & transcription pack; detailed text editing in the asset editor | [Editor models](next-models.en.md) |
| Transcription | Qwen3-ASR | Manual isolated environment | [Editor models](next-models.en.md) |
| Speech denoising | DPDFNet2, experimental GTCRN | AI tools → Clean speech recordings | [Speech cleanup](speech-cleanup.en.md) |

## Stems, melody, transcription and speech cleanup

Open **AI tools** from Home or the workstation model panel. Choose a pack and click **Download and install**. The app prepares private Python and dependencies, verifies checkpoints and runs inference on bundled samples offline before enabling the tools. No system Python, terminal or administrator account is needed.

- **Stems, melody & transcription**: CPU Torch 2.5.1, Demucs, CREPE and Whisper small; download estimate 1–2 GB, keep 6 GB free. Includes librosa tempo/key analysis and time/pitch processing, which are DSP.
- **Clean speech recordings**: sherpa-onnx, DPDFNet2 and GTCRN; download estimate 150–300 MB, keep 1 GB free. Intended for speech; processing complete music may damage instruments.
- Both packs run on Windows x64 CPU without a dedicated GPU. ACE-Step has separate GPU requirements. Automatic GPU acceleration setup is not included in these two packs yet.
- Pause/retry retains completed downloads. Closing the app stops its installation subprocesses. Files live under `%LOCALAPPDATA%\MusicWorkbench\AI\tools`, outside the application and projects.

After installation, click **Use in workstation**, import a recording, select an audio clip and run a tool from the model list. Audition results before adding tracks. CREPE notes can be added to an instrument track; **Details and editing** opens transcript corrections.

Use **Check environment** to find missing dependencies or corrupt weights, or **Repair setup** to prepare the pack again. Explicitly configured inference environments retain priority; existing models do not need moving.

[Installation and workstation validation](model-tools-validation.md).

## Automatic ACE-Step setup

Open **AI setup** on Home. Follow the hardware checks, environment preparation, model download and generation test. Return to the workstation, generate material, audition and adopt it.

- Windows x64, compatible NVIDIA driver and at least 8 GB VRAM.
- At least 35 GB free space; roughly 8–12 GB of initial downloads with internet access.
- Verified hardware: RTX 4070 Laptop 8 GB with 32 GB RAM. Other configurations can differ in compatibility and speed.
- Pause/retry reuses verified caches. Managed files default to `%LOCALAPPDATA%\MusicWorkbench\AI`.

## Manual setup and compatibility editor

RoFormer and Qwen3-ASR still need manual setup with a source checkout and Python. Follow the relevant guide and restart the workstation afterwards. Keep incompatible Torch dependencies in separate environments.

`next.html` is the retained single-asset editor for speech processing, transcription and detailed results. Its Next runtime instructions are not prerequisites for the installed app's basic features.

Beat This, Basic Pitch, Transkun, DiffSinger, CLAP and other research/evaluation candidates are not necessarily available from the workstation. See [model research and licenses](local-model-candidates.en.md).

Code and weights have separate license terms. Individual guides record revisions, hashes and measurements. A runtime check or completed download does not establish output quality; audition and review results.
