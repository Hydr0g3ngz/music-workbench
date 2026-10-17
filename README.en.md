# Music Workbench

[中文](README.md) · English

An open local music workstation. Turn an idea into a piece you can keep, with editable tracks, MIDI, mixing and optional local AI.

[**Download Windows installer**](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/Music-Workbench-0.2.0.dev14-Setup-x64.exe) · [Watch the 36-second demo (with audio)](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/Music-Workbench-First-Sketch-Demo.mp4) · [Beginner guide](docs/first-sketch.md) · [Release and checksums](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev14)

Windows 10 22H2 / 11 x64 · English / 中文 · Development preview, unsigned installer

![Real UI highlights: listen, edit notes, mix and export](docs/images/first-sketch-demo.gif)

## Make your first sketch

Install → choose **Make your first musical sketch** on Home → listen, explore layers, change a note, balance and export WAV. Five in-app steps locate controls and track actual operations. Close and resume, explicitly skip, or repeat without resetting the music. Allow 5–10 minutes; no model downloads are needed. Open **Learn** in the header to resume or read the full offline handbook inside the app.

[Guide and validation](docs/first-sketch.md) · [Editable MWB example](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/First-Sketch-Example.mwb) · [Demo storyboard and launch materials](docs/launch-kit.md)

The demo is an edit of real UI screenshots with the exported example as accompaniment. The basic example is not AI-generated. Platform and local models come before deep Agent integration.

## Two independent products

This repository develops the music workstation. The original song separation and lyrics/melody/chord analysis product remains at [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Releases, launchers and project directories are independent.

## Start

Windows installer preview (`Setup-x64.exe`): install, then open **Music Workbench** from the desktop or Start menu. It opens in its own desktop window, with a bundled basic runtime and no Python setup, commands or browser management. [Installation guide](docs/windows-install.md).

**AI setup** checks the computer, downloads an isolated environment and models, verifies files and performs a real generation before enabling ACE-Step. The first automatic profile supports Windows x64 with an NVIDIA 8 GB GPU; initial setup needs internet and 35 GB free space. Automatic environments for other models are still being integrated. Basic instruments, recording, editing, arrangement and mixing need no models.

Source users: configure Python 3.11/3.12 and the basic environment, then use `Start-Music-Workbench.cmd`, or:

```sh
python -m pip install -e ".[workstation]"
music-workbench
```

Source default: port 8920 and `outputs/workbench`. Portable projects: `%LOCALAPPDATA%\MusicWorkbench\Projects`. Launches reuse the same workspace service and choose an available port. Existing projects are never automatically migrated or overwritten. This is a development preview, not a complete DAW.

New: **local recording → audition → adoption at the playhead**, with input devices, meter, WAV download and undo. [Usage and limits](docs/recording.en.md).

**Refine a section**: custom loop bars, a selected-clip range shortcut, and a metronome with adjustable level and bar accents. Settings persist; exports contain the complete piece. [Loop and metronome](docs/timing.en.md).

**Tested by making a piece**: “Radio Through the Clouds,” 64 seconds, 32 bars, nine tracks. Local ACE-Step created the theme and reference variation; Demucs separated four parts; CREPE turned the bass into editable MIDI. Arrangement and mixing used UI operations, without an externally authored full score. Restoring its portable project in a fresh directory produced an identical WAV. [Journal and measurements](docs/creations/radio-through-the-clouds.md) · [AI across production stages](docs/ai-production-workflow.md). This demonstrates workflow integration, not listening quality.

The earlier “After the Last Tram” exposed editing gaps now addressed with note drag/resize, selection, group velocity/quantization, section copying, bar positioning, fit view, portable projects and output measurements. [Priorities](docs/workbench-roadmap.md) · [First piece MIDI source](examples/after-the-last-tram/compose.py).

## Available

- Editable volume curves, linear/equal-power crossfades and an AI region-repaint shortcut from transition editing. Audition before adoption; outside samples are preserved. [Usage and validation](docs/volume-and-repaint.md).
- Beat fitting with waveform anchors, half/double time and two-beat tempo calibration; loudness-matched A/B for generated/processed candidates. [Usage and regression](docs/material-fitting.md).
- Creative blueprint, section roles/energy/intentions and three editable structure sketches; AI generation uses pinned project context with an actual-prompt preview. [Methods and workflow](docs/arranging-methods.md).
- Sample instruments, grooves and MIDI import; note drag/resize, selection, copy, transpose, quantization and velocity edits.
- Section markers, multitrack section copying, bar positioning, key/scale hints and reversible arrangement.
- EQ, compression, reverb, mixing; WAV/MIDI, levels and optional LUFS/true peak, portable `.mwb` project restore.
- Optional local ACE-Step text/reference generation, RoFormer/Demucs, four-part separation and monophonic MIDI extraction.
- Estimated source tempo/key and independent time/pitch editing (DSP, originals retained).
- Isolated model runtimes, queued jobs, audition before adoption and preserved source audio.
- Chinese / English interface.

[Getting started](docs/create-preview.en.md) · [Models](docs/next-models.md) · [Generation](docs/music-generation.en.md) · [Separation evaluation](docs/separation.en.md) · [Roadmap](docs/workbench-roadmap.md)

MIT covers this project's code. Model weights and assets have separate licenses. Weights are not bundled.
