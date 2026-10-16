# Music Studio

> **Create · 0.2.0.dev5: an idea-to-export workstation preview.** Sampled instruments,
> editable grooves, MIDI import, multitrack arrangement, a mixer and WAV/MIDI export. Run
> `Start-Music-Studio-Create.cmd`; see [setup and scope](create-preview.en.md).
> Earlier versions and data remain available; recording, buses and automation remain planned.
> New: [live EQ, compression, reverb, presets and master limiting](mixing.en.md), A/B and tail-aware WAV export.
> [Sampled instruments, eight grooves, MIDI import and note properties](creation-library.en.md), available offline.
> New: [modern separation → audition → aligned track replacement](separation.en.md), with retained originals, one-step undo and frozen-set measurements.
> Optional: [local ACE-Step music generation](music-generation.en.md). Audition before adding a track; hardware measurements and failed runs are documented.
> [Local models, open assets and databases](audio-resources.en.md) · [Full model index](local-model-candidates.en.md)

![Music production workstation development preview](images/create-effects-en.png)

> **Next · 0.2.0.dev2**: a local audio AI workbench. Clean speech, normalize loudness and
> compare synchronized A/B before adopting, with undo. Trim, mix, separate, transcribe,
> correct text and extract notes/beats. UI, MCP and Codex share projects, tasks and previews.
> Speech cleanup runs on CPU without a GPU.
> [Try Next](next-preview.en.md) · [Plan](workbench-plan.en.md) ·
> [Speech cleanup results](speech-cleanup.en.md) · [Melody comparison](melody-next.en.md).
> The older **v0.1.2** and existing data stay separate.
> [Local models and setup](next-models.en.md). The classic guide follows below;
> melody quality and the broader workbench continue to develop.

![Next speech cleanup workbench](images/next-cleanup-workbench-en.png)

*Actual UI: CC BY 4.0 noisy speech, real CPU enhancement and loudness measurements.
Some clips regress; the evaluation report retains those results.*

[中文](README.md) · [Download preview](https://github.com/Hydr0g3ngz/music-studio/releases) · [Quick start](QUICKSTART.md) · [Benchmark](lyrics-v4.en.md) · [Roadmap](roadmap.en.md)

**Unfold a song into vocals, backing, timed lyrics, vocal-melody MIDI, chords and beats — on one timeline.**

Runs locally with a browser workbench, CLI and Python engine. No account or paid API;
your songs stay on your computer. Switch **English / 中文** in the UI and keep your
preference. Model installation requires downloads; cached models support offline inference.

![English workbench](images/workbench-en.jpg)

*Actual UI. Example: Let's Go Fishin' — Karissa Hobbs, CC BY 3.0. Lyrics, timing and notes are machine estimates.*

## Hear something before downloading models

1. Download the Windows ZIP from [Releases](https://github.com/Hydr0g3ngz/music-studio/releases) and extract into a writable folder.
2. Install **Python 3.11 or 3.12** and double-click `Start-Music-Studio.cmd`. First startup downloads Python dependencies.
3. Choose **Try the demo** to explore a credited 45-second precomputed example: original/vocal/backing playback, lyric correction, sing along and exports. No neural-model download required.

**Early preview. The ZIP contains source, a wheel and a credited demo. It is not a standalone EXE and does not bundle Python, CUDA or neural weights.**
See [Quick start](QUICKSTART.md) for CPU setup, troubleshooting and preserving data during upgrades.

From source:

```powershell
git clone https://github.com/Hydr0g3ngz/music-studio.git
cd music-studio
.\scripts\setup.ps1 -Mode preview
.\scripts\launch.ps1
```

To analyze your own songs, explicitly install the inference runtime and base models:

```powershell
.\scripts\setup.ps1 -Mode full -Device cuda -DownloadModels
# Use -Device cpu without an NVIDIA GPU (slower inference).
.\scripts\launch.ps1
```

The launcher defaults to offline mode and finds a free local port without stopping
other services. Use its printed URL. NVIDIA 8GB VRAM is the main tested inference
target; macOS/AMD/Intel GPU inference has not been validated.

On Linux, create a Python 3.11/3.12 environment, install suitable CPU/CUDA PyTorch
wheels, then `pip install ".[ui,inference]"` and run `music-studio ui --open`.

For optional Qwen lyric recognition, after the base installation:

```powershell
.\scripts\setup_lyrics.ps1 -Models qwen
.\.venv\Scripts\music-studio.exe ui --model-dir .cache/models --asr-backend qwen --lyrics-alignment anchors --lyrics-python .artifacts/lyrics-env/Scripts/python.exe --offline --open
```

Qwen uses an optional separate environment and about 4.38GiB of weights. The base
installation does not silently add this download. For dual timing guides, download
the `large-v3-turbo` model with `music-studio models download --asr-model large-v3-turbo --model-dir .cache/models`
and add `--anchor-model dual`. More coverage can also worsen timing tails; listen to verify.

## Listen, correct and take the results with you

| Workflow | What you can do |
| --- | --- |
| Hear each layer | Demucs vocals/backing; position-preserving track switching and lazy caching; synthesized melody MIDI |
| Correct lyrics | Whisper or optional Qwen; seek by line, loop context, correct text, or paste correct lyrics for alignment |
| Review difficult phrases | Separate text hints from missing timing; generate a line candidate, compare and explicitly accept it; retain earlier versions and edits |
| Practice | Large sing-along lyrics, backing with adjustable guide vocals, line navigation and loops |
| Export | LRC/SRT, melody MIDI, vocal/backing audio, chord/beat CSV and project JSON |
| Manage songs | Search, rename, delete, undo and Trash restore; stop/resume analysis and rerun an existing song with a new model |

![Sing-along view](images/singalong.jpg)

*The same CC BY 3.0 example. Song names and lyrics are never translated when changing UI language.*

## Evidence, including regressions

The frozen suite accounts for **43 cases**: 26 original component regressions and
17 Mandarin karaoke recordings. The new data was split into 8 development and 9
confirmation recordings before inference, grouped by singer and lyric overlap.

| Fixed comparison | Measured result |
| --- | --- |
| Mandarin confirmation: 9 recordings, 1113 reference characters | Whisper small CER **45.28%** → Qwen3-ASR 1.7B **14.65%** |
| Unchanged Qwen text, 7 English regressions | Correct words within 200ms onset / all timed references: **52.83% → 59.14%** |
| Dual guides on Mandarin confirmation | Coverage improved, but onset P90 worsened **0.616s → 0.713s**; dual guides remain optional |

These are small, domain-specific engineering checks, not an unseen-data leaderboard.
Model pretraining overlap is unknown. Gray text means missing reliable word timing,
not necessarily incorrect text. Vocal melody is a single-lead estimate; chords
currently cover major/minor/N. Review markers and model scores are not accuracy
probabilities. Long songs consume more browser memory.

[Report and interpretation](lyrics-v4.en.md) · [Full per-case results](lyrics-v4.md) · [Data and reproducibility](benchmarks/README.md)

## Help improve it

Issues and contributions in English or Chinese are welcome. Start with a reproducible
problem: installation that blocks first playback, lyrics that are hard to correct,
or exports that do not work downstream. Try the credited demo first; keep private audio out of public issues.

[Contributing](CONTRIBUTING.md) · [Roadmap](roadmap.en.md) · [Changelog](CHANGELOG.md)

```sh
python -m pip install -e ".[ui,benchmark,dev]"
python -m ruff check .
python -m pytest -q
node --test tests/ui_playback.test.cjs tests/ui_i18n.test.cjs
python scripts/package_release.py
```

Core, API and playback checks require no neural weights. Real-model evaluation is
opt-in. No frontend build or external CDN. Original code is [MIT](LICENSE);
models, data and recordings retain their own licenses. See [third-party notices](THIRD_PARTY_NOTICES.md)
and [demo attribution](src/music_studio/ui/demo/ATTRIBUTION.md).
