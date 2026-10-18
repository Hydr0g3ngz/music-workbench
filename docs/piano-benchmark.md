# Piano transcription development benchmark / 钢琴转录开发评测

This is a six-excerpt development comparison, not a broad model ranking. 本评测用于选择钢琴工作流的默认工具，不作为通用排行榜。

| Backend / 后端 | Onset F1 / 起音 | Onset + offset F1 / 含结束时间 | Raw velocity MAE / 原始力度误差 | Mean call / 平均调用 |
| --- | ---: | ---: | ---: | ---: |
| Basic Pitch 0.4.0 ONNX CPU | 0.8354 | 0.1792 | 37.33 / 127 | 6.37 s |
| Transkun 2.0.1 V2 CUDA FP32 | 0.9965 | 0.8292 | 6.77 / 127 | 9.04 s |

On this small piano suite, prefer Transkun when its runtime is suitable. Basic Pitch remains a lightweight CPU option and supports other single instruments. Devices differ, so this is not a CPU/GPU speed comparison. Each call loads the model; host-memory peaks and CUDA context are not included. Hardware: RTX 4070 Laptop 8 GB on the development Windows host.

本小型钢琴集上 Transkun 更合适；Basic Pitch 保留为轻量 CPU 与其他单乐器方案。两者使用不同设备，耗时不能解读为算法速度排名。力度直接以 MIDI 1–127 比较，未作缩放或校准；它只在正确匹配的起音/音高上计算，不评价漏音的力度。

## Data and scoring / 数据与方法

- Official [SMD v2, Zenodo record 13753319](https://zenodo.org/records/13753319), described by the [SMD project](https://www.audiolabs-erlangen.de/resources/MIR/SMD/). Use v2 synchronization rather than mixing v0/v2 labels. 本次使用官方 v2 的同步钢琴与 MIDI。
- Bach BWV849-01, Beethoven Op027No1-01 and Chopin Op028-04; each contributes 10–25 s and 40–55 s. Both adapters receive the same official mono 22050 Hz audio, resampled internally as needed. 三首各两个固定 15 秒窗口，输入相同。
- Freeze hashes in [the source manifest](../benchmarks/data-manifests/smd-v2-piano.json). No manual labels, time shifting or alignment fitting. 固定文件哈希，不人工标注、不调整时间对齐。
- Score onsets 0.1–14.9 seconds into each crop; truncate offsets at 15 seconds. Exclude notes already sounding at the left boundary. Raw MIDI key-release times, no CC64 sustain extension. 窗口边界留 0.1 秒，不给左边已起音的持续音计分，结束时间按窗口截断。
- mir_eval: onset tolerance 50 ms, pitch 50 cents; offset tolerance 20% or at least 50 ms. Macro-average the six excerpts. 所有参数一致，按六个片段宏平均。
- Training/test disjointness is not verified; SMD has been used in piano research. Timing uncertainty, style coverage and the small sample limit interpretation. 未核实训练集完全独立；不能据此声称无偏泛化成绩。
- Dataset CC BY-NC-SA 3.0; local noncommercial evaluation only. Do not include recordings or reference MIDI in the app, repository or promotional music. 仅公开来源、哈希与数值，不分发原音频或 MIDI。

Full per-case results, counts, times and Torch peaks: [report](../benchmarks/reports/piano-v1.json).

## Reproduce / 复现

Install the `benchmark` extra in a development environment. Prepare the two model packs and separately obtain the exact licensed SMD files listed in the manifest. 安装评测依赖，准备两个模型工具包，并依法下载清单中的数据文件。

```sh
python scripts/benchmark_piano.py --data <SMD-folder> \
  --manifest benchmarks/data-manifests/smd-v2-piano.json --output <results> \
  --basic-python <polyphonic-notes/env/python> --basic-models <polyphonic-notes/models> \
  --piano-python <piano-notes/env/python> --piano-models <piano-notes/models>
```

Use a fresh output folder after changing models, parameters or code; existing inference outputs are reused for rescoring. 修改模型、参数或实现后使用新的输出目录；已有输出只适合重复计分。
