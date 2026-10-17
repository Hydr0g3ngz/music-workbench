# 云隙电台 / Radio Through the Clouds

2026-10-16 · 64 秒 / seconds · 32 小节 / bars · 工程网格 / project grid 120 BPM · 9 轨 / tracks

## 创作动机 / Intent

把“云层之间时断时续的无线电信号”变成一段器乐草稿：先有模糊纹理，节拍进入，
中段留下空间，随后出现更明亮的变奏，最后让最初的信号回响。
制作方法是以 AI 音频为主体，再拆解、重组，并将部分声部转成可编辑音符。

A radio signal passes through cloud: texture, pulse, open space, brighter variation, then a final reply.
AI-generated audio forms the main material, separated and rearranged with an editable MIDI echo.
The arrangement combines generated audio with transcribed MIDI.

![工程 / Session](../images/cloud-radio-workbench-zh.png)

## 实际步骤 / Actual steps

| 步骤 / Step | 操作与目的 / Action and purpose |
| --- | --- |
| 1 · 定题 / Brief | 新建 120 BPM 工程，生成条件请求 A minor。Create a 120 BPM project and request A minor. |
| 2 · 主题 / Theme | ACE-Step 文本生成 32 秒，seed `20261017`，8 steps；提示 organic downtempo、四音符 pluck、Rhodes、圆润贝斯和 breakbeat、无歌声。Generated a 32 s instrumental theme. |
| 3 · 变奏 / Variation | 采用原稿为临时音频片段，再从参考变奏模式固定裁切后的实际音频。32 秒、seed `20261018`、参考强度 0.65，要求保留动机、改变日光质感。Pinned source audio for a reference-based variation. |
| 4 · 拆解 / Separate | 两份生成各跑一次 Demucs htdemucs 四声部分离，成为鼓/贝斯/vocals/other；在编排中将后两者命名为主题/纹理。These are estimated source roles, not verified isolated instruments. |
| 5 · 可编辑动机 / Editable echo | 对原稿贝斯跑 CREPE，采用 36 个单旋律估计音符，整体升两个八度、力度 72，换马林巴，裁出留白段。36 stored notes, 15 active note events in the exported bridge MIDI. |
| 6 · 编排 / Arrange | 用界面的小节定位和跨轨段落复制，组成下表 6 段；采用、重命名、裁切、淡化与复制通过编排工具完成。Use arrangement tools for adoption, naming, trims, fades and copies. |
| 7 · 混音 / Mix | 纹理轨降低电平、变奏轨微调；马林巴 −14 dB、右偏 0.15、氛围空间。尾段 3 秒淡出，主输出 +2 dB，采样峰值限制 −1 dBFS。Static edits, not automated mastering. |
| 8 · 交付 / Deliver | 实际从界面导出 WAV、MIDI、`.mwb`；保留原始生成、参数与处理记录。新目录恢复同版本工程后 WAV 字节完全相同。 |

| 段落 / Section | 小节 / Bars, end exclusive | 时间 / Seconds | 声部安排 / Arrangement |
| --- | --- | --- | --- |
| 寻频 / Tuning | 1–5 | 0–8 | 原稿主题与纹理渐入 / Theme and texture fade in |
| 穿云 / Signal | 5–13 | 8–24 | 原稿四声部 / Four parts of A |
| 留白 / Open sky | 13–17 | 24–32 | 主题/纹理与转录马林巴 / Texture, theme and transcribed marimba |
| 日光变奏 / Daylight | 17–25 | 32–48 | 参考变奏四声部 / Four parts of B |
| 回信 / Return | 25–29 | 48–56 | 原稿声部回归 / Return of A |
| 余波 / Afterglow | 29–33 | 56–64 | 主题与纹理淡出 / Theme and texture fade out |

## 实测 / Measurements

RTX 4070 Laptop 8GB，Windows，32GB RAM；模型为独立离线 worker。
以下是本机实际任务数据，不是跨模型质量 benchmark。每次重新加载模型；文件缓存状态并未控制，不能当作热驻留性能。

| 操作 / Operation | 加载 / Load | 生成或处理 / Generate or process | 总计 / Total | Torch CUDA allocated peak |
| --- | --- | --- | --- | --- |
| ACE-Step 主题 / Theme | 35.844 s | 11.593 s | 47.437 s | 3162 MiB |
| ACE-Step 参考变奏 / Variation | 32.547 s | 11.969 s | 44.516 s | 3335 MiB |
| Demucs 原稿 / A | — | 9.514 s | 9.514 s | 549 MiB |
| Demucs 变奏 / B | — | 9.176 s | 9.176 s | 549 MiB |
| CREPE 贝斯 / Bass | — | 10.361 s | 10.361 s | 734 MiB |

ACE-Step 进程驻留 RAM 峰值约 11.1–11.2 GiB，Windows 私有提交约 17.6–17.8 GiB。
这不是整机显存/RAM 峰值，不保证低内存设备可运行。完整模型参数、哈希与原始指标在本地资料包的 JSON 中。

- 总混音 / Mix: 44.1 kHz, stereo PCM24, 64.00 s; sample peak −1.00 dBFS, −17.71 LUFS, true peak −0.84 dBTP，零满幅样本 / no full-scale samples.
- 原稿速度 / Source tempo: librosa coarse 117.45 BPM；同一组估计节拍的恒速拟合为 120.56 BPM，残差 26.0 ms。拟合不是强拍或真实速度标注。
- 调性 / Key: C major 相关性 0.455、E minor 0.445；A minor 是更低候选。候选很接近，未声称符合提示词的调性，工程保持“未指定”。
- 播放 / Playback: 浏览器 Web Audio 主输出捕获覆盖全曲 64 秒，10 ms RMS 包络与离线导出相关性 0.987，未发现参考有声而捕获静音的窗口；128 个播放中时间样本最大步进偏差约 11 ms。
- 恢复 / Restore: 新目录恢复 10 份素材、9 轨，编排相同，导出 WAV SHA256 `4bb022c3120e17112af9f935d50a113d269513a4ff3c1924960928ba617fdbcf` 与原文件一致。
- 回归 / Regression: 160 Python + 56 Node tests passed; real note resize, marquee, group move and undo were exercised in a disposable QA project.

捕获发生在浏览器内部、操作系统输出之前，使用有损 Opus；包络和播放头测量不能证明所有瞬态都无异常。
本次没有直接听感或盲听评价，不把“模型运行成功”写成“作品好听”。
Capture taps browser audio before OS output, encoded with lossy Opus. These checks are not listening evaluation or a universal glitch guarantee.

## 此案例的限制 / Case-study limits

此案例使用 dev8。后续版本已加入 [对拍与等响度比较](../material-fitting.md)、[音量曲线、交叉淡化与重绘](../volume-and-repaint.md)。以下保留创作当时的限制，便于理解测量范围。

This case used dev8. Later builds added beat fitting, matched A/B, curves, crossfades and repaint. The observations below describe the original workflow.

1. **候选适配优先**：生成条件未必被遵守；全局 BPM/调性并不等于段落对齐。需要拍点/强拍与起拍校准、匹配音量的候选比较。
   Fit material first: estimated tempo/key do not establish downbeat alignment or compliance; add beat views and loudness-matched candidates.
2. **局部变奏与过渡**：参考变奏已经可用，但缺少段落内重生成、音量自动化、交叉淡化与总线/发送。
   Add validated region regeneration and practical transition/mixing tools.
3. **转录编辑仍需改善**：CREPE 是单旋律估计；裁切后卷帘仍显示完整原始音符范围，应突出当前可播放区域，再评估多音/鼓 MIDI。
   Focus the piano roll on the active crop, then evaluate polyphonic/drum transcription.
4. **模型等待**：本机两次生成超过三分之二时间用于加载；需要可释放的常驻 worker，独立测冷/热启动。
   Loading dominates these two tasks; benchmark releasable residency with controlled cold/warm conditions.

资源表仅列出用于最终编排的任务；排除三个未采用的额外处理任务。
The resource table covers tasks used in the final arrangement; three unused extra processing tasks are excluded.

来源：本地模型输出与软件自带 VCSL 马林巴；未使用其他歌曲作参考。
模型/采样许可与版本分别见[生成](../music-generation.md)、[素材库](../creation-library.md)。
生成音频和该案例工程未随源码分发；复现时可按上述参数生成自己的候选并沿段落表编排。需要现成可编辑工程，可使用 [入门示例](../first-sketch.md)。模型/素材许可与生成内容的具体使用条件分别适用。

The generated audio and this case project are not distributed with the source. Generate your own candidates with the recorded settings and arrange using the section table, or start with the [bundled lesson](../first-sketch.md). Model/asset terms apply separately.
