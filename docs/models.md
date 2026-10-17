# 本地模型：支持状态与安装

[English](models.en.md) · [文档目录](README.md)

模型是可选组件。采样乐器、MIDI、录音、编排、效果器与导出不需要神经网络权重。

| 能力 | 当前后端 | 安装方式 | 使用入口 |
| --- | --- | --- | --- |
| 文字生成、参考变奏、局部重绘 | ACE-Step 1.5 Turbo | Windows 首页 **AI 自动配置**；源码也可用安装脚本 | [生成](music-generation.md) · [重绘](volume-and-repaint.md) |
| 人声/伴奏分离 | Mel-Band RoFormer KJ | 手动安装独立环境 | [分轨指南](separation.md) |
| 两声部/四声部分离 | Demucs htdemucs | 手动配置推理环境 | [推理环境](next-models.md) · [工作流](ai-production-workflow.md) |
| 单旋律 MIDI | CREPE | 与 Demucs 共用可选推理环境 | [工作流](ai-production-workflow.md) · [评测](melody-next.md) |
| 转写与歌词改字 | Whisper small、可选 Qwen3-ASR | 兼容素材编辑器，Qwen 使用独立环境 | [素材编辑器模型](next-models.md) |
| 讲话降噪 | DPDFNet2、实验性 GTCRN | 兼容素材编辑器内单独下载权重，CPU 推理 | [语音清理](speech-cleanup.md) |

## ACE-Step 自动配置

打开首页 **AI 自动配置**，按提示检查电脑、准备环境、下载模型并完成生成测试。准备成功后，回工作台生成素材；完成后先试听，再采用。

- Windows x64；兼容 NVIDIA 驱动，至少 8 GB 显存。
- 至少 35 GB 可用磁盘，首次下载约 8–12 GB，需要网络。
- 已验证的硬件为 RTX 4070 Laptop 8 GB、32 GB RAM；其他硬件的可用性与速度可能不同。
- 暂停或失败后可重试，复用已校验缓存。模型和环境默认放在 `%LOCALAPPDATA%\MusicWorkbench\AI`。

## 手动配置与兼容界面

RoFormer、Demucs、CREPE 等尚未全部提供软件内自动环境安装。其脚本需要源码与 Python；请按对应指南操作，完成后重启工作台。不同模型使用隔离环境，不要合并不同版本的 Torch 依赖。

`next.html` 是保留的单素材编辑器，供语音处理、转写和详细结果操作使用；其模型文档中的 Next 环境不是 Windows 安装版基础功能的前置条件。

Beat This、Basic Pitch、Transkun、DiffSinger、CLAP 等研究或评测候选不等于可从工作台直接使用。完整选型与许可见 [候选调研](local-model-candidates.md)。

代码与权重分别适用其许可，具体修订、哈希和测量见各模型指南。环境检查和下载完成不代表音乐质量；输出需试听与核对。
