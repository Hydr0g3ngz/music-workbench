# 两个独立产品 / Two independent products

[中文文档](README.md) · [English documentation](README.en.md) · [Workbench 路线图 / Roadmap](workbench-roadmap.md)

Music Workbench 用于创作、录音、编辑、编排、混音和交付作品。Music Studio 用于分析已有歌曲的人声、伴奏、歌词、主旋律、和弦和节拍。二者分别安装、保存数据和发布。

Music Workbench creates, records, edits, arranges, mixes and exports music. Music Studio analyzes existing songs into stems, timed lyrics, melody, chords and beats. They have separate installations, data and releases.

| 产品 / Product | 仓库 / Repository | 主要工作 / Main workflow |
| --- | --- | --- |
| Music Workbench | [music-workbench](https://github.com/Hydr0g3ngz/music-workbench) | 想法 → 录音、演奏或生成 → 编辑编排 → 混音 → 保存与分享 / Idea → record, play or generate → edit and arrange → mix → save and share |
| Music Studio | [music-studio](https://github.com/Hydr0g3ngz/music-studio) | 导入歌曲 → 分离与识别 → 试听核对 → 导出分析 / Import → separate and recognize → review → export analysis |

## Workbench 的入口 / Workbench entry points

以下行为从 dev19 源码版开始提供；较早安装包按各自发布说明使用。

The following behavior starts with dev19 source builds. Earlier installers retain their documented behavior.

| 入口 / Entry | 用途 / Purpose |
| --- | --- |
| `music-workbench`、`Start-Music-Workbench.cmd` | 创作首页；源码默认 `outputs/workbench` / Creation home; source default `outputs/workbench` |
| `scripts/launch-workbench.ps1` | 可指定工作区、端口及独立模型环境的源码入口 / Source launcher with workspace, port and explicit model runtimes |
| `/`、`/index.html` | 创作首页 / Creation home |
| `/station.html?session=…` | 打开指定多轨工程 / Open an arrangement |
| `/next.html?project=…` | 打开单素材编辑器 / Open a single audio asset |
| 旧书签 `/?project=…` / Old bookmark | 保留素材 ID，转到素材编辑器 / Preserve the asset ID and open the asset editor |

从工程任务打开「详细结果与编辑」会保留返回该创作工程的链接。素材编辑与编排是不同记录；打开或返回页面不会把素材编辑器的修改自动套用到编排。处理结果仍需明确采用。

Task details retain a return link to the originating arrangement. Asset edits and arrangements are separate records: opening or returning does not automatically apply asset edits to the arrangement. Processed results still require explicit adoption.

旧的 Studio 名称启动文件保留为兼容别名；新说明使用 Workbench 入口。`launch-next.ps1` 仍可明确打开既有单素材工作区。旧 `--interface classic` 开发入口返回创作首页。

Old Studio-named launch files are compatibility aliases; new instructions use Workbench entries. `launch-next.ps1` can explicitly open an existing asset workspace. The old internal `--interface classic` entry now opens creation home.

## 数据与模型 / Data and models

- 安装版作品 / Installed projects: `%LOCALAPPDATA%\MusicWorkbench\Projects`。
- 自动 AI 工具包 / Managed AI packs: `%LOCALAPPDATA%\MusicWorkbench\AI\tools`。
- 未显式指定目录时的普通模型缓存 / Default unmanaged model cache: `%LOCALAPPDATA%\MusicWorkbench\AI\models`。
- 源码默认工作区 / Default source workspace: `outputs/workbench`。

dev19 不迁移、删除或自动扫描 Music Studio 的歌曲、缓存及环境。显式提供 `--workspace`、`--model-dir` 或独立解释器时继续使用指定位置；旧 Workbench 工作区可通过明确指定路径打开，多轨作品也可导出和恢复 `.mwb`。

dev19 does not migrate, delete or scan Music Studio songs, caches or environments. Explicit workspace, model-directory and interpreter settings remain supported. Open an older Workbench workspace by its path, or transfer arrangements with `.mwb` export and restore.

## 开发边界 / Development boundary

Workbench 内部仍使用 `music_studio` Python 命名空间，以及既有 API、工程格式标识和隐藏文件名，以保持保存、任务、历史和便携工程兼容。这些内部名称不表示启动了另一个产品。Workbench wheel 只注册 `music-workbench` 公共命令；保留的内部分析代码和历史文档供旧结果读取与实验复现，不作为创作首页的功能入口。

Workbench retains the historical `music_studio` Python namespace, existing API paths, format identifiers and hidden filenames for project, task, history and portable-project compatibility. These internal names do not launch the other product. The wheel registers only the public `music-workbench` command. Retained analysis code and historical documentation support older results and reproduction, rather than creation-home navigation.

Workbench 可以接入分轨、转写和音符提取，但应服务于可继续制作的素材和声部。后续模型评测围绕素材可用性、音符修改量、音乐条件、衔接、资源消耗，以及试听到采用的完整路径开展。整曲歌词识别改进属于 Studio 的独立开发方向。

Stem separation, transcription and note extraction can supply Workbench material and parts. Evaluate usable assets, note corrections, musical conditions, joins, resources and the complete audition-to-adoption path. Full-song lyric recognition improvements belong to Studio's separate development track.

深度 Agent 接入在工程操作成熟后推进，复用与界面相同的命令、版本与撤销机制。

Deep Agent integration follows reliable project operations and shares the interface's commands, revisions and undo mechanisms.
