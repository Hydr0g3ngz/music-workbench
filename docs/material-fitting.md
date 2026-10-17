# 素材对拍与候选比较 / Beat fitting and candidate comparison

2026-10-16 · Development preview 0.2.0.dev10

让生成或导入的音频能够进入同一首作品：**分析 → 人工确认参考拍 → 制作适配候选 → 等响度试听 → 采用 / 撤销**。
Tempo analysis and stretching use DSP. No additional neural model or Agent was added.

![对拍校准 / Beat fitting](images/material-fit-zh.png)

![AI 素材等响度比较 / Matched AI material comparison](images/material-ab-zh.png)

## 对拍校准 / Beat fit

1. 选中音频片段，打开「素材适配 / AI」运行速度分析。报告内可直接打开「对拍校准」；也可以从时间线上方打开并手填已知 BPM。
   Select audio and run material analysis, then open **Beat fit** from its report or the toolbar.
2. 在当前片段波形中选择你确认的一拍，或输入其**源文件秒数**。白线为估计拍点；紫色参考网格从所选拍展开。
   Choose a beat by ear or enter its **source-file time**. Estimated beats are white; the tempo grid expands from your anchor.
3. 可选择半速 / 倍速解释。若估计不准，展开“两拍校准”，填写较晚一拍及两拍之间的间隔数。例如第 1 拍至第 17 拍为 16 个间隔。
   Resolve half/double-time ambiguity or calibrate from two known beats and their interval count.
4. 指定所选拍要落到第几小节。预览展示速度比、片段起点和时长；参考拍之前的弱起会保留。如果弱起超出工程开头，应移动目标或先裁切。
   Choose its target bar. The preview retains pickup audio and reports timing; an out-of-range pickup requires a later target or trimming.
5. 制作候选。完成后，先在「候选 A/B」试听，再在任务里采用适配结果。当前片段被修改、移除或工程 BPM 改变时不能直接采用旧对拍任务。
   Create a candidate, compare, then adopt. Changes to the source clip or project tempo invalidate replacement.

对拍模型为恒定速度，4/4 小节坐标；**没有自动强拍检测**。BPM 或参考拍错误仍会导致错位。
自由速度、速度变化和模型生成的节奏漂移，可能无法用单一速度比解决。工作台不根据弱调性候选自动移调。
这些结果只是可以继续编辑的 DSP 候选；不会保证保持复杂瞬态或音乐质量。

This fits a single constant tempo on a 4/4 grid, **without automatic downbeat detection**.
Free timing, tempo changes or generated drift may need local timing edits. There is no automatic pitch change
from an uncertain key estimate. Phase-vocoder transients may smear.

## 候选 A/B / Candidate A/B

- 从工程音频片段、已完成的生成草稿、关联处理任务的音频中选择 A 与 B。
  Choose arrangement clips, completed generated drafts or linked processing outputs.
- A/B 起点按**当前片段内的秒数**填写，与对拍面板的源文件秒数不同。每侧可单独移动起点；试听窗口取两侧可用范围的共同长度，0.4–60 秒。
  Offsets here are **seconds within the selected clip**, not source-file time. Windows share the same available duration, 0.4–60 s.
- 原片段与它的对拍候选成对选择时，可一键把两侧起点设到已确认的参考拍。它只对齐起点，不能让不同时速的后续节奏保持同步。
  Pairing an original with its beat-fit task offers an anchor shortcut. It aligns the starting point, not subsequent beats at different tempi.
- 两侧窗口独立测量 integrated LUFS，匹配到较低的共同目标，只衰减，同时给预览保留至少 −1 dBTP 的测量余量。
  Integrated LUFS is measured per window. Matching only attenuates, preserving a measured ceiling at or below −1 dBTP.
- 切换 A/B 继承当前试听时间；切换响度匹配和监听音量不重设位置。后台任务刷新不重新绑定音源。切换采用 HTML 音频播放，不是无缝 crossfade。
  A/B retains the preview time. Matching, monitoring and task refresh do not reload sources; switching is not a seamless crossfade.
- 静音、低于门限、极短窗口或缺少 `pyebur128` 时明确禁用响度匹配，仍可原音比较。不会用 RMS 冒充 LUFS。
  Unmeasurable audio or missing `pyebur128` disables matching explicitly. Raw comparison remains available; RMS is not substituted.
- 比较的是素材原音，**不含片段/轨道增益、淡变、效果器、声像或主输出**。匹配增益只作用于监听，不写回工程，不改变原素材。
  This compares **source audio before arrangement gain, fades, effects, pan and master processing**. Matching never changes the project.
- 预览音频按内容哈希缓存；准备和下载均检查归属及输入/输出哈希。后续编辑工程时必须按新版本重新准备。
  Previews use immutable content-keyed caching with ownership and integrity checks. Project edits require preparing with the new revision.

## 实测 / Verification

独立测试工程 `82a2193550e44173`（`outputs/benchmark/material-dev10`）：浏览器导入授权自制节拍音，
运行分析、两拍校准、120 BPM 对拍任务、试听、采用、撤销与重做；还比较了上一轮 ACE-Step 的 16 秒主题和参考变奏。
这些是工作流验收样本，不是新完成作品或模型音质排名。

The independent fixture used browser import, actual DSP tasks, calibration, A/B, adoption and history.
It also compared the earlier real ACE-Step theme and variation. These are workflow fixtures, not music-quality rankings.

| 项目 / Check | 结果 / Result |
| --- | --- |
| 源音频真值 / Source truth | 100 BPM，首拍 0.37 s，12 s stereo / 44.1 kHz；带弱起。 |
| 对拍参数 / Alignment | 120 BPM，速度比 1.2；参考拍落到第 3 小节 / 4 s，片段从 3.691667 s 开始、时长 10 s。 |
| 实际音频 / Rendered timing | 最近脉冲峰值最大误差 22.03 ms；首尾漂移 9.48 ms。峰值位置包含声码器瞬态变化。 |
| 等响度复测 / Remeasured matching | 衰减后的文件 −37.769 / −37.787 LUFS，差约 0.018 LU；仅此固定样本。 |
| 实际浏览器 / Browser | 两个音源各一次加载；中途切换、匹配开关、完整播放；没有任务刷新触发重载。 |
| AI 音乐 / AI material | 既有主题 / 变奏窗口约 −15.93 / −14.84 LUFS；均完成匹配试听，无艺术质量评级。 |

时间基准可复跑（需安装 librosa 推理依赖）：

```sh
python scripts/benchmark_material_fit.py --output outputs/benchmark/material-fit
```

阈值：本固定脉冲样本最大峰值误差 <40 ms，首尾漂移 <20 ms；不是全部风格的保证。
本地原始验证证据：`outputs/benchmark/material-fixtures-dev10/verification.json`。
自动测试还覆盖无效边界、静音、峰值余量、跨工程访问拒绝、候选损坏、版本冲突、
参考变奏/处理结果的比较、对拍采用时 BPM 变化、撤销与原素材保持。

The reproducible pulse regression checks <40 ms peak error and <20 ms endpoint drift on this fixture only.
Tests also cover bounds, silence, headroom, ownership, corruption, revisions, candidate types and undo.

167 项 Python 测试、64 项前端测试通过；安装后的 wheel 验证覆盖对拍预览与候选比较。
原有工程行、音频引用和撤销历史逐项对照保持一致。
167 Python and 64 frontend tests passed. Installed-wheel checks cover fit preview and candidate A/B;
all pre-existing project rows, audio references and undo history were unchanged.
[固定时间基准结果 / Fixed timing result](../benchmarks/results/material-fit-dev10.json)

## 后续 / Next

将下一轮重点放在可撤销的音量自动化与真正的跨片段过渡；再研究局部时间校准、
自动强拍模型和候选批量评估。支持模型要以对拍真值、音乐听感与操作修改量验证。

Next: reversible volume automation and actual transitions; then local timing correction,
learned downbeats and candidate evaluation with timing truth, listening and correction effort.
