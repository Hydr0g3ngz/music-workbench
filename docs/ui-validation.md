# Local UI validation · 2026-10-15

> Historical reference for the Studio analysis workflow or a pre-split build. Start with [current Workbench documentation](README.en.md). The analysis product is maintained in [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Commands and measurements below apply to the stated historical version.

The local workbench was tested against actual saved model outputs and through a browser. It is a playback and inspection UI, with no lyric/note editing yet. These checks establish working integration, not transcription accuracy.

## Full song through the workbench

The browser loaded the licensed example and started analysis through the local API. All stages ran with cached models and `offline=true`:

```powershell
.\.venv\Scripts\python.exe -u -m music_studio ui --model-dir .cache/models --workspace outputs/ui --port 8765 --offline
```

Input: **Let's Go Fishin' — Karissa Hobbs**, CC BY 3.0. The UI downloads librosa's high-quality `fishin` recording on first use, keeps a local copy, and shows the artist/license. [Source attribution](https://librosa.org/data/audio/Karissa_Hobbs_-_Lets_Go_Fishin.txt), [original release](https://freemusicarchive.org/music/Karissa_Hobbs/Age_of_Flowers/09_Lets_Go_Fishin), [license](https://creativecommons.org/licenses/by/3.0/).

Hardware/runtime: Windows, Python 3.12.4, RTX 4070 Laptop GPU with 8GB VRAM; Demucs `htdemucs`, multilingual Whisper `small`, CREPE full, and librosa rhythm/harmony baselines. See [engine validation](validation.md) for model revisions and runtime versions. No GPU-memory sampling was performed for this full-song UI run.

| Result | Observed value |
| --- | --- |
| Source duration | 132.989 s |
| Analysis wall time | 107.31 s |
| Detected language | English |
| Lyric lines / word entries | 18 / 165 |
| Melody notes | 276 |
| Notes linked to at least one word | 205 |
| Chord intervals | 39 |
| Beat positions | 261 |
| Displayed global tempo estimate | 117 BPM |
| Output validation | Passed |

The validator checked aligned audio sample counts/rates/channels, annotation bounds, pitch time order, artifact hashes and MIDI note timing. These counts are not correctness scores. The song has not been manually annotated for lyric error rate, note F1, chord accuracy or beat accuracy. Word timestamps remain Whisper estimates and can cover gaps or merge sung phrases.

## Browser checks

- The completed project loaded real waveform envelopes, pitch, notes, chords, beats and all 18 lyric segments.
- Playback time advanced; original, vocal, instrumental and synthesized MIDI track controls changed the selected mode.
- Clicking a lyric sought to its timestamp, updated lyric highlighting, and enabled the single-line loop control. The browser UI exposes loop state; no sample-accurate loop-boundary measurement was made.
- The whole-song view adjusted the timeline range and disabled the unneeded view-position slider. The 30-second view showed detailed waveforms and notes.
- MIDI was downloaded through the export selector. Its SHA-256 matched the engine export, and Mido read 276 note-on events. MIDI duration ends at the final event, which need not equal the source audio duration.
- Narrow in-app browser layout showed the project selector and fixed playback controls. The lyrics list scrolls internally during following.
- Browser console checks reported no warning/error entries during these flows. A malformed MIDI option tag discovered during testing was repaired and the download was tested again successfully.

## Automated checks and packaging

15 tests passed: the existing 11 engine tests plus four UI tests. The UI tests use a deterministic analyzer to test audio upload, analysis lifecycle, restored history, real peak extraction, HTTP range playback, MIDI download, single-active-job handling, cancellation, invalid input, origin checks and asset path containment. They do not download or score neural models.

Ruff, JavaScript syntax and dependency consistency checks passed. The wheel was rebuilt and inspected to confirm that the server plus HTML/CSS/JavaScript assets are included. The Windows/Linux CI configuration now installs `.[ui,dev]`; remote CI has not been run in this local task.

## Current limits

The UI is a local single-user workbench. It decodes three full audio buffers into browser memory, so it is intended for individual songs. It provides playback, visual inspection, stop/resume and export. Lyric correction, note dragging, notation, multi-song concurrency and automatic accuracy assessment are future work.
