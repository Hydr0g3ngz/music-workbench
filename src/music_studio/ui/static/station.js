"use strict";
(() => {
  const $ = (id) => document.getElementById(id),
    { uid, duration, splitClip, StationEngine } = Station;
  const engine = new StationEngine(),
    previewEngine = new StationEngine(),
    generationAudio = new Audio(),
    colors = ["#b69aff", "#86c9bc", "#e7b985", "#8cabed", "#d592b5"];
  let recordingPanel,
    timingPanel,
    workflowPanel,
    compositionPanel,
    envelopePanel,
    fitPanel,
    auditionPanel,
    tutorialPanel;
  const s = {
    session: null,
    track: null,
    clip: null,
    view: "assets",
    dock: "mixer",
    zoom: 38,
    position: 0,
    dirty: false,
    change: 0,
    saving: null,
    models: [],
    tasks: [],
    generations: [],
    generationHealth: null,
    library: null,
    lang: localStorage.getItem("station-language") || "zh",
  };
  let saveTimer,
    toastTimer,
    polling = false,
    starting = false,
    previewKey = null,
    previewTimer,
    pendingMidi = null;
  let generationAudioKey = null,
    generationSubmitting = false;
  const words = {
    generationKey: "Key",
    generationMode: "Generation mode",
    generationStrength: "Reference strength",
    generationRegion: "Use loop range duration",
    cancel: "Cancel",
    timingTitle: "Loop and metronome",
    timingCopy:
      "Focus on a section. The loop follows your tempo; the metronome keeps you in time.",
    timingLoop: "Enable range loop",
    timingStart: "Start bar",
    timingEnd: "End bar (exclusive)",
    timingBars:
      "For example, 1 → 5 repeats bars 1–4. Use decimals for beat positions. Minimum length: 1/4 beat.",
    timingClip: "Use selected clip",
    timingWhole: "Whole arrangement",
    timingClick: "Enable metronome during playback",
    timingVolume: "Click volume",
    timingAccent: "Accent the first beat of each bar (4/4)",
    timingListen:
      "The metronome is for listening. Exports contain the full arrangement, without clicks or loop repetitions.",
    timingApply: "Apply settings",
    recording: "Record your sound",
    recordingCopy:
      "Connect a microphone or instrument input. Check the level, record and audition, then add your take to the session.",
    recordDevice: "Audio input",
    recordDefault: "System default input",
    recordEnable: "Enable input",
    recordLevel: "Input level",
    recordStart: "Start recording",
    recordStop: "Stop recording",
    recordAdopt: "Add to session",
    recordDownload: "Download WAV",
    recordDiscard: "Discard and reset",
    recordNote:
      "Mono recording, no models required; input is never played through speakers. Arrangement pauses during capture; synchronized overdubbing and latency compensation are not available yet. Add or download your take before closing this page.",
    projects: "Sessions",
    new: "New",
    previous: "Previous workbench ↗",
    export: "Export",
    assets: "Sound library",
    assetsTab: "Assets",
    instruments: "Instruments",
    models: "AI models",
    import: "Import audio / MIDI",
    factoryLibrary: "STARTER GROOVES",
    grooveCopy:
      "Two-bar performances by real drummers. Audition, edit notes and follow the session tempo.",
    credits: "Sources and attribution",
    creditsCopy:
      "Keep asset creators, licenses and modifications with your work",
    midiImport: "Import MIDI",
    midiTiming:
      "Keep performance timing and velocity on this session's beat grid. Tempo changes become note positions; the 4/4 grid does not change note times.",
    midiControllers:
      "CC64 sustain becomes note duration; instruments are approximated. Pitch bends, other controllers and automation are not imported yet.",
    sourceTempo: "Use MIDI's initial tempo in an empty session",
    addToSession: "Add to session",
    sessionAssets: "SESSION AUDIO",
    demoTitle: "A starting point for your sound",
    demoCopy: "Explore arrangement and mixing with an editable sketch.",
    demo: "Open demo session ↗",
    instrumentCopy:
      "Start with notes and choose a sound. Double-click the piano roll to add or remove notes.",
    instrumentNote:
      "VCSL sampled instruments, CC0. Audition and WAV export use the same samples. Original synth sounds remain available.",
    modelCopy:
      "Process the selected clip’s full source audio. Add results directly as new tracks.",
    comingModels: "Creation models · Planned",
    notIntegrated: "Not integrated; cannot run yet.",
    generationCopy:
      "Turn a sound idea into a music draft. Audition it, then add a track.",
    generationPrompt: "Describe the music",
    generationLyrics: "Lyrics",
    generationLanguage: "Vocal language",
    instrumental: "Instrumental",
    generationDuration: "Duration",
    generationAdvanced: "More parameters",
    generationGPUProfile: "GPU profile",
    generationGPUAuto: "Automatic",
    generationGPULow: "Save VRAM · DiT INT8 + CPU offload",
    generationGPUBalanced: "Balanced · DiT INT8 · 10 GB free VRAM",
    generationGPUQuality: "Original precision · BF16 · 18 GB free VRAM",
    generationSeed: "Random seed",
    generationSteps: "Inference steps",
    generationSubmit: "Generate music draft",
    generationProfile:
      "Experimental · NVIDIA GPU with 8 GB+ VRAM · precision and offload depend on the profile · no language model. Try 12–20s first. Generated tempo may differ from the target BPM.",
    audioProcessing: "AUDIO PROCESSING",
    taskDetails: "Parameters and diagnostics",
    local: "Local production · Your sound stays here",
    signature: "METER",
    ready: "Ready",
    arrangement: "Arrange",
    snap: "Snap",
    tracks: "TRACKS",
    addAudio: "＋ Audio track",
    addMidi: "＋ Instrument track",
    dropHint: "Drop audio here to build your sound.",
    emptyTitle: "Your next piece starts here.",
    emptyCopy: "Import a recording, write a melody or explore the demo.",
    mixer: "Mixer",
    effects: "Effects",
    piano: "Piano roll",
    tasks: "Tasks",
    mixerHint: "Listen, adjust and find your balance.",
    inspector: "Inspector",
    workflowNote: "Audio, notes and model outputs belong to one music project.",
    shortcutHint:
      "Space Play/Pause · Ctrl Z Undo · Double-click a clip to edit",
    exportCopy:
      "Export the arrangement with track effects, levels, pan, clip fades and output limiting.",
    mixExport: "Stereo mix · 44.1 kHz",
    midiExport: "Instrument tracks · Notes, velocity and tempo",
    projectFile: "Portable project · MWB",
    projectExport: "Arrangement + audio + credits; restore in Projects",
  };
  const chinese = new WeakMap(),
    tr = (zh, en) => (s.lang === "zh" ? zh : en);
  const esc = (x) =>
    String(x ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const icon = (name) => `<svg><use href="#i-${name}"/></svg>`;
  const content = () => s.session.content;
  const selectedTrack = () => content().tracks.find((t) => t.id === s.track);
  const selectedClip = () =>
    selectedTrack()?.clips.find((c) => c.id === s.clip);
  const asset = (id) => s.session.assets.find((a) => a.id === id);
  const seconds = (value) =>
    `${Math.floor(Math.max(0, value) / 60)
      .toString()
      .padStart(
        2,
        "0",
      )}:${(Math.max(0, value) % 60).toFixed(2).padStart(5, "0")}`;
  const beatSeconds = () => 60 / content().bpm;
  const snap = (value) =>
    $("snap").checked
      ? Math.round(value / (beatSeconds() / 4)) * (beatSeconds() / 4)
      : value;
  function toast(message, error = false) {
    const host = document.querySelector("dialog[open]") || document.body;
    if ($("toast").parentElement !== host) host.append($("toast"));
    $("toast").textContent = message;
    $("toast").classList.toggle("error", error);
    $("toast").hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(
      () => ($("toast").hidden = true),
      error ? 9000 : 3500,
    );
  }
  async function request(url, body, method = "POST") {
    const opts =
      body === undefined
        ? {}
        : {
            method,
            body: body instanceof FormData ? body : JSON.stringify(body),
            headers:
              body instanceof FormData
                ? {}
                : { "Content-Type": "application/json" },
          };
    const response = await fetch(url, opts);
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw Error(`HTTP ${response.status}`);
    }
    if (!response.ok)
      throw Error(
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail || data),
      );
    return data;
  }
  const base = () => `/api/workstation/projects/${s.session.id}`;
  function guarded(fn) {
    return async (...args) => {
      try {
        return await fn(...args);
      } catch (e) {
        toast(e.message, true);
      }
    };
  }
  function localize() {
    document.documentElement.lang = s.lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-t]").forEach((el) => {
      if (el.id === "audio-status") return;
      if (!chinese.has(el)) chinese.set(el, el.textContent);
      el.textContent =
        s.lang === "zh"
          ? chinese.get(el)
          : words[el.dataset.t] || chinese.get(el);
    });
    $("language").textContent = s.lang === "zh" ? "EN" : "中文";
    recordingPanel?.render();
    timingPanel?.render();
    $("asset-search").placeholder = tr("搜索素材…", "Search assets…");
    $("generation-prompt").placeholder = tr(
      "例如：温暖的爵士钢琴、轻鼓点和木贝斯，适合夜晚写作",
      "Warm jazz piano, brushed drums and upright bass, for late-night writing",
    );
    renderGenerationHealth();
    $("project-title").setAttribute(
      "aria-label",
      tr("工程名称", "Session name"),
    );
    $("audio-status").textContent = engine.playing
      ? tr("正在播放", "Playing")
      : starting
        ? tr("准备音频…", "Preparing audio…")
        : tr("准备就绪", "Ready");
  }
  function savedLabel() {
    $("save-state").textContent = s.saving
      ? tr("保存中…", "Saving…")
      : s.dirty
        ? tr("尚未保存", "Unsaved")
        : tr("✓ 已保存到本机", "✓ Saved locally");
  }
  function dirty() {
    tutorialPanel?.observe();
    s.dirty = true;
    s.change++;
    savedLabel();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(
      () => flush().catch((e) => toast(e.message, true)),
      450,
    );
  }
  async function flush() {
    clearTimeout(saveTimer);
    if (s.saving) await s.saving;
    if (!s.dirty) return;
    s.saving = (async () => {
      while (s.dirty) {
        const serial = s.change,
          snapshot = structuredClone(content());
        const result = await request(
          base(),
          { revision: s.session.revision, content: snapshot },
          "PUT",
        );
        s.session.revision = result.revision;
        s.session.can_undo = result.can_undo;
        s.session.can_redo = result.can_redo;
        if (serial === s.change) s.dirty = false;
      }
    })();
    savedLabel();
    try {
      await s.saving;
    } finally {
      s.saving = null;
      savedLabel();
      updateHistoryButtons();
    }
  }
  function pause() {
    engine.pause();
    s.position = Math.max(0, engine.position);
    $("play").innerHTML = icon("play");
    $("audio-status").textContent = tr("准备就绪", "Ready");
  }
  function mutate(fn, { live = false, render = true } = {}) {
    if (!live) pause();
    fn();
    dirty();
    if (live) engine.update(content());
    if (render) renderAll();
  }
  function accept(session, { selectLast = false } = {}) {
    const changedProject = session.id !== s.session?.id;
    if (changedProject) {
      s.tasks = [];
      s.generations = [];
    }
    s.session = session;
    tutorialPanel?.attach(session.id);
    s.dirty = false;
    s.change = 0;
    if (selectLast) {
      const t = content().tracks.at(-1);
      s.track = t?.id;
      s.clip = t?.clips[0]?.id;
    }
    if (!selectedTrack()) {
      s.track = content().tracks[0]?.id;
      s.clip = content().tracks[0]?.clips[0]?.id;
    }
    history.replaceState({}, "", `/station.html?session=${session.id}`);
    localStorage.setItem("station-session", session.id);
    if (changedProject && duration(content()) > 0)
      s.zoom = Math.max(
        0.5,
        Math.min(
          38,
          ($("arranger").clientWidth - headWidth() - 15) /
            (duration(content()) + (60 / content().bpm) * 2),
        ),
      );
    renderAll();
  }
  async function open(key) {
    stopPreview();
    await flush();
    engine.reset();
    s.position = 0;
    s.track = null;
    s.clip = null;
    accept(await request(`/api/workstation/projects/${key}`));
    s.tasks = [];
    renderTasks();
    await pollTasks();
  }
  async function create(demo = false) {
    stopPreview();
    await flush();
    engine.reset();
    s.position = 0;
    s.track = null;
    s.clip = null;
    accept(
      await request("/api/workstation/projects", {
        title: demo ? "Midnight Sketch" : tr("未命名工程", "Untitled session"),
        demo,
      }),
    );
    if (demo)
      toast(
        tr(
          "内置合成示例已载入，可自由编排和混音。",
          "Built-in synth demo loaded. Arrange and mix freely.",
        ),
      );
  }
  function headWidth() {
    return (
      parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue(
          "--track-head",
        ),
      ) || 188
    );
  }
  function renderAll() {
    if (!s.session) return;
    localize();
    $("browser-title").textContent = {
      assets: tr("声音素材", "Sound library"),
      instruments: tr("乐器与音色", "Instruments"),
      models: tr("本地 AI 模型", "Local AI models"),
    }[s.view];
    $("project-title").value = content().title;
    $("bpm").value = content().bpm;
    renderAssets();
    renderTracks();
    renderMixer();
    renderEffects();
    renderInspector();
    if (s.dock === "piano") renderPiano();
    renderInstruments();
    renderGrooves();
    updateHistoryButtons();
    savedLabel();
    workflowPanel?.render();
    compositionPanel?.render();
    envelopePanel?.render();
    fitPanel?.render();
    auditionPanel?.render();
    tutorialPanel?.render();
    $("session-summary").textContent = tr(
      `${content().tracks.length} 轨道 · ${s.session.assets.length} 音频素材`,
      `${content().tracks.length} tracks · ${s.session.assets.length} audio assets`,
    );
  }
  function updateHistoryButtons() {
    $("undo").disabled = !s.session?.can_undo;
    $("redo").disabled = !s.session?.can_redo;
  }
  function renderAssets() {
    $("asset-count").textContent = s.session.assets.length;
    const query = $("asset-search").value.toLowerCase();
    $("asset-list").innerHTML =
      s.session.assets
        .filter((a) => a.name.toLowerCase().includes(query))
        .map(
          (a, i) =>
            `<button class="asset-item" draggable="true" data-asset="${a.id}" style="--color:${colors[i % colors.length]}" title="${tr("点击添加到轨道，或拖入编排区", "Click to add a track, or drag into the arrangement")}"><span class="asset-symbol">${icon("wave")}</span><span><strong>${esc(a.name)}</strong><small>WAV · ${seconds(a.duration).slice(0, 5)}</small></span><span class="asset-add">＋</span></button>`,
        )
        .join("") ||
      `<p class="empty-assets">${tr("音频素材会出现在这里；MIDI 直接加入轨道", "Audio appears here; MIDI goes directly to tracks")}</p>`;
  }
  function renderTracks() {
    const loop = { ...StationTiming.loopDefaults(), ...content().loop },
      bar = beatSeconds() * 4,
      end = Math.max(
        bar * 12,
        loop.enabled ? loop.end * beatSeconds() + bar : 0,
        Math.ceil(duration(content()) / bar + 2) * bar,
      ),
      width = Math.ceil(end * s.zoom);
    $("arrangement-content").style.width = `${width + headWidth()}px`;
    $("arrangement-content").style.setProperty(
      "--bar-width",
      `${bar * s.zoom}px`,
    );
    $("ruler-ticks").innerHTML = Array.from(
      { length: Math.ceil(end / bar) },
      (_, i) => `<span style="left:${i * bar * s.zoom}px">${i + 1}</span>`,
    ).join("");
    if (loop.enabled)
      $("ruler-ticks").insertAdjacentHTML(
        "beforeend",
        `<div class="loop-band" aria-hidden="true" style="left:${loop.start * beatSeconds() * s.zoom}px;width:${(loop.end - loop.start) * beatSeconds() * s.zoom}px"></div>`,
      );
    $("track-list").innerHTML = content()
      .tracks.map(
        (t, i) =>
          `<div class="track ${t.id === s.track ? "selected" : ""}" style="--color:${t.color}" data-track="${t.id}"><div class="track-header"><div class="track-title-row">${icon(t.kind === "midi" ? "keys" : "wave")}<span class="track-name">${esc(t.name)}</span><span class="track-number">${String(i + 1).padStart(2, "0")}</span></div><div class="track-controls"><button class="mini-toggle mute ${t.mute ? "active" : ""}" data-toggle="mute" aria-label="${esc(t.name)} ${tr("静音", "mute")}" aria-pressed="${t.mute}">M</button><button class="mini-toggle ${t.solo ? "active" : ""}" data-toggle="solo" aria-label="${esc(t.name)} ${tr("独奏", "solo")}" aria-pressed="${t.solo}">S</button><input class="track-gain" type="range" min="-60" max="12" step=".5" value="${t.gain_db}" aria-label="${esc(t.name)} ${tr("音量", "level")}" data-level="${t.id}"><button class="track-delete" data-remove-track="${t.id}" aria-label="${tr("删除轨道", "Delete track")} ${esc(t.name)}">×</button></div></div><div class="track-lane" data-lane="${t.id}">${t.clips.map((c) => `<div class="clip ${c.id === s.clip ? "selected" : ""}" tabindex="0" role="button" aria-label="${esc(c.name)} ${tr("片段", "clip")}" data-clip="${c.id}" style="left:${c.start * s.zoom}px;width:${Math.max(12, c.duration * s.zoom)}px"><div class="clip-label">${esc(c.name)}</div><canvas data-wave="${c.id}"></canvas><span class="clip-handle"></span></div>`).join("")}</div></div>`,
      )
      .join("");
    $("empty-guide").hidden = content().tracks.length > 0;
    $("split").disabled = !selectedClip();
    $("duplicate").disabled = !selectedClip();
    $("delete-clip").disabled = !selectedClip();
    fitPanel?.render();
    for (const t of content().tracks) for (const c of t.clips) drawClip(t, c);
    workflowPanel?.render();
  }
  function drawClip(t, c) {
    const canvas = document.querySelector(`[data-wave="${c.id}"]`);
    if (!canvas) return;
    const width = Math.max(12, Math.ceil(c.duration * s.zoom)),
      h = 49,
      dpr = devicePixelRatio || 1;
    // Avoid allocating an enormous bitmap for a long zoomed-in recording.
    canvas.width = Math.min(width, 8192) * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.scale(Math.min(width, 8192) / width, 1);
    ctx.fillStyle = t.color;
    if (t.kind === "audio") {
      const a = asset(c.asset);
      if (!a) return;
      const peak = Math.max(0.01, ...a.waveform);
      for (let x = 0; x < width; x += 3) {
        const time = c.offset + x / s.zoom,
          index = Math.min(
            a.waveform.length - 1,
            Math.floor((time / a.duration) * a.waveform.length),
          );
        const amp = (a.waveform[index] / peak) * 20;
        ctx.fillRect(x, h / 2 - amp, 1.3, Math.max(1, amp * 2));
      }
    } else {
      const pitches = c.notes.map((n) => n.pitch),
        low = Math.min(45, ...pitches),
        high = Math.max(80, ...pitches);
      for (const n of c.notes) {
        const start = n.start * beatSeconds() - c.offset,
          stop = start + n.length * beatSeconds();
        if (stop < 0 || start > c.duration) continue;
        ctx.fillRect(
          Math.max(0, start * s.zoom),
          4 + ((high - n.pitch) / (high - low)) * 35,
          Math.max(
            2,
            (Math.min(stop, c.duration) - Math.max(0, start)) * s.zoom - 1,
          ),
          3,
        );
      }
    }
  }
  function renderMixer() {
    $("mixer").innerHTML =
      content()
        .tracks.map(
          (t) =>
            `<div class="channel ${s.track === t.id ? "selected" : ""}" data-channel="${t.id}" style="--color:${t.color}"><span class="channel-name">${esc(t.name)}</span><input class="channel-pan" type="range" min="-1" max="1" step=".05" value="${t.pan}" data-pan="${t.id}" aria-label="${esc(t.name)} ${tr("声像", "pan")}"><div class="fader-row"><input type="range" min="-60" max="12" step=".5" value="${t.gain_db}" data-level="${t.id}" aria-label="${esc(t.name)} ${tr("推子", "fader")}"><div class="vu"><span data-vu="${t.id}"></span></div></div><span class="channel-db" data-db="${t.id}">${t.gain_db.toFixed(1)} dB</span><button class="channel-fx ${fxActive(t) ? "active" : ""}" data-open-effects="${t.id}" aria-label="${esc(t.name)} ${tr("效果器", "effects")}">FX ${fxActive(t) ? "●" : "+"}</button><div class="channel-buttons"><button class="mini-toggle mute ${t.mute ? "active" : ""}" data-mixer-toggle="mute" data-id="${t.id}" aria-label="${esc(t.name)} ${tr("混音静音", "mixer mute")}" aria-pressed="${t.mute}">M</button><button class="mini-toggle ${t.solo ? "active" : ""}" data-mixer-toggle="solo" data-id="${t.id}" aria-label="${esc(t.name)} ${tr("混音独奏", "mixer solo")}" aria-pressed="${t.solo}">S</button></div></div>`,
        )
        .join("") +
      `<div class="channel master-channel"><span class="channel-name">MASTER</span><span class="channel-db">STEREO OUT</span><div class="fader-row"><input type="range" min="-60" max="6" step=".5" value="${content().master_db}" data-master aria-label="${tr("主输出音量", "Master output")}"><div class="vu"><span id="master-vu"></span></div></div><span class="channel-db" id="master-db">${content().master_db.toFixed(1)} dB</span><button class="channel-fx ${content().limiter?.enabled ? "active" : ""}" data-open-effects="master">${tr("峰值保护", "Peak guard")} ${content().limiter?.enabled ? "●" : "+"}</button></div>`;
  }
  function fxActive(track) {
    const fx = StationEffects.normalize(track.effects);
    return (
      !fx.bypass &&
      (fx.eq.enabled || fx.compressor.enabled || fx.reverb.enabled)
    );
  }
  function fxSlider(label, path, value, min, max, step, suffix = "") {
    return `<label class="fx-control"><span>${label}<output data-fx-output="${path}">${Number(value.toFixed(2))}${suffix}</output></span><input type="range" data-fx-param="${path}" data-suffix="${suffix}" min="${min}" max="${max}" step="${step}" value="${value}" aria-label="${label}"></label>`;
  }
  function renderEffects() {
    const track = selectedTrack(),
      fx = StationEffects.normalize(track?.effects),
      limit = { ...StationEffects.limiterDefaults(), ...content().limiter };
    const enable = (key, title, on) =>
      `<label class="fx-enable"><input type="checkbox" data-fx-enable="${key}" ${on ? "checked" : ""} ${!track && key !== "limiter" ? "disabled" : ""} id="fx-${key}-enabled"><span>${title}</span></label>`;
    $("effects").innerHTML =
      `<div class="fx-toolbar"><div class="fx-target"><span>${tr("轨道效果", "TRACK EFFECTS")}</span><select data-fx-track aria-label="${tr("效果器目标轨道", "Effects target track")}">${!track ? `<option value="">${tr("先创建轨道", "Create a track first")}</option>` : ""}${content()
        .tracks.map(
          (t) =>
            `<option value="${t.id}" ${t.id === track?.id ? "selected" : ""}>${esc(t.name)}</option>`,
        )
        .join(
          "",
        )}</select></div><div class="fx-actions"><select data-fx-preset aria-label="${tr("效果预设", "Effect preset")}" ${track ? "" : "disabled"}><option value="">${tr("选择预设…", "Choose preset…")}</option>${Object.entries(
        StationEffects.presets,
      )
        .map(
          ([key, p]) =>
            `<option value="${key}">${p.title[s.lang === "zh" ? 0 : 1]}</option>`,
        )
        .join(
          "",
        )}</select><button data-fx-bypass aria-pressed="${fx.bypass}" class="${fx.bypass ? "active" : ""}" ${track ? "" : "disabled"}>${fx.bypass ? tr("原声 · 旁路中", "Dry · bypassed") : tr("A/B 原声", "A/B dry")}</button><button data-fx-reset ${track ? "" : "disabled"}>${tr("重置", "Reset")}</button></div></div>
      <div class="fx-cards ${!track ? "fx-no-track" : ""}">
        <section class="fx-card ${fx.eq.enabled ? "enabled" : ""}"><header>${enable("eq", tr("三段均衡", "3-band EQ"), fx.eq.enabled)}<small>01 / TONE</small></header><fieldset ${!track ? "disabled" : ""}>
          ${fxSlider(tr("低频 · 150 Hz", "Low · 150 Hz"), "eq.low_db", fx.eq.low_db, -12, 12, 0.5, " dB")}
          ${fxSlider(tr("中频 · 1 kHz", "Mid · 1 kHz"), "eq.mid_db", fx.eq.mid_db, -12, 12, 0.5, " dB")}
          ${fxSlider(tr("高频 · 4 kHz", "High · 4 kHz"), "eq.high_db", fx.eq.high_db, -12, 12, 0.5, " dB")}
        </fieldset></section>
        <section class="fx-card ${fx.compressor.enabled ? "enabled" : ""}"><header>${enable("compressor", tr("压缩器", "Compressor"), fx.compressor.enabled)}<small>02 / DYNAMICS</small></header><fieldset ${!track ? "disabled" : ""}>
          ${fxSlider(tr("阈值", "Threshold"), "compressor.threshold_db", fx.compressor.threshold_db, -48, 0, 1, " dB")}
          ${fxSlider(tr("压缩比", "Ratio"), "compressor.ratio", fx.compressor.ratio, 1, 12, 0.5, ":1")}
          <details class="fx-advanced"><summary>${tr("起音、释放与补偿", "Attack, release & makeup")}</summary>
          ${fxSlider(tr("起音", "Attack"), "compressor.attack_ms", fx.compressor.attack_ms, 1, 100, 1, " ms")}
          ${fxSlider(tr("释放", "Release"), "compressor.release_ms", fx.compressor.release_ms, 20, 1000, 10, " ms")}
          ${fxSlider(tr("补偿增益", "Makeup"), "compressor.makeup_db", fx.compressor.makeup_db, 0, 12, 0.5, " dB")}</details>
          <div class="fx-readout">${tr("增益衰减", "Gain reduction")}<output id="fx-compression">0.0 dB</output></div>
        </fieldset></section>
        <section class="fx-card ${fx.reverb.enabled ? "enabled" : ""}"><header>${enable("reverb", tr("混响", "Reverb"), fx.reverb.enabled)}<small>03 / SPACE</small></header><fieldset ${!track ? "disabled" : ""}>
          ${fxSlider(tr("湿声比例", "Wet mix"), "reverb.mix", fx.reverb.mix, 0, 0.5, 0.01)}
          ${fxSlider(tr("衰减时间", "Decay"), "reverb.decay", fx.reverb.decay, 0.2, 3, 0.1, " s")}
          <p>${tr("让声音进入同一个空间。播放与 WAV 导出都会保留尾音。", "Put sounds in a shared space. Playback and WAV export include the tail.")}</p>
        </fieldset></section>
        <section class="fx-card fx-master ${limit.enabled ? "enabled" : ""}"><header>${enable("limiter", tr("主输出限制", "Output limiter"), limit.enabled)}<small>MASTER</small></header>
          ${fxSlider(tr("峰值上限", "Peak ceiling"), "limiter.ceiling_db", limit.ceiling_db, -12, -0.1, 0.1, " dBFS")}
          ${fxSlider(tr("释放", "Release"), "limiter.release_ms", limit.release_ms, 20, 500, 10, " ms")}
          <div class="fx-readout">${tr("增益衰减", "Gain reduction")}<output id="fx-limiting">0.0 dB</output></div>
          <div id="fx-output-peak" class="fx-readout">${tr("输出峰值", "Output peak")} · −∞ dBFS</div>
          <p>${tr("立体声联动采样峰值限制。不是 True Peak；过度限制会改变音色。", "Stereo-linked sample-peak limiting. Not true peak; heavy limiting changes the sound.")}</p>
        </section>
      </div><div class="fx-footnote">${fx.bypass ? tr("轨道效果已旁路 · 主输出限制独立生效", "Track bypassed · output limiter stays independent") : tr("EQ → 压缩 → 混响 → 推子 / 声像 → 主输出", "EQ → compression → reverb → fader / pan → master")}<span>${tr("实时试听 · 自动保存 · 可撤销", "Live audition · autosave · undo")}</span></div>`;
  }
  const field = (label, key, value, attrs = "") =>
    `<label class="field-row"><span>${label}</span><input type="number" data-field="${key}" value="${Number(value.toFixed(6))}" ${attrs.replace(/step="[^"]+"/, 'step="any"')}></label>`;
  function renderInspector() {
    workflowPanel?.render();
    const t = selectedTrack(),
      c = selectedClip();
    if (!t) {
      $("inspector-content").innerHTML =
        `<div class="selection-tag">SESSION</div><div class="selection-name">${esc(content().title)}</div><div class="selection-subtitle">${tr("本地音乐工程", "Local music project")}</div><div class="inspector-section"><h3>${tr("开始制作", "MAKE SOMETHING")}</h3><p>${tr("导入音频创建轨道，或从乐器页开始写旋律。所有操作会自动保存在本机。", "Import audio to create a track, or choose an instrument and write notes. Changes are saved locally.")}</p></div>`;
      return;
    }
    $("inspector-content").innerHTML =
      `<div class="selection-tag" style="--color:${t.color}">● ${t.kind === "midi" ? "INSTRUMENT" : "AUDIO"} ${c ? "CLIP" : "TRACK"}</div><div class="selection-name">${esc(c?.name || t.name)}</div><div class="selection-subtitle">${c ? seconds(c.duration) + " · " : ""}${tr("可撤销编辑", "Reversible edits")}</div><section class="inspector-section"><h3>${tr("轨道设置", "TRACK")}</h3><label class="field-row"><span>${tr("名称", "Name")}</span><input type="text" data-track-name value="${esc(t.name)}" maxlength="150"></label>${field(tr("音量 · dB", "Level · dB"), "track.gain_db", t.gain_db, 'min="-60" max="12" step=".5"')}${field(tr("声像 · L / R", "Pan · L / R"), "track.pan", t.pan, 'min="-1" max="1" step=".05"')}${
        t.kind === "midi"
          ? `<label class="field-row"><span>${tr("音色", "Sound")}</span><select data-instrument>${instrumentIds()
              .map(
                (k) =>
                  `<option value="${k}" ${t.instrument === k ? "selected" : ""}>${instrumentName(k)}</option>`,
              )
              .join("")}</select></label>`
          : ""
      }</section>${c ? `<section class="inspector-section"><h3>${tr("片段位置 · 秒", "CLIP POSITION · SECONDS")}</h3>${field(tr("开始位置", "Start"), "clip.start", c.start, 'min="0" max="599" step=".1"')}${field(tr("素材起点", "Source offset"), "clip.offset", c.offset, 'min="0" max="599" step=".1"')}${field(tr("片段长度", "Duration"), "clip.duration", c.duration, 'min=".01" max="600" step=".1"')}${field(tr("片段增益 · dB", "Clip gain · dB"), "clip.gain_db", c.gain_db, 'min="-60" max="12" step=".5"')}</section><section class="inspector-section"><h3>${tr("淡入与淡出 · 秒", "FADES · SECONDS")}</h3>${field(tr("淡入", "Fade in"), "clip.fade_in", c.fade_in, 'min="0" max="30" step=".05"')}${field(tr("淡出", "Fade out"), "clip.fade_out", c.fade_out, 'min="0" max="30" step=".05"')}</section><div class="inspector-buttons"><button data-inspect-duplicate>${tr("复制片段", "Duplicate")}</button><button data-inspect-remove>${tr("移除片段", "Remove")}</button></div>` : ""}<section class="inspector-section"><h3>${tr("制作提示", "TIP")}</h3><p>${tr(t.kind === "midi" ? "双击片段打开钢琴卷帘。双击网格添加音符，双击音符移除。" : "拖动片段改变位置；拖动右侧边缘改变长度。M 静音，S 独奏。", t.kind === "midi" ? "Double-click the clip to open the piano roll. Double-click the grid to add a note or a note to remove it." : "Drag a clip to move it. Drag its right edge to trim. M mutes; S solos.")}</p></section>`;
    if (c?.origin)
      $("inspector-content").insertAdjacentHTML(
        "beforeend",
        `<section class="inspector-section source-credit"><h3>${tr("素材来源", "SOURCE")}</h3><strong>${esc(c.origin.title)}</strong><p>${esc(c.origin.author)}</p><small>${esc(c.origin.license)}</small></section>`,
      );
    const note =
      t.kind === "midi" && c?.id === s.noteClip ? c.notes[s.noteIndex] : null;
    if (note)
      $("inspector-content").insertAdjacentHTML(
        "beforeend",
        `<section class="inspector-section"><h3>${tr("选中音符", "SELECTED NOTE")}</h3>${field(tr("音高 · MIDI", "Pitch · MIDI"), "note.pitch", note.pitch, 'min="0" max="127" step="1"')}${field(tr("开始 · 拍", "Start · beats"), "note.start", note.start, 'min="0" max="3000" step=".25"')}${field(tr("时长 · 拍", "Length · beats"), "note.length", note.length, 'min=".001" max="3000" step=".25"')}${field(tr("力度", "Velocity"), "note.velocity", note.velocity, 'min="1" max="127" step="1"')}</section>`,
      );
    workflowPanel?.enhanceInspector();
    envelopePanel?.render();
  }
  const instrumentName = (k) =>
    s.library?.instruments.find((i) => i.id === k)?.title[
      s.lang === "zh" ? 0 : 1
    ] ||
    {
      keys: tr("柔和键盘", "Velvet keys"),
      bass: tr("温暖贝斯", "Warm bass"),
      pad: tr("空气铺底", "Air pad"),
    }[k];
  const instrumentIds = () => [
    ...(s.library?.instruments.map((i) => i.id) || []),
    "keys",
    "bass",
    "pad",
  ];
  function renderInstruments() {
    $("instrument-list").innerHTML = instrumentIds()
      .map(
        (k) =>
          `<div class="instrument-row"><button class="instrument-card" data-add-instrument="${k}">${icon("keys")}<span><strong>${instrumentName(k)}</strong><small>${k.startsWith("vcsl-") ? "VCSL · SAMPLED · CC0" : "BUILT-IN SYNTH"}</small></span><span>＋</span></button><button class="library-preview ${previewKey === k ? "active" : ""}" data-preview-instrument="${k}" aria-label="${tr("试听", "Audition")} ${esc(instrumentName(k))}">${previewKey === k ? "■" : "▶"}</button></div>`,
      )
      .join("");
  }
  const styleName = (style) =>
    ({
      pop: "流行",
      rock: "摇滚",
      funk: "放克",
      hiphop: "嘻哈",
      soul: "灵魂",
      jazz: "爵士",
      latin: "拉丁",
      afrobeat: "非洲节拍",
    })[style];
  function renderGrooves() {
    const query = $("asset-search").value.trim().toLowerCase();
    $("groove-list").innerHTML = (s.library?.patterns || [])
      .filter((p) =>
        `${p.style} ${p.bpm} ${styleName(p.style)}`
          .toLowerCase()
          .includes(query),
      )
      .map(
        (p) =>
          `<div class="groove-card" draggable="true" data-pattern="${p.id}"><button class="library-preview ${previewKey === p.id ? "active" : ""}" data-preview-groove="${p.id}" aria-label="${tr("试听", "Audition")} ${p.style}">${previewKey === p.id ? "■" : "▶"}</button><span><strong>${tr(styleName(p.style), p.style[0].toUpperCase() + p.style.slice(1))}</strong><small>${p.bpm} BPM · ${tr("2 小节", "2 bars")}</small></span><button class="groove-add" data-add-groove="${p.id}" title="${tr("跟随工程速度加入", "Add at session tempo")}">＋</button></div>`,
      )
      .join("");
  }
  function stopPreview() {
    fitPanel?.stop();
    auditionPanel?.stop();
    previewEngine.pause();
    generationAudio.pause();
    clearTimeout(previewTimer);
    previewKey = null;
    renderGrooves();
    renderInstruments();
    if (s.session) renderTasks();
  }
  async function audition(key, instrument, notes, bpm, beats) {
    if (previewKey === key) return stopPreview();
    stopPreview();
    pause();
    previewKey = key;
    renderGrooves();
    renderInstruments();
    const length = (beats * 60) / bpm,
      track = newTrack("midi", instrument);
    track.clips = [
      {
        id: uid(),
        offset: 0,
        start: 0,
        duration: length,
        gain_db: 0,
        fade_in: 0,
        fade_out: 0.04,
        notes,
      },
    ];
    try {
      const ok = await previewEngine.play(
        { bpm, master_db: -6, tracks: [track] },
        [],
        "factory",
        0,
      );
      if (ok && previewKey === key)
        previewTimer = setTimeout(stopPreview, (length + 0.1) * 1000);
    } catch (e) {
      stopPreview();
      throw e;
    }
  }
  async function addGroove(id, at = s.position) {
    document.body.classList.remove("library-open");
    stopPreview();
    pause();
    await flush();
    accept(
      await request(base() + "/patterns", {
        revision: s.session.revision,
        pattern: id,
        at: snap(at),
      }),
      { selectLast: true },
    );
    dock("piano");
    toast(
      tr(
        "鼓点已加入，跟随工程速度；可以编辑音符和力度",
        "Groove added at session tempo; edit notes and velocity",
      ),
    );
  }
  async function chooseMidi(file) {
    const form = new FormData();
    form.append("file", file);
    const meta = await request("/api/workstation/midi/inspect", form);
    pendingMidi = file;
    const warnings = {
      tempo_map: tr(
        "包含速度变化：将保留演奏时间，转换为当前网格的音符位置。",
        "Tempo changes will be flattened while preserving performance timing.",
      ),
      time_signature: tr(
        "包含非 4/4 拍号：原音符时间保留，工程显示为 4/4 网格。",
        "Non-4/4 meter: original note times are kept on a 4/4 display grid.",
      ),
      instrument_mapping: tr(
        "部分乐器将近似映射到钢琴、马林巴或贝斯。",
        "Some instruments will be approximated by piano, marimba or bass.",
      ),
      unclosed_notes: tr(
        "未关闭的音符将于文件末尾结束。",
        "Unclosed notes will end at the end of the file.",
      ),
      drum_mapping: tr(
        "少量未覆盖的打击乐音色将由闭镲近似代替，原音符保留。",
        "Unmapped percussion will use a closed-hat approximation; original notes are kept.",
      ),
    };
    $("midi-info").innerHTML =
      `<strong>${esc(file.name)}</strong><p>${meta.track_count} ${tr("声部", "parts")} · ${meta.note_count} ${tr("音符", "notes")} · ${seconds(meta.duration)} · ${Number(meta.bpm.toFixed(2))} BPM</p>${meta.warnings.map((w) => `<p class="import-warning">${esc(warnings[w] || w)}</p>`).join("")}`;
    $("midi-source-tempo").disabled =
      !!content().tracks.length || meta.bpm < 30 || meta.bpm > 300;
    $("midi-source-tempo").checked = !$("midi-source-tempo").disabled;
    $("midi-dialog").showModal();
    return new Promise((resolve) =>
      $("midi-dialog").addEventListener(
        "close",
        () => {
          pendingMidi = null;
          resolve();
        },
        { once: true },
      ),
    );
  }
  function view(name, reveal = false) {
    if (reveal) {
      document.body.classList.add("library-open");
      document.body.classList.remove("inspector-open");
    }
    s.view = name;
    document
      .querySelectorAll("[data-view]")
      .forEach((b) => b.classList.toggle("active", b.dataset.view === name));
    for (const key of ["assets", "instruments", "models"])
      $(key + "-view").hidden = key !== name;
    $("browser-title").textContent = {
      assets: tr("声音素材", "Sound library"),
      instruments: tr("乐器与音色", "Instruments"),
      models: tr("本地 AI 模型", "Local AI models"),
    }[name];
    if (name === "models") loadModels();
  }
  function dock(name) {
    s.dock = name;
    document.body.classList.toggle("piano-open", name === "piano");
    document.body.classList.toggle("effects-open", name === "effects");
    if (name === "effects") renderEffects();
    for (const key of ["mixer", "effects", "piano", "tasks"]) {
      $(key).hidden = key !== name;
      $(key + "-tab").classList.toggle("active", key === name);
    }
    if (name === "piano") {
      renderPiano();
      $("piano").scrollTop = 100;
    }
    if (name === "tasks") pollTasks();
  }
  function newTrack(kind = "audio", instrument = "keys") {
    const t = {
      id: uid(),
      name:
        kind === "midi"
          ? instrumentName(instrument)
          : tr("音频轨道", "Audio track"),
      kind,
      color: colors[content().tracks.length % colors.length],
      gain_db: 0,
      pan: 0,
      mute: false,
      solo: false,
      instrument,
      clips: [],
    };
    if (kind === "midi")
      t.clips = [
        {
          id: uid(),
          name: t.name,
          asset: null,
          start: snap(s.position),
          offset: 0,
          duration: beatSeconds() * 16,
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
          notes: [],
        },
      ];
    return t;
  }
  function addTrack(kind = "audio", instrument = "keys") {
    document.body.classList.remove("library-open");
    if (content().tracks.length >= 32)
      throw Error(
        tr("当前最多支持 32 条轨道", "This preview supports 32 tracks"),
      );
    mutate(() => {
      const t = newTrack(kind, instrument);
      content().tracks.push(t);
      s.track = t.id;
      s.clip = t.clips[0]?.id;
    });
    if (kind === "midi") dock("piano");
  }
  function addAsset(id, trackId, at = 0) {
    const a = asset(id);
    if (!a) return;
    mutate(() => {
      let t = content().tracks.find(
        (x) => x.id === trackId && x.kind === "audio",
      );
      if (!t) {
        t = newTrack();
        content().tracks.push(t);
        t.name = a.name;
      }
      const c = {
        id: uid(),
        name: a.name,
        asset: id,
        start: Math.min(snap(at), 600 - a.duration),
        offset: 0,
        duration: a.duration,
        gain_db: 0,
        fade_in: 0,
        fade_out: 0,
        notes: [],
      };
      t.clips.push(c);
      s.track = t.id;
      s.clip = c.id;
    });
  }
  function duplicate() {
    const t = selectedTrack(),
      c = selectedClip();
    if (!c) return;
    const copy = structuredClone(c);
    copy.id = uid();
    copy.start = c.start + c.duration;
    if (copy.start + copy.duration > 600)
      throw Error(tr("超过 10 分钟工程限制", "Session limit is 10 minutes"));
    mutate(() => {
      t.clips.push(copy);
      s.clip = copy.id;
    });
  }
  function removeClip() {
    const t = selectedTrack();
    if (!t || !s.clip) return;
    mutate(() => {
      t.clips = t.clips.filter((c) => c.id !== s.clip);
      s.clip = null;
    });
  }
  function toggle(t, key) {
    mutate(() => (t[key] = !t[key]), { live: true });
  }
  async function importFiles(files) {
    pause();
    await flush();
    try {
      for (const file of files) {
        if (/\.midi?$/i.test(file.name)) {
          await chooseMidi(file);
          continue;
        }
        $("audio-status").textContent = tr("正在导入…", "Importing…");
        const form = new FormData();
        form.append("file", file);
        accept(
          await request(
            base() + `/import?revision=${s.session.revision}`,
            form,
          ),
          { selectLast: true },
        );
      }
    } finally {
      $("audio-status").textContent = tr("准备就绪", "Ready");
    }
    toast(tr("导入操作完成", "Import complete"));
  }
  async function play() {
    const tutorialProject = s.session.id;
    stopPreview();
    if (engine.playing || starting) {
      pause();
      return;
    }
    if (!duration(content()) && !content().metronome?.enabled)
      return toast(
        tr("先添加音频或 MIDI 片段", "Add an audio or MIDI clip first"),
      );
    starting = true;
    $("audio-status").textContent = tr("准备音频…", "Preparing audio…");
    try {
      s.position = StationTiming.range(
        content(),
        duration(content()),
        s.position,
      ).at;
      const ok = await engine.play(
        content(),
        s.session.assets,
        s.session.id,
        s.position,
      );
      if (ok) {
        tutorialPanel?.observe("listen", tutorialProject);
        s.position = engine.position;
        $("play").textContent = "Ⅱ";
        $("audio-status").textContent = tr("正在播放", "Playing");
      }
    } catch (error) {
      engine.pause();
      throw error;
    } finally {
      starting = false;
      if (!engine.playing)
        $("audio-status").textContent = tr("准备就绪", "Ready");
    }
  }
  function seek(at) {
    const was = engine.playing;
    pause();
    const end = StationTiming.range(content(), duration(content())).end;
    s.position = Math.max(0, Math.min(at, end || at));
    engine.position = s.position;
    if (was) guarded(play)();
  }
  function renderPiano() {
    const t = selectedTrack(),
      c = selectedClip();
    if (t?.kind !== "midi" || !c) {
      $("piano").innerHTML =
        `<div class="piano-message">${tr("选择一个乐器片段编辑音符，或在左侧添加乐器轨道。", "Select an instrument clip to edit notes, or add an instrument track.")}</div>`;
      return;
    }
    const beatWidth = Math.max(30, beatSeconds() * s.zoom),
      beats = Math.max(16, (c.offset + c.duration) / beatSeconds()),
      low = Math.max(
        0,
        Math.min(
          t.instrument === "vcsl-drums" ? 35 : 48,
          ...c.notes.map((n) => n.pitch),
        ),
      ),
      high = Math.min(
        127,
        Math.max(
          t.instrument === "vcsl-drums" ? 59 : 84,
          ...c.notes.map((n) => n.pitch),
        ),
      );
    const keys = Array.from({ length: high - low + 1 }, (_, i) => {
      const pitch = high - i,
        black = [1, 3, 6, 8, 10].includes(pitch % 12),
        drum =
          t.instrument === "vcsl-drums"
            ? {
                35: tr("底鼓", "Kick"),
                36: tr("底鼓", "Kick"),
                37: tr("边击", "Rim"),
                38: tr("军鼓", "Snare"),
                39: tr("拍手", "Clap"),
                40: tr("军鼓", "Snare"),
                41: tr("通鼓", "Tom"),
                42: tr("闭镲", "Hat"),
                43: tr("通鼓", "Tom"),
                44: tr("闭镲", "Hat"),
                45: tr("通鼓", "Tom"),
                46: tr("开镲", "Open"),
                47: tr("通鼓", "Tom"),
                48: tr("通鼓", "Tom"),
                49: tr("吊镲", "Crash"),
                50: tr("通鼓", "Tom"),
                51: tr("叮镲", "Ride"),
                52: tr("吊镲", "Crash"),
                55: tr("吊镲", "Crash"),
                57: tr("吊镲", "Crash"),
                59: tr("叮镲", "Ride"),
              }[pitch]
            : null,
        label =
          drum || (pitch % 12 === 0 ? "C" + (Math.floor(pitch / 12) - 1) : "");
      return `<button class="piano-key ${black ? "black" : ""}" aria-label="${drum || "MIDI " + pitch}" title="MIDI ${pitch}" data-note-key="${pitch}" style="top:${i * 14}px">${label}</button>`;
    }).join("");
    $("piano").innerHTML =
      `<div class="piano-grid" style="width:${beats * beatWidth}px;height:${(high - low + 1) * 14}px;--note-step:${beatWidth / 4}px" data-beat-width="${beatWidth}" data-high="${high}" data-low="${low}">${keys}${c.notes.map((n, i) => `<button class="piano-note" data-note="${i}" aria-label="MIDI ${n.pitch}, ${n.start.toFixed(2)} beats" title="${tr("双击删除", "Double-click to remove")}" style="left:${n.start * beatWidth}px;top:${(high - n.pitch) * 14 + 1}px;width:${Math.max(4, n.length * beatWidth - 2)}px"></button>`).join("")}</div>`;
    workflowPanel?.enhancePiano();
  }
  async function loadModels() {
    try {
      [s.models, s.generationHealth] = await Promise.all([
        request("/api/studio/models"),
        request("/api/workstation/generation/status"),
      ]);
      renderModels();
      renderGenerationHealth();
    } catch (e) {
      toast(e.message, true);
    }
  }
  function renderGenerationHealth() {
    const health = s.generationHealth;
    $("generation-submit").disabled =
      !health?.available || generationSubmitting;
    $("generation-health").textContent = health?.available
      ? tr(
          "本地环境已配置 · 生成结果保留为草稿",
          "Local runtime configured · results stay as drafts",
        )
      : health
        ? tr(
            "本地 AI 生成尚未配置。可先用乐器和录音创作，或返回首页查看 AI 准备说明。",
            "Local AI generation is not configured. Start with instruments or recording, or see AI setup on Home.",
          )
        : tr(
            "打开模型面板以检查本地环境",
            "Open Models to check the local runtime",
          );
    if (health?.available) {
      const profile = health.hardware?.recommended;
      $("generation-health").textContent += profile
        ? ` · ${tr("自动建议：", "Auto recommendation: ")}${profile.gpu.name} · ${profile.id} · ${profile.quantization ? "DiT INT8" : "BF16"}`
        : " · " + tr("生成前会检查显存和兼容性", "VRAM and compatibility checked before generation");
    }
    $("generation-health").title = health?.message || "";
    $("generation-bpm").textContent = s.session ? `${content().bpm} BPM` : "";
  }
  function renderGenerationTasks() {
    return s.generations
      .map((t) => {
        const pending = [
            "queued",
            "checking",
            "running",
            "cancelling",
          ].includes(t.status),
          playing = previewKey === "generation:" + t.id,
          status =
            {
              queued: tr("等待运行", "Queued"),
              checking: tr("检查环境", "Checking"),
              running: tr("正在生成", "Generating"),
              cancelling: tr("正在取消", "Cancelling"),
              cancelled: tr("已取消", "Cancelled"),
              interrupted: tr(
                "运行中断，可调整后重试",
                "Interrupted; adjust and retry",
              ),
              complete: tr("草稿已就绪", "Draft ready"),
              failed: tr(
                "生成失败，请查看诊断",
                "Generation failed; view diagnostics",
              ),
            }[t.status] || t.status,
          detail = t.error
            ? status
            : t.progress?.message
              ? `${status} · ${t.progress.message}`
              : status,
          url = `${base()}/generations/${t.id}`;
        return `<div class="task-row generation-task"><span><strong>✦ ${esc(t.model)} · ${t.parameters.duration}s</strong><small>${esc(t.user_prompt || t.parameters.prompt)}</small>${t.composition_context ? `<small>${tr("蓝图", "Blueprint")} r${t.composition_context.revision} · ${esc(t.composition_context.section?.name || tr("整首", "Whole piece"))}</small>` : ""}<small>${esc(detail)}</small>${t.metrics ? `<small>${t.metrics.total_seconds}s · ${t.metrics.peak_allocated_mib} MiB · Seed ${t.parameters.seed}</small>` : ""}</span>${t.status === "complete" ? `<button data-preview-generation="${t.id}">${playing ? "■ " + tr("停止", "Stop") : "▶ " + tr("试听", "Audition")}</button><button data-adopt-generation="${t.id}">${tr("加入播放头", "Add at playhead")}</button>${t.parameters.mode === "repaint" ? `<button data-adopt-generation="${t.id}" data-replace-source>${tr("采用重绘 · 可撤销", "Apply repaint · undoable")}</button>` : ""}${t.composition_context?.section ? `<button data-adopt-section-generation="${t.id}" title="${tr("放在原段落起点，保留素材全长；可继续裁剪", "Place at the original section start, retaining the full clip; trim afterward")}">${tr("加入段落起点", "Add at section start")}</button>` : ""}<a class="task-artifact" href="${url}/audio" download="ace-step-${t.id}.wav">WAV ↧</a>` : pending ? `<button data-cancel-generation="${t.id}">${tr("取消", "Cancel")}</button>` : ""}<button data-info-generation="${t.id}">${tr("参数与诊断", "Details")}</button></div>`;
      })
      .join("");
  }
  async function auditionGeneration(id) {
    const key = "generation:" + id;
    if (previewKey === key) return stopPreview();
    stopPreview();
    pause();
    previewKey = key;
    if (generationAudioKey !== id) {
      generationAudio.src = `${base()}/generations/${id}/audio`;
      generationAudioKey = id;
    }
    generationAudio.currentTime = 0;
    renderTasks();
    try {
      await generationAudio.play();
    } catch (error) {
      stopPreview();
      throw error;
    }
  }
  generationAudio.onended = () => {
    stopPreview();
    renderTasks();
  };
  async function auditionTask(project, id) {
    const key = "task:" + id;
    if (previewKey === key) return stopPreview();
    stopPreview();
    pause();
    previewKey = key;
    if (generationAudioKey !== key) {
      generationAudio.src = `/api/projects/${project}/studio/artifacts/${id}`;
      generationAudioKey = key;
    }
    const task = s.tasks.find((t) => t.artifacts.some((a) => a.id === id));
    generationAudio.currentTime = task?.source_clip?.offset || 0;
    renderTasks();
    try {
      await generationAudio.play();
    } catch (error) {
      stopPreview();
      throw error;
    }
    if (task?.source_clip)
      previewTimer = setTimeout(stopPreview, task.source_clip.duration * 1000);
  }
  const modelOptions = {};
  function renderModels() {
    for (const card of $("model-list").querySelectorAll("[data-model-card]")) {
      try { modelOptions[card.dataset.modelCard] = StationModelControls.read(card); } catch { /* Keep last valid values. */ }
    }
    $("model-list").innerHTML = s.models
      .map(
        (m) =>
          `<div class="model-card" data-model-card="${esc(m.id)}"><strong>${esc(m.title[s.lang === "zh" ? 0 : 1])}</strong><small>${esc(m.description[s.lang === "zh" ? 0 : 1])}</small>${m.id === "mel-band-roformer-kj" && !m.runnable ? `<details class="model-setup"><summary>${tr("安装与诊断", "Setup and diagnostics")}</summary><p>${tr("首次使用需安装独立环境与约 913 MB 权重；启动和推理不自动下载。", "First use requires a separate runtime and ~913 MB weights. Startup and inference never download.")}</p><code>python scripts/setup_separation.py</code>${m.health.error ? `<p>${esc(m.health.error)}</p>` : ""}</details>` : ""}${StationModelControls.controls(m, modelOptions[m.id], s.lang)}<small>${m.execution_device === "cuda" ? tr("自动模式默认：NVIDIA GPU", "Automatic defaults to NVIDIA GPU") : m.execution_device === "cpu" ? (m.device === "cpu" ? tr("使用 CPU", "Runs on CPU") : tr("自动模式默认：CPU", "Automatic defaults to CPU")) : tr("检查后显示实际运行设备", "Check to see the runtime device")}${m.stage === "melody" ? tr(" · 请使用独唱、哼唱或单音乐器，CPU 提取可能较慢。", " · Use solo singing, humming or a monophonic instrument. CPU extraction can be slow.") : ""}</small>${m.setup_url && !m.runnable ? `<a class="model-setup-link" href="${esc(m.setup_url)}">${tr("安装此工具 →", "Set up this tool →")}</a>` : ""}<div class="model-actions"><span>${esc(({verified: tr("已验证", "Verified"), unchecked: tr("待检查", "Not checked"), missing: tr("缺少组件", "Missing components"), failed: tr("检查失败", "Check failed")})[m.health.state] || m.health.state)} · ${m.health.weights ? tr("权重已缓存", "weights cached") : tr("权重待检查", "check weights")}</span><button data-check-model="${m.id}">${tr("检查", "Check")}</button><button data-run-model="${m.id}" ${m.runnable ? "" : "disabled"}>${tr("运行", "Run")}</button></div></div>`,
      )
      .join("");
  }
  async function pollTasks() {
    if (!s.session || polling) return;
    polling = true;
    const key = s.session.id;
    try {
      const projects = [
        ...new Set(s.session.assets.map((a) => a.source_project)),
      ];
      const [rows, generations, processing] = await Promise.all([
        Promise.all(
          projects.map(async (p) =>
            (await request(`/api/projects/${p}/studio/tasks`)).map((t) => ({
              ...t,
              source_project: p,
            })),
          ),
        ),
        request(base() + "/generations"),
        request(base() + "/processing"),
      ]);
      if (s.session.id !== key) return;
      const linked = new Map(processing.map((t) => [t.id, t]));
      s.tasks = [
        ...new Map(
          [...rows.flat(), ...processing].map((t) => [
            t.id,
            { ...t, source_clip: linked.get(t.id)?.source_clip },
          ]),
        ).values(),
      ].sort((a, b) => b.created_at - a.created_at);
      s.generations = generations;
      renderTasks();
    } catch (e) {
      console.warn(e.message);
    } finally {
      polling = false;
    }
  }
  function taskLabel(value) {
    const labels = {
      queued: ["排队中", "Queued"],
      checking: ["检查环境", "Checking runtime"],
      running: ["正在处理", "Processing"],
      cancelling: ["正在取消", "Cancelling"],
      cancelled: ["已取消", "Cancelled"],
      interrupted: ["已中断", "Interrupted"],
      complete: ["已完成", "Complete"],
      failed: ["失败", "Failed"],
      vocals: ["人声", "Vocals"],
      instrumental: ["伴奏", "Backing"],
      "separation-report": ["处理报告", "Separation report"],
    };
    return labels[value] ? tr(...labels[value]) : value;
  }
  function canReplaceStems(task) {
    const clips = s.session?.content?.tracks?.flatMap((t) => t.clips) || [];
    const clip = clips.find((c) => c.id === task.source_clip?.id);
    return (
      clip &&
      JSON.stringify(clip) === JSON.stringify(task.source_clip) &&
      (!task.fit || task.fit.project_bpm === content().bpm)
    );
  }
  function renderTasks() {
    $("task-count").textContent = [...s.tasks, ...s.generations].filter((t) =>
      ["queued", "checking", "running", "cancelling"].includes(t.status),
    ).length;
    $("tasks").innerHTML =
      renderGenerationTasks() +
        s.tasks
          .map(
            (t) =>
              `<div class="task-row"><span><strong>${esc(t.model)}</strong><small>${esc(t.error || taskLabel(t.status))}</small>${t.metrics ? `<small>${esc(t.metrics.device.toUpperCase())} · ${t.metrics.seconds.toFixed(1)}s${t.metrics.realtime_factor == null ? "" : " · " + t.metrics.realtime_factor.toFixed(2) + "× " + tr("音频时长", "audio duration")}</small>` : ""}${t.source_clip ? `<small>${esc(t.source_clip.name)} · ${t.source_clip.start.toFixed(2)}s · ${tr("完整素材处理，采用时保留片段范围", "Full source processed; clip bounds retained on adoption")}</small>` : ""}</span>${t.status === "complete" && ["separate", "transform"].includes(t.stage) && t.source_clip ? `<button data-adopt-stems="${t.id}" ${canReplaceStems(t) ? "" : "disabled"} title="${tr("源片段更改或移除后，需要先撤销再替换", "Undo source clip changes or removal before replacing")}">${t.stage === "transform" ? tr("采用适配结果", "Adopt fitted result") : tr("用分轨替换片段", "Replace clip with stems")}</button>` : ""}${t.status === "complete" && t.stage === "melody" && t.source_clip ? `<button data-adopt-melody="${t.id}">${tr("旋律加入乐器轨", "Add melody as notes")}</button>` : ""}${
                t.artifacts
                  .map((a) =>
                    a.kind === "audio"
                      ? `<button data-preview-task="${a.id}" data-project="${t.source_project}">${previewKey === "task:" + a.id ? "■" : "▶"} ${esc(taskLabel(a.role))}</button><button data-attach-task="${a.id}" data-project="${t.source_project}">${esc(taskLabel(a.role))} · ${tr("加入工程", "Add track")}</button>`
                      : `${a.role === "musical-analysis" ? `<button data-musical-report="${a.id}" data-project="${t.source_project}">${tr("查看素材分析", "View analysis")}</button>` : ""}<a class="task-artifact" href="/api/projects/${t.source_project}/studio/artifacts/${a.id}?download=true" download>${esc(taskLabel(a.role))} ↧</a>`,
                  )
                  .join("") ||
                `<span class="task-state">${esc(t.status)}</span>`
              }${["queued", "checking", "running", "cancelling"].includes(t.status) ? `<button data-cancel-task="${t.id}" data-project="${t.source_project}">${tr("取消", "Cancel")}</button>` : `<a class="task-artifact" href="/next.html?project=${t.source_project}" target="_blank" rel="noopener">${tr("详细结果与编辑 ↗", "Details and editing ↗")}</a>`}</div>`,
          )
          .join("") ||
      `<p class="panel-copy">${tr("暂无任务。在 AI 模型面板生成音乐，或选中音频片段运行处理。", "No tasks yet. Generate music in Models, or select audio to process it.")}</p>`;
  }
  async function projectDialog() {
    await flush();
    const [active, deleted] = await Promise.all([
      request("/api/workstation/projects"),
      request("/api/workstation/projects?deleted=true"),
    ]);
    $("project-list").innerHTML =
      active
        .map(
          (p) =>
            `<div class="project-row"><button data-open-session="${p.id}">${esc(p.content.title)}<small>${p.content.tracks.length} ${tr("轨道", "tracks")} · ${new Date(p.updated * 1000).toLocaleString()}</small></button><button data-trash-session="${p.id}" data-revision="${p.revision}">${tr("移入回收站", "Trash")}</button></div>`,
        )
        .join("") +
      (deleted.length
        ? `<p class="section-caption" style="margin-top:25px">${tr("回收站 · 可恢复", "TRASH · RECOVERABLE")}</p>` +
          deleted
            .map(
              (p) =>
                `<div class="project-row"><span>${esc(p.content.title)}</span><button data-restore-session="${p.id}" data-revision="${p.revision}">${tr("恢复", "Restore")}</button></div>`,
            )
            .join("")
        : "");
    if (!$("project-dialog").open) $("project-dialog").showModal();
  }
  async function exportFile(kind) {
    const tutorialProject = s.session.id;
    await flush();
    const button = $("export-" + (kind === "mid" ? "midi" : "wav"));
    button.disabled = true;
    $("export-feedback").textContent = tr(
      "正在渲染与测量输出，请稍候…",
      "Rendering and measuring output…",
    );
    $("export-feedback").setAttribute("aria-busy", "true");
    try {
      toast(tr("正在导出…", "Rendering export…"));
      const result = await request(base() + "/export/" + kind, {
        revision: s.session.revision,
      });
      const link = document.createElement("a");
      link.href = result.url;
      link.download = "";
      link.click();
      if (result.measurements) {
        const levels = result.measurements.levels,
          loudness = result.measurements.loudness;
        const peak =
          levels.peak_dbfs === null ? "−∞" : levels.peak_dbfs.toFixed(1);
        $("export-feedback").textContent =
          `${tr("导出就绪", "Export ready")} · ${levels.duration.toFixed(2)}s · ${peak} dBFS · ${loudness?.integrated_lufs == null ? tr("LUFS 不可用", "LUFS unavailable") : loudness.integrated_lufs.toFixed(1) + " LUFS"} · ${loudness?.true_peak_dbtp == null ? "" : loudness.true_peak_dbtp.toFixed(1) + " dBTP"}`;
      } else $("export-dialog").close();
      toast(tr("导出完成", "Export ready"));
      if (kind === "wav") tutorialPanel?.observe("export", tutorialProject);
    } finally {
      button.disabled = false;
      $("export-feedback").setAttribute("aria-busy", "false");
    }
  }
  document
    .querySelectorAll("[data-view]")
    .forEach((b) => (b.onclick = () => view(b.dataset.view, true)));
  $("close-library").onclick = () =>
    document.body.classList.remove("library-open");
  $("close-inspector").onclick = () =>
    document.body.classList.remove("inspector-open");
  $("panel-shade").onclick = () =>
    document.body.classList.remove("library-open", "inspector-open");
  $("toggle-inspector").onclick = () => {
    document.body.classList.remove("library-open");
    document.body.classList.toggle("inspector-open");
  };
  $("language").onclick = () => {
    s.lang = s.lang === "zh" ? "en" : "zh";
    localStorage.setItem("station-language", s.lang);
    renderAll();
    view(s.view);
    renderModels();
    renderTasks();
  };
  $("new-project").onclick = guarded(() => create());
  $("demo").onclick = $("empty-demo").onclick = guarded(() => create(true));
  $("open-projects").onclick = guarded(projectDialog);
  $("project-title").onchange = () => {
    const name = $("project-title").value.trim();
    if (name)
      mutate(() => (content().title = name), { live: true, render: false });
    else $("project-title").value = content().title;
  };
  $("project-title").oninput = () => {
    const title = $("project-title").value.trim();
    if (s.session && title && title !== content().title) {
      content().title = title;
      dirty();
    }
  };
  $("bpm").onchange = () => {
    const bpm = Number($("bpm").value);
    if (bpm < 30 || bpm > 300 || !Number.isFinite(bpm))
      return ($("bpm").value = content().bpm);
    const ratio = content().bpm / bpm;
    if (
      (content().loop && (content().loop.end * 60) / bpm > 600 + 1e-9) ||
      (content().sections || []).some(
        (section) => (section.end * 60) / bpm > 600 + 1e-9,
      ) ||
      content().tracks.some(
        (t) =>
          t.kind === "midi" &&
          t.clips.some(
            (c) =>
              (c.start + c.duration) * ratio > 600 || c.offset * ratio > 600,
          ),
      )
    ) {
      $("bpm").value = content().bpm;
      return toast(
        tr(
          "调速后的 MIDI、段落或循环区间超出 10 分钟范围，请先缩短工程",
          "MIDI, section or loop range would exceed 10 minutes; shorten the session first",
        ),
        true,
      );
    }
    mutate(() => {
      for (const t of content().tracks)
        if (t.kind === "midi")
          for (const c of t.clips) {
            c.duration *= ratio;
            c.offset *= ratio;
            c.start *= ratio;
            c.fade_in = Math.min(30, c.fade_in * ratio);
            c.fade_out = Math.min(30, c.fade_out * ratio);
            for (const point of c.volume_points || []) point.time *= ratio;
          }
      content().bpm = bpm;
      renderGenerationHealth();
    });
  };
  $("import").onclick = $("empty-import").onclick = () =>
    $("audio-files").click();
  $("audio-files").onchange = guarded(async () => {
    try {
      await importFiles($("audio-files").files);
    } finally {
      $("audio-files").value = "";
    }
  });
  $("asset-search").oninput = () => {
    renderAssets();
    renderGrooves();
  };
  $("asset-list").onclick = guarded((e) => {
    const el = e.target.closest("[data-asset]");
    if (el) addAsset(el.dataset.asset, null, s.position);
  });
  $("asset-list").ondragstart = (e) => {
    const el = e.target.closest("[data-asset]");
    if (el)
      e.dataTransfer.setData("application/x-studio-asset", el.dataset.asset);
  };
  $("add-audio").onclick = guarded(() => addTrack());
  $("add-midi").onclick = guarded(() => addTrack("midi"));
  $("instrument-list").onclick = guarded(async (e) => {
    const preview = e.target.closest("[data-preview-instrument]");
    if (preview) {
      const k = preview.dataset.previewInstrument,
        drum = k === "vcsl-drums";
      return audition(
        k,
        k,
        (drum ? [36, 42, 38, 42] : [60, 64, 67, 72]).map((pitch, i) => ({
          pitch,
          start: i * 0.5,
          length: 0.5,
          velocity: 90,
        })),
        120,
        4,
      );
    }
    const el = e.target.closest("[data-add-instrument]");
    if (el) {
      stopPreview();
      addTrack("midi", el.dataset.addInstrument);
    }
  });
  $("groove-list").onclick = guarded(async (e) => {
    const add = e.target.closest("[data-add-groove]"),
      preview = e.target.closest("[data-preview-groove]");
    if (add) return addGroove(add.dataset.addGroove);
    if (preview) {
      const pattern = s.library.patterns.find(
        (p) => p.id === preview.dataset.previewGroove,
      );
      return audition(
        pattern.id,
        "vcsl-drums",
        pattern.notes,
        pattern.bpm,
        pattern.beats,
      );
    }
  });
  $("groove-list").ondragstart = (e) => {
    const el = e.target.closest("[data-pattern]");
    if (el)
      e.dataTransfer.setData(
        "application/x-studio-pattern",
        el.dataset.pattern,
      );
  };
  $("midi-confirm").onclick = guarded(async () => {
    if (!pendingMidi) return;
    const button = $("midi-confirm");
    button.disabled = true;
    try {
      pause();
      await flush();
      const form = new FormData();
      form.append("file", pendingMidi);
      const query = new URLSearchParams({
        revision: s.session.revision,
        at: snap(s.position),
        use_source_tempo: $("midi-source-tempo").checked,
      });
      accept(await request(base() + "/midi?" + query, form), {
        selectLast: true,
      });
      $("midi-dialog").close();
      dock("piano");
    } finally {
      button.disabled = false;
    }
  });
  $("play").onclick = guarded(play);
  $("stop").onclick = () => {
    stopPreview();
    pause();
    s.position = engine.position = 0;
  };
  $("rewind").onclick = () => seek(0);
  $("split").onclick = guarded(() => {
    const c = selectedClip();
    if (!c) return;
    const parts = splitClip(c, snap(s.position));
    if (!parts)
      return toast(
        tr(
          "把播放头放在片段内部再切分",
          "Place the playhead inside the clip to split",
        ),
      );
    mutate(() => {
      const t = selectedTrack();
      t.clips.splice(t.clips.indexOf(c), 1, ...parts);
      s.clip = parts[1].id;
    });
  });
  $("duplicate").onclick = guarded(duplicate);
  $("delete-clip").onclick = removeClip;
  for (const direction of ["undo", "redo"])
    $(direction).onclick = guarded(async () => {
      pause();
      await flush();
      accept(
        await request(base() + "/history/" + direction, {
          revision: s.session.revision,
        }),
      );
    });
  $("zoom-in").onclick = () => {
    s.zoom = Math.min(140, s.zoom * 1.3);
    renderTracks();
    if (s.dock === "piano") renderPiano();
  };
  $("zoom-out").onclick = () => {
    s.zoom = Math.max(0.5, s.zoom / 1.3);
    renderTracks();
    if (s.dock === "piano") renderPiano();
  };
  $("ruler-ticks").onclick = (e) =>
    seek(
      Math.max(
        0,
        (e.clientX - $("ruler-ticks").getBoundingClientRect().left) / s.zoom,
      ),
    );
  $("track-list").onclick = guarded((e) => {
    const row = e.target.closest("[data-track]");
    if (!row) return;
    const t = content().tracks.find((t) => t.id === row.dataset.track);
    if (e.target.closest("[data-toggle]"))
      return toggle(t, e.target.closest("[data-toggle]").dataset.toggle);
    if (e.target.closest("[data-remove-track]"))
      return mutate(() => {
        content().tracks = content().tracks.filter((x) => x.id !== t.id);
        s.track = content().tracks[0]?.id;
        s.clip = null;
      });
    if (e.target.matches("input")) return;
    s.track = t.id;
    s.clip = e.target.closest("[data-clip]")?.dataset.clip || null;
    document
      .querySelectorAll("[data-track]")
      .forEach((el) =>
        el.classList.toggle("selected", el.dataset.track === s.track),
      );
    document
      .querySelectorAll("[data-clip]")
      .forEach((el) =>
        el.classList.toggle("selected", el.dataset.clip === s.clip),
      );
    $("split").disabled = !selectedClip();
    $("duplicate").disabled = !selectedClip();
    $("delete-clip").disabled = !selectedClip();
    renderMixer();
    renderEffects();
    renderInspector();
    if (s.dock === "piano") renderPiano();
  });
  $("track-list").ondblclick = (e) => {
    const el = e.target.closest("[data-clip]");
    if (el && selectedTrack()?.kind === "midi") dock("piano");
  };
  $("track-list").onpointerdown = (e) => {
    if (e.button !== 0) return;
    const el = e.target.closest("[data-clip]");
    if (!el) return;
    const t = content().tracks.find(
        (t) => t.id === el.closest("[data-track]").dataset.track,
      ),
      c = t.clips.find((c) => c.id === el.dataset.clip);
    const startX = e.clientX,
      oldStart = c.start,
      oldDuration = c.duration,
      resizing = e.target.classList.contains("clip-handle");
    const originalPoints = structuredClone(c.volume_points || []);
    let moved = false;
    const move = (event) => {
      const delta = (event.clientX - startX) / s.zoom;
      if (Math.abs(event.clientX - startX) < 3 && !moved) return;
      if (!moved) {
        pause();
        moved = true;
      }
      s.track = t.id;
      s.clip = c.id;
      if (resizing) {
        const max =
          t.kind === "audio"
            ? asset(c.asset).duration - c.offset
            : 600 - c.start;
        c.duration = Math.max(
          0.02,
          Math.min(max, snap(oldDuration + delta), 600 - c.start),
        );
        c.fade_in = Math.min(c.fade_in, c.duration);
        c.fade_out = Math.min(c.fade_out, c.duration - c.fade_in);
        c.volume_points = StationEnvelope.crop(
          { ...c, volume_points: originalPoints },
          0,
          c.duration,
        );
        el.style.width = `${Math.max(12, c.duration * s.zoom)}px`;
      } else {
        c.start = Math.max(
          0,
          Math.min(600 - c.duration, snap(oldStart + delta)),
        );
        el.style.left = `${c.start * s.zoom}px`;
      }
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      if (moved) {
        dirty();
        renderAll();
      }
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up, { once: true });
  };
  $("arranger").ondragover = (e) => {
    e.preventDefault();
    $("arranger").classList.add("drag-over");
  };
  $("arranger").ondragleave = (e) => {
    if (!$("arranger").contains(e.relatedTarget))
      $("arranger").classList.remove("drag-over");
  };
  $("arranger").ondrop = guarded(async (e) => {
    e.preventDefault();
    $("arranger").classList.remove("drag-over");
    if (e.dataTransfer.files.length) return importFiles(e.dataTransfer.files);
    const pattern = e.dataTransfer.getData("application/x-studio-pattern");
    if (pattern) return addGroove(pattern);
    const id = e.dataTransfer.getData("application/x-studio-asset"),
      lane = e.target.closest("[data-lane]");
    if (id)
      addAsset(
        id,
        lane?.dataset.lane,
        lane
          ? Math.max(
              0,
              (e.clientX - lane.getBoundingClientRect().left) / s.zoom,
            )
          : s.position,
      );
  });
  document.addEventListener("input", (e) => {
    const el = e.target;
    if (!s.session) return;
    if (el.dataset.level) {
      const t = content().tracks.find((t) => t.id === el.dataset.level);
      t.gain_db = Number(el.value);
      document
        .querySelectorAll(`[data-level="${t.id}"]`)
        .forEach((input) => (input.value = el.value));
      document.querySelector(`[data-db="${t.id}"]`).textContent =
        t.gain_db.toFixed(1) + " dB";
      engine.update(content());
      dirty();
    } else if (el.dataset.pan) {
      content().tracks.find((t) => t.id === el.dataset.pan).pan = Number(
        el.value,
      );
      engine.update(content());
      dirty();
    } else if (el.hasAttribute("data-master")) {
      content().master_db = Number(el.value);
      $("master-db").textContent = content().master_db.toFixed(1) + " dB";
      engine.update(content());
      dirty();
    }
  });
  $("mixer").onclick = (e) => {
    const fx = e.target.closest("[data-open-effects]");
    if (fx) {
      if (fx.dataset.openEffects !== "master") {
        s.track = fx.dataset.openEffects;
        s.clip = null;
      }
      renderTracks();
      renderMixer();
      renderInspector();
      dock("effects");
      if (fx.dataset.openEffects === "master") $("fx-limiter-enabled").focus();
      return;
    }
    const toggleButton = e.target.closest("[data-mixer-toggle]");
    if (toggleButton)
      return toggle(
        content().tracks.find((t) => t.id === toggleButton.dataset.id),
        toggleButton.dataset.mixerToggle,
      );
    const channel = e.target.closest("[data-channel]");
    if (channel && !e.target.matches("input")) {
      s.track = channel.dataset.channel;
      s.clip = selectedTrack().clips[0]?.id;
      renderTracks();
      renderMixer();
      renderEffects();
      renderInspector();
    }
  };
  $("inspector-content").onchange = guarded((e) => {
    const el = e.target,
      t = selectedTrack(),
      c = selectedClip();
    function edit(fn, live = false) {
      mutate(fn, { live, render: e.type !== "input" });
      if (e.type === "input") {
        renderTracks();
        renderMixer();
      }
    }
    if (el.hasAttribute("data-track-name")) {
      if (el.value.trim() && t.name !== el.value.trim())
        edit(() => (t.name = el.value.trim()), true);
      return;
    }
    if (el.hasAttribute("data-instrument"))
      return t.instrument === el.value
        ? undefined
        : edit(() => (t.instrument = el.value));
    if (!el.dataset.field) return;
    const [kind, key] = el.dataset.field.split("."),
      obj = kind === "track" ? t : kind === "note" ? c?.notes[s.noteIndex] : c,
      value = Number(el.value);
    if (
      !obj ||
      !Number.isFinite(value) ||
      !el.checkValidity() ||
      (kind === "note" &&
        ["pitch", "velocity"].includes(key) &&
        !Number.isInteger(value))
    ) {
      if (e.type !== "input") renderInspector();
      return;
    }
    if (obj[key] === value) return;
    const candidate = { ...obj, [key]: value };
    if (
      kind === "clip" &&
      (candidate.start + candidate.duration > 600 ||
        candidate.fade_in + candidate.fade_out > candidate.duration ||
        (t.kind === "audio" &&
          candidate.offset + candidate.duration >
            asset(c.asset).duration + 1 / 44100))
    ) {
      if (e.type === "input") return;
      renderInspector();
      throw Error(
        tr(
          "片段范围超出素材或淡化长度不正确",
          "Clip bounds or fade length are invalid",
        ),
      );
    }
    edit(() => {
      if (kind === "clip" && key === "duration")
        obj.volume_points = StationEnvelope.crop(obj, 0, value);
      obj[key] = value;
    }, kind === "track");
    if (kind === "note") renderPiano();
  });
  $("inspector-content").oninput = $("inspector-content").onchange;
  $("inspector-content").onclick = guarded((e) => {
    if (e.target.closest("[data-inspect-duplicate]")) duplicate();
    if (e.target.closest("[data-inspect-remove]")) removeClip();
  });
  $("effects").oninput = (event) => {
    const el = event.target,
      path = el.dataset.fxParam;
    if (!path || !el.checkValidity()) return;
    const [section, key] = path.split("."),
      value = Number(el.value);
    if (!Number.isFinite(value)) return;
    if (section !== "limiter" && !selectedTrack()) return;
    mutate(
      () => {
        if (section === "limiter") {
          content().limiter = {
            ...StationEffects.limiterDefaults(),
            ...content().limiter,
            [key]: value,
          };
        } else {
          const track = selectedTrack();
          track.effects = StationEffects.normalize(track.effects);
          track.effects[section][key] = value;
        }
      },
      { live: true, render: false },
    );
    document.querySelector(`[data-fx-output="${path}"]`).textContent =
      `${value}${el.dataset.suffix}`;
  };
  $("effects").onchange = (event) => {
    const el = event.target;
    if (el.hasAttribute("data-fx-track")) {
      s.track = el.value;
      s.clip = null;
      renderTracks();
      renderMixer();
      renderInspector();
      renderEffects();
      return;
    }
    if (!el.dataset.fxEnable && !el.hasAttribute("data-fx-preset")) return;
    if (el.hasAttribute("data-fx-preset") && !el.value) return;
    mutate(
      () => {
        if (el.dataset.fxEnable === "limiter") {
          content().limiter = {
            ...StationEffects.limiterDefaults(),
            ...content().limiter,
            enabled: el.checked,
          };
        } else {
          const track = selectedTrack();
          if (!track) return;
          track.effects = StationEffects.normalize(track.effects);
          if (el.dataset.fxEnable)
            track.effects[el.dataset.fxEnable].enabled = el.checked;
          else
            track.effects = StationEffects.normalize(
              StationEffects.presets[el.value].settings,
            );
        }
      },
      { live: true, render: false },
    );
    renderMixer();
    renderEffects();
  };
  $("effects").onclick = (event) => {
    if (!selectedTrack()) return;
    const bypass = event.target.closest("[data-fx-bypass]"),
      reset = event.target.closest("[data-fx-reset]");
    if (!bypass && !reset) return;
    mutate(
      () => {
        const track = selectedTrack();
        track.effects = reset
          ? StationEffects.defaults()
          : StationEffects.normalize(track.effects);
        if (bypass) track.effects.bypass = !track.effects.bypass;
      },
      { live: true, render: false },
    );
    renderMixer();
    renderEffects();
  };
  for (const name of ["mixer", "effects", "piano", "tasks"])
    $(name + "-tab").onclick = () => dock(name);
  $("piano").onclick = guarded(async (e) => {
    const key = e.target.closest("[data-note-key]");
    if (key)
      await engine.note(
        Number(key.dataset.noteKey),
        selectedTrack()?.instrument,
      );
    const note = e.target.closest("[data-note]");
    if (note) {
      s.noteClip = selectedClip().id;
      s.noteIndex = Number(note.dataset.note);
      renderInspector();
      await engine.note(
        selectedClip().notes[Number(note.dataset.note)].pitch,
        selectedTrack().instrument,
      );
    }
  });
  $("piano").ondblclick = guarded(async (e) => {
    const c = selectedClip(),
      t = selectedTrack(),
      grid = e.target.closest(".piano-grid");
    if (!c || t.kind !== "midi" || !grid || e.target.closest("[data-note-key]"))
      return;
    const n = e.target.closest("[data-note]");
    if (n) {
      s.noteClip = null;
      return mutate(() => c.notes.splice(Number(n.dataset.note), 1));
    }
    const rect = grid.getBoundingClientRect(),
      start = Math.max(
        0,
        Math.round(
          ((e.clientX - rect.left) / Number(grid.dataset.beatWidth)) * 4,
        ) / 4,
      ),
      pitch =
        Number(grid.dataset.high) - Math.floor((e.clientY - rect.top) / 14);
    if (
      pitch < Number(grid.dataset.low) ||
      pitch > Number(grid.dataset.high) ||
      start * beatSeconds() >= c.offset + c.duration ||
      c.notes.length >= 512
    )
      return;
    mutate(() => c.notes.push({ pitch, start, length: 0.5, velocity: 90 }));
    await engine.note(pitch, t.instrument);
  });
  $("model-list").onclick = guarded(async (e) => {
    const check = e.target.closest("[data-check-model]"),
      run = e.target.closest("[data-run-model]");
    if (check) {
      check.disabled = true;
      check.textContent = "…";
      try {
        const model = await request(
          `/api/studio/models/${check.dataset.checkModel}/check`,
          {},
        );
        s.models = s.models.map((m) => (m.id === model.id ? model : m));
        renderModels();
      } finally {
        check.disabled = false;
      }
      return;
    }
    if (!run) return;
    const c = selectedClip(),
      a = c && asset(c.asset);
    if (!a)
      throw Error(tr("请先选择一段音频素材", "Select an audio clip first"));
    await flush();
    await request(base() + "/process", {
      revision: s.session.revision,
      clip: c.id,
      model: run.dataset.runModel,
      ...StationModelControls.read(run.closest("[data-model-card]")),
    });
    dock("tasks");
    await pollTasks();
    toast(tr("任务已加入本地队列", "Task queued locally"));
  });
  $("tasks").onclick = guarded(async (e) => {
    const report = e.target.closest("[data-musical-report]");
    if (report)
      return workflowPanel.showReport(
        report.dataset.project,
        report.dataset.musicalReport,
      );
    const melody = e.target.closest("[data-adopt-melody]");
    if (melody) {
      stopPreview();
      pause();
      await flush();
      accept(
        await request(
          `${base()}/processing/${melody.dataset.adoptMelody}/adopt-melody`,
          { revision: s.session.revision },
        ),
        { selectLast: true },
      );
      dock("piano");
      return;
    }
    const generation = e.target.closest(
      "[data-preview-generation], [data-adopt-generation], [data-adopt-section-generation], [data-cancel-generation], [data-info-generation]",
    );
    if (generation) {
      const id =
        generation.dataset.previewGeneration ||
        generation.dataset.adoptGeneration ||
        generation.dataset.adoptSectionGeneration ||
        generation.dataset.cancelGeneration ||
        generation.dataset.infoGeneration;
      if (generation.dataset.infoGeneration) {
        const task = s.generations.find((t) => t.id === id);
        $("task-info").textContent = JSON.stringify(task, null, 2);
        $("task-info-dialog").showModal();
        return;
      }
      if (generation.dataset.previewGeneration) return auditionGeneration(id);
      if (generation.dataset.cancelGeneration) {
        await request(`${base()}/generations/${id}/cancel`, {});
      } else {
        stopPreview();
        pause();
        await flush();
        accept(
          await request(`${base()}/generations/${id}/adopt`, {
            revision: s.session.revision,
            at: snap(s.position),
            target_section: !!generation.dataset.adoptSectionGeneration,
            replace_source: generation.hasAttribute("data-replace-source"),
          }),
          { selectLast: true },
        );
        toast(
          tr(
            generation.hasAttribute("data-replace-source")
              ? "局部重绘已采用，可撤销恢复原片段"
              : "生成草稿已加入新轨道，可撤销",
            generation.hasAttribute("data-replace-source")
              ? "Repaint applied; undo restores the original clip"
              : "Draft added as a new track; you can undo",
          ),
        );
      }
      await pollTasks();
      return;
    }
    const preview = e.target.closest("[data-preview-task]");
    if (preview)
      return auditionTask(preview.dataset.project, preview.dataset.previewTask);
    const stems = e.target.closest("[data-adopt-stems]");
    if (stems) {
      stopPreview();
      pause();
      await flush();
      accept(
        await request(
          `${base()}/processing/${stems.dataset.adoptStems}/adopt-stems`,
          {
            revision: s.session.revision,
          },
        ),
        { selectLast: true },
      );
      toast(
        tr(
          "已替换为对齐分轨；原素材保留，可一次撤销",
          "Replaced with aligned stems; original retained, undo in one step",
        ),
      );
      await pollTasks();
      return;
    }
    const cancel = e.target.closest("[data-cancel-task]");
    if (cancel) {
      await request(
        `/api/projects/${cancel.dataset.project}/studio/tasks/${cancel.dataset.cancelTask}/cancel`,
        {},
      );
      await pollTasks();
      return;
    }
    const el = e.target.closest("[data-attach-task]");
    if (!el) return;
    stopPreview();
    pause();
    await flush();
    accept(
      await request(base() + "/attach", {
        revision: s.session.revision,
        source_project: el.dataset.project,
        asset: "asset:" + el.dataset.attachTask,
        at: snap(s.position),
      }),
      { selectLast: true },
    );
    toast(tr("处理结果已加入新轨道", "Result added as a new track"));
  });
  $("generation-instrumental").onchange = () => {
    $("generation-vocal").hidden = $("generation-instrumental").checked;
    $("generation-lyrics").required = !$("generation-instrumental").checked;
  };
  $("open-generation").onclick = guarded(async () => {
    $("generation-key").innerHTML =
      '<option value="">Auto</option>' +
      StationEdit.keyNames
        .flatMap((k) =>
          ["major", "minor"].map(
            (mode) => `<option value="${k} ${mode}">${k} ${mode}</option>`,
          ),
        )
        .join("");
    $("generation-key").value = content().key || "";
    const reference = selectedClip();
    const canVary =
      reference?.asset && reference.duration >= 10 && reference.duration <= 60;
    $("generation-mode").querySelector('[value="cover"]').disabled = !canVary;
    $("generation-mode").querySelector('[value="repaint"]').disabled = !canVary;
    if (canVary) {
      $("repaint-start").value = Math.min(4, reference.duration / 3);
      $("repaint-end").value = Math.min(8, (reference.duration * 2) / 3);
      $("repaint-end").max = reference.duration;
    }
    if (!canVary) $("generation-mode").value = "text2music";
    $("generation-context").textContent = tr(
      `工程 ${content().bpm} BPM · ${content().key || "未指定调性"}。这些是生成条件，采用前仍需分析和试听。`,
      `Session ${content().bpm} BPM · ${content().key || "unspecified key"}. These are requested conditions; analyze and audition the output.`,
    );
    if (canVary)
      $("generation-context").textContent += tr(
        ` 变奏参考：${reference.name}，${reference.duration.toFixed(2)} 秒。`,
        ` Variation source: ${reference.name}, ${reference.duration.toFixed(2)} s.`,
      );
    compositionPanel.prepareGeneration();
    $("generation-dialog").showModal();
    await loadModels();
  });
  $("generation-use-region").onclick = () => {
    const loop = content().loop || { start: 0, end: 16 };
    const seconds = ((loop.end - loop.start) * 60) / content().bpm;
    const length = Math.max(10, Math.min(60, Math.round(seconds)));
    const option = document.createElement("option");
    option.value = length;
    option.textContent = length + " s · region";
    $("generation-duration").append(option);
    $("generation-duration").value = length;
    $("generation-context").textContent = tr(
      `范围 ${seconds.toFixed(2)} 秒 → 请求 ${length} 秒（模型支持整数 10–60 秒），采用时需裁剪。`,
      `Range ${seconds.toFixed(2)} s → requested ${length} s (integer 10–60 s supported); trim on adoption.`,
    );
  };
  document.querySelectorAll("[data-generation-preset]").forEach(
    (button) =>
      (button.onclick = () => {
        $("generation-prompt").value = {
          jazz: "Warm jazz trio, soft grand piano, brushed acoustic drums and upright bass, intimate late-night room, instrumental",
          electronic:
            "Melodic electronic house, warm analog synth arpeggios, deep bass and a steady four-on-the-floor beat, instrumental",
          cinematic:
            "Gentle cinematic soundtrack, expressive piano, warm strings and subtle percussion, hopeful and spacious, instrumental",
        }[button.dataset.generationPreset];
      }),
  );
  $("generation-form").onsubmit = (event) => {
    event.preventDefault();
    guarded(async () => {
      if (generationSubmitting) return;
      generationSubmitting = true;
      renderGenerationHealth();
      try {
        const project = s.session.id;
        await flush();
        if (s.session.id !== project)
          throw Error(
            tr("工程已切换，请重新生成", "Session changed; submit again"),
          );
        await request(base() + "/generations", {
          revision: s.session.revision,
          ...compositionPanel.generationPayload(),
        });
        if (s.session.id === project) {
          $("generation-dialog").close();
          document.body.classList.remove("library-open");
          dock("tasks");
          await pollTasks();
        }
        toast(tr("音乐草稿已加入本地生成队列", "Music draft queued locally"));
      } finally {
        generationSubmitting = false;
        renderGenerationHealth();
      }
    })();
  };
  $("project-list").onclick = guarded(async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    if (btn.dataset.openSession) {
      await open(btn.dataset.openSession);
      $("project-dialog").close();
      return;
    }
    const key = btn.dataset.trashSession || btn.dataset.restoreSession,
      restore = !!btn.dataset.restoreSession;
    if (!key) return;
    await request(
      `/api/workstation/projects/${key}/${restore ? "restore" : "trash"}`,
      { revision: Number(btn.dataset.revision) },
    );
    if (!restore && key === s.session.id) {
      s.dirty = false;
      const list = await request("/api/workstation/projects");
      if (list.length) await open(list[0].id);
      else await create();
    }
    await projectDialog();
  });
  $("export").onclick = () => $("export-dialog").showModal();
  $("export-wav").onclick = guarded(() => exportFile("wav"));
  $("export-midi").onclick = guarded(() => exportFile("mid"));
  $("export-credits").onclick = guarded(async () => {
    await flush();
    const link = document.createElement("a");
    link.href = base() + "/credits";
    link.download = "music-studio-credits.txt";
    link.click();
    $("export-dialog").close();
  });
  $("export-project").onclick = guarded(async () => {
    const button = $("export-project");
    button.disabled = true;
    $("export-feedback").textContent = tr(
      "正在打包工程与音频…",
      "Packing project and audio…",
    );
    $("export-feedback").setAttribute("aria-busy", "true");
    try {
      await flush();
      const result = await request(base() + "/pack", {
        revision: s.session.revision,
      });
      const link = document.createElement("a");
      link.href = result.url;
      link.download = "";
      link.click();
      $("export-dialog").close();
    } finally {
      button.disabled = false;
      $("export-feedback").setAttribute("aria-busy", "false");
    }
  });
  document
    .querySelectorAll(".close-dialog")
    .forEach((b) => (b.onclick = () => b.closest("dialog").close()));
  document.querySelectorAll("dialog").forEach(
    (d) =>
      (d.onclick = (e) => {
        if (
          e.target === d &&
          e.offsetX >= 0 &&
          e.offsetX <= d.clientWidth &&
          e.offsetY >= 0 &&
          e.offsetY <= d.clientHeight
        )
          return;
        if (
          e.target === d &&
          !(d.id === "recording-dialog" && recordingPanel?.busy())
        )
          d.close();
      }),
  );
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape")
      document.body.classList.remove("library-open", "inspector-open");
    if (
      e.target.matches("input,textarea,select") ||
      document.querySelector("dialog[open]")
    )
      return;
    if (e.code === "Space") {
      e.preventDefault();
      guarded(play)();
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
      e.preventDefault();
      $(e.shiftKey ? "redo" : "undo").click();
    }
    if (!e.defaultPrevented && (e.key === "Delete" || e.key === "Backspace")) {
      e.preventDefault();
      removeClip();
    }
  });
  window.addEventListener("beforeunload", (e) => {
    if (s.dirty || s.saving) {
      e.preventDefault();
      e.returnValue = "";
    }
  });
  window.WorkbenchDesktop = {
    async prepareClose() {
      if (recordingPanel?.busy() || recordingPanel?.hasUnsavedTake())
        throw Error(
          tr(
            "请先完成录音并保留录音结果",
            "Finish and keep your recording first",
          ),
        );
      await flush();
    },
  };
  engine.onerror = (error) => {
    pause();
    toast(error.message, true);
  };
  function animate() {
    if (s.session) {
      if (engine.playing) {
        s.position = Math.max(0, engine.current());
        if (!engine.playRange.loop && s.position >= engine.playRange.end) {
          pause();
          s.position = engine.position = 0;
        }
      }
      $("time-display").textContent = seconds(s.position);
      const beat = s.position / beatSeconds();
      $("beat-display").textContent =
        `${Math.floor(beat / 4) + 1} . ${Math.floor(beat % 4) + 1} . ${Math.floor((beat % 1) * 4) + 1}`;
      $("playhead").style.left = `${headWidth() + s.position * s.zoom}px`;
      for (const t of content().tracks) {
        const level = engine.meter(t.id),
          el = document.querySelector(`[data-vu="${t.id}"]`);
        if (el)
          el.style.height = `${Math.min(100, Math.max(0, ((20 * Math.log10(level || 1e-6) + 60) / 60) * 100))}%`;
      }
      if ($("fx-compression"))
        $("fx-compression").textContent =
          `${(engine.graphs.get(s.track)?.effect?.reduction || 0).toFixed(1)} dB`;
      if ($("fx-limiting"))
        $("fx-limiting").textContent =
          `${(engine.masterEffect?.reduction || 0).toFixed(1)} dB`;
      if ($("fx-output-peak")) {
        const peak = engine.masterEffect?.peak || 0;
        $("fx-output-peak").textContent =
          peak >= 1
            ? tr(
                "削波风险 · 降低音量或开启限制",
                "Clipping · lower level or enable limiter",
              )
            : `${tr("输出峰值", "Output peak")} · ${peak > 0 ? (20 * Math.log10(peak)).toFixed(1) : "−∞"} dBFS`;
        $("fx-output-peak").classList.toggle("fx-clipping", peak >= 1);
      }
      if ($("master-vu"))
        $("master-vu").style.height =
          `${Math.min(100, Math.max(0, ((20 * Math.log10(engine.masterMeter() || 1e-6) + 60) / 60) * 100))}%`;
    }
    requestAnimationFrame(animate);
  }
  let timingBusy = false;
  async function applyTiming(settings) {
    if (timingBusy) return;
    timingBusy = true;
    const controls = ["loop", "metronome", "timing-settings"].map($);
    controls.forEach((button) => (button.disabled = true));
    try {
      await flush();
      const oldLoop = { ...StationTiming.loopDefaults(), ...content().loop },
        restart = JSON.stringify(oldLoop) !== JSON.stringify(settings.loop),
        wasPlaying = engine.playing || starting;
      mutate(() => Object.assign(content(), settings), { live: !restart });
      await flush();
      if (restart && wasPlaying) await play();
    } finally {
      timingBusy = false;
      controls.forEach((button) => (button.disabled = false));
    }
  }
  timingPanel = StationTimingUI.mount({
    $,
    tr,
    content: () => s.session?.content,
    selectedClip,
    duration,
    apply: applyTiming,
    toggle: guarded(async (kind) => {
      const settings = {
        loop: { ...StationTiming.loopDefaults(), ...content().loop },
        metronome: {
          ...StationTiming.metronomeDefaults(),
          ...content().metronome,
        },
      };
      settings[kind].enabled = !settings[kind].enabled;
      await applyTiming(settings);
    }),
  });
  recordingPanel = StationRecording.mount({
    $,
    tr,
    uid,
    toast,
    flush,
    position: () => s.position,
    session: () => s.session,
    pause: () => {
      stopPreview();
      pause();
    },
    adopt: async (blob, name, target) => {
      await flush();
      const form = new FormData();
      form.append("file", blob, name);
      const query = new URLSearchParams({
        revision: s.session.revision,
        at: target.at,
        import_id: target.importId,
      });
      accept(await request(base() + "/import?" + query, form), {
        selectLast: true,
      });
    },
  });
  workflowPanel = StationWorkflow.mount({
    $,
    s,
    tr,
    esc,
    uid,
    content,
    selectedClip,
    selectedTrack,
    mutate,
    renderAll,
    renderPiano,
    renderInspector,
    pause,
    seek,
    request,
    base,
    flush,
    accept,
    dock,
    pollTasks,
    toast,
    guarded,
    engine,
    headWidth,
    openBeatFit: (report, clip) => fitPanel.open(report, clip),
  });
  compositionPanel = StationCompositionUI.mount({
    $,
    s,
    tr,
    esc,
    content,
    uid,
    mutate,
    flush,
    request,
    base,
    guarded,
    toast,
    selectedClip,
    selectedTrack,
    seek,
  });
  envelopePanel = StationEnvelopeUI.mount({
    $,
    tr,
    esc,
    content,
    selectedClip,
    mutate,
    flush,
    guarded,
    toast,
  });
  fitPanel = StationFitUI.mount({
    $,
    s,
    tr,
    esc,
    content,
    selectedClip,
    flush,
    request,
    base,
    guarded,
    pause,
    stopPreview,
    pollTasks,
    dock,
    toast,
  });
  auditionPanel = StationAudition.mount({
    $,
    s,
    tr,
    esc,
    selectedClip,
    content,
    request,
    base,
    flush,
    guarded,
    pollTasks,
    pause,
    stopPreview,
  });
  tutorialPanel = StationTutorial.mount({
    document,
    storage: localStorage,
    tr,
    content,
    action: guarded(async (step) => {
      if (step === "listen") return "#play";
      if (step === "layers") return "[data-toggle='solo']";
      if (step === "melody") {
        const track = content().tracks.find(
          (t) => t.kind === "midi" && t.clips.length,
        );
        if (!track)
          return toast(
            tr(
              "先从首页打开可编辑示例，或添加一个乐器片段。",
              "Open the editable example from Home, or add an instrument clip first.",
            ),
          );
        s.track = track.id;
        s.clip = track.clips[0].id;
        renderAll();
        dock("piano");
        return "#piano";
      }
      if (step === "balance") {
        dock("mixer");
        return "#mixer";
      }
      if (step === "export") {
        $("export-dialog").showModal();
        return "#export-wav";
      }
      if (step === "manual") {
        await flush();
        location.href = "/learn.html";
      }
      if (step === "ai") {
        await flush();
        if (s.generationHealth?.available) $("open-generation").click();
        else location.href = "/ai-setup.html";
      }
    }),
  });
  $("open-tutorial").onclick = () => tutorialPanel.show();
  guarded(async () => {
    localize();
    s.library = await request("/api/workstation/library");
    engine.setLibrary(s.library);
    previewEngine.setLibrary(s.library);
    const sessions = await request("/api/workstation/projects"),
      key =
        new URLSearchParams(location.search).get("session") ||
        localStorage.getItem("station-session");
    const start = new URLSearchParams(location.search).get("start");
    const exists = sessions.find((p) => p.id === key) || sessions[0];
    if (exists) accept(exists);
    else await create();
    if (new URLSearchParams(location.search).has("tools")) {
      view("models", true);
    }
    if (start) {
      if (start === "example") tutorialPanel.show();
      const clean = new URL(location.href);
      clean.searchParams.delete("start");
      history.replaceState({}, "", clean);
      if (start === "ai") $("open-generation").click();
      if (start === "recording")
        document.querySelector('[data-view="assets"]').click();
    }
    animate();
    setInterval(() => {
      if (
        s.dock === "tasks" ||
        s.view === "models" ||
        [...s.tasks, ...s.generations].some((t) =>
          ["queued", "checking", "running"].includes(t.status),
        )
      )
        pollTasks();
    }, 4000);
  })();
})();
