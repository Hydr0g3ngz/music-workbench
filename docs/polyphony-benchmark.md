# Basic Pitch 开发评测 / Development benchmark

[使用指南 / User guide](polyphonic-notes.md) · [数值 / Numerical report](../benchmarks/reports/polyphony-v1.json)

## 数据与协议 / Data and method

GuitarSet 1.1.0，CC BY 4.0，[原始记录 / Source](https://zenodo.org/records/3371780)。使用现有冻结集的五首 accompaniment take：00_BN1-129-Eb、01_Funk1-114-Ab、02_Jazz1-130-D、03_Rock1-130-A、04_SS1-100-C#。输入与 JAMS 的 SHA-256 来自 `benchmarks/suite-v1.json`，运行前强制校验，不另做人工标注。

Five fixed accompaniment takes from GuitarSet 1.1.0; input/reference hashes are verified against the existing manifest. No new manual annotation is used. JAMS `note_midi` annotations for all six strings are merged; fractional MIDI is rounded to the nearest integer.

mir_eval 0.8.2：起音容差 50 ms、音高 50 cents；含止音指标允许 20% 音符长度或至少 50 ms 误差。每配置运行五首，宏平均 F1。报告同时保留逐例 precision/recall、漏音和多余音符数。

Onset tolerance 50 ms, pitch tolerance 50 cents; offsets allow 20% of note duration or at least 50 ms. Five cases per profile, macro F1; per-case precision, recall, missing/extra counts and CPU wall time remain in the report.

| 设置 / Profile | Onset / frame / min ms | Onset F1 | Onset + offset F1 |
| --- | --- | --- | --- |
| Default | .50 / .30 / 127.7 | 0.6717 | 0.3329 |
| Conservative | .60 / .35 / 150 | 0.6558 | 0.3147 |
| Sensitive | .35 / .25 / 100 | 0.6041 | 0.3233 |

保留默认值；止音识别仍较弱，应提供可编辑结果，不能承诺自动准确扒谱。Basic Pitch 训练使用 GuitarSet，可能有数据重叠；这些结果仅支持此开发集上的参数选择。未测独立钢琴集、力度准确率、人工修改量、峰值 RAM 或其他模型，不能据此声称 SOTA。

Keep defaults. Offset quality remains weak, supporting editable output rather than an accurate automatic-score claim. GuitarSet was used in Basic Pitch training; overlap is possible. No held-out piano, velocity accuracy, correction-effort, peak-RAM or cross-model result is claimed.

## 复现 / Reproduce

在安装了多音音符工具包的机器，指定下载后的原始 WAV/JAMS 目录；模型由工具管理器准备。Windows PowerShell 示例：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$pack = "$env:LOCALAPPDATA/MusicWorkbench/AI/tools/polyphonic-notes"
& "$pack/env/python.exe" scripts/benchmark_polyphony.py `
  --data '<GuitarSet WAV/JAMS directory>' --model-dir "$pack/models" `
  --output .artifacts/polyphony-benchmark
```

The official data is downloaded separately. Only numerical measurements and hashes are committed; recordings and annotation content are not redistributed. The managed environment pins Basic Pitch 0.4.0 source, ONNX Runtime 1.23.2 and the checkpoint SHA-256 recorded in the report. Wall time includes adapter import/model load per call; the first call has additional initialization cost.
