# Music Workbench roadmap / 路线图

[文档 / Documentation](README.md) · [平台设计 / Platform design](workbench-plan.md)

## 方向 / Direction

想法 → 导入、录音或生成 → 试听与适配 → 可编辑段落 → 混音 → 保存与分享。

Idea → import, record or generate → audition and fit → editable sections → mix → save and share.

每个模型后端应进入同一工程流程，提供来源、试听、明确采用、撤销与导出。深度 Agent 控制建立在这些工程操作之上。

Model backends share project operations, provenance, audition, explicit adoption, undo and export. Deep Agent control builds on these operations.

Music Workbench 专注新作品的制作；整曲分析由独立 Music Studio 维护。分轨、转写和音符提取接入时，应帮助用户继续创作。仓库、入口、数据和兼容约定见[产品边界](product-boundaries.md)。

Music Workbench focuses on making new music. Full-song analysis belongs to the independent Music Studio product. Separation, transcription and note extraction should help users continue creating. See [product boundaries](product-boundaries.md) for entries, data and compatibility.

## 当前可用 / Available in dev21

dev21 提供以下功能，安装版与源码按同一版本发布。The dev21 installer and source share the capabilities below.

- 多轨编排、采样乐器、鼓点、MIDI 编辑、段落与创作蓝图。Arrangement, instruments, grooves, MIDI editing, sections and creative blueprint.
- 本地录音、循环、节拍器、EQ/压缩/混响、音量曲线与交叉淡化。Recording, loops, metronome, effects, volume curves and crossfades.
- ACE-Step 生成/参考变奏/重绘、分轨、单旋律 MIDI、DSP 对拍与等响度候选比较。Generation/reference/repaint, stems, monophonic MIDI, DSP fitting and matched candidate A/B.
- WAV/MIDI、带音频的 MWB 工程、来源署名与恢复。WAV/MIDI, portable audio projects, credits and recovery.
- Windows 安装器、独立窗口、ACE-Step 自动配置、五步跟练与离线手册。Windows installer/window, ACE-Step setup, guided lesson and offline handbook.
- CPU/CUDA 工具包、RoFormer/Qwen 自动配置、逐片段处理、限时模型复用与工程位置还原；这些是可用性验证，不代表质量全面提升。CPU/CUDA packs, managed RoFormer/Qwen, selected-clip processing, bounded model reuse and timeline placement; execution checks do not establish across-the-board quality gains.
- 独立创作入口、素材编辑器品牌、旧书签兼容与返回工程链接。Dedicated creation entry, asset-editor branding, old bookmark compatibility and return-to-arrangement links.
- 跨轨片段成组、独立副本与历史；8 条一级总线、推子后发送和共享湿声混响。[使用方法 / Guide](groups-and-routing.md)。Clip groups, independent copies/history, eight one-level buses, post-fader sends and shared wet reverb.
- Basic Pitch ONNX 多音识别、试听、加入乐器轨编辑与导出。[实测与限制 / Evidence and limits](polyphonic-notes.md)。Editable polyphonic note estimates with a managed CPU pack.
- 《窗灯》32 小节创作、导出与 MWB 恢复验证。[案例 / Case study](creations/windowlight.md)。Windowlight: a 32-bar creation/export/restore case.

## 计划与验收 / Planned work and acceptance

以下是贡献方向，不是交付日期承诺。Planned work has no committed release dates.

| 优先级 / Priority | 工作 / Work | 对用户的价值 / Value | 验证方式 / Validation |
| --- | --- | --- | --- |
| 基础已完成 / Foundation delivered | 分组与段落 / Groups and form | dev20 已从 8 小节扩展至 32 小节，独立分组复制、撤销与恢复。Independent groups, copy, undo and recovery. | [验证 / Validation](preagent-validation.md)；继续观察真实用户编辑复杂工程的卡点。Observe complex-project editing. |
| 基础已完成，质量继续 / Baseline delivered, quality ongoing | 可编辑 AI 音符 / Editable AI notes | Basic Pitch 与 Transkun 已贯通，提供声部整理。Both backends and note-part simplification are integrated. | [五首参数对照 / Five-case comparison](polyphony-benchmark.md)；[钢琴六片段评测 / Piano comparison](piano-benchmark.md)已完成；仍需更广风格与人工修改量。Broader styles and correction effort remain. |
| 案例已完成 / Case delivered | 创作闭环 / Creation workflow | 《窗灯》完成生成、转音符、段落对比、总线与交付。Windowlight validates generation, editable notes, contrast, routing and delivery. | dev21《雨后的街灯》创作编辑已全程 UI 验证；仍需目标用户试用。UI-only creation validated; observed beginner trials remain. |
| 基础已完成 / Foundation delivered | 混音 / Mixing | dev20 已提供总线/发送；效果参数自动化、VST、同步叠录和延迟补偿仍未提供。Buses/sends delivered; FX automation, VST, overdubbing and latency compensation remain unavailable. | 路由数值、尾音、旁路、历史与实时音源不重载回归。Routing, tails, bypass, history and no-source-reload checks. |
| P1 | 本地 AI 交付 / Local AI delivery | dev15–18 已完成自动工具包和首台 CUDA 验证；扩展硬件覆盖与冷启动体验。Managed packs and first CUDA-host checks landed in dev15–18; broaden hardware coverage and improve cold startup. | [安装与工程衔接验证 / Setup validation](model-tools-validation.md)，再扩展全新 Windows 与 GPU 配置。 |
| P1 | 安装与首次创作可靠性 / Installation and first creation | 更多电脑能顺利完成安装、学习和导出；覆盖缺少 WebView2、受限网络、显示缩放与失败恢复。Broader hardware/network/display coverage and recovery. | 全新 Windows 环境与目标用户试用，记录卡点、完成率及恢复结果。Clean machines and observed user trials. |
| P1 | 更可靠的节拍适配 / Better timing fit | 变速音乐的局部修正与强拍辅助，减少手动对齐。Local timing and downbeat assistance. | 扩展风格与真值，报告首尾漂移和人工修改量。Style-specific drift and correction effort. |
| P2 | 候选与重绘 / Candidates and repaint | 延续已有模型复用，改善多候选管理、接缝试听和重绘上下文。Extend existing model reuse with candidate management, join audition and repaint context. | 控制冷/热启动条件；测 RAM/VRAM、取消/释放、恢复与盲听。Controlled timing, resources, recovery and listening. |
| P3 | 新的声音制作后端 / More sound tools | 音乐修复、音色转换、音效生成和本地检索，按许可与实用性引入。Restoration, timbre, sound effects and retrieval. | 授权固定素材、质量对照及完整试听/采用/恢复流程。Licensed comparisons and complete workflows. |
| 后续 / Later | 工作台 Agent 深度操作 / Deep workstation Agent control | 操作工程、轨道、音符、效果和模型，过程可检查。Reviewable project/track/note/effect/model actions. | UI 与 Agent 共用命令和历史；失败不损坏工程，采用可撤销。Shared commands/history and safe recovery. |

首个持续验收案例是：从空工程建立 8 小节，扩展为有段落变化的 32 小节作品，试听混音、导出，再从 MWB 恢复继续修改。模型数量与文件生成成功不能代替这个验收。

The recurring acceptance case starts empty, builds 8 bars, develops 32 bars with section changes, mixes/exports and restores MWB for further edits. Model counts and successful file generation do not replace this check.

## 模型接入要求 / Model requirements

隔离运行环境，固定版本与哈希；区分代码、权重和素材许可。每项能力分别报告质量、失败、加载/推理耗时、峰值 RAM/VRAM、离线运行与取消恢复。安装完成、推理成功和质量测量分别标记。

Isolate and pin runtimes; separate code, weight and asset licenses. Report quality, failures, load/inference time, peak memory, offline behavior and cancellation. Distinguish installation, inference and quality evidence.

[模型候选 / Model research](local-model-candidates.md) · [评测与版本记录 / Technical reference](technical-reference.md)
