# 雨后的街灯 / After the Rain

[下载示例工程包 / Example projects](../examples.md) · [音符整理 / Note tools](../note-editing.md)

雨停后的街道，一盏灯映在水面上。独奏钢琴代表街灯，马林巴的短音像水滴；中段变奏改变水面的颜色，最后回到最初的钢琴。这份工程适合学习：怎样把一段生成音频发展成有起伏的作品。

A piano stands for a streetlight, with marimba notes like droplets. A middle variation changes the reflection, then the original piano returns. Use this project to explore how one generated phrase can become a small piece.

![32-bar arrangement](../images/after-the-rain-dev21.png)

## 先打开听 / Start by listening

从 [示例包](../examples.md) 恢复 `After-the-Rain.mwb`。音频、音符、效果和编排已包含，不需要 AI 模型就能播放和编辑。依次独奏钢琴、马林巴和变奏轨，再恢复全部声音，比较它们的分工。

Restore `After-the-Rain.mwb` from the example pack. Audio, notes, effects and arrangement are included. Solo the three tracks in turn, then listen to them together. No model download is needed to play or edit existing material.

## 怎样制作 / Make your own version

1. **定方向。** 新建 120 BPM、4/4 工程。向 ACE-Step 描述独奏钢琴、上行短动机、雨后明亮氛围，无鼓无人声；请求 C major。生成的节奏与和声仍需核对。
2. **选主题。** 本例使用 ACE-Step 1.5 Turbo，20 秒、seed 42、8 步。试听候选后加入轨道，裁成 8 小节；设置约 0.02 秒淡入、0.2 秒淡出。
3. **写回应。** 用 Transkun 转录钢琴，试听后加入乐器轨。打开整理声部，尝试 MIDI 60–84、最小力度 45、相近起音取最高音。本例把 28 个估计音符减为 12 个，再换成马林巴；这是编曲取舍，不是自动纠错。
4. **安排段落。** 两个片段成组，复制到第 9、17、25 小节。建立“雨停、街灯、水面、归家”四段，第一段留钢琴独奏，第二段加入回应。
5. **改变中段。** 从原钢琴做 16 秒参考变奏，试听后放入第三段，替换该段原钢琴，给前后主题留下对比。
6. **混音收尾。** 三轨输出到分组总线，再用小发送量进入 100% 湿声混响。马林巴降低至约 −17 dB、变奏 −2 dB；结尾片段降低 3 dB 并淡出 3 秒。
7. **保存。** WAV 保存完整声音，MIDI 只保存可编辑的马林巴音符，MWB 保留全部编排与音频。修改前后各留一个 MWB，方便比较。

Start with a piano theme, transcribe an upper part into marimba, copy the phrase into four sections, add a contrasting reference variation, then balance shared effects and fade the return. Save WAV for the mix and MWB for further editing. The MIDI export contains the editable marimba part.

## 可以尝试的变化 / Try a change

- 让马林巴晚两拍进入，听留白是否更自然。Delay the echo by two beats.
- 关闭共享混响，再少量打开，比较空间感。Compare dry and shared reverb.
- 给第三段换一个音色，而保留它的进入位置。Change the contrast's timbre without changing its placement.

工程为 32 小节、三轨、两条总线，含尾音约 65.7 秒。模型输出是估计和候选；重新生成不一定重复本例。模型使用 [ACE-Step](https://github.com/ACE-Step/ACE-Step-1.5) 与 [Transkun](https://github.com/Yujia-Yan/Transkun)，马林巴采样来自 [VCSL](https://github.com/sgossner/VCSL)。来源署名可随作品导出。

The project has 32 bars, three tracks and two buses, about 65.7 seconds including tails. New generations can differ. Model and sample terms apply separately; export project credits when sharing.
