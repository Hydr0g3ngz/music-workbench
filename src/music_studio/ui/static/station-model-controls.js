"use strict";
((root) => {
  const esc = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll('"', "&quot;");
  function controls(model, values = {}, lang = "zh") {
    const tr = (zh, en) => (lang === "zh" ? zh : en);
    const option = (value, label, current) =>
      `<option value="${value}" ${value === current ? "selected" : ""}>${label}</option>`;
    let html = "";
    if (model.device !== "cpu") {
      const device = values.device || "auto";
      html += `<label>${tr("运行设备", "Run on")}<select data-model-option="device">${option("auto", tr("自动选择", "Automatic"), device)}${option("cpu", "CPU", device)}${model.devices?.includes("cuda") ? option("cuda", "NVIDIA GPU", device) : ""}</select></label>`;
    }
    if (model.stage === "lyrics") {
      html += `<label>${tr("录音语言", "Audio language")}<select data-model-option="language">${[
        ["", tr("自动识别", "Detect automatically")],
        ["zh", "中文"],
        ["en", "English"],
        ["ja", "日本語"],
        ["ko", "한국어"],
        ["es", "Español"],
        ["fr", "Français"],
        ["de", "Deutsch"],
      ]
        .map(([v, label]) => option(v, label, values.language || ""))
        .join("")}</select></label>`;
    }
    if (model.id === "qwen3-asr") {
      html += `<label>${tr("时间精度", "Word timing")}<select data-model-option="alignment">${[
        ["auto", tr("自动 · 使用工具包推荐", "Automatic · pack default")],
        ["qwen", tr("逐字对齐 · 较慢", "Acoustic word timing · slower")],
        ["native", tr("粗略段落 · 较快", "Coarse paragraphs · faster")],
      ]
        .map(([v, label]) => option(v, label, values.alignment || "auto"))
        .join("")}</select></label>`;
    }
    if (model.stage === "denoise") {
      html += `<label>${tr("降噪强度 · 0–1", "Cleanup strength · 0–1")}<input type="number" min="0" max="1" step="0.05" value="${esc(values.strength ?? 1)}" data-model-option="strength"></label>`;
    }
    if (model.id === "basic-pitch") {
      html += `<label>${tr("起音阈值 · 越高越少误检", "Onset threshold · higher rejects notes")}<input type="number" min=".1" max=".95" step=".05" value="${esc(values.note_onset ?? 0.5)}" data-model-option="note_onset"></label><label>${tr("持续阈值", "Frame threshold")}<input type="number" min=".05" max=".95" step=".05" value="${esc(values.note_frame ?? 0.3)}" data-model-option="note_frame"></label><label>${tr("最短音符 · 毫秒", "Minimum note · ms")}<input type="number" min="40" max="1000" step="any" value="${esc(values.note_min_ms ?? 127.7)}" data-model-option="note_min_ms"></label>`;
    }
    return html ? `<div class="model-options">${html}</div>` : "";
  }
  function read(card) {
    const values = {};
    for (const input of card.querySelectorAll("[data-model-option]")) {
      const key = input.dataset.modelOption;
      values[key] =
        key === "strength" || key.startsWith("note_")
          ? Number(input.value)
          : key === "language"
            ? input.value || null
            : input.value;
      if (input.checkValidity && !input.checkValidity()) {
        input.reportValidity();
        throw Error("Invalid tool setting");
      }
    }
    return values;
  }
  function clipWindow(task) {
    const clip = task?.source_clip;
    const ratio = task?.stage === "transform" ? task.time_ratio || 1 : 1;
    if (clip && task.source_range?.scope === "clip" && task.input_audio)
      return {
        offset: 0,
        duration:
          Math.round(task.input_audio.frames / ratio) /
          task.input_audio.sample_rate,
      };
    return {
      offset:
        Math.max(0, (clip?.offset || 0) - (task?.source_range?.start || 0)) /
        ratio,
      duration: clip ? clip.duration / ratio : null,
    };
  }
  function sourceReport(task, report) {
    const origin = task?.source_range?.start || 0;
    return { ...report, beats: report.beats?.map((time) => time + origin) };
  }
  const api = { controls, read, clipWindow, sourceReport };
  if (typeof module !== "undefined") module.exports = api;
  else root.StationModelControls = api;
})(typeof window === "undefined" ? globalThis : window);
