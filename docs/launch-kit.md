# 发布与演示素材 / Launch kit

主张 / Message: **从第一段音乐，到本地 AI 音乐工作台。 / Your first musical sketch, then a local AI workstation.**

先邀请零基础创作者完成一个可编辑作品。展示“用户自己改了什么、带走什么”，再展示模型。公开传播以当前可用功能为依据，不承诺专业 DAW 替代、SOTA 全覆盖或一键产出完整商业歌曲。

Invite beginners to finish an editable sketch. Show what they change and what they export, then introduce local models. Describe the current preview and hardware requirements accurately.

## 演示视频 / Demo video

首版素材是实际 UI 截图剪辑配软件导出的示例音频，标题注明“操作画面节选”；不是连续实时录屏，基础示例不是 AI 生成。可作为 GitHub/短视频的演示预览。发布包提供 MP4；仓库提供无声 GIF 预览。更长版本可按以下分镜补录。

The first cut combines real UI screenshots with the exported tutorial example and is labelled edited UI highlights. It is not continuous real-time capture; the basic example is not AI-generated. An MP4 is provided with the release and a silent GIF in the repository. Use this storyboard for a longer recording.

| 时间 / Time | 画面 / Shot | 字幕或口播 / Caption or narration |
| --- | --- | --- |
| 0–5 s | 工作台四轨 / Four-track view | “没学过编曲，也可以先改出第一段音乐。” / “Start with a sketch you can change.” |
| 5–12 s | 鼓独奏并还原 / Solo drums, then restore | “先拆开听：鼓、贝斯、键盘与氛围。” / “Hear the parts before changing the whole.” |
| 12–22 s | 钢琴卷帘改一个音 / Change one note | “从一个音开始，随时撤销。” / “Make one note yours. Undo any time.” |
| 22–30 s | 贝斯音量降低 / Lower bass fader | “给主角留出空间。” / “Make room for the main idea.” |
| 30–38 s | WAV/MWB 导出与跟练完成 / Export and finish | “带走音频，也保留可以继续编辑的工程。” / “Keep the audio and the editable project.” |
| 38–45 s | AI 配置页 / AI setup | “再把本地开源模型加入流程。首批自动配置 ACE-Step。” / “Add local AI when ready. ACE-Step setup included.” |

AI 演示建议另做第二条，录制实际生成 → 试听 → 入轨 → 对拍/裁切 → 混音。等待若加速，显式写出实际耗时与硬件。先做 12 秒草稿，避免让用户把快速剪辑误认为瞬时生成。

Make local AI a second video: real generation → audition → adoption → fit/trim → mix. Label sped-up waits with actual time and hardware.

## 发布文案草稿 / Post drafts

**中文标题**：做了个开源音乐工作台：不用配 Python，先跟着改出第一段音乐

**中文正文**：Music Workbench 是本地运行的开源创作工具。下载 Windows 安装器后，跟着软件里的五步教程试听音轨、改音符、混音并导出 WAV。基础创作无需模型；想继续尝试 AI，可在软件里配置 ACE-Step，再把生成素材放回自己的编排。当前是开发预览，欢迎反馈最影响创作的三个问题。下载与源码：https://github.com/Hydr0g3ngz/music-workbench

**English title**: An open local music workbench, with a first sketch you can actually edit

**English copy**: Install the Windows preview, follow five in-app steps, change a note, balance the mix and export a WAV. Basic creation needs no model setup. When ready, configure local ACE-Step and bring generated material into your arrangement. This is a development preview; feedback on the three biggest workflow obstacles is welcome. https://github.com/Hydr0g3ngz/music-workbench

## 发布顺序 / Distribution plan

1. GitHub 发布页：安装器、校验文件、教程、已知限制、示例工程、短片；README 前屏提供明确下载入口与动态预览。
2. 找 3–5 位目标用户试用，记录启动失败、跟练卡点、导出成功与主观反馈；不开隐式遥测。
3. 经用户发布到 B 站/小红书，分别以实操演示和制作过程为内容。社区分享遵循规则，披露作者身份，提供可复现示例。
4. 先解决试用最常见的阻碍，再发布 AI 深入制作演示。关注首次完成创作与复用意愿，stars 作为结果指标。

Publish artifacts and a clear download path, observe a small set of novice trials without hidden telemetry, then share reproducible demos with author disclosure. Prioritize successful first exports and repeat use; stars are an outcome. These posts are drafts and have not been sent to any external community.
