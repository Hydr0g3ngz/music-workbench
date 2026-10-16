# Music Workbench · 启动 / Quick start

安装 Python 3.11/3.12，解压到可写目录，双击 `Start-Music-Workbench.cmd`。首次联网安装基础环境，模型单独安装。默认端口 8920（占用时尝试后续端口），项目目录 outputs/workbench。

Install Python 3.11/3.12, extract to a writable folder and run Start-Music-Workbench.cmd. Initial setup installs base dependencies, not models. Default port 8920, project directory outputs/workbench.

## 源码 / From source

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[ui,audio]"
music-workbench
```

无需显卡即可使用采样乐器、鼓点、MIDI、编排、混音与录音。录音时允许浏览器麦克风访问；停止后试听，确认才加入工程。

No GPU required for samples, grooves, MIDI, arrangement, mixing or recording. Allow microphone access, then stop and audition before adopting your take.

[录音 / Recording](docs/recording.md) · [生成 / Generation](docs/music-generation.md) · [分轨 / Separation](docs/separation.md) · [模型 / Models](docs/next-models.md)

## 数据 / Data

更新前备份 outputs；不要让两个版本同时写同一个 workspace。旧 Music Studio 数据不会自动迁移。原歌曲分析产品位于 https://github.com/Hydr0g3ngz/music-studio 。

Back up outputs before upgrades. Never run two versions against one workspace. Existing Music Studio data is not migrated automatically. The original analysis product is maintained separately.
