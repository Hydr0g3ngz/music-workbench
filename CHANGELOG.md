# Changelog / 更新记录

## 0.2.0.dev7 — Loop and metronome / 循环与节拍器

Custom beat-based loop ranges, selected-clip/whole-arrangement shortcuts, a visible ruler range,
and a live metronome with level and bar accents. Timing settings autosave with undo/redo.
Loop cycles share decoded buffers and effect graphs, scheduled against the audio clock;
WAV/MIDI exports remain full arrangements without clicks or repetitions.
新增自定义循环区间与节拍器，支持所选片段、完整编排快捷设置，随工程保存并可撤销。
节拍器开关与音量调整不重载编排；循环复用已解码音频与效果器。旧工程按默认设置读取。
后台长时间阻塞仍可能造成漏播；同步叠录、预备拍与延迟校准尚未实现。
详见 [中文指南](docs/timing.md) / [English](docs/timing.en.md)。

## 0.2.0.dev6 — Workbench recording / 本地录音

Input selection, live level meter, mono PCM WAV capture, audition and explicit adoption at the playhead.
Stop/cancel release devices; failed saves retain downloads; retry cannot duplicate a take. Undo/redo and export supported.
独立工作台新增录音、试听与入轨。当前无同步叠录或延迟补偿，见 [录音说明](docs/recording.md)。

## 0.2.0.dev5 — Separation into arrangement / 分轨进入编排

Optional pinned Mel-Band RoFormer KJ in an isolated offline worker. Audition task audio without
reloading on refresh; replace the source clip with both aligned stems in one undoable edit.
Retains position, trims, fades and originals. Changed clips or damaged/incomplete results are rejected.
Two frozen MUSDB7 previews improve vocal SI-SDR by 2.56/2.83 dB over Demucs; this is not a full-set claim.
The bundled 45 s song passed real processing and browser adoption, approximately 2040 MiB Torch peak.

新增可选本地 Mel-Band RoFormer、人声/伴奏试听和一键对齐替换；原素材保留、一次撤销。
修复处理结果总是放到时间零点的问题，单独加入放在当前播放头。固定测试片段与完整授权示例实测，
新旧模型并存；安装与推理环境隔离。详见[分轨指南与实测](docs/separation.md) / [English](docs/separation.en.md)。

## 0.2.0.dev4 — Mixing / 实时混音

Live fixed-order track EQ, compression and reverb, four editable presets, a smooth A/B bypass,
and optional stereo-linked master sample-peak limiting. Effects autosave and undo with sessions;
WAV includes tails. Worklet and export kernels share tested DSP semantics, with an actual
Chromium/server WAV comparison. Existing sessions default to dry; Classic and Next are retained.
Seeking rebuilds effects state; this is not true-peak mastering, automation, recording or VST support.

新增三段 EQ、压缩、混响、四组预设、原声 A/B 和主输出采样峰值限制；试听中调参不重载音频。
效果随工程保存并可撤销，WAV 包含尾音。125 项 Python / 37 项 Node 检查通过，真实浏览器与
导出 WAV 最大逐采样误差约 1.49×10⁻⁷。定位/恢复会重建效果状态，限制器不是 True Peak。
详见[混音指南](docs/mixing.md) / [English](docs/mixing.en.md)。

## 0.2.0.dev3 — Create / 音乐制作开发预览

A multitrack creation workspace with a unified transport, reversible clip/track edits,
a mixer and WAV/MIDI export. Adds 23 credited CC0 samples, eight editable GMD drum grooves,
MIDI import and pitch/timing/velocity editing. Optional isolated ACE-Step 1.5 Turbo generates
drafts to audition and explicitly adopt; one 12s instrumental passed on an 8GB CUDA GPU.
Windows checkpoint loading avoids full-file mmap commit reservation. Pinned setup,
provenance, diagnostics and bilingual guides are included. Effects, recording, modern
separation/transcription and full creation acceptance remain incomplete. Classic and Next
entry points remain available; no automatic migration of old songs.

新增独立多轨制作界面、采样乐器/鼓点、MIDI 导入与音符属性编辑，支持可撤销编排、
混音与 WAV/MIDI 导出。可选 ACE-Step 生成草稿，试听后明确加入工程，附真实资源与失败记录。
主线为「想法 → 草稿 → 编排 → 混音 → 导出」；下一批优先完善效果器与混音预设。
旧版本与工作区保留。此包不是独立 EXE，不包含 Python 或神经模型权重。

## 0.2.0.dev2 — Speech cleanup / 语音清理开发预览

CPU speech cleanup with fixed, explicitly installed GTCRN / DPDFNet2 weights; integrated
LUFS, true-peak and LRA measurement; static-gain normalization with peak constraints;
synchronized matched A/B without reloading tracks. Sixteen UI/MCP/Codex tools share the
same immutable assets and reversible previews. Includes a credited CC BY 4.0 speech demo,
32 paired regression cases with per-case failures, and bilingual setup/results.
Older Next APIs hide unsupported controls; the launcher detects mismatched running versions.
Classic v0.1.2 and prior workspaces remain separate.

新增 CPU 语音清理（权重明确安装）、LUFS / 真峰值 / LRA、受峰值约束的音量统一、
同位置等响度 A/B。16 个界面/MCP/Codex 工具共用素材与可撤销预览，附 CC BY 4.0
语音示例、32 对回归及逐例退步、中英说明。新页面兼容旧 Next 能力清单，启动器检测旧后台。
经典版与已有工作区独立保留。GTCRN 为实验项；DPDFNet 也有 STOI 退步，见实测报告。

## 0.2.0.dev1 — Next development / 开发预览

The 0.2.0.dev0 release gate stopped on an asynchronous test's three-second deadline
on a shared Windows runner. The test now allows time for fixture exports to finish;
the success assertions and release checks are retained. No 0.2.0.dev0 release was published.

0.2.0.dev0 发布被 Windows 共享运行器上过短的异步测试等待时间拦住；
现给测试导出留足完成时间，保留所有成功断言与发布检查。未发布 0.2.0.dev0 安装包。

An independent audio-editing preview with waveform selections, typed PCM operations,
immutable audition candidates, undo/redo and WAV export. MCP and an experimental Codex
app-server bridge share the same project state and events. A separate launcher/runtime/output
retains v0.1.2. Seven local capability entries share a persistent serial queue, runtime checks,
immutable assets and text-correction versions through 15 UI/MCP/Codex tools. Real model runs
validate the path. Rest-preserving melody decoding improves vocadito but regresses on GTSinger;
it is an experimental option and does not replace the classic default.

独立的音频编辑预览：波形选区、非破坏处理、候选试听、撤销/重做和 WAV 导出；
MCP 与实验性 Codex 连接共用项目状态。启动器、环境和输出独立，稳定版 v0.1.2 保留。
新增本地模型清单、隔离环境检查、持久化队列、固定素材与转写改字版本，15 个共享工具覆盖
7 个能力入口，均完成真实模型验证。保留休止的音符解码作为实验选项，因跨数据集退步而未替换默认值。

## 0.1.2 — 2026-10-15 · Preview / 预览版

Fix Qwen recognition failing after separation when starting with the Windows shortcut.
The launcher now connects the optional environment installed by `setup_lyrics.ps1`,
or accepts `-LyricsPython` for a custom environment. The workbench disables recognizers
whose Python dependencies are absent; the API rejects unavailable runtimes before
starting separation or creating a result revision. Older running backends prompt a restart.

修复双击启动后选择 Qwen、运行到歌词识别阶段才失败的问题。启动器会自动连接已安装的
歌词独立环境，也支持 `-LyricsPython` 自定义路径；界面停用缺少依赖的识别模式，
后台在开始分离音轨、创建结果版本前检查所需运行环境。旧后台会提示重启；原有结果保留。

## 0.1.1 — 2026-10-15 · Preview / 预览版

The first published preview. The 0.1.0 build was stopped during release validation.
Importing the compressed demo now also prepares canonical float WAV caches, so
later lyric recognition/alignment can reuse the normal worker contract. No neural
models or decoder packages are needed to prepare this cache. Added a
demo-to-inference regression check.

首个实际发布的预览版。0.1.0 构建在发布验收中停止；现将压缩示例在导入时准备为标准 float WAV
缓存，修复安装模型后对示例重新识别 / 对齐时找不到音轨的问题。此准备过程不依赖模型或 PyAV，
保留统一时间基准，并增加示例转入识别流程的回归检查。

## 0.1.0 — 2026-10-15 · Preview / 预览版

- Local workbench: vocals/backing, synchronized lyrics, vocal MIDI, chords and beats.
- 中文 / English interface switch; browser language detection and saved preference.
- Bundled, credited 45-second precomputed demo; no model download needed to explore.
- Windows launcher, preview/full installation modes, packaged wheel/source and checksums.
- Lyric text correction, review markers, contextual loops, version comparison and explicit candidate acceptance.
- Sing-along view with adjustable guide vocals; LRC/SRT/MIDI/audio/CSV/JSON export.
- Project search, rename, recoverable delete and Trash restore.
- Playback fixes: stable result polling, lazy stem caching and rapid seek/pause handling.
- 43-case component/lyric benchmark with provenance and separately reported timing coverage/error.

中文：首个公开预览版，提供完整本地分析工作台、中英切换、免模型授权示例、Windows 启动入口、
歌词纠错与版本核对、跟唱与导出、歌曲回收站，以及可复现 benchmark。修复反复载入音轨和快速拖动时暂停的问题。

This is an early release. The Windows ZIP requires Python 3.11/3.12 and an initial
dependency download. Models are optional downloads with their own licenses.
It is not a standalone EXE or a complete score/arrangement editor.

这是早期版本。Windows ZIP 需要 Python 3.11/3.12，首次安装依赖需联网；模型需另行下载并遵守各自许可。
本版本不是独立 EXE，也不是完整谱面或编曲编辑器。
