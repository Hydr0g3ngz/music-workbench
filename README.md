# Music Workbench

[English](README.en.md) · [中文](README.md)

本地运行的开源音乐创作工作台。用可编辑音轨、MIDI、混音与本地 AI，把一段灵感做成可以保存的作品。

[**下载 Windows 安装器**](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/Music-Workbench-0.2.0.dev14-Setup-x64.exe) · [看 36 秒演示（有声）](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/Music-Workbench-First-Sketch-Demo.mp4) · [入门教程](docs/first-sketch.md) · [版本与校验](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev14)

Windows 10 22H2 / 11 x64 · 中文 / English · 开发预览，安装器未签名

![实际界面节选：试听、改音符、混音、导出](docs/images/first-sketch-demo.gif)

## 第一次用，从这里开始

安装 → 首页选 **跟着做出第一段音乐** → 试听、分层、改一个音、调混音、导出 WAV。软件内五步跟练会定位按钮、记录真实操作，支持关闭后继续、跳过与重新学习。基础示例无需下载模型，约 5–10 分钟。可在顶部 **入门** 打开教程，也可阅读软件内的完整离线手册。

[教程与实际验收](docs/first-sketch.md) · [可编辑示例工程 MWB](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev14/First-Sketch-Example.mwb) · [宣传素材与分镜](docs/launch-kit.md)

演示为实际操作截图剪辑，配软件导出的示例音乐；基础示例不是 AI 生成。先把制作平台与本地模型做好，再做深入 Agent 集成。

## 与 Music Studio 分开

本仓库独立开发大型工作台。原来的歌曲分离、歌词、旋律、和弦与节拍分析项目保留在 [Music Studio](https://github.com/Hydr0g3ngz/music-studio)。两者独立发布、独立启动、独立保存项目。

## 启动

Windows 安装预览版（`Setup-x64.exe`）：下载并安装，从桌面或开始菜单打开 **Music Workbench**，直接进入独立的软件窗口。自带基础运行时，无需安装 Python、输入命令或管理浏览器。[安装说明](docs/windows-install.md)。

首页的 **AI 自动配置** 会检查电脑、下载独立环境和模型、校验文件，并实际生成一段音乐后再启用 ACE-Step。首批自动配置支持 Windows x64、NVIDIA 8 GB 显存；首次需联网和 35 GB 可用空间。其他模型的自动环境安装仍在接入中。基础乐器、录音、剪辑、编排和混音无需模型。

源码用户：配置 Python 3.11/3.12 和基础环境，再用 `Start-Music-Workbench.cmd`，或：

源码：

```sh
python -m pip install -e ".[workstation]"
music-workbench
```

源码默认端口 8920、目录 `outputs/workbench`；便携版作品在 `%LOCALAPPDATA%\MusicWorkbench\Projects`。重复启动复用同目录服务，空闲端口自动选择。不会自动迁移或覆盖旧项目。当前是开发预览，并非完整 DAW。

新增：**本地录音 → 试听 → 从播放头入轨**，支持设备选择、电平、WAV 下载与撤销。[使用说明与限制](docs/recording.md)。

**反复打磨一段作品**：自定义循环小节、使用所选片段设置区间，以及可调音量与重拍的节拍器。设置随工程保存，导出完整作品。[循环与节拍器](docs/timing.md)。

**用实际作品检验流程**：《云隙电台》，64 秒、32 小节、9 轨。用本地 ACE-Step 生成主题与参考变奏，Demucs 拆成四个声部，再用 CREPE 把贝斯转成可编辑 MIDI，完成编排与混音。这次没有外部脚本写入完整乐谱；工程包在新目录恢复后导出一致。[创作记录与测量](docs/creations/radio-through-the-clouds.md) · [AI 如何嵌入各阶段](docs/ai-production-workflow.md)。这是实际功能验收，尚无盲听质量结论。

上一次《末班车后的微光》暴露的编辑问题已进入本轮改进：音符拖动、拉长、框选、批量力度/量化、段落复制、小节定位、整首适配视图、便携工程与响度反馈。[开发顺序](docs/workbench-roadmap.md) · [首作 MIDI 源码](examples/after-the-last-tram/compose.py)。

## 已有能力

- 可编辑音量曲线、线性/等功率交叉淡化；从过渡编辑进入 AI 局部重绘，试听后采用，选区外采样保持不变。[用法与实测](docs/volume-and-repaint.md)。
- 素材对拍：波形选拍、半速/倍速、两拍 BPM 校准；生成/处理候选的等响度 A/B，支持先试听再采用。[使用与基准](docs/material-fitting.md)。
- 创作蓝图、段落角色/能量/意图、三种可编辑结构草案；AI 生成读取工程上下文，预览实际提示词并保留版本。[编曲方法与操作](docs/arranging-methods.md)。
- 采样乐器、鼓点、MIDI 导入；音符拖动/拉长、多选、复制、移调、量化和力度编辑。
- 段落标记、跨轨段落复制、小节定位、调性/音阶提示，多轨编排与撤销。
- EQ、压缩、混响、混音；WAV/MIDI 导出、电平与 LUFS/真峰值测量、便携 `.mwb` 工程恢复。
- 可选本地 ACE-Step 文本生成/参考变奏、RoFormer/Demucs 分轨、四声部分离与单旋律 MIDI 提取。
- 素材速度/调性估计、独立变速变调（DSP，原素材保留）。
- 模型隔离安装、任务队列、先试听再采用，保留原素材。
- 中文 / English 界面。

[制作入门](docs/create-preview.md) · [模型安装](docs/next-models.md) · [生成](docs/music-generation.md) · [分轨实测](docs/separation.md) · [路线图](docs/workbench-roadmap.md)

MIT 仅适用于本项目代码；各模型权重与素材的许可独立适用，安装前查看对应说明。模型权重不随源码分发。
