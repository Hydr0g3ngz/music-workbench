# Repository split / 仓库拆分

- Music Studio: https://github.com/Hydr0g3ngz/music-studio — original song analysis; D:/Music Studio.
- Music Workbench: https://github.com/Hydr0g3ngz/music-workbench — creation/arrangement/mixing; D:/Music Workbench.

The workstation retains shared engine code under the internal `music_studio` namespace to preserve serialization/import compatibility. It is a separate checkout, remote, distribution (`music-workbench-local`), entry point (`music-workbench`) and default workspace. Historical compatibility pages remain internal; no requirement to install the classic product.
工作台暂保留内部 music_studio 包名以兼容已有项目及导入；这是独立仓库、独立发行包和独立启动入口，不依赖安装原产品。

Existing user data, model environments and running servers were not moved. New launches use outputs/workbench on port 8920. To open old projects, explicitly pass --workspace with the original absolute path after closing its previous server. Back up that directory first; do not run two versions against one workspace.
已有数据、模型环境和服务均未移动。旧项目需在原服务关闭后显式指定绝对路径打开，先备份，不让两个版本同时写入。

Model setup scripts use the new checkout by default. Existing large model runtimes may be reused through the documented runtime configuration paths without redownloading. No model weights or user audio are copied into this repository.
模型安装默认使用新目录；可按模型文档配置绝对路径复用已有环境与缓存，不会将模型权重或用户音频提交到仓库。
