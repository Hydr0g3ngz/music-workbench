# 本地音频模型、素材与数据库选型

[English](audio-resources.en.md) · [完整模型候选](local-model-candidates.md) · [工作台路线](workbench-plan.md)

调研日期：2026-10-16。依据官方仓库、模型卡和数据发布页筛选。
本文是模型、素材与存储的研究快照，表中判断按调研日期解释；当前可安装后端见 [模型支持](models.md)。
代码、权重、声库与素材分别记录许可，不能仅凭仓库标注“开源”决定全部用途。

## 优先验证的模型

优先级依据当前工作台的创作价值、工程适配难度与许可清晰度，不代表统一质量排名。

| 能力 | 推荐候选与来源 | 能给用户什么 | 接入判断 |
| --- | --- | --- | --- |
| 音乐创作与改编 | [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5)、[权重卡](https://huggingface.co/ACE-Step/Ace-Step1.5) | 描述/歌词生成、参考改编、局部重生成，结果作为新音频片段 | 第一批试点；代码与所列模型卡为 MIT。先验证 2B turbo；base/turbo 的能力不同，不能把 base 的添声部功能写成 turbo 已支持 |
| 人声/伴奏分离 | [MelBand RoFormer KJ](https://huggingface.co/KimberleyJSN/melbandroformer)、[MSST 配置与模型表](https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md) | 对齐的人声与伴奏轨，供重混、转谱和识别使用 | 第一批与现有 Demucs 比较；KJ 权重卡标 MIT。四轨等需求再选 BS-RoFormer/SCNet 的具体 checkpoint，不混用许可和成绩 |
| 节拍/小节网格 | [Beat This!](https://github.com/CPJKU/beat_this) | 节拍、强拍和可审阅的时间网格 | 代码和发布权重 MIT；用现有参考评测，检查训练集重叠；不替代音频时间拉伸引擎 |
| 钢琴音频转 MIDI | [Transkun V2](https://github.com/Yujia-Yan/Transkun) | 钢琴复音、力度和音符起止位置 | 代码 MIT；固定包附带 checkpoint 与许可后，用钢琴数据测。不能外推为任意混音完整转谱 |
| 旋律/和弦/段落联合分析 | [SheetSage2](https://huggingface.co/m-a-p/SheetSage2) | 旋律与和弦 MIDI、ABC、节拍、调性、段落事件 | 值得做可选后端；权重 CC BY-NC 4.0，依赖 MERT2。属于 lead sheet 转录，非逐乐器完整还原 |
| 可控歌声 | [OpenVPI DiffSinger](https://github.com/openvpi/DiffSinger) | 音符+歌词合成歌声，控制音高和表现参数 | 第二批；代码 Apache-2.0，必须另选声库/声码器。先做好 MIDI、歌词音素和时长接口 |
| 中英文音效生成 | [MOSS-SoundEffect v2.0](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0)、[官方实现](https://github.com/OpenMOSS/MOSS-TTS/tree/main/moss_soundeffect_v2) | 最长 30 秒、48kHz 的环境、动作与短音效片段 | 第二批优先试点；模型卡 Apache-2.0，DiT 1.3B 之外还有 Qwen3 编码器和 VAE，显存不能只按 1.3B 估算 |
| 素材语义检索 | [LAION CLAP](https://github.com/LAION-AI/CLAP)、[官方所链接权重](https://huggingface.co/lukewys/laion_clap) | 文字找声音、以声音找相似素材 | 第一批素材库试点；仓库与权重库标 CC0，依赖另记。区分短音效/音乐 checkpoint，中英文检索分别测 |
| 配音/声音设计 | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)、[0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) | 配音与参考声音合成；声音设计使用对应变体 | 第二批；代码与该 Base 权重 Apache-2.0。Base、CustomVoice、VoiceDesign 不是同一组能力；语音合成不等于可控演唱 |
| 压缩音乐修复 | [Apollo](https://github.com/JusperLee/Apollo)、[权重卡](https://huggingface.co/JusperLee/Apollo) | 低码率音乐修复候选，可与原音 A/B | 第二批实验；上游工作与权重为 CC BY-SA 4.0。测伪影与音色损伤；不能宣传为找回原始无损信息 |
| 交互式音乐生成 | [Magenta RealTime 2](https://github.com/magenta/magenta-realtime)、[模型卡](https://github.com/magenta/magenta-realtime/blob/main/MODEL.md) | 文字、音频参考与 MIDI 条件控制的连续音乐生成 | 后续扩展；代码 Apache-2.0，权重 CC BY 4.0。small 230M/base 2.4B，当前实时路径主打 Apple Silicon；NVIDIA 离线推理与 Windows 接入另验 |
| 吉他音箱建模 | [Neural Amp Modeler](https://github.com/sdatkinson/neural-amp-modeler)、[推理核心](https://github.com/sdatkinson/NeuralAmpModelerCore) | 吉他 DI 经过音箱/效果音色模型形成成品轨 | 后续录音/效果器方向；代码/核心 MIT，第三方 .nam 音色与箱体 IR 各有许可。不是 MIDI 吉他乐器；低延迟设备链路仍需实现 |

已有 Qwen3-ASR、Whisper、Demucs、CREPE 和语音清理继续作为对照和可用工具，见[实际支持](models.md)。
模型生成出的 WAV 应成为可试听、插入、移动、撤销和导出的工程素材；转录出的 MIDI 应能换音色继续创作。
MIDI 导入与采样乐器已可用于继续制作，见 [素材库指南](creation-library.md)。

## 高资源或受限的补充候选

| 候选 | 值得保留的能力 | 当前安排 |
| --- | --- | --- |
| [YuE2](https://huggingface.co/m-a-p/YuE2-3B)、[代码及许可说明](https://github.com/multimodal-art-projection/YuE#license) | 可编辑旋律/和弦计划到完整歌曲 | 官方 Linux/24GB GPU 方案；HF 权重标 CC BY-NC，GitHub 另列创作者许可与企业商业许可安排，需对齐实际下载修订。编辑曲谱后重新生成音频，不保证未编辑区间波形保持 |
| [SAM Audio](https://github.com/facebookresearch/sam-audio) | 按文本/时间/视觉条件提取目标声音 | 自定义 SAM License、权重访问申请、资源与 Windows 依赖均需单测；不当作默认 8GB 插件 |
| [Sony Woosh](https://github.com/SonyResearch/Woosh) | 文本音效与视频配音效 | 多数代码 MIT、部分 Apache-2.0；公开权重 CC BY-NC，作为研究可选后端 |
| [Stable Audio Open Small](https://huggingface.co/stabilityai/stable-audio-open-small) | 最长 11 秒、44.1kHz 立体声短素材 | Community License；保留轻量候选，不能写成 MIT/Apache 权重 |

HeartMuLa、多乐器转谱、音色转换与音乐理解等其他候选保留在[完整表](local-model-candidates.md)。
上游宣传与不同条件的榜单不能代替本项目同输入、同候选次数、同资源档位的对照。

## “数据库”首先要覆盖创作素材

这些来源中，有的是开放素材，有的是开放软件/服务，有的是评测数据，不能统一视为可以随软件打包的音频库。

| 来源 | 适合做什么 | 内容与使用条件 | 建议 |
| --- | --- | --- | --- |
| [VCSL](https://github.com/sgossner/VCSL) | 默认乐器/采样器音色库 | CC0 的乐器采样，有 SFZ 版本；上游典型乐器约 20–75MB | 最优先，按乐器下载；从鼓、键盘、贝斯等实际可用音色做小包并审听，不把所有原始采样塞进安装包 |
| [Salamander Grand Piano](https://github.com/sfzinstruments/SalamanderGrandPiano) | 较真实的钢琴播放 | 钢琴采样/SFZ，CC BY 3.0，保留 Alexander Holm 等来源与修改说明 | 可选高质量钢琴包；采样播放器另行实现/选择 |
| [Groove MIDI Dataset](https://magenta.withgoogle.com/datasets/groove) | 可编辑鼓点与 fills、鼓机预设 | 1,150 份人类演奏 MIDI，CC BY 4.0；MIDI-only 3.11MB，含音频版本 4.76GB | 最优先，只取 MIDI 与元数据，转成短小节模板；保留署名、速度/风格/鼓映射信息 |
| [Freesound](https://freesound.org/help/faq/)、[API](https://freesound.org/docs/api/overview.html) | 搜索/试听/导入音效、环境声、one-shots | 每条素材各有 CC0/BY/BY-NC 等许可；API 凭据与原音下载 OAuth2 有区别 | 可选在线来源，优先 CC0/BY 筛选，导入时保存署名及许可；非统一无限制素材库 |
| [MusicBrainz](https://musicbrainz.org/doc/About/Data_License) | 歌名、艺人、专辑、录音 ID 和版本匹配 | 核心数据 CC0；补充数据与 live feed 为 CC BY-NC-SA 3.0；不含歌曲音频/歌词授权 | 先用核心元数据；查到同名曲不等于识别对版本，也不提供可创作的音频 |
| [LRCLIB](https://github.com/tranxuanthang/lrclib) | 查询普通/同步歌词，辅助纠错 | 自托管服务代码 MIT，支持歌词 API；歌词内容权利不能从 MIT 代码许可推导 | 可选歌词候选来源，匹配艺人/版本/时长并让用户确认；不直接当标准答案，不默认打包整库 |

Freesound 2026 年 FAQ 另列上传者的生成式 AI 训练偏好；素材使用、评测与训练用途需要分别记录。
大规模训练数据应走其 Data Packs 流程。歌词检索也不替代 ASR 与强制对齐的独立评测。

## 可复用的评测数据

现有测试集与[benchmark 协议](benchmark-protocol.md)保留；按新增任务扩展，避免为每个模型重新手工标注。

| 数据 | 已有标注/适用任务 | 条件和本平台的使用方式 |
| --- | --- | --- |
| [MUSDB18 / HQ](https://sigsep.github.io/datasets/musdb.html) | 人声、鼓、贝斯、其他四轨参考，分离评测 | 官方完整数据有学术用途/申请与逐曲条款；现有短预览回归继续使用，完整 HQ 评测固定授权与版本；不作为内置创作素材 |
| [MAESTRO](https://magenta.withgoogle.com/datasets/maestro) | 精确对齐的真实钢琴音频和 MIDI，音符/力度/踏板评测 | CC BY-NC-SA 4.0；优先对接公开测试划分，不能只看 Transkun 自己训练/验证分区，也不当通用乐器测试 |
| [Slakh](https://www.slakh.com/)、[redux 数据](https://zenodo.org/records/4599666)、[官方工具](https://github.com/ethman/slakh-utils) | 多乐器分轨与对齐 MIDI，可测分离→转谱链路 | 发布方标 CC BY 4.0；合成音频。redux 避免原始 MIDI 重复，1710 首/151 测试曲；完整归档约 104GB，先小规模验证数据与引用，不一次全下载 |
| [GuitarSet](https://guitarset.weebly.com/) | 吉他音符、逐弦音高、和弦、节拍/强拍 | 已有 benchmark 来源继续复用；区分实际/指示和弦，按演奏者/曲目划分并记录许可版本和训练交集 |
| [FSD50K](https://zenodo.org/records/4060432) | 51,197 个短音频、200 类声音事件，分类/按类检索 | 整体策展 CC BY，逐文件混合 CC0/BY/NC/Sampling+；官方要求商业用途联系策展人。作为评测候选，逐条过滤，不能把整体标签许可覆盖音频许可 |

自动标签的类别检索成绩不等于自然语言搜索满意度；音效生成还需固定提示、人工盲听与失败样本。
Slakh 的合成域表现也不能代替真实混音评测。各模型训练重叠未知时明确写出，不声称全是盲测。

## 如果指软件存储，保留 SQLite，再按需加索引

当前代码 `StudioService` 已用 `.studio.sqlite3` 保存工程相关状态，采用 WAL；制作工程表也在其中。
以下索引方案是待评估设计；当前未进行相应数据库迁移。

| 组件 | 角色 | 选择依据 |
| --- | --- | --- |
| [SQLite](https://sqlite.org/copyright.html) + [FTS5](https://sqlite.org/fts5.html) | 工程、素材元数据、任务、历史、标签与文字索引 | SQLite 公有领域；继续作为本地事实来源。中文搜索需要适配分词/子串，不把默认英文分词当中英文检索已解决 |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | CLAP embedding 相似素材查询 | MIT/Apache-2.0 双许可、C 扩展、支持 Windows；首选验证方案，版本仍 pre-v1，要冻结扩展版本并可重建索引 |
| [LanceDB OSS](https://github.com/lancedb/lancedb) | 素材数量增长后的向量与元数据索引替代 | Apache-2.0，嵌入式可本地运行；与 sqlite-vec 实测检索、内存、过滤和备份后择一，不同时引入两套默认向量库 |

音频和大文件放磁盘，SQLite 保存内容哈希、相对路径、时长/采样率、来源、许可、标签和模型版本。
向量索引为可重建派生物，通过稳定 asset ID 连接工程；删除或许可过滤不能遗漏索引里的素材。
embedding 模型/维度/预处理不同要分索引版本，不能把 CLAP 与 MERT 的向量混在一起计算相似度。
备份以工程与原始素材为准。云端多用户成为明确需求后，再评估服务型数据库。

## 落到当前界面的接入顺序

1. **素材与乐器闭环**：VCSL 小音色包、Groove MIDI、MIDI 导入、采样器与可用的基础效果。素材可试听并拖入时间轴，用户马上能编曲。
2. **AI 创作闭环**：ACE-Step 2B 单独环境，固定短片段生成→试听候选→插入工程→继续混音；之后验证 repaint/base 扩展。一次跑一个 GPU 任务，不占用播放线程。
3. **已有音频再创作**：RoFormer 分轨、Beat This 网格、Transkun 钢琴 MIDI；SheetSage2 作为受限可选分析档。结果保持统一时间基准。
4. **素材发现与声音制作**：CLAP + 可重建本地向量索引；MOSS 音效、DiffSinger 歌声与 Qwen 配音按任务扩展。保留原作与完整生成条件。
5. **更深的模型与 Agent 接入**：以同一工程/素材/任务接口扩展 YuE2、MRT2、NAM 等；基础制作体验先达到可用。

EQ、压缩、混响、总线、自动化和稳定播放仍是平台基础；[Pedalboard](https://github.com/spotify/pedalboard)
与 [DawDreamer](https://github.com/DBraun/DawDreamer)值得作为 DSP/宿主参考，但都涉及 GPL-3.0，
采用前需要明确当前 MIT 项目的整合发行方式；独立进程本身不能自动免除许可义务。

每项接入需有固定输入/模型哈希、冷/热启动时间、峰值显存/RAM、质量对照、长输入、取消和失败恢复记录。
先测 CPU、8GB、12–16GB、24GB+ 的真实档位。ACE-Step 的 [6–8GB 官方方案](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/GPU_COMPATIBILITY.md)
依赖量化/offload；不据此承诺所有模型都能在本机 8GB 显存运行，参数量也不是整个管线的显存预算。
