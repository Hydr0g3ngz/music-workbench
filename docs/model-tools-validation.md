# Local tool pack validation / 本地工具包验证

## dev18: selected clips and model reuse / 片段处理与模型复用

Workstation tools now pin only the selected clip, with exact source frame bounds and
SHA-256 provenance. Identical selected samples produce identical input WAV hashes.
Audio/lyric/MIDI exports use clip-relative time; adoption restores the session position.
Old whole-source tasks retain their original mapping. Transcript correction can audition
the pinned task input instead of matching its times against an unrelated full-length track.

工作台只处理选中的片段，结果从片段内 0 秒开始。已验证非零素材偏移、分轨替换、A/B、
MIDI 回填、变速、重开、WAV 导出和撤销。歌词编辑器提供提交时音频片段的试听。

Same Windows host as dev17. Each pair below uses identical input hashes, a new worker,
then an immediate repeat. OS caches were warm; these are single trials with background
activity. Worker time includes imports, weights, inference and writing. Invocation time
also includes environment checks and Python startup; HTTP time includes polling.

| Tool / 工具 | Input / 输入 | First worker → reused / 模型阶段 | First invocation → reused / 含检查与启动 |
| --- | --- | --- | --- |
| RoFormer | 12 s song window | 12.349 → 3.453 s | 13.375 → 4.547 s |
| Demucs htdemucs | Same 12 s song window | 6.021 → 0.415 s | 14.672 → 1.016 s |
| Whisper small, CUDA INT8/FP16 | 12 s noisy speech window | 13.928 → 0.812 s | 23.078 → 1.141 s |

Repeated separator outputs were sample-identical; Whisper returned an identical
transcript. One resident capability is retained for at most 30 idle seconds; tool or
settings changes, cancellation, shutdown and queued generation retire it. Real RoFormer
idle exit and cancellation passed. Timeout, shutdown and generation handoff use a tiny
process/queue fixture; a new ACE generation was not included in this round.

Qwen still releases recognition before loading its aligner. A 12 s cropped speech test
produced 36 structurally valid word spans in three lines, with no timing review flags:
36.052 s worker time, 75.297 s including the initial environment check. CREPE on a 4 s
synthetic monophonic window took 21.890 s in the worker and placed 3 extracted notes back
at the correct project time. The 4 s DSP time/pitch task took 20.519 s; startup/import
costs remain substantial. These checks do **not** establish recognition or music quality.

上述数值来自单台电脑的单次测试，不能作为普遍性能承诺。裁短片段会减少上下文，可能影响
识别、分轨和节拍质量；需试听比较。Qwen 字词数量、时间边界与 MIDI 位置检查不代表准确率。

[Raw measurements / 原始记录](../benchmarks/results/selected-clips-2026-10-17.json).
For reproduction, start a dedicated QA server, then run:

```powershell
python -m music_studio ui --interface create --workspace .artifacts/clip-benchmark --port 8933 --offline
# In a second terminal, using the same installed source environment:
python scripts/benchmark_workstation_clips.py src/music_studio/ui/demo/audio/source.ogg --start 3.25 --duration 12 --model mel-band-roformer-kj --output .artifacts/roformer-clips.json
```

Prepare the model pack first. The script creates a new QA project and never downloads
models or edits existing projects. Repeat with `--model demucs-htdemucs`, or use the
bundled speech fixture with `--model whisper-small`. For isolated cold-worker comparisons,
keep using `scripts/benchmark_local_models.py`.

## dev17: managed RoFormer and Qwen / 自动分轨与转写工具包

Windows x64, Core Ultra 9 185H, RTX 4070 Laptop 8 GB, 32 GB RAM, Python 3.12.10,
Torch 2.10 CUDA 12.8. Both packs were installed into new embedded environments.
Existing model downloads were reused and checked against pinned upstream hashes;
the full remote weight transfer was not repeated. Offline verification disabled
Python socket connections and required valid outputs before publishing runtime manifests.

两个工具包使用新建的独立环境，复用已有模型文件并逐项核对固定上游哈希。
安装后禁用 Python socket 连接进行真实 CUDA 推理；Qwen 的五秒安装示例通过了完整声学对齐检查。
这是已有 Windows 电脑上的环境安装验证，没有覆盖全新系统或更多显卡。

| Workflow / 流程 | Measured outcome / 实测结果 |
| --- | --- |
| RoFormer, 30 s factory-sample mix / 内置乐器混合 | 20.6 s; aligned replacement, reopening, WAV export and undo passed / 对齐替换、重开、导出与撤销通过 |
| Qwen, 23.112 s noisy speech / 含噪语音 | Coarse 36.2 s; acoustic timing 43.2 s. Same 67 recognized tokens; 64 valid word spans, three lines flagged / 识别文字保留，三行需复核 |
| Text correction / 改字 | Edited-line word times cleared; original transcript preserved; TXT/LRC/SRT contain corrections / 清除改动行旧字词时间，保留原识别并导出更正 |
| Licensed 45 s song / 自带授权歌曲 | RoFormer 19.8 s → adopt vocals → Qwen 34.9 s; 66 recognized tokens, 37 valid word spans; all six lines need review / 六行均有部分时间需复核 |

Times are worker-stage measurements including imports, loading, inference and writing;
they exclude queueing, environment probes and initial Python startup. These are single
trials with warm OS caches and background checks/setup activity, not controlled speed
comparisons. First Qwen installation verification took 101.9 s on five seconds of audio.
Torch peak allocations were about 2.0 GiB for song separation and 4.4 GiB for Qwen;
CUDA context and other applications are excluded.

有效时间段数量只表示通过结构检查，**不是对齐准确率**。歌曲示例的六行均需复核，不能据此
宣称歌词或歌唱对齐已经准确。模型加载开销明显，后续优先改善片段处理和重复加载。
工作台任务卡会显示部分时间需复核；逐字定位不改正识别错词。

The song demo is an execution example, not annotated ground truth. Valid word spans
do not measure accuracy. Every song line needed timing review. The workstation now
shows this in task cards, rather than presenting a completed task as reliable timing.

Raw records, input hashes, versions and limits:
[JSON](../benchmarks/results/managed-advanced-2026-10-17.json).
Reproduce timed Qwen stages with `scripts/benchmark_local_models.py --models qwen3-asr`
and `--alignment native` or `--alignment qwen`, using its managed Python and model
directory. `--input-dir` reuses identical input WAVs. For RoFormer, use
`--models mel-band-roformer-kj --separation-config <pack>/separation-runtime.json`.

[Setup and use / 安装与使用](qwen-and-separation.md) ·
[English guide](qwen-and-separation.en.md).

## dev15: CPU pack / CPU 工具包

Scope: dev15 automatic installation and workstation integration. These checks
establish executable workflows, not separation, transcription or composition quality.

dev16 hardware and GPU follow-up: [measured speed and integration audit](model-hardware.en.md).
dev16 的 CPU/GPU 速度与流程复查见 [硬件报告](model-hardware.md)；下文保留 dev15 的验证范围。

范围：dev15 的自动安装与工程衔接。以下结果验证运行流程，不代表音乐或转写质量评测。

### Environment / 环境

- Windows x64, Intel Core Ultra 9 185H, four inference threads.
- Each pack was installed into a new embedded Python 3.12.10 directory. No system
  Python or manually configured Music Studio model environment was used by the packs.
- Music pack: Torch/torchaudio 2.5.1 CPU, Demucs 4.0.1, torchcrepe 0.0.24,
  faster-whisper 1.2.1, CTranslate2 4.6.0, librosa 0.11.0.
- Speech pack: sherpa-onnx 1.13.8, DPDFNet2 48 kHz and GTCRN. GPU acceleration was
  not used or evaluated for these packs.
- This is a clean inference environment on an existing Windows host, not a fresh
  Windows virtual-machine or broad hardware compatibility test.

### Offline inference / 离线推理

Setup checked checkpoint hashes and ran every declared capability with Python
socket connections disabled. Demucs processed a non-silent mix of licensed factory
samples; CREPE used the same sample material. Speech tools processed a five-second
excerpt of the bundled attributed noisy-speech demo. Outputs were checked for file
presence, finite audio, sample rate, channel count and duration alignment.

安装在校验权重后，禁用 Python socket 连接，逐项执行真实推理。分轨和旋律使用
自带且有授权说明的乐器样本混合，转写和降噪使用内置语音示例。检查产物存在、
音频数值有限、采样率、声道及时间对齐。

| Capability / 能力 | Result / 结果 |
| --- | --- |
| Demucs four stems / 四分轨 | Four aligned audio tracks and report / 四条对齐音轨及报告 |
| Demucs two stems / 两分轨 | Vocal and residual backing tracks / 人声与残差伴奏 |
| CREPE rest and legacy decoders / 两种解码 | MIDI, notes, contour and note preview / MIDI、音符、音高与试听 |
| Whisper small | Transcript and text exports / 转写及文本导出 |
| DPDFNet2 and GTCRN | Cleaned speech and reports / 降噪音频及报告 |
| Librosa analysis, time/pitch and beats / DSP | Analysis and aligned transformed audio / 分析及对齐的处理音频 |

The ten paths above use five AI model families and several DSP operations. Decoder
variants and DSP tools are not additional AI models. All paths passed. This smoke
test does not measure recognition errors or perceptual quality.

以上十条处理路径涉及五种 AI 模型及 DSP 操作，解码器变体和 DSP 不作为新增模型计数。
全部运行通过；本次未测识别误差或听感质量。

### Workstation workflow / 工程流程

Using the real HTTP task queue with default settings and automatic managed-runtime
discovery:

1. Import audio, separate four stems, replace the source clip, then undo to restore it.
2. Extract CREPE notes and adopt them into a sampled MIDI track; reopen the project
   and export WAV successfully.
3. Transcribe speech with Whisper and save an edited transcript while retaining the
   recognition output.
4. Clean speech with DPDFNet2 and add the result as a second track.

通过真实任务队列和默认配置，验证了导入、四分轨替换及撤销、旋律音符采用、
重开与 WAV 导出、转写改字、降噪音频加入工程。未改动用户已有作品。

### Failure behavior / 失败行为

Automated regression checks cover cross-window cancellation, interrupted setup,
preservation of the last published manifest after inference failure, corrupt or
deleted weights, explicit runtime priority, and rebinding embedded Python after app
upgrades. UI tests cover polling without replacing cards, retained error messages,
and hiding use controls after failed checks. Existing ACE-Step preview playback is
checked against repeated reloads.

### Remaining coverage / 尚未覆盖

In dev15, RoFormer and Qwen3-ASR required manual setup; dev17 adds managed packs
described in the [current guide](qwen-and-separation.en.md). CPU throughput on full-length
songs, automatic GPU profiles, new Windows installations and more hardware/network
conditions need separate validation. Existing model quality benchmarks remain the
source for quality claims; installation success does not replace them.
