# Music Workbench roadmap / 路线图

[文档 / Documentation](README.md) · [平台设计 / Platform design](workbench-plan.md)

## 方向 / Direction

想法 → 导入、录音或生成 → 试听与适配 → 可编辑段落 → 混音 → 保存与分享。

Idea → import, record or generate → audition and fit → editable sections → mix → save and share.

每个模型后端应进入同一工程流程，提供来源、试听、明确采用、撤销与导出。深度 Agent 控制建立在这些工程操作之上。

Model backends share project operations, provenance, audition, explicit adoption, undo and export. Deep Agent control builds on these operations.

## 当前可用 / Available in dev14

- 多轨编排、采样乐器、鼓点、MIDI 编辑、段落与创作蓝图。Arrangement, instruments, grooves, MIDI editing, sections and creative blueprint.
- 本地录音、循环、节拍器、EQ/压缩/混响、音量曲线与交叉淡化。Recording, loops, metronome, effects, volume curves and crossfades.
- ACE-Step 生成/参考变奏/重绘、分轨、单旋律 MIDI、DSP 对拍与等响度候选比较。Generation/reference/repaint, stems, monophonic MIDI, DSP fitting and matched candidate A/B.
- WAV/MIDI、带音频的 MWB 工程、来源署名与恢复。WAV/MIDI, portable audio projects, credits and recovery.
- Windows 安装器、独立窗口、ACE-Step 自动配置、五步跟练与离线手册。Windows installer/window, ACE-Step setup, guided lesson and offline handbook.

## 计划与验收 / Planned work and acceptance

以下是贡献方向，不是交付日期承诺。Planned work has no committed release dates.

| 优先级 / Priority | 工作 / Work | 对用户的价值 / Value | 验证方式 / Validation |
| --- | --- | --- | --- |
| P1 | 本地 AI 交付 / Local AI delivery | dev15 首批 CPU 工具包已完成；继续补齐 RoFormer、Qwen 的图形化配置和硬件验证。First CPU packs landed in dev15; finish RoFormer/Qwen setup and hardware coverage. | [安装与工程衔接验证 / Setup validation](model-tools-validation.md)，再扩展全新 Windows 与 GPU 配置。 |
| P1 | 八小节创作流程 / Eight-bar creation workflow | 哼唱 → 音符修正 → 可编辑伴奏候选 → 编排导出。Humming → corrected notes → editable accompaniment candidates → arrangement and export. | 测量音符误差、人工修正量、候选采用率，以及首次完成 30–60 秒作品的耗时。Measure note errors, corrections, candidate adoption and time to a first piece. |
| P1 | 安装与首次创作可靠性 / Installation and first creation | 更多电脑能顺利完成安装、学习和导出；覆盖缺少 WebView2、受限网络、显示缩放与失败恢复。Broader hardware/network/display coverage and recovery. | 全新 Windows 环境与目标用户试用，记录卡点、完成率及恢复结果。Clean machines and observed user trials. |
| P1 | 分组编排与过渡 / Grouped arrangement | 移动段落时保留相关声部、淡变和相对位置；突出 MIDI 当前裁切范围。Move related stems together and show active MIDI crops. | 经界面从 8 小节扩展至 32 小节，撤销、重开、导出保持一致。UI-only form development with matching history/export. |
| P1 | 更可靠的节拍适配 / Better timing fit | 变速音乐的局部修正与强拍辅助，减少手动对齐。Local timing and downbeat assistance. | 扩展风格与真值，报告首尾漂移和人工修改量。Style-specific drift and correction effort. |
| P2 | 更短模型等待与候选管理 / Model latency and candidates | 可释放的驻留 worker、多候选、边界试听和更丰富重绘上下文。Releasable workers, candidates and repaint context. | 控制冷/热启动条件；测 RAM/VRAM、取消/释放、恢复与盲听。Controlled timing, resources, recovery and listening. |
| P2 | 更丰富的可编辑声部 / Editable parts | 评估 Basic Pitch 单件乐器多音转录、更多采样与总线/发送。Evaluate single-instrument polyphonic transcription, instruments and buses/sends. | 固定音符真值测 F1、时值和音高误差；比较实际修改量。Note metrics and correction effort. |
| P3 | 新的声音制作后端 / More sound tools | 音乐修复、音色转换、音效生成和本地检索，按许可与实用性引入。Restoration, timbre, sound effects and retrieval. | 授权固定素材、质量对照及完整试听/采用/恢复流程。Licensed comparisons and complete workflows. |
| 后续 / Later | 工作台 Agent 深度操作 / Deep workstation Agent control | 操作工程、轨道、音符、效果和模型，过程可检查。Reviewable project/track/note/effect/model actions. | UI 与 Agent 共用命令和历史；失败不损坏工程，采用可撤销。Shared commands/history and safe recovery. |

## 模型接入要求 / Model requirements

隔离运行环境，固定版本与哈希；区分代码、权重和素材许可。每项能力分别报告质量、失败、加载/推理耗时、峰值 RAM/VRAM、离线运行与取消恢复。安装完成、推理成功和质量测量分别标记。

Isolate and pin runtimes; separate code, weight and asset licenses. Report quality, failures, load/inference time, peak memory, offline behavior and cancellation. Distinguish installation, inference and quality evidence.

[模型候选 / Model research](local-model-candidates.md) · [评测与版本记录 / Technical reference](technical-reference.md)
