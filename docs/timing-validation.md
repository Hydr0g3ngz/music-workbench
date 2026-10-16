# Timing validation / 循环与节拍器验证

2026-10-16, Windows, Python 3.12, Chromium. Applies to 0.2.0.dev7.

- 149 Python tests and 52 Node tests passed, plus Ruff. Eight new Node cases cover beat events, fractional boundaries, seeks, adjacent scheduling windows, loop source offsets/joins, shared buffers/graphs, live click changes, delayed scheduler recovery, cleanup and dialog validation. Fourteen Python cases cover persistence/history, rejected bounds, nonfinite values, legacy rows and exports.
- API checks save/reopen fractional beat positions, undo/redo both settings, and reject invalid timing without changing the project. Simulated dev6 rows and history remain readable without eager migration. With loop and clicks enabled, complete WAV and MIDI exports are byte-identical to the same arrangement with them disabled.
- The non-editable wheel passed the installed release verifier in a separate environment with no Torch, Demucs, faster-whisper or Qwen-ASR. Packaged timing scripts/styles, settings persistence/history, samples, effects and exports were exercised.
- In Chrome, the four-track Midnight Sketch repeated a one-bar range for dozens of cycles with one audio request, four cached clip buffers and four effect graphs. Opening settings and switching language did not restart playback or issue another audio request. Scheduled cycles advanced by 2.2222222222 seconds at 108 BPM. Live click disable preserved the running clock.
- Browser checks covered empty-session metronome playback, range validation, selected-clip shortcut, apply/cancel, undo, reload and persisted settings. Chinese/English desktop dialogs and a 420 × 850 layout were visually inspected. At 420 px the body/document widths were both 420 px; dialog actions remained visible. Browser error output was empty.

中文：检查了时钟排程、循环边界和缓存复用，并在浏览器中持续运行、修改设置与重开工程。
循环开启前后导出文件完全一致；新功能不会把节拍声或重复片段写入导出。

These checks establish scheduling and functional behavior, not hardware timing accuracy or an exhaustive listening benchmark. A system/browser stall beyond the 1.5-second lookahead can miss playback. Recovery preserves timeline phase. Source discontinuities may click; effect tails persist across cycles. Synchronized overdubbing, count-in and latency calibration are not provided.

中文：未测量声卡端实际延迟；长时间后台阻塞仍可能漏播。循环边界的波形不连续与跨轮效果器尾音需要使用者结合素材调整。

Reproduce / 复现:

```sh
python -m pytest -q
python -m ruff check .
node --test tests/ui_timing.test.cjs tests/ui_station.test.cjs tests/ui_creation.test.cjs
python scripts/package_release.py
# In a separate venv, install the wheel with [ui,audio,agent] and httpx:
python scripts/verify_release.py --no-models
```
