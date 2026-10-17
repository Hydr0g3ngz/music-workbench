# Workstation guide

[中文](create-preview.md) · [Documentation](README.en.md)

![Music workstation](images/create-workbench-en.png)

Open an example, create a project or import material from Home after installation. Start with the [five-step lesson](first-sketch.md), or see [source quick start](../QUICKSTART.md).

## Find your tools

| Area | Common actions |
| --- | --- |
| Transport | Play, pause, stop, seek, BPM, loop, metronome and recording; Space toggles playback |
| Assets and instruments | Import audio/MIDI; search, audition and add sounds, grooves or assets |
| Arrangement | Move, trim, split and duplicate audio/MIDI; snap, zoom, section markers and range copying |
| Lower dock | Mixer, effects and piano roll; drag, resize, select and batch-edit notes |
| Inspector | Name, placement, source offset, duration, gain, fades and instrument |
| AI models and tasks | Setup, queue, cancel and audition candidates; adoption changes the project explicitly |
| Project menu | New, reopen, rename, trash/restore, undo/redo and portable project recovery |

## Build a piece

1. Choose an instrument or import your own audio/MIDI. [Instruments and MIDI](creation-library.en.md)
2. Double-click a MIDI clip to edit notes. Loop a section and try a rhythmic or melodic change. [Loop and metronome](timing.en.md)
3. Extend the form with section markers and cross-track range copying. [Creative blueprint](arranging-methods.md)
4. Balance track levels, pan and effects. Shape joins with volume curves and fades. [Mixing](mixing.en.md) · [Transitions](volume-and-repaint.md)
5. Keep the editable project and export audio to audition elsewhere.

Clip edits retain source material. Track/clip removal supports undo; deleted projects can be restored from Trash. Completed tasks never automatically replace the arrangement or change the audition track.

## Save and export

Projects autosave with undo/redo history. If another window has edited the project, refresh to the current revision before continuing.

| Format | Purpose |
| --- | --- |
| WAV | 44.1 kHz, 24-bit stereo audio, including the mix and effect tails; play and share |
| MIDI | Instrument note data; excludes audio tracks/effects and does not transcribe the whole mix |
| Portable project `.mwb` | Arrangement, audio and source credits; use Projects → Restore portable project in another workspace |
| JSON snapshot | Local arrangement record referencing asset paths; copying it alone is not an MWB backup |

MWB excludes model weights, runtimes and the complete task database. Restore with the same app version to reduce sample/DSP differences. WAV/MIDI export the complete arrangement without metronome clicks or loop repetitions. With peak limiting off, overloaded exports request a lower master level.

## Add local AI

Generate a draft from an empty project, or select audio for stems, monophonic MIDI or fitting. Audition candidates before adding at the playhead or replacing an aligned clip. Adoption supports undo. [Models and setup](models.en.md) · [AI workflow](ai-production-workflow.md)

## Current limits

- Fixed 4/4 and 44.1 kHz stereo; up to 32 tracks and ten-minute projects. Maximum upload: 256 MiB; decoded/synthesized audition budget: 256 MiB.
- BPM changes affect MIDI and the grid. Audio needs a separate [beat-fit candidate](material-fitting.md) for time stretching.
- Built-in sampled/synth sounds and fixed-order effects; no general SFZ/SoundFont, VST or buses/sends yet.
- Clip volume curves vary over time. Live effect tweaks are not recorded as automation.
- Recording pauses arrangement playback; synchronized overdubbing, input monitoring and latency compensation are unavailable.
- Seek and pause/resume rebuild effects; loops preserve effect tails. Discontinuous source boundaries can click.
- Task input ranges differ: separation uses the complete source asset; reference generation/repaint use the ranges specified in their panels.

See the [roadmap](workbench-roadmap.md) for future work and [technical reference](technical-reference.md) for version-specific checks and evaluations.
