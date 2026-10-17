# AI throughout production / AI 嵌入制作流程

2026-10-16 · Development preview 0.2.0.dev10

主线：一个想法 → 一组可比较的素材 → 可编辑的声部 → 段落编排 → 混音 → 可恢复交付。
每一步都保留原素材、参数和撤销入口。先把这些操作做好，再向 Agent 开放同一组操作。

The workflow is idea → comparable material → editable parts → sections → mix → recoverable delivery.
Retain originals and parameters; expose the same reversible operations to Agent later.

| 阶段 / Stage | 目前可用 / Available | 下一步 / Next | 如何验收 / Acceptance |
| --- | --- | --- | --- |
| 构思 / Brief | 可编辑作品意图、音色、动机、和声方向；段落角色/相对能量/意图进入实际提示词。Editable blueprint and section intentions enter generation. | 先验收这些规则是否降低修改量，再评估本地语言模型辅助。Measure correction effort, then optional local language assistance. | 预览与入队条件一致；任务固定上下文/工程版本/哈希；手动试听符合度。Preview/queue parity, pinned context and audition. |
| 素材 / Material | ACE-Step 文本生成与参考变奏；所选音频实际裁切后固定引用。Text generation and cropped-audio reference variation. | 多候选并列试听、相同响度比较、可取消的常驻 worker；局部重生成需先验证上游支持。Candidate comparison, releasable residency, validated region regeneration. | 同 seed/素材版本可追溯；报告加载与生成耗时、RAM/VRAM。Traceable inputs and separate load/generation/memory metrics. |
| 拆解 / Deconstruct | RoFormer 人声/伴奏、Demucs 四声部；一次采用并保留时间与撤销。Two/four-part separation with aligned adoption. | 比较适合纯音乐的多乐器模型，处理漏音与复杂混音。Compare instrumental separation and leakage. | 固定授权混合音及真值声部，质量/耗时/显存分别报告。Licensed mixture/stem fixtures, separate quality/runtime/memory. |
| 音符 / Notes | CREPE 单旋律 MIDI 入轨；可拖动、框选、移调、量化、改力度。Editable monophonic transcription. | 首先评估 Basic Pitch 的和弦/多音转录，再评估鼓转录。Evaluate Basic Pitch polyphony, then drums. | 标注音符 F1、时值与音高误差；比较修改次数，不能把检测值当乐谱真值。Note F1/timing/pitch and correction effort. |
| 适配 / Fit | 波形/估计拍点、参考拍校准、半速/倍速、两拍 BPM、可撤销变速候选。Waveform, manual anchors, half/double-time, two-beat BPM and reversible fitting. | 局部时间校准、自动强拍模型评估。Local timing correction and learned downbeat evaluation. | 固定脉冲样本最大峰值误差 22.03 ms、首尾漂移 9.48 ms；不代表通用精度。Fixture peak error/drift, not general accuracy. |
| 编排 / Arrange | 段落标记、跨轨复制、小节定位、结构草案、意图/布局对照与边缘淡变。Sections, copying, structure sketches, layout observations and edge fades. | 音量自动化、段落移动与真正的边界交叉淡化。Automation, section moves and actual crossfades. | 不写代码把 8 小节变为 32 小节，能单步撤销；不把轨道层数当作音乐质量。Develop 8→32 bars with coherent undo; no quality score from layer counts. |
| 录音与修复 / Record & restore | 本地录音；Next 素材编辑器已有可选 GTCRN/DPDFNet 语音降噪。Recording and optional speech cleanup in Next. | 把处理后的录音顺畅送回制作轨道；音乐去噪/去混响需要独立评估。Connect cleanup to creation; separately evaluate music restoration. | 原音/处理音对齐试听，保留下载恢复；语音效果不冒充音乐效果。Aligned audition and recovery; distinguish speech from music. |
| 混音 / Mix | EQ、压缩、混响、峰值保护、输出测量；素材候选同窗口 LUFS A/B。DSP effects/output measurement and equal-window source candidate LUFS A/B. | 总线/发送、自动化；整工程参考比较。Buses/sends, automation and whole-mix referencing. | 素材 A/B 不含轨道效果；盲听、峰值/动态/频谱与撤销独立验证。Source A/B excludes track effects; separate listening and measurement. |
| 交付 / Deliver | WAV、MIDI、署名、`.mwb` 音频工程包及恢复。Audio/MIDI/credits and portable projects. | 任务配方随包携带、缺少模型/采样的诊断；之后支持 Agent 批处理导出。Portable task recipes, dependency diagnostics, then Agent export. | 全新目录恢复同版工程，编排与总混音一致。Fresh-workspace restore with the same build and matching mix. |

## 使用入口 / Where to use it

新增「创作蓝图」贯穿构思、段落发展与编排打磨；可保存并直接为目标段落生成。
见 [编曲方法到工作流 / Arrangement methods](arranging-methods.md)。

新增「对拍校准」与「候选 A/B」：[操作与基准 / Usage and regression](material-fitting.md)。

1. 「AI 模型」生成；模式可选文字草稿或所选音频的参考变奏。完成后试听，再加入工程。
   Generate in **AI models**; choose text or reference variation, audition, then adopt.
2. 选择音频片段 →「素材适配 / AI」→ 分析、四轨拆解、旋律 MIDI 或独立变速变调。
   Select audio → **Make this material fit** → analysis, four stems, melody or time/pitch.
3. 「处理任务」中试听与采用。分析仅展示报告，不会自动改 BPM/调性；模型采用可撤销。
   Audition/adopt in **Tasks**. Reports do not automatically change tempo/key; adoption is reversible.
4. 「段落与调性」设置标记、按小节复制所有轨道的范围；「适配整首」查看完整结构。
   Use **Sections & key** for markers and range copying; **Fit song** shows the complete form.
5. 导出「便携工程」。换目录/电脑后在「工程 → 恢复便携工程」导入 `.mwb`。
   Export **Portable project**, then restore `.mwb` from **Projects** in another workspace.

工程包包含当前素材、编排、来源署名；不包含模型权重、已完成/排队任务数据库或独立模型环境。
内置乐器由软件自带；要复现完全相同的采样与 DSP，使用同一软件版本。
MIDI 导出仅含乐器音符，不会把音频声部自动转成全曲乐谱。项目暂限 10 分钟。

Packs contain current assets, arrangement and credits, not model weights, task databases or runtimes.
Factory instruments ship with the app; use the same build for identical sampling/DSP.
MIDI contains instrument notes, not automatic full-score transcription of audio. Projects currently cap at ten minutes.

## 模型与 DSP 边界 / AI and DSP

[ACE-Step](https://github.com/ACE-Step/ACE-Step-1.5)、
[Demucs](https://github.com/facebookresearch/demucs)、
[torchcrepe](https://github.com/maxrmorrison/torchcrepe) 已在本次作品实际运行。
[librosa](https://github.com/librosa/librosa) 分析/变速变调和 libebur128 测量属于 DSP，不标成 AI。
[Basic Pitch](https://github.com/spotify/basic-pitch) 是下一阶段评估对象，此处不声称已接入。

ACE-Step, Demucs and CREPE ran on the actual piece. librosa and libebur128 are DSP/measurement.
Basic Pitch is a proposed next evaluation, not an implemented capability. Existing pinned source/weight versions
remain documented in [generation](music-generation.en.md) and [models](next-models.en.md).

不把模型数量、生成成功或请求的调性当作质量证明。
第二首实走的调性候选接近，因此工程没有自动标成提示词要求的 A 小调。
详见[创作记录与验证边界](creations/radio-through-the-clouds.md)。

Model count, successful generation and requested key do not establish quality.
The second piece has close key candidates, so its project key remains unspecified.
