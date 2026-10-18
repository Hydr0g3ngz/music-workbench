# Music Workbench

[中文](README.md) · English

An open-source music workstation that runs locally. Create with sampled instruments, MIDI, multitrack arrangement, recording and mixing, and bring material from local AI generation, separation and transcription into your project.

[**Download Windows installer**](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/Music-Workbench-0.2.0.dev21-Setup-x64.exe) · [Beginner lesson](docs/first-sketch.md) · [Documentation](docs/README.en.md)

Windows 10 22H2 / 11 x64 · English / 中文 · Development preview; unsigned installer

**dev21 development preview** connects AI piano drafts, editable notes, grouped arrangement, bus mixing and portable projects. New: [Transkun piano transcription](docs/piano-notes.en.md), [note-part simplification and batch fades](docs/note-editing.en.md), plus task-button, save and selection fixes. [Release notes](docs/releases/v0.2.0.dev21.md) · [After the Rain creation case](docs/creations/after-the-rain.md).

![Listen, edit notes, mix and export](docs/images/first-sketch-demo.gif)

## Start making music

1. Download and install, then open **Music Workbench** from the desktop or Start menu. The basic runtime is included; no Python installation is needed.
2. Choose **Make your first musical sketch** on Home to create a separate eight-bar example.
3. Follow five in-app steps: listen to the layers, change a note, balance the mix and export WAV.
4. Export `.mwb` to keep the editable project and its audio, ready to restore and continue later.

Allow 5–10 minutes. No account, AI models or dedicated GPU are required. Resume from **Learn** in the header; a full offline handbook is included.

[Installation and upgrades](docs/windows-install.md) · [Lesson steps](docs/first-sketch.md) · [Optional example projects](docs/examples.md)


## What you can do

| Task | Available tools | Guide |
| --- | --- | --- |
| Write music from scratch | Sampled piano, marimba, drums and synth sounds; eight grooves; MIDI import, note dragging, selection, quantization and velocity | [Instruments and MIDI](docs/creation-library.en.md) |
| Build an arrangement | Multitrack clips, group copies, sections, range copying, bar positioning, loops, metronome and undo/redo | [Workstation](docs/create-preview.en.md) · [Loops](docs/timing.en.md) |
| Record a sound | Input selection, meter, recording and audition before adding a take at the playhead | [Recording](docs/recording.en.md) |
| Refine a mix | Level/pan, buses/sends, EQ, compression, reverb, volume curves and batch fades | [Mixing](docs/mixing.en.md) · [Volume and transitions](docs/volume-and-repaint.md) |
| Make material with AI | ACE-Step drafts/variations/repaint; RoFormer/Demucs stems; Basic Pitch polyphony, Transkun piano and CREPE monophonic MIDI | [Models and setup](docs/models.en.md) |
| Fit material together | Tempo/key estimates, beat anchors, independent time/pitch edits and loudness-matched candidate A/B | [Material fitting](docs/material-fitting.md) |
| Save and share | WAV, MIDI, source credits and portable `.mwb` projects containing audio | [Projects and export](docs/create-preview.en.md#save-and-export) |

## Local AI is optional

**AI setup** on Home installs an isolated ACE-Step environment and downloads verified models. This profile needs a compatible **NVIDIA GPU with at least 8 GB VRAM and 35 GB free disk space**. Initial downloads are roughly 8–12 GB. Basic creation works offline without models.

AI tools also offers seven isolated processing packs, downloaded on demand and checked with real offline inference. Audition candidates before adopting them; adoption supports undo. Runtime, memory and results depend on hardware, inputs and settings. [Supported models and requirements](docs/models.en.md) · [AI production workflow](docs/ai-production-workflow.md)

## Preview scope

The current version supports fixed 4/4 time, up to 32 tracks, eight buses and ten-minute projects. VST, effect-parameter automation, synchronized overdubbing, latency compensation and full workstation Agent control are not available yet. There is no automatic updater; save your work and close the app before updating. [dev21 release notes and checksums](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev21)

## Run from source and contribute

Python 3.11 / 3.12:

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[workstation]"
music-workbench
```

Source projects default to `outputs/workbench`; the service chooses an available port starting at 8920. Installed Windows projects live in `%LOCALAPPDATA%\MusicWorkbench\Projects`. Transfer projects between workspaces using `.mwb`.

[Contributing](CONTRIBUTING.md) · [Roadmap](docs/workbench-roadmap.md) · [Report a problem](https://github.com/Hydr0g3ngz/music-workbench/issues) · [Changelog](CHANGELOG.md)

For full-song lyrics, melody, chord and beat analysis, see the independent [Music Studio](https://github.com/Hydr0g3ngz/music-studio) project.

## License

Application code is [MIT](LICENSE). Model weights, instruments and assets have separate source licenses; weights are downloaded separately. Export source credits with your project. See [third-party notices](THIRD_PARTY_NOTICES.md).
