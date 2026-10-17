# 本地音乐生成：ACE-Step 1.5

[English](music-generation.en.md) · [制作工作台](create-preview.md)

在「AI 模型 → 生成音乐草稿」描述风格、乐器和氛围，选择时长并运行。
草稿完成后先试听，再明确点击「加入工程」；生成、失败或取消不会改写编排。
加入后可移动、裁剪、调音量和淡入淡出，与采样乐器、鼓点和导入 MIDI 一起制作，最后导出 WAV。
加入工程可撤销，原始生成文件与参数仍保留。

## 安装与运行

Windows 安装版可从首页 **AI 自动配置** 完成准备，无需另外安装 Python。要求兼容 NVIDIA 显卡、至少 8 GB 显存、35 GB 可用空间与首次约 8–12 GB 下载。已验证配置为 Windows 11、RTX 4070 Laptop 8 GB、32 GB RAM；其他硬件速度与兼容性可能不同。[模型支持与要求](models.md)。

源码用户可在 Python 3.11/3.12 中，从仓库根目录手动安装：

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

[技术验证 / Technical verification](feature-validation.md)。

## 故障与数据

开启「使用已保存的创作蓝图与段落目标」，会将作品意图、音色、动机、和声方向与段落任务
加入实际提示词，BPM/调性跟随已保存工程。可先「预览实际提示词」，再提交任务。
规则负责组装提示词，本地 ACE-Step 负责音频生成；请试听判断结果是否符合意图。
详见 [编曲方法与流程](arranging-methods.md)。

「参数与诊断」提供错误和资源指标；完整日志在工作区 `.creation-tasks/<id>/worker.log`，
阶段内存记录在 `output/resources.jsonl`。不要只看最后一句 CUDA OOM：Windows 系统提交量不足也可能造成该错误。
取消只停止本任务的子进程；重开后保留已完成草稿，中断任务不会悄悄自动重跑。
当前每次任务使用新进程，冷启动偏慢；共享常驻模型、热缓存和更低 RAM 的加载仍待优化。
