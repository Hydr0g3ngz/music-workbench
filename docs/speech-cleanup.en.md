# Speech cleanup and matched listening

> For the compatibility asset editor `next.html`. This page covers speech cleanup and a fixed-data evaluation. See the [workstation guide](create-preview.en.md) for music creation.

[中文](speech-cleanup.md) · [Next setup](next-preview.en.md) · [Local models](next-models.en.md)

Speech cleanup, loudness normalization and synchronized A/B use shared assets, previews and undo history. Experimental Codex / MCP tools can use the same operations.

![Real speech cleanup comparison](images/next-cleanup-en.png)

## Try a recording

1. Launch `Start-Music-Studio-Next.cmd`, import audio or load the noisy speech demo.
2. Choose **Clearer speech**. First use shows the model source, size and license; weights
   download only when you explicitly install them.
3. DPDFNet 48 kHz is the initial choice. Adjust strength if needed. Jobs pin the full currently
   auditioned asset, rather than modifying the source.
4. Compare input and output at the same position. Loudness matching only attenuates the louder
   side for listening and does not change exports.
5. Create an editable preview, explicitly adopt it, or continue with loudness, trimming and
   export. Adoption supports undo and redo.

Both denoisers run on CPU through Sherpa-ONNX, without a GPU or Torch. The basic Next install
includes the CPU runtime and loudness library, but no downloaded neural weights. Installation
is a separate UI / CLI action; analysis and agent tools do not download models implicitly.
DPDFNet weights are about 10.11 MiB; GTCRN is about 0.51 MiB. Both are pinned by SHA-256.

Speech enhancement can alter speech, remove ambience, damage music or change the stereo image.
GTCRN operates at 16 kHz and does not preserve content above 8 kHz. DPDFNet operates at 48 kHz
but does not guarantee unchanged speech or music. Results are separate assets.

## Paired evaluation before choosing the UI default

The [official VoiceBank-DEMAND dataset](https://doi.org/10.7488/ds/2117),
Cassia Valentini-Botinhao (2017), provides existing clean/noisy pairs under CC BY 4.0.
No new manual labels were created. This is a small engineering regression exercise, not a
reproduction of a full published leaderboard.

- Freeze pilot first: rank filenames by `SHA256("speech-cleanup-v1:" + filename)` and select
  the first eight per test speaker, 16 pairs total.
- After GTCRN's pilot STOI regressions, add DPDFNet as a candidate. Its 12 dB attenuation limit
  follows the upstream example.
- Freeze a disjoint follow-up before inference: ranks 8–15 from the same two speakers,
  another 16 pairs. Do not tune processing on those results.
- Verify manifest and original WAV hashes. Process full files without post-hoc lag or gain
  fitting. Retain native-rate and 16 kHz SI-SDR / STOI, per-case regressions, clean controls
  and timing.

Primary 16 kHz paired results follow. STOI deltas use its 0–1 scale. A regression is any
negative delta, including tiny numerical changes.

| Model / subset | Mean SI-SDR delta | Mean STOI delta | STOI regressions | Median CPU RTF |
| --- | ---: | ---: | ---: | ---: |
| GTCRN / pilot | +5.637 dB | −0.00725 | 8 / 16 | 0.105 |
| DPDFNet2 / pilot | +8.192 dB | +0.01525 | 2 / 16 | 0.409 |
| GTCRN / follow-up | +6.012 dB | −0.00368 | 10 / 16 | 0.126 |
| DPDFNet2 / follow-up | +7.029 dB | +0.01265 | 5 / 16 | 0.496 |

DPDFNet is therefore the initial choice **when a user opens speech cleanup**, while GTCRN
remains experimental. Imports are never automatically denoised. DPDFNet improved SI-SDR on
all 16 follow-up files but regressed in STOI on five: `p257_216` −0.00962, `p257_297` −0.00817,
`p257_352` −0.01698, `p257_396` −0.01231 and `p257_043` −0.00211.

GTCRN had one pilot SI-SDR regression; the other three groups had none. All measured outputs
retained rate, channels and frame count, were finite, and left source hashes unchanged.
Cross-correlation lag diagnostics within ±20 ms were zero throughout. Clean speech is also
altered: follow-up clean-control mean STOI was 0.99182 for DPDFNet and 0.97861 for GTCRN,
rather than 1.

RTF is processing time / audio duration, including model loading, resampling and metering.
These Windows measurements use two CPU threads and are not a controlled speed ranking.
One DPDFNet case had RTF about 1.12; the median does not establish universal real-time speed.
There is no independent-speaker confirmation, confidence interval or subjective blinded
listening study. Pretraining overlap was not independently ruled out. Both subsets share
one domain and two speakers, so the results do not establish Chinese, music or general
real-world performance.

[GTCRN pilot](../benchmarks/results/cleanup-gtcrn-pilot-2026-10-16.json) ·
[DPDFNet pilot](../benchmarks/results/cleanup-dpdfnet2-pilot-2026-10-16.json) ·
[GTCRN follow-up](../benchmarks/results/cleanup-gtcrn-validation-2026-10-16.json) ·
[DPDFNet follow-up](../benchmarks/results/cleanup-dpdfnet2-validation-2026-10-16.json)

## Loudness and playback rules

[pyebur128](https://github.com/jodhus/pyebur128) / libebur128 1.2.6 measures gated integrated
LUFS, true peak in dBTP and LRA. RMS and sample peak retain separate labels. LUFS can be
unmeasurable below the gate, for silence or for audio shorter than 400 ms. LRA is marked
provisional below 60 seconds. Current support is mono and stereo.

Normalization applies static gain, with no compressor or limiter. The editable −16 LUFS /
−1 dBTP defaults are starting points, not platform compliance promises. True-peak headroom
caps the gain; an unmet target is reported instead of silently clipping. Each preview retains
before/after measurements, target, applied gain and the peak constraint.

A/B requires equal length, rate and channels. Both immutable assets are preloaded and switched
at the same position. Matching attenuates the louder integrated-LUFS side, never boosts the
quieter side, and does not change export. Noise contributes to this measurement, so it is not
an exact speech-only level match. Trimmed clips are not treated as the same timeline.

Synthetic checks cover a −23 LUFS tone, stereo summation, gating, silence, short audio,
resampling alignment and intersample peaks. The official EBU test ZIP returned HTTP 403 in
this run; that suite has not been completed. No EBU certification or full conformity claim
is made.

## Reproduce

```bash
python -m pip install -e '.[ui,audio,agent,benchmark,dev]'
python scripts/download_speech_cleanup.py --suite all
python -m music_studio.studio.cleanup download --model-dir .cache/models --model dpdfnet2-48k
python scripts/benchmark_speech_cleanup.py --data-dir .cache/benchmarks/speech-cleanup --model-dir .cache/models --model dpdfnet2-48k --suite validation --output .artifacts/dpdf-validation.json
```

Use `--model gtcrn` for GTCRN and `--suite pilot` for the pilot. Use a fresh result path;
existing experiments are not overwritten. The downloader requests needed members from the
official ZIPs, reuses verified files, retries transient HTTP failures and rejects existing
checksum mismatches. Reports are committed; full datasets, weights and enhanced audio are not.

The bundled demo concatenates eight pilot utterances with 10 ms edge fades and 350 ms gaps.
It was selected after the pilot and is a demonstration, not blinded evaluation evidence.
[Source files and modifications](../src/music_studio/ui/speech_demo/ATTRIBUTION.md).

Upstream: [GTCRN](https://github.com/Xiaobin-Rong/gtcrn) (MIT),
[DPDFNet](https://github.com/ceva-ip/DPDFNet) (Apache-2.0),
[Sherpa-ONNX exports and examples](https://github.com/k2-fsa/sherpa-onnx/tree/master/python-api-examples).

[Real UI / Codex / downloaded WAV / stereo inference checks](../benchmarks/results/next-cleanup-integration-2026-10-16.json)
retain the 80% CPU task, −16 LUFS preview, A/B event and unchanged adopted revision 3.
This is functional evidence, not an additional quality score.
