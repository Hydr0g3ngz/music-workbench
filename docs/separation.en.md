# Separation into arrangement

[中文](separation.md)

Separate imported/generated audio into vocals and backing, audition and adopt aligned tracks, then continue arranging and mixing. Choose Demucs or optional Mel-Band RoFormer KJ; originals are retained. See [AI workflow](ai-production-workflow.md) for four-part Demucs separation.

![Separation audition and aligned arrangement](images/create-separation-en.png)

## Use

1. Select an audio clip, open **Models**, check either separator, then run it.
2. Cancel from **Tasks** if needed. Processing does not change the arrangement.
3. Audition vocals or backing. Auditions cover the clip range captured when the task was submitted.
4. **Replace clip with stems** adds both aligned tracks and removes the original clip in one reversible edit, avoiding doubled playback.
5. Continue arranging, mixing and exporting WAV. One Undo restores the original clip; Redo restores both stems.

From dev18, only the selected clip is processed. Replacement preserves session position, duration, gain and fades; its new source offset starts at zero. Older whole-asset tasks retain their original offset.
New tracks copy the original track's gain, pan, mute, solo and effects. Nonlinear effects such as compression can sound different when applied to separate stems.
If the source clip changes or disappears, replacement is rejected. Undo those changes or add individual results instead.
Individual **Add track** inserts the full result at the current playhead without replacing anything.

## Optional setup

dev17 Windows builds offer automatic setup in **AI tools → Vocals & backing · RoFormer**; see the [guide](qwen-and-separation.en.md). The following instructions are an advanced source setup option.

From the repository root using Python 3.11/3.12:

```powershell
python scripts/setup_separation.py
```

Creates a separate environment with PyTorch 2.5.1 CUDA 12.4, required inference dependencies, pinned source and approximately 913 MB of weights.
Weights are not included in release ZIPs. Setup requires network access and additional disk space; startup/inference never download.
Use `--runtime-python <prepared-python>` to check and reuse an existing environment without installing packages into it.
For CPU wheels use `--torch-index-url https://download.pytorch.org/whl/cpu`. Inference respects the workbench CPU/Auto setting; CPU can be slow.

Setup writes `.artifacts/separation-runtime.json`. To use another location, set `MUSIC_STUDIO_SEPARATION_CONFIG` to its absolute path and restart.
Only local configuration selects runtime paths; HTTP/Agent requests cannot choose executable code or download URLs.
An owned worker loads the model and releases it after completion/cancellation. Separation and music generation share the workspace queue lock.

## Reproducibility and limits

- [Pinned MSST source](https://github.com/ZFTurbo/Music-Source-Separation-Training/tree/6fdad13686bb7e84d029ec66f9dbe76e65c93ebf), MIT. Training dependencies are not installed wholesale.
- [Pinned KJ checkpoint](https://huggingface.co/KimberleyJSN/melbandroformer/tree/ac9b0614ab3cd7f77219e18ba494dfd93956c348), model card states MIT. Weights are downloaded separately.
- SHA-256: `87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e`.
- Original 8 s window / 50% overlap; inference batch reduced from 4 to 1. CUDA autocast, CPU FP32, no compilation or TTA.
- Model vocals plus residual backing (`input − vocals`); aligned FLOAT WAV, original gain, no independent normalization.
- Frame count, rate, channels, finite values and output checksums are validated. Outputs publish together.
- This RoFormer backend outputs vocals/backing only; use Demucs for four parts. Stems can still contain leakage.
- Up to 10 minutes per task. Memory depends on hardware and input; batch 1 is not a fixed VRAM guarantee.

## Benchmark

Uses the two frozen public MUSDB7 previews in `benchmarks/suite-v1.json`. No manual labels added.
Checks source hashes and reports vocals/backing SI-SDR, inference/task time, Torch allocator peak and mixture reconstruction error.

```powershell
$env:PYTHONPATH = "src"
python scripts/benchmark_separation.py --data <dataset-root> --python <model-python> --model mel-band-roformer-kj --model-dir <model-cache> --output <new-output-directory>
```

Run `--model demucs-htdemucs` with the Demucs interpreter on the same inputs for comparison.
Two seven-second excerpts do not establish general superiority or full MUSDB scores. Respect dataset terms; reference audio is not redistributed.

### Local results (2026-10-16)

Windows, RTX 4070 Laptop 8 GB, Python 3.12.4; RoFormer used Torch 2.5.1+cu121.
Upstream's newer `set_priority` keyword is incompatible with Torch 2.5.1. The adapter selects upstream's legacy SDPA branch; weights are unchanged.

| Preview                            | Demucs vocals / backing SI-SDR | RoFormer vocals / backing SI-SDR |
| ---------------------------------- | ------------------------------ | -------------------------------- |
| AM Contra — Heart Peripheral       | 10.74 / 14.21 dB               | 13.30 / 16.35 dB                 |
| Angels In Amplifiers — I'm Alright | 11.16 / 13.18 dB               | 13.99 / 15.70 dB                 |

Torch peak: approximately 549 MiB for Demucs and 2003 MiB for RoFormer, excluding CUDA context and other processes.
Processing time including model loading: 21.1/9.2 s versus 19.7/20.2 s. Cache states were not controlled, so these do not establish a speed advantage.
Both reconstruct the mixture with approximately `2.98e-8` maximum error.

The complete bundled 45 s licensed song also passed overlap-window processing in 25.2 s, approximately 2040 MiB Torch peak.
A 30 s clip starting at source offset 3 s was placed at timeline 2.5 s; actual audition, paired replacement and Undo/Redo were checked.
No independent reference stems were used for this song; it validates workflow/alignment, not separation quality.
See [machine-readable results and failures](../benchmarks/separation-local-20261016.json). No blind listening study was conducted.
