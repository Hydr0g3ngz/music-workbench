# Music Studio 详细使用说明

> 历史参考：原 Music Studio 歌曲分析流程或拆分前版本。当前工作台请从 [安装与入门](README.md) 开始；原分析产品见 [Music Studio](https://github.com/Hydr0g3ngz/music-studio)。本页的功能、命令与测量按所述旧版本解释。

快速体验请先阅读 [历史首页](pre-split-readme.zh.md) 与 [历史快速开始](legacy-quickstart.md)。

[English](pre-split-readme.en.md) · [实测与取舍](../docs/lyrics-v4.md) · [产品路线图](../docs/roadmap.md) · [贡献](../CONTRIBUTING.md)

**本地运行的开源扒歌引擎：歌曲 → 人声 / 伴奏 + 带时间的歌词 + 主唱旋律 MIDI + 和弦 + 节拍。**

Local-first song analysis with a shared audio timeline. Runs on your computer; no account, paid API, hosted inference, or audio upload. Model installation requires downloads; cached models support offline inference.

v0.1 提供本地网页工作台、命令行和 Python 引擎，支持同步试听与歌词文字纠错。当前范围不包含音符编辑、简谱和五线谱编辑器。

![Music Studio 工作台](../docs/images/workbench.jpg)

*实际分析与界面截图。示例：Karissa Hobbs — Let's Go Fishin'，CC BY 3.0；歌词和音符是自动估计。*

## 功能

- MP3、WAV、FLAC、M4A 等由 PyAV 解码的音频格式。
- Demucs 人声与伴奏分离，保留原曲时长、起点和采样率。
- Whisper / 可选Qwen3-ASR自动识别歌词，独立选择时间定位方式，并标出未定位的字词。
- CREPE 单声部人声音高与音符提取；可选择 pYIN 作为 CPU 基线。
- 节拍 / 全局 BPM，以及大小三和弦估计。
- 原始音高曲线、歌词与音符的时间重叠关联。
- 主旋律 MIDI（含节拍速度映射）、LRC、SRT、和弦 / 节拍 CSV、完整项目 JSON。
- 分阶段独立进程、低显存分段、结果缓存、失败后续跑、输出完整性检查。
- 本地 UI：导入音频、示例歌曲、项目搜索 / 重命名、删除 / 撤销 / 回收站恢复、分析进度、停止 / 继续分析。
- 同步时间轴：真实波形、音高曲线、音符、歌词、和弦和节拍；点击定位、逐词高亮、单句循环。
- 原曲 / 人声 / 伴奏切换，以及主旋律合成试听和结果下载。
- 逐句歌词纠错、恢复识别原文、持久保存与同步导出；上一句 / 下一句与键盘定位。
- 重新分析 / 仅更新歌词、结果版本比较与切回，纠词与所属版本绑定。
- 可选 Qwen3-ASR / HeartTranscriptor、独立时间对齐、粘贴完整歌词和单句重识别。
- 歌词核对筛选、下一处核对、持久核对记录；单句重识别先比较候选，再明确采用。
- 跟唱视图：当前句与前后句、伴奏与原唱提示音量、逐句定位和循环试听。
- 固定 43 例公开标注 benchmark（原 26 例 + 新增 17 首中文录音），独立评分、失败记录及显存 / 耗时采样。

## 歌词 v4 历史实测

新增中文确认集 9 首、1113 个参考字：Whisper small CER **45.28%**，Qwen3-ASR 1.7B CER **14.65%**。同一份 Qwen 文字使用双模型时间锚点后，7 首英语混音的“正确且起音误差 ≤200ms / 全部时间参考词”从 **52.83% 提高到 59.14%**。中文确认集的时间覆盖提高，P90 却从 0.616 秒增至 0.713 秒，因此保留轻量方案，双模型按需选择。

这些是小规模工程验证，包含不同录音域，模型预训练重叠未知。完整数据、逐例回退和资源范围见 [v4 报告](../docs/lyrics-v4.md)，没有把时间算法的收益记成文字识别收益。

## 安装

需要 **Python 3.11 或 3.12**。建议先以 NVIDIA CUDA 显卡运行；CPU 可用但处理速度取决于设备和模型。8GB 显存是首版的主要适配目标，具体实测见 [验证记录](../docs/validation.md)。

Windows PowerShell，在仓库根目录运行：

```powershell
# 创建 .venv 并安装 CUDA 版依赖；安装较大的 PyTorch 包可能需要一些时间
.\scripts\setup.ps1 -Device cuda

# 或安装 CPU 版
.\scripts\setup.ps1 -Device cpu
```

也可以手动安装：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
.\.venv\Scripts\python.exe -m pip install -e ".[ui,inference]"
.\.venv\Scripts\music-studio.exe doctor
```

Linux 使用 `python3.12 -m venv .venv`，激活环境后执行同样的 pip 安装命令。纯 CPU 将 PyTorch 索引地址改为 `https://download.pytorch.org/whl/cpu`。首版未验证 macOS / AMD / Intel GPU 后端。

核心与 UI 测试安装 `.[ui,dev]`；完整歌曲分析需要 `.[inference]`，网页界面额外需要 `.[ui]`。PyAV 的安装包提供解码库，本项目的处理流程不依赖外部 `ffmpeg` 命令。

## 使用

启动本地工作台：

```powershell
.\.venv\Scripts\music-studio.exe ui --model-dir ".cache\models" --open

# 已经下载模型后，可直接离线运行
.\.venv\Scripts\music-studio.exe ui --model-dir ".cache\models" --offline --open
```

浏览器打开服务打印的地址（手动启动默认 http://127.0.0.1:8765）。点击「加载示例歌曲」可直接体验随包提供的 45 秒预计算授权示例，无需联网或下载模型。示例为 Karissa Hobbs — Let's Go Fishin'（CC BY 3.0）；自己的歌曲需安装推理依赖与模型后再开始分析。

分析完成后，点击时间轴或歌词定位，切换原曲、人声、伴奏及旋律 MIDI 试听。点击歌词旁的铅笔修改文字；修改句保留整句时间并按整句高亮，旧的逐词时间不会冒充新文字的对齐。LRC / SRT / JSON / MIDI 同步使用修改后的文字，可随时恢复原文。

歌曲名称右侧可重命名或删除，也可以从左侧列表删除。删除移入回收站，支持立即撤销和重启后恢复，原音频与分析结果一并保留；运行中的歌曲需先停止。空格播放 / 暂停，左右方向键前后 5 秒，上下方向键上一句 / 下一句。

界面和推理都在本机运行。文件选择后的传输仅到本机服务；不需要账号或云服务。服务只监听 `127.0.0.1`，一次分析一首歌。项目保存在 `outputs/ui/`，重新启动仍可选择；可用 `--workspace` 和 `--port` 改变目录或端口。在终端按 Ctrl+C 关闭服务，已完成阶段会保留。播放器先加载原曲，人声和伴奏首次切换时加载并缓存；长曲仍会占用较多浏览器内存。

点击「下一处核对」从尚未处理的歌词开始循环试听；“待定位”表示缺少部分词时间，“文字疑点”表示有识别提示，两者分开处理。编辑后可保存修改，或标记已核对。按 `K` 或点「跟唱」进入大字歌词视图，伴奏模式中可加入原唱提示。按 `N` 跳到下一处核对。

新版实测：在 RTX4070 Laptop 8GB 上，以缓存模型离线分析整首132.989秒示例歌耗时103.21秒。结果包含18句歌词、206个音符、42个和弦区间和261个节拍；这些数量不是准确率。见 [新版 UI 验证](../docs/ui-v2-validation.md)，[旧版验证记录](../docs/ui-validation.md) 保留供核对。

已完成的歌曲可展开「更新分析与歌词」，选择「仅更新歌词」或「整曲分析」，不用重新导入。每次更新生成新版本，旧结果仍可试听；更新失败或停止时保留旧版本。版本下拉框可切回，包括该版本的手动修改。「比较版本」显示文字变化并可定位试听，文字变化本身不是准确率。

安装可选歌词模型（Windows，需先完成基础安装）：

```powershell
# 基础音频模型与声学引导模型（已准备过可略过）
.\.venv\Scripts\music-studio.exe models download --model-dir .cache/models
.\scripts\setup_lyrics.ps1 -Models qwen
.\.venv\Scripts\music-studio.exe ui --model-dir .cache/models --asr-backend qwen --lyrics-alignment anchors --lyrics-python .artifacts/lyrics-env/Scripts/python.exe --offline --open
```

脚本默认只准备Qwen；使用 `-Models aligner,heart` 可另装实验模型。可选运行环境与基础音频依赖分开；权重固定官方修订版并校验 SHA-256，均保存在 `.cache/models/lyrics/`，不随 Git 分发。Qwen权重约4.38GiB，首次准备需要下载；本机8GB显存已完成整组测试，具体显存范围见[歌词评测](../docs/lyrics-v3.md)。

「对齐已修改歌词」只处理保存后的歌词时间；「粘贴歌词」支持每行一句的完整文本，保留实际演唱的副歌与增删句。超过4分钟的参考文本需与已有识别有足够匹配，无法定位时明确失败。声学锚点只给匹配到的词提供时间；未定位文字以灰色下划线显示，仍完整保留在导出中。实验强制对齐仍需试听，异常时会回退、标记或失败。单句编辑框可另外选择模型和音源生成候选，保留原版本，试听比较后再采用；关闭后可从「查看待确认候选」重新打开。

可选更完整的时间锚点（需先准备 turbo；增加推理时间，结果仍需核对）：

```powershell
.\.venv\Scripts\music-studio.exe models download --asr-model large-v3-turbo --model-dir .cache/models
.\.venv\Scripts\music-studio.exe ui --model-dir .cache/models --asr-backend qwen --lyrics-alignment anchors --anchor-model dual --lyrics-python .artifacts/lyrics-env/Scripts/python.exe --offline --open
```

命令行也可以独立使用：

```powershell
# 自动选择 CUDA / CPU，自动判断语言
.\.venv\Scripts\music-studio.exe analyze "D:\Songs\歌曲.mp3" -o "outputs\我的歌曲"

# 指定中文、显卡以及本地模型目录
.\.venv\Scripts\music-studio.exe analyze "D:\Songs\歌曲.mp3" -o "outputs\我的歌曲" --language zh --device cuda --model-dir ".cache\models"

# 中断后重跑：复用通过哈希校验的已完成阶段
.\.venv\Scripts\music-studio.exe analyze "D:\Songs\歌曲.mp3" -o "outputs\我的歌曲" --language zh --device cuda --model-dir ".cache\models" --resume

# 检查输出音轨的采样点、标注范围、缓存哈希和 MIDI 音符时间
.\.venv\Scripts\music-studio.exe validate "outputs\我的歌曲"
```

续跑时保留原来的模型和语言等参数。修改参数会使相关阶段失效并重新计算。不要把输入音频放在输出目录中，也不要把同一个输出目录用于另一首歌。

首次运行会下载模型。提前准备模型并离线处理：

```powershell
.\.venv\Scripts\music-studio.exe models download --model-dir ".cache\models"
.\.venv\Scripts\music-studio.exe analyze "D:\Songs\歌曲.mp3" -o "outputs\离线项目" --model-dir ".cache\models" --offline
```

基础安装默认使用固定修订版的多语言 `small`，配合稳定音符解码、打击成分节拍、自动调音的 CQT 和弦及伴奏残差重建。按上面的可选环境命令启动后，工作台默认使用Qwen文字优先与保守声学锚点；基础安装不会自动下载额外数GB权重。Whisper `large-v3-turbo` 仍可选择，离线使用前运行 `models download --asr-model large-v3-turbo --model-dir .cache/models` 下载。不同识别和对齐方案的独立分数、失败及取舍见[歌词v3评测](../docs/lyrics-v3.md)。

通过 `--asr-model` 选择其他模型或本地目录，通过 `--asr-revision` 固定其他 Hugging Face commit。旧算法选项仍可用：`--melody-decoder classic --rhythm-backend librosa --harmony-backend stft --no-mixture-consistency`。可选 Beat This 需额外安装 `.[rhythm]` 并下载模型；small/final 训练过 GuitarSet，不用于默认方案的评测选择。

完整的 [benchmark 协议](../docs/benchmark-protocol.md)、[实测与取舍](../docs/benchmark-v2.md) 和 [复现命令](../benchmarks/README.md) 已加入项目。不同数据域分别报告，原始音频和歌词不随 Git 分发。

低显存和 CPU 示例：

```powershell
.\.venv\Scripts\music-studio.exe analyze "song.mp3" -o "outputs\low-memory" --segment-seconds 3 --asr-model base
.\.venv\Scripts\music-studio.exe analyze "song.mp3" -o "outputs\cpu" --device cpu --pitch-backend pyin
```

运行进度显示在终端，模型的详细输出写入项目下 `logs/`。Ctrl+C 会终止当前工作进程，保留已完成阶段，之后使用 `--resume` 继续。

## 输出

```text
我的歌曲/
  project.json                 # 统一时间轴、歌词、音符、和弦、节拍、模型设置
  run.json                     # 运行状态、缓存签名和阶段性能
  audio/
    source.wav                 # 解码后的 44.1kHz 双声道时间基准
    vocals.wav                 # 人声估计
    instrumental.wav           # 伴奏估计
  analysis/
    lyrics.json                # 句级 / 词级时间和识别分数
    melody.json                # 音符估计
    pitch.json                 # 每 10ms 的音高轨迹，无声处为 null
    rhythm.json                # 节拍位置和 BPM
    harmony.json               # 和弦区间
  exports/
    melody.mid                 # 实际演唱时间 + 估计 tempo map
    lyrics.lrc
    lyrics.srt
    chords.csv
    beats.csv
  logs/                        # 各阶段诊断
```

所有时间都相对于 `source.wav` 的第一个采样点。MIDI 保留实际音符时间，没有自动把演唱量化到网格。WAV 使用浮点格式，避免各音轨单独归一化引入音量差异。JSON 中的音频路径相对于项目目录。

## 能力边界

- 歌词是自动识别草稿。歌唱、合唱、重混响和跨语言片段会出错；模型的词时间不等于精确的歌唱强制对齐。中文一个 token 可能包含多个字，本项目不按平均时长伪造逐字边界。
- 旋律仅指单一主唱的音高估计；和声、滑音、颤音、同音重唱可能造成错音或碎音符。保留音高曲线供后续编辑器校正。
- 和弦首版只有大小三和弦与 `N`，复杂七和弦、转位及器乐完整谱面未实现。分数是模板相似度，不是“正确率”。
- 节拍可能出现半速 / 倍速误判；首版基线不估计小节起点和拍号，因此不伪造这两项结果。
- 适用于单首歌曲。长录音会增加 CPU 内存、磁盘和耗时；这不是实时分析程序。
- 如更改设置后运行失败，旧的 `project.json` 可能仍在；以 `run.json` 的最新状态为准，`validate` 会拒绝未完成的运行。

## 开发与测试

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui,dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/ui_playback.test.cjs
.\.venv\Scripts\python.exe -m build

# 实际模型的端到端测试，需要一首本地音频
.\.venv\Scripts\python.exe scripts\smoke_test.py "song.mp3" --device cuda --model-dir .cache\models
```

参考 [架构](../docs/architecture.md)、[贡献指南](../CONTRIBUTING.md)、[引擎验证](../docs/validation.md)、[UI 验证](../docs/ui-validation.md) 和 [第三方组件说明](../THIRD_PARTY_NOTICES.md)。仓库包含 Windows / Linux 的核心与 UI 测试 CI 配置；神经模型的下载和 GPU 测试由独立 smoke test 执行。

另外提供 [公开标注测试集与评测工具](../benchmarks/README.md)：固定原 26 个多模块样本及新增 17 首中文录音。数据按原许可下载到本机，Git 仓库保留来源、版本、校验值和指标。该版本的后续规划记录在 [历史路线图](roadmap.md)。

## 许可

本项目原创代码使用 [MIT](../LICENSE)。第三方依赖及模型保留其自身许可与声明，见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。音频、模型权重和运行产物默认被 Git 忽略。
