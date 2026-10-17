# dev19 入口与工程兼容验证 / Entry and project compatibility

[产品与数据边界 / Product boundaries](product-boundaries.md) · [版本说明 / Release notes](releases/v0.2.0.dev19.md)

2026-10-17，在 Windows 本机验证 `0.2.0.dev19` 源码与安装包内置运行时。此记录验证启动、导航、工程兼容和导出；没有运行模型质量评测，也不代表其他电脑已完成验证。

On 2026-10-17, source and bundled-runtime checks covered startup, navigation, project compatibility and export on one Windows host. These checks measure no model quality and do not establish compatibility with every machine.

| 检查 / Check | 结果 / Result |
| --- | --- |
| 后端 / Backend | 55 项通过：入口、桌面启动、UI API、编排、创作任务、素材工具、处理任务与素材编辑。55 passed across entry, desktop, API, arrangement, tasks, material tools and asset editing. |
| 前端 / Frontend | 84 项通过，包括导航、试听源稳定性与创作控件。84 passed, including navigation, stable audition sources and creation controls. |
| 静态检查 / Static checks | 修改的 Python 通过 Ruff；修改的 JS 通过语法检查；PowerShell 启动脚本解析成功。Ruff, JS syntax and PowerShell parsing passed for changed code. |
| 浏览器 / Browser | 从首页建立示例，播放，打开素材编辑器，返回原多轨工程，下载 WAV；英文编辑器保留原工程返回链接。Create example, play, edit asset, return and download WAV; English editor retains the return link. |
| 独立运行时 / Bundled runtime | 系统 PATH 仅保留 System32，启动成功；端口冲突恢复、重复启动复用、无模型示例与 WAV 导出通过。Starts with System32-only PATH; port recovery, relaunch reuse and model-free example/export passed. |
| 安装包 HTTP 工作流 / Packaged HTTP workflow | 新建 → 音量编辑 → 撤销/重做 → WAV/MIDI → MWB 导出恢复，恢复内容相同。Create, edit gain, undo/redo, export WAV/MIDI and restore matching MWB content. |
| 旧素材与书签 / Existing assets and bookmarks | 素材可读取；根地址重定向保留素材 ID 与返回工程 ID，读取前后内容相同。Assets remain readable and bookmark redirects retain both IDs without changing asset state. |
| 已有工程 / Existing arrangements | 本地预览更新前后 7 个工程的完整 API 状态相同；测试创作使用独立工作区。Seven existing arrangements matched before/after the preview restart; creation tests used separate workspaces. |
| 打包一致性 / Package consistency | wheel、内置运行时与源码的 178 个程序及资源文件逐字节相同；公共命令只有 `music-workbench`。178 package files match source byte for byte; only `music-workbench` is registered publicly. |

安装包工作流导出的 WAV 为 44.1 kHz 双声道、784,000 帧，包含非零有限采样。此音频来自内置示例，不能作为模型生成质量的证据。

The packaged workflow exported 784,000 stereo frames at 44.1 kHz with finite, nonzero samples. The built-in example is not evidence of model generation quality.

## 复查 / Recheck

```powershell
$env:PYTHONPATH = "$PWD/src"
python -m pytest tests/test_workbench_entry.py tests/test_desktop.py tests/test_ui.py tests/test_arrangement.py tests/test_creation_tasks.py tests/test_material_tools.py tests/test_local_tasks.py tests/test_studio.py -q
node --test tests/ui_*.test.cjs
python scripts/verify_portable.py <portable-directory> --workspace <new-empty-qa-directory>
```

浏览器和实际安装包 HTTP 检查属于本次本地验收。后续仍需在干净的 Windows 环境中验证安装、升级、不同显示缩放与硬件。

Browser and actual packaged HTTP checks are local acceptance evidence. Clean-machine installation, upgrades, display scaling and broader hardware coverage remain to be tested.

## 构建指纹 / Build fingerprints

- Wheel SHA-256: `e9cdacd8c4a1de4b7ed6af95fdcf0f4d63b8ecc86ba3dd4a452df39d1ca9eb73`。
- Windows installer: `Music-Workbench-0.2.0.dev19-Setup-x64.exe`, 310,182,089 bytes。
- Installer SHA-256: `072bfd1a4917842fcf40a9961b82a39b36dee192a627464f6189887ccadc3239`。

本地构建不等于 GitHub 已发布；公开下载请以仓库 Releases 为准。

A local build is not a GitHub publication; use repository Releases for public downloads.
