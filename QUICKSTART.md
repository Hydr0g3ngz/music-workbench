# 快速开始 / Quick start

## Windows 安装版 / Windows installer

1. 从 [发布页](https://github.com/Hydr0g3ngz/music-workbench/releases/tag/v0.2.0.dev14) 下载 `Music-Workbench-0.2.0.dev14-Setup-x64.exe` 并安装。
2. 从桌面或开始菜单打开 **Music Workbench**。
3. 首页选择 **跟着做出第一段音乐**，按五步提示完成编辑与导出。

Download the Setup executable, install, open Music Workbench and choose **Make your first musical sketch**. No separate Python installation, model download or dedicated GPU is needed for the lesson. [Bilingual lesson](docs/first-sketch.md).

Windows 10 22H2 / 11 x64；基础创作可离线使用。需要 AI 时再从首页单独配置。[安装说明 / Installation](docs/windows-install.md)

## 从源码运行 / From source

需要 Python 3.11 / 3.12。Requires Python 3.11 / 3.12.

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[workstation]"
music-workbench
```

源码工程保存在 `outputs/workbench`，从端口 8920 起自动选择空闲端口。Windows 源码用户也可运行 `Start-Music-Workbench.cmd`。

Source projects use `outputs/workbench`; the service selects an available port starting at 8920. Windows source users can also run `Start-Music-Workbench.cmd`.

Windows 开发者也可使用 `scripts/launch-workbench.ps1`；更换工作区时加 `-Workspace <路径>`，不会自动导入另一个产品的数据。普通浏览器访问根地址会进入创作首页，旧的 `?project=` 素材书签转到素材编辑器。[产品与数据边界](docs/product-boundaries.md)

Windows developers can also use `scripts/launch-workbench.ps1`, with `-Workspace <path>` for an existing workspace. It does not import another product's data. The root URL opens creation home; older `?project=` asset bookmarks open the asset editor. [Product and data boundaries](docs/product-boundaries.md).

## 保存作品 / Keep your work

导出 **WAV** 分享音频，导出 **便携工程 `.mwb`** 保存可编辑编排及音频。安装版作品默认位于 `%LOCALAPPDATA%\MusicWorkbench\Projects`。更新前保存并备份工程，关闭使用同一工作区的旧版本。

Export **WAV** to share audio and **Portable project `.mwb`** to keep editable work and media. Installed projects default to `%LOCALAPPDATA%\MusicWorkbench\Projects`. Save and back up before upgrades; close the older version using that workspace.

[中文文档](docs/README.md) · [English documentation](docs/README.en.md) · [模型 / Models](docs/models.md)
