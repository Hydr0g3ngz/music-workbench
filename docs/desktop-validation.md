# dev11 验证 / Validation

验证日期：2026-10-16，Windows x64。这里记录开发验收，不代表已完成青少年可用性研究或正式稳定发布。

173 Python tests、66 Node UI tests、Ruff 和 diff 检查通过。安装 wheel 后，原有发布烟测通过；与当前源码的 148 个包文件逐一一致。

## 基础便携包 / Portable basics

内置 CPython 3.12.10 x64，SHA-256 固定；依赖版本与许可证保留。测试子进程仅保留 System32 的 PATH，移除 PYTHONHOME/PYTHONPATH；在带中文和空格的新作品目录启动。

- 首选端口故意占用，自动选择空闲端口并等到就绪。
- 二次启动复用相同服务，不创建第二个后台；退出复用控制器不影响原服务。
- 无模型配置时创建四轨示例，导出真实 WAV 与响度结果。
- 正常退出后释放端口与工作目录锁。原生 Windows 启动器编译通过；后台协议和实际浏览器流程已测试，尚无自动化原生窗口点击覆盖或全新 Windows 虚拟机验收。
- 实际浏览器打开便携版：未配置 AI 时提供说明与“先玩示例”，成功进入示例、显示首次创作提示并播放。双语首页和创作窗口分别检查。

Reproduce on Windows after building a portable folder:

```powershell
python scripts/verify_portable.py <portable-folder> --workspace <fresh-test-folder>
```

This tests application-local Python, an occupied port, relaunch reuse, no-model example creation, WAV export and clean shutdown. A real browser additionally exercised the unconfigured-AI guidance and editable-example path. Native launcher compilation passed; automated native-window clicking and a clean Windows VM remain untested.

## 制作链 / Production path

- [真实重绘记录](../benchmarks/results/repaint-dev11.json)：16 秒既有 AI 素材重绘 6–10 秒，选区外采样完全一致。浏览器原位采用，撤销和重做通过。
- [音量与过渡播放记录](../benchmarks/results/volume-playback-dev11.json)：两段 16 秒素材，2 拍/1.111111 秒等功率交叉淡化，带音量曲线；WAV 全长 30.888889 秒。浏览器主输出 Opus 捕获与离线 WAV 的 10 ms RMS 相关系数 0.993665，没有额外静音窗。覆盖过渡边界，不是听感评价。
- 曲线 WAV 逐采样与预期误差 `<3e-7`；便携工程恢复、撤销、边界校验通过。
- 原有五条工程数据库记录（包括回收站）内容、素材与历史逐字节核对未改变。验证素材使用独立工作目录。

Real model inference and browser audio capture validate the implemented path, not musical quality. Existing five project rows, asset references and histories were unchanged. Model tests used a separate workspace. Model installation still needs a technical setup guide; a no-terminal installer, signed distribution, runtime security upgrade and actual beginner testing are next-release work.
