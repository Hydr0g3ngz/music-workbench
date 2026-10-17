# 从编曲方法到可操作流程 / Arrangement methods in the workflow

2026-10-16 · Development preview 0.2.0.dev9

主线：**创作意图 → 动机与音色 → 发展变化 → 段落组织 → 对比与打磨**。
这些方法是可修改的创作起点，不是通用规范或自动评分标准。

The workflow is **intention → motif and palette → development → arrangement → comparison and refinement**.
Methods provide editable starting points, not universal rules or an automatic music score.

[真实操作与模型测量 / Real workflow verification](arranging-validation.md)

## 依据与产品实现 / Sources and implementation

下表为独立概括与产品设计，不复制教程、乐谱或范例音频。
The table summarizes principles and our implementation; it reproduces no tutorial, score or example audio.

| 来源 / Primary source | 方法 / Principle | 当前落地 / Implemented | AI 的作用 / AI role |
| --- | --- | --- | --- |
| [Ableton Learning Music — Song structure](https://learningmusic.ableton.com/song-structure/song-structure.html) | 许多风格以 4/8/16 小节组织模式，但不是强制。Many styles organize patterns in four/eight/sixteen bars; this is optional. | 三种可预览的 4/4 结构草案，采用后可修改或撤销；替换现有标记需明确勾选。Three previewable sketches; editable, reversible, explicit replacement. | 目标段落范围随生成任务记录，按段落设置 10–60 秒支持范围内的时长。Pin target ranges and request supported section durations. |
| [Ableton Making Music — Dramatic Arc](https://makingmusic.ableton.com/dramatic-arc) | 用引入、发展、高潮与释放组织旅程；有些风格适合不同结构。Shape a journey through introduction, development and release; other forms remain valid. | 段落角色、可选 1–5 相对能量、段落意图。Roles, optional relative energy and intentions. | 提示词包含当前段落任务、前后段名称/角色；不会把能量等级当成响度指标。Condition on purpose and neighboring roles, never a loudness target. |
| [Berklee — Writing Melodies: 3 Simple Tools](https://online.berklee.edu/takenote/simple-tools-for-better-melodies/) | 重复建立动机，再从节奏、留白、音区等方向形成对比。Establish motifs through repetition, vary rhythm, space and register. | 蓝图保存贯穿作品的动机；生成任务可选建立、重复、发展、对比、收束、连接。Persist the recurring motif and choose a development purpose. | 同一蓝图进入文本生成和音频参考变奏；精确音符保留仍用 MIDI 编辑。Shared context for text/reference generation; exact note retention still needs MIDI. |
| [Ableton — Arranging as a Subtractive Process](https://makingmusic.ableton.com/arranging-as-a-subtractive-process) | 从丰富素材中逐步减去部分声部，形成空间与层次。Shape space by subtracting parts from rich material. | 使用既有跨轨范围复制、静音、剪辑和四声部采用；蓝图面板提供直接入口。Use range copy, mute, clip edits and four-stem adoption. | Demucs 拆出可继续编排的鼓/贝斯/人声/其他。Separate editable parts before subtractive arranging. |
| [iZotope — Reference tracks](https://www.izotope.com/en/learn/13-tips-for-using-references-while-mixing) | 对比时先匹配电平、一次关注一个元素。Match level and focus on one element at a time. | 面板内嵌试听方法；现有输出报告提供峰值/LUFS；工作台生成候选自动等响度 A/B 尚待实现。Embedded listening guidance and export measurements; automatic workstation candidate A/B is pending. | 后续建议应基于测量与可撤销参数，而不是把“更响”当成“更好”。Future assistance needs measurements and reversible settings. |

## 使用 / Use

1. 点击时间线上方的「创作蓝图」，填写作品意图、音色、动机、可选和声方向并保存。
   Open **Creative blueprint**, write an intention, palette, motif and optional harmony, then save.
2. 在「段落发展」预览结构草案，明确采用后编辑各段角色、预期能量与意图。位置和长度仍在「段落与调性」编辑。
   Preview/apply a structure in **Development**, then edit intentions. Timing stays in **Sections & key**.
3. 选择「保存并为此段生成」。填写本次素材描述，选择发展方式，预览实际提示词；准备好后再生成。
   Choose **Save & generate for section**, describe the material, choose its purpose and preview the actual prompt before queuing.
4. 文本生成先建立素材；已有 10–60 秒音频可选择参考变奏。参考音频裁切、哈希及原署名沿用既有机制。
   Text generation establishes material; selected 10–60 s audio can drive reference variation. Cropping, hashes and attribution are retained.
5. 完成后试听，加入播放头或原段落起点。加入段落只定位，保留全长，不自动变速、裁切或判定调性。
   Audition, then add at the playhead or original section start. Target placement retains the full clip and performs no automatic fitting.
6. 在「编排与打磨」查看各段片段覆盖、平均层数及标记留白/重叠，定位试听；选中音频可加 15 ms 边缘淡变。
   Review clip coverage, average layers and marker gaps/overlaps, locate sections, and optionally add 15 ms edge fades.

## AI 与规则的边界 / Rules and model boundaries

- 蓝图、模板、检查、提示词组装均为确定性规则；实际音频生成由本地 **ACE-Step 1.5 Turbo** 完成。本轮没有增加语言模型或 Agent，也没有把规则包装成模型推理。
  Blueprint/template/check/prompt assembly are deterministic; local **ACE-Step 1.5 Turbo** generates audio. No additional language model or Agent is implied.
- 开启蓝图时 BPM/调性来自已保存工程。预览和入队使用同一服务端组装器；任务固定用户原文、最终提示、蓝图、段落、前后段、发展方式、工程版本和上下文 SHA256。
  Enabled context uses saved project tempo/key. Preview and queue share a server compiler; tasks pin the original/compiled prompt, context, revision and hash.
- 工程修改不会改写排队任务。原段落被移动、改长或工程速度改变时，目标起点采用会拒绝；仍可在播放头采用。
  Later edits never rewrite queued jobs. Changed section bounds or tempo invalidate original target placement; playhead adoption remains available.
- 描述某个动机、速度或调性不代表结果符合条件；参数固定也不保证跨硬件逐样本复现。需要分析、试听、MIDI 修正与独立质量评估。
  Requested motifs, tempo and key are not verified compliance. Fixed parameters do not imply cross-hardware sample identity. Analyze, audition and correct.
- 片段覆盖统计忽略静音轨与非独奏轨，MIDI 只统计裁切范围内的音符；音频按整个片段计算，无法知道片段内是否静音，也不代表实际频谱密度。没有音乐质量分数。
  Coverage respects mute/solo and visible MIDI notes, but counts entire audio clips including silence. It measures neither spectral density nor artistic quality.
- 15 ms 淡变只处理边缘、保留更长的现有淡变，可撤销；不是跨片段 crossfade、音量自动化或段落过渡模型。
  Edge fades retain longer fades and are reversible; crossfades, automation and generated transitions remain separate work.
- 蓝图和段落目标随 `.mwb` 携带。任务完整记录保留在工作区数据库；工程包中的生成素材带来源及上下文哈希，不含完整任务历史或模型权重。
  Packs include intentions and source context hashes, not full task history or model weights.

## 后续 / Next

先解决生成素材的实用兼容性：拍点/强拍、半速/倍速、段落起拍、候选等响度比较；
再做音量自动化与真正的跨片段过渡。增加本地语言模型前，先验证它能否给出比这些规则更有用、
可检查和可撤销的建议，并测量用户修改次数与完成时间。

Next: beat/downbeat alignment, half/double-time choices and matched-level candidates;
then automation and actual transitions. Evaluate optional local language assistance against
these rules using correction effort, completion time and reviewable changes.
