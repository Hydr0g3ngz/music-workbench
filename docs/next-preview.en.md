# Compatibility asset editor (Next)

[中文](next-preview.md) · [Documentation](README.en.md) · [Model setup](next-models.en.md)

Next is the retained single-asset editor for transcript correction, speech cleanup, waveform processing and experimental MCP/Codex tools. Use the [Music Workbench workstation](create-preview.en.md) for multitrack music; the two interfaces store different project records.

## Available tools

- Import, waveform selection, trim, gain, fades, balance, reverse and separate previews.
- Audition originals/candidates, explicitly adopt, undo/redo, reopen and export WAV.
- On-demand stems, Whisper/Qwen transcription, monophonic MIDI, beats and levels.
- Correct transcript lines as new versions and download TXT/LRC/SRT, retaining recognition.
- CPU speech cleanup, LUFS/true peak, static-gain normalization and synchronized matched A/B.

Cleanup can damage music or environmental sound. Audition before adoption. [Speech cleanup](speech-cleanup.en.md) · [Models and tasks](next-models.en.md)

## Launch from source

This advanced entry needs Python 3.11/3.12 and optional dependencies. It is not a prerequisite for basic creation in the installed app.

```sh
python -m pip install -e ".[ui,audio,agent]"
music-workbench ui --interface next --workspace outputs/asset-editor --port 8926 --open
```

Projects stay in the selected workspace. Use one writing service per workspace and close the older service before updating. Neural weights need [separate setup](next-models.en.md).

## Experimental MCP and Codex

The editor can connect an existing Codex CLI/login. Choose **Codex assistant → Connect local Codex**, and try “Lower this audio by 3 dB and create a preview.” Audition the tool result and choose whether to keep it.

Audio processing is local. Codex conversations, read transcripts and tool results use its service; audio is not implicitly attached. These tools cover single-asset editing/tasks, not full workstation track, note and effect control. The experimental app-server interface can vary by CLI version; the tested version is `0.162.0-alpha.17.2`.

External MCP clients can use this configuration after replacing absolute paths:

```toml
[mcp_servers.music_workbench_assets]
command = "/absolute/path/to/.venv/bin/python"
args = ["-m", "music_studio.studio.mcp", "--workspace", "/absolute/path/to/outputs/asset-editor"]
tool_timeout_sec = 180
```

On Windows use `.venv/Scripts/python.exe`. Sixteen tools cover selection, previews, adoption/history, model checks, queueing, artifacts, text corrections and A/B. Install weights first. Tools do not accept arbitrary shells, interpreters or download URLs. Conversations last for the service lifetime; editing state and candidates persist in the workspace.

## Limits and reference

Melody is monophonic estimation; review text/timing. Speech cleanup is not music restoration, and static LUFS processing does not establish broadcast compliance. Integer exports reject overloads. Long-audio streaming is not available.

[Speech methods](speech-cleanup.en.md) · [Melody evaluation](melody-next.en.md) · [Historical task checks](../benchmarks/results/next-capabilities-2026-10-16.json) · [Technical index](technical-reference.md)
