# Piano transcription with Transkun

[中文](piano-notes.md) · [Simplify/edit notes](note-editing.en.md)

In **AI tools → Piano polyphonic notes**, install the isolated pack. Setup verifies the official Transkun 2.0.1 source, V2 checkpoint and configuration. It installs inference dependencies only, without the training stack's native compiler requirement. A real offline transcription of the included piano sample must succeed before the pack becomes ready.

Select solo piano audio and run **Piano → editable polyphonic MIDI**. Results include note JSON, MIDI and synthesized audition. **Add notes to instrument track** to edit, simplify, change instruments and export with the project.

## Hardware and precision

- Windows x64; automatic setup uses Torch 2.10 / CUDA 12.8, **FP32 without quantization**.
- Setup requires a Turing-or-newer NVIDIA GPU, at least 4 GB total VRAM and a compatible driver. Runtime also checks about 2 GB free VRAM. Explicit CPU selection uses the same pack; it is not a small CPU-only download.
- Expected download 3–5 GB; reserve 10 GB disk space. The checkpoint is about 56 MB, much smaller than its runtime.
- One 16-second piano clip on RTX 4070 Laptop 8 GB took about 10.8 seconds in the model call and 18.3 seconds for the complete invocation, peaking at about 904 MiB in Torch. This includes loading and excludes CUDA context memory; it is not a minimum-hardware guarantee.

Basic Pitch remains useful for users avoiding Torch and for other solo instruments. Choose for the input. The [piano development benchmark](../benchmarks/reports/piano-v1.json) covers six excerpts from three pieces, not a ranking across all styles.

## Limits

This model targets piano. The current V2 default uses key-release offsets; CC64 sustain is not expanded into note durations. Pedal events are not imported into the piano roll. Velocities are estimates. There is no calibrated per-note confidence: JSON `score=0` means unavailable, not certainly incorrect.

Do not expect a full mix to become an accurate score. Check synthesized piano, strong reverb, unusual playing and generated audio carefully. The official checkpoint and configuration are hash-pinned before loading. Source and weights come from the [official project](https://github.com/Yujia-Yan/Transkun) under its MIT license.
