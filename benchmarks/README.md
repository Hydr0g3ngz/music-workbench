# Model evaluation datasets and commands

Speech cleanup has a separate **32-pair** VoiceBank-DEMAND regression protocol,
with disjoint 16-pair pilot/follow-up files from the same two test speakers. It is not added
to the older song/lyric case count. See [methods, per-case regressions and reproduction](../docs/speech-cleanup.en.md)
([中文](../docs/speech-cleanup.md)), [pilot](speech-cleanup-v1.json) and
[follow-up](speech-cleanup-validation-v1.json). Numerical reports are in `results/cleanup-*.json`;
full audio and model weights remain local.

This suite reuses published audio and annotations. No new manual labels are required. The frozen selection lives in [suite-v1.json](suite-v1.json); audio and reference text are downloaded into the ignored `.artifacts/benchmark/data/` directory.

The [v4 extension](suite-v2-mir1k.json) adds 17 Mandarin karaoke recordings with human character boundaries, bringing the inventory to **43 cases**. Its 8-development / 9-confirmation split was frozen before new inference. See v4 results and limitations; the original 26-case suite remains unchanged.

The suite evaluates individual analysis components used by the audio tools. It does not measure the usability or musical quality of a complete Workbench project. This is an engineering regression set, not an official benchmark split or an unbiased model leaderboard. It keeps four different evaluation domains separate:

The original ten-case pilot is retained. Complete **26/26** baselines and paired improvements are in [results](results/), with a [fixed protocol](protocol-v1.json), v2 decisions and lyrics v3 results. Basic installation retains small ASR; the optional Qwen configuration prioritizes text accuracy and marks missing word times explicitly.

| Source | Cases | What it tests | Reference |
| --- | ---: | --- | --- |
| Jam-ALT + JamendoLyrics | 7 English full songs | Lyrics from real accompanied mixes; matched-word timing | Revised Jam-ALT text/line timings and the corresponding Jamendo word timings |
| GTSinger | 12 phrases: 6 Mandarin, 6 English | Clean singing recognition and note transcription; natural, breathy, vibrato performances | Published word/phone and note-start/end JSON, with TextGrid originals |
| GuitarSet 1.1.0 | 5 accompaniment recordings | Beat positions and chords on acoustic guitar | JAMS beat positions and the inferred performed-chord annotation |
| MUSDB18 seven-second previews | 2 official test tracks | Vocal/instrumental source separation | Original mix, drums, bass, other and vocal streams in one STEMS container |

The selected GuitarSet takes cover five players and five styles. GTSinger covers four singers; all selections use frozen upstream IDs without inspecting model predictions. The source dataset revisions, download URLs, byte counts and individual SHA-256 hashes are recorded in the manifest. For ZIPs, only selected members are fetched and their SHA-256 verified; the whole archive's MD5 is recorded for provenance but is not claimed to have been verified by a partial download.

## Reproduce

From a source checkout with Python 3.11/3.12:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[benchmark]"

# Download exactly the frozen audio/reference files, then verify them
.\.venv\Scripts\python.exe scripts/benchmark.py prepare
.\.venv\Scripts\python.exe scripts/benchmark.py validate

# Ten representative cases; inference dependencies/models are also needed
.\.venv\Scripts\python.exe scripts/benchmark.py run --smoke --device cuda --model-dir .cache/models --offline

# Entire 26-case old baseline
.\.venv\Scripts\python.exe scripts/benchmark.py run --device cuda --offline --output .artifacts/benchmark/runs/my-baseline

# All components of the new default; no inherited predictions
.\.venv\Scripts\python.exe scripts/benchmark.py run --settings benchmarks/experiments/balanced-v2.json --device cuda --offline --output .artifacts/benchmark/runs/my-balanced

# Compare the same cases, rejecting missing results or changed suite hashes
.\.venv\Scripts\python.exe scripts/compare_benchmarks.py .artifacts/benchmark/runs/my-baseline/report.json .artifacts/benchmark/runs/my-balanced/report.json --output .artifacts/benchmark/my-comparison.json

# Recompute metrics without rerunning inference
.\.venv\Scripts\python.exe scripts/benchmark.py score --smoke
```

Use `--data` to store audio elsewhere, `--output` for a new model/configuration comparison, and repeated `--case ID` options for a subset. Case IDs are frozen; `--smoke` selects those marked in the manifest. Model offline mode and benchmark download preparation are separate operations.

Neural stages reuse the product's existing workers. Clean singing is supplied directly to the lyric/melody adapters; guitar accompaniment directly to the rhythm/harmony adapters; real lyric mixes undergo separation before ASR. Original reference words/notes are never passed into these inference calls. Languages are supplied from dataset metadata. MUSDB preview inference uses only the mixture stream; the original stems are used exclusively during scoring.

Predictions, stage logs, cache signatures and scores are saved under `.artifacts/benchmark/runs/`. Input, package/backend and setting signatures prevent mixing incompatible runs. Stage artifacts and their audio dependencies are hashed before reuse. Selecting a different model/configuration requires a new output directory. An interrupted run can be continued with the same command. Scoring failures can be repaired and rerun with `score` without paying for neural inference again.

## Metrics

See the [complete protocol](../docs/benchmark-protocol.md) for gates, resource measurements and product flows. New runs freeze Python sources into `_engine/`, so edits cannot change a running evaluation. Cached and inherited predictions are excluded from newly executed timing totals. GPU memory uses roughly 1Hz device-wide samples, including other processes; this can miss instantaneous peaks.

`scripts/ablate.py` executes selected components against hash-verified baseline artifacts. Rhythm changes must also rerun harmony because beats control chord boundaries. Example:

```powershell
.\.venv\Scripts\python.exe scripts/ablate.py --baseline .artifacts/benchmark/runs/my-baseline --output .artifacts/benchmark/runs/my-turbo --settings benchmarks/experiments/lyrics-turbo.json --stage lyrics
.\.venv\Scripts\python.exe scripts/ablate.py --baseline .artifacts/benchmark/runs/my-turbo --output .artifacts/benchmark/runs/my-text-profile --settings benchmarks/experiments/combined-v2.json --stage melody --stage rhythm --stage harmony --stage separate
.\.venv\Scripts\python.exe scripts/ablate.py --baseline .artifacts/benchmark/runs/my-text-profile --lyrics-from .artifacts/benchmark/runs/my-baseline --output .artifacts/benchmark/runs/my-balanced-composed --settings benchmarks/experiments/balanced-v2.json
```

Composition validates identical source/vocal hashes and preserves measured component provenance. It is a quality regression check, not a fresh speed measurement; use full `run` for that. Separation-only comparisons score MUSDB, without claiming downstream ASR gains. `--beat-folds` selects official held-out fold weights from a pinned GuitarSet split. small0 diagnostics require `--training-overlap` and cannot be promoted by the comparison tool. The archived v2 experiment used small0 only for diagnostics; out-of-fold weights were not evaluated.

- **Text:** normalized CER for Mandarin, normalized WER for English. Normalization uses Unicode NFKC, case folding, punctuation removal and apostrophe collapsing; Mandarin whitespace is removed. No simplified/traditional conversion is performed. This transparent basic score is not a reproduction of the official Jam-ALT formatting/readability metrics.
- **Word timing:** exact-text monotonic matches from a Levenshtein alignment, with onset MAE/median/P90 and match coverage. Missing or incorrect words remain reflected in text errors and coverage. An error over a few surviving matches must never be described as overall alignment accuracy. Multi-character ASR tokens keep their existing boundaries; no character timing is fabricated.
- **Notes:** `mir_eval` onset/pitch F1 (50 ms, 50 cents), plus onset/offset/pitch F1 (offset tolerance max of 50 ms or 20% of reference duration). GTSinger's `note_start`/`note_end` are used, not the quantized score duration field.
- **Beats:** `mir_eval` F-measure with 70 ms tolerance and first five seconds excluded, plus correct/any metric-level continuity. A correct global BPM does not prove correct beat phase.
- **Chords:** duration-weighted root and major/minor reduction, using GuitarSet's performed rather than instructed chords. The fraction of reference duration eligible for major/minor scoring is reported; sus/other unsupported reference types can be excluded by this metric.
- **Separation:** SI-SDR and improvement over the input mixture, for vocals and summed accompaniment. Stereo channels are flattened after mean removal. Sample counts/rates must match; no time-shift fitting is applied. These AAC previews are not the full-song MUSDB-HQ evaluation, and the metric is not SiSEC's BSS Eval SDR.

Text errors are pooled by reference token count within the same dataset/language. Other summary scores are explicitly case averages. Different domains/tasks are not collapsed into a single percentage.

## Scope and reuse

Some candidate singing models were trained on GTSinger. In particular, VocalParse documents GTSinger as training data; STARS also documents a GTSinger preparation path. Record candidate training overlap before using this suite as evidence of generalization. Beat models may also have seen public beat datasets. The frozen subset is useful for compatibility and local regressions even when it cannot establish unseen-data performance.

The v1 suite contains no Mandarin commercial-style accompanied mix with both lyric and note ground truth. The v4 addition is amateur karaoke, with lyric/character timing references but no new note ground truth. GTSinger is isolated singing, GuitarSet is acoustic accompaniment, and MUSDB previews are very short. Preserve these distinctions when reporting results. DALI's broad automatically aligned corpus and MIR-ST500's YouTube-based audio links are useful expansion candidates, but are not silently treated as equivalent to these locally verified references.

## Sources and attribution

- [Jam-ALT](https://huggingface.co/datasets/jamendolyrics/jam-alt), [JamendoLyrics](https://huggingface.co/datasets/jamendolyrics/jamendolyrics), and [AudioShake's benchmark/code](https://github.com/audioshake/alt-eval). Full-song credits and per-track CC variants are in the manifest. The seven English tracks were selected from the recorded non-ND variants; some are non-commercial.
- [GTSinger](https://huggingface.co/datasets/AaronZ345/GTSinger) by Yu Zhang and collaborators, [official code](https://github.com/AaronZ345/GTSinger), CC BY-NC-SA 4.0. Recordings and labels retain their upstream terms; no dataset material is relicensed as MIT.
- [GuitarSet 1.1.0](https://zenodo.org/records/3371780) by Qingyang Xi, Rachel Bittner, Johan Pauwels, Xuzhou Ye and Juan Pablo Bello, CC BY 4.0. The chord/beat adapter follows the [mirdata documented interpretation](https://mirdata.readthedocs.io/en/stable/_modules/mirdata/datasets/guitarset.html).
- [SiSEC18-MUS previews](https://zenodo.org/records/3270814) by Fabian-Robert Stöter, Antoine Liutkus and Nobutaka Ito; see the [MUSDB source/stream definitions and per-track rights](https://sigsep.github.io/datasets/musdb.html). The preview record metadata and underlying track-use notices are both retained; benchmark audio is optional local evaluation material.

GitHub receives code, the frozen manifest and aggregate reports. Original audio, lyrics, annotations and derived audio stay in ignored local directories under their original terms.

## Lyrics v3 experiments

Install the optional lyric runtime as documented in the project README. The following commands start from the measured balanced run above, recognize all 19 lyric cases and inherit the other seven cases with hash checks:

```powershell
# Fresh seed=0 control (explicit CTranslate2 seed, native word times)
.venv/Scripts/python.exe scripts/realign_benchmark.py --baseline .artifacts/benchmark/runs/my-balanced --output .artifacts/benchmark/runs/my-small --settings benchmarks/experiments/lyrics-small-seeded.json --recognize

# Qwen text with its original coarse 60-second containers; no forced aligner needed
.venv/Scripts/python.exe scripts/realign_benchmark.py --baseline .artifacts/benchmark/runs/my-balanced --output .artifacts/benchmark/runs/my-qwen-native --settings benchmarks/experiments/lyrics-qwen-native.json --recognize

# Independent alignment ablation: unchanged Qwen text, measured small acoustic guides
.venv/Scripts/python.exe scripts/realign_benchmark.py --baseline .artifacts/benchmark/runs/my-qwen-native --output .artifacts/benchmark/runs/my-qwen-anchors --settings benchmarks/experiments/lyrics-qwen-anchors.json --guide-from .artifacts/benchmark/runs/my-small --native-input

# Domain-separated text comparisons and pooled word timing (no prediction text in output)
.venv/Scripts/python.exe scripts/compare_benchmarks.py .artifacts/benchmark/runs/my-small/report.json .artifacts/benchmark/runs/my-qwen-anchors/report.json --output .artifacts/benchmark/lyrics-comparison.json
.venv/Scripts/python.exe scripts/summarize_lyrics_benchmark.py .artifacts/benchmark/runs/my-small .artifacts/benchmark/runs/my-qwen-anchors --output .artifacts/benchmark/lyrics-summary.json
```

`--recognize` uses shared ASR models across cases and then releases them before the selected alignment phase. `--native-input` selects the saved pre-alignment ASR result and verifies that normalized text matches the measured prediction. `--guide-from` validates small's revision, native timing, audio, language, seed, output hash and seeded engine before using its predictions. It never accepts gold lyric annotations as a guide. Cached guide matching runs on CPU and does not measure neural ASR/alignment runtime.

The initial archived Qwen-vocals run predates native-result caching and has one output for every 60-second chunk, including all short clips. Its final production ablation uses `--qwen-native-windows` to restore only those coarse containers, after rejecting any missing/split chunk sequence. Recognition text is unchanged; no word boundaries are reconstructed. Source/Heart runs use actual cached native results. New experiments should use native caching directly as in the commands above.

The published v3 matrix also includes source input, Heart, freshly seeded turbo, two forced aligners, earlier anchor matchers, and an explicitly incomplete 28-second attempt. See `lyrics-v3-protocol.json` and `results/lyrics-v3-summary.json`. A warm batch's per-case stage times exclude process startup; do not compare them with cold full-pipeline speed. A fresh worker reproduced the same small and Qwen text on one complete song; this does not establish determinism for all hardware or library versions.

## MIR-1K v4 extension

[The frozen extension](suite-v2-mir1k.json) selects all 17 human-aligned recordings from the pinned ASRU author annotation file. Its original stereo channels are averaged into a mix before Demucs separation. The manifest records both original and derived hashes. The original host was unavailable; a pinned individual-file mirror is recorded. Mirror metadata does not replace the original source terms, and no recording or lyric content is redistributed here.

After installing the base and optional Qwen environments described in the project README, prepare the cached small/turbo/Qwen models, then run:

```powershell
.venv/Scripts/python.exe scripts/benchmark.py prepare --manifest benchmarks/suite-v2-mir1k.json
.venv/Scripts/python.exe scripts/benchmark.py validate --manifest benchmarks/suite-v2-mir1k.json
.venv/Scripts/python.exe scripts/benchmark.py run --manifest benchmarks/suite-v2-mir1k.json --settings benchmarks/experiments/lyrics-v4-small.json --output .artifacts/benchmark/runs/mir-small-v4 --device cuda --model-dir .cache/models --offline
.venv/Scripts/python.exe scripts/realign_benchmark.py --manifest benchmarks/suite-v2-mir1k.json --baseline .artifacts/benchmark/runs/mir-small-v4 --output .artifacts/benchmark/runs/mir-qwen-dual-v4 --settings benchmarks/experiments/lyrics-v4-dual.json --recognize
.venv/Scripts/python.exe scripts/evaluate_lyrics_v4.py --mir-only
```

The recognition batch requires a fresh output directory. It inherits verified audio/separation results and runs Qwen plus both timing guides, saving native recognition and guide caches. The CPU evaluation then compares small versus dual guides on exactly the same Qwen text. No reference lyrics enter the inference engine. `--mir-only` uses a separate report filename and does not overwrite the full 43-case report.

For the complete regression plus confirmation table, first reproduce the v3 directories above using the archived run names (`lyrics-qwen-production-v3`, `lyrics-small-seeded-v3`, `lyrics-turbo-seeded-v3`), then run:

```powershell
.venv/Scripts/python.exe scripts/evaluate_lyrics_v4.py
```

The scorer saves predictions before reading references, checks source/guide hashes and model revisions, separates language and split, reports pooled S/D/I, coverage, 200ms end-to-end onset score, pooled MAE/P90 and per-case results. Descriptive paired bootstrap intervals use the frozen singer/lyric clusters, 10,000 draws and seed 20261015. They do not establish model-training exclusion or population-level generalization.

A separate optional interface diagnostic compares the official Qwen aligner raw-text input with the adapter's token input on three saved v3 predictions. It requires the optional aligner model/runtime and keeps detailed token text in ignored local output:

```powershell
$env:PYTHONPATH='src'
.artifacts/lyrics-env/Scripts/python.exe scripts/audit_lyric_aligner.py --offline
```

It is a malformed-span diagnostic, not another accuracy benchmark. Public reports contain numerical summaries, input hashes and model/driver identity. See v4 decisions and [results](results/).
