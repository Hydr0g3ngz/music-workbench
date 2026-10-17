# Music Workbench 与 Music Studio / Two projects

| 项目 / Project | 用途 / Purpose | 仓库 / Repository |
| --- | --- | --- |
| Music Workbench | 创作、编排、录音、混音与本地模型 / Creation, arrangement, recording, mixing and local models | [music-workbench](https://github.com/Hydr0g3ngz/music-workbench) |
| Music Studio | 整曲分离、歌词、旋律、和弦与节拍分析 / Full-song stems, lyrics, melody, chord and beat analysis | [music-studio](https://github.com/Hydr0g3ngz/music-studio) |

两个产品独立安装、发布和保存项目。使用 Music Workbench 无需安装 Music Studio。内部 `music_studio` 包名用于兼容工程及 Python 导入，并不表示需要同时运行两个产品。

The products have independent installations, releases and project storage. Workbench does not require Studio. The internal `music_studio` Python namespace preserves import and serialization compatibility.

Music Workbench 安装版默认作品目录为 `%LOCALAPPDATA%\MusicWorkbench\Projects`；源码默认为 `outputs/workbench`。通过 `.mwb` 转移工作台工程。Music Studio 的歌曲分析结果不自动转换成编排工程；需要时导出音轨或 MIDI，再导入工作台。

Installed Workbench projects default to `%LOCALAPPDATA%\MusicWorkbench\Projects`; source launches use `outputs/workbench`. Transfer arrangements with `.mwb`. Studio analysis results are not automatically converted into arrangements; export stems/MIDI and import them into Workbench.

高级用户可按模型文档连接已有隔离环境与缓存；不要让两个服务同时写同一工作区。拆分前的说明与分析评测保留在 [技术与历史参考](technical-reference.md)，不作为当前安装指南。

Advanced users can connect existing isolated model runtimes/caches using the model guides. Use one service per workspace. Pre-split documentation and analysis evaluations remain in [technical reference](technical-reference.md).
