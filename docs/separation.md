# 分轨进入编排

[English](separation.en.md)

将导入或生成的音频拆成人声/伴奏，试听后作为对齐轨道继续编排、混音与导出。可选 Demucs 或 Mel-Band RoFormer KJ；原始素材保留。四声部 Demucs 入口见 [AI 制作流程](ai-production-workflow.md)。

![分轨试听与对齐编排](images/create-separation-zh.png)

## 使用

1. 在工程中选中音频片段，打开 **AI 模型**。
2. 检查 Demucs 或 Mel-Band RoFormer，然后运行。任务可取消，完成前不会改变工程。
3. 在 **处理任务** 试听人声或伴奏。试听范围与提交时选中的片段一致。
4. 点击 **用分轨替换片段**：一次加入两条轨道并移除原片段，避免原曲叠加。
   原始文件保留；**一次撤销**恢复原片段，再次重做恢复两条分轨。
5. 继续编排、调效果器、混音并导出 WAV。

dev18 起只分离选中的片段，采用时保留它在工程中的位置、时长、增益与淡入淡出；新素材偏移从 0 开始。旧版整份素材任务仍按原偏移采用。
新轨道复制原轨道的音量、声像、静音/独奏与效果设置。
注意：压缩等非线性效果分别处理两条分轨时，听感可能与先混合再处理不同。
处理期间若修改或删除源片段，替换会被拒绝；可撤销修改后重试，或单独加入结果。
单独 **加入工程** 放在当前播放头，加入完整结果，不执行替换。

## 可选模型安装

dev17 Windows 版可从 **AI 工具管理 → 人声与伴奏 · RoFormer** 自动安装，详见[安装与使用](qwen-and-separation.md)。以下为源码用户的高级配置方法。

在仓库根目录、Python 3.11/3.12 中运行：

```powershell
python scripts/setup_separation.py
```

安装独立环境、PyTorch 2.5.1 CUDA 12.4、必要推理依赖、固定上游源码与约 913 MB 权重。
这不是 ZIP 内置模型。首次需要联网与额外磁盘空间；页面启动和模型推理不会下载。
已有准备好的独立 Python 可以使用 `--runtime-python <python路径>`，脚本只检查依赖，不修改该环境。
CPU 环境使用 `--torch-index-url https://download.pytorch.org/whl/cpu`。
推理设备沿用工作台的 CPU/Auto 设置；CPU 推理可能很慢。

设置记录在 `.artifacts/separation-runtime.json`。其他位置可使用环境变量
`MUSIC_STUDIO_SEPARATION_CONFIG` 指向该文件的绝对路径，然后重新启动工作台。
配置中记录解释器、文件路径和哈希，不能从 HTTP/Agent 请求指定任意代码或下载地址。
模型在独立任务进程加载；完成/取消后释放。与音乐生成共用工作区任务锁，串行执行。

## 固定实现与边界

- [MSST 源码](https://github.com/ZFTurbo/Music-Source-Separation-Training/tree/6fdad13686bb7e84d029ec66f9dbe76e65c93ebf)：固定版本，MIT；未整体引入训练依赖。
- [KJ 权重](https://huggingface.co/KimberleyJSN/melbandroformer/tree/ac9b0614ab3cd7f77219e18ba494dfd93956c348)：模型卡标注 MIT；权重不随软件分发。
- 权重 SHA-256：`87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e`。
- 原配 8 秒窗口、50% 重叠；将推理批次从 4 改为 1，CUDA 使用 autocast，CPU 使用 FP32，不编译、不做 TTA。
- 人声来自模型，伴奏为输入减去人声；保持原始增益与时间，输出 FLOAT WAV，不对分轨各自归一化。
- 自动检查帧数、采样率、声道、有限数值和输出哈希；任一分轨失败不发布半份结果。
- 此 RoFormer 后端仅输出人声/伴奏两分轨；四声部请使用 Demucs。分轨仍可能包含串音。
- 当前最多 10 分钟/任务。显存仍取决于设备与音频；单批次不是固定显存保证。

## 可复现对比

沿用 `benchmarks/suite-v1.json` 冻结的两首 MUSDB7 公开预览，不新增手工标注。
脚本校验公开文件哈希，记录人声/伴奏 SI-SDR、推理与整次任务耗时、Torch 显存峰值和混合重建误差。

```powershell
$env:PYTHONPATH = "src"
python scripts/benchmark_separation.py --data <测试集目录> --python <模型环境python> --model mel-band-roformer-kj --model-dir <模型缓存> --output <新的结果目录>
```

改为 `--model demucs-htdemucs` 并使用 Demucs 环境，运行相同输入作对照。
两个七秒片段不足以宣称普遍领先；不等于 MUSDB 全测试集成绩。数据仅用于本机评估，遵循原数据授权，不打包分发参考音频。

### 本机结果（2026-10-16）

Windows、RTX 4070 Laptop 8 GB、Python 3.12.4；RoFormer 使用 Torch 2.5.1+cu121。
上游的新版 `set_priority` 参数与 Torch 2.5.1 不兼容，适配层选择其自带的旧版 SDPA 分支，未修改上游权重。

| 参考片段                           | Demucs 人声 / 伴奏 SI-SDR | RoFormer 人声 / 伴奏 SI-SDR |
| ---------------------------------- | ------------------------- | --------------------------- |
| AM Contra — Heart Peripheral       | 10.74 / 14.21 dB          | 13.30 / 16.35 dB            |
| Angels In Amplifiers — I'm Alright | 11.16 / 13.18 dB          | 13.99 / 15.70 dB            |

Demucs Torch 显存峰值约 549 MiB，RoFormer 约 2003 MiB；不包括 CUDA 上下文及其他进程。
模型处理阶段（含加载）分别约 21.1/9.2 秒与 19.7/20.2 秒，缓存状态未严格控制，不能据此宣称速度领先。
两种模型的分轨相加最大重建误差均约 `2.98e-8`。

另用内置授权歌曲完整 45 秒验证跨窗口处理：25.2 秒完成，Torch 峰值约 2040 MiB。
在工程中将其中 30 秒片段（源偏移 3 秒）放到 2.5 秒，完成真实试听、成对替换与撤销/重做检查。
这首歌没有用于本次评测的独立参考分轨，因此只验证流程与对齐，不报告质量分数。
原始计量与失败说明见 [JSON 记录](../benchmarks/separation-local-20261016.json)。未开展盲听评测。
