# Music Workbench

[中文](README.md) · English

An open local music workstation: ideas → material → arrangement → mixing → export. Platform and local model integration come before deep Agent integration.

![Workstation](docs/images/create-effects-en.png)

## Two independent products

This repository develops the music workstation. The original song separation and lyrics/melody/chord analysis product remains at [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Releases, launchers and project directories are independent.

## Start

On Windows install Python 3.11/3.12 and run `Start-Music-Workbench.cmd`. Initial setup installs base dependencies; neural models are optional installations.

```sh
python -m pip install -e ".[ui,audio]"
music-workbench
```

Default port: 8920. Project directory: `outputs/workbench`. Existing projects are never automatically migrated or overwritten. This is a development preview, not a complete DAW.

New: **local recording → audition → adoption at the playhead**, with input devices, meter, WAV download and undo. [Usage and limits](docs/recording.en.md).

## Available

- Sample instruments, grooves, MIDI import, note editing and reversible multitrack arrangement.
- EQ, compression, reverb, mixing and WAV/MIDI export.
- Optional local ACE-Step generation, RoFormer/Demucs separation, transcription and pitch analysis.
- Isolated model runtimes, queued jobs, audition before adoption and preserved source audio.
- Chinese / English interface.

[Getting started](docs/create-preview.en.md) · [Models](docs/next-models.md) · [Generation](docs/music-generation.en.md) · [Separation evaluation](docs/separation.en.md) · [Roadmap](docs/workbench-roadmap.md)

MIT covers this project's code. Model weights and assets have separate licenses. Weights are not bundled.
