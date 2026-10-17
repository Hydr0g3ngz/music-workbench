# 音量、过渡与 AI 局部重绘 / Volume, transitions and region repaint

选中片段 → **音量与过渡**。双击图表添加点，拖动或输入秒数与 dB，再应用。渐强、留出空间和清除曲线都是可编辑的起点。相邻点按振幅线性插值；曲线相对片段起点，随移动、分割、裁剪、段落复制和变速调整。实时播放以约 400 Hz 采样包络，WAV 逐采样计算，极短变化会有插值差异。最多保存 128 点，界面新增限制为 64 点，为裁剪边界留余量。

Select a clip → **Volume & transitions**. Double-click to add points; drag or enter seconds/dB, then apply. Presets are editable. Amplitude interpolates linearly. Points follow moves, splits, trims, section copies and time fitting. Playback samples the envelope at about 400 Hz; WAV evaluates each sample, so very short changes can differ. Storage allows 128 points; the editor adds up to 64, leaving room for crop boundaries.

交叉淡化：选下一片段、重叠拍数与曲线，查看新起点后应用。**仅移动下一片段**，不自动移动同组分轨。等功率适合不相关声音，相关素材可能叠加变响；可尝试线性曲线，并检查输出、试听。当前曲线类型作用于参与片段的两端淡化。实时播放与 WAV 包含曲线，`.mwb` 保留编辑信息；MIDI 导出不含这组音频增益自动化。

Choose the next clip, overlap in beats and fade shape, then review its new start. **Only that next clip moves**, not associated stems. Equal-power can raise correlated material; try linear fades and audition. The shape applies to both fades on each participating clip. Playback/WAV include the curve; `.mwb` retains edits. MIDI does not include this audio-gain automation.

## 在过渡处使用 AI / AI at a transition

1. 选 10–60 秒音频片段，在过渡窗口点击“用 AI 重绘片段尾部过渡”，或在生成窗口选择“局部重绘”。
2. 设定相对片段的起止秒数，至少 0.5 秒；快捷入口默认最后 4 秒，可修改。
3. 修改描述。蓝图、乐器、动机、段落目标继续进入提示词，可预览实际输入。
4. 生成、试听；加入新轨比较，或“采用重绘”在原位替换。源片段已改变时拒绝替换，但保留候选。
5. 撤销恢复原片段。原音频、候选、参考哈希与上下文继续保留。

Select a 10–60 s audio clip, open region repaint, and choose a clip-relative region of at least 0.5 s. The shortcut proposes the last four seconds. Edit the prompt, generate and audition; blueprint/section intentions still condition generation. Add a comparison track or apply in place if the source is unchanged. Undo restores the original. Sources, candidates, hashes and pinned context remain available.

固定 ACE-Step 构建使用 `repaint` 与显式区域 mask。输入为不可变的原素材裁剪，未烘焙轨道效果、淡化或曲线；采用后继续使用原混音设置。模型生成上下文后，工作台只拼回选区，选区内边缘做 0.1 秒线性过渡。**选区外保留原始 44.1 kHz float 采样**，不依赖模型保证。API 可设拼接过渡 0–0.25 秒；界面固定 0.1 秒。音乐连贯与和声符合度仍需试听。

The pinned ACE-Step build uses `repaint` with an explicit region mask. Input is an immutable dry crop before effects/fades/automation; adoption keeps those mix settings. Only the selected region is spliced back, blending inside its edges for 0.1 s. **Outside 44.1 kHz float samples are preserved by the workbench.** The API allows a 0–0.25 s blend; the UI uses 0.1 s. Musical continuity and harmonic compliance still need listening.

## 实测 / Validation

- 既有 16 秒本地 AI 素材，重绘 6–10 秒，真实 ACE-Step 推理。4070 Laptop、8 步、INT8/CPU offload：加载 56.797 秒，生成 18.296 秒，峰值显存 3326 MiB。
- 最终候选选区外逐采样完全一致；选区内 RMS 差 0.248255，只证明发生变化。浏览器原位采用、撤销和重做通过。
- 合成夹具检查边界；真实 WAV 检查曲线，误差小于 `3e-7`。曲线的工程包恢复和撤销通过。
- [基准记录](../benchmarks/results/repaint-dev11.json)。单次验收没有盲听质量或风格遵循分数，资源数据不是最低硬件承诺。
- [完整播放验证](../benchmarks/results/volume-playback-dev11.json)：30.889 秒带曲线与交叉淡化的浏览器输出，10 ms RMS 与 WAV 的相关系数 0.993665，无额外静音窗。[启动与交付验收](desktop-validation.md)。

The real 16 s fixture was repainted from 6–10 s. On an RTX 4070 Laptop, eight INT8/offloaded steps took 56.797 s loading and 18.296 s generation, peaking at 3326 MiB VRAM. Outside samples were identical. In-place adoption and undo/redo passed in the browser. Synthetic boundary tests and actual WAV-envelope/portable-project tests passed. These are not listening-quality results or minimum hardware requirements.

Upstream: [pinned inference implementation](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/acestep/inference.py). 编曲来源与方法见 [arranging-methods.md](arranging-methods.md)。
