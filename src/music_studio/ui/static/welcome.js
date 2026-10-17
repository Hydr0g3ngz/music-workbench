"use strict";
(() => {
  const $ = (id) => document.getElementById(id),
    esc = (x) =>
      String(x)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll('"', "&quot;");
  let lang = localStorage.getItem("station-language") || "zh",
    projects = [],
    available = false;
  const tr = (zh, en) => (lang === "zh" ? zh : en);
  const labels = {
    "welcome-title": [
      "从一个小灵感，<br>做出自己的音乐。",
      "A little idea.<br>A track of your own.",
    ],
    "welcome-intro": [
      "不必先懂乐理。先听一段、改一个音，再让想法长成作品。",
      "Start by listening and changing a note. Let a small idea grow into a piece.",
    ],
    "welcome-privacy": [
      "作品自动保存在本机 · 基础创作无需登录或下载模型",
      "Saved on this computer · No login or model download for basic creation",
    ],
    "example-title": ["跟着做出第一段音乐", "Make your first musical sketch"],
    "example-copy": [
      "五步跟练：试听、认识音轨、改一个音、调混音、导出。无需乐理基础。",
      "Five guided steps: listen, explore layers, edit a note, balance and export. No music theory needed.",
    ],
    "example-foot": ["无需模型，立即开始 ↗", "No models needed. Start now ↗"],
    "recording-title": ["从自己的录音开始", "Start with your own sound"],
    "recording-copy": [
      "导入哼唱、乐器或音频片段，剪辑、叠加与混音。",
      "Import a recording, an instrument or a clip. Edit, layer and mix.",
    ],
    "ai-title": ["和本地 AI 一起创作", "Create with local AI"],
    "ai-copy": [
      "描述音乐、生成素材、做参考变奏或局部重绘，再由你编排。",
      "Describe music, generate material, vary a reference or repaint a region. Arrange it your way.",
    ],
    "recent-title": ["接着上次的灵感", "Pick up an idea"],
    "start-empty": ["空白工程 ＋", "Empty project ＋"],
    "welcome-footer": [
      "你决定音乐的方向。AI 是工具，作品属于你的创作过程。",
      "You set the direction. AI is a tool in your creative process.",
    ],
  };
  function draw() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    for (const [id, pair] of Object.entries(labels))
      $(id).innerHTML = tr(...pair);
    $("welcome-language").textContent = tr("English", "中文");
    $("ai-foot").textContent = available
      ? tr("本地生成已配置 ↗", "Local generation configured ↗")
      : tr("打开 AI 自动配置 ↗", "Open automatic AI setup ↗");
    $("recent-projects").innerHTML = projects.length
      ? projects
          .slice(0, 6)
          .map(
            (p) =>
              `<a class="recent-project" href="/station.html?session=${p.id}"><strong>${esc(p.content.title)}</strong><span>${p.content.tracks.length} ${tr("条音轨", "tracks")} · ${p.content.bpm} BPM</span></a>`,
          )
          .join("")
      : `<p class="empty-copy">${tr("你的第一首作品会出现在这里。", "Your first piece will appear here.")}</p>`;
  }
  async function api(path, data) {
    const r = await fetch(
      path,
      data
        ? {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          }
        : {},
    );
    if (!r.ok)
      throw Error(
        tr(
          "暂时无法连接工作台，请回到启动器重试。",
          "Cannot reach the workspace. Retry from the launcher.",
        ),
      );
    return r.json();
  }
  async function start(kind) {
    document
      .querySelectorAll(".start-card,#start-empty")
      .forEach((b) => (b.disabled = true));
    try {
      const p = await api("/api/workstation/projects", {
        title:
          kind === "example"
            ? tr("我的第一段音乐", "My first musical sketch")
            : tr("新的灵感", "A new idea"),
        demo: kind === "example",
      });
      location.href = `/station.html?session=${p.id}&start=${kind}`;
    } catch (e) {
      $("welcome-error").textContent = e.message;
      document
        .querySelectorAll(".start-card,#start-empty")
        .forEach((b) => (b.disabled = false));
    }
  }
  for (const kind of ["example", "recording", "ai", "empty"])
    $("start-" + kind).onclick = () => {
      if (kind !== "ai" || available) return start(kind);
      location.href = "/ai-setup.html";
    };
  $("welcome-language").onclick = () => {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("station-language", lang);
    draw();
  };
  draw();
  Promise.allSettled([
    api("/api/workstation/projects"),
    api("/api/workstation/generation/status"),
  ]).then(([p, a]) => {
    if (p.status === "fulfilled") projects = p.value;
    else $("welcome-error").textContent = p.reason.message;
    if (a.status === "fulfilled") available = a.value.available;
    draw();
  });
})();
