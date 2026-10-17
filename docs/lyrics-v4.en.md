# Lyrics benchmark v4

> Historical reference for the Studio analysis workflow or a pre-split build. Start with [current Workbench documentation](README.en.md). The analysis product is maintained in [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Commands and measurements below apply to the stated historical version.

[中文完整报告 / Full per-case report](lyrics-v4.md) · [Suite and commands](../benchmarks/README.md)

The suite has **43 cases**: 26 prior component regressions and 17 new Mandarin
MIR-1K karaoke recordings. Of the new recordings, 8 are development and 9 are
confirmation cases, grouped before inference by singer and lyric overlap.
No new manual annotation was produced. Character boundaries come from the
[ASRU 2023 authors](https://github.com/navi0105/LyricAlignment), commit
`1c39cd0369ce7dc55fa45277b59215b333d3a817`.

## Text recognition

On the 9-recording confirmation split (1113 reference characters), Whisper small
CER was **45.2830% (504/1113)** and Qwen3-ASR 1.7B CER was **14.6451% (163/1113)**.
Across all 17 new cases the corresponding values were **43.3415%** and **13.1695%**.

The paired singer/lyric-cluster bootstrap CER difference (Qwen minus small) was
**−30.6379 percentage points**, descriptive 95% interval **[−36.1726, −25.3046]**.
There are only 8 confirmation clusters; this is not a broad generalization claim.

## Timing with unchanged text

Dual acoustic guides use small-model timings first and turbo only for missing,
monotonic exact text matches. The Qwen text remains unchanged; unmatched text is
kept with sentence timing. Multi-character acoustic units are not divided into
fabricated character timestamps.

| Metric | Small guide | Dual guides |
| --- | ---: | ---: |
| English, 7 full-song regressions: matched onset coverage | 71.6179% | 78.8391% |
| English: correct text and onset within 200ms / all timed reference words | 52.8336% | 59.1408% |
| English: conditional onset MAE | 0.3664s | 0.27794s |
| English: conditional onset P90 | 0.5583s | 0.52431s |
| Mandarin confirmation: matched onset coverage | 39.8922% | 55.7951% |
| Mandarin confirmation: correct and within 200ms / all timed references | 26.2354% | 35.3998% |
| Mandarin confirmation: conditional onset MAE | 0.2520s | 0.28421s |
| Mandarin confirmation: conditional onset P90 | 0.616365s | 0.713276s |

Mandarin coverage improved, but conditional timing tails worsened. Dual guides
remain optional. Report coverage and the end-to-end 200ms score together with
conditional timing error; evaluating only the matched easy words is misleading.

The paired cluster bootstrap difference for Mandarin confirmation's 200ms score
was **+9.1644 points**, descriptive 95% interval **[6.9306, 11.7872]**.
Both bootstrap checks use 10,000 samples and seed 20261015.

## Runtime scope and limits

The 17-case Qwen/dual batch took **270.299s** for **1173.660s** of audio, with a
whole-GPU 1Hz observed peak of **5051MiB** on RTX 4070 Laptop 8GB. This was a warm
batch with inherited separation, not a cold end-to-end pipeline or an isolated
process memory measurement. Do not compare it to full-analysis startup timings.

These are small engineering checks across different recording domains. Karaoke
recordings do not establish commercial-master accuracy; pretraining overlap is
unknown. Existing full-song regressions have already informed development.
The independent forced-aligner audit found invalid or zero-length outputs and
does not support a universal alignment improvement claim.

See the [full report](lyrics-v4.md) for per-case regressions, the aligner audit,
source hashes, model/runtime pins and reproduction commands. Frozen manifest
bytes and confirmation assignments must remain unchanged. Dataset audio,
reference text and recognition transcripts are not redistributed.
