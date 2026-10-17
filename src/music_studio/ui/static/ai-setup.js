"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  let lang = localStorage.getItem("station-language") || "zh",
    check,
    status,
    pending = false,
    actionError = "";
  const tr = (zh, en) => (lang === "zh" ? zh : en);
  const words = {
    title: ["让 AI 加入你的创作。", "Bring AI into your music."],
    intro: [
      "准备一次，以后直接创作。软件会自动下载、配置并实际生成一段音乐来验证。",
      "Set up once, then create. The app downloads, configures and generates a real musical sketch to check everything works.",
    ],
    "step-check": ["检查电脑", "Check computer"],
    "step-install": ["准备创作工具", "Prepare tools"],
    "step-verify": ["生成音乐验证", "Make a test sketch"],
    features: [
      "文字生成音乐 · 参考变奏 · 局部重绘",
      "Text to music · Reference variations · Region repaint",
    ],
    note: [
      "首次需要联网，预计下载 8–12 GB。请预留 35 GB 可用空间，并保持软件打开。之后音乐在本机生成，无需账号。",
      "The first setup downloads about 8–12 GB. Keep 35 GB free and leave the app open. Music then runs locally, with no account.",
    ],
    "preview-title": [
      "这台电脑生成的第一段音乐",
      "The first music made on this computer",
    ],
    "preview-copy": [
      "验证通过后即可生成自己的素材，音乐质量仍由你试听和选择。",
      "You can now make your own material. Listen and choose what works for your music.",
    ],
    "details-title": ["存放位置与模型说明", "Storage and model details"],
    "details-copy": [
      "AI 工具单独保存，升级或卸载程序不会删除你的作品与模型。暂停后可继续，已下载并校验的文件会复用。",
      "AI tools are stored separately. App upgrades and uninstalls keep your projects and models. Retry reuses verified downloads.",
    ],
    "failure-title": ["查看错误详情", "Error details"],
    skip: [
      "先用示例、录音和乐器创作 →",
      "Create with examples, recordings and instruments first →",
    ],
    local: [
      "你的工程和音频不会上传。",
      "Your projects and audio stay on your computer.",
    ],
    create: ["开始创作 →", "Start creating →"],
    cancel: ["暂停准备", "Pause setup"],
  };
  const stages = {
    preparing: ["正在准备", "Preparing"],
    runtime: ["准备独立的创作环境", "Preparing a separate music environment"],
    dependencies: [
      "下载与配置 AI 运行组件",
      "Downloading and configuring AI components",
    ],
    source: ["校验模型程序", "Verifying model software"],
    models: ["下载与校验音乐模型", "Downloading and verifying music models"],
    verify: [
      "正在本机生成 12 秒音乐，验证真实运行",
      "Generating a 12-second sketch locally to verify real inference",
    ],
    complete: ["准备完成", "Ready"],
  };
  const reasons = {
    "windows-x64": [
      "自动配置目前支持 Windows 10/11 64 位。",
      "Automatic setup currently supports Windows 10/11 x64.",
    ],
    "nvidia-8gb": [
      "这套音乐生成工具需要 NVIDIA 显卡，建议至少 8 GB 显存。当前电脑可先使用录音、乐器、剪辑与混音。",
      "This music generation profile requires an NVIDIA GPU with at least 8 GB VRAM. Recording, instruments, editing and mixing are available now.",
    ],
    "disk-35gb": [
      "空间不足，请在 AI 工具所在磁盘释放至少 35 GB。",
      "Free at least 35 GB on the AI tools drive.",
    ],
  };
  function draw() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    for (const [id, pair] of Object.entries(words))
      $(id).textContent = tr(...pair);
    $("language").textContent = tr("English", "中文");
    const state = status?.state || "idle",
      active = ["installing", "cancelling"].includes(state),
      ready = status?.generation?.available;
    const states = {
      idle: ["未配置", "Not set up"],
      installing: ["正在准备", "Setting up"],
      cancelling: ["正在暂停", "Pausing"],
      cancelled: ["已暂停", "Paused"],
      interrupted: ["准备中断，可继续", "Interrupted; resume"],
      failed: ["需要重试", "Retry needed"],
      ready: ["准备完成", "Ready"],
    };
    $("badge").textContent = ready
      ? tr("可创作", "Ready to create")
      : tr(...(states[state] || states.idle));
    $("install").textContent = active
      ? tr("正在准备…", "Setting up…")
      : tr(
          ...(["cancelled", "failed", "interrupted"].includes(state)
            ? ["继续准备", "Resume setup"]
            : ["下载并自动配置", "Download and set up"]),
        );
    $("install").hidden = Boolean(ready);
    $("install").disabled = pending || active || !check?.supported;
    $("cancel").hidden = !active;
    $("cancel").disabled = pending || state === "cancelling";
    $("create").hidden = !ready;
    $("reason").textContent =
      actionError ||
      (check?.reasons || []).map((r) => tr(...reasons[r])).join(" ");
    if (check) {
      $("hardware").textContent = check.gpus.length
        ? check.gpus
            .map((g) => `${g.name} · ${(g.memory_mib / 1024).toFixed(1)} GB`)
            .join(" / ")
        : tr("未检测到兼容的 NVIDIA 显卡", "No compatible NVIDIA GPU detected");
      $("space").textContent =
        tr("可用空间：", "Free space: ") +
        (check.free_bytes / 1024 ** 3).toFixed(1) +
        " GB";
      $("directory").textContent = check.directory;
    }
    const progress = status?.progress;
    document.querySelector(".install-progress").hidden = !active;
    $("stage").textContent = tr(
      ...(stages[progress?.stage] || stages.preparing),
    );
    $("progress").value = progress?.fraction || 0;
    $("progress-hint").textContent = tr(
      "这是准备阶段进度；下载速度取决于网络。可暂停后继续。关闭软件也会暂停。",
      "This indicates setup stages. Download time depends on your connection. Pause and resume anytime; closing the app also pauses setup.",
    );
    ["step-check", "step-install", "step-verify"].forEach((id, i) =>
      $(id).classList.toggle(
        "active",
        i === (active ? (progress?.stage === "verify" ? 2 : 1) : ready ? 2 : 0),
      ),
    );
    $("failure").hidden = state !== "failed";
    $("error").textContent = status?.error || "";
    $("verification").hidden = !status?.preview;
    const audio = $("verification").querySelector("audio");
    // Preserve the player while status polls. Never reload a playing preview.
    if (status?.preview && !audio.getAttribute("src"))
      audio.src = "/api/workstation/ai-setup/preview";
  }
  async function api(path, post = false) {
    const r = await fetch("/api/workstation/ai-setup" + path, {
      method: post ? "POST" : "GET",
    });
    const data = await r.json();
    if (!r.ok) throw Error(data.detail || r.statusText);
    return data;
  }
  async function refresh() {
    try {
      status = await api("");
      draw();
    } catch (e) {
      $("reason").textContent = tr(
        "连接中断，请重新打开软件。",
        "Connection lost. Reopen the app.",
      );
    }
  }
  async function action(path) {
    pending = true;
    actionError = "";
    draw();
    try {
      status = await api(path, true);
      await refresh();
    } catch (e) {
      actionError = e.message;
    } finally {
      pending = false;
      draw();
    }
  }
  $("install").onclick = () => action("/start");
  $("cancel").onclick = () => action("/cancel");
  $("language").onclick = () => {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("station-language", lang);
    draw();
  };
  draw();
  api("/preflight")
    .then((x) => {
      check = x;
      draw();
    })
    .catch(() => {
      $("reason").textContent = tr(
        "暂时无法检查电脑，请重新打开软件。",
        "Cannot check this computer. Reopen the app.",
      );
    });
  refresh();
  const timer = setInterval(refresh, 2500);
  addEventListener("pagehide", () => clearInterval(timer));
})();
