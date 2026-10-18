# Local models: support and setup

[中文](models.md) · [Documentation](README.en.md)

Models are optional. Sampled instruments, MIDI, recording, arrangement, effects and exports work without neural weights.

**dev21** offers seven isolated processing packs, plus separate ACE-Step setup. Models are optional downloads, outside the basic installer.

| Capability | Backend | Setup | Guide |
| --- | --- | --- | --- |
| Text generation, reference variation, region repaint | ACE-Step 1.5 Turbo | **AI setup** on Windows Home, or a source setup script | [Generation](music-generation.en.md) · [Repaint](volume-and-repaint.md) |
| Vocal/backing separation | Mel-Band RoFormer KJ | AI tools → Vocals & backing | [Setup and use](qwen-and-separation.en.md) · [Separation](separation.en.md) |
| Two/four-part separation | Demucs htdemucs | AI tools → Stems, melody & transcription | [Workflow](ai-production-workflow.md) |
| Monophonic MIDI | CREPE | Shared automatic tool pack with Demucs | [Workflow](ai-production-workflow.md) · [Evaluation](melody-next.en.md) |
| Piano polyphonic MIDI | Transkun 2.0.1 V2 FP32 | AI tools → Piano notes | [Use and limits](piano-notes.en.md) · [Piano comparison](piano-benchmark.md) |
| Single-instrument polyphonic MIDI | Basic Pitch 0.4.0 ONNX CPU | AI tools → Polyphonic notes | [Use and limits](polyphonic-notes.en.md) · [Parameter comparison](polyphony-benchmark.md) |
| Transcription and text correction | Whisper small | Stems, melody & transcription pack; detailed text editing in the asset editor | [Editor models](next-models.en.md) |
| Transcription and word timing | Qwen3-ASR-1.7B + ForcedAligner-0.6B | AI tools → Speech, lyrics & word timing | [Setup and use](qwen-and-separation.en.md) |
| Speech denoising | DPDFNet2, experimental GTCRN | AI tools → Clean speech recordings | [Speech cleanup](speech-cleanup.en.md) |

## Stems, melody, transcription and speech cleanup

Open **AI tools** from Home or the workstation model panel. Choose a pack and click **Download and install**. The app prepares private Python and dependencies, verifies checkpoints and runs inference on bundled samples offline before enabling the tools. No system Python, terminal or administrator account is needed.

- **Stems, melody & transcription**: CPU Torch 2.5.1, Demucs, CREPE and Whisper small; download estimate 1–2 GB, keep 6 GB free. Includes librosa tempo/key analysis and time/pitch processing, which are DSP.
- **Clean speech recordings**: sherpa-onnx, DPDFNet2 and GTCRN; download estimate 150–300 MB, keep 1 GB free. Intended for speech; processing complete music may damage instruments.
- **Polyphonic notes**: Basic Pitch ONNX in a private CPU environment; estimated download 150–350 MB, keep 2 GB free. Neither Torch nor TensorFlow is installed. Extracts overlapping chord notes for manual review.
- **NVIDIA acceleration pack**: private Torch 2.10 / CUDA 12.8 runtime; estimated download 3–5 GB, keep 10 GB free. Requires Turing or newer, at least 4 GB VRAM and driver 570 or newer. Setup tests real CUDA inference.
- **Vocals & backing · RoFormer**: private CUDA runtime; download estimate 4–6 GB, keep 12 GB disk space free. Requires Turing or newer NVIDIA GPU with at least 4 GB total VRAM.
- **Speech, lyrics & word timing · Qwen**: ASR and alignment load sequentially in BF16; download estimate 10–13 GB, keep 24 GB disk space free. Requires Ampere or newer NVIDIA GPU with at least 8 GB total VRAM; tasks also check for about 6 GB free VRAM. Alignment does not fix recognition errors. See the [guide](qwen-and-separation.en.md).
- Windows x64 CPU and CUDA packs can coexist; choose the device in the workstation. Explicit interpreter settings retain priority. Cleanup and DSP use CPU. ACE-Step has separate requirements.
- Pause/retry retains completed downloads. Closing the app stops its installation subprocesses. Files live under `%LOCALAPPDATA%\MusicWorkbench\AI\tools`, outside the application and projects.

After installation, click **Use in workstation**, import a recording, select an audio clip and run a tool from the model list. Audition results before adding tracks. CREPE notes can be added to an instrument track; **Details and editing** opens transcript corrections.

Use **Check environment** to find missing dependencies or corrupt weights, or **Repair setup** to prepare the pack again. Explicitly configured inference environments retain priority; existing models do not need moving.

[Hardware requirements and measured speed](model-hardware.en.md)

## Automatic ACE-Step setup

Open **AI setup** on Home. Follow the hardware checks, environment preparation, model download and generation test. Return to the workstation, generate material, audition and adopt it.

- Windows x64, NVIDIA Ampere or newer, at least 8 GB total VRAM and driver 570 or newer. Free VRAM selects INT8 offload, resident INT8 or BF16 before generation.
- At least 35 GB free space; roughly 8–12 GB of initial downloads with internet access.
- Verified hardware: RTX 4070 Laptop 8 GB with 32 GB RAM. Other configurations can differ in compatibility and speed.
- Pause/retry reuses verified caches. Managed files default to `%LOCALAPPDATA%\MusicWorkbench\AI`.

## Advanced setup and compatibility editor

Existing manual RoFormer/Qwen3-ASR environments remain supported, and explicit interpreter or separation configuration takes priority. Source setup scripts are available for customization. Keep incompatible Torch dependencies in separate environments.

`next.html` is the retained single-asset editor for speech processing, transcription and detailed results. Its Next runtime instructions are not prerequisites for the installed app's basic features.

Basic Pitch and Transkun are integrated into the workstation. Beat This, DiffSinger, CLAP and other research/evaluation candidates are not necessarily available. See [model research and licenses](local-model-candidates.en.md).

Code and weights have separate license terms. Individual guides record revisions, hashes and measurements. A runtime check or completed download does not establish output quality; audition and review results.
