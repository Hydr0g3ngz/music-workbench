# 用本地 AI 制作音乐 / Produce with local AI

[文档 / Documentation](README.md) · [模型与安装 / Models and setup](models.md)

把模型结果当作可继续制作的素材：先试听、选择，再编辑和混音。基础编排无需 Agent；当前模型不会自动接管整首作品。

Treat model outputs as material to audition, select, edit and mix. Basic arrangement needs no Agent; the current models do not automatically direct the complete production.

## 1. 写下创作意图 / Set a direction

打开「创作蓝图」，填写氛围、音色、动机与段落意图，选择结构草案。生成面板可读取已保存的 BPM、调性与段落上下文；先预览实际提示词。[编曲方法](arranging-methods.md)

Open **Creative blueprint**, set a mood, palette, motif and section intentions, then choose a structure sketch. Generation can use saved tempo/key and section context; preview the compiled prompt first. Blueprint/template assembly uses rules, while ACE-Step generates audio.

## 2. 生成并比较素材 / Generate and compare

在「AI 模型」生成短器乐草稿。已有 10–60 秒音频可做参考变奏；需要改变局部时使用重绘。完成后试听候选，再加入播放头或指定段落。[生成指南](music-generation.md) · [局部重绘](volume-and-repaint.md)

Generate a short instrumental in **AI models**, use a selected 10–60 s source for reference variation, or repaint a region. Audition before adding at the playhead or target section. [Generation](music-generation.en.md) · [Repaint](volume-and-repaint.md)

模型请求的调性、节奏或动机不保证被遵守。比较候选时使用 [等响度 A/B](material-fitting.md)，避免只因更响而选择。该比较听素材原音，不含轨道效果。

Requested key, rhythm or motifs are not verified compliance. Use [matched candidate A/B](material-fitting.md) to compare source audio without arrangement effects.

## 3. 拆解成可编辑声部 / Separate editable parts

选择音频 →「素材适配 / AI」，可用 Demucs 四声部或 RoFormer 人声/伴奏分离。需要旋律音符时对合适的单旋律声部运行 CREPE，再换音色或编辑音符。钢琴可选择 Transkun，其他独奏乐器可用 Basic Pitch 提取多音音符。采用保留时间关系与来源，支持撤销。[分轨](separation.md)

Select audio → **Make this material fit** for Demucs four-part or RoFormer vocal/backing separation. Apply CREPE to a suitable monophonic source, then edit notes or change instruments. Use Transkun for piano and Basic Pitch for other solo-instrument polyphony. Adopted parts retain timing/provenance and support undo. [Separation](separation.en.md)

分轨可能串音，CREPE 不能完整转录复音和声；导出 MIDI 也不会自动为音频轨生成乐谱。

Stems can leak, and CREPE cannot transcribe complete polyphonic harmony. MIDI export does not automatically score audio tracks.

## 4. 对拍与编排 / Fit and arrange

分析速度，人工确认参考拍；必要时选择半速/倍速或两拍校准，制作变速候选。用段落标记与跨轨复制组织材料，再用音量曲线、交叉淡化和局部重绘处理连接。

Analyze tempo, confirm a beat anchor, resolve half/double time or calibrate two beats, then create a fit candidate. Use markers/range copies for form, and curves/crossfades/repaint for joins. Tempo/key analysis and stretching are DSP; they need no new neural model.

[素材适配 / Material fitting](material-fitting.md) · [过渡 / Transitions](volume-and-repaint.md) · [循环 / Loop](timing.md)

## 5. 混音与交付 / Mix and deliver

调整声部音量、声像和效果，检查输出峰值/LUFS。导出 WAV 分享，导出 `.mwb` 保存编排、音频与署名。换电脑后恢复工程继续制作。[混音](mixing.md) · [工程导出](create-preview.md#保存与导出)

Balance levels, pan and effects, check output peaks/LUFS, then export WAV and an editable `.mwb` with audio/credits. Restore the project to continue on another computer. [Mixing](mixing.en.md) · [Project export](create-preview.en.md#save-and-export)

MWB 不包含模型权重、独立环境或完整任务库。生成与处理参数留在原工作区；完全复现采样与 DSP 建议使用相同软件版本。

MWB excludes weights, runtimes and the full task database. Generation/processing recipes remain in the original workspace. Use the same app version for consistent samples/DSP.

## 案例与扩展 / Case study and future work

可以打开 [《雨后的街灯》](creations/after-the-rain.md) 跟着编辑，或按 [《云隙电台》](creations/radio-through-the-clouds.md) 的配方组合生成、分轨与 MIDI。后续计划见 [路线图](workbench-roadmap.md)。

Open [After the Rain](creations/after-the-rain.md) to edit a ready-made project, or remake [Radio Through the Clouds](creations/radio-through-the-clouds.md) with generation, stems and MIDI. See the [roadmap](workbench-roadmap.md) for planned features.
