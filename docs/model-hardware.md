# 选择适合电脑的 AI 工具

[English](model-hardware.en.md) · [安装模型](models.md)

基础编排、乐器、录音、混音和导出无需显卡。AI 工具按需安装；CPU 能完成部分任务，但等待时间会随素材长度和电脑配置增加。

## 按任务选择

| 工具 / Tool | 适合的用途 / Use | 安装和硬件 / Setup |
| --- | --- | --- |
| Basic Pitch | 独奏乐器转多音 MIDI / Single-instrument polyphonic MIDI | CPU；下载约 150–350 MB，预留 2 GB / CPU, 2 GB disk |
| 讲话清理 / Speech cleanup | 讲话录音降噪 / Reduce speech noise | CPU；下载约 150–300 MB，预留 1 GB / CPU, 1 GB disk |
| Demucs、CREPE、Whisper | 分轨、单旋律、转写 / Stems, monophonic MIDI, text | 可选 CPU 或 NVIDIA 工具包 / CPU or NVIDIA pack |
| Transkun | 钢琴专用多音 MIDI / Piano notes | 自动安装需 Turing 或更新 NVIDIA、4 GB 显存；可显式用 CPU / Managed CUDA pack, optional CPU inference |
| RoFormer | 人声与伴奏 / Vocals and backing | Turing 或更新 NVIDIA、4 GB 显存 / Turing+ NVIDIA, 4 GB VRAM |
| Qwen ASR + Aligner | 转写与逐字时间 / Text and word times | Ampere 或更新 NVIDIA、8 GB 总显存；运行前约 6 GB 空闲 / Ampere+, 8 GB total and about 6 GB free |
| ACE-Step | 文字生成、变奏和重绘 / Generation and variations | Ampere 或更新 NVIDIA、8 GB 总显存，预留 35 GB 磁盘 / Ampere+, 8 GB VRAM, 35 GB disk |

CUDA 工具包使用 Torch 2.10 / CUDA 12.8，需要兼容驱动；自动配置按实际显卡和空闲显存检查。Transkun 约预留 10 GB、RoFormer 12 GB、Qwen 24 GB 磁盘，包含各自的独立环境。选择 CPU 不会把已安装的 CUDA 工具包变成小体积 CPU 包。

## 速度参考

以下为 Windows、Core Ultra 9 185H、RTX 4070 Laptop 8 GB、32 GB RAM 的单机结果。时间包含所述调用中的加载成本，不能按比例当作整首歌的耗时承诺。

| 任务 | 输入 | 完整调用时间 |
| --- | --- | --- |
| Basic Pitch CPU | 16 秒 AI 钢琴 | 约 11.6 秒 |
| Transkun GPU FP32 | 同一 16 秒钢琴 | 约 18.3 秒 |
| Transkun CPU FP32 | 同一 16 秒钢琴 | 约 30.4 秒 |
| Demucs CPU / GPU | 30 秒器乐 | 约 49.6 / 9.1 秒 |
| CREPE CPU / GPU | 30 秒器乐 | 约 109.0 / 11.0 秒 |

新任务可能再次加载模型，首次导入也可能更慢。长曲可先裁短，再处理选中的片段。模型结果先试听；钢琴、多音乐器与混音应分别选择合适的后端。

## ACE-Step 配置与显存选项

当前使用 ACE-Step 1.5 Turbo。下载的主网络约 2.39B、VAE 约 169M、文本编码器约 596M，权重合计约 6.32 GB，存储为 BF16；完整安装还包括运行环境。

生成窗口可以选择节省显存、均衡或原始精度。节省显存与均衡方案对 DiT 解码器线性权重做 INT8 量化，其他组件仍为 BF16；它不是全模型 INT8。节省显存方案按阶段在内存和显卡之间移动模型，因此也需要足够系统内存。

自动选择参考空闲显存：4–10 GB 使用节省显存，10–18 GB 使用均衡，18 GB 以上可用原始精度。自动安装仍要求至少 8 GB 总显存。低于约 4 GB 空闲时应先关闭其他占用显卡的程序；不同方案的全硬件覆盖仍有限。

已测 20 秒钢琴生成约 65.5 秒（含加载）；资源与质量取决于提示、时长和配置。当前自动配置不提供 CPU 音乐生成。

[钢琴评测方法](piano-benchmark.md) · [多音参数比较](polyphony-benchmark.md) · [原始硬件数值](../benchmarks/results/local-hardware-2026-10-17.json)
