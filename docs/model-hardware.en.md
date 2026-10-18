# Choose AI tools for your computer

[中文](model-hardware.md) · [Model setup](models.en.md)

Arrangement, instruments, recording, mixing and export need no dedicated GPU. Install AI tools only when needed. CPU processing works for some tasks, with longer waits for long material.

## Choose by task

| 工具 / Tool | 适合的用途 / Use | 安装和硬件 / Setup |
| --- | --- | --- |
| Basic Pitch | 独奏乐器转多音 MIDI / Single-instrument polyphonic MIDI | CPU；下载约 150–350 MB，预留 2 GB / CPU, 2 GB disk |
| 讲话清理 / Speech cleanup | 讲话录音降噪 / Reduce speech noise | CPU；下载约 150–300 MB，预留 1 GB / CPU, 1 GB disk |
| Demucs、CREPE、Whisper | 分轨、单旋律、转写 / Stems, monophonic MIDI, text | 可选 CPU 或 NVIDIA 工具包 / CPU or NVIDIA pack |
| Transkun | 钢琴专用多音 MIDI / Piano notes | 自动安装需 Turing 或更新 NVIDIA、4 GB 显存；可显式用 CPU / Managed CUDA pack, optional CPU inference |
| RoFormer | 人声与伴奏 / Vocals and backing | Turing 或更新 NVIDIA、4 GB 显存 / Turing+ NVIDIA, 4 GB VRAM |
| Qwen ASR + Aligner | 转写与逐字时间 / Text and word times | Ampere 或更新 NVIDIA、8 GB 总显存；运行前约 6 GB 空闲 / Ampere+, 8 GB total and about 6 GB free |
| ACE-Step | 文字生成、变奏和重绘 / Generation and variations | Ampere 或更新 NVIDIA、8 GB 总显存，预留 35 GB 磁盘 / Ampere+, 8 GB VRAM, 35 GB disk |

CUDA packs use Torch 2.10 / CUDA 12.8 and a compatible driver. Setup checks actual hardware and free memory. Reserve about 10 GB for Transkun, 12 GB for RoFormer and 24 GB for Qwen, including their separate runtimes. Selecting CPU does not shrink a CUDA pack into a lightweight CPU installation.

## Speed reference

Single-host measurements: Windows, Core Ultra 9 185H, RTX 4070 Laptop 8 GB, 32 GB RAM. Invocation times include the stated loading overhead; they are not full-song guarantees.

| Task | Input | Full invocation |
| --- | --- | --- |
| Basic Pitch CPU | 16 s AI piano | About 11.6 s |
| Transkun GPU FP32 | Same 16 s piano | About 18.3 s |
| Transkun CPU FP32 | Same 16 s piano | About 30.4 s |
| Demucs CPU / GPU | 30 s instrumental | About 49.6 / 9.1 s |
| CREPE CPU / GPU | 30 s instrumental | About 109.0 / 11.0 s |

New tasks may reload models; first-use imports can be slower. Trim long material and process the selected clip. Audition estimates and choose a backend suited to piano, another solo instrument or a separated stem.

## ACE-Step configuration

ACE-Step 1.5 Turbo uses about 2.39B main-network, 169M VAE and 596M text-encoder tensor elements. The downloaded BF16 checkpoints total about 6.32 GB, before runtime dependencies.

Low-VRAM and balanced modes quantize DiT decoder linear weights to INT8; other components remain BF16. This is partial quantization, not a fully INT8 model. Low-VRAM mode moves modules between RAM and GPU, so system RAM matters too.

Automatic selection uses free VRAM: low-VRAM at 4–10 GB, balanced at 10–18 GB, original precision at 18 GB or more. Setup still requires at least 8 GB total VRAM. Close other GPU applications if less than about 4 GB is free. Hardware coverage beyond the measured configuration remains limited.

A measured 20 s piano generation took about 65.5 s including loading. Results and resources vary with prompts, length and settings. Managed setup does not offer CPU music generation.

[Piano comparison](piano-benchmark.md) · [Polyphony settings](polyphony-benchmark.md) · [Hardware measurements](../benchmarks/results/local-hardware-2026-10-17.json)
