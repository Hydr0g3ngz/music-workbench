# 桌面版启动 / Desktop startup

推荐使用 [Windows 安装器](windows-install.md)：安装后从桌面或开始菜单打开 **Music Workbench**，直接进入独立窗口。无需安装 Python 或管理浏览器。

Use the [Windows installer](windows-install.md), then open **Music Workbench** from the desktop or Start menu. It opens in its own window without separate Python setup or browser management.

## 入门 / First steps

首页选择 **跟着做出第一段音乐**，按五步试听、改音符、混音与导出。基础功能无需模型；需要本地 AI 时再打开 **AI 自动配置**。[教程 / Lesson](first-sketch.md) · [模型 / Models](models.md)

Choose **Make your first musical sketch** on Home. Follow five steps to listen, edit, balance and export. Basic tools need no model download. Open **AI setup** when ready for local generation.

## 工程与故障排查 / Projects and troubleshooting

- 作品 / Projects：`%LOCALAPPDATA%\MusicWorkbench\Projects`。
- AI 环境与模型 / Managed AI：`%LOCALAPPDATA%\MusicWorkbench\AI`。
- 启动日志 / Startup log：`%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log`。

使用软件菜单打开作品目录或诊断，导出 `.mwb` 保存包含音频的备份。更新前保存并关闭软件；卸载程序不删除作品和模型。

Use the app menu to open project files or diagnostics. Export `.mwb` for a backup containing media. Save and close before upgrades; uninstall retains project/model data.

## 旧便携预览 / Earlier portable preview

dev11 的 **Windows-Portable.zip** 是较早的发行方式：完整解压后运行 **Music Workbench.exe**。该版有单独启动器，关闭音乐窗口后需从启动器退出后台；它与当前安装版的单窗口行为不同。新用户请使用当前安装器，具体历史行为见 [dev11 验证](desktop-validation.md)。

The earlier dev11 **Windows-Portable.zip** requires full extraction before running **Music Workbench.exe**. It has a separate launcher: closing its music window leaves the launcher active. Prefer the current installer; see [dev11 verification](desktop-validation.md) for historical behavior.

## 开发者说明 / Developer notes

源码启动见 [Quick start](../QUICKSTART.md)。桌面运行时使用固定的 CPython 3.12.10 x64 embeddable distribution，许可证与精确依赖保存在发行包中；它不是最新的 Python 安全补丁版本。运行时升级和更多全新系统测试见 [路线图](workbench-roadmap.md) 与 [Windows 验证](windows-validation.md)。

See [Quick start](../QUICKSTART.md) for source launches. The desktop runtime pins CPython 3.12.10 x64 embeddable distribution, with licenses and exact dependencies included. This is not the latest Python security patch level; runtime upgrades and broader clean-system testing remain maintenance work.
