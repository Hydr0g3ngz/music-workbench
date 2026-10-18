# Windows 安装版 / Windows installer

当前下载为 **dev21 开发预览版**。直接运行安装器并核对发布页的 SHA-256，无需先安装旧版本。[本版新增功能](releases/v0.2.0.dev21.md)。

The current download is the **dev21 development preview**. Run Setup and check the release SHA-256. No older installation is required. See the dev21 release notes.

下载 [`Music-Workbench-0.2.0.dev21-Setup-x64.exe`](https://github.com/Hydr0g3ngz/music-workbench/releases/download/v0.2.0.dev21/Music-Workbench-0.2.0.dev21-Setup-x64.exe)，运行安装器，选择语言和安装目录。安装结束后从桌面或开始菜单打开 **Music Workbench**。工作台在自己的桌面窗口内显示，无需 Python、终端、端口或单独的浏览器窗口。

Download and run the x64 Setup executable, choose language and installation directory, then open Music Workbench from the desktop or Start menu. The workspace opens in its own desktop window, without a separate Python installation, terminal, port selection or browser window.

第一次打开建议选择 **跟着做出第一段音乐**，按五步完成试听、认识音轨、音符编辑、混音和 WAV 导出。教程可关闭、继续或重新学习；顶部“入门”可再次打开。完整离线手册也在软件内。[教程](first-sketch.md)。

Choose **Make your first musical sketch** on first launch. Five in-app steps cover listening, track layers, note edits, balance and WAV export. Resume from **Learn** in the header, or read the offline handbook inside the app.

支持 Windows 10 22H2 / Windows 11 x64。默认安装到当前用户的 Programs 目录，不要求管理员权限。安装器包含基础创作运行时和微软签名的 WebView2 离线安装器；已安装显示运行时则复用，否则自动安装。安装后基础功能可离线使用。

Windows 10 22H2 / Windows 11 x64. Installs per user without administrator rights. The package includes the basic creation runtime and Microsoft-signed offline WebView2 installer, used only when needed. Basic creation works offline after installation.

基础功能包括示例、乐器、MIDI、录音、剪辑、编排、混音和导出。首页 AI 入口提供 ACE-Step 图形化自动配置：检查显卡和磁盘、下载独立环境与固定版本模型、校验、生成 12 秒音乐验证，然后启用文字生成、参考变奏和局部重绘。无需另外安装 Python 或 CUDA Toolkit。需要 Windows x64、NVIDIA 至少 8 GB 显存和兼容驱动、35 GB 可用空间；首次下载约 8–12 GB，网络和硬件决定耗时。失败可重试，已有校验缓存复用；关闭程序会暂停准备。AI 工具管理还提供七个独立处理工具包，包含钢琴、多音音符、分轨、转写与语音清理；模型另外下载。

Examples, instruments, MIDI, recording, editing, arrangement, mixing and export are included. Home offers graphical ACE-Step setup: hardware/disk checks, isolated dependencies, pinned model downloads, checksum verification and a real 12-second generation test. No separate Python or CUDA Toolkit installation is needed. Requires Windows x64, an NVIDIA GPU with at least 8 GB VRAM and a compatible driver, 35 GB free space and about 8–12 GB of initial downloads. Retry reuses verified caches; closing pauses setup. AI tools offers seven isolated processing packs for piano/polyphonic notes, separation, transcription and speech cleanup. Models download separately.

作品默认保存在 `%LOCALAPPDATA%\MusicWorkbench\Projects`，与安装目录分离。升级后继续使用；卸载只处理程序文件，不删除作品、模型或浏览器用户数据。可通过软件菜单打开作品目录，或用 `.mwb` 转移作品。原源码工程在 `outputs/workbench`，不自动迁移。

Projects remain in `%LOCALAPPDATA%\MusicWorkbench\Projects`, separate from program files. Upgrades retain them; uninstall removes program files while preserving project/model/profile data. Source-checkout projects in `outputs/workbench` are not migrated automatically.

AI 文件保存在 `%LOCALAPPDATA%\MusicWorkbench\AI`，也与程序和作品分离。显示支持按显示器 DPI 缩放；若误调了页面大小，可用菜单“显示设置 → 恢复 100% 页面缩放”。诊断入口可查看实际 DPI 与渲染像素比。

AI files live separately in `%LOCALAPPDATA%\MusicWorkbench\AI`. The desktop uses per-monitor DPI scaling. Use Display → Reset page zoom to 100% after an accidental zoom change; diagnostics show actual DPI and rendering pixel ratio.

退出时会等待当前工程保存；录音尚未保留时应先加入轨道或下载，再退出。重复打开激活已有窗口。正在运行时需要先关闭软件再升级或卸载。后台由本窗口启动时，退出会一并关闭；连接已有独立服务时保留该服务。

Closing waits for project saves and protects unadopted recordings. Relaunch activates the existing window. Close the software before upgrading/uninstalling. Closing stops a backend owned by this window, while retaining a reused independent service.

本预览安装器尚未签名，也没有自动更新器。dev21 可在 [发布页](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev21) 核对 SHA-256。遇到启动问题时，从软件菜单打开诊断或查看 `%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log`；反馈时提供系统、软件版本与错误信息。

The preview installer is unsigned. Version & updates in the app opens release links and manual upgrade instructions; there is no background updater. Verify the release checksums. For startup problems, open diagnostics or inspect `%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log`; include the OS, app version and error when reporting a problem. Broader compatibility results are in the technical report below.

## 开发者：构建与验证 / Developers: build and verification

Implementation references: [Microsoft WebView2 distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution), [Inno Setup per-user installation](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm), [installer command-line options](https://jrsoftware.org/ishelp/topic_setupcmdline.htm).

[实测记录与边界 / Validation and limits](windows-validation.md)。源码构建：先用 `scripts/prepare_installer_tools.py` 获取并校验构建工具，安装 Inno 编译器到 `.artifacts/desktop-build-tools/inno`，再用 `scripts/package_installer.py`。Evergreen 下载链接会更新；哈希不匹配时先复核微软签名和版本，再有意识地更新固定输入，不跳过校验。

Source builds: prepare and verify build inputs with `scripts/prepare_installer_tools.py`, install the Inno compiler into `.artifacts/desktop-build-tools/inno`, then use `scripts/package_installer.py`. The Evergreen URL changes over time: review Microsoft's signature/version before updating the pinned input; do not bypass verification.
