# Music Workbench platform design

[中文](workbench-plan.md) · [Roadmap](workbench-roadmap.md) · [Model research](local-model-candidates.en.md)

This document is for platform and backend contributors. Consult the [user guide](create-preview.en.md) for supported behavior and limits. Planned capabilities are not implementation claims.

Workbench and Studio maintain creation and full-song analysis separately. See [product boundaries](product-boundaries.md) for public entries, data locations and format compatibility. Integrations should supply material that users can continue editing, arranging and mixing.

## Product and engineering goals

Create, arrange, record, edit, mix and export locally. Templates, presets, lessons and reversible edits help beginners; advanced parameters remain available as needed. AI outputs become editable project material. Future Agent control reuses project commands; basic creation does not require conversation.

| Area | Existing foundation | Extension |
| --- | --- | --- |
| Arrangement | Audio/MIDI tracks, source ranges and positions, split/copy, groups, loops and sections | Local timing correction, longer projects |
| Instruments and MIDI | Samples/synths, grooves, import, piano roll and batch edits | More samples, controller events, third-party instruments |
| Recording | Mono capture, device/meter and audition before adoption | Overdub, monitoring, count-in and latency compensation |
| Mixing | Levels/pan, fixed EQ/compressor/reverb, volume curves, crossfades, buses and sends | Effect automation and plugin hosting |
| AI material | ACE-Step, stems, monophonic/polyphonic MIDI, source/task records | Broader multi-instrument transcription, singing, timbre, effects, retrieval and restoration |
| Delivery | WAV/MIDI, credits and portable MWB projects | Portable task recipes, dependency diagnostics and batch delivery |
| Onboarding | Windows installer/window, ACE-Step setup and bilingual lesson | Broader hardware coverage and observed usability trials |

## Project representation and integrity

Projects contain tracks and clips. Audio assets are independent; clips reference source ranges and timeline positions, while MIDI stores notes. Convert explicitly between seconds, beats, bars, samples and MIDI ticks. The current grid is fixed 4/4; tempo maps and changing signatures remain future work.

SQLite stores revisions, asset references, tasks and history; large files remain on disk. Saves/adoption check optimistic revisions, sources stay immutable and failures retain recoverable state. MWB packs the current arrangement, media and credits, excluding weights, environments and the full task database. Incompatible changes need migration, history compatibility and roundtrip checks.

## Playback, rendering and processes

One Web Audio transport schedules audition. Task polling and redraws must preserve active sources. AudioWorklet runs realtime processors; Python DSP renders offline with the same semantics. Compare order, tails, sample rates and clip edges. Record state-rebuild differences after seeking versus uninterrupted playback.

Separate control, audio and model workers so inference cannot block playback. Models use isolated runtimes and cancellable subprocesses. Low-latency recording, device drivers and plugin hosting need separate validation; browser playback does not establish native-device performance.

## Backend contract

| Part | Required information |
| --- | --- |
| Description | Stable provider ID, capabilities, bilingual parameters, version, maintenance and separate code/weight/voice licenses |
| Inputs | Capability-specific text, audio, MIDI, lyrics, regions and musical conditions; explicit source/project time |
| Execution | Pinned dependencies, isolation, device/precision/offload, estimated/measured resources, progress and cancellation |
| Outputs | Typed assets, timebase, input hashes, settings, seed, code/weight revisions and file hashes |
| Adoption | Explicit target/alignment, source-revision checks, audition, undo, reopen and export |
| Failure | Actionable diagnostics, no partial publication, retry and explicit interrupted states |

Runtime availability, downloaded weights, successful inference and evaluated quality are distinct states. Keep incompatible Torch/Transformers profiles separate. CPU, 8 GB, 12–16 GB and 24 GB+ tiers need actual measurements; parameter count is not a pipeline VRAM budget.

## Evaluation and release

Project checks cover operations, history, playback/export consistency, memory and recovery. Evaluate each model task separately. Do not combine lyric, stem, note and generation scores into one ranking. Disclose training overlap, failures and per-case regressions.

- Separation: reference SI-SDR, alignment, leakage, transients and resources.
- Transcription/rhythm: onset, pitch and offset F1, octave errors, beats/downbeats and correction effort.
- Generation: fixed prompts/seeds, conditions, reference retention, joins, candidate-selection cost and blind listening.
- Restoration/effects: clean controls, distortion, fidelity, matched levels and realtime/offline consistency.
- Every backend: controlled cold/warm timings, RAM/VRAM, long input, offline execution, cancellation and recovery.

Validate a complete production path: brief/import, editing, mixing, saving, export and restore in another workspace. Producing one model file does not validate the other project operations. See the [current roadmap](workbench-roadmap.md) and [technical reference](technical-reference.md) for priorities and reproduction.
