# Windows 安装与更新 / Install and update

[**下载安装器 / Download installer**](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/Music-Workbench-0.2.0.dev21-Setup-x64.exe)

适用于 Windows 10 22H2 / Windows 11 x64。基础运行环境已包含，无需安装 Python。基础乐器、MIDI、录音、编排、混音和导出无需 AI 模型。

For Windows 10 22H2 / Windows 11 x64. The basic runtime is included; no Python setup is needed. Instruments, MIDI, recording, arrangement, mixing and export work without AI models.

## 首次安装 / First installation

1. 下载上面的 `Setup-x64.exe`，运行安装器并选择安装位置。安装器目前未签名，Windows 可能显示来源提醒。
2. 安装后，从桌面或开始菜单打开 **Music Workbench**。
3. 首页选择 **跟着做出第一段音乐**。五步跟练和离线手册已随软件提供。
4. 需要生成、分轨或转录时，再打开 **AI 工具管理**。不同模型的下载量和显卡要求见 [模型指南](models.md)。

Run Setup, install and open Music Workbench. Choose the first lesson on Home. The installer is currently unsigned. Install AI tools later when needed; see [model requirements](models.en.md).

## 更新 / Update

保存工程并关闭软件，下载新版本安装器，安装到原来的位置。软件菜单中的 **版本与更新** 提供发布入口；目前没有后台自动更新器。建议先导出 `.mwb` 备份。

Save and close the app, then install the new version in the same location. **Version & updates** opens the release page. Updates are manual; export an `.mwb` backup first.

## 作品放在哪里 / Where files are stored

| 内容 / Data | 位置 / Location |
| --- | --- |
| 工程 / Projects | `%LOCALAPPDATA%\MusicWorkbench\Projects` |
| AI 环境和模型 / AI tools and weights | `%LOCALAPPDATA%\MusicWorkbench\AI` |
| 启动日志 / Startup log | `%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log` |

升级和卸载保留这些数据。可以从软件菜单打开作品目录；用 `.mwb` 转移完整作品。源码版默认使用 `outputs/workbench`，不会自动搬到安装版。

These folders are retained on upgrade and uninstall. Open the project folder from the app menu or transfer projects with MWB. Source projects default to `outputs/workbench` and are not moved automatically.

## 遇到问题 / Troubleshooting

- 启动失败：从软件菜单打开诊断，或查看上面的启动日志。报告问题时附系统、软件版本和错误信息。
- 显示过大或模糊：在 **显示设置** 中恢复 100% 页面缩放；诊断页可查看 DPI。
- AI 工具不可用：在工具管理中选择 **检查当前环境** 或 **修复安装**；先确认空间、显卡和网络满足要求。
- 退出前，未采用的录音应先加入轨道或下载。重复打开会激活已有窗口。

For startup failures, inspect diagnostics/logs and include the OS, app version and error in your report. Reset page zoom to 100% for display issues. Check or repair missing AI tools. Keep an unadopted recording before closing.

[检查下载文件的 SHA-256 / Checksums](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/SHA256SUMS.txt) · [报告问题 / Report a problem](https://github.com/Hydr0g3ngz/music-workbench/issues) · [从源码运行 / Run from source](../QUICKSTART.md)
