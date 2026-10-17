# 本地音乐模型候选与接入策略

[English](local-model-candidates.en.md) · [平台路线](workbench-plan.md) · 调研：2026-10-16

选型顺序、开放素材/评测数据与存储建议见[音频资源调研](audio-resources.md)。

本表依据上游仓库和官方模型卡，记录平台要覆盖的能力与候选，不是已安装/可运行的模型清单。
当前实际支持见 [模型目录](models.md)。本表保留调研时的候选判断；已有 ACE-Step、RoFormer 等后续接入以使用指南为准。下述硬件数字为上游说明，不是本平台同条件测速。

## 按能力选择后端

| 方向 | 候选与第一手来源 | 用途与当前判断 | 需要验证的条件 |
| --- | --- | --- | --- |
| 音乐生成/改编 | [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) | 官方列出描述/歌词生成、参考改编、局部重生成、添加声部和人声配伴奏；优先验证创作接口 | 官方 6–8GB 档为 2B turbo + 0.6B LM；代码 MIT，选定权重与依赖另核查 |
| 可编辑曲谱驱动生成 | [YuE2](https://github.com/multimodal-art-projection/YuE)、[模型卡](https://huggingface.co/m-a-p/YuE2-3B) | 旋律/和弦计划 → 歌曲，保留 ABC；2026 年 9 月的新候选。曲谱修改后重新生成整曲，不能声称未改区间波形不变 | 官方方案 Linux/24GB GPU；代码 Apache-2.0，权重 CC BY-NC 4.0 加额外创作者许可，单列可选接入 |
| 歌词到歌曲 | [HeartMuLa](https://github.com/HeartMuLa/heartlib) | 3B 歌曲生成候选；与其他生成器做同提示比较 | 代码 Apache-2.0；固定 Codec/权重修订，测峰值内存。参考条件等仍在 TODO 中的能力不算已开放 |
| 高质量分轨 | [BSRoFormer / MelBand RoFormer 推理框架](https://github.com/ZFTurbo/Music-Source-Separation-Training) | 人声、伴奏和乐器分离候选；与现有 Demucs 基线比较 | 模型家族不是一个 checkpoint；明确目标声部、权重哈希/许可、窗口长度、对齐与显存 |
| 按描述提取声音 | [SAM Audio](https://github.com/facebookresearch/sam-audio) | 文本、时间范围等条件提取目标声音，产出目标和残余轨 | 自定义 SAM License；资源与依赖待测，不能当作宽松许可默认包 |
| 综合音乐转谱 | [SheetSage2](https://huggingface.co/m-a-p/SheetSage2) | 旋律、和弦、节拍、调性、段落到 ABC/MIDI/事件；适合接入工程音乐结构 | 权重 CC BY-NC 4.0，依赖 MERT2；隔离环境、验证时间/音高与曲谱往返 |
| 钢琴转录 | [Transkun](https://github.com/Yujia-Yan/Transkun) | 钢琴复音、力度与起止音的专用候选 | 代码 MIT；固定模型和许可，使用真实钢琴参考评测；钢琴结果不外推到完整混音 |
| 多乐器转录 | [YourMT3+](https://github.com/mimbres/YourMT3) | 多乐器音频到带乐器信息的 MIDI | 仓库 GPL-3.0，README 指向预发布实现；先验证代码/权重可复现性与许可 |
| 轻量音频转 MIDI | [Basic Pitch](https://github.com/spotify/basic-pitch) | 轻量对照、音高弯曲与单乐器素材，补充专用大模型 | 较早基线，不标为最新 SOTA；混合多乐器与起止音误差需单独测 |
| 可控歌声合成 | [OpenVPI DiffSinger](https://github.com/openvpi/DiffSinger) | 音符和歌词到歌声，控制音高与表现参数 | 代码 Apache-2.0；声库/声码器许可分别核查，验证中英音素、时长和调音参数 |
| 歌声/音色转换 | [Seed-VC](https://github.com/Plachtaa/seed-vc) | 参考声音条件下的语音/歌声转换候选 | GPL-3.0，仓库已归档；可作基线或可替换适配器，不认定为当前最佳 |
| 配音/声音设计 | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | 0.6B/1.7B 系列，语音合成、声音设计与参考声音克隆 | 代码 Apache-2.0；按具体版本区分能力，测长文本、时延和权重许可 |
| 多语言配音 | [CosyVoice 3](https://github.com/QwenAudio/CosyVoice) | Fun-CosyVoice3-0.5B 系列候选，作为独立配音后端比较 | 固定 base/RL 权重和许可；流式、语言和加速后端分别测，不合并不同配置成绩 |
| 中英文音效生成 | [MOSS-SoundEffect v2.0](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0) | 最长 30 秒、48kHz 音效，DiT 1.3B 候选 | 模型卡 Apache-2.0；包括 Qwen3 文本编码器与 VAE，隔离 Python 3.12 环境，Windows 编译与整管线资源待测 |
| 交互式音乐生成 | [Magenta RealTime 2](https://github.com/magenta/magenta-realtime) | 文字、音频和 MIDI 控制的连续生成 | 代码 Apache-2.0、权重 CC BY 4.0；230M/2.4B，实时路径主打 Apple Silicon；Windows/NVIDIA 接入不等同于实时能力已验证 |
| 音乐压缩修复 | [Apollo](https://github.com/JusperLee/Apollo)、[权重卡](https://huggingface.co/JusperLee/Apollo) | 低码率音乐修复候选 | 上游工作与权重 CC BY-SA 4.0；与原音 A/B 并测伪影，不承诺找回原始无损信号 |
| 视频/文本音效生成 | [Sony Woosh](https://github.com/SonyResearch/Woosh) | 文本或视频生成声音候选 | 代码多为 MIT，视频模型部分 Apache-2.0；公开权重 CC BY-NC，列为可选研究档 |
| 短音效/loop 生成 | [Stable Audio Open Small](https://huggingface.co/stabilityai/stable-audio-open-small) | 描述生成最长 11 秒、44.1kHz 立体声音效/素材 | Stability AI Community License，按具体条款展示使用范围；loop 仍需检查节拍与接缝 |
| 音效生成替代 | [TangoFlux](https://github.com/declare-lab/TangoFlux) | 文本到音效的研究候选 | 上游声明研究/学术、非商业限制，涉及 Stability/WavCaps 条款；仅列受限可选实验 |
| 节拍/强拍 | [Beat This!](https://github.com/CPJKU/beat_this) | 节拍与小节网格候选 | 代码与发布权重 MIT；固定 checkpoint、推理配置，检查训练重叠；保留 librosa 基线 |
| 乐曲结构 | [All-In-One](https://github.com/mir-aidj/all-in-one) | 速度、节拍/强拍和 intro/verse/chorus 等段落标记 | Windows 的 NATTEN 等原生依赖、训练折与资源实测；不把段落标签当完全正确 |
| 素材语义检索 | [CLAP](https://github.com/LAION-AI/CLAP)、[所链接权重库](https://huggingface.co/lukewys/laion_clap) | 本地声音/文字 embedding，用于检索和相似素材 | 仓库及所链接权重库标 CC0，依赖另记；固定权重，测中英搜索、短音效和索引成本；embedding 不是生成器 |
| 音乐语义特征 | [MERT2](https://huggingface.co/m-a-p/MERT-v2-FullSong) | 音乐表征、素材分类/相似性和转谱编码器候选 | 权重 CC BY-NC 4.0；与 CLAP 按任务比较，不共用未经验证的相似度阈值 |
| 音乐理解 | [MusicFlamingo / Audio Flamingo](https://github.com/NVIDIA/audio-flamingo) | 音色、结构与音乐描述/问答，辅助素材与工程检查 | 代码 MIT；权重非商业并含底模条件，资源待测，作为可选理解后端 |

上游自称 SOTA 是纳入候选的线索；本平台默认选择需要同任务、同条件的质量与资源评测。
本表同时保留近期候选、成熟专用模型和轻量基线，不宣称它们都处在各自领域第一名。

## 混音、乐器与效果器

制作平台还需要稳定的非神经网络引擎。EQ、压缩、混响、延迟、路由、采样器、MIDI 渲染、
音频设备和插件宿主是基础能力；不应等某个 AI 模型才能成立。

| 参考项目 | 可研究的能力 | 选型约束 |
| --- | --- | --- |
| [Spotify Pedalboard](https://github.com/spotify/pedalboard) | 常用 DSP，VST3 乐器和效果器，MIDI 渲染 | GPL-3.0；插件本身和其他依赖另有许可；本次仅调研，未集成 |
| [DawDreamer](https://github.com/DBraun/DawDreamer) | 乐器/效果处理图、MIDI、参数自动化、时间拉伸 | GPL-3.0；先验证 Windows、参数保存、插件扫描/崩溃隔离和音频一致性 |
| [Neural Amp Modeler Core](https://github.com/sdatkinson/NeuralAmpModelerCore) | 吉他音箱/效果音色模型推理，用于 DI 录音处理 | 核心 MIT；具体 .nam 音色与箱体 IR 许可单独核查；不是 MIDI 乐器，音频设备与延迟链路另做 |

主程序当前为 MIT。采用 GPL 组件前需明确整合与发行的许可方案；独立进程不自动消除许可义务。
比较宿主与依赖后再做决定，不能在清单中把 GPL 组件写成 MIT 内置功能。

## 从候选到可用后端

1. **登记**：任务范围、第一手来源、代码/权重/声库许可、维护状态、操作系统和运行环境。
2. **冻结**：选定 checkpoint、代码修订、配置、依赖与文件哈希；记录下载量与磁盘占用。
3. **跑通**：在独立环境对固定短例推理，保留失败与诊断；离线可复现。
4. **测量**：质量、时延、显存/RAM、长输入、取消恢复与逐例退步，官方数字与本机实测分开。
5. **接入**：输出成为工程素材，带时间基准与来源，可试听、拖入、撤销和导出。
6. **选择默认**：按任务提供推荐、轻量、高质量和实验档；更新不覆盖用户既有结果。

按 CPU、8GB、12–16GB、24GB+ 建立硬件档位，记录具体设备、精度、offload 和输入长度。
例如 ACE-Step 上游给出 8GB 附近的配置，YuE2 官方方案面向 24GB；这不等于本机已验证两者。
使用限制不同的开放权重模型单独标记，不能把它们统一宣传为可无限制商用的开源模型。

适配器应允许社区补充模型、参数和硬件优化。基础安装保持可用，模型按需安装和切换；
允许连接用户已配置的本地模型服务，避免为同一个模型重复下载。首批实现顺序见[路线](workbench-plan.md)。
