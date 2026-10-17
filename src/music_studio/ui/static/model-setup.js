"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const tr = (zh, en) => localStorage.getItem("station-language") === "en" ? en : zh;
  const esc = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
  const cards = new Map(), pending = new Set(), errors = new Map();
  let rows = [], polling = false, stopped = false;
  const labels = {
    "tools-title": ["为你的下一步创作准备工具", "Tools for your next creative step"],
    "tools-intro": ["按需安装。语音清理和转写可使用 CPU；分轨、旋律提取推荐 NVIDIA 加速。首次下载后可离线处理。", "Install what you need. CPU works for speech cleanup and transcription; NVIDIA acceleration is recommended for stems and melody. Process offline after setup."],
    "manual-title": ["安装后，在工作台使用", "Use installed tools in the workstation"],
    "manual-copy": ["选择一个音频片段，再打开 AI 模型。Qwen 可选择逐字定位或较快的粗略时间；分离结果可试听后加入轨道。", "Select an audio clip and open AI Models. Choose acoustic word timing or faster coarse timing for Qwen; audition separated stems before adopting them."],
    "manual-link": ["打开工作台模型列表 →", "Open workstation models →"],
  };
  const stages = {
    preparing: ["准备开始", "Preparing"], runtime: ["准备独立环境", "Preparing private environment"],
    dependencies: ["安装运行组件", "Installing runtime components"],
    models: ["下载并校验模型", "Downloading and verifying models"],
    verify: ["正在离线处理示例音频，验证各项功能", "Processing example audio offline to verify every tool"],
    complete: ["验证完成", "Verified"],
  };
  const states = {
    idle: ["未安装", "Not installed"], installing: ["正在准备", "Setting up"],
    cancelling: ["正在暂停", "Pausing"], cancelled: ["已暂停", "Paused"],
    interrupted: ["已中断，可继续", "Interrupted; resume"], failed: ["准备失败，可重试", "Setup failed; retry"],
    ready: ["准备完成", "Set up"],
  };
  function draw() {
    for (const [id, pair] of Object.entries(labels)) $(id).textContent = tr(...pair);
    for (const row of rows) {
      if (!cards.has(row.id)) {
        const card = document.createElement("section");
        card.className = "setup-panel tool-pack";
        card.id = row.id;
        card.innerHTML = `<div class="setup-panel-top"><h3 data-field="title"></h3><span class="tool-badge" data-field="state"></span></div>
          <p data-field="description"></p><p class="tool-meta" data-field="resources"></p>
          <div data-field="progress-wrap" hidden><p data-field="stage"></p><progress max="1" value="0"></progress></div>
          <p class="tool-error" data-field="error" role="alert"></p>
          <div class="setup-actions"><button class="primary" data-action="start"></button><button data-action="cancel" hidden></button><button data-action="check"></button><a data-action="use"></a></div>
          <p class="tool-verification" data-field="verification"></p>
          <details><summary data-field="details-title"></summary><p data-field="backend"></p><p class="tool-directory" data-field="directory"></p><a data-field="source" target="_blank" rel="noreferrer"></a></details>`;
        card.addEventListener("click", (event) => {
          const button = event.target.closest("button[data-action]");
          if (button && !button.disabled) action(row.id, button.dataset.action);
        });
        $("tool-pack-list").appendChild(card);
        cards.set(row.id, card);
        if (location.hash === "#" + row.id) card.scrollIntoView({ block: "center" });
      }
      const card = cards.get(row.id), field = (key) => card.querySelector(`[data-field="${key}"]`);
      const button = (key) => card.querySelector(`[data-action="${key}"]`);
      const active = ["installing", "cancelling"].includes(row.state), busy = pending.has(row.id);
      const ready = row.installed || row.checked;
      field("title").textContent = tr(...row.title);
      field("description").textContent = tr(...row.description);
      field("state").textContent = active ? tr(...states[row.state]) : ready ? tr("可使用", "Available") : tr(...(states[row.state === "ready" ? "idle" : row.state] || states.idle));
      field("resources").textContent = `${row.device === "cuda" ? "NVIDIA · " + ((row.preflight.min_vram_mib || 4000) / 1000).toFixed(0) + tr(" GB 显存及以上", " GB+ VRAM") : "CPU"} · ${tr("预计下载", "Download estimate")} ${row.download_estimate} · ${tr("磁盘预留", "Free disk")} ${(row.required_free_bytes / 1024 ** 3).toFixed(0)} GB`;
      field("progress-wrap").hidden = !active;
      field("stage").textContent = tr(...(stages[row.progress?.stage] || stages.preparing));
      card.querySelector("progress").value = row.progress?.fraction || 0;
      const reason = (row.preflight.reasons || []).map((r) => r === "windows-x64" ? tr("自动安装需要 Windows 64 位。", "Automatic setup requires Windows x64.") : r === "cuda-compatibility" ? (row.preflight.min_capability >= 8 ? tr("需要 Ampere 或更新的 NVIDIA 显卡、至少 8 GB 显存和 570 或更新驱动。", "Requires NVIDIA Ampere or newer, at least 8 GB VRAM and driver 570 or newer.") : tr("需要 Turing 或更新的 NVIDIA 显卡、至少 4 GB 显存和 570 或更新驱动。", "Requires NVIDIA Turing or newer, at least 4 GB VRAM and driver 570 or newer.")) : tr("磁盘空间不足，请释放空间后重试。", "Free disk space before retrying.")).join(" ");
      const failed = row.capabilities?.find((m) => !m.runnable && m.health.state !== "unchecked");
      const diagnostic = failed ? `${tr(...failed.title)}: ${failed.health.error || tr("缺少运行组件或权重，请安装或修复工具包。", "Runtime components or weights are missing. Install or repair this pack.")}` : "";
      field("error").textContent = errors.get(row.id) || row.error || diagnostic || (!ready ? reason : "");
      button("start").textContent = ready ? tr("修复安装", "Repair setup") : tr("下载并安装", "Download and install");
      if (["failed", "cancelled", "interrupted"].includes(row.state)) button("start").textContent = tr("继续准备", "Resume setup");
      button("start").disabled = busy || active || !row.preflight.supported;
      button("cancel").textContent = tr("暂停", "Pause");
      button("cancel").hidden = !active;
      button("cancel").disabled = busy || row.state === "cancelling";
      button("check").textContent = busy ? tr("处理中…", "Working…") : tr("检查当前环境", "Check environment");
      button("check").disabled = busy || active;
      button("use").textContent = row.id === "speech-cleanup" ? tr("打开语音清理 →", "Open speech cleanup →") : tr("在工作台使用 →", "Use in workstation →");
      button("use").href = row.entry;
      button("use").hidden = !ready;
      field("verification").textContent = row.installed ? tr("已通过示例音频的离线推理验证。", "Passed offline inference on example audio.") : row.checked ? tr("当前配置的运行环境与权重已检查。", "Configured runtime and weights checked.") : "";
      field("details-title").textContent = tr("模型与存放位置", "Models and storage");
      field("backend").textContent = row.backend;
      field("directory").textContent = row.preflight.directory;
      field("source").textContent = row.license + " ↗";
      field("source").href = row.source;
    }
  }
  async function api(path = "", post = false) {
    const response = await fetch("/api/workstation/model-setup" + path, { method: post ? "POST" : "GET" });
    const data = await response.json();
    if (!response.ok) throw Error(data.detail || response.statusText);
    return data;
  }
  async function refresh() {
    if (polling || stopped) return;
    polling = true;
    try {
      rows = await api();
      $("tools-error").textContent = "";
      draw();
    } catch (error) {
      $("tools-error").textContent = tr("暂时无法读取工具状态，请重试。", "Cannot read tool status. Please retry.");
    } finally { polling = false; }
  }
  async function action(key, operation) {
    pending.add(key); errors.delete(key); draw();
    try {
      const result = await api(`/${encodeURIComponent(key)}/${operation}`, true);
      rows = rows.map((row) => row.id === key ? result : row);
    } catch (error) { errors.set(key, error.message); }
    finally { pending.delete(key); draw(); }
  }
  $("language").addEventListener("click", draw);
  addEventListener("storage", draw);
  refresh();
  const timer = setInterval(refresh, 2500);
  addEventListener("pagehide", () => { stopped = true; clearInterval(timer); });
})();
