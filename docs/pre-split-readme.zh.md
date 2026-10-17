# Music Studio

> 历史参考：原 Music Studio 歌曲分析流程或拆分前版本。当前工作台请从 [安装与入门](README.md) 开始；原分析产品见 [Music Studio](https://github.com/Hydr0g3ngz/music-studio)。本页的功能、命令与测量按所述旧版本解释。

> **Create · 0.2.0.dev5：从想法到作品的制作工作台预览**。采样乐器、鼓点、MIDI 导入、多轨编排、混音台与 WAV/MIDI 导出。
> 双击 `Start-Music-Studio-Create.cmd`，或阅读[启动与功能范围](create-preview.md)。旧版与旧数据保留；录音、总线与自动化仍在开发。
> 新增：[实时 EQ、压缩、混响、预设与主输出限制](mixing.md)，播放中调参、A/B，带尾音导出。
> [真实采样音色、八种鼓点、MIDI 导入与音符属性编辑](creation-library.md)，随软件离线提供。
> 新增：[现代分轨 → 试听 → 对齐替换轨道](separation.md)，保留原素材、一次撤销；附固定测试集实测。
> 可选：[本地 ACE-Step 音乐生成](music-generation.md)，先试听再入轨；包含实机资源与失败记录。
> [本地模型、开放素材与数据库调研](audio-resources.md) · [完整模型候选](local-model-candidates.md)

![音乐制作工作台开发预览](images/create-effects-zh.png)

> **Next · 0.2.0.dev2**：本地音频 AI 工作台。清理讲话、统一听感音量、同位置 A/B，
> 满意后再采用，随时撤销。也能裁剪、混音、分轨、转写改字、提取 MIDI 与节拍。
> MCP / Codex 与界面共用项目、任务、素材和预览。语音清理可用 CPU，无需显卡。
> [体验 Next](next-preview.md) · [开发计划](workbench-plan.md) ·
> [语音清理实测](speech-cleanup.md) · [旋律模型对比](melody-next.md)。旧版 **v0.1.2** 与已有数据独立保留；
> [本地模型与安装](next-models.md)。下面仍是经典版说明；旋律质量等改进持续进行。

![Next 语音清理工作台](images/next-cleanup-workbench-zh.png)

*Next 实机界面；CC BY 4.0 带噪语音示例、真实 CPU 降噪与响度测量。模型并不保证每个片段都改善，逐例退步见实测报告。*

[English](pre-split-readme.en.md) · [下载预览版](https://github.com/Hydr0g3ngz/music-studio/releases) · [快速开始](legacy-quickstart.md) · [实测](lyrics-v4.md) · [路线图](roadmap.md)

**把一首歌，展开成可以同步试听的人声、伴奏、歌词、主旋律 MIDI、和弦与节拍。**

在本机处理，通过浏览器使用。无需账号或付费 API；歌曲不会上传到云端。
界面支持 **中文 / English**，可记住选择。模型首次安装需下载，缓存后可离线推理。

![Music Studio 中文工作台](images/workbench-zh.jpg)

*真实界面。示例：Let's Go Fishin' — Karissa Hobbs，CC BY 3.0。歌词、时间与音符为机器估计。*

## 先听到声音，再决定下载模型

1. 从 [Releases](https://github.com/Hydr0g3ngz/music-studio/releases) 下载 Windows ZIP，解压到可写目录。
2. 安装 **Python 3.11 / 3.12**，双击 `Start-Music-Studio.cmd`；首次会联网安装 Python 依赖。
3. 点击 **加载示例歌曲**，立即探索 45 秒预计算授权示例，切换原曲、人声与伴奏，改字并导出。无需下载神经模型。

**这是早期预览版。ZIP 包含源码、wheel 和授权示例，不是独立 EXE，不包含 Python、CUDA 或模型权重。**
详细安装、CPU 选项、故障处理和升级保留数据见 [快速开始](legacy-quickstart.md)。

从源码体验：

```powershell
git clone https://github.com/Hydr0g3ngz/music-studio.git
cd music-studio
.\scripts\setup.ps1 -Mode preview
.\scripts\launch.ps1
```

分析自己的歌曲，明确安装推理依赖与基础模型：

```powershell
.\scripts\setup.ps1 -Mode full -Device cuda -DownloadModels
# 无 NVIDIA 显卡时改用 -Device cpu（推理较慢）
.\scripts\launch.ps1
```

启动器默认离线并自动选择空闲端口；不停止已有服务。浏览器地址以启动窗口为准。
NVIDIA 8GB 显存为主要本地验证目标；macOS、AMD / Intel GPU 推理尚未验证。
Linux 手动安装、Qwen 与双模型锚点、CLI 和输出格式见 [详细使用说明](usage.zh-CN.md)。

## 一条时间轴，完成听、改、带走

| 场景 | 可以做什么 |
| --- | --- |
| 听清每一层 | Demucs 分离人声与伴奏；三轨切换保留位置，按需缓存；旋律 MIDI 可合成试听 |
| 改对歌词 | Whisper / 可选 Qwen 识别；点击逐句试听、循环上下文、文字纠错、粘贴正确歌词并对齐 |
| 核对难句 | 分开提示文字疑点与缺失时间；单句换模型生成候选，比较后明确采用；旧版本和改字保留 |
| 学唱与练习 | 大字跟唱视图，伴奏叠加可调原唱提示，逐句跳转与循环 |
| 带走结果 | LRC / SRT、主旋律 MIDI、人声 / 伴奏音频、和弦 / 节拍 CSV、完整项目 JSON |
| 管理歌曲 | 搜索、重命名、删除、撤销、回收站恢复；停止 / 继续分析，已有歌曲可用新模型重跑 |

![跟唱视图](images/singalong.jpg)

*同一首 CC BY 3.0 授权示例。歌曲名与用户歌词保持原文，不随界面语言翻译。*

## 准确率用实测说明

冻结评测共 **43 例**：原 26 例组件回归，加 17 首中文卡拉 OK 录音。
新增数据先按歌手 / 歌词重合划分 8 首开发与 9 首确认，不自行补人工标签。

| 固定条件 | 结果 |
| --- | --- |
| 中文确认集 9 首 / 1113 参考字 | Whisper small CER **45.28%** → Qwen3-ASR 1.7B **14.65%** |
| 同一份 Qwen 文字，7 首英语回归 | 正确且起音误差 ≤200ms / 全部时间参考词：**52.83% → 59.14%** |
| 中文确认集的双模型锚点 | 时间覆盖提高，但起音 P90 **0.616s → 0.713s**，因此仍为可选项 |

这是小规模工程验证，含不同录音域，模型预训练重叠未知，不代表任意商业歌曲的准确率。
灰字只表示缺少可靠词时间，不等于错词。主旋律是单主唱估计，和弦目前为大小三和弦 / N；
自动结果仍需试听核对，核对标记与模型分数不是正确率。长歌曲占用更多浏览器内存。

[完整报告与逐例结果](lyrics-v4.md) · [数据来源与复现命令](../benchmarks/README.md) · [算法与时间基准](architecture.md)

## 一起改进

欢迎用中文或英文提交可复现的安装、播放、识别问题。优先反馈：哪一步阻碍首次试听、
哪句歌词难以修正、哪种导出不好用。请先用内置授权示例复现，避免公开私人音频。

[贡献指南](../CONTRIBUTING.zh-CN.md) · [English contributing guide](../CONTRIBUTING.md) · [路线图](roadmap.md) · [版本记录](../CHANGELOG.md)

```sh
python -m pip install -e ".[ui,benchmark,dev]"
python -m ruff check .
python -m pytest -q
node --test tests/ui_playback.test.cjs tests/ui_i18n.test.cjs
python scripts/package_release.py
```

核心 / API / 播放测试不下载神经模型；真实模型评测需另行执行。前端没有构建步骤或外部 CDN。
代码采用 [MIT](../LICENSE)。模型、数据与示例录音各自保留原许可，见 [第三方说明](../THIRD_PARTY_NOTICES.md)
与 [示例署名](../src/music_studio/ui/demo/ATTRIBUTION.md)。
