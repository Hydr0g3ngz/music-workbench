# 技术、评测与历史参考 / Technical and historical reference

[中文文档](README.md) · [English documentation](README.en.md) · [贡献 / Contributing](../CONTRIBUTING.md)

本文供贡献者与需要复现实验的读者使用。技术记录中的版本、设备、数据集与测试数量只适用于所述实验；当前功能以使用指南为准。

This index is for contributors and experiment reproduction. Versions, devices, datasets and test counts apply to the stated experiment, not every current installation.

## 模型与数据 / Models and data

- [支持状态 / Current support](models.md) · [模型候选 / Candidates](local-model-candidates.md) · [资源与存储 / Resources](audio-resources.md)
- [公开测试集与命令 / Dataset and commands](../benchmarks/README.md)
- [评测协议 / Protocol](benchmark-protocol.md) · [历史结果目录 / Result index](../benchmarks/results/README.md)
- [旋律候选对比 / Melody comparison](melody-next.md) · [Speech cleanup](speech-cleanup.en.md)
- [分轨对照 / Separation comparison](separation.md#可复现对比) · [素材适配 / Material fitting](material-fitting.md)

## 工作台版本验证 / Workstation verification

- [dev20 编排、多音音符、路由与打包 / Arrangement, polyphony, routing and packaging](preagent-validation.md)
- [多音参数开发评测 / Polyphonic parameter benchmark](polyphony-benchmark.md)
- [dev19 入口与工程兼容 / Entry and project compatibility](workbench-entry-validation.md)
- [教程、乐器、录音、混音与生成 / Lesson, instruments, recording, mixing and generation](feature-validation.md)
- [Windows 安装与 AI 配置 / Windows setup](windows-validation.md)
- [dev11 便携版 / Portable build](desktop-validation.md)
- [dev7 循环与节拍器 / Timing](timing-validation.md)
- [dev9 创作蓝图 / Blueprint](arranging-validation.md)
- [AI 制作案例 / Production case study](creations/radio-through-the-clouds.md)

## 兼容素材编辑器 / Compatibility asset editor

`next.html` 是单素材处理界面；与 `station.html` 的多轨工程不同。它保留转写、语音清理与实验 MCP/Codex 接口。完整工作台 Agent 操作仍在规划中。

`next.html` edits one asset and retains transcription, speech cleanup and experimental MCP/Codex tools. It is distinct from the `station.html` arrangement. Full workstation Agent control remains planned.

- [编辑器 / Editor](next-preview.md) · [模型与任务 / Models and tasks](next-models.md)
- [语音清理 / Speech cleanup](speech-cleanup.md) · [MIDI 评测 / MIDI evaluation](melody-next.md)

## 拆分前文档 / Pre-split archive

以下记录属于原 Music Studio 分析流程或拆分前设计，不是 Music Workbench 当前功能和安装说明。原产品在 [独立仓库](https://github.com/Hydr0g3ngz/music-studio) 维护。

These describe the original Studio analysis workflow or pre-split design. They are not current Workbench installation instructions.

| 类型 / Type | 文档 / Documents |
| --- | --- |
| 原 README / Old README | [中文](pre-split-readme.zh.md) · [English](pre-split-readme.en.md) |
| 原使用指南 / Analysis guides | [详细说明](usage.zh-CN.md) · [Quick start](legacy-quickstart.md) |
| 分析架构 / Analysis architecture | [Architecture](architecture.md) |
| 歌词研究 / Lyric studies | [v3](lyrics-v3.md) · [v4 中文](lyrics-v4.md) · [v4 English](lyrics-v4.en.md) |
| 初始基准 / Early baselines | [Pilot](benchmark-baseline.md) · [v2](benchmark-v2.md) |
| 原路线与研究 / Old plans | [路线图](roadmap.md) · [Roadmap](roadmap.en.md) · [优化研究](optimization-plan.md) |
| 验证 / Validation | [Engine](validation.md) · [UI](ui-validation.md) · [UI v2](ui-v2-validation.md) · [UI v4](ui-v4-validation.md) · [v0.1.2 release](release-validation.md) |

版本发布内容见 [更新记录](../CHANGELOG.md)。旧版本说明按当时行为保留；它们的安装包不包含后续新增功能。

See the [changelog](../CHANGELOG.md) for version history. Historical release notes describe their own builds and do not include later features.
