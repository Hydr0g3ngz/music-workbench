# Workbench 与 Studio / Workbench and Studio

**Music Workbench** 用于创作、录音、MIDI 编辑、编排、混音和导出。**[Music Studio](https://github.com/Hydr0g3ngz/music-studio)** 用于分析已有歌曲的歌词、旋律、和弦、节拍和分轨结果。两者是独立软件，分别安装和更新。

Music Workbench creates and edits music. Music Studio analyzes existing songs. Each has its own installation and releases.

## 保存与迁移 / Save and transfer

- 安装版 Workbench 工程位于 `%LOCALAPPDATA%\MusicWorkbench\Projects`，模型位于 `%LOCALAPPDATA%\MusicWorkbench\AI`。
- 源码版默认使用 `outputs/workbench`。换电脑、换工作区或从源码版转到安装版时，先导出包含音频的 `.mwb`，再在目标软件中恢复。
- 普通音频可以在两个产品间导入；Studio 的歌曲分析目录不是 Workbench 多轨工程。

Installed Workbench projects and AI tools live in separate folders under `%LOCALAPPDATA%\MusicWorkbench`. Source projects default to `outputs/workbench`. Transfer complete arrangements with MWB; audio can be imported by either product.

## 工作台里的素材编辑器 / Asset editor

转写结果的 **详细结果与编辑** 会打开单素材编辑器，可以修改识别文字并导出文本或字幕。通过页面中的返回入口回到多轨工程。

**Detailed results & editing** opens the single-asset editor for text corrections and subtitle exports. Use its return link to go back to the arrangement.

[安装与更新 / Installation](windows-install.md) · [素材编辑器指南 / Asset editor](next-preview.md)
