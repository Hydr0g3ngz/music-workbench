# 采样音色、鼓点与 MIDI

[English](creation-library.en.md) · [启动工作台](create-preview.md)

先试听音色或鼓点，再放进多轨工程。基础采样与三个合成音色随软件提供，使用时无需下载模型、显卡或联网。

## 从空工程开始

1. 打开左侧「乐器」，试听采样三角钢琴、马林巴或原声鼓组，点音色卡加入乐器轨。
2. 在「素材库」试听八种鼓点，点 `＋` 或拖入时间轴。两小节模板按工程 BPM 播放。
3. 双击 MIDI 片段打开钢琴卷帘，双击网格加音符、双击音符移除。点击音符后，
   在检查器修改音高、开始拍、时长和力度；鼓组键盘显示底鼓、军鼓、镲片等名称。
4. 点击「导入音频 / MIDI」导入自己的 `.mid` / `.midi` 文件。确认窗口显示声部、
   音符数量、时长、初始速度及转换说明。
5. 保存、撤销、重开、换音色、混音、导出 WAV/MIDI，使用同一份工程。

窄窗口也能通过左侧图标打开素材库和检查器，顶部保留工程菜单与新建入口。
素材试听不会增加轨道；后台任务刷新不会重载正在播放的采样或音频。

## 包含什么

| 内容 | 当前实现 | 来源与许可 |
| --- | --- | --- |
| 钢琴 | 9 个采样根音，按最近根音移调 | VCSL，CC0 |
| 马林巴 | 5 个采样根音，按最近根音移调 | VCSL，CC0 |
| 鼓组 | 9 个 one-shot，映射常见 GM 鼓音高；后续踩镲会截断前一个踩镲 | VCSL，CC0 |
| 鼓点 | 流行、摇滚、放克、嘻哈、灵魂、爵士、拉丁、非洲节拍；各两小节 | Groove MIDI Dataset，CC BY 4.0 |

23 个 FLAC 合计约 3.6 MB。它们是轻量、单力度层选集，不是完整 VCSL、SFZ 播放器、
专业鼓库或 VST 宿主。未覆盖的打击乐以闭镲近似代替，保留原 MIDI 音符并在导入时提示。
音符力度控制音量；暂不包含多力度采样层、踏板共鸣或轮替采样。

浏览器和离线 WAV 导出共用采样资源与音符语义，包含起音、note-off 淡出与镲片截断。
仍受浏览器采样率与插值差异影响，不宣称逐采样一致。MIDI 导出使用乐器 program 和鼓通道 10。

## MIDI 转换边界

- 支持 Standard MIDI File 0/1，单文件最多 8 MiB、128 个 MIDI track、8192 音符、32 个声部、10 分钟。
- 保留音高、力度与实际演奏时刻。多段 tempo 转换到固定工程网格；CC64 延音转换为音符时长。
- 只有空工程可以采用文件的初始 BPM。非 4/4 音符时间保留，界面仍使用 4/4 网格。
- 超过单片段容量的密集声部会分成多个片段，保留全部音符。
- 部分 GM 乐器近似映射到钢琴、马林巴、贝斯或鼓组；弯音、其他 CC、自动化暂未导入。
- SMF 2、SMPTE 时间基准和超出上限的文件会明确拒绝。
- 原始 MIDI 按 SHA256 保存到工作区 `.midi-originals`，转换不覆盖原文件。

## 来源与署名

音色来自 [Versilian Community Sample Library](https://github.com/sgossner/VCSL)，
固定代码修订 `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e`。
采样经过起音裁剪、归一化、截短/淡出和格式转换。

鼓点取自 [Groove MIDI Dataset](https://magenta.withgoogle.com/datasets/groove) v1.0.0
训练集的八个两小节片段，保留鼓手微时序与力度，统一短音符时值并映射少量鼓音高。
作者为 Jon Gillick、Adam Roberts、Jesse Engel、Douglas Eck、David Bamman、Google LLC
及 manifest 标明的鼓手。训练集素材不用于声明模型测试集成绩。

选择「导出作品 → 素材来源与署名」，可导出实际使用模板的作者、来源、许可与修改说明。
完整记录见 `src/music_studio/data/creation/NOTICE.md` 和 `manifest.json`；
每个源文件与派生采样都有哈希。需要重建时运行 `python scripts/build_creation_library.py`，
这是主动联网操作，应用启动不会运行它。

[技术验证 / Technical verification](feature-validation.md)。
