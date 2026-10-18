# 旋律与 MIDI：候选模型实测

这是早期旋律后端的固定数据对照，保留原环境和参数。当前 Basic Pitch 与 Transkun 已可在工具管理中安装；操作与要求见 [多音音符](polyphonic-notes.md) 和 [钢琴转录](piano-notes.md)。

[English](melody-next.en.md) · 2026-10-16 · [逐例 JSON](../benchmarks/results/melody-next-2026-10-16.json)

**结论：暂不替换默认模型。** ROSVOT 在既有 GTSinger 回归上明显更好，
但在独立的 vocadito 数据上退步；Basic Pitch 在 GTSinger 上也未超过现有算法。
音符准确度、合成音色与 MIDI 时间序列化分别评测。

## 评测协议

- 原有 GTSinger 12 段（中文/英文各 6 段）继续冻结，用作工程回归，已经参与过开发。
- 新增 [vocadito](https://zenodo.org/records/5578807) 全部 40 段；发布元数据含 29 个歌手 ID。
  官方介绍为 7 种语言，CSV 另含混合语言和无歌词标签，未将这些标签强行合并。
  [清单](../benchmarks/vocadito-v1.json) 固定音频、f0、两套音符标注的 SHA256。
- vocadito 是单人清唱，不能据此承诺复杂混音中的效果；两位人工音符标注者 A1 / A2 分别计分。
- 起音容差 50 ms、音高容差 50 cents；止音容差为 `max(50 ms, 20% 音符时长)`。
  使用 `mir_eval 0.8.2`，按片段取宏平均。失败案例进入分母并计零，不挑选成功样本。
- 模型仅接收音频，不接收参考歌词、音符时间或真值词边界。ROSVOT 使用 RWBD 预测词边界，
  阈值使用官方推理默认值 0.85 / 0.5，未在 vocadito 上调阈值。
- 输出 MIDI 后再读取，核对音高、音符数量、同音重叠与绝对秒数，最大时间误差阈值 10 ms。
- 逐帧 f0 单独计分；稳定引擎的无声 `null` 先转为 0 Hz。两套最终结果已用修正后的同一评分函数
  重新核算，全部 80 个片段的数值与保留结果一致。

## 音符结果

以下均为 F1 百分数，不能当成“正确音符的百分比”。

| 数据 / 指标 | CREPE + stable | Basic Pitch | ROSVOT + RWBD |
| --- | ---: | ---: | ---: |
| GTS 中文：起音+音高 | 30.6 | 19.8 | **59.8** |
| GTS 英文：起音+音高 | 38.8 | 19.5 | **48.9** |
| GTS 中文：包含止音 | 16.6 | 10.8 | **56.3** |
| GTS 英文：包含止音 | 20.8 | 6.3 | **36.9** |
| vocadito A1：起音+音高 | **45.6** | 未测 | 26.0 |
| vocadito A2：起音+音高 | **42.0** | 未测 | 27.0 |
| vocadito A1：包含止音 | **25.7** | 未测 | 18.5 |
| vocadito A2：包含止音 | **22.9** | 未测 | 21.6 |

ROSVOT 在 vocadito 的起音+音高分数相对 CREPE，A1 有 39/40 段退步，A2 有 37/40 段退步。
按歌手聚类、2000 次重采样的配对差值 95% 区间分别为 −23.3 至 −15.9、−18.9 至 −11.1
个百分点；这是当前样本的工程估计，不是跨所有歌唱场景的保证。

| vocadito 逐帧指标（宏平均） | CREPE | ROSVOT 所用 RMVPE |
| --- | ---: | ---: |
| Raw Pitch Accuracy | 98.07% | 98.20% |
| Raw Chroma Accuracy | 98.15% | 98.28% |
| Voicing Recall | 99.09% | 99.83% |
| Voicing False Alarm | 27.37% | 31.27% |

高逐帧音高准确率与低音符 F1 同时出现，提示应重点检查起止音、重复同音、无声/辅音间隙，
不能据此证明每个片段的音高都没有问题。下面的分段实验继续检查这一点。

## 保留休止：可选解码器，尚不替换默认

旧 `stable` 会桥接最多 100 ms 的同音间隙，并把相邻音符之间最多 250 ms 的间隙平分给两边。
新增 `rest` 保留 Viterbi 解码后的间隙，不再执行这两步；音高网络、阈值与最短音符长度保持原样。
它能恢复部分同音重复，但不能解决所有起止音、滑音、八度或伴奏串扰问题。

按元数据歌手 ID 划分 22 段开发（14 ID）、18 段验证（15 ID），先在开发侧比较
0 / 20 / 40 ms 桥接，再冻结 0 ms、关闭间隙平分。[协议](../benchmarks/melody-boundaries-v1.json)
在打开验证侧音符标签前保存。整个 vocadito 已用于前一轮模型比较，因此这里只称分段优化的
歌手隔离后续验证，不冒称从未见过的盲测。复用同一份缓存 CREPE 轨迹，两位标注者分开计分。

| 数据 / 指标，F1% | stable | rest |
| --- | ---: | ---: |
| vocadito 验证 A1：起音+音高 | 45.6 | **55.8** |
| vocadito 验证 A1：包含止音 | 24.7 | **35.9** |
| vocadito 验证 A2：起音+音高 | 43.0 | **51.1** |
| vocadito 验证 A2：包含止音 | 20.6 | **29.8** |
| GTS 中文：起音+音高 | **30.6** | 19.6 |
| GTS 英文：起音+音高 | **38.8** | 34.3 |

验证 A1 / A2 仍分别有 3/18、5/18 段退步；按歌手聚类 2000 次重采样，起音+音高
差值的 95% 区间分别为 +5.3 至 +15.8、+3.1 至 +14.0 个百分点。
GTS 的明显退步意味着不能把这个方案当作全面改进。经典默认仍为 `stable`，Next 同时提供
两个可选入口以及可试听的估计音符合成。合成音色与转录准确性仍分开评价。

[逐例报告](../benchmarks/results/melody-boundaries-2026-10-16.json)保留开发网格、验证、GTS、轨迹哈希
和 MIDI 往返记录；[原始选择记录](../benchmarks/results/melody-boundaries-selection-v1.json)的字节由协议固定。
选定方案的 52 个片段全部完成，最大往返时间差约 0.21 ms。
这不代表音符已经与真人演唱一致。后续应优先做起音/止音检测与音源条件分析，再引入新验证数据。

复现：`scripts/evaluate_note_boundaries.py` 使用 vocadito 数据和缓存 CREPE 运行目录；
`--partition heldout --bridges 0` 固定已选方案。`scripts/evaluate_boundary_regression.py`
对冻结 GTS 清单检查退步；脚本拒绝覆盖旧输出。

## 资源与 MIDI 排查

本机为 RTX 4070 Laptop 8GB，PyTorch 2.5.1+cu121，4 个 Torch CPU 线程。
vocadito 片段的单段推理中位数：CREPE 1.04 s，ROSVOT 0.51 s；
最大 `torch.cuda.max_memory_allocated` 分别约 734 MiB 与 708 MiB。
这不包含驱动、CUDA 上下文、其他 GPU 程序或进程内存，不能外推整首长歌和其他 AI 模型。

所有最终实验均完成，MIDI 往返检查通过。还只读检查了 3 首已有歌曲的原 MIDI，
最大时间差 0.354 ms，音高与已保存的音符一致；这只排除了明显的序列化时间漂移，
不代表音符与原唱一致。用户觉得“旋律不对”的问题仍需要实质性改进转录和分段。

Basic Pitch 的 ONNX Runtime 1.31.0 在本机导入时出现原生崩溃，实验使用独立的 1.20.1
兼容目录完成。因此模型健康检查应在隔离进程里实际导入，
不能仅凭包已安装就显示“可用”。

## 复现与来源

入口为 [GTS 评测脚本](../scripts/evaluate_melody_next.py)、
[vocadito 评测脚本](../scripts/evaluate_vocadito.py)、
[实验适配器](../scripts/rosvot_adapter.py)。每次使用新的输出目录，保留运行代码快照、
模型与数据哈希、原始输出和逐例分数。公开 JSON 保留实际运行身份与最终评分核验记录；
本地运行快照不等于当前脚本逐字节相同，后续增加了 CPU 选项与输入校验。

先安装仓库的 `[benchmark]` 依赖及实验环境中的 Torch、torchaudio、torchcrepe、pyworld、pretty_midi、PyYAML；
ROSVOT 权重按作者 README 获取。已验证的具体版本保存在逐例 JSON，模型推理不随常规测试自动运行。
数据可用校验过的下载器准备：

```bash
python scripts/download_vocadito.py --data /data/vocadito
python scripts/evaluate_vocadito.py --data /data/vocadito --backend crepe --output runs/vocadito-crepe
python scripts/evaluate_vocadito.py --data /data/vocadito --backend rosvot --upstream /path/ROSVOT --checkpoints /path/checkpoints --output runs/vocadito-rosvot
```

默认实验设备为 CUDA，可用 `--device cpu`。推理实验依赖单独安装，不属于无需模型的编辑安装。
ROSVOT 适配器当前只支持小于 30000 个模型帧的片段，明确拒绝超长输入；尚未接入生产长曲。

- [ROSVOT](https://github.com/RickyL-2000/ROSVOT)：`3c8332bf43adae35f6e4d64971862f2f6139b310`，
  Ruiqi Li，MIT 代码；[许可副本](licenses/ROSVOT-MIT.txt)。权重从作者的官方链接下载，未在本仓库再分发。
- [Basic Pitch](https://github.com/spotify/basic-pitch)：`fa5997af0a8210982619003269994a1be25eddf3`，
  Spotify，Apache-2.0，官方 ONNX 模型与默认推理。
- vocadito：Rachel Bittner、Katherine Pasalo、Juan José Bosch、Gabriel Meseguer Brocal、David Rubinstein，
  2021，CC BY 4.0，[数据记录](https://zenodo.org/records/5578807)。本仓库只包含清单和指标，不分发录音。

现有 GTSinger 数据的许可、来源与选择规则继续沿用 [原基准说明](../benchmarks/README.md)。
