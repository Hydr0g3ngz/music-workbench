# Compatibility asset editor: models and tasks

> Advanced source/runtime setup for the retained Next single-asset editor and shared inference environment. See [current model support](models.en.md) for workstation installation paths.

[中文](next-models.md) · [Preview guide](next-preview.en.md) · [Future candidates (not integrated)](local-model-candidates.en.md)

Run the capability you need without starting the entire song-analysis pipeline.
Open **Local models** for sources, licenses, runtime checks and weight-cache status.
Choose a capability below the timeline and select **Queue task**. The UI, MCP and
Codex share the same queue, input snapshots, assets and events.

| Capability | Implementation | Outputs | Runtime |
| --- | --- | --- | --- |
| Levels | NumPy / SoundFile | Peak, RMS and full-scale sample JSON | Base install, no model |
| Loudness and true peak | pyebur128 / libebur128 | LUFS, dBTP and LRA JSON | Base Next runtime; CPU, no weights |
| Speech cleanup | [DPDFNet2 48 kHz](https://github.com/ceva-ip/DPDFNet) / Sherpa-ONNX | Enhanced WAV, input snapshot, measurements | Base Next runtime; CPU; separate Apache-2.0 weights |
| Lightweight denoising (experimental) | [GTCRN](https://github.com/Xiaobin-Rong/gtcrn) / Sherpa-ONNX | Enhanced WAV, input snapshot, measurements | Base Next runtime; CPU; separate MIT weights |
| Vocals and backing | [Demucs htdemucs](https://github.com/facebookresearch/demucs) | Two aligned WAV stems | Next model environment; MIT |
| Speech and lyrics | [faster-whisper small](https://huggingface.co/Systran/faster-whisper-small) | Editable transcript, TXT / LRC / SRT | Next model environment; MIT |
| Qwen speech and lyrics | [Qwen3-ASR-1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) | Editable transcript, TXT / LRC / SRT | Isolated lyrics environment; Apache-2.0 |
| Monophonic melody | [torchcrepe](https://github.com/maxrmorrison/torchcrepe) | MIDI, note JSON, estimated-note synthesis WAV | Next model environment; MIT |
| Beats and tempo | [librosa](https://github.com/librosa/librosa) | Beat JSON / CSV | Next model environment; ISC |

Checks import the relevant libraries in a child process and catch native loading
failures. Package presence alone never means ready. Passing runtime imports and
having cached weight files are separate signals; neither guarantees weight loading
or transcription quality. A task loads its model and retains any failure diagnostics.

## Windows setup

Speech cleanup does not need the Torch environment below. Open **Clearer speech** or
**Local models** and explicitly install pinned DPDFNet (about 10.11 MiB) or GTCRN
(about 0.51 MiB) weights. The launcher updates its own Next environment if the new CPU
runtime is missing. CLI setup is also available:

```powershell
.\scripts\setup-next-cleanup.ps1 -Model dpdfnet2-48k
```

These models can damage music or ambience; GTCRN also limits bandwidth. See the
[evaluation and regressions](speech-cleanup.en.md). Ten capability entries include
non-neural algorithms and two melody decoders, not ten different neural networks.

`Start-Music-Studio-Next.cmd` installs the separate `.venv-next` on first start.
Editing, playback, undo and WAV export need no neural model. For inference, run:

```powershell
# NVIDIA GPU with a CUDA 12.1 compatible driver. Creates .venv-next-models.
powershell -ExecutionPolicy Bypass -File .\scripts\setup-next-models.ps1 -Device cuda
# Use -Device cpu for CPU, or -SkipDownload to install packages only.
.\Start-Music-Studio-Next.cmd
```

The script uses the official PyTorch index, PyPI and official weight sources. It
does not alter the classic `.venv`. Demucs and Whisper weights use `.cache/models`;
CREPE weights ship in its upstream package. The launcher finds the new environment.
To reuse an installed runtime and cache explicitly:

```powershell
.\scripts\launch-next.ps1 -InferencePython 'D:\envs\audio\Scripts\python.exe' -ModelDir 'D:\models\music-studio'
```

Subsequent launches reuse this workspace's saved model runtime, lyrics runtime and cache paths.
Explicit launch arguments take precedence. Auto device selection respects the configured
server device; explicitly choosing CPU or CUDA overrides it for that task.

Qwen is optional. After installing the Next model environment:

```powershell
.\scripts\setup_lyrics.ps1 -Python .\.venv-next-models\Scripts\python.exe -Models qwen
.\Start-Music-Studio-Next.cmd
```

The launcher finds this checkout's `.artifacts/lyrics-env`, or accepts
`-LyricsPython ...`. All UI tasks force offline execution. Missing packages or
weights produce an error without silently installing or downloading. Setup needs
network access. Release packages do not redistribute model weights.

## Queue, assets and text corrections

- One on-demand Next task runs at a time **per workspace**, including separate UI and MCP
  processes. Each task uses an isolated process and releases its GPU models on exit.
  Other workspaces and applications can still compete for memory.
  Classic full-song analysis retains its own pipeline; avoid overlapping GPU work there too.
- A task captures the **entire auditioned track**, its hash and edit revision. To
  analyze a selection, render a trimmed preview and select it first. Completion
  never adopts an output, changes the auditioned track or resets playback time.
- Model tasks currently accept up to 600 seconds per clip; levels and loudness accept 7200
  seconds. The queue allows 20 pending tasks. Trim long recordings first. Streaming,
  memory budgets and batch slicing remain future work.
- Stems and note synthesis can be auditioned, edited and exported separately. MIDI,
  beats and structured outputs can be downloaded. Synthesis helps compare estimated
  notes; a different instrument is not an accuracy improvement.
- Correct transcript lines and save a new version without overwriting recognition.
  Changed lines retain line timing and clear previous word timings. Corrections do
  not pretend to rerun alignment. New TXT / LRC / SRT files accompany the version.
- Cancel queued or running tasks. On Windows, cancellation stops the owned process
  tree. Pending tasks must finish or be cancelled before trashing their project.
  Queued tasks resume after restart; tasks whose execution owner was lost are marked
  interrupted. Completed assets and edit versions persist.

## Agent tools and scope

The original eight editing tools remain. Eight additions bring the shared catalog
to 16: `audio_list_models`, `audio_check_model`, `audio_run_task`, `audio_get_tasks`,
`audio_cancel_task`, `audio_read_artifact`, `audio_correct_transcript`, and
`audio_prepare_comparison`. Comparison prepares the UI without autoplay or adoption.
Ask Codex to separate vocals and read the transcription, for example. Arguments use
fixed model and project-asset IDs, never shell code, Python paths or download URLs.
Structured results can enter the conversation; audio bytes are never uploaded implicitly.

MCP reads the workspace's `.studio-runtime.json` by default, or accepts
`--inference-python`, `--lyrics-python` and `--model-dir`. Keep this configuration local.

Melody remains a monophonic estimate. Both rest-preserving and legacy decoding are
available; see the [evaluation](melody-next.en.md). Speech denoising is available;
text-conditioned separation and automatic model routing remain planned. Music generation is available in the multitrack workstation; see [supported models](models.en.md).
