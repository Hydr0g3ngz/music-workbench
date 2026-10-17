# 打开就能开始 / Open and start creating

Windows 10/11 x64 预览版：解压 **Windows-Portable.zip**，双击 **Music Workbench.exe**。无需安装 Python、运行命令或选择端口。请完整解压后运行，不要从压缩包内直接打开。

Windows 10/11 x64 preview: extract **Windows-Portable.zip**, then double-click **Music Workbench.exe**. No Python installation, commands or port selection. Extract the whole folder first.

启动器显示“已就绪”后会打开工作台。也可以点击“打开音乐工作台”或“在浏览器中打开”。重复打开会复用同一作品目录的服务。关闭音乐窗口后，启动器仍在；在启动器点击“退出”才会停止它启动的后台。已有的独立服务不会被它关闭。运行中的 AI 任务会随所属后台退出而中断，已保存工程和候选仍保留。

The launcher opens the workspace after it is ready. Reopen the app window or use your browser from the launcher. Repeated launches reuse the same project directory. Closing the music window leaves the launcher running; exiting its owner stops the background service, interrupting active AI work while keeping saved projects and drafts. A reused independent service is retained.

## 第一段音乐 / Your first sketch

1. 首页选“玩一个可编辑示例”。播放，试着静音或独奏一条音轨。
2. 双击乐器片段打开音符编辑，拖一个音，或换一种乐器。
3. 选中片段，用“音量与过渡”做渐强或交叉淡化。支持撤销。
4. 导出 WAV 分享声音，导出 `.mwb` 保留可编辑工程与音频。

Choose the editable example, play and solo a track, double-click an instrument clip and move a note. Try a volume curve or crossfade. Export WAV to share audio, or `.mwb` to keep an editable project with its media.

基础编曲、采样乐器、录音、剪辑、混音与导出无需 AI 模型。**便携包不含神经网络权重和 CUDA 推理环境**。本地 AI 仍需按仓库模型文档配置对应运行环境；当前 ACE-Step 配置要求 NVIDIA CUDA。可先用完整的基础功能创作，再配置 AI，不必在第一次启动时下载大模型。

Basic composition, sampled instruments, recording, editing, mixing and export need no AI models. **Neural weights and CUDA inference environments are separate.** Configure local AI using the repository model documentation; the current ACE-Step profile requires NVIDIA CUDA. Start creating before setting up AI.

## 作品与日志 / Projects and logs

便携版默认作品目录：`%LOCALAPPDATA%\MusicWorkbench\Projects`；启动器“我的作品文件”直接打开它。源码入口沿用仓库 `outputs/workbench`。两者不会自动迁移或覆盖彼此。通过 `.mwb` 导出/导入转移作品。日志在 `%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log`，失败时点“启动日志”。安装包或程序目录可以删除，作品目录独立保存。

Portable projects live in `%LOCALAPPDATA%\MusicWorkbench\Projects`; the source launcher retains `outputs/workbench`. They do not migrate or overwrite each other. Transfer projects with `.mwb`. Startup logs are in `%LOCALAPPDATA%\MusicWorkbench\Logs\startup.log`. Project data is separate from the application folder.

本版启动器尚未签名，没有自动更新器；遇到系统提示时请核对下载来源和发布 SHA-256。不要关闭系统保护。程序可使用 Edge 独立窗口，找不到 Edge 时使用默认浏览器。

This preview launcher is unsigned and has no automatic updater. Verify the download source and release SHA-256 if Windows shows a warning; do not disable system protection. Edge opens an app window when available, otherwise the default browser is used.

运行时采用 [Python 官方 Windows embeddable distribution](https://docs.python.org/3.12/using/windows.html#windows-embeddable)，当前固定 [CPython 3.12.10 x64](https://www.python.org/downloads/release/python-31210/)，这是 3.12 最后提供常规官方 Windows 二进制的维护版本，并非最新安全补丁版本。后续应迁移到经过依赖验证、持续获得安全更新的运行时，再做正式稳定发布。许可证随运行时和依赖保留，精确版本见 `DEPENDENCIES.json`。

The application-local runtime uses the official Windows embeddable distribution, pinned to CPython 3.12.10 x64, the last regular 3.12 Windows binary maintenance release, not the latest security patch level. A supported and dependency-tested runtime upgrade is required before a stable release. Runtime and dependency licenses are retained; versions are recorded in `DEPENDENCIES.json`.
