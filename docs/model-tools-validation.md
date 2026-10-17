# CPU tool pack validation / CPU 工具包验证

Scope: dev15 automatic installation and workstation integration. These checks
establish executable workflows, not separation, transcription or composition quality.

范围：dev15 的自动安装与工程衔接。以下结果验证运行流程，不代表音乐或转写质量评测。

## Environment / 环境

- Windows x64, Intel Core Ultra 9 185H, four inference threads.
- Each pack was installed into a new embedded Python 3.12.10 directory. No system
  Python or manually configured Music Studio model environment was used by the packs.
- Music pack: Torch/torchaudio 2.5.1 CPU, Demucs 4.0.1, torchcrepe 0.0.24,
  faster-whisper 1.2.1, CTranslate2 4.6.0, librosa 0.11.0.
- Speech pack: sherpa-onnx 1.13.8, DPDFNet2 48 kHz and GTCRN. GPU acceleration was
  not used or evaluated for these packs.
- This is a clean inference environment on an existing Windows host, not a fresh
  Windows virtual-machine or broad hardware compatibility test.

## Offline inference / 离线推理

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

## Workstation workflow / 工程流程

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

## Failure behavior / 失败行为

Automated regression checks cover cross-window cancellation, interrupted setup,
preservation of the last published manifest after inference failure, corrupt or
deleted weights, explicit runtime priority, and rebinding embedded Python after app
upgrades. UI tests cover polling without replacing cards, retained error messages,
and hiding use controls after failed checks. Existing ACE-Step preview playback is
checked against repeated reloads.

## Remaining coverage / 尚未覆盖

RoFormer and Qwen3-ASR still require manual setup. CPU throughput on full-length
songs, automatic GPU profiles, new Windows installations and more hardware/network
conditions need separate validation. Existing model quality benchmarks remain the
source for quality claims; installation success does not replace them.
