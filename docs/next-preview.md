# 兼容素材编辑器（Next）

[English](next-preview.en.md) · [文档目录](README.md) · [模型配置](next-models.md)

Next 是保留的单素材编辑界面，适合转写改字、讲话清理、波形处理与实验性 MCP/Codex 操作。制作多轨音乐请使用 [Music Workbench 工作台](create-preview.md)；两种界面的工程记录不同。

## 可以做什么

- 导入音频、波形选区、裁剪、增益、淡入淡出、平衡、倒放与独立预览。
- 试听原音和候选，明确采用、撤销/重做、保存重开与 WAV 导出。
- 按需分轨、Whisper/Qwen 转写、单旋律 MIDI、节拍及电平任务。
- 逐行改转写文字，另存版本，下载 TXT/LRC/SRT；原始识别保留。
- CPU 语音清理、LUFS/真峰值测量、静态增益统一与同位置等响度 A/B。

清理模型可能损伤音乐或环境声，先试听再采用。[语音清理](speech-cleanup.md) · [模型与任务](next-models.md)

## 从源码启动

此高级入口需要 Python 3.11/3.12 与可选依赖，不是安装版基础创作的前置步骤：

```sh
python -m pip install -e ".[ui,audio,agent]"
music-workbench ui --interface next --workspace outputs/asset-editor --port 8926 --open
```

工程保存到所选工作区。一个工作区只由一个服务写入；升级前先关闭旧服务。神经权重单独安装，见 [配置指南](next-models.md)。

## 实验性 MCP 与 Codex

编辑器可连接已有 Codex CLI 与登录。选择 **Codex 助手 → 连接本机 Codex**，例如请求“将当前音频降低 3 dB，先创建预览”。工具结果出现后，在界面试听并决定是否采用。

音频计算在本机；Codex 对话、读取的转写和工具结果使用其服务，不隐式附加音频。该接口仅覆盖单素材编辑和按需任务，不等于完整工作台轨道、音符和效果操作。实验 app-server 接口可能随 CLI 版本变化；已验证版本为 `0.162.0-alpha.17.2`。

外部 MCP 客户端可使用以下配置，自行替换绝对路径：

```toml
[mcp_servers.music_workbench_assets]
command = "/absolute/path/to/.venv/bin/python"
args = ["-m", "music_studio.studio.mcp", "--workspace", "/absolute/path/to/outputs/asset-editor"]
tool_timeout_sec = 180
```

Windows 的解释器为 `.venv/Scripts/python.exe`。16 个工具涵盖选区、预览、采用/历史、模型检查、排队、结果读取、转写改字及 A/B。权重需先安装，工具不接受任意 shell、解释器或下载地址。会话在本次服务运行中保留；编辑状态与候选保存在工作区。

## 边界与参考

旋律是单旋律估计，歌词与词时间需核对。语音清理不等于音乐修复；静态 LUFS 处理不保证广播合规。整数导出拒绝满幅过载，长音频流式处理未提供。

[语音方法与评测](speech-cleanup.md) · [旋律对照](melody-next.md) · [历史任务验证](../benchmarks/results/next-capabilities-2026-10-16.json) · [技术目录](technical-reference.md)
