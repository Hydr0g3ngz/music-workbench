"use strict";

const $ = (id) => document.getElementById(id);
const words = {
  import: ["＋ 导入音频", "＋ Import audio"],
  models: ["本地模型", "Local models"],
  localTasks: ["本地音频任务", "Local audio tasks"],
  cleanupSpeech: ["让讲话更清楚", "Make speech clearer"],
  cleanupCopy: [
    "本地语音降噪，原音保留",
    "Local speech cleanup. Keep the original.",
  ],
  cleanupStrength: ["降噪强度", "Cleanup strength"],
  cleanupHelp: [
    "适合讲话，仍可能改变音色、音乐或环境声。立体声分别处理；完成后可按相同位置对比原音。轻量 GTCRN 内部为 16 kHz，会削弱高频。",
    "For speech; may still alter tone, music or ambience. Stereo channels are processed separately. Compare at the same position after processing. Lightweight GTCRN uses 16 kHz and reduces high frequencies.",
  ],
  loudnessNormalize: ["统一听感音量", "Set listening loudness"],
  loudnessCopy: [
    "按 LUFS 调整，保留动态与峰值余量",
    "Set LUFS while preserving dynamics and peak headroom.",
  ],
  loudnessHelp: [
    "调整整段听感音量，不做压缩。−16 LUFS 是可修改的起点；如果峰值余量不足，会少加一些音量并说明原因。",
    "Changes whole-file loudness without compression. −16 LUFS is an editable starting point. If peaks prevent the target, less gain is applied and reported.",
  ],
  targetLoudness: ["目标响度（LUFS）", "Target loudness (LUFS)"],
  peakCeiling: ["真峰值上限（dBTP）", "True peak ceiling (dBTP)"],
  peakLimited: [
    "已保留峰值余量，未完全达到响度目标。可在预览报告查看实际结果。",
    "Peak headroom limited the gain. The preview report shows the achieved loudness.",
  ],
  compare: ["A/B 对比", "Compare A/B"],
  before: ["处理前", "Before"],
  after: ["处理后", "After"],
  matchLoudness: ["匹配试听响度", "Match listening loudness"],
  compareHelp: [
    "A/B 在同一位置切换，不改变编辑或导出。匹配按整段 LUFS 衰减较响的一边，含噪声的参考也会影响测量。",
    "Switch at the same position without changing edits or exports. Matching attenuates the louder whole-file LUFS; noise in the reference affects this measurement too.",
  ],
  compareReady: [
    "A/B 对比已准备好，可在“预览与版本”打开。",
    "A/B comparison is ready. Open it under Previews & versions.",
  ],
  createPreview: ["生成编辑预览", "Create editing preview"],
  keepAsset: ["使用这份素材", "Use this asset"],
  integrated: ["整段响度", "Integrated loudness"],
  truePeak: ["真峰值", "True peak"],
  loudnessRange: ["响度范围", "Loudness range"],
  provisionalLra: [
    "短于 60 秒，响度范围仅作参考。",
    "Loudness range is provisional before 60 seconds.",
  ],
  unmeasurable: [
    "片段过短、静音或低于响度门限。",
    "Too short, silent or below the loudness gate.",
  ],
  comparePlay: ["播放 / 暂停", "Play / pause"],
  comparePosition: ["对比位置", "Comparison position"],
  playbackVolume: ["试听音量", "Listening volume"],
  installCleanup: ["安装模型", "Install model"],
  installAndRun: ["安装模型并生成试听", "Install model & prepare audio"],
  cleanupModel: ["处理方式", "Processing model"],
  firstModelDownload: [
    "首次将从 GitHub 下载并校验模型权重：",
    "First use downloads and verifies model weights from GitHub: ",
  ],
  compareLoading: ["正在准备两条试听音轨…", "Preparing both audio tracks…"],
  installingWeights: ["正在下载并校验…", "Downloading & verifying…"],
  localTasksHelp: [
    "按需运行模型，结果作为独立素材保留。",
    "Run only what you need. Results become separate assets.",
  ],
  serialQueue: [
    "逐个运行 · 不占用试听",
    "One at a time · playback stays available",
  ],
  capability: ["想做什么？", "Choose a capability"],
  device: ["运行设备", "Device"],
  runLocal: ["加入任务", "Queue task"],
  taskSource: [
    "处理当前试听音轨（全长）",
    "Processes the full auditioned track",
  ],
  emptyTasks: [
    "还没有分析任务。剪辑和导出无需加载模型。",
    "No analysis tasks yet. Editing and export need no model.",
  ],
  taskQueued: [
    "任务已排队，完成后会出现可试听或下载的素材。",
    "Task queued. Results will appear for listening or download.",
  ],
  tasksFinished: [
    "本地任务已结束，结果和诊断保留在下方。",
    "Local tasks finished. Results and diagnostics are available below.",
  ],
  modelNotReady: [
    "模型尚未就绪，请打开“本地模型”查看检查结果和安装说明。",
    "Model not ready. Open Local models for checks and setup instructions.",
  ],
  toolFailed: ["未完成", "Unsuccessful"],
  agentStopped: ["已停止", "Stopped"],
  agentFailed: ["运行失败", "Failed"],
  modelCheck: ["检查环境", "Check runtime"],
  modelChecking: ["正在隔离检查…", "Checking in isolation…"],
  modelHelp: [
    "检查会实际导入运行环境，不下载模型。缓存文件存在不等于已成功加载；运行任务时才加载权重。",
    "Checks import the runtime without downloading. Cached files are not loaded weights; loading happens when a task runs.",
  ],
  modelsSetup: ["安装说明 ↗", "Setup guide ↗"],
  state_unchecked: ["尚未检查", "Not checked"],
  state_missing: ["缺少运行依赖", "Runtime missing"],
  state_verified: ["运行环境检查通过", "Runtime imports passed"],
  state_failed: ["运行环境错误", "Runtime failed"],
  state_queued: ["排队中", "Queued"],
  state_checking: ["检查环境中", "Checking runtime"],
  state_running: ["运行中", "Running"],
  state_cancelling: ["正在取消", "Cancelling"],
  state_complete: ["已完成", "Complete"],
  state_cancelled: ["已取消", "Cancelled"],
  state_interrupted: ["已中断，可重新运行", "Interrupted; run a new task"],
  weightsCached: ["权重已缓存", "Weights cached"],
  weightsMissing: ["缺少缓存权重", "Weights not cached"],
  weightsNone: ["无需额外权重", "No extra weights"],
  inspectResult: ["查看结果", "View result"],
  taskDetails: ["参数与诊断", "Parameters & diagnostics"],
  synthesis: ["估计音符合成", "Estimated note synthesis"],
  downloadFile: ["下载", "Download"],
  taskFailed: ["任务失败", "Task failed"],
  editTranscript: ["修改转写文字", "Correct transcript text"],
  transcriptHelp: [
    "保存为新版本，原识别结果保留。行时间保持不变；修改行的逐字时间会清除。",
    "Saves a new version and retains the original. Line timing stays; word times on changed lines are cleared.",
  ],
  transcriptSaved: [
    "改字已保存为新版本，可下载 TXT、LRC 和 SRT。",
    "Corrections saved as a new version with TXT, LRC and SRT downloads.",
  ],
  search: ["搜索项目", "Search projects"],
  projects: ["项目", "PROJECTS"],
  trash: ["♲ 回收站", "♲ Trash"],
  local: ["音频处理在本机完成", "Audio is processed locally"],
  workspace: ["工作区", "Workspace"],
  newProject: ["新项目", "New project"],
  creationHome: ["创作首页 ↗", "Creation home ↗"],
  returnSession: ["返回创作工程 ↗", "Return to arrangement ↗"],
  welcomeTitle: [
    "从一段声音，开始创作。",
    "Start with a sound. Make it yours.",
  ],
  welcomeCopy: [
    "剪一个片段，调整声音，或让 AI 帮你完成。每一步都可以试听、比较和撤销。",
    "Shape a clip, adjust your sound, or ask AI for help. Preview, compare and undo every step.",
  ],
  drop: ["把音频拖到这里", "Drop your audio here"],
  formats: ["MP3 · WAV · FLAC · M4A · OGG", "MP3 · WAV · FLAC · M4A · OGG"],
  choose: ["选择音频", "Choose audio"],
  demo: ["试试歌曲素材 →", "Try the music demo →"],
  speechDemo: ["试试录音降噪 →", "Try speech cleanup →"],
  principle1: ["原音始终保留", "Keep your original"],
  principle1Copy: [
    "修改先成为独立预览，由你决定是否采用。",
    "Every edit creates a separate preview. You choose what to keep.",
  ],
  principle2: ["不必从专业术语开始", "Start with a goal"],
  principle2Copy: [
    "选一个目标，再按需要展开参数。",
    "Choose a task and open the details when you need them.",
  ],
  principle3: ["试听后再采用", "Audition before adoption"],
  principle3Copy: [
    "先比较原音与处理结果，保留操作记录和可恢复版本。",
    "Compare the original and result, with history and recoverable versions.",
  ],
  rename: ["重命名", "Rename"],
  delete: ["删除", "Delete"],
  export: ["导出音频 ↗", "Export audio ↗"],
  timeline: ["声音时间轴", "Audio timeline"],
  timelineHelp: [
    "拖动波形选择片段；单击定位试听。",
    "Drag to select a range. Click to seek.",
  ],
  undo: ["撤销", "Undo"],
  redo: ["重做", "Redo"],
  fit: ["适应", "Fit"],
  loop: ["循环选区", "Loop selection"],
  selection: ["选区（秒）", "Selection (seconds)"],
  from: ["从", "From"],
  to: ["到", "To"],
  all: ["全选", "Select all"],
  previews: ["预览与版本", "Previews & versions"],
  previewsHelp: [
    "先听一听，再决定是否采用。",
    "Listen first. Keep the version you like.",
  ],
  activity: ["操作记录", "Activity"],
  shared: ["界面 · MCP · Codex", "UI · MCP · Codex"],
  whatNext: ["想对声音做些什么？", "What would you like to do?"],
  clip: ["做个短片段", "Make a short clip"],
  clipCopy: ["截取选区，自动淡入淡出", "Trim the selection, add gentle fades"],
  normalize: ["调整峰值电平", "Set the peak level"],
  normalizeCopy: [
    "将最高峰值调整到 −1 dBFS",
    "Bring the highest peak to −1 dBFS",
  ],
  gain: ["音量增益", "Gain"],
  add: ["加入操作", "Add to recipe"],
  fade: ["淡入 / 淡出", "Fade in / out"],
  fadeIn: ["淡入", "Fade in"],
  fadeOut: ["淡出", "Fade out"],
  advanced: ["更多操作", "More operations"],
  balance: ["左右平衡", "Stereo balance"],
  trim: ["裁剪到选区", "Trim to selection"],
  reverse: ["倒放音频", "Reverse audio"],
  mix: ["人声与伴奏混音", "Mix vocals & backing"],
  vocals: ["人声 dB", "Vocals dB"],
  instrumental: ["伴奏 dB", "Backing dB"],
  recipe: ["待预览操作", "Preview recipe"],
  clear: ["清空", "Clear"],
  render: ["生成试听预览", "Render preview"],
  renderHelp: [
    "预览不会替换当前版本。",
    "Rendering leaves your current version unchanged.",
  ],
  inspect: ["声音检查", "Audio inspection"],
  meterHelp: [
    "当前显示样本峰值与整段 RMS，不能代替感知响度或真峰值测量。",
    "Sample peak and full-file RMS. These are not perceptual loudness or true peak.",
  ],
  notConnected: ["未连接", "Disconnected"],
  agentCopy: [
    "通过共享音频工具操作项目。连接后，生成的预览会出现在左侧。",
    "Work through shared audio tools. Agent previews appear alongside yours.",
  ],
  connectAgent: ["连接本机 Codex", "Connect local Codex"],
  agentPrompt: ["告诉 Codex 你想做什么", "Tell Codex what you want to do"],
  send: ["发送", "Send"],
  stop: ["停止", "Stop"],
  agentPrivacy: [
    "音频处理在本机；对话、读取的转写文字和工具结果会发送给 Codex 服务。不会自动上传音频文件。",
    "Audio processing stays local. Codex receives the conversation, transcripts it reads and tool results. Audio files are not uploaded automatically.",
  ],
  source: ["原始音频", "Original audio"],
  current: ["当前版本", "Current version"],
  vocalAsset: ["人声", "Vocals"],
  backingAsset: ["伴奏", "Backing"],
  listen: ["试听", "Listen"],
  adopt: ["采用", "Keep"],
  adopted: ["已采用", "Current"],
  stale: ["基于旧版本", "Older base"],
  failed: ["失败", "Failed"],
  rendering: ["正在渲染…", "Rendering…"],
  noPreviews: [
    "还没有预览。先选一个右侧任务，试听它会怎样改变声音。",
    "No previews yet. Choose a task on the right to hear what it changes.",
  ],
  noEvents: ["操作记录会显示在这里。", "Your activity will appear here."],
  noRecipe: ["还没有操作", "No operations yet"],
  preparing: ["正在准备音频…", "Preparing audio…"],
  previewReady: [
    "预览已生成，试听后可采用。",
    "Your preview is ready. Listen before keeping it.",
  ],
  adoptReady: [
    "已采用预览，可随时撤销。",
    "Preview kept. You can undo this at any time.",
  ],
  busy: ["正在处理…", "Working…"],
  save: ["保存", "Save"],
  cancel: ["取消", "Cancel"],
  deleteTitle: ["移入回收站？", "Move to trash?"],
  deleteCopy: [
    "项目和原始音频会保留在回收站，可恢复。",
    "The project and its original audio can be restored from Trash.",
  ],
  restore: ["恢复", "Restore"],
  emptyTrash: ["回收站为空。", "Trash is empty."],
  exportTitle: ["导出正在试听的音频", "Export the audio you are listening to"],
  exportCopy: [
    "导出正在试听的原音、预览或已采用版本。整数 WAV 若超过满幅会提示先降低音量。",
    "Export the audio you are listening to. Integer WAV requires peaks within full scale.",
  ],
  download: ["下载 WAV", "Download WAV"],
  clipInvalid: [
    "选区需要有有效的起止时间。",
    "Choose a valid selection first.",
  ],
  chooseProject: ["先选择一个项目。", "Select a project first."],
  peak: ["样本峰值", "Sample peak"],
  rms: ["整段 RMS", "Full-file RMS"],
  clipping: ["达到或超过满幅的样本", "Samples at or above full scale"],
  channels: ["声道", "Channels"],
  frames: ["采样帧数", "Sample frames"],
  newRemote: [
    "项目出现新版本，当前试听保持不变。",
    "A new version is available. Your current playback is unchanged.",
  ],
  connected: ["已连接", "Connected"],
  connecting: ["正在连接…", "Connecting…"],
  agentRunning: ["正在处理", "Working"],
  agentDone: ["已完成", "Complete"],
  recipeDownload: ["配方", "Recipe"],
  errorPrefix: ["操作未完成：", "Could not complete: "],
  playbackError: [
    "音频暂时无法播放，请重新选择音轨。",
    "Audio could not play. Select the track again.",
  ],
  importing: ["正在导入…", "Importing…"],
  emptyLibrary: ["还没有项目", "No projects yet"],
  createdBy: ["来自", "By"],
  recipeApplied: [
    "已加入操作，可生成预览。",
    "Recipe added. Render a preview to listen.",
  ],
  selectionTip: [
    "已截取选区并添加淡入淡出，可生成预览。",
    "Selection and fades added. Render a preview to listen.",
  ],
  previewsChange: ["预览生成完成", "Preview rendered"],
  adoptChange: ["采用预览", "Preview kept"],
  undoChange: ["撤销修改", "Edit undone"],
  redoChange: ["重做修改", "Edit redone"],
  exportChange: ["导出 WAV", "WAV exported"],
  previewAsset: ["试听预览", "Preview"],
  manualTools: ["手动操作", "Manual tools"],
  agentTools: ["Codex 助手", "Codex assistant"],
  selectionChange: ["更新选区", "Selection updated"],
  demoCredit: ["示例：", "Demo: "],
  previewFail: ["预览失败", "Preview failed"],
  previewStart: ["开始渲染预览", "Preview rendering started"],
};
const originSession = WorkbenchNavigation.identity(new URLSearchParams(location.search).get("session"));
let language = localStorage.getItem("station-language") || localStorage.getItem("musicStudioNextLanguage") || "zh";
if (!["zh", "en"].includes(language)) language = "zh";
const t = (key) => words[key]?.[language === "en" ? 1 : 0] || key;
const S = {
  projects: [],
  project: null,
  session: null,
  asset: null,
  info: null,
  waveform: [],
  selection: [0, 0],
  zoom: 1,
  viewStart: 0,
  operations: [],
  events: [],
  cursor: 0,
  busy: false,
  assetToken: 0,
  agentThread: null,
  agentCursor: 0,
  agentBusy: false,
  localModels: [],
  localTasks: [],
  taskSignature: "",
  pendingComparison: null,
  supportsCleanup: false,
  openedAt: Date.now() / 1000,
};
const audio = $("audio");
const transport = new window.AudioAssetTransport(audio);
audio.volume = 0.7;
const element = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
};
function translate() {
  document.documentElement.lang = language === "en" ? "en" : "zh-CN";
  $("lang").value = language;
  $("return-workstation").href = WorkbenchNavigation.workstation(originSession);
  $("return-workstation").textContent = t(originSession ? "returnSession" : "creationHome");
  document
    .querySelectorAll("[data-t]")
    .forEach((n) => (n.textContent = t(n.dataset.t)));
  document
    .querySelectorAll("[data-placeholder]")
    .forEach((n) => (n.placeholder = t(n.dataset.placeholder)));
  document
    .querySelectorAll("[data-title]")
    .forEach((n) => (n.title = t(n.dataset.title)));
  renderProjects();
  renderRecipe();
  renderLocalModels();
  renderLocalTasks();
  if (S.session) {
    renderSession();
    renderCandidates();
    renderEvents();
  }
  if (S.noticeTranslation)
    notice(t(S.noticeTranslation), S.noticeError, S.noticeSuffix);
  document.querySelectorAll("[data-agent-tool]").forEach(renderAgentTool);
}
function notice(message, error = false, suffix = "") {
  S.noticeError = error;
  S.noticeTranslation =
    Object.keys(words).find((key) => words[key].includes(message)) || null;
  S.noticeSuffix = suffix;
  const box = S.project ? $("notice") : $("global-notice");
  box.textContent = message + suffix;
  box.hidden = !message;
  box.classList.toggle("error", error);
}
async function api(path, method = "GET", body) {
  const options = { method };
  if (body !== undefined) {
    if (body instanceof FormData) options.body = body;
    else {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = response.statusText;
    }
    const error = new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail),
    );
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}
const base = () => `/api/projects/${S.project.id}/studio`;
function formatTime(value, precise = false) {
  value = Math.max(0, Number(value) || 0);
  const minutes = Math.floor(value / 60),
    seconds = Math.floor(value % 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}${precise ? "." + String(Math.floor((value % 1) * 100)).padStart(2, "0") : ""}`;
}
async function task(action) {
  if (S.busy) return;
  S.busy = true;
  updateButtons();
  if (S.session) renderCandidates();
  try {
    await action();
  } catch (error) {
    notice(t("errorPrefix") + error.message, true);
  } finally {
    S.busy = false;
    updateButtons();
    if (S.session) renderCandidates();
  }
}
function updateButtons() {
  $("welcome-import").disabled = S.busy;
  document
    .querySelectorAll("#projects button")
    .forEach((button) => (button.disabled = S.busy));
  for (const id of [
    "render",
    "export",
    "undo",
    "redo",
    "delete",
    "rename",
    "import",
    "demo",
    "speech-demo",
  ])
    $(id).disabled =
      S.busy ||
      (id === "export" && (!S.session || !S.info)) ||
      (id === "render" && !S.operations.length) ||
      (id === "undo" && !S.session?.can_undo) ||
      (id === "redo" && !S.session?.can_redo);
  $("render").textContent = t(S.busy ? "busy" : "render");
  $("play").disabled = !S.info;
  for (const id of [
    "start",
    "end",
    "quick-clip",
    "quick-normalize",
    "quick-loudness",
    "quick-cleanup",
    "add-gain",
    "add-fade",
    "add-pan",
    "add-trim",
    "add-reverse",
    "add-mix",
    "clear-recipe",
    "clear-selection",
  ])
    $(id).disabled = S.busy || !S.info;
  $("connect-agent").disabled = S.busy || !S.session;
  const selectedModel = S.localModels.find(
    (m) => m.id === $("local-model").value,
  );
  $("run-local").disabled =
    S.busy ||
    !S.info ||
    !$("local-model").value ||
    (selectedModel?.health.state !== "unchecked" &&
      selectedModel?.runnable === false);
}
async function loadProjects() {
  S.projects = await api("/api/projects");
  renderProjects();
}
function renderProjects() {
  const search = $("search").value.trim().toLowerCase();
  $("count").textContent = S.projects.length;
  const list = $("projects");
  list.replaceChildren();
  for (const p of S.projects.filter((p) =>
    p.title.toLowerCase().includes(search),
  )) {
    const item = element(
      "button",
      undefined,
      "project" + (S.project?.id === p.id ? " active" : ""),
    );
    item.title = p.title;
    const text = element("span", undefined, "project-text");
    text.append(
      element("strong", p.title),
      element("small", p.duration ? formatTime(p.duration) : "AUDIO"),
    );
    item.append(element("span", "≋", "project-symbol"), text);
    item.onclick = () => task(() => openProject(p.id));
    list.append(item);
  }
  if (!S.projects.length)
    list.append(element("div", t("emptyLibrary"), "empty"));
}
async function openProject(id) {
  S.pendingComparison = null;
  S.openedAt = Date.now() / 1000;
  $("open-comparison").hidden = true;
  transport.clear();
  S.assetToken++;
  S.project =
    S.projects.find((p) => p.id === id) || (await api(`/api/projects/${id}`));
  S.session = null;
  S.asset = null;
  S.info = null;
  S.operations = [];
  S.events = [];
  S.cursor = 0;
  S.zoom = 1;
  S.viewStart = 0;
  S.agentThread = null;
  S.agentCursor = 0;
  S.agentBusy = false;
  S.localTasks = [];
  S.taskSignature = "";
  renderLocalTasks();
  $("file-info").textContent = t("preparing");
  $("attribution").hidden = true;
  $("assets").replaceChildren();
  $("waveform").hidden = true;
  $("ruler").replaceChildren();
  $("revision").textContent = "—";
  $("time").textContent = "00:00.00";
  $("duration").textContent = "/ —";
  $("start").value = "0";
  $("end").value = "0";
  $("selection-duration").textContent = "";
  $("loop").checked = false;
  $("candidate-count").textContent = "0";
  $("candidates").replaceChildren(element("div", t("preparing"), "empty"));
  $("events").replaceChildren();
  updateButtons();
  $("agent-messages").replaceChildren();
  $("agent-form").hidden = true;
  $("connect-agent").hidden = false;
  setAgentStatus("notConnected");
  $("welcome").hidden = true;
  $("editor").hidden = false;
  $("title").textContent = S.project.title;
  $("breadcrumb").textContent = S.project.title;
  history.replaceState(null, "", WorkbenchNavigation.editor(id, originSession));
  renderProjects();
  notice(t("preparing"));
  const session = await api(base());
  S.session = session;
  await selectAsset(session.active);
  renderSession();
  renderCandidates();
  renderRecipe();
  notice("");
  await pollEvents();
  await Promise.all([loadLocalModels(), pollLocalTasks()]);
}
async function selectAsset(asset, play = false) {
  const token = ++S.assetToken;
  const key = `${S.project.id}:${asset}`;
  if (transport.key !== key || !S.info || audio.error) {
    S.asset = asset;
    S.info = null;
    updateButtons();
    const data =
      asset === S.session.active
        ? S.session
        : await api(base() + `/assets/${encodeURIComponent(asset)}/info`);
    if (token !== S.assetToken) return;
    S.info = data.audio;
    S.waveform = data.waveform;
    $("waveform").hidden = false;
    S.selection =
      S.session.selection?.asset === asset
        ? [S.session.selection.start, S.session.selection.end]
        : [0, S.info.duration];
    S.zoom = 1;
    S.viewStart = 0;
    transport.bind(key, base() + `/assets/${encodeURIComponent(asset)}`, {
      retry: Boolean(audio.error),
    });
  } else S.asset = asset;
  renderSession();
  drawWave();
  await saveSelection();
  if (play) await audio.play();
}
function renderSession() {
  if (!S.session) return;
  const info = S.info || S.session.audio;
  $("title").textContent = S.project.title;
  $("breadcrumb").textContent = S.project.title;
  const credit = S.project.attribution;
  $("attribution").hidden = !credit;
  $("attribution").replaceChildren();
  if (credit) {
    $("attribution").append(
      document.createTextNode(
        t("demoCredit") + credit.title + " · " + credit.artist + " · ",
      ),
    );
    const link = element("a", credit.license);
    try {
      const url = new URL(credit.license_url);
      if (["https:", "http:"].includes(url.protocol)) link.href = url.href;
    } catch {
      /* Invalid attribution URLs remain plain text. */
    }
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    $("attribution").append(link);
  }
  $("file-info").textContent =
    `${formatTime(info.duration)}  ·  ${(info.sample_rate / 1000).toFixed(1)} kHz  ·  ${info.channels} ${t("channels")}  ·  WAV`;
  $("revision").textContent = `v${S.session.revision}`;
  $("duration").textContent = "/ " + formatTime(info.duration, true);
  const mix = availableMix();
  $("mix-panel").hidden = !mix;
  $("mix-source").textContent = mix
    ? `${language === "zh" ? "分轨来源" : "Stem set"} · ${mix.task.slice(-6)} · ${formatTime(mix.audio.duration)}`
    : "";
  const assets = $("assets");
  assets.replaceChildren();
  const choices = [["source", t("source")]];
  if (S.session.active !== "source")
    choices.push([S.session.active, t("current")]);
  if (S.asset?.startsWith("candidate:") && S.asset !== S.session.active)
    choices.push([S.asset, t("previewAsset")]);
  for (const a of S.session.assets.filter((a) => a !== "source"))
    choices.push([
      S.session.analysis_assets?.[a] || a,
      t(a === "vocals" ? "vocalAsset" : "backingAsset"),
    ]);
  for (const a of (S.session.registered_assets || [])
    .filter(
      (a) =>
        a.kind === "audio" &&
        a.role !== "cleanup-input" &&
        !choices.some(([key]) => key === `asset:${a.id}`),
    )
    .slice(0, 8))
    choices.push([`asset:${a.id}`, assetName(`asset:${a.id}`)]);
  if (
    S.asset?.startsWith("asset:") &&
    !choices.some(([key]) => key === S.asset)
  )
    choices.push([S.asset, assetName(S.asset)]);
  for (const [asset, label] of choices) {
    const button = element(
      "button",
      label,
      asset === S.asset ? "selected" : "",
    );
    button.onclick = () => task(() => selectAsset(asset));
    assets.append(button);
  }
  $("asset-label").textContent = assetName(S.asset);
  const peak = info.peak_dbfs;
  $("meter-fill").style.width =
    Math.max(0, Math.min(100, (((peak ?? -60) + 60) / 60) * 100)) + "%";
  $("meter-fill").style.background = info.peak > 1 ? "var(--danger)" : "";
  const dl = $("measurements");
  dl.replaceChildren();
  for (const [label, value] of [
    [t("peak"), peak === null ? "−∞ dBFS" : peak.toFixed(1) + " dBFS"],
    [
      t("rms"),
      info.rms_dbfs === null ? "−∞ dBFS" : info.rms_dbfs.toFixed(1) + " dBFS",
    ],
    [t("clipping"), info.samples_at_or_above_full_scale.toLocaleString()],
    [t("frames"), info.frames.toLocaleString()],
  ])
    dl.append(element("dt", label), element("dd", value));
  renderSelection();
  renderTaskSource();
  updateButtons();
}
function assetName(asset) {
  if (asset === "source") return t("source");
  if (asset === "vocals") return t("vocalAsset");
  if (asset === "instrumental") return t("backingAsset");
  if (asset?.startsWith("asset:")) {
    const found = S.session?.registered_assets?.find(
      (a) => `asset:${a.id}` === asset,
    );
    if (found) return roleName(found.role) + " · " + found.id.slice(0, 4);
  }
  return (
    t(asset === S.session.active ? "current" : "previewAsset") +
    " · " +
    (asset?.split(":")[1]?.slice(0, 6) || "")
  );
}
function opName(op) {
  switch (op.type) {
    case "trim":
      return `${t("trim")} · ${op.start.toFixed(2)}–${op.end.toFixed(2)} s`;
    case "gain":
      return `${t("gain")} ${op.db > 0 ? "+" : ""}${op.db} dB`;
    case "fade":
      return `${t("fade")} ${op.in_seconds || 0} / ${op.out_seconds || 0} s`;
    case "balance":
      return `${t("balance")} ${op.pan}`;
    case "normalize":
      return `${t("normalize")} ${op.peak_dbfs ?? -1} dBFS`;
    case "reverse":
      return t("reverse");
    case "keep":
      return t("keepAsset");
    case "loudness":
      return `${t("loudnessNormalize")} ${op.target_lufs ?? -16} LUFS · ${op.ceiling_dbtp ?? -1} dBTP`;
    case "mix":
      return (
        t("mix") +
        " · " +
        op.tracks.map((a) => `${a.asset} ${a.gain_db || 0} dB`).join(" / ")
      );
    default:
      return op.type;
  }
}
function renderRecipe() {
  const list = $("recipe");
  list.replaceChildren();
  S.operations.forEach((op, index) => {
    const row = element("li");
    const remove = element("button", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `${t("delete")} ${opName(op)}`);
    remove.onclick = () => {
      S.operations.splice(index, 1);
      renderRecipe();
    };
    row.append(element("span", `${index + 1}. ${opName(op)}`), remove);
    list.append(row);
  });
  if (!S.operations.length) list.append(element("li", t("noRecipe")));
  updateButtons();
}
function addOperation(op) {
  if (S.busy) return;
  if (S.operations.length >= 24) {
    notice("Maximum 24 operations per preview.", true);
    return;
  }
  S.operations.push(op);
  renderRecipe();
}
function selectedTrim() {
  const start = Number($("start").value),
    enteredEnd = Number($("end").value);
  const end =
    S.info && enteredEnd <= S.info.duration + 0.000501
      ? Math.min(enteredEnd, S.info.duration)
      : enteredEnd;
  if (!S.info || end <= start || start < 0 || end > S.info.duration + 0.00001)
    throw new Error(t("clipInvalid"));
  return { type: "trim", start, end };
}
function renderCandidates() {
  const list = $("candidates");
  list.replaceChildren();
  $("candidate-count").textContent = S.session.candidates.length;
  for (const c of S.session.candidates) {
    const active = S.session.active === `candidate:${c.id}`;
    const card = element(
      "div",
      undefined,
      "candidate" + (active ? " active" : ""),
    );
    const content = element("div");
    content.append(
      element("h3", c.operations.map(opName).join(" → ")),
      element(
        "p",
        `${c.audio ? formatTime(c.audio.duration) + " · " : ""}${t("createdBy")} ${c.actor.toUpperCase()} · v${c.base_revision} · ${new Date(c.created_at * 1000).toLocaleTimeString(language === "en" ? "en-US" : "zh-CN", { hour: "2-digit", minute: "2-digit" })}`,
      ),
    );
    const actions = element("div", undefined, "candidate-actions");
    if (c.status === "ready") {
      const listen = element("button", t("listen"), "quiet");
      listen.disabled = S.busy;
      listen.onclick = () => task(() => selectAsset(`candidate:${c.id}`, true));
      actions.append(listen);
      if (
        S.supportsCleanup &&
        !c.operations.some((op) => op.type === "trim") &&
        /^(source|asset:|candidate:)/.test(c.source_asset)
      ) {
        const compare = element("button", t("compare"), "quiet");
        compare.disabled = S.busy;
        compare.onclick = () =>
          task(() => openComparison(c.source_asset, `candidate:${c.id}`));
        actions.append(compare);
      }
      const loudness = c.processing?.find((step) => step.loudness)?.loudness;
      if (loudness) {
        const value = loudness.after.integrated_lufs;
        content.append(
          element(
            "p",
            `${t("integrated")} ${value === null ? "—" : value.toFixed(1)} LUFS · ${t("truePeak")} ${loudness.after.true_peak_dbtp?.toFixed(1) ?? "—"} dBTP`,
          ),
        );
        if (loudness.peak_limited)
          content.append(element("p", t("peakLimited"), "warm-note"));
      }
      const keep = element(
        "button",
        t(active ? "adopted" : "adopt"),
        active ? "quiet" : "primary",
      );
      keep.disabled =
        active || c.base_revision !== S.session.revision || S.busy;
      keep.title =
        !active && c.base_revision !== S.session.revision ? t("stale") : "";
      keep.onclick = () =>
        task(async () => {
          const session = await api(base() + "/adopt", "POST", {
            revision: S.session.revision,
            candidate: c.id,
          });
          S.session = session;
          await selectAsset(session.active);
          renderCandidates();
          notice(t("adoptReady"));
          await pollEvents();
        });
      actions.append(keep);
      const recipe = element("a", t("recipeDownload"));
      recipe.href = base() + `/recipe/${c.id}`;
      recipe.download = `recipe-${c.id}.json`;
      actions.append(recipe);
    } else
      actions.append(
        element(
          "span",
          t(c.status === "failed" ? "failed" : "rendering"),
          "badge",
        ),
      );
    card.append(content, actions);
    if (c.error) content.append(element("p", c.error));
    list.append(card);
  }
  if (!S.session.candidates.length)
    list.append(element("div", t("noPreviews"), "empty"));
}
function renderEvents() {
  const list = $("events");
  list.replaceChildren();
  const names = {
    "preview.started": "previewStart",
    "preview.ready": "previewsChange",
    "preview.failed": "previewFail",
    "preview.adopted": "adoptChange",
    "history.undo": "undoChange",
    "history.redo": "redoChange",
    "audio.exported": "exportChange",
    "selection.changed": "selectionChange",
    "transcript.corrected": "editTranscript",
    "comparison.prepared": "compare",
  };
  for (const e of [...S.events].reverse()) {
    const row = element("div", undefined, "event");
    row.append(
      element(
        "time",
        new Date(e.created * 1000).toLocaleTimeString(
          language === "en" ? "en-US" : "zh-CN",
          { hour: "2-digit", minute: "2-digit", second: "2-digit" },
        ),
      ),
      element("strong", e.actor.toUpperCase()),
      element(
        "span",
        e.kind.startsWith("task.")
          ? t("localTasks") + " · " + t("state_" + e.kind.split(".")[1])
          : t(names[e.kind] || e.kind),
      ),
    );
    list.append(row);
  }
  if (!S.events.length) list.append(element("div", t("noEvents"), "empty"));
}
async function pollEvents() {
  if (!S.project || !S.session || S.busy) return;
  const project = S.project.id;
  const events = await api(base() + `/events?after=${S.cursor}`);
  if (S.project?.id !== project || !events.length) return;
  S.cursor = events.at(-1).seq;
  S.events.push(...events);
  S.events = S.events.slice(-150);
  renderEvents();
  const comparison = events
    .filter((e) => e.kind === "comparison.prepared" && e.created >= S.openedAt)
    .at(-1);
  if (comparison) {
    S.pendingComparison = comparison.data;
    $("open-comparison").hidden = false;
    if (!$("modal").open)
      await openComparison(
        comparison.data.reference,
        comparison.data.processed,
      );
    else notice(t("compareReady"));
  }
  const selected = events
    .filter((e) => e.kind === "selection.changed" && e.actor !== "ui")
    .at(-1);
  if (selected && selected.data.asset === S.asset) {
    S.selection = [selected.data.start, selected.data.end];
    renderSelection();
    drawWave();
  }
  if (
    events.some((e) =>
      [
        "preview.ready",
        "preview.failed",
        "preview.adopted",
        "history.undo",
        "history.redo",
        "task.complete",
        "transcript.corrected",
      ].includes(e.kind),
    )
  ) {
    const previous = S.session;
    const session = await api(base());
    if (S.project?.id !== project) return;
    S.session = session;
    if (previous.active !== session.active) {
      if (audio.paused && S.asset === previous.active)
        await selectAsset(session.active);
      else notice(t("newRemote"));
    }
    renderSession();
    renderCandidates();
    renderLocalTasks();
  }
}
async function saveSelection() {
  if (!S.session || !S.info) return;
  const session = S.session,
    project = S.project.id,
    asset = S.asset;
  try {
    const selected = await api(
      `/api/projects/${project}/studio/selection`,
      "POST",
      {
        revision: session.revision,
        asset,
        start: S.selection[0],
        end: S.selection[1],
      },
    );
    if (S.session === session && S.asset === asset)
      session.selection = selected;
  } catch (e) {
    if (S.project?.id === project) notice(e.message, true);
  }
}
function renderSelection() {
  $("start").value = S.selection[0].toFixed(3);
  $("end").value = S.selection[1].toFixed(3);
  $("selection-duration").textContent =
    (S.selection[1] - S.selection[0]).toFixed(3) + " s";
}
function drawWave() {
  if (!S.info) return;
  const canvas = $("waveform"),
    ratio = window.devicePixelRatio || 1,
    rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const w = rect.width,
    h = rect.height,
    duration = S.info.duration,
    span = duration / S.zoom;
  S.viewStart = Math.max(0, Math.min(duration - span, S.viewStart));
  const x = (time) => ((time - S.viewStart) / span) * w;
  ctx.fillStyle = "#141a21";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#26313b";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 6; i++) {
    const gx = (w * i) / 6;
    ctx.beginPath();
    ctx.moveTo(gx, 0);
    ctx.lineTo(gx, h);
    ctx.stroke();
  }
  const sx = x(S.selection[0]),
    ex = x(S.selection[1]);
  ctx.fillStyle = "#a8d8c812";
  ctx.fillRect(Math.max(0, sx), 0, Math.min(w, ex) - Math.max(0, sx), h);
  const n = S.waveform.length,
    step = 3;
  for (let px = 0; px < w; px += step) {
    const time = S.viewStart + (px / w) * span;
    const a = Math.max(0, Math.floor((time / duration) * n)),
      b = Math.min(
        n,
        Math.max(a + 1, Math.ceil(((time + (step / w) * span) / duration) * n)),
      );
    let peak = 0;
    for (let i = a; i < b; i++) peak = Math.max(peak, S.waveform[i]);
    const height = Math.max(1, Math.min(h * 0.84, peak * h * 0.85));
    ctx.fillStyle =
      time >= S.selection[0] && time <= S.selection[1] ? "#a0cbbc" : "#4a645d";
    ctx.fillRect(px, h / 2 - height / 2, 1.7, height);
  }
  ctx.strokeStyle = "#91c9b8";
  for (const edge of [sx, ex]) {
    if (edge >= 0 && edge <= w) {
      ctx.beginPath();
      ctx.moveTo(edge, 0);
      ctx.lineTo(edge, h);
      ctx.stroke();
    }
  }
  const cursor = x(audio.currentTime);
  if (cursor >= 0 && cursor <= w) {
    ctx.strokeStyle = "#efd8b5";
    ctx.beginPath();
    ctx.moveTo(cursor, 0);
    ctx.lineTo(cursor, h);
    ctx.stroke();
    ctx.fillStyle = "#efd8b5";
    ctx.fillRect(cursor - 3, 0, 6, 5);
  }
  const ruler = $("ruler");
  ruler.replaceChildren();
  for (let i = 0; i <= 6; i++)
    ruler.append(element("span", formatTime(S.viewStart + (span * i) / 6)));
}
let drag = null;
function pointerTime(event) {
  const rect = $("waveform").getBoundingClientRect();
  return Math.max(
    0,
    Math.min(
      S.info.duration,
      S.viewStart +
        (((event.clientX - rect.left) / rect.width) * S.info.duration) / S.zoom,
    ),
  );
}
$("waveform").addEventListener("pointerdown", (e) => {
  if (!S.info || S.busy) return;
  drag = { time: pointerTime(e), x: e.clientX, selection: [...S.selection] };
  $("waveform").setPointerCapture(e.pointerId);
});
$("waveform").addEventListener("pointermove", (e) => {
  if (!drag) return;
  const now = pointerTime(e);
  S.selection = [Math.min(drag.time, now), Math.max(drag.time, now)];
  renderSelection();
  drawWave();
});
$("waveform").addEventListener("pointerup", (e) => {
  if (!drag) return;
  const now = pointerTime(e);
  if (Math.abs(e.clientX - drag.x) < 4) {
    S.selection = drag.selection;
    audio.currentTime = now;
  } else {
    S.selection = [Math.min(drag.time, now), Math.max(drag.time, now)];
    audio.currentTime = S.selection[0];
  }
  drag = null;
  renderSelection();
  drawWave();
  saveSelection();
});
$("waveform").addEventListener("pointercancel", () => {
  if (drag) S.selection = drag.selection;
  drag = null;
  renderSelection();
  drawWave();
});
let selectionTimer;
function inputSelection(showError = false) {
  if (!S.info) return;
  const start = Number($("start").value),
    enteredEnd = Number($("end").value);
  const end =
    enteredEnd <= S.info.duration + 0.000501
      ? Math.min(enteredEnd, S.info.duration)
      : enteredEnd;
  if (
    !Number.isFinite(start) ||
    !Number.isFinite(end) ||
    start < 0 ||
    end > S.info.duration ||
    end <= start
  ) {
    if (showError) notice(t("clipInvalid"), true);
    return;
  }
  S.selection = [start, end];
  $("selection-duration").textContent = (end - start).toFixed(3) + " s";
  drawWave();
  clearTimeout(selectionTimer);
  selectionTimer = setTimeout(saveSelection, 150);
}
for (const id of ["start", "end"]) {
  $(id).oninput = () => inputSelection();
  $(id).onchange = () => inputSelection(true);
}
$("clear-selection").onclick = () => {
  if (!S.info) return;
  S.selection = [0, S.info.duration];
  renderSelection();
  drawWave();
  saveSelection();
};
$("zoom-in").onclick = () => {
  if (!S.info) return;
  S.zoom = Math.min(32, S.zoom * 2);
  S.viewStart = Math.max(0, audio.currentTime - S.info.duration / S.zoom / 2);
  drawWave();
};
$("zoom-out").onclick = () => {
  S.zoom = Math.max(1, S.zoom / 2);
  drawWave();
};
$("fit").onclick = () => {
  S.zoom = 1;
  S.viewStart = 0;
  drawWave();
};
async function togglePlay() {
  if (!S.info) return;
  if (!audio.paused) audio.pause();
  else {
    if (
      audio.currentTime >= S.selection[1] ||
      audio.currentTime < S.selection[0]
    )
      audio.currentTime = S.selection[0];
    try {
      await audio.play();
    } catch (e) {
      notice(t("playbackError") + " " + e.message, true);
    }
  }
}
$("play").onclick = togglePlay;
audio.addEventListener("play", () => {
  $("play").textContent = "Ⅱ";
});
audio.addEventListener("pause", () => {
  $("play").textContent = "▶";
});
audio.addEventListener("timeupdate", () => {
  if (
    $("loop").checked &&
    S.selection[1] > S.selection[0] &&
    audio.currentTime >= S.selection[1]
  )
    audio.currentTime = S.selection[0];
  $("time").textContent = formatTime(audio.currentTime, true);
  drawWave();
});
audio.addEventListener("error", () => {
  if (audio.src) notice(t("playbackError"), true);
});
audio.addEventListener("ended", () => {
  if ($("loop").checked && S.selection[1] > S.selection[0]) {
    audio.currentTime = S.selection[0];
    audio
      .play()
      .catch((error) => notice(t("playbackError") + " " + error.message, true));
  }
});
$("volume").oninput = () => {
  audio.volume = Number($("volume").value);
};
document.addEventListener("keydown", (e) => {
  if (
    e.code === "Space" &&
    !["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(e.target.tagName) &&
    !$("modal").open
  ) {
    e.preventDefault();
    togglePlay();
  }
});
window.addEventListener("resize", drawWave);
$("gain").oninput = () => {
  $("gain-value").textContent = Number($("gain").value) + " dB";
};
$("pan").oninput = () => {
  $("pan-value").textContent = $("pan").value;
};
$("add-gain").onclick = () =>
  addOperation({ type: "gain", db: Number($("gain").value) });
$("add-pan").onclick = () =>
  addOperation({ type: "balance", pan: Number($("pan").value) });
$("add-fade").onclick = () =>
  addOperation({
    type: "fade",
    in_seconds: Number($("fade-in").value),
    out_seconds: Number($("fade-out").value),
  });
$("add-reverse").onclick = () => addOperation({ type: "reverse" });
$("add-trim").onclick = () => {
  try {
    addOperation(selectedTrim());
  } catch (e) {
    notice(e.message, true);
  }
};
$("quick-normalize").onclick = () =>
  addOperation({ type: "normalize", peak_dbfs: -1 });
$("quick-clip").onclick = () => {
  try {
    const trim = selectedTrim();
    if (trim.end - trim.start === S.info.duration)
      trim.end = Math.min(trim.end, trim.start + 30);
    S.operations = [
      trim,
      {
        type: "fade",
        in_seconds: Math.min(0.3, (trim.end - trim.start) / 4),
        out_seconds: Math.min(1, (trim.end - trim.start) / 4),
      },
    ];
    renderRecipe();
    notice(t("selectionTip"));
  } catch (e) {
    notice(e.message, true);
  }
};
$("add-mix").onclick = () => {
  const mix = availableMix();
  if (!mix) return;
  if (S.operations.length) {
    notice(
      language === "zh"
        ? "混音将成为新配方的第一步。"
        : "Mixing starts a new recipe.",
    );
    S.operations = [];
  }
  addOperation({
    type: "mix",
    tracks: [
      {
        asset: mix.vocals,
        gain_db: Number($("vocal-gain").value),
        pan: 0,
      },
      {
        asset: mix.instrumental,
        gain_db: Number($("instrumental-gain").value),
        pan: 0,
      },
    ],
  });
};
$("clear-recipe").onclick = () => {
  S.operations = [];
  renderRecipe();
};
$("render").onclick = () =>
  task(async () => {
    const result = await api(base() + "/preview", "POST", {
      revision: S.session.revision,
      asset: S.asset,
      operations: S.operations,
    });
    S.session = await api(base());
    renderCandidates();
    await selectAsset(`candidate:${result.id}`);
    S.operations = [];
    renderRecipe();
    notice(t("previewReady"));
  });
for (const direction of ["undo", "redo"])
  $(direction).onclick = () =>
    task(async () => {
      S.session = await api(base() + `/history/${direction}`, "POST", {
        revision: S.session.revision,
      });
      await selectAsset(S.session.active);
      renderCandidates();
    });
function modal(title, body, actions = []) {
  $("modal-title").textContent = title;
  $("modal-body").replaceChildren(...body);
  $("modal-actions").replaceChildren();
  for (const [label, action, primary] of actions) {
    const button = element("button", label, primary ? "primary" : "quiet");
    button.type = "button";
    button.onclick = action;
    $("modal-actions").append(button);
  }
  $("modal").showModal();
}
$("rename").onclick = () => {
  const input = element("input");
  input.value = S.project.title;
  input.maxLength = 120;
  input.setAttribute("aria-label", t("rename"));
  modal(
    t("rename"),
    [input],
    [
      [
        t("save"),
        () =>
          task(async () => {
            S.project = await api(`/api/projects/${S.project.id}`, "PATCH", {
              title: input.value,
            });
            await loadProjects();
            renderSession();
            $("modal").close();
          }),
        true,
      ],
    ],
  );
  input.focus();
  input.select();
};
$("delete").onclick = () =>
  modal(
    t("deleteTitle"),
    [element("p", t("deleteCopy"))],
    [
      [t("cancel"), () => $("modal").close()],
      [
        t("delete"),
        () =>
          task(async () => {
            audio.pause();
            await api(`/api/projects/${S.project.id}`, "DELETE");
            S.project = null;
            S.session = null;
            S.info = null;
            transport.clear();
            $("modal").close();
            await loadProjects();
            if (S.projects.length) await openProject(S.projects[0].id);
            else {
              $("editor").hidden = true;
              $("welcome").hidden = false;
              history.replaceState(null, "", WorkbenchNavigation.editor(null, originSession));
            }
          }),
        true,
      ],
    ],
  );
$("trash").onclick = () =>
  task(async () => {
    const items = await api("/api/trash"),
      body = [];
    for (const item of items) {
      const row = element("div", undefined, "trash-item"),
        restore = element("button", t("restore"), "quiet");
      restore.type = "button";
      restore.onclick = () =>
        task(async () => {
          await api(`/api/trash/${item.id}/restore`, "POST");
          await loadProjects();
          $("modal").close();
          await openProject(item.id);
        });
      row.append(element("span", item.title), restore);
      body.push(row);
    }
    if (!body.length) body.push(element("p", t("emptyTrash")));
    modal(t("trash"), body);
  });
$("export").onclick = () => {
  const select = element("select");
  select.setAttribute("aria-label", "WAV encoding");
  for (const [value, label] of [
    ["PCM_24", "WAV · 24-bit PCM"],
    ["PCM_16", "WAV · 16-bit PCM"],
    ["FLOAT", "WAV · 32-bit float"],
  ]) {
    const option = element("option", label);
    option.value = value;
    select.append(option);
  }
  modal(
    t("exportTitle"),
    [element("p", t("exportCopy")), select],
    [
      [
        t("download"),
        () =>
          task(async () => {
            const result = await api(base() + "/export", "POST", {
              revision: S.session.revision,
              asset: S.asset,
              subtype: select.value,
            });
            const a = element("a");
            a.href = result.url;
            a.download = `${S.project.title}.wav`;
            document.body.append(a);
            a.click();
            a.remove();
            $("modal").close();
            notice(
              t("exportChange"),
              false,
              ` · ${formatTime(result.audio.duration)} · ${select.value}`,
            );
          }),
        true,
      ],
    ],
  );
};
async function importFile(file) {
  if (!file) return;
  await task(async () => {
    notice(t("importing"));
    const body = new FormData();
    body.append("file", file);
    const record = await api("/api/projects", "POST", body);
    await loadProjects();
    await openProject(record.id);
  });
  $("file").value = "";
}
$("import").onclick = $("welcome-import").onclick = () => $("file").click();
$("file").onchange = () => importFile($("file").files[0]);
$("demo").onclick = () =>
  task(async () => {
    const record = await api("/api/demo", "POST");
    await loadProjects();
    await openProject(record.id);
  });
$("speech-demo").onclick = () =>
  task(async () => {
    const record = await api("/api/studio/demo/speech", "POST");
    await loadProjects();
    await openProject(record.id);
  });
document.addEventListener("dragover", (e) => {
  if (e.dataTransfer.types.includes("Files")) {
    e.preventDefault();
    $("drop").classList.add("dragging");
  }
});
document.addEventListener("dragleave", (e) => {
  if (!e.relatedTarget) $("drop").classList.remove("dragging");
});
document.addEventListener("drop", (e) => {
  e.preventDefault();
  $("drop").classList.remove("dragging");
  if (e.dataTransfer.files.length) importFile(e.dataTransfer.files[0]);
});
$("search").oninput = renderProjects;
$("lang").onchange = () => {
  language = $("lang").value;
  localStorage.setItem("station-language", language);
  translate();
};
function localized(value) {
  return Array.isArray(value) ? value[language === "en" ? 1 : 0] : value;
}
function availableMix() {
  if (!S.info) return null;
  const pairs = (S.session?.mix_pairs || []).filter((pair) =>
    ["frames", "sample_rate", "channels"].every(
      (key) => pair.audio[key] === S.info[key],
    ),
  );
  return (
    pairs.find((pair) => [pair.vocals, pair.instrumental].includes(S.asset)) ||
    pairs[0] ||
    null
  );
}
function roleName(role) {
  return (
    {
      vocals: t("vocalAsset"),
      instrumental: t("backingAsset"),
      "note-synthesis": t("synthesis"),
      levels: language === "zh" ? "电平报告" : "Level report",
      loudness: language === "zh" ? "响度报告" : "Loudness report",
      "cleanup-input": t("before"),
      "cleaned-speech": t("after"),
      "cleanup-report":
        language === "zh" ? "降噪与响度报告" : "Cleanup & loudness report",
      "lyrics-txt": language === "zh" ? "转写 TXT" : "Transcript TXT",
      "lyrics-lrc": "LRC",
      "lyrics-srt": "SRT",
      pitch: language === "zh" ? "音高轨迹" : "Pitch contour",
      lyrics: language === "zh" ? "可编辑转写" : "Editable transcript",
      midi: "MIDI",
      melody: language === "zh" ? "音符数据" : "Note data",
      rhythm: language === "zh" ? "节拍数据" : "Beat data",
    }[role] || role
  );
}
function renderTaskSource() {
  $("task-source").textContent = S.info
    ? `${t("taskSource")} · ${assetName(S.asset)} · ${formatTime(S.info.duration)}`
    : "";
}
function renderLocalModels() {
  const select = $("local-model"),
    previous = select.value;
  select.replaceChildren();
  for (const model of S.localModels) {
    const option = element("option", localized(model.title));
    option.value = model.id;
    select.append(option);
  }
  if (S.localModels.some((m) => m.id === previous)) select.value = previous;
  else if (S.localModels.some((m) => m.id === "demucs-htdemucs"))
    select.value = "demucs-htdemucs";
  renderModelDescription();
}
function renderModelDescription() {
  const model = S.localModels.find((m) => m.id === $("local-model").value);
  $("local-description").textContent = model
    ? localized(model.description) +
      (model.health.state !== "unchecked" && !model.runnable
        ? " " + t("modelNotReady")
        : "")
    : "";
  $("cleanup-strength-row").hidden = model?.stage !== "denoise";
  const cuda = $("local-device").querySelector('[value="cuda"]');
  cuda.disabled = model?.device === "cpu";
  if (cuda.disabled && $("local-device").value === "cuda")
    $("local-device").value = "cpu";
  updateButtons();
}
$("local-model").onchange = renderModelDescription;
async function loadLocalModels() {
  const models = await api("/api/studio/models");
  S.localModels = models;
  S.supportsCleanup = models.some((m) => m.id === "loudness-ebur128");
  for (const id of ["quick-cleanup", "quick-loudness", "speech-demo"])
    $(id).hidden = !S.supportsCleanup;
  renderLocalModels();
  updateButtons();
}
async function pollLocalTasks() {
  if (!S.project || !S.session || S.busy) return;
  const project = S.project.id,
    tasks = await api(base() + "/tasks");
  if (S.project?.id !== project) return;
  const signature = JSON.stringify(tasks);
  if (signature !== S.taskSignature) {
    S.localTasks = tasks;
    S.taskSignature = signature;
    renderLocalTasks();
    if (
      tasks.some((j) =>
        ["complete", "failed", "cancelled", "interrupted"].includes(j.status),
      )
    )
      await loadLocalModels();
    if (
      S.noticeTranslation === "taskQueued" &&
      tasks.every(
        (j) =>
          !["queued", "checking", "running", "cancelling"].includes(j.status),
      )
    )
      notice(t("tasksFinished"));
  }
}
function renderLocalTasks() {
  const list = $("local-tasks");
  list.replaceChildren();
  const rank = (job) =>
    ["checking", "running", "cancelling"].includes(job.status)
      ? 0
      : job.status === "queued"
        ? 1
        : 2;
  const ordered = [...S.localTasks].sort(
    (a, b) =>
      rank(a) - rank(b) ||
      (rank(a) === 1
        ? a.created_at - b.created_at
        : b.created_at - a.created_at),
  );
  for (const task of ordered.slice(0, 20)) {
    const card = element("article", undefined, "local-task");
    const title = element("div", undefined, "local-task-heading");
    const model = S.localModels.find((m) => m.id === task.model);
    const state =
      task.status === "failed" ? t("taskFailed") : t("state_" + task.status);
    title.append(
      element("strong", model ? localized(model.title) : task.model),
      element("span", state, "task-state " + task.status),
    );
    card.append(title);
    const duration = task.input_audio?.duration;
    card.append(
      element(
        "p",
        `${formatTime(duration)} · ${task.id.slice(0, 6)} · ${task.metrics?.device || task.device}${task.metrics ? " · " + task.metrics.seconds.toFixed(2) + " s" : ""}`,
        "subtle",
      ),
    );
    if (task.source_range?.scope === "clip")
      card.append(element("p", language === "zh"
        ? `源片段 ${task.source_range.start.toFixed(2)}–${task.source_range.end.toFixed(2)} s；结果时间从 0 开始。`
        : `Source clip ${task.source_range.start.toFixed(2)}–${task.source_range.end.toFixed(2)} s; result times start at zero.`, "subtle"));
    if (task.error)
      card.append(
        element(
          "p",
          task.error.split("\n").filter(Boolean).at(-1)?.slice(0, 350),
          "task-error",
        ),
      );
    if (["queued", "checking", "running", "cancelling"].includes(task.status)) {
      const cancel = element("button", t("cancel"), "quiet");
      cancel.disabled = task.status === "cancelling";
      const project = S.project?.id;
      cancel.onclick = async () => {
        cancel.disabled = true;
        try {
          await api(
            `/api/projects/${project}/studio/tasks/${task.id}/cancel`,
            "POST",
          );
          await pollLocalTasks();
        } catch (error) {
          notice(error.message, true);
          cancel.disabled = false;
        }
      };
      card.append(cancel);
    }
    const outputs = element("div", undefined, "task-artifacts");
    const artifacts = (S.session?.registered_assets || []).filter(
      (a) => a.task === task.id,
    );
    for (const artifact of artifacts.length
      ? artifacts
      : task.artifacts || []) {
      const row = element("div", undefined, "task-artifact");
      row.append(
        element(
          "span",
          roleName(artifact.role) +
            (artifact.transcript_revision
              ? ` · v${artifact.transcript_revision}`
              : ""),
        ),
      );
      const project = S.project?.id;
      const url = `/api/projects/${project}/studio/artifacts/${artifact.id}`;
      if (artifact.kind === "audio") {
        const listen = element("button", t("listen"), "quiet");
        listen.onclick = () =>
          taskAction(project, async () => {
            S.session = await api(base());
            await selectAsset(`asset:${artifact.id}`, true);
          });
        row.append(listen);
      } else if (["json", "transcript"].includes(artifact.kind)) {
        const view = element(
          "button",
          t(
            artifact.kind === "transcript" ? "editTranscript" : "inspectResult",
          ),
          "quiet",
        );
        view.onclick = async () => {
          try {
            if (artifact.kind === "transcript") {
              await openTranscriptEditor(project, artifact);
              return;
            }
            const result = await api(url);
            const pre = element(
              "pre",
              JSON.stringify(result, null, 2),
              "result-json",
            );
            if (artifact.role === "loudness") {
              modal(roleName(artifact.role), [
                loudnessCard(t("integrated"), result),
              ]);
            } else if (artifact.role === "cleanup-report") {
              const pair = element("div", undefined, "loudness-pair");
              pair.append(
                loudnessCard(t("before"), result.before),
                loudnessCard(t("after"), result.after),
              );
              const details = element("details");
              details.append(element("summary", t("taskDetails")), pre);
              modal(roleName(artifact.role), [
                pair,
                element("p", t("cleanupHelp"), "footnote"),
                details,
              ]);
            } else modal(roleName(artifact.role), [pre]);
          } catch (error) {
            notice(error.message, true);
          }
        };
        row.append(view);
      }
      const download = element("a", t("downloadFile"), "artifact-download");
      download.href = url + "?download=true";
      download.setAttribute("download", "");
      row.append(download);
      outputs.append(row);
    }
    if (outputs.children.length) card.append(outputs);
    const before = (task.artifacts || []).find(
      (a) => a.role === "cleanup-input",
    );
    const after = (task.artifacts || []).find(
      (a) => a.role === "cleaned-speech",
    );
    if (before && after) {
      const compare = element("button", t("compare"), "quiet");
      compare.onclick = () =>
        taskAction(S.project.id, () =>
          openComparison(`asset:${before.id}`, `asset:${after.id}`),
        );
      card.append(compare);
    }
    const diagnostics = element("details", undefined, "task-diagnostics");
    diagnostics.append(
      element("summary", t("taskDetails")),
      element(
        "pre",
        JSON.stringify(
          {
            input_sha256: task.input_sha256,
            base_revision: task.revision,
            runtime: task.runtime,
            metrics: task.metrics,
            error: task.error,
          },
          null,
          2,
        ),
      ),
    );
    card.append(diagnostics);
    list.append(card);
  }
  if (!S.localTasks.length)
    list.append(element("div", t("emptyTasks"), "empty"));
}
async function taskAction(project, action) {
  if (project !== S.project?.id) return;
  await task(action);
}
async function openTranscriptEditor(project, artifact) {
  const result = await api(
    `/api/projects/${project}/studio/artifacts/${artifact.id}`,
  );
  const fields = [],
    body = [element("p", t("transcriptHelp"))];
  const task = S.localTasks.find((task) => task.id === artifact.task);
  if (task) {
    audio.pause();
    const preview = element("audio");
    preview.controls = true;
    preview.preload = "metadata";
    preview.src = `/api/projects/${project}/studio/tasks/${task.id}/input`;
    preview.setAttribute("aria-label", language === "zh" ? "转写对应的音频片段" : "Audio used for this transcript");
    body.push(preview, element("p", language === "zh"
      ? "试听的是提交时的音频片段。下方时间从此片段的 0 秒开始。"
      : "Audition the captured task input. Times below start at zero within this audio.", "subtle"));
    $("modal").addEventListener("close", () => {
      preview.pause();
      preview.removeAttribute("src");
      preview.load();
    }, {once: true});
  }
  for (const line of result.segments) {
    const label = element("label", undefined, "transcript-line");
    const input = element("textarea");
    input.value = line.text;
    input.maxLength = 2000;
    input.rows = 2;
    input.setAttribute("aria-label", `${line.id} ${formatTime(line.start)}`);
    label.append(
      element(
        "span",
        `${formatTime(line.start, true)} → ${formatTime(line.end, true)}`,
      ),
      input,
    );
    fields.push({ id: line.id, text: line.text, input });
    body.push(label);
  }
  modal(t("editTranscript"), body, [
    [
      t("save"),
      () =>
        taskAction(project, async () => {
          const changes = Object.fromEntries(
            fields
              .filter((f) => f.input.value !== f.text)
              .map((f) => [f.id, f.input.value]),
          );
          if (!Object.keys(changes).length) {
            $("modal").close();
            return;
          }
          await api(
            `/api/projects/${project}/studio/transcripts/${artifact.id}`,
            "POST",
            { sha256: artifact.sha256, changes },
          );
          S.session = await api(base());
          renderLocalTasks();
          $("modal").close();
          notice(t("transcriptSaved"));
        }),
      true,
    ],
  ]);
}
$("run-local").onclick = () =>
  task(async () => {
    const project = S.project.id;
    await api(base() + "/tasks", "POST", {
      model: $("local-model").value,
      revision: S.session.revision,
      asset: S.asset,
      device: $("local-device").value,
      ...(S.localModels.find((m) => m.id === $("local-model").value)?.stage ===
      "denoise"
        ? { strength: Number($("cleanup-strength").value) }
        : {}),
    });
    const tasks = await api(base() + "/tasks");
    if (project !== S.project?.id) return;
    S.localTasks = tasks;
    S.taskSignature = JSON.stringify(tasks);
    renderLocalTasks();
    notice(t("taskQueued"));
  });

$("cleanup-strength").oninput = () => {
  $("cleanup-strength-value").textContent =
    Math.round(Number($("cleanup-strength").value) * 100) + "%";
};

function loudnessCard(title, levels) {
  const card = element("section", undefined, "loudness-card");
  card.append(element("h3", title));
  const values = [
    [t("integrated"), levels.integrated_lufs, "LUFS"],
    [t("truePeak"), levels.true_peak_dbtp, "dBTP"],
    [t("loudnessRange"), levels.loudness_range_lu, "LU"],
  ];
  const list = element("dl");
  for (const [label, value, unit] of values) {
    list.append(
      element("dt", label),
      element("dd", value === null ? "—" : `${value.toFixed(1)} ${unit}`),
    );
  }
  card.append(list);
  if (levels.integrated_lufs === null)
    card.append(element("p", t("unmeasurable"), "footnote"));
  if (!levels.loudness_range_stable)
    card.append(element("p", t("provisionalLra"), "footnote"));
  return card;
}

async function openComparison(reference, processed) {
  const project = S.project?.id;
  if (!project || $("modal").open) return;
  const metadata = await api(base() + "/compare", "POST", {
    reference,
    processed,
  });
  if (S.project?.id !== project || $("modal").open) return;
  S.pendingComparison = {
    reference: metadata.reference,
    processed: metadata.processed,
  };
  $("open-comparison").hidden = false;
  audio.pause();
  const wrapper = element("div", undefined, "comparison-panel");
  const cards = element("div", undefined, "loudness-pair");
  cards.append(
    loudnessCard("A · " + t("before"), metadata.a.levels),
    loudnessCard("B · " + t("after"), metadata.b.levels),
  );
  const controls = element("div", undefined, "comparison-controls");
  const aButton = element("button", "A · " + t("before"));
  const bButton = element("button", "B · " + t("after"));
  const play = element("button", "▶ " + t("comparePlay"), "primary");
  for (const button of [aButton, bButton, play]) {
    button.type = "button";
    button.disabled = true;
  }
  controls.append(aButton, bButton, play);
  const position = element("input");
  position.type = "range";
  position.min = "0";
  position.max = String(metadata.duration);
  position.step = "0.01";
  position.value = "0";
  position.setAttribute("aria-label", t("comparePosition"));
  position.disabled = true;
  const clock = element(
    "p",
    `00:00.00 / ${formatTime(metadata.duration, true)}`,
    "subtle",
  );
  const matchLabel = element("label", undefined, "check");
  const match = element("input");
  match.type = "checkbox";
  match.checked = metadata.matching_available;
  match.disabled = !metadata.matching_available;
  matchLabel.append(match, element("span", t("matchLoudness")));
  const volume = element("input");
  volume.type = "range";
  volume.min = "0";
  volume.max = "1";
  volume.step = "0.01";
  volume.value = "0.7";
  volume.setAttribute("aria-label", t("playbackVolume"));
  const volumeLabel = element("label", undefined, "comparison-volume");
  volumeLabel.append(element("span", "♫"), volume);
  const media = [element("audio"), element("audio")];
  for (const node of media) node.hidden = true;
  const status = element("p", t("compareLoading"), "subtle");
  status.setAttribute("role", "status");
  wrapper.append(
    cards,
    status,
    controls,
    position,
    clock,
    matchLabel,
    volumeLabel,
    element("p", t("compareHelp"), "footnote"),
    ...media,
  );
  let closed = false;
  const player = new window.MatchedABPlayer(
    media[0],
    media[1],
    metadata,
    (p) => {
      if (closed) return;
      aButton.setAttribute("aria-pressed", String(p.side === "a"));
      bButton.setAttribute("aria-pressed", String(p.side === "b"));
      play.textContent = (p.current.paused ? "▶ " : "Ⅱ ") + t("comparePlay");
      position.value = String(p.current.currentTime);
      clock.textContent = `${formatTime(p.current.currentTime, true)} / ${formatTime(p.duration, true)}`;
    },
  );
  player.setVolume(audio.volume);
  volume.value = String(audio.volume);
  const action = (fn) => async () => {
    try {
      await fn();
    } catch (error) {
      if (!closed) {
        status.hidden = false;
        status.textContent = t("playbackError") + " " + error.message;
      }
    }
  };
  play.onclick = action(() =>
    player.current.paused ? player.play() : player.pause(),
  );
  aButton.onclick = action(() => player.select("a"));
  bButton.onclick = action(() => player.select("b"));
  match.onchange = () => player.setMatching(match.checked);
  volume.oninput = () => player.setVolume(Number(volume.value));
  position.oninput = () => player.seek(Number(position.value));
  const ready = () => {
    const available = media.every(
      (node) => node.readyState >= 1 && !node.error,
    );
    for (const button of [aButton, bButton, play]) button.disabled = !available;
    position.disabled = !available;
    if (available) {
      status.hidden = true;
      player.onChange(player);
    }
  };
  for (const node of media) {
    node.addEventListener("loadedmetadata", ready);
    node.addEventListener("error", () => {
      if (!closed) {
        status.hidden = false;
        status.textContent = t("playbackError");
      }
      ready();
    });
  }
  modal(
    t("compare"),
    [wrapper],
    [
      [
        t("createPreview"),
        () =>
          taskAction(project, async () => {
            const preview = await api(base() + "/preview", "POST", {
              revision: S.session.revision,
              asset: metadata.processed,
              operations: [{ type: "keep" }],
            });
            S.session = await api(base());
            $("modal").close();
            await selectAsset(`candidate:${preview.id}`);
            renderCandidates();
            notice(t("previewReady"));
          }),
        true,
      ],
    ],
  );
  $("modal").addEventListener(
    "close",
    () => {
      closed = true;
      audio.volume = player.volume;
      $("volume").value = String(player.volume);
      player.dispose();
    },
    { once: true },
  );
  ready();
}

$("open-comparison").onclick = () =>
  task(() =>
    openComparison(
      S.pendingComparison.reference,
      S.pendingComparison.processed,
    ),
  );
$("quick-loudness").onclick = () => {
  const project = S.project?.id;
  if (!project) return;
  const target = element("input");
  target.type = "number";
  target.min = "-36";
  target.max = "-9";
  target.step = "0.5";
  target.value = "-16";
  target.required = true;
  const ceiling = element("input");
  ceiling.type = "number";
  ceiling.min = "-6";
  ceiling.max = "-0.1";
  ceiling.step = "0.1";
  ceiling.value = "-1";
  ceiling.required = true;
  const a = element("label", undefined, "transcript-line"),
    b = element("label", undefined, "transcript-line");
  a.append(element("span", t("targetLoudness")), target);
  b.append(element("span", t("peakCeiling")), ceiling);
  modal(
    t("loudnessNormalize"),
    [element("p", t("loudnessHelp")), a, b],
    [
      [
        t("render"),
        () =>
          taskAction(project, async () => {
            if (
              !target.checkValidity() ||
              !ceiling.checkValidity() ||
              !target.value ||
              !ceiling.value
            ) {
              target.reportValidity();
              ceiling.reportValidity();
              return;
            }
            const result = await api(base() + "/preview", "POST", {
              revision: S.session.revision,
              asset: S.asset,
              operations: [
                {
                  type: "loudness",
                  target_lufs: Number(target.value),
                  ceiling_dbtp: Number(ceiling.value),
                },
              ],
            });
            S.session = await api(base());
            $("modal").close();
            await selectAsset(`candidate:${result.id}`);
            renderCandidates();
            notice(
              t(
                result.processing?.[0]?.loudness?.peak_limited
                  ? "peakLimited"
                  : "previewReady",
              ),
            );
          }),
        true,
      ],
    ],
  );
};
$("quick-cleanup").onclick = () => {
  const project = S.project?.id;
  if (!project) return;
  const choose = element("select");
  choose.setAttribute("aria-label", t("cleanupModel"));
  for (const entry of S.localModels.filter((m) => m.stage === "denoise")) {
    const option = element("option", localized(entry.title));
    option.value = entry.id;
    choose.append(option);
  }
  if ([...choose.options].some((o) => o.value === "dpdfnet2-48k"))
    choose.value = "dpdfnet2-48k";
  const modelLabel = element("label", undefined, "transcript-line");
  modelLabel.append(element("span", t("cleanupModel")), choose);
  const input = element("input");
  input.type = "range";
  input.min = "0";
  input.max = "1";
  input.step = "0.05";
  input.value = "1";
  input.setAttribute("aria-label", t("cleanupStrength"));
  const label = element("label", undefined, "transcript-line");
  const caption = element("span", t("cleanupStrength") + " · 100%");
  input.oninput = () => {
    caption.textContent =
      t("cleanupStrength") +
      " · " +
      Math.round(Number(input.value) * 100) +
      "%";
  };
  label.append(caption, input);
  const status = element("p", "", "footnote");
  const body = [
    element("p", t("cleanupHelp")),
    modelLabel,
    label,
    status,
    element(
      "p",
      `${t("taskSource")} · ${assetName(S.asset)} · ${formatTime(S.info.duration)}`,
      "subtle",
    ),
  ];
  const actionLabel = () => {
    const model = S.localModels.find((m) => m.id === choose.value);
    return t(model?.runnable ? "runLocal" : "installAndRun");
  };
  const refresh = () => {
    const model = S.localModels.find((m) => m.id === choose.value);
    status.textContent = model?.runnable
      ? ""
      : `${t("firstModelDownload")}${((model?.download_bytes || 0) / 1024 ** 2).toFixed(2)} MiB · ${model?.license || ""}`;
    const action = $("modal-actions").querySelector("button");
    if (action) {
      action.textContent = actionLabel();
      action.disabled = !model;
    }
  };
  const queue = () =>
    taskAction(project, async () => {
      const model = S.localModels.find((m) => m.id === choose.value);
      const asset = S.asset,
        revision = S.session.revision;
      const action = $("modal-actions").querySelector("button");
      choose.disabled = true;
      input.disabled = true;
      action.disabled = true;
      try {
        if (!model.runnable) {
          status.textContent = t("installingWeights");
          const result = await api(
            `/api/studio/models/${model.id}/install`,
            "POST",
          );
          S.localModels = S.localModels.map((m) =>
            m.id === result.id ? result : m,
          );
          renderLocalModels();
        }
        if (
          project !== S.project?.id ||
          !modelLabel.isConnected ||
          !$("modal").open
        )
          return;
        await api(`/api/projects/${project}/studio/tasks`, "POST", {
          revision,
          model: model.id,
          asset,
          device: "cpu",
          strength: Number(input.value),
        });
        S.localTasks = await api(`/api/projects/${project}/studio/tasks`);
        if (project !== S.project?.id) return;
        S.taskSignature = JSON.stringify(S.localTasks);
        $("modal").close();
        renderLocalTasks();
        notice(t("taskQueued"));
      } catch (error) {
        status.textContent = error.message;
        throw error;
      } finally {
        choose.disabled = false;
        input.disabled = false;
        action.disabled = false;
        action.textContent = actionLabel();
      }
    });
  modal(t("cleanupSpeech"), body, [[actionLabel(), queue, true]]);
  choose.onchange = refresh;
  refresh();
};
$("models").onclick = async () => {
  try {
    await loadLocalModels();
    const guide = element("a", t("modelsSetup"));
    guide.href = `https://github.com/Hydr0g3ngz/music-workbench/blob/main/docs/models${language === "en" ? ".en" : ""}.md`;
    guide.target = "_blank";
    guide.rel = "noopener noreferrer";
    const body = [element("p", t("modelHelp")), guide];
    for (const model of S.localModels) {
      const card = element("div", undefined, "model-card");
      const status = element("p", "", "subtle"),
        details = element("pre", "", "model-diagnostic");
      const renderHealth = (value) => {
        status.textContent = t("state_" + value.health.state);
        if (value.health.weights !== null && value.health.weights !== undefined)
          status.textContent +=
            " · " +
            t(
              value.health.weight_files === 0
                ? "weightsNone"
                : value.health.weights
                  ? "weightsCached"
                  : "weightsMissing",
            );
        details.textContent =
          value.health.error ||
          (value.health.missing?.length
            ? value.health.missing.join(", ")
            : Object.entries(value.health.versions || {})
                .map(([k, v]) => `${k} ${v}`)
                .join(" · "));
      };
      renderHealth(model);
      const source = element("a", model.license);
      source.href = model.source;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      const check = element("button", t("modelCheck"), "quiet");
      check.type = "button";
      check.onclick = async () => {
        check.disabled = true;
        check.textContent = t("modelChecking");
        try {
          const result = await api(
            `/api/studio/models/${model.id}/check`,
            "POST",
          );
          renderHealth(result);
          S.localModels = S.localModels.map((m) =>
            m.id === result.id ? result : m,
          );
          renderModelDescription();
        } catch (error) {
          details.textContent = error.message;
        } finally {
          check.disabled = false;
          check.textContent = t("modelCheck");
        }
      };
      card.append(
        element("strong", localized(model.title)),
        element("p", localized(model.description)),
        status,
        source,
        check,
        details,
      );
      if (model.setup_url && !model.runnable) {
        const setup = element("a", localized(["安装运行环境与模型 →", "Set up runtime and model →"]));
        setup.href = model.setup_url;
        card.append(setup);
      }
      if (model.installable_weights) {
        const installLabel = `${t("installCleanup")} · ${(model.download_bytes / 1024 ** 2).toFixed(2)} MiB`;
        const install = element("button", installLabel, "quiet");
        install.type = "button";
        install.disabled = model.runnable;
        install.onclick = async () => {
          install.disabled = true;
          install.textContent = t("installingWeights");
          try {
            const result = await api(
              `/api/studio/models/${model.id}/install`,
              "POST",
            );
            renderHealth(result);
            S.localModels = S.localModels.map((m) =>
              m.id === result.id ? result : m,
            );
            renderModelDescription();
          } catch (error) {
            details.textContent = error.message;
          } finally {
            install.textContent = installLabel;
            install.disabled = Boolean(
              S.localModels.find((m) => m.id === model.id)?.runnable,
            );
          }
        };
        card.append(install);
      }
      body.push(card);
    }
    modal(t("models"), body);
  } catch (error) {
    notice(error.message, true);
  }
};

// The Codex transport is implemented by the local backend, not by an intent parser.
function inspectorMode(mode) {
  const agent = mode === "agent";
  $("tools-content").hidden = agent;
  $("meter-panel").hidden = agent;
  $("agent-content").hidden = !agent;
  $("tab-tools").setAttribute("aria-selected", String(!agent));
  $("tab-agent").setAttribute("aria-selected", String(agent));
  localStorage.setItem("musicStudioNextPanel", mode);
}
$("tab-tools").onclick = () => inspectorMode("tools");
$("tab-agent").onclick = () => inspectorMode("agent");
inspectorMode(localStorage.getItem("musicStudioNextPanel") || "tools");
function setAgentStatus(key) {
  $("agent-status").dataset.t = key;
  $("agent-status").textContent = t(key);
}
function disconnectAgent(message) {
  S.agentThread = null;
  S.agentBusy = false;
  $("connect-agent").hidden = false;
  $("agent-form").hidden = true;
  setAgentStatus("notConnected");
  if (message)
    $("agent-messages").append(element("div", message, "tool-event"));
}
$("connect-agent").onclick = () =>
  task(async () => {
    if (!S.project) return;
    setAgentStatus("connecting");
    let result;
    try {
      result = await api("/api/studio/agent/connect", "POST", {
        project: S.project.id,
      });
    } catch (error) {
      disconnectAgent(error.message);
      throw error;
    }
    S.agentThread = result.thread;
    S.agentCursor = 0;
    S.agentBusy = result.busy;
    $("agent-messages").replaceChildren();
    $("connect-agent").hidden = true;
    $("agent-form").hidden = false;
    $("agent-send").disabled = result.busy;
    $("agent-stop").hidden = !result.busy;
    setAgentStatus(result.busy ? "agentRunning" : "connected");
    notice("");
  });
$("agent-form").onsubmit = async (e) => {
  e.preventDefault();
  if (S.agentBusy || !S.agentThread) return;
  const prompt = $("agent-input").value.trim();
  if (!prompt) return;
  try {
    await api("/api/studio/agent/message", "POST", {
      thread: S.agentThread,
      message: prompt,
    });
    $("agent-input").value = "";
    S.agentBusy = true;
    $("agent-send").disabled = true;
    $("agent-stop").hidden = false;
    setAgentStatus("agentRunning");
  } catch (error) {
    notice(error.message, true);
  }
};
$("agent-stop").onclick = async () => {
  try {
    await api("/api/studio/agent/stop", "POST", { thread: S.agentThread });
  } catch (error) {
    notice(error.message, true);
  }
};
async function pollAgent() {
  if (!S.agentThread) return;
  const thread = S.agentThread;
  let result;
  try {
    result = await api(
      `/api/studio/agent/events?thread=${encodeURIComponent(thread)}&after=${S.agentCursor}`,
    );
  } catch (error) {
    if ([404, 503].includes(error.status)) disconnectAgent(error.message);
    throw error;
  }
  if (thread !== S.agentThread) return;
  if (result.connected === false) {
    disconnectAgent(t("notConnected"));
    return;
  }
  for (const event of result.events) {
    S.agentCursor = event.seq;
    const list = $("agent-messages");
    if (event.kind === "user") {
      list.append(element("div", event.text, "user"));
    } else if (event.kind === "text") {
      let target = list.lastElementChild;
      if (!target || !target.classList.contains("assistant")) {
        target = element("div", "", "assistant");
        list.append(target);
      }
      target.dataset.raw = (target.dataset.raw || "") + event.text;
      target.replaceChildren();
      for (const part of target.dataset.raw.split(/(\*\*[^*]+\*\*)/g)) {
        if (part.startsWith("**") && part.endsWith("**"))
          target.append(element("strong", part.slice(2, -2)));
        else target.append(document.createTextNode(part));
      }
    } else if (event.kind === "tool") {
      // Overall turn status already shows work in progress. Keep one terminal
      // record per call, including rejected reads, instead of stale Working rows.
      if (event.status === "inProgress") continue;
      const node = element("div", "", "tool-event");
      node.dataset.agentTool = event.tool;
      node.dataset.toolStatus = event.status;
      renderAgentTool(node);
      list.append(node);
    } else if (event.kind === "error")
      list.append(element("div", event.message, "tool-event"));
    else if (event.kind === "done") {
      S.agentBusy = false;
      $("agent-send").disabled = false;
      $("agent-stop").hidden = true;
      setAgentStatus(
        event.status === "completed"
          ? "agentDone"
          : event.status === "interrupted"
            ? "agentStopped"
            : "agentFailed",
      );
    }
    list.scrollTop = list.scrollHeight;
  }
}
function renderAgentTool(node) {
  const names = {
    audio_get_session: "inspect",
    audio_render_preview: "render",
    audio_set_selection: "selectionChange",
    audio_adopt_preview: "adopt",
    audio_export_wav: "export",
    audio_history: "activity",
    audio_list_models: "models",
    audio_check_model: "modelCheck",
    audio_run_task: "runLocal",
    audio_get_tasks: "localTasks",
    audio_cancel_task: "cancel",
    audio_read_artifact: "inspectResult",
    audio_correct_transcript: "editTranscript",
    audio_prepare_comparison: "compare",
  };
  node.textContent =
    (names[node.dataset.agentTool]
      ? t(names[node.dataset.agentTool])
      : node.dataset.agentTool) +
    " · " +
    t(node.dataset.toolStatus === "completed" ? "agentDone" : "toolFailed");
  node.classList.toggle("tool-failed", node.dataset.toolStatus !== "completed");
}
let polling = false;
setInterval(async () => {
  if (polling || document.hidden) return;
  polling = true;
  try {
    await pollEvents();
    await pollAgent();
    await pollLocalTasks();
  } catch {
    /* A transient polling error must never reload audio. */
  } finally {
    polling = false;
  }
}, 1600);
translate();
(async () => {
  try {
    await Promise.all([loadProjects(), loadLocalModels()]);
    const id = new URL(location.href).searchParams.get("project");
    if (id) await task(() => openProject(id));
  } catch (e) {
    notice(e.message, true);
  }
})();
