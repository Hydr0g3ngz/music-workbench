# 兼容素材编辑器：模型与任务

> 本文供需要手动配置模型的源码用户使用，描述保留的 Next 单素材编辑器与共用推理环境。当前工作台的安装方式与支持状态见 [模型目录](models.md)。

[English](next-models.en.md) · [预览说明](next-preview.md) · [未来模型候选（尚未接入）](local-model-candidates.md)

Next 的模型按任务使用，不要求导入音频后跑完整套歌曲分析。打开右上角“本地模型”，
查看来源、许可、运行环境检查与权重缓存；在时间轴下面选择能力，点击“加入任务”。
界面、MCP 与 Codex 共用同一队列、输入快照、素材和操作记录。

| 能力 | 实现 | 结果 | 运行环境 |
| --- | --- | --- | --- |
| 电平检查 | NumPy / SoundFile | 峰值、RMS、满刻度采样 JSON | 基础环境，无模型 |
| 响度与真峰值 | pyebur128 / libebur128 | LUFS、dBTP、LRA JSON | Next 基础环境；CPU，无权重 |
| 语音清理 | [DPDFNet2 48 kHz](https://github.com/ceva-ip/DPDFNet) / Sherpa-ONNX | 清理 WAV、处理前快照、测量报告 | Next 基础环境；CPU；Apache-2.0 权重另装 |
| 轻量降噪（实验） | [GTCRN](https://github.com/Xiaobin-Rong/gtcrn) / Sherpa-ONNX | 清理 WAV、处理前快照、测量报告 | Next 基础环境；CPU；MIT 权重另装 |
| 人声与伴奏 | [Demucs htdemucs](https://github.com/facebookresearch/demucs) | 两个对齐的 WAV | Next 模型环境；MIT |
| 语音与歌词 | [faster-whisper small](https://huggingface.co/Systran/faster-whisper-small) | 可编辑转写、TXT / LRC / SRT | Next 模型环境；MIT |
| Qwen 语音与歌词 | [Qwen3-ASR-1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) | 可编辑转写、TXT / LRC / SRT | 独立歌词环境；Apache-2.0 |
| 单旋律估计 | [torchcrepe](https://github.com/maxrmorrison/torchcrepe) | MIDI、音符 JSON、估计音符合成 WAV | Next 模型环境；MIT |
| 节拍与速度 | [librosa](https://github.com/librosa/librosa) | 节拍 JSON / CSV | Next 模型环境；ISC |

模型检查实际启动子进程并导入相应库，捕获原生加载失败；不会只检查安装包是否存在。
“运行环境检查通过”和“权重已缓存”是独立状态，均不表示权重已成功加载或识别质量有保证。
第一次任务会实际加载模型，失败原因保留在任务的“参数与诊断”里。

## Windows 安装

语音降噪无需安装下面的 Torch 模型环境。打开“让讲话更清楚”或“本地模型”，明确点击安装，
下载固定哈希的 DPDFNet（约 10.11 MiB）或 GTCRN（约 0.51 MiB）权重。
已有 Next 环境缺少新 CPU 运行库时，启动器会补齐自己的环境。命令行安装可用：

```powershell
.\scripts\setup-next-cleanup.ps1 -Model dpdfnet2-48k
```

模型可能损伤音乐与环境声；GTCRN 还有频带限制。默认选择依据、退步样本和 A/B 说明见
[语音清理报告](speech-cleanup.md)。10 个能力入口包含算法与两种旋律解码，并非 10 个不同神经网络。

基础剪辑、试听、撤销与导出只需要 `Start-Music-Studio-Next.cmd`。
首次启动会建立 `.venv-next`。要启用本地推理，关闭并重新启动 Next 前执行：

```powershell
# NVIDIA GPU；需要兼容 CUDA 12.1 的驱动。单独建立 .venv-next-models。
powershell -ExecutionPolicy Bypass -File .\scripts\setup-next-models.ps1 -Device cuda
# CPU 改用 -Device cpu；只安装依赖、不下载权重则加 -SkipDownload。
.\Start-Music-Studio-Next.cmd
```

安装脚本从 PyTorch 官方索引、PyPI 与官方模型来源下载。新环境不会改动经典版 `.venv`。
Demucs 和 Whisper 权重会下载到 `.cache/models`；CREPE 权重随上游包安装。
Next 启动器自动发现自己的模型环境。也可显式连接已有环境与缓存：

```powershell
.\scripts\launch-next.ps1 -InferencePython 'D:\envs\audio\Scripts\python.exe' -ModelDir 'D:\models\music-studio'
```

再次启动会读取该工作区上次保存的模型环境、歌词环境和缓存路径；显式启动参数优先。
任务设备选“Auto”时遵守启动配置中的设备选择，显式选 CPU / CUDA 可覆盖它。

Qwen 是可选的独立环境，先完成上面的模型环境安装，再执行：

```powershell
.\scripts\setup_lyrics.ps1 -Python .\.venv-next-models\Scripts\python.exe -Models qwen
.\Start-Music-Studio-Next.cmd
```

Next 自动发现本仓库 `.artifacts/lyrics-env`。也可通过 `launch-next.ps1 -LyricsPython ...`
指定运行环境。所有界面任务均强制离线；缺少依赖或权重时会失败并给出说明，不静默下载安装。
安装脚本本身需要网络。权重不会随发布包再分发。

## 队列、素材与改字

- Next 的按需分析任务在每个工作区一次运行一个，UI 与 MCP 两个进程也通过文件锁共享队列。
  RoFormer、Demucs 和 Whisper 可在相同设置下复用独立进程；空闲 30 秒、切换工具、取消、关闭或等待生成任务时释放。其他工具每次退出后释放模型。不同工作区与其他软件仍可能竞争显存。
  经典整曲分析使用原有流程，也应避免与其他 GPU 任务同时运行。
- 单素材编辑器固定**当前试听音轨的完整长度**，工作台则固定选中的片段，均包含输入哈希和当时编辑版本。单素材编辑器要分析选区，先裁成预览，
  选中这份预览后再运行。任务完成不会采用结果、改变播放音轨或重置播放位置。
- 模型任务目前限每段 600 秒，电平与响度测量限 7200 秒，最多 20 个待处理任务。
  长录音请先裁剪；内存预算、流式长音频与批量切片仍需完善。
- 分轨与音符合成可以独立试听、继续剪辑和导出；MIDI、节拍与其他结构化文件可以下载。
  音符合成仅用于核对估计音符，合成音色不是准确率提升。
- 转写可逐行改字，保存为新版本；原始识别不覆盖。修改行保留原行时间并清除旧逐字时间，
  不把改字后的逐字对应伪装成重新对齐。新版本提供 TXT / LRC / SRT。
- 可以取消排队或运行中的任务；Windows 会停止本任务拥有的进程树。
  删除有待处理任务的项目前须先取消任务。重启后排队任务继续；丢失执行进程的任务标为中断，
  已完成素材与编辑版本保留。

## Agent 工具与限制

原有 8 个编辑工具保留，新增 `audio_list_models`、`audio_check_model`、`audio_run_task`、
`audio_get_tasks`、`audio_cancel_task`、`audio_read_artifact`、`audio_correct_transcript` 与
`audio_prepare_comparison`，共 16 个。A/B 工具只准备界面对比，不自动播放或采用。
例如让 Codex “先分离当前音频的人声，再读取转写结果”。工具参数只接受固定模型 ID 和项目素材 ID，
不能提交 shell、Python 路径或下载地址；转写等结构化结果可进入对话上下文，音频字节不会隐式上传。

MCP 默认读取同一工作区的 `.studio-runtime.json`，也支持启动参数
`--inference-python`、`--lyrics-python` 和 `--model-dir`。只在自己的机器上使用这个本地配置。

旋律仍是单旋律估计。保留休止与旧版解码都提供作比较，详见
[分段评测](melody-next.md)。语音去噪可用；按描述分离与自动模型选择仍待开发。音乐生成已在多轨工作台提供，见 [支持模型](models.md)。
