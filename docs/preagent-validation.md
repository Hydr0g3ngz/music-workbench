# dev20 创作基础验证 / Creation foundation verification

[版本说明 / Release notes](releases/v0.2.0.dev20.md) · [技术目录 / Technical reference](technical-reference.md)

记录日期：2026-10-17。只修改 Music Workbench；Music Studio 为独立项目。全部创作验证使用独立 QA 工作区，不改动现有作品。

Recorded 2026-10-17. Workbench changes only; Studio remains independent. Creation checks use a separate QA workspace.

## 自动检查 / Automated checks

- Python：**221 passed**；4 条现有依赖弃用警告（Starlette/httpx 和 audioread 的标准库兼容警告）。测试隔离本机 AI 工具目录，避免单测扫描或修复用户的真实工具包。Full Python suite, with isolated user-data paths for non-integration tests.
- Node：**90 passed**。覆盖分组复制和范围、保留源音符/淡变、路由连接、总线 Solo、实时参数更新不重载音源和暂停后释放节点。Frontend group, graph and lifecycle checks.
- 新总线渲染用真实 WAV 数值验证轨道推子后发送、总线增益/声像/Mute/Solo；100% 湿声首段无干声、尾音、旁路、撤销与 MWB 恢复。Offline numerical routing/tail/bypass/history tests use actual rendered PCM.
- Basic Pitch 验证可调参数传递、多音保留、时间/力度边界、缺失和损坏模型失败。These adapter tests do not replace real inference.

## 真实模型 / Actual model execution

Windows 11、RTX 4070 Laptop 8 GB、32 GB RAM。多音工具包为独立 Python 3.12.10、ONNX Runtime 1.23.2、Basic Pitch 0.4.0 官方源码/ONNX；权重 230,444 字节，SHA-256 `2c3c1d144bfa61ad236e92e169c13535c880469a12a047d4e73451f2c059a0ec`。

安装器校验官方 wheel、源码和权重，保留 Apache-2.0 LICENSE。环境中没有 Torch/TensorFlow，`pip check` 通过；实际运行离线推理，结果经工作台试听、采用、换音色、编辑与导出。已验证环境的依赖固定在独立 requirements 中。Only this Windows environment is verified; other platforms are not inferred from it.

[五首 GuitarSet 参数评测](polyphony-benchmark.md)运行 15 次真实 CPU 转录，不引入手工标注。默认 onset F1 0.6717、onset+offset F1 0.3329。训练数据可能重叠，不作无偏排名、力度准确率或峰值 RAM 结论。

## 界面与作品 / UI and creation

[《窗灯》](creations/windowlight.md)从空工程开始，界面完成生成、裁切、多音处理、换音色、量化、双击删音符、成组复制 8→32 小节、撤销/重做、总线发送、创作蓝图、参考变奏与段落采用。后期层次筛选和精确淡变明确记录为脚本编辑。

完整播放建立 7 个片段音源、请求 2 份音频与 3 份马林巴采样；总线音量调整后和自动播放结束前没有重复音频请求或源重建，页面未捕获错误。曾因开发服务中断产生的连接失败不算作成功回归；服务恢复后重新载入执行上述检查。

Playback instrumentation verifies no repeated source loading; it is not a calibrated audio-device dropout measurement or a listening-quality score. Both language layouts are inspected. The offline handbook explains the new workflow.

补充界面回归：Shift 点击添加整组为四片段、取消一组回到两片段，以及取消最后一组回到零选择均通过。总线重命名后，三条轨道的输出选项和发送标签立即更新。Whole-group Shift add/remove, empty selection and live route-label refresh are verified in the browser.

导出 WAV/MIDI/MWB；恢复后工程内容相同，修改总线后撤销回到相同状态，再导出 WAV 哈希完全一致。最终立体声 44.1 kHz / 24-bit / 65.7 秒，约 −19.96 LUFS / −2.00 dBTP。见[机器可读记录](../benchmarks/reports/windowlight-workflow-v1.json)。

## 升级保留 / Existing projects

启动 dev20 前后，现有工作区的全部 arrangement 表逐行比较相同：8 条工程记录（含回收站）、10 条处理关联、0 条 fitting 关联。应用入口运行 dev20，现有作品未修改。新字段保持默认值兼容；dev20 新保存工程不能保证被旧版接受。

All arrangement-table rows were identical across the local preview upgrade. Older projects remain intact; backward opening of newly saved dev20 projects is not promised.

## 独立运行包 / Bundled runtime

使用 Windows 安装器的嵌入式 Python，把 PATH 限制为 System32：自动启动、端口占用后换端口、再次启动复用服务和内置示例 WAV 导出均通过；测试工具本身由外部开发 Python 驱动，不把它视为应用依赖。

Packaged HTTP checks run the app with embedded Python and restricted PATH. They verify entry redirects, all three branded pages, new static modules, offline handbook, six tool packs, grouped bus routing, undo/redo, WAV/MIDI/credits and MWB recovery. Restoring Windowlight and rendering in the basic packaged app produces the same WAV SHA-256 as source, without neural inference dependencies. Source package files are compared byte-for-byte with the staged runtime.

本轮完成安装器编译、WebView2 前置安装包签名检查和嵌入式运行验证；未在全新 Windows 上重新走完整安装向导、卸载或缺少 WebView2 的安装流程。安装器资源中的文件版本按当前构建版本生成，避免仍显示 dev14 的数字版本。安装包未签名，模型另行下载。

The installer is compiled with a verified WebView2 prerequisite. This is not a clean-machine install/uninstall test. Installer file-version metadata follows the build version; the app remains unsigned and models download separately.

## 尚未证明 / Not established

未验证所有 GPU、全新 Windows 虚拟机、目标青少年用户完成率、长时间硬件音频稳定性、专业监听质量、独立钢琴转录准确率或 Transkun。VST、同步叠录、延迟补偿、效果参数自动化、更多声音模型与深度 Agent 操作仍未提供。此版本打通创作主流程，不代表通用专业 DAW 的全部功能。

No claim of universal hardware compatibility, professional mastering, full DAW parity or complete transcription accuracy is made. Deep Agent operation remains a subsequent phase.
