"use strict";
((root) => {
  const esc = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
  function controls(model, values = {}, lang = "zh") {
    const tr = (zh, en) => lang === "zh" ? zh : en;
    const option = (value, label, current) => `<option value="${value}" ${value === current ? "selected" : ""}>${label}</option>`;
    let html = "";
    if (model.device !== "cpu") {
      const device = values.device || "auto";
      html += `<label>${tr("运行设备", "Run on")}<select data-model-option="device">${option("auto", tr("自动选择", "Automatic"), device)}${option("cpu", "CPU", device)}${model.devices?.includes("cuda") ? option("cuda", "NVIDIA GPU", device) : ""}</select></label>`;
    }
    if (model.stage === "lyrics") {
      html += `<label>${tr("录音语言", "Audio language")}<select data-model-option="language">${[["", tr("自动识别", "Detect automatically")], ["zh", "中文"], ["en", "English"], ["ja", "日本語"], ["ko", "한국어"], ["es", "Español"], ["fr", "Français"], ["de", "Deutsch"]].map(([v, label]) => option(v, label, values.language || "")).join("")}</select></label>`;
    }
    if (model.id === "qwen3-asr") {
      html += `<label>${tr("时间精度", "Word timing")}<select data-model-option="alignment">${[["auto", tr("自动 · 使用工具包推荐", "Automatic · pack default")], ["qwen", tr("逐字对齐 · 较慢", "Acoustic word timing · slower")], ["native", tr("粗略段落 · 较快", "Coarse paragraphs · faster")]].map(([v, label]) => option(v, label, values.alignment || "auto")).join("")}</select></label>`;
    }
    if (model.stage === "denoise") {
      html += `<label>${tr("降噪强度 · 0–1", "Cleanup strength · 0–1")}<input type="number" min="0" max="1" step="0.05" value="${esc(values.strength ?? 1)}" data-model-option="strength"></label>`;
    }
    return html ? `<div class="model-options">${html}</div>` : "";
  }
  function read(card) {
    const values = {};
    for (const input of card.querySelectorAll("[data-model-option]")) {
      const key = input.dataset.modelOption;
      values[key] = key === "strength" ? Number(input.value) : key === "language" ? input.value || null : input.value;
      if (input.checkValidity && !input.checkValidity()) { input.reportValidity(); throw Error("Invalid tool setting"); }
    }
    return values;
  }
  const api = { controls, read };
  if (typeof module !== "undefined") module.exports = api;
  else root.StationModelControls = api;
})(typeof window === "undefined" ? globalThis : window);
