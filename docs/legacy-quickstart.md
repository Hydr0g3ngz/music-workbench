# 开始使用 / Getting started

> 历史参考：原 Music Studio 歌曲分析流程或拆分前版本。当前工作台请从 [安装与入门](README.md) 开始；原分析产品见 [Music Studio](https://github.com/Hydr0g3ngz/music-studio)。本页的功能、命令与测量按所述旧版本解释。

**Next · 0.2.0.dev2 音频工作台 / Audio workbench**

双击 **Start-Music-Studio-Next.cmd**，导入录音或打开带噪语音示例，点击“让讲话更清楚”。
首次 Next 依赖安装需联网；CPU 清理模型的权重需在界面明确安装。支持音量统一、A/B、
预览、采用、撤销和导出。[完整 Next 说明](next-preview.md)。

Double-click **Start-Music-Studio-Next.cmd**, import audio or try the noisy speech demo,
then choose **Clearer speech**. Initial dependency setup needs network access; install
CPU model weights explicitly in the UI. [Next guide](next-preview.en.md).
The classic launcher and its existing workspace remain separate; its guide follows.

**经典歌曲分析 · Classic song analysis · v0.1.2 workflow**

中文：解压到可写目录，双击 **Start-Music-Studio.cmd**。需已安装 Python 3.11 或 3.12；
首次启动联网安装 Python 依赖，之后自动打开本地浏览器界面。点击“加载示例歌曲”，
不下载神经模型即可试听 45 秒授权歌曲、切换人声/伴奏、修改歌词和导出。
右上角可切换中文 / English。停止服务请在启动窗口按 Ctrl+C。

English: extract into a writable folder and double-click **Start-Music-Studio.cmd**.
Install Python 3.11 or 3.12 first. Initial startup downloads Python dependencies and
opens the local browser workbench. Choose **Try the demo** to explore a 45-second
licensed song, switch stems, edit lyrics and export without neural-model downloads.
Switch 中文 / English at the top right. Keep the console open; Ctrl+C stops the server.

This ZIP includes application source, a Python wheel and a credited precomputed
example. **It is not a standalone EXE and does not bundle Python, CUDA or models.**
此 ZIP 含源码、Python wheel 和授权预计算示例；不是独立 EXE，不包含 Python、CUDA 或模型权重。

## 分析自己的歌曲 / Analyze your own songs

在解压目录打开 PowerShell / Open PowerShell in the extracted folder:

```powershell
# NVIDIA GPU (8GB VRAM is the main tested target)
.\scripts\setup.ps1 -Mode full -Device cuda -DownloadModels
# CPU alternative / 无 NVIDIA 显卡时使用 CPU（更慢）
# .\scripts\setup.ps1 -Mode full -Device cpu -DownloadModels
.\scripts\launch.ps1
```

模型下载由上述命令明确触发，可重新运行以复用缓存。启动器默认离线；
需要允许分析时下载缺失模型可用 `launch.ps1 -Online`。
The command explicitly downloads base models; rerun to reuse cached files.
The launcher defaults to offline mode. Use `launch.ps1 -Online` to allow missing-model downloads.

Qwen 更适合优先减少错词，需单独安装运行环境与权重，见 [中文说明](README.md) / [English guide](README.en.md).
Basic Whisper recognition is not specialized for singing; always review the text.

```powershell
# Optional Qwen recognition / 可选 Qwen 歌词识别
.\scripts\setup_lyrics.ps1
.\Start-Music-Studio.cmd
```

启动器会自动连接此独立环境，界面会停用未安装的识别模式。自定义环境可用
`scripts/launch.ps1 -LyricsPython 'C:\path\to\python.exe'`。安装后请先在原启动窗口按 Ctrl+C，再重新启动。
The launcher automatically connects the separate lyric environment. Uninstalled recognizers
are disabled in the UI. Use `scripts/launch.ps1 -LyricsPython 'C:\path\to\python.exe'`
for a custom environment. After installation, stop the old console with Ctrl+C and restart.

## 常见问题 / Troubleshooting

- 找不到 Python / Python not found: install 3.11/3.12 from [python.org](https://www.python.org/downloads/), then retry; or run `scripts/setup.ps1 -Python 'C:\path\to\python.exe' -Mode preview`.
- PowerShell 禁止脚本 / Scripts are blocked: use the `.cmd` launcher, which permits scripts for that process only. It does not change the system execution policy.
- 端口占用 / Port in use: the launcher finds a free port; use the URL it prints. It never stops another service.
- 模型缺失 / Missing models: finish the full installation and explicit download above. The demo remains usable without models.
- 下载失败 / Download failed: keep the log and rerun setup; no uploaded song is removed. Do not include personal songs or private paths in public issues.
- 升级 / Upgrade: keep `outputs/ui` (songs/results/corrections) and `.cache/models` (weights); copy them to the new extracted folder while the service is stopped. Do not run two servers on the same workspace.

示例音频 / Demo audio: **Let's Go Fishin' — Karissa Hobbs, CC BY 3.0**.
Changes: first 45 seconds, separated stems, compressed previews and machine estimates.
[Full attribution / 完整署名](../src/music_studio/ui/demo/ATTRIBUTION.md).
