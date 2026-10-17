# v0.1 validation · 2026-10-15

> Historical reference for the Studio analysis workflow or a pre-split build. Start with [current Workbench documentation](README.en.md). The analysis product is maintained in [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Commands and measurements below apply to the stated historical version.

These are actual local runs. They demonstrate interoperability, offline execution and output integrity, **not accuracy across arbitrary songs**.

The subsequent workbench run analyzed the full 132.989-second song in 107.31 seconds. Its browser and API checks are recorded in [UI validation](ui-validation.md).

## Environment

- Windows, Python 3.12.4, 32GB system memory.
- NVIDIA GeForce RTX 4070 Laptop GPU, approximately 8GB VRAM, driver 591.74.
- PyTorch / torchaudio 2.5.1+cu121; Demucs 4.0.1 (`htdemucs`).
- faster-whisper 1.2.1, CTranslate2 4.6.0, multilingual `small` at revision `536b0662742c02347bc0e980a01041f333bce120`.
- torchcrepe 0.0.24, full CREPE; librosa 0.11.0.
- Selected package versions are recorded in [environment-win-cuda.txt](environment-win-cuda.txt). This is an environment record, not a cross-platform lockfile.

The initial CTranslate2 4.8.3 installation exited during model loading on this host. Version 4.6.0 successfully loaded and transcribed on CUDA; its `pkg_resources` import also requires setuptools <81. Both constraints are now part of the inference extra. The existing compatible PyTorch runtime was copied into the isolated development environment to avoid downloading the same large runtime again; the public setup script installs the matching official wheels.

## Real GPU pipeline, offline

```powershell
.\.venv\Scripts\python.exe -u scripts\smoke_test.py .artifacts\demo\fishin-30s.wav --output .artifacts\fishin-gpu --device cuda --model-dir .cache\models --offline --sample-gpu
```

Input: a 30-second crop, source time 20–50 s, of **Let's Go Fishin' — Karissa Hobbs**, CC-BY 3.0, obtained through librosa. See [attribution](../THIRD_PARTY_NOTICES.md). No input audio or derived test files are committed to the repository.

| Result | Observed value |
| --- | --- |
| Duration | 30.000 s |
| Automatically detected language | English |
| Lyric lines / word entries | 5 / 54 |
| Melody notes | 71 |
| Notes linked to at least one word | 69 |
| Chord intervals | 11 |
| Beat positions | 59 |
| End-to-end wall time | 69.79 s |
| Sampled whole-GPU peak | 1,031 MiB |
| GPU memory baseline | 0 MiB |
| Output validation | Passed |

The wall time includes worker startup, imports, model loading and validation, but not initial downloads. GPU memory was sampled about once per second with `nvidia-smi`, across 48 samples, and includes other processes if present. It may miss transient peaks. It is not a minimum-memory guarantee and should not be extrapolated to other models or song lengths.

Validation checked identical sample counts / rates / channels for all three audio tracks, annotation bounds, artifact hashes, pitch-contour time order, and MIDI note pitches / start / end times against project JSON. MIDI time differences must remain within 10ms. The number of generated lyrics or notes is **not** an accuracy score; this sample has not been manually annotated for CER/WER or note F1.

An earlier 20-second Demucs repository sample also completed all stages and validation (25 notes, 8 chord intervals, 38 beats). Its ASR result was empty, so it was not used as evidence for lyric transcription. A second CLI run with `--resume --offline` reused all six cached stages successfully.

## CPU fallback

The CLI also completed a 5-second excerpt of the same song (source time 25–30 s) with `--device cpu --pitch-backend pyin --offline`. Output validation passed: one lyric line, 12 melody notes, three chord intervals and 11 estimated beat positions. This confirms the CPU execution path and the pYIN adapter work on this host; it is not a CPU throughput benchmark or an accuracy measurement.

## Core tests and packaging

11 core tests passed. They cover decoded audio alignment, stereo channel preservation, stem gain, vibrato / repeated notes, one-word-to-many-note links, chord and beat baselines on generated signals, variable-tempo MIDI timing, damaged cache recovery and restart after a stage failure. The orchestration tests deliberately use deterministic model adapters; real-model evidence is reported separately above.

This host's shared default pytest temporary folder had an existing permission issue. Tests used an explicit project-local temporary directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .artifacts\pytest-final
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\uv.exe build --out-dir dist --offline
```

Ruff and dependency consistency checks passed. A Python wheel and source distribution were built. The repository contains a Windows / Linux, Python 3.11 / 3.12 core-test CI matrix; that remote matrix has not been executed in this local task. macOS and AMD / Intel GPU backends have not been validated.
