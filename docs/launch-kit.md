# 演示与媒体素材 / Media kit

Music Workbench 是本地运行的开源音乐创作工作台，提供可编辑音轨、MIDI、录音、混音及可选本地 AI。

Music Workbench is an open-source local music workstation with editable tracks, MIDI, recording, mixing and optional local AI.

## 下载素材 / Assets

| 素材 / Asset | 内容 / Contents |
| --- | --- |
| [入门宣传片 / Introductory film](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/Music-Workbench-dev21-Promo-1080p.mp4) | 实机录屏、作品原声、VoxCPM2 合成旁白与字幕 / Real UI footage, original examples, synthetic narration and subtitles |
| [GIF](images/first-sketch-demo.gif) | 无声界面预览 / Silent interface preview |
| [可编辑示例 / Editable MWB](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/First-Sketch-Example.mwb) | 八小节、四轨示例，可恢复后修改 / Eight bars, four tracks, ready to restore and edit |
| [入门教程 / Beginner lesson](first-sketch.md) | 软件内五步跟练的操作说明 / Companion guide to the five in-app steps |
| [安装器与校验 / Installer and checksums](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev21) | Windows 预览版 / Windows preview |

入门跟练使用内置乐器，无需 AI；《雨后的街灯》案例使用 ACE-Step 与 Transkun。视频采用实际操作录屏，生成等待经过剪辑并注明实测时间，配音为 VoxCPM2 合成女声。

The beginner lesson uses built-in instruments without AI; After the Rain uses ACE-Step and Transkun. The film edits real UI recordings, identifies shortened waits with measured times, and uses VoxCPM2 synthetic narration.

## 项目简介 / Description

**中文**：从一段可编辑音乐开始，用采样乐器、MIDI、多轨剪辑与混音完成自己的草稿。Music Workbench 提供 Windows 安装器和软件内双语教程，基础创作无需配置 Python 或下载模型；可选 ACE-Step 本地 AI 帮助生成、变奏和重绘素材。

**English**: Start with an editable sketch and make it yours with sampled instruments, MIDI, multitrack editing and mixing. Music Workbench includes a Windows installer and bilingual in-app lesson. Basic creation needs no Python setup or model download; optional local ACE-Step adds generated material, variations and region repaint.

## 录制一段演示 / Record a walkthrough

1. 从首页新建教程示例，试听四轨。Create a lesson example and play its four layers.
2. 独奏鼓，再恢复整体。Solo the drums, then restore the mix.
3. 在钢琴卷帘中移动一个音符，演示撤销。Move a note in the piano roll and undo it.
4. 调整贝斯音量，导出 WAV 与 MWB。Balance the bass and export audio plus the editable project.
5. 若展示 AI，单独记录生成、试听、采用和适配；标明硬件及实际等待时间。For AI, record generation, audition, adoption and fitting; label hardware and elapsed time.

## 版本与署名 / Version and attribution

当前发布是 Windows 10 22H2 / 11 x64 开发预览，安装器未签名。ACE-Step 自动配置需要兼容 NVIDIA ≥8 GB 显卡与 35 GB 空间；其他模型安装方式见 [模型目录](models.md)。功能状态与限制以 [发布说明](releases/v0.2.0.dev21.md) 为准。

The release is an unsigned Windows development preview. ACE-Step automatic setup requires a compatible NVIDIA GPU with at least 8 GB VRAM and 35 GB free space. Other models have separate setup paths; see [supported models](models.en.md) and [release notes](releases/v0.2.0.dev21.md).

介绍项目时请附上 [源码与下载入口](https://github.com/Hydr0g3ngz/music-workbench)。代码、模型权重、截图中的素材及示例工程分别适用其许可，详见 [第三方说明](../THIRD_PARTY_NOTICES.md)；导出工程的素材署名可从软件取得。

Link to the [repository](https://github.com/Hydr0g3ngz/music-workbench) when introducing the project. Code, models and example assets have separate licenses; see [third-party notices](../THIRD_PARTY_NOTICES.md) and export project credits from the app.
