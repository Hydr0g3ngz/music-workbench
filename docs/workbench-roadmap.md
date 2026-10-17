# Music Workbench roadmap / 工作台路线图

2026-10-16 · Updated after two complete creation walkthroughs.

## 产品主线 / Main workflow

想法 → 导入/录音/生成 → 可试听素材 → 拆解与适配 → 段落编排 → 混音 → 可恢复交付。
Idea → import/record/generate → audition → separate/fit → arrange → mix → recoverable delivery.

先把平台和可编辑素材做好，再接 Agent；每项模型能力必须能试听、按时间采用、撤销、保存重开与导出。
Model count is not acceptance. Each capability needs audition, aligned adoption, undo, reopen and export.

## 已完成的基础 / Implemented foundations

dev11 补齐：音量曲线、线性/等功率交叉淡化、真实 ACE-Step 局部重绘与原位采用/撤销；Windows 基础免安装包、新手首页与首次创作提示。[音量与重绘实测](volume-and-repaint.md) · [启动说明](desktop-start.md)。

dev11 adds volume curves, crossfades, verified region repaint, portable basic runtime, Home and first-creation hints. AI environment installation and real novice testing remain separate work.

| 首作发现 / First-piece friction | 本轮结果 / Current result | 验证边界 / Evidence limits |
| --- | --- | --- |
| 逐音符数字编辑，完整配器依赖外部脚本。Per-note inspector work and external score authoring. | 拖动/拉长、框选/多选、复制粘贴、移调、量化、批量力度；调性/音阶提示。Direct/group note tools and scale hints. | 纯函数测试与实际浏览器编辑验证；尚未做零基础用户 10 分钟完成 8 小节的可用性实验。Novice usability still untested. |
| 秒/拍混用，段落组织和整首视图不足。Weak musical positioning/form. | 小节定位、段落标记、跨轨范围复制、适配整首。Bar positioning, sections, range copying, fit view. | 第二首 32 小节、6 段、9 轨；未注入外部完整乐谱。Second piece used UI operations. |
| 生成结果不能继续拆解或参考。Generation isolated from production. | 实际裁切音频参考变奏、Demucs 四声部、CREPE MIDI 采用；DSP 分析与独立变速变调。Reference generation, four parts, editable melody, DSP fitting. | 两次 ACE-Step、两次有效四分轨、一次有效贝斯转录实际运行；适配质量仍需更系统评估。Real inference is not a quality benchmark. |
| JSON 不含音频，缺少恢复入口和输出响度。Nonportable snapshots, weak output feedback. | `.mwb` 包含音频/编排/署名，工程页恢复；WAV 电平及可选 LUFS/真峰值。Portable projects and output measurements. | 第二首在新目录恢复，同版输出逐字节一致。Same-build fresh-workspace proof. |
| 中文 MIDI 导出失败并残留文件。Unicode MIDI failure. | UTF-8 导出/重新导入、旧 Latin-1 兼容与失败清理。Unicode and cleanup fixes. | 首作 737 音符与第二首中文段落/轨道导出均验证。Regression and real exports. |

## 接下来的顺序 / Next priorities

dev9 已将创作意图、段落发展方法与可预览的上下文生成接入实际任务。
它帮助组织素材，但不解决素材对拍、精确动机保留或自然过渡；以下 P1 顺序保留。
dev9 connects intentions and arranging methods to actual generation. Beat alignment,
exact motif retention and natural transitions still need the P1 work below.
[方法与限制 / Methods and limits](arranging-methods.md)。

dev10 已补人工参考拍校准、半速/倍速、两拍速度计算，以及同窗口 LUFS 候选比较。
下一步以自动化和段落过渡为先，拍点模型和局部时间修正继续独立评估。
dev10 adds manual beat fitting and matched candidate A/B; prioritize automation and transitions next.
[测量及边界 / Measurements and limits](material-fitting.md)。

| 优先级 / Priority | 工作 / Work | 原因 / Why | 验收 / Acceptance |
| --- | --- | --- | --- |
| P1 | 扩展节拍真值集、局部时间校准与自动强拍模型。Expand beat truth, local timing edits and learned downbeats. | dev10 已有人工参考拍与相同响度候选比较，仍无法解决变速音乐或不准确的输入。Manual fitting cannot solve varying tempo or incorrect input. | 按不同风格报告首尾漂移和人工修正量；没有弱候选自动移调。Style-specific drift and correction effort; no weak-key automatic pitch shift. |
| P1 | AI 准备向导、下载/磁盘/硬件检查、断点恢复；邀请零基础用户走完示例到导出。AI setup and first-use validation. | 基础包已免 Python，模型安装仍需要技术操作；尚未对青少年进行可用性验证。Model setup is still technical; novice usability is untested. | 无终端完成受支持模型配置；记录卡点、完成率与恢复结果。No-terminal setup and observed completion/recovery. |
| P1 | 段落整体移动、成组分轨过渡、突出 MIDI 当前裁切范围。Section moves, grouped transitions and active MIDI crop. | dev11 已有片段曲线与交叉淡化，但不会自动移动相关分轨。Clip transitions do not move grouped stems. | 8→32 小节可经界面编排，撤销和导出保持一致。Reversible form and matching export. |
| P2 | 可释放的模型驻留、多候选；扩展重绘上下文和边界试听。Releasable workers, candidates and richer repaint context. | 已实测局部重绘；加载仍占多数时间，听感需要独立评价。Repaint is verified; loading dominates and quality needs listening. | 冷/热耗时、取消/释放、RAM/VRAM、旧任务恢复和边界盲听。Controlled latency, recovery and listening tests. |
| P2 | Basic Pitch 多音转录、鼓转录；扩展乐器采样与总线/发送。Polyphonic/drum transcription, instruments, buses/sends. | 单旋律 CREPE 无法表达完整和声，现有采样与混音结构有限。Monophonic notes and limited sound/mix structure. | 固定音符真值测 F1/时值/音高与人工修改量，输出继续编辑。Quality and correction effort with editable outputs. |
| P3 | 音乐修复、音色转换、音效生成，按可用性与许可分批引入。Music restoration, timbre transfer, sound effects. | 开放扩展要服务完整创作流程；语音修复不能直接冒充音乐修复。Expansion needs production value and separate evaluation. | 授权固定素材、对齐试听、采用/撤销/重开/导出完整。Licensed workflow acceptance. |
| 之后 / Later | Agent 通过同一套工程/素材/任务/历史操作制作。Agent through the same project/asset/task/history operations. | 先确保基础操作可逆、稳定、可追溯。Stable reversible primitives first. | 提案、运行、试听、采用与撤销可检查，失败不破坏工程。Reviewable actions and safe recovery. |

本轮 160 Python / 56 Node 测试通过；第二首浏览器主输出捕获覆盖全曲。
捕获及电平测量不能替代听感评价。首次录音已有设备/电平/试听/恢复；同步叠录、预备拍和延迟校准仍待验证。
160 Python and 56 Node tests passed; actual browser capture covered the second piece.
Listening and novice usability remain untested. Overdub, count-in and latency calibration remain separate work.

## 模型平台与 benchmark / Model platform and benchmark

继续沿用独立环境、固定版本/哈希、代码/权重许可区分、安装/诊断/取消、离线检测。
区分已验证、实验性和候选；每个模块分别报告质量、失败率、加载/推理耗时、峰值 RAM/VRAM、CPU 回退及取消恢复。
创作验收增加外部工具依赖次数、人工修正量、完整交付与恢复；盲听反馈单列，不能以生成成功代替质量。

Keep isolated/pinned runtimes and separate code/weight licenses. Report quality, failures, load/inference,
memory, fallback and cancellation per module. Track external-tool dependence, correction effort and
delivery/restore; keep listening evidence separate from integration tests.

[AI 各阶段设计 / AI workflow](ai-production-workflow.md) ·
[第二首实走 / Second piece](creations/radio-through-the-clouds.md) ·
[首作原创 MIDI 源码 / First piece source](../examples/after-the-last-tram/compose.py)
