# Music Workbench

[English](README.en.md) · [中文](README.md)

本地、开源的音乐创作工作台：从想法到素材、编排、混音和导出。先把制作平台与本地模型做好，再接入 Agent。

![工作台](docs/images/create-effects-zh.png)

## 与 Music Studio 分开

本仓库独立开发大型工作台。原来的歌曲分离、歌词、旋律、和弦与节拍分析项目保留在 [Music Studio](https://github.com/Hydr0g3ngz/music-studio)。两者独立发布、独立启动、独立保存项目。

## 启动

Windows：安装 Python 3.11/3.12，双击 `Start-Music-Workbench.cmd`。首次安装基础依赖，模型单独安装。

源码：

```sh
python -m pip install -e ".[ui,audio]"
music-workbench
```

默认端口 8920，项目目录 `outputs/workbench`。不会自动迁移或覆盖旧项目。当前是开发预览，并非完整 DAW。

## 已有能力

- 采样乐器、鼓点、MIDI 导入和音符编辑，多轨编排与撤销。
- EQ、压缩、混响、混音、WAV/MIDI 导出。
- 可选本地 ACE-Step 生成、RoFormer/Demucs 分轨、转写与音高分析。
- 模型隔离安装、任务队列、先试听再采用，保留原素材。
- 中文 / English 界面。

[制作入门](docs/create-preview.md) · [模型安装](docs/next-models.md) · [生成](docs/music-generation.md) · [分轨实测](docs/separation.md) · [路线图](docs/workbench-roadmap.md)

MIT 仅适用于本项目代码；各模型权重与素材的许可独立适用，安装前查看对应说明。模型权重不随源码分发。
