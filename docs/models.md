# 本地模型：支持状态与安装

[English](models.en.md) · [文档目录](README.md)

模型是可选组件。采样乐器、MIDI、录音、编排、效果器与导出不需要神经网络权重。

**dev21** 提供七个独立处理工具包，ACE-Step 单独配置。模型不包含在基础安装器中；根据素材和硬件按需安装。

| 能力 | 当前后端 | 安装方式 | 使用入口 |
| --- | --- | --- | --- |
| 文字生成、参考变奏、局部重绘 | ACE-Step 1.5 Turbo | Windows 首页 **AI 自动配置**；源码也可用安装脚本 | [生成](music-generation.md) · [重绘](volume-and-repaint.md) |
| 人声/伴奏分离 | Mel-Band RoFormer KJ | AI 工具管理 → 人声与伴奏 | [安装与使用](qwen-and-separation.md) · [分轨指南](separation.md) |
| 两声部/四声部分离 | Demucs htdemucs | AI 工具管理 → 分轨、旋律与转写 | [工作流](ai-production-workflow.md) |
| 单旋律 MIDI | CREPE | 与 Demucs 共用自动工具包 | [工作流](ai-production-workflow.md) · [评测](melody-next.md) |
| 钢琴多音 MIDI | Transkun 2.0.1 V2 FP32 | AI 工具管理 → 钢琴多音音符 | [使用与限制](piano-notes.md) · [评测](piano-benchmark.md) |
| 单乐器多音 MIDI | Basic Pitch 0.4.0 ONNX CPU | AI 工具管理 → 多音音符 | [使用与限制](polyphonic-notes.md) · [参数评测](polyphony-benchmark.md) |
| 转写与歌词改字 | Whisper small | 分轨、旋律与转写工具包；详细改字在素材编辑器 | [素材编辑器模型](next-models.md) |
| 转写与字词时间 | Qwen3-ASR-1.7B + ForcedAligner-0.6B | AI 工具管理 → 语音、歌词与逐字定位 | [安装与使用](qwen-and-separation.md) |
| 讲话降噪 | DPDFNet2、实验性 GTCRN | AI 工具管理 → 清理讲话录音 | [语音清理](speech-cleanup.md) |

## 分轨、旋律、转写与语音清理

从首页或工作台模型面板打开 **AI 工具管理**，选择需要的工具包，点击 **下载并安装**。软件准备独立 Python 与依赖，校验权重，并对自带样本执行离线推理；通过后才启用使用入口。无需系统 Python、终端或管理员权限。

- **分轨、旋律与转写**：CPU 版 Torch 2.5.1、Demucs、CREPE 与 Whisper small，预计下载 1–2 GB，预留 6 GB。还包含 librosa 速度/调性分析与变速变调；这些属于 DSP。
- **清理讲话录音**：sherpa-onnx、DPDFNet2 与 GTCRN，预计下载 150–300 MB，预留 1 GB。用于讲话录音，处理完整音乐可能损伤乐器。
- **钢琴多音音符**：Transkun，独立 Torch 2.10 / CUDA 12.8、FP32，下载约 3–5 GB、预留 10 GB；默认使用 NVIDIA GPU，可显式选择 CPU。[硬件与边界](piano-notes.md)。
- **多音音符**：Basic Pitch ONNX、独立 CPU 环境，预计下载 150–350 MB，预留 2 GB。不安装 Torch 或 TensorFlow；可同时提取和弦音符，结果需人工核对。
- **NVIDIA 加速工具包**：独立的 Torch 2.10 / CUDA 12.8 环境，预计下载 3–5 GB，预留 10 GB。需要 Turing 或更新的 NVIDIA GPU、至少 4 GB 显存和 570 或更新驱动；安装逐项执行真实 CUDA 推理。
- **人声与伴奏 · RoFormer**：独立 CUDA 环境，预计下载 4–6 GB，预留 12 GB 磁盘；需要 Turing 或更新的 NVIDIA GPU、至少 4 GB 总显存。
- **语音、歌词与逐字定位 · Qwen**：ASR 与对齐模型按阶段加载，使用 BF16；预计下载 10–13 GB，预留 24 GB 磁盘。需要 Ampere 或更新的 NVIDIA GPU、至少 8 GB 总显存；运行前另检查至少约 6 GB 空闲显存。逐字定位不会修正识别错词，详见[使用指南](qwen-and-separation.md)。
- CPU 与 CUDA 工具包支持 Windows x64，可以共存；工作台可选择设备，显式配置的解释器仍优先。降噪与 DSP 使用 CPU。ACE-Step 的 GPU 条件独立计算。
- 安装可暂停、重试，保留已完成下载；关闭软件会停止它启动的安装子进程。存放于 `%LOCALAPPDATA%\MusicWorkbench\AI\tools`，与应用及工程分开。

安装后点击 **在工作台使用**，导入录音并选中音频片段，在模型列表运行处理。结果先试听，再加入轨道；CREPE 结果可作为音符加入乐器轨。转写结果的 **详细结果与编辑** 支持修改识别文字。

**检查当前环境** 用于检测缺失依赖或损坏权重，**修复安装** 会重新检查和准备工具。显式配置的旧推理环境继续优先使用，无需搬动已有模型。

[硬件要求与速度参考](model-hardware.md)

## ACE-Step 自动配置

打开首页 **AI 自动配置**，按提示检查电脑、准备环境、下载模型并完成生成测试。准备成功后，回工作台生成素材；完成后先试听，再采用。

- Windows x64；Ampere 或更新的 NVIDIA GPU、至少 8 GB 总显存和 570 或更新驱动。生成前按空闲显存选择 INT8 卸载、INT8 常驻或 BF16。
- 至少 35 GB 可用磁盘，首次下载约 8–12 GB，需要网络。
- 已验证的硬件为 RTX 4070 Laptop 8 GB、32 GB RAM；其他硬件的可用性与速度可能不同。
- 暂停或失败后可重试，复用已校验缓存。模型和环境默认放在 `%LOCALAPPDATA%\MusicWorkbench\AI`。

## 高级配置与兼容界面

已有 RoFormer 或 Qwen3-ASR 手动环境可以继续使用；显式配置的解释器或分轨配置优先。需要定制时可使用源码安装脚本。不同模型使用隔离环境，不要合并不同版本的 Torch 依赖。

`next.html` 是保留的单素材编辑器，供语音处理、转写和详细结果操作使用；其模型文档中的 Next 环境不是 Windows 安装版基础功能的前置条件。

Basic Pitch、Transkun 已接入工作台。Beat This、DiffSinger、CLAP 等研究或评测候选不等于可从工作台直接使用。完整选型与许可见 [候选调研](local-model-candidates.md)。

代码与权重分别适用其许可，具体修订、哈希和测量见各模型指南。环境检查和下载完成不代表音乐质量；输出需试听与核对。
