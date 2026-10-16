# Music Workbench roadmap / 工作台路线图

## 产品主线 / Product workflow

想法 → 导入/录音/生成素材 → 分轨与修复 → 编排 → 混音 → 导出。
Idea → import/record/generate → separate/restore → arrange → mix → export.

模型的数量不等于可用性。每项能力必须能生成可试听素材、按时间入轨、撤销、保存重开与最终导出。
Every capability must support audition, aligned adoption, undo, reopen and export.

## 1. 制作基础优先 / Production foundations first

首版单声道录音、设备选择与电平、试听后入轨、失败后的下载恢复已完成。切分、复制、吸附、自定义循环区间与节拍器可用。下一步以编排为主线推进素材变调/变速与节拍匹配；同步叠录、预备拍和延迟校准需要独立验证。
Initial mono recording, device selection/metering, audition/adoption and recovery downloads are implemented. Split/duplicate/snap, custom loop ranges and metronome are available. Next: pitch/time editing and beat matching for arrangement; synchronized overdubbing, count-in and latency calibration require separate validation.

## 2. 模型平台 / Model platform

统一模型清单、代码/权重独立许可、固定版本与哈希、显存/内存需求、安装/卸载/诊断、下载进度/取消、离线检测；所有模型使用独立推理环境。区分已验证、实验性、候选。
Unify model catalog, separate code/weight licenses, pinned revisions and hashes, memory requirements, install/remove/diagnostics, cancellable downloads and offline readiness. Isolate inference environments; distinguish verified, experimental and candidate models.

## 3. 按工作流扩展 / Expand by workflow

- 修复：先完善现有语音降噪与响度流程，再评估音乐修复/去混响。Restoration: finish existing cleanup/loudness, then evaluate music restoration and dereverberation.
- 分轨：扩展鼓/贝斯/其他声部，比较质量与耗时。Separation: drums/bass/other, with quality and runtime comparisons.
- 创作：生成延续、局部重生成、参考音频与可控长度；先验证模型支持再承诺。Creation: continuation, region regeneration, reference audio and duration controls, subject to actual model support.
- 转录：多音 MIDI、鼓转录与节拍对齐，输出必须能继续编辑。Transcription: polyphonic MIDI, drum transcription and beat alignment with editable outputs.
- 声音设计：音效生成、音色转换与变调变速；声线能力单独列授权与使用边界。Sound design: effects generation, timbre conversion, time stretch/pitch shift; voice features require separate license review.

候选参考：Demucs/MSST、ACE-Step、Basic Pitch、MT3、DeepFilterNet、Resemble Enhance、AudioCraft。此处是候选方向，不代表均已接入、可商用或适合每台显卡。
Candidates include Demucs/MSST, ACE-Step, Basic Pitch, MT3, DeepFilterNet, Resemble Enhance and AudioCraft; this is not a claim of integration, commercial eligibility or hardware compatibility.

## 4. 验收与 Agent / Acceptance and Agent

固定授权测试音频；每模块记录质量、失败率、冷/热启动、峰值显存/RAM、CPU回退和取消恢复。界面覆盖导入到导出整条路径，不用模型数量充当 benchmark。
Use licensed fixed fixtures; measure quality, failure rate, cold/warm runtime, peak VRAM/RAM, CPU fallback and cancellation recovery. Test import-to-export workflows.

等项目/素材/轨道/任务/历史 API 稳定后，再将 Agent 接到同一组可撤销操作；当前不把聊天界面作为主入口。
Integrate Agent with the same reversible operations after project/asset/track/task/history APIs stabilize; chat is not the current primary interface.
