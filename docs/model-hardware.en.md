# Local AI: hardware, speed and workflow

[中文](model-hardware.md) · [Model setup](models.en.md)

CPU execution is practical for speech cleanup and short transcription. Stems and monophonic transcription benefit substantially from a GPU. The current Windows ACE-Step configuration requires NVIDIA CUDA; CPU generation is not offered.

## Measurements

Measured on 2026-10-17: Windows x64, Core Ultra 9 185H, RTX 4070 Laptop 8 GB, 32 GB RAM. The private CPU pack uses Python 3.12.10 and Torch 2.5.1 CPU; the separate GPU pack uses Torch 2.10 CUDA 12.8. Both use the same model versions and algorithm parameters, with four CPU inference threads.

Each case starts a new process, matching the workstation queue. Time includes startup, imports, weight loading, inference and artifact writing. OS file caches were not flushed. The 30-second music fixture combines attributed factory instrument samples; speech uses the bundled 23.112-second VoiceBank-DEMAND example. These measure execution speed, not recognition/separation quality or full-song performance. A real-time factor below one means processing finished faster than the input duration.

| Task | Input duration | CPU completion | Sampled peak process RAM |
| --- | ---: | ---: | ---: |
| Demucs four stems | 30 s | 49.6 s | 1336 MiB |
| CREPE monophonic notes | 30 s | 109.0 s | 1191 MiB |
| Whisper small | 23.112 s | 16.6 s | 855 MiB |
| DPDFNet2 speech cleanup | 23.112 s | 11.3 s | 160 MiB |
| GTCRN speech cleanup | 23.112 s | 3.2 s | 112 MiB |

The private CUDA pack completed the identical frozen inputs in **9.1 s** (Demucs), **11.0 s** (CREPE) and **11.7 s** (Whisper). Torch peak allocations were about 553 MiB and 735 MiB for the first two. Whisper uses CTranslate2; a zero Torch allocation is not zero VRAM, so its VRAM is unmeasured. These are single trials, not a statistical ranking.

Installation smoke tests on a few seconds cannot establish practical throughput. Initialization, content, temperature and other applications affect latency. Do not extrapolate short fixtures linearly to complete songs.

## Exact ACE-Step configuration

Pinned ACE-Step 1.5 Turbo: source `ca1e85fe9430179831e6bc6be790c332190a3866`, model `19671f406d603126926c1b7e2adc169acbcade22`. Reading the safetensors headers gives:

| Component | Stored tensor elements (approximate parameters) | Weight file bytes | Storage dtype |
| --- | ---: | ---: | --- |
| Turbo generation network | 2,393,872,518 | 4,787,825,604 | BF16 |
| VAE | 168,695,426 | 337,431,388 | BF16 |
| Qwen3-Embedding text encoder | 595,776,512 | 1,191,586,416 | BF16 |

The three weight files total 6.32 GB / 5.88 GiB. Python, CUDA libraries, model code and retained downloads increase installation size. Qwen3-Embedding encodes prompts; this configuration has no 5Hz language model or AI arrangement planner.

The low-VRAM profile applies torchao `int8_weight_only` after loading, specifically to **DiT decoder linear weights**. The rest of the network, VAE and text encoder are not all INT8. Downloaded checkpoints remain BF16.

dev16 checks GPU architecture and current free VRAM before loading. Automatic setup uses CUDA 12.8 and requires Windows NVIDIA driver 570 or newer.

| Profile | Free VRAM policy | Execution |
| --- | --- | --- |
| Low VRAM | 4–10 GB | Decoder linear weights in INT8; stage-wise CPU offload |
| Balanced | 10–18 GB | Same INT8; generation network stays on GPU, other modules offload |
| Original precision | At least 18 GB | BF16, no quantization or CPU offload |

Automatic ACE setup also requires Ampere or newer and at least 8 GB total VRAM. Below 4 GB free, close other GPU applications first. Advanced generation settings can select a profile explicitly; insufficient memory is reported instead of silently changing it. These thresholds are resource policies, not universal compatibility guarantees for every GPU or 60-second task. Actual hardware validation currently covers the 4070 Laptop low-VRAM profile; the other policies have selection regression tests and still require physical-device validation.

One new 12-second, 8-step instrumental generation completed in 94.7 s: 78.7 s initialization/checks and 16.0 s generation/output. Torch peak allocated VRAM was about 3150 MiB, peak resident RAM 11,292 MiB, and peak private commit 17,947 MiB. Installation activity was present, so this is execution evidence rather than a controlled speed comparison. CPU offload needs substantial system RAM; 32 GB is the measured configuration. Workers exit after each task to release models, so each task pays loading costs.

## Integration audit

| Model | Purpose and result adoption | Evidence and limits |
| --- | --- | --- |
| ACE-Step | Text, reference variation, repaint → audition draft → adopt audio track → undo/export | Real generation; outputs audio rather than separately editable instrumental notes |
| Demucs | Two/four stems → audition → aligned source replacement or additional tracks | Real CPU/CUDA inference; separation does not compose new performances |
| Mel-Band RoFormer KJ | Vocals/backing → same aligned adoption workflow | Existing quality comparison; independent manual setup remains necessary |
| CREPE | Solo singing/humming/monophonic instrument → pitch/MIDI → editable sampled instrument notes | Public annotated-data evaluations; not reliable polyphonic whole-song transcription |
| Whisper small | Speech/lyrics → transcript → line corrections in detailed asset editor → TXT/LRC/SRT | Real CPU/CUDA execution; singing, backing and overlapping voices remain difficult |
| Qwen3-ASR-1.7B | Optional speech/lyrics transcription → same correction workflow | Manual environment; this task entry produces coarse segment times and does not automatically call ForcedAligner |
| DPDFNet2 | Speech cleanup → original/processed audition → add new track | Measured CPU execution and adjustable strength; may damage music/ambience |
| GTCRN | Lightweight speech cleanup → same adoption workflow | Measured CPU execution; internal 16 kHz limits high frequencies; experimental alternative |

The main workstation now passes device, transcription language and cleanup strength into real tasks. Processing still covers the **whole source asset**; adoption preserves the clip range. Shortening a timeline clip does not reduce model computation automatically. Transcript correction still opens **Details and editing** in the asset editor rather than an inline multitrack editor.

Beats, tempo, key, time/pitch, EQ, compression, reverb and volume curves use DSP. Blueprint and section-prompt compilation use rules. No hidden AI model performs those functions. CREPE stable/rest are decoder variants of one neural network.

Quality evidence: [melody evaluation](melody-next.en.md), [separation](separation.en.md), [speech cleanup](speech-cleanup.en.md). Successful installation/inference does not establish accuracy gains.

## Reproduce and extend

Run `scripts/benchmark_local_models.py` with an isolated interpreter, model directory, device and output directory; the development environment needs psutil. Use `--input-dir` to reuse identical WAV bytes in paired CPU/GPU runs. Machine-readable results: `benchmarks/results/local-hardware-2026-10-17.json`. Record driver/runtime versions, input hashes and actual devices. Developer GPU environments must not stand in for installer CPU results.

Next priorities: managed RoFormer/Qwen installation and alignment; processing selected clips only; releasable resident workers to reduce waits; and a complete humming → corrected MIDI → editable accompaniment → arrangement/export workflow. AI mixing, polyphonic transcription, controllable singing and deep Agent integration remain future work.
