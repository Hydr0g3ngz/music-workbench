# 窗灯 / Windowlight

[文档 / Documentation](../README.md) · [多音音符 / Polyphonic notes](../polyphonic-notes.md) · [编排与路由 / Groups and routing](../groups-and-routing.md)

## 创作动机 / Creative brief

黄昏街道的一盏窗灯：先听见稀疏的近距离钢琴，回声逐渐加入，第三段换成钟琴般的钢琴变奏，最后回到原来的短句。没有鼓与人声，用留白和音色变化形成一首安静器乐小品。

A lit window on a twilight street: intimate piano, gradually arriving echoes, a bell-like piano contrast, then a quiet return. Space and timbre carry this instrumental sketch without drums or vocals.

![Windowlight arrangement in dev20](../images/windowlight-dev20-zh.png)

这是 dev20 的实际工作流案例，完成于 2026-10-17。工程目标为 120 BPM、C minor、4/4、32 小节。BPM 和调性是输入条件，未做独立真值验证；不能把提示词当作模型已遵守的证据。

Completed on 2026-10-17 in dev20. Requested conditions: 120 BPM, C minor, 4/4, 32 bars. Tempo/key compliance was not independently established.

## 制作步骤 / Production steps

| 步骤 / Step | 实际操作 / Action | AI 与编辑的边界 / What made the result |
| --- | --- | --- |
| 1 | 从空工程命名、设定速度；ACE-Step 生成 20 秒 felt piano，seed 42、8 steps。Create empty project, request 20 s felt piano. | ACE-Step 本地推理；提示要求下降动机、无鼓无人声。Local model generation. |
| 2 | 在界面采用、裁为 8 小节 / 16 秒，设置短淡入淡出。Adopt and trim to eight bars. | 人工编排与 DSP；没有重新生成。Editorial trim/fades. |
| 3 | Basic Pitch 处理所选 16 秒；试听后加入可编辑乐器轨。Transcribe the selected crop and adopt notes. | ONNX CPU 音符估计，保留重叠和弦；不是人工真值。Polyphonic model estimates. |
| 4 | 钢琴卷帘全选量化到 1/16、换马林巴、降低音量、略向右；双击删除一个 MIDI 31 低音。Quantize, change timbre and remove a low note. | 规则量化、采样合成与实际界面编辑；不是新 AI 配器。Rules/sample playback and UI edits. |
| 5 | 两片段成组，界面复制到第 9、17、25 小节；验证独立撤销/重做。Group and develop 8 bars into 32. | 分组编辑；副本独立，保留源范围、音符和淡变。Ordinary arrangement operations. |
| 6 | 创建 Piano family 总线与 100% 湿声 Twilight room；两轨输出到分组，发送分别 −20/−16 dB。Create group and shared reverb buses. | 手工混音与 DSP。Editorial mix decisions. |
| 7 | 保存创作蓝图、四段标记；以原片段做 16 秒参考变奏，目标为第三段“回声”。Create contextual reference variation for Echoes. | 规则编译蓝图和段落提示，ACE-Step 做真实生成。Context compilation is deterministic; audio generation is neural. |
| 8 | 界面试听并采用到目标段落。Audition and adopt at the section start. | 保留来源、任务参数和模型修订。Provenance retained. |
| 9 | 精确整理：移除第三段原钢琴，第一段回声延后出现，结尾减少高音并渐弱；参考变奏也接入总线。Thin layers and finish transitions. | 此后期使用本地 API 脚本完成；没有声称全程只用界面。Scripted editorial finishing, explicitly separate from UI verification. |
| 10 | 界面调整主输出，导出 WAV/MIDI/MWB，恢复新工程、改总线再撤销，重新导出。Finalize level, export and restore. | 完整恢复后 WAV 哈希相同。Restored export is byte-identical. |

## 结构 / Form

| 小节 / Bars | 段落 / Section | 层次 / Texture |
| --- | --- | --- |
| 1–8 | 入夜 / Arrival | 钢琴进入，马林巴在后半段出现。Piano; echoes enter halfway. |
| 9–16 | 灯亮 / Glow | 完整短句与高音回声。Full phrase and upper-register echoes. |
| 17–24 | 回声 / Echoes | AI 参考变奏替换原钢琴与马林巴。AI variation replaces the earlier layers. |
| 25–32 | 归途 / Home | 原钢琴回归、更少回声、较长淡出。Original piano returns, fewer echoes, longer fade. |

最终包含 3 轨、7 片段、2 总线；WAV 为 44.1 kHz、24-bit、立体声、65.7 秒（含 1.7 秒尾音）。libebur128 测得约 **−19.96 LUFS**、**−2.00 dBTP**，用于安静器乐示例；没有为追逐响度加重限制。MIDI 只含马林巴音符，不会把两个音频钢琴自动转成完整 MIDI。

The final 3-track/7-clip/2-bus WAV is 44.1 kHz, 24-bit stereo, 65.7 s including tails. Measured integrated loudness is about −19.96 LUFS and true peak −2.00 dBTP. MIDI contains editable marimba notes, not automatic transcriptions of both piano audio tracks.

## 测量与限制 / Evidence and limits

- RTX 4070 Laptop 8 GB、32 GB RAM；ACE-Step 使用 low-vram：DiT decoder linear weights INT8、VAE/text encoder BF16、CPU offload，不加载语言模型。First generation: 99.734 s load + 17.766 s generation = 117.5 s, excluding preceding checkpoint verification; peak Torch allocation 3156.6 MiB, peak resident RAM 9705.9 MiB. Reference variation total was 72.234 s. These are single-machine measurements.
- Basic Pitch：16 秒输入，任务推理 6.633 秒，完整调用 11.593 秒；没有峰值 RAM 或本曲音符准确率真值。No note-accuracy ground truth or peak-RAM measurement for this sketch.
- 音符量化、删低音、筛高音和段落取舍属于创作编辑，不能当作统计“修正了多少识别错误”。Editorial thinning is not a transcription correction-rate measurement.
- 实际修复了双击删音符的指针捕获、快速分组操作合并撤销、总线重命名后路由标签滞后。The case exposed pointer capture, history batching and stale route-label issues, now fixed.
- 完整播放期间保持 7 个片段音源与 5 次源/采样音频请求，调整总线音量后没有重建音源或重复请求，页面无未捕获错误。这验证播放流程，不是专业监听或盲听结论。Playback instrumentation checks lifecycle, not perceptual quality.

可复现的[工作流数值记录](../../benchmarks/reports/windowlight-workflow-v1.json)包含最终导出哈希和恢复检查。音频与 MWB 作为本地构建附带示例交付，未随 Git 仓库存储；不包含测试集录音。模型与采样署名保留在工程和导出 credits 中。

The [numerical record](../../benchmarks/reports/windowlight-workflow-v1.json) retains hashes and recovery evidence. Audio/MWB accompany the local build rather than Git; no benchmark recordings are redistributed. Project/export credits retain model and sample attribution.
