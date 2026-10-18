# Analysis-component evaluation results

These are engineering regressions on the pinned 26-case subset. See [the protocol](../protocol-v1.json), [model hashes](../model-provenance.json), method and decisions.

`baseline.json`, `balanced.json` and `text-priority.json` each account for all 26 cases. The latter two inherit unchanged, measured components; they are not fresh full-run speed tests. The two note decoders use the same hash-verified seed=0 pitch contours. Composition also checks identical source and vocal audio. Per-case metrics and provenance are included; raw audio, reference lyrics and prediction text are excluded.

`rejected-vocal-chunks.json` covers the seven real full songs. `diagnostic-beat-this-small0.json` covers five guitar clips and explicitly records known GuitarSet training overlap; it is blocked from default promotion by the comparison tool. The archived v2 experiment did not evaluate out-of-fold Beat This weights. Aggregate hardware-memory samples include other GPU activity and are not instantaneous model-only peaks.

The original unseeded pilot/baseline remains in the earlier report/history. These reports do not establish unbiased generalization, full-song source separation quality or performance on complex Mandarin mixes. Each data source retains its own license; these original aggregate measurements do not relicense upstream recordings or annotations.

## Lyrics v3

`lyrics-v3-small.json`, `lyrics-v3-turbo.json`, `lyrics-v3-qwen-vocals.json`, `lyrics-v3-qwen-source.json` and `lyrics-v3-heart.json` each account for 26/26 cases. All 19 lyric cases were recognized for each model/input candidate; seven non-lyric predictions are inherited and hash-verified. The optional-model reports then inherit that measured ASR text unchanged and apply the final conservative anchor matcher using verified small predictions. Their elapsed times cover that alignment ablation, not recognition plus alignment or a cold full pipeline.

The three `*-recognition.json` reports preserve the original Qwen vocal (cold processes), Qwen mix and Heart (shared batches) recognition runs, including their initial experimental alignment. They retain actual recognition provenance and memory data; their timing scope differs from the final CPU-only anchor ablation.

`lyrics-v3-summary.json` pools actual word onset errors to compute medians and P90; it never averages per-song quantiles. It reports text errors, timing coverage, partial/untimed sentences and the fraction of **all** reference words matched within 200ms separately. Its local report hashes refer to scored reports before publication/sanitization. The published per-case reports retain engine hashes and runtime versions.

`lyrics-v3-global-anchors.json` and `lyrics-v3-window-anchors.json` preserve earlier matching algorithms. The two forced-alignment reports preserve independent Qwen/Whisper experiments; their recognition text equals the Qwen candidate. The legacy-turbo Qwen alignment report uses unchanged v2 text; the unseeded turbo diagnostic predates the explicit CTranslate2 seed and is not the v3 control. `lyrics-v3-rejected-28s.json` has only an interrupted first attempt, no complete accuracy result. Nothing is silently removed from the comparison because it failed or regressed.

See lyrics v3 decisions and [protocol](../lyrics-v3-protocol.json). Qwen/Heart training membership is unverified. This is a small, previously used engineering suite, including only 64 Chinese characters; it is not an unseen-test leaderboard.

## Lyrics v4

`lyrics-v4-mir-small.json` and `lyrics-v4-mir-qwen-dual.json` each account for all 17 new Mandarin karaoke recordings. The former includes measured separation and small recognition; the latter inherits the same audio/separation and executes Qwen with two acoustic guides in a shared-model batch. Their cold/warm timing scopes differ. Hardware metadata is explicitly supplied by `hardware-local-20261015.json`; the exporter does not invent the author's hardware for other users' runs.

`lyrics-v4-summary.json` accounts for all 43 cases: 36 lyric cases re-scored on fixed Qwen text and cached guides, plus seven unchanged non-lyric cases. It separates dataset/language/split, pools actual onset errors, retains per-case regressions and includes descriptive cluster-bootstrap intervals. The MIR-1K manifest and split were frozen before inference. The independently measured small/Qwen recognition comparison is reported separately from the timing ablation. No inference-speed claim is made for CPU-only scoring.

`lyrics-v4-aligner-audit.json` is a three-case diagnostic of official raw-text versus tokenized Qwen aligner input, with no reference text supplied. It reports invalid spans, not alignment accuracy. Detailed token outputs remain local.

See v4 report for scope, Mandarin P90 regressions and product validation. Data and prediction text remain excluded; upstream data/model terms are not replaced by this repository's MIT license.
