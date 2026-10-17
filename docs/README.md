# Music Workbench 文档

[English](README.en.md) · [返回项目首页](../README.md)

## 开始使用

- [安装与升级](windows-install.md)：Windows 安装器、电脑要求、作品位置。
- [五步入门](first-sketch.md)：从试听到改音符、混音与导出。
- [工作台使用指南](create-preview.md)：界面布局、轨道与片段、保存与导出。
- [源码启动](../QUICKSTART.md)：Python 环境与启动命令。
- [产品与数据边界](product-boundaries.md)：Workbench 与 Studio、旧书签和素材编辑器。

## 制作音乐

| 工作 | 指南 |
| --- | --- |
| 音色、鼓点、导入 MIDI | [采样乐器与 MIDI](creation-library.md) |
| 循环练习与节拍 | [循环与节拍器](timing.md) |
| 麦克风或声卡录音 | [本地录音](recording.md) |
| 组织动机与段落 | [创作蓝图与编曲方法](arranging-methods.md) |
| 让音频对齐工程 | [对拍、变速与候选比较](material-fitting.md) |
| 效果器与电平 | [混音](mixing.md) |
| 渐强、交叉淡化、局部重绘 | [音量与过渡](volume-and-repaint.md) |

## 使用本地 AI

- [支持的模型与安装方式](models.md)：区分软件内自动配置、手动安装和研究候选。
- [硬件与实测速度](model-hardware.md)
- [RoFormer 与 Qwen 自动配置](qwen-and-separation.md)：人声伴奏、转写与逐字时间。
- [ACE-Step 音乐生成](music-generation.md)：文字、参考变奏、参数与故障排查。
- [人声与伴奏分离](separation.md)：试听后对齐采用，保留原素材。
- [AI 制作流程](ai-production-workflow.md)：从构思到可恢复交付。
- [《云隙电台》制作案例](creations/radio-through-the-clouds.md)：生成、分轨与可编辑 MIDI 的组合示例。

## 贡献与技术参考

- [贡献指南](../CONTRIBUTING.zh-CN.md) · [当前路线图](workbench-roadmap.md) · [平台设计](workbench-plan.md)
- [模型候选调研](local-model-candidates.md) · [开放素材与存储选型](audio-resources.md)
- [评测与历史文档目录](technical-reference.md)：冻结数据、复现协议、版本验证及兼容编辑器。
- [发布素材](launch-kit.md) · [更新记录](../CHANGELOG.md) · [第三方许可](../THIRD_PARTY_NOTICES.md)

整曲歌词、旋律、和弦与节拍分析由独立项目 [Music Studio](https://github.com/Hydr0g3ngz/music-studio) 提供。兼容页面和拆分前文档保留供维护与复现，不是当前工作台的入门入口。
