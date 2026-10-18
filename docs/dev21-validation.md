# dev21 validation / 验证记录

Version: 0.2.0.dev21. This report describes development-host evidence, not universal compatibility. 本文记录开发机上的实际验证，不代表所有电脑均通过。

| Check / 检查 | Evidence / 结果 |
| --- | --- |
| Python suite | 223 passed; four dependency deprecation warnings |
| Frontend suite | 93 passed, including group bounds, note thinning, routing/source reuse and notification recovery |
| Static checks | Ruff passed |
| Managed piano pack | Official Transkun 2.0.1 source/checkpoint verified; inference-only environment installed; real offline sample produced nonempty notes/MIDI/audition |
| Piano task in the UI | 16 s input on RTX 4070 Laptop 8 GB: model call 10.764 s, invocation 18.313 s, Torch peak 904.03 MiB |
| Explicit CPU piano task | Same 16 s clip: model call 22.928 s, invocation 30.391 s, FP32; no CPU peak-memory measurement |
| Piano quality | Six frozen SMD v2 excerpts, identical audio to both adapters; [protocol/results](piano-benchmark.md) |
| UI creation | After the Rain: empty project → ACE-Step → Transkun → simplified editable notes → marimba → grouped 32 bars → reference variation → buses/sends → batch ending → WAV/MIDI/MWB |
| Portable case | Restored content identical; rendered WAV byte-identical to the UI export; [case evidence](../benchmarks/reports/after-the-rain-v1.json) |
| Playback | Two audio sources in the creation case; playhead advances across live fader changes. Shared-source 32-track/96-clip/8-bus, 600 s fixture reopens and plays near the start/end; fader changes add no audio fetches |
| Save/adoption regression | Simulated 350 ms save latency with overlapping edits/group action: no HTTP 409. During delayed adoption, edits are blocked and Escape cannot dismiss the busy guard. Post-adoption edit succeeds |
| Selection/notification regression | Quantize/undo, clear MIDI selection and preview simplification without page errors; repeated invalid fade operations recover the error notice after dialog rebuilds |
| Initial loading | A modal prevents editing until project initialization completes, avoiding early input being overwritten by loaded state |
| Bundled runtime | Source modules match staged files. With only System32 on PATH: starts without system Python, handles occupied port, reuses existing service, creates/exports the lesson without model dependencies |
| Packaged workflow | Seven processing packs listed, static files/handbook load, groups/buses/history retained, WAV/MIDI export and MWB round-trip; the AI case renders identically without installing model runtimes in the base app |
| Actual install/upgrade/uninstall | Unique QA AppId: install dev20, upgrade to dev21 without specifying a new directory, run bundled runtime, uninstall. Program removed; separately stored dev20 project database hash unchanged |
| Existing local preview | Upgraded owned 8922 service. Seven active user projects plus one trashed project preserved; arrangement/processing/fitting database rows unchanged |

## Scope / 边界

- Windows development host, RTX 4070 Laptop 8 GB, 32 GB RAM. No clean Windows VM or additional physical GPUs were available. Actual host installation is not a clean-machine certification. 未进行全新 Windows 虚拟机或其他实体显卡测试。
- The stress fixture shares one source among its clips. It does not establish worst-case memory, audio-underrun performance or 32 unique long files. 大工程检查不等于完整 DAW 性能认证。
- Piano scores use a small development set and unverified training disjointness. MIDI velocity MAE is not a calibrated expression score. Never distribute SMD audio/MIDI with the product or film. 不把小样本结果外推。
- AI inference is local after downloads; pack installation and repair need network access. Models are separate from the basic installer. CPU piano runs in the tested CUDA-capable pack; a small CPU-only Transkun installer is not provided. 模型按需下载，基础安装包不包含权重。
- Installer remains unsigned. Updates are manual through **Version & updates**. No unattended updater, VST, synchronized overdubbing or deep workstation Agent control is claimed. 安装器未签名，仍为开发预览。

The source benchmark script and numeric manifests/reports are included. Private QA workspaces, raw benchmark recordings and local environment paths are not part of the repository distribution. 源码包公开可复现脚本与数值；不发布私有工程、原始评测录音或本机环境路径。
