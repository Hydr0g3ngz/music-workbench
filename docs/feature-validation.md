# 功能集成验证记录 / Feature integration records

面向维护者的历史测量，按原测试日期与版本解释；不是最新全套测试结果或通用质量排名。当前操作见 [文档目录](README.md)。

Historical measurements for maintainers, scoped to their original dates/builds. These are not current suite counts or general quality rankings. See [user documentation](README.en.md).

## 五步教程 / Beginner lesson · dev14

教程示例通过真实界面完成五步：开始播放、鼓独奏并还原、键盘片段内将一个音升半音、贝斯推子降低 2 dB、导出 WAV 与 MWB。WAV 17.78 秒，采样峰值 −10.5 dBFS、约 −24.6 LUFS。实际生成文件作为教程验证，未做听感或易用性研究。

All five actions were performed through the real UI in a separate test project: playback, drum solo and restore, a keys note raised by one semitone, bass lowered 2 dB, WAV and MWB exports. The WAV is 17.78 seconds, −10.5 dBFS sample peak and about −24.6 LUFS. This verifies operations and files, not listening quality or novice usability.

## 混音 / Mixing · 2026-10-16 · 中文

- 125 项 Python、37 项 Node 检查通过。覆盖 EQ 频响、压缩稳态/释放/立体声联动、限制器上限、混响尾音、任意分块边界、极端参数、旁路、保存/撤销/冲突和源文件保留。
- JavaScript DSP 与 Python 对同一固定随机输入比较，绝对/相对误差阈值均为 2×10⁻¹⁰；处理和旁路两种条件通过。
- 实际 Chromium `OfflineAudioContext + AudioWorklet` 与服务器 24-bit WAV 对比：44.1 kHz、61,740 帧，最大绝对误差 **1.4901161193847656×10⁻⁷**，RMS 误差 **6.861744876506113×10⁻⁸**。这是固定测试素材和参数的数值一致性结果，不代表主观音质评分。
- 浏览器实际操作：预设、播放、旁路、中英切换；播放头持续前进，源音频请求数保持 1。另检查窄屏布局、真实 WAV 和撤销恢复。

参数选择仍需要听音判断。此版本没有声称达到商用混音插件或自动母带的质量。

## Mixing · 2026-10-16 · English

- 125 Python and 37 Node checks passed, covering EQ response, compression steady state/release/stereo linking, limiter ceiling, reverb tails, arbitrary block boundaries, extreme settings, bypass, persistence/undo/conflicts and original-file preservation.
- JavaScript and Python kernels were compared on identical fixed random inputs with absolute/relative tolerances of 2×10⁻¹⁰, both processed and bypassed.
- Actual Chromium `OfflineAudioContext + AudioWorklet` against a server 24-bit WAV: 44.1 kHz, 61,740 frames, maximum absolute error **1.4901161193847656×10⁻⁷**, RMS error **6.861744876506113×10⁻⁸**. This is numerical consistency for one fixed input/configuration, not a perceptual quality score.
- Actual browser controls verified presets, playback, A/B and language changes; the playhead advanced while source requests stayed at one. Narrow layout, real WAV and undo/restore were also checked.

Listening judgment is still required; this release does not claim commercial-plugin or automatic-mastering quality.

## 采样与 MIDI / Samples and MIDI · 2026-10-16 · 中文

后端覆盖真实 FLAC 解码/校验、钢琴音高频谱、WAV/MIDI 导出、鼓通道、署名、MIDI 速度变化、
延音踏板、原文件保留、1025 音符密集导入、撤销恢复与损坏输入。
安装后的 wheel 也已解码并校验全部 23 个采样，wheel/源码包均检查了资源完整性。
浏览器实际验证了循环播放、MIDI 导入、力度修改、音色试听、中英切换、WAV 导出和窄窗口入口。

## Samples and MIDI · 2026-10-16 · English

Backend checks cover real FLAC decoding/hashes, piano pitch spectra, WAV/MIDI, drum channels,
credits, tempo changes, sustain, original-file retention, dense 1025-note imports, history
and malformed inputs. An installed wheel decoded and verified all 23 samples; both wheel
and source distribution were checked for asset completeness. Actual browser verification
covered looping, MIDI import, velocity editing, instrument audition, both languages, WAV
export and narrow-window controls.

## 录音 / Recording · dev6 · 中文

Node 测试覆盖尾块、精确帧数上限、PCM WAV、取消后迟到授权、设备释放、权限拒绝和设备断开。API 测试覆盖非零入轨位置、重复提交、保存重开、撤销重做与 WAV 导出。

浏览器使用合成 440 Hz WAV 作为虚拟输入，验证完整流程、保存失败后下载/重试与窄屏。此验证不代表真实声卡延迟或真人录音音质评测。

## Recording · dev6 · English

Node tests cover tail blocks, frame limits, PCM WAV, cancelled permission, resource release, permission denial and device loss. API tests cover nonzero placement, retry, reopen, history and WAV export.

Browser checks use synthetic 440 Hz WAV input for the full workflow, save failure/retry and narrow layouts. This does not measure real hardware latency or microphone quality.

## ACE-Step · 2026-10-16 · 中文

固定提示为 `Warm jazz trio, soft grand piano, brushed acoustic drums and upright bass, intimate late-night room, instrumental`，
12 秒、108 BPM、seed 42、8 步。以下是接入与资源检查，不是音乐质量 benchmark，也不是最优 seed 筛选。

| 项目 | 成功运行结果 |
| --- | --- |
| profile | `cuda-int8-offload-v3-pread` |
| 冷进程总耗时 | 112.453 秒，包含权重校验和加载 |
| 加载 / 后续生成 | 80.906 / 31.547 秒；扩散核心约 3.90 秒，其余包括 offload、编码与解码 |
| CUDA 已分配 / 预留峰值 | 3150 / 3222 MiB（PyTorch 统计，不是整机显存） |
| 进程驻留 RAM 峰值 | 9821.3 MiB |
| Windows 进程私有提交峰值 | 17941.6 MiB；包含分页支持的内存，不能等同于驻留 RAM |
| 原始结果 | 48kHz 立体声 WAV，12.0 秒；SHA256 `bb108bf1c3900e2d346ff091ab9631ee059c38c856ddd71dcb02e6730472fc0e` |
| 工程副本 | 44.1kHz 立体声，12.0 秒，sample peak −0.979 dBFS，零个满幅样本 |

此前同参数三次尝试全部保留：BF16/offload 在加载 GPU 时分配失败；
INT8 v1 在文本编码器分配失败（当时 GPU 仍有约 5.9GiB 空闲）；
INT8 v2 在 DiT 加载失败后标为中断。
Windows 的 copy-on-write mmap 会为整个 4.79GB checkpoint 预留提交量。
隔离 worker 改用 safetensors 官方 `pread` 后，第四次完成。此修改只影响本模型子进程。
测试未控制其他应用的资源占用与系统提交量；这些条件会影响结果。

尚待完成：更多风格与中英提示、不同 seed、长片段、人声歌词、盲听与对拍指标，
以及低内存/不同 GPU 的测量。单个成功草稿不能代表稳定性、音乐质量或所有硬件兼容性。

同提示、同 seed 随后又验证了 20 秒请求：总计 66.500 秒，加载 49.641 秒、生成 16.859 秒，
CUDA 已分配/预留峰值 3152.1/3226 MiB，驻留 RAM 峰值 10936.1 MiB，私有提交峰值 17997.4 MiB。
这是新进程，但系统文件缓存已预热，不能把与首例的耗时差解释为时长越长越快。
20 秒原始 WAV SHA256 为 `bb5339c690b4a8e4e56fbf783dd866029c8fbf8f6d0a60285e975881a720a3de`。
工程副本 peak −1.144 dBFS、零个满幅样本。API 验证了真实草稿入轨、撤销/重做、来源记录与导出；
还把两小节采样鼓点和导入 MIDI 钢琴放在草稿前，导出 24.444 秒、44.1kHz/24-bit 的三轨编排。
这些检查覆盖功能连接，不是完整混音制作或听感验收。

## ACE-Step · 2026-10-16 · English

Prompt: `Warm jazz trio, soft grand piano, brushed acoustic drums and upright bass, intimate late-night room, instrumental`.
Duration 12s, BPM 108, seed 42, eight steps. This is an integration/resource check, not a music
quality benchmark or a selected best seed.

| Measurement | Successful run |
| --- | --- |
| Profile | `cuda-int8-offload-v3-pread` |
| Cold-process total | 112.453s, including checksum verification and loading |
| Loading / subsequent generation | 80.906 / 31.547s; diffusion itself ~3.90s; remaining work includes offload, encoding and decoding |
| CUDA allocated / reserved peaks | 3150 / 3222 MiB, PyTorch counters rather than total system VRAM |
| Peak resident RAM | 9821.3 MiB |
| Peak Windows private commit | 17941.6 MiB, includes page-backed memory and is not resident RAM |
| Original output | Stereo 48kHz WAV, 12.0s; SHA256 `bb108bf1c3900e2d346ff091ab9631ee059c38c856ddd71dcb02e6730472fc0e` |
| Arrangement copy | Stereo 44.1kHz, 12.0s, sample peak −0.979 dBFS, zero full-scale samples |

All three earlier attempts remain recorded: BF16/offload failed on GPU transfer; INT8 v1
failed at the text encoder despite ~5.9GiB of free VRAM; INT8 v2 failed transferring DiT and
was subsequently marked interrupted. Windows copy-on-write mmap
reserved commit for the entire 4.79GB checkpoint. Switching the isolated worker to the official
safetensors `pread` backend allowed attempt four to complete. Other application resource usage and available system commit were uncontrolled.

More styles, Chinese/English prompts, seeds, longer audio, vocals/lyrics, blind listening,
tempo adherence and other RAM/GPU configurations remain to be evaluated. One successful
draft establishes neither broad stability nor music quality.

A subsequent 20s request with the same prompt and seed completed in 66.500s: loading
49.641s, generation 16.859s, CUDA allocated/reserved peaks 3152.1/3226 MiB, resident RAM
peak 10936.1 MiB and private commit peak 17997.4 MiB. It used a fresh worker but warm OS
file caches; the timing difference does not establish a duration/performance relationship.
Original WAV SHA256: `bb5339c690b4a8e4e56fbf783dd866029c8fbf8f6d0a60285e975881a720a3de`.
The canonical copy peaks at −1.144 dBFS with zero full-scale samples. API checks verified
real-draft adoption, undo/redo, provenance and export. A sampled two-bar groove and imported
piano MIDI intro were also arranged before the draft and exported as a 24.444s, 44.1kHz,
24-bit three-track mix. These are integration checks, not full mixing or listening acceptance.
