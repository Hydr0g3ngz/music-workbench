# 参与 Music Workbench 开发

[English](CONTRIBUTING.md) · [路线图](docs/workbench-roadmap.md)

欢迎使用中文或英文提交 issue 和 PR。说明要完成的音乐任务、当前障碍与期望行为。较大的引擎或模型改动建议先讨论；小修复可以直接提交 PR。复现材料请使用可分享的合成或授权音频。

## 开发环境

使用 Python 3.11/3.12 与 Node 22。前端为静态 HTML/CSS/JavaScript，无构建步骤或外部 CDN；基础开发不需要 Torch 或模型权重。

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[workstation,benchmark,agent,dev]"
music-workbench
```

源码默认作品目录为 `outputs/workbench`，从端口 8920 起选择空闲端口。Windows 也可运行 `Start-Music-Workbench.cmd`。破坏性测试使用独立工作区，不要使用个人作品。

## 代码位置

| 范围 | 位置 |
| --- | --- |
| 启动入口 | `src/music_studio/workbench_cli.py` |
| 工程、版本与素材 | `src/music_studio/studio/service.py`、`arrangement.py`、`models.py`、`project_pack.py` |
| 创作与模型适配 | `studio/` 下的 `creation.py`、`tasks.py`、`registry.py`、`ace_worker.py`、`separation.py`、`ai_setup.py` |
| 音频、乐器与效果 | `studio/dsp.py`、`effects.py`、`library.py`；`ui/static/station-engine.js`、`effects-dsp.js` 与 worklet |
| 工作台界面 | `src/music_studio/ui/static/` 下的 `station*`、`welcome*`、`learn*`、`ai-setup*` |
| 桌面与打包 | `desktop/`、`scripts/package_*.py`、`scripts/build-desktop.ps1` |

内部 `music_studio` 包名用于兼容已有导入与工程；当前产品入口为 Music Workbench。经典分析与 Next 单素材编辑器是兼容组件；独立歌曲分析产品由 [Music Studio](https://github.com/Hydr0g3ngz/music-studio) 维护。

## 验证修改

```sh
python -m ruff check .
python -m pytest -q
node --test tests/ui_playback.test.cjs tests/ui_i18n.test.cjs tests/ui_transport.test.cjs tests/ui_comparison.test.cjs tests/ui_station.test.cjs tests/ui_creation.test.cjs tests/ui_recording.test.cjs tests/ui_timing.test.cjs tests/ui_workflow.test.cjs tests/ui_composition.test.cjs tests/ui_material.test.cjs tests/ui_envelope.test.cjs tests/ui_desktop.test.cjs tests/ui_setup.test.cjs tests/ui_tutorial.test.cjs
```

以上命令与 [CI](.github/workflows/tests.yml) 一致。确定性适配器测试不代表模型质量。修改打包时，另运行 `python scripts/package_release.py`，在独立环境安装生成的 wheel 及 `[ui,audio,agent]`、`httpx`，执行 `python scripts/verify_release.py --no-models`。

界面或音频改动需在真实浏览器验证导入、连续播放、快速定位、静音/独奏、编辑、撤销、重开和导出。任务轮询、切换语言、面板重绘必须保持现有音源与统一时钟；DSP 修改要比较实际导出。界面 PR 提供中英文截图，检查窄窗口与键盘访问。

## 翻译

工作台各模块使用中英成对消息及局部翻译函数，`station.js` 保存 `station-language`。首页、教程和 AI 配置有各自文案；经典界面的 `i18n.js` 不覆盖整个工作台。

沿用对应模块的方式并检查两种语言。工程名、歌词、提示词与模型输出不进入翻译器。切换语言应保留播放、工程和待处理操作。

## 模型与工程完整性

模型使用隔离环境，固定源码、权重修订和哈希，分别记录许可。结果保存为有类型、带来源的候选；任务完成不能自动替换编排。采用须支持撤销、保存重开与导出，失败和取消需有明确诊断。

模型改动使用授权固定输入，报告硬件、版本、参数、失败、质量和资源；复现与数据规则见 [技术参考](docs/technical-reference.md)、[benchmark](benchmarks/README.md)。保持确认集划分，报告退步和训练重叠。不提交私人音频、参考歌词正文、转写、凭据或权重。

保持时间单位、原素材与乐观版本检查。工程格式不兼容变更需明确升级 schema 与迁移，检查历史和便携工程。缺失音符/词时间应保持缺失，模型分数不能标成正确率。

## 文档与发布

使用指南面向未读过开发讨论的用户，说明操作、结果和限制；路线图说明未来功能，发布说明聚焦用户可见变化，中英保持一致。内部测试日志、给项目负责人的交接和宣传制作说明留在公开文档之外。

提交前运行 `python scripts/check_public_docs.py`。移动文档或移除附件时同时检查链接。

下载页只突出一个 Windows 安装器入口。附件限安装器、可选示例工程 ZIP 和对应校验文件。wheel、sdist 等源码构建结果保留在 CI 产物中；GitHub 自动提供源码归档。软件发布页不附逐个演示导出、QA 报告、视频、字幕、封面或宣传文案包。

发布工作流校验标签，在 Actions 保留构建结果。新标签只创建草稿，不自动上传 `dist/*`。公开前添加审核后的用户下载并检查 SHA-256；已有发布不自动替换附件。
