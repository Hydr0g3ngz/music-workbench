# 本地音乐生成：ACE-Step 1.5

[English](music-generation.en.md) · [制作工作台](create-preview.md)

在「AI 模型 → 生成音乐草稿」描述风格、乐器和氛围，选择时长并运行。
草稿完成后先试听，再明确点击「加入工程」；生成、失败或取消不会改写编排。
加入后可移动、裁剪、调音量和淡入淡出，与采样乐器、鼓点和导入 MIDI 一起制作，最后导出 WAV。
加入工程可撤销，原始生成文件与参数仍保留。

## 安装与运行

基础编排和内置音色无需安装此模型。生成是可选能力，需要 NVIDIA CUDA 显卡、
Python 3.11/3.12 和额外磁盘空间。当前仅实测 Windows 11、RTX 4070 Laptop 8GB、32GB RAM。
准备至少约 20GB 可用磁盘；下载缓存、独立环境及安装临时文件可能占用更多。
32GB RAM 是本次测试条件，不能据此保证所有 8GB 显卡或低内存电脑都能运行。

在项目根目录明确执行安装：

```powershell
py -3.12 scripts/setup_ace.py
.\Start-Music-Workbench.cmd
```

Linux 使用 `python3.12 scripts/setup_ace.py`。Linux 路径已实现但尚未完成实机推理验收。
安装器从官方 PyTorch、PyPI、GitHub 和 Hugging Face 下载，建立独立环境，
不升级 UI、经典版或其他模型的 Torch。应用启动不会自动下载权重。
默认配置是项目根目录 `.artifacts/acestep-runtime.json`；高级用户可用
`MUSIC_STUDIO_ACE_CONFIG` 指向另一配置。权重缓存后，worker 强制离线推理。

默认使用 Turbo、INT8 线性层权重、BF16、SDPA、CPU offload、8 步、单候选，
不加载 5Hz 语言模型，不编译，也不使用 Flash Attention。先尝试 12–20 秒器乐。
界面提供 10–60 秒请求范围；已实际运行 12/20/32 秒器乐，60 秒和人声歌词质量尚未验收。
工程 BPM 作为生成条件传入，输出不保证准确对拍，也不会自动拉伸。

新增参考变奏：先选中 10–60 秒音频片段，在生成面板选择「参考变奏」。
worker 使用的是所选片段实际裁切后的固定副本，记录音频/来源哈希及参数；源素材不改动。
可继承工程调性与循环长度，但生成条件不等于结果验证。32 秒实际创作及资源记录见
[《云隙电台》](creations/radio-through-the-clouds.md)，操作入口见[工作流](ai-production-workflow.md)。

## 固定版本与来源

| 内容 | 固定版本 |
| --- | --- |
| [ACE-Step 源码](https://github.com/ACE-Step/ACE-Step-1.5) | `ca1e85fe9430179831e6bc6be790c332190a3866`，MIT |
| [Ace-Step1.5 权重](https://huggingface.co/ACE-Step/Ace-Step1.5) | `19671f406d603126926c1b7e2adc169acbcade22`，仓库声明 MIT |
| 下载内容 | Turbo DiT、VAE、Qwen3-Embedding-0.6B；17 文件，6,336,686,268 字节 |
| 推理依赖 | Torch/Torchaudio 2.10.0 CUDA 12.8、Transformers 4.57.6、TorchAO 0.16.0、safetensors 0.8.0；完整列表在 `requirements/acestep.txt` |

安装器验证源码 ZIP SHA256、HF LFS SHA256 和小文件 Git blob 哈希。
上游会同步源码里的模型实现；本项目建立单独的固定代码视图，保留下载快照。
worker 再检查 manifest 与文件 SHA256，首次任务的加载时间包含该校验。
任务保留源码/权重修订、worker 哈希、profile、seed、描述、时长、BPM、步数、文件哈希和资源记录。
生成音频不是训练素材许可或生成内容使用权的保证；发布作品前仍需判断具体内容。

## 2026-10-16 本机验证

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
INT8 v2 仍在 DiT 加载失败，后因服务所有者结束标为中断。
Windows 的 copy-on-write mmap 会为整个 4.79GB checkpoint 预留提交量。
隔离 worker 改用 safetensors 官方 `pread` 后，第四次完成。此修改只影响本模型子进程。
本机当时还运行其他应用，可用系统提交量会影响结果；未关闭用户应用或修改系统分页设置。

尚待完成：更多风格与中英提示、不同 seed、长片段、人声歌词、盲听与对拍指标，
以及低内存/不同 GPU 的测量。单个成功草稿不能代表稳定性、音乐质量或所有硬件兼容性。

同提示、同 seed 随后又验证了 20 秒请求：总计 66.500 秒，加载 49.641 秒、生成 16.859 秒，
CUDA 已分配/预留峰值 3152.1/3226 MiB，驻留 RAM 峰值 10936.1 MiB，私有提交峰值 17997.4 MiB。
这是新进程，但系统文件缓存已预热，不能把与首例的耗时差解释为时长越长越快。
20 秒原始 WAV SHA256 为 `bb5339c690b4a8e4e56fbf783dd866029c8fbf8f6d0a60285e975881a720a3de`。
工程副本 peak −1.144 dBFS、零个满幅样本。API 验证了真实草稿入轨、撤销/重做、来源记录与导出；
还把两小节采样鼓点和导入 MIDI 钢琴放在草稿前，导出 24.444 秒、44.1kHz/24-bit 的三轨编排。
这些检查覆盖功能连接，不是完整混音制作或听感验收。

## 故障与数据

开启「使用已保存的创作蓝图与段落目标」，会将作品意图、音色、动机、和声方向与段落任务
加入实际提示词，BPM/调性跟随已保存工程。可先「预览实际提示词」，再提交任务。
规则负责组装，本地 ACE-Step 负责音频生成；没有新增语言模型，也不保证结果满足意图。
详见 [编曲方法与流程](arranging-methods.md)。

「参数与诊断」提供错误和资源指标；完整日志在工作区 `.creation-tasks/<id>/worker.log`，
阶段内存记录在 `output/resources.jsonl`。不要只看最后一句 CUDA OOM：Windows 系统提交量不足也可能造成该错误。
取消只停止本任务的子进程；重开后保留已完成草稿，中断任务不会悄悄自动重跑。
当前每次任务使用新进程，冷启动偏慢；共享常驻模型、热缓存和更低 RAM 的加载仍待优化。
