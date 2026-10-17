# 语音清理与等响度试听

> 适用于兼容素材编辑器 `next.html`。这是语音清理指南与固定数据评测，音乐创作入口见 [工作台](create-preview.md)。

[English](speech-cleanup.en.md) · [Next 入门](next-preview.md) · [模型安装](next-models.md)

“让讲话更清楚”“统一听感音量”和同位置 A/B 操作同一份素材、预览与撤销历史；实验 Codex / MCP 接口也能调用。

![真实语音清理对比界面](images/next-cleanup-zh.png)

## 从一段录音开始

1. 用 `Start-Music-Studio-Next.cmd` 启动，导入录音，或打开首页的带噪语音示例。
2. 点击“让讲话更清楚”。首次会显示模型来源、下载大小、许可；点击安装才下载权重。
3. DPDFNet 48 kHz 是此面板的初始选择。可调整处理强度；任务固定当时正在试听的整条素材。
4. 完成后打开 A/B，同位置切换原音与结果。响度匹配只衰减较响的一边，不改变导出。
5. 满意后生成编辑预览、明确采用；也可继续统一音量、裁剪和导出。采用后支持撤销、重做。

两个清理模型均使用 Sherpa-ONNX 的 CPU 推理，不需要显卡或 Torch。基础 Next 安装包含
CPU 推理与响度测量运行库，不包含模型权重。权重下载仅发生在明确的界面安装或 CLI 安装操作中；
分析与 Agent 工具不会顺便下载。DPDFNet 权重约 10.11 MiB，GTCRN 约 0.51 MiB，均固定 SHA-256。

这是语音增强：可能改变音色、删掉环境声音、损伤音乐或立体声。GTCRN 内部为 16 kHz，
不会保留 8 kHz 以上内容；DPDFNet 内部为 48 kHz，也不保证原样保留。所有结果独立保存。

## 先做配对测试，再选择入口默认值

数据来自 Cassia Valentini-Botinhao（2017）的
[VoiceBank-DEMAND 官方数据](https://doi.org/10.7488/ds/2117)，CC BY 4.0，使用已有干净/带噪配对，
没有自行补人工标签。评测为小型工程回归，不是完整公开榜单复现。

- 先冻结 pilot：按 `SHA256("speech-cleanup-v1:" + 文件名)` 排序，每位测试说话人取前 8 条，共 16 对。
- GTCRN 的 pilot 出现 STOI 退步后，加入 DPDFNet 候选；其 12 dB 衰减上限来自上游示例。
- 再冻结 follow-up：同样两位说话人取接下来的 8 条，共 16 对，与 pilot 不重合。
  在这 16 条推理前固定清单与处理配置，不按它们的结果调整参数。
- 原始 WAV 与冻结清单均有文件哈希；全长处理，不对结果额外拟合时移或增益。
  保留原采样率和 16 kHz 两套 SI-SDR / STOI、逐例退步、干净音频处理对照与耗时。

16 kHz 配对结果如下。STOI 变化使用 0–1 标度；“退步”指任何负变化，包含很小的浮点变化。

| 模型 / 子集 | SI-SDR 均值变化 | STOI 均值变化 | STOI 退步 | CPU RTF 中位数 |
| --- | ---: | ---: | ---: | ---: |
| GTCRN / pilot | +5.637 dB | −0.00725 | 8 / 16 | 0.105 |
| DPDFNet2 / pilot | +8.192 dB | +0.01525 | 2 / 16 | 0.409 |
| GTCRN / follow-up | +6.012 dB | −0.00368 | 10 / 16 | 0.126 |
| DPDFNet2 / follow-up | +7.029 dB | +0.01265 | 5 / 16 | 0.496 |

因此 DPDFNet 作为**用户主动打开语音清理时**的初始选项，GTCRN 保留为实验对照。
不会自动处理每次导入。DPDFNet 在 follow-up 的 16 条 SI-SDR 均提升，但 STOI 有 5 条退步：
`p257_216` −0.00962、`p257_297` −0.00817、`p257_352` −0.01698、
`p257_396` −0.01231、`p257_043` −0.00211。

GTCRN 的 pilot 有一条 SI-SDR 退步；其他三组没有。所有测得输出都保持输入的采样率、声道与帧数，
数值有限、原文件哈希不变；±20 ms 范围内的互相关时移诊断均为 0。
干净对照也会被改变：follow-up 的平均 STOI 为 DPDFNet 0.99182、GTCRN 0.97861，而不是 1。

RTF 是处理秒数 / 音频秒数，包含模型初始化、重采样和电平测量。本机 Windows、2 CPU 线程，
不是受控速度排名；DPDFNet 有一个片段 RTF 约 1.12，不能据中位数承诺始终实时。
没有独立说话人确认集、置信区间或主观盲听实验；预训练重叠未独立排除。
两个子集来自同一数据域和两位说话人，不能推广为中文、音乐或任意真实录音的保证。

[GTCRN pilot](../benchmarks/results/cleanup-gtcrn-pilot-2026-10-16.json) ·
[DPDFNet pilot](../benchmarks/results/cleanup-dpdfnet2-pilot-2026-10-16.json) ·
[GTCRN follow-up](../benchmarks/results/cleanup-gtcrn-validation-2026-10-16.json) ·
[DPDFNet follow-up](../benchmarks/results/cleanup-dpdfnet2-validation-2026-10-16.json)

## 响度与试听规则

测量使用 [pyebur128](https://github.com/jodhus/pyebur128) / libebur128 1.2.6，提供门控整段 LUFS、
真峰值 dBTP 与响度范围 LRA。RMS 与样本峰值仍独立标识。短于 400 ms、静音或低于测量门限时，
LUFS 可不可测；不足 60 秒的 LRA 标为参考值。当前支持单声道、立体声。

“统一听感音量”仅施加静态增益，不压缩、不限制器。默认 −16 LUFS / −1 dBTP 是可改起点，
不是平台合规承诺。增益受真峰值余量限制；到不了目标时明确提示，不悄悄削波。
每份预览记录处理前后测量、目标、实际增益与峰值限制原因。

A/B 要求时间长度、采样率、声道一致。两边固定素材与哈希，预加载后按同一位置切换；
响度匹配按整段 LUFS 衰减较响的一边，不放大安静的一边。噪声也参与响度测量，因此匹配不等于
精确匹配语音本身音量。剪短后的片段不会被当作同时间线 A/B。

合成校准测试覆盖 −23 LUFS 正弦、立体声加和、门控、静音、短音频、重采样对齐及采样间真峰值。
官方 EBU 测试包本次下载返回 403，未完成该套验证，不声称 EBU 认证或完整符合性测试。

## 复现

```bash
python -m pip install -e '.[ui,audio,agent,benchmark,dev]'
python scripts/download_speech_cleanup.py --suite all
python -m music_studio.studio.cleanup download --model-dir .cache/models --model dpdfnet2-48k
python scripts/benchmark_speech_cleanup.py --data-dir .cache/benchmarks/speech-cleanup --model-dir .cache/models --model dpdfnet2-48k --suite validation --output .artifacts/dpdf-validation.json
```

GTCRN 使用 `--model gtcrn`，pilot 使用 `--suite pilot`。输出需为新路径，防止覆盖实验。
下载器只读取官方 ZIP 的所需成员，复用已校验文件，重试临时 HTTP 错误；不覆盖哈希不同的现有文件。
数值报告随仓库提供，完整数据、权重与处理后音频不提交。

带噪语音示例是 pilot 中 8 个句子的拼接，含 10 ms 边缘淡化与 350 ms 间隔，
是评测后选出的演示，不能当盲测证据。[逐文件来源与修改](../src/music_studio/ui/speech_demo/ATTRIBUTION.md)。

上游：[GTCRN](https://github.com/Xiaobin-Rong/gtcrn)（MIT）、
[DPDFNet](https://github.com/ceva-ip/DPDFNet)（Apache-2.0）、
[Sherpa-ONNX 导出与示例](https://github.com/k2-fsa/sherpa-onnx/tree/master/python-api-examples)。

[真实界面 / Codex / WAV 导出与双声道推理核验](../benchmarks/results/next-cleanup-integration-2026-10-16.json)
记录 80% 强度 CPU 任务、−16 LUFS 预览、A/B 事件及编辑 v3 保留；这是功能证据，不是新的质量评分。
