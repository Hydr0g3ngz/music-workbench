# Melody and MIDI: candidate comparison

[中文](melody-next.md) · 2026-10-16 · [Per-case JSON](../benchmarks/results/melody-next-2026-10-16.json)

**Keep the current default for now.** ROSVOT improves the existing GTSinger regression but
regresses on independent vocadito recordings. Basic Pitch also fails to beat the current
GTSinger baseline. Model accuracy, synthesis timbre and MIDI serialization are evaluated separately.

## Protocol

- Retain the frozen 12-clip GTSinger regression: six Chinese, six English. It has already informed development.
- Add all 40 [vocadito](https://zenodo.org/records/5578807) clips. Released metadata has 29 singer IDs.
  The official description lists seven languages; CSV mixed-language and no-lyrics labels remain separate.
  The [manifest](../benchmarks/vocadito-v1.json) pins audio, f0 and both note annotations by SHA256.
- Vocadito is solo singing, not mixtures. Report human annotators A1 and A2 separately.
- `mir_eval 0.8.2`: 50 ms onset, 50 cents pitch, offset `max(50 ms, 20% duration)`.
  Clip macro averages; failed clips count as zero rather than disappearing from denominators.
- Audio only: no reference lyrics, notes or true word boundaries enter models.
  ROSVOT uses RWBD and the official default thresholds 0.85/0.5, without vocadito tuning.
- MIDI roundtrips check pitch, counts, same-pitch overlap and absolute seconds within 10 ms.
- Contour scores are separate. Unvoiced `null` values become 0 Hz. All 80 final vocadito outputs
  have been rescored through the same corrected scorer; every metric matches the retained results.

## Note scores

F1 percentages are not percentages of correctly transcribed notes.

| Dataset / metric | CREPE + stable | Basic Pitch | ROSVOT + RWBD |
| --- | ---: | ---: | ---: |
| GTS Chinese onset+pitch | 30.6 | 19.8 | **59.8** |
| GTS English onset+pitch | 38.8 | 19.5 | **48.9** |
| GTS Chinese with offsets | 16.6 | 10.8 | **56.3** |
| GTS English with offsets | 20.8 | 6.3 | **36.9** |
| vocadito A1 onset+pitch | **45.6** | Not tested | 26.0 |
| vocadito A2 onset+pitch | **42.0** | Not tested | 27.0 |
| vocadito A1 with offsets | **25.7** | Not tested | 18.5 |
| vocadito A2 with offsets | **22.9** | Not tested | 21.6 |

ROSVOT onset+pitch scores regress on 39/40 clips for A1 and 37/40 for A2. Paired differences
with 2000 singer-cluster bootstrap samples have 95% intervals of −23.3 to −15.9 and −18.9 to −11.1
percentage points. These describe this engineering sample, not every singing domain.

| vocadito contour macro average | CREPE | ROSVOT's RMVPE |
| --- | ---: | ---: |
| Raw Pitch Accuracy | 98.07% | 98.20% |
| Raw Chroma Accuracy | 98.15% | 98.28% |
| Voicing Recall | 99.09% | 99.83% |
| Voicing False Alarm | 27.37% | 31.27% |

High contour scores alongside weak note F1 point toward onsets, offsets, repeated pitches and
unvoiced/consonant gaps as priorities. They do not prove pitch is correct in every clip.
The decoder follow-up below tests this without changing the pitch network.

## Rest-preserving decoding remains optional

Legacy `stable` bridges same-pitch gaps up to 100 ms, then divides gaps up to 250 ms
between neighboring notes. The new `rest` decoder skips both postprocessing steps,
retaining Viterbi gaps. Pitch estimation, thresholds and minimum duration stay unchanged.
Some repeated notes reappear; onsets, offsets, slides, octave errors and bleed remain concerns.

Split by metadata singer ID into 22 development clips (14 IDs) and 18 validation clips
(15 IDs). Compare 0/20/40 ms bridging on development, then freeze zero bridging and no
gap sharing in the [protocol](../benchmarks/melody-boundaries-v1.json) before opening validation
note labels. Vocadito was already inspected in the earlier model comparison: this is a
singer-separated follow-up, not a previously unseen blind test. Reuse cached CREPE contours
and score both human annotators separately.

| Data / metric, F1% | stable | rest |
| --- | ---: | ---: |
| vocadito validation A1 onset+pitch | 45.6 | **55.8** |
| vocadito validation A1 including offset | 24.7 | **35.9** |
| vocadito validation A2 onset+pitch | 43.0 | **51.1** |
| vocadito validation A2 including offset | 20.6 | **29.8** |
| GTS Chinese onset+pitch | **30.6** | 19.6 |
| GTS English onset+pitch | **38.8** | 34.3 |

A1/A2 still regress on 3/18 and 5/18 validation clips. Singer-cluster bootstrap intervals
(2000 replicates) for onset+pitch changes are +5.3 to +15.8 and +3.1 to +14.0 percentage
points. GTS regressions prevent claiming a universal improvement. The classic default stays
`stable`; Next offers both options and an estimated-note audio synthesis for comparison.
An instrument change remains separate from transcription quality.

The [per-case report](../benchmarks/results/melody-boundaries-2026-10-16.json) retains the
development grid, validation, GTS regressions, contour hashes and MIDI checks. The original
[selection record](../benchmarks/results/melody-boundaries-selection-v1.json) has protocol-pinned bytes. All 52 selected
candidate clips complete; maximum MIDI roundtrip error is about 0.21 ms. That does not prove
notes match the performance. Next prioritize onset/offset detection and source conditions,
with new validation data before promoting another default.

Reproduce with `scripts/evaluate_note_boundaries.py` and cached vocadito CREPE runs;
`--partition heldout --bridges 0` enforces the selection. Use `scripts/evaluate_boundary_regression.py`
for the frozen GTS regression. Both refuse to overwrite previous outputs.

## Resources and serialization

RTX 4070 Laptop 8GB, PyTorch 2.5.1+cu121, four Torch CPU threads. Median clip inference was
1.04 s for CREPE and 0.51 s for ROSVOT. Maximum Torch allocated GPU memory was about
734/708 MiB. This excludes driver/context memory, other GPU programs and process RAM,
and cannot be extrapolated to long songs or other models.

All final runs completed and passed MIDI roundtrips. Three existing song MIDIs were also
inspected read-only: maximum timing difference 0.354 ms, pitches matching saved predictions.
This rules out obvious serialization drift, not transcription errors. Melody quality remains unresolved.

ONNX Runtime 1.31.0 crashed on import on this machine; Basic Pitch ran through an isolated
1.20.1 compatibility directory. Model health checks therefore
need actual imports in a subprocess, rather than package-presence checks alone.

## Reproduce and attribute

Use the [GTS runner](../scripts/evaluate_melody_next.py),
[vocadito runner](../scripts/evaluate_vocadito.py) and [experimental adapter](../scripts/rosvot_adapter.py).
Fresh output directories preserve source snapshots, model/data hashes, raw outputs and per-case scores.
Public JSON retains run identities and canonical rescoring checks. Local execution snapshots differ
byte-for-byte from the current scripts, which subsequently gained CPU/input validation options.

Install the repository `[benchmark]` extra plus Torch, torchaudio, torchcrepe, pyworld, pretty_midi and PyYAML
in an isolated experiment environment; obtain ROSVOT weights through the author README. Tested versions
are recorded in JSON. Neural experiments do not run in normal tests. The downloader verifies archive hashes.

```bash
python scripts/download_vocadito.py --data /data/vocadito
python scripts/evaluate_vocadito.py --data /data/vocadito --backend crepe --output runs/vocadito-crepe
python scripts/evaluate_vocadito.py --data /data/vocadito --backend rosvot --upstream /path/ROSVOT --checkpoints /path/checkpoints --output runs/vocadito-rosvot
```

CUDA is the experiment default; `--device cpu` is available. Inference dependencies are separate
from basic editing installation. The experimental ROSVOT adapter rejects inputs above 30000 model
frames; production long-song chunking is not implemented.

- [ROSVOT](https://github.com/RickyL-2000/ROSVOT), commit `3c8332bf43adae35f6e4d64971862f2f6139b310`,
  Ruiqi Li, MIT code ([copy](licenses/ROSVOT-MIT.txt)). Author-provided weights are not redistributed here.
- [Basic Pitch](https://github.com/spotify/basic-pitch), commit `fa5997af0a8210982619003269994a1be25eddf3`,
  Spotify, Apache-2.0, official ONNX weights/default inference.
- vocadito, Rachel Bittner, Katherine Pasalo, Juan José Bosch, Gabriel Meseguer Brocal and David Rubinstein,
  2021, CC BY 4.0 ([record](https://zenodo.org/records/5578807)). Only manifests and metrics are included here.

Existing GTSinger provenance and selection remain in the [original benchmark guide](../benchmarks/README.md).
