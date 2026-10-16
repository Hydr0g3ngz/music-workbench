"use strict";
StationRecording.mount = function ({
  $,
  tr,
  position,
  session,
  pause,
  flush,
  adopt,
  toast,
  uid,
}) {
  const recorder = new StationRecording.Recorder(),
    dialog = $("recording-dialog");
  let target,
    url,
    takeName,
    saving = false,
    message = "";
  const active = () =>
    ["requesting", "recording", "stopping"].includes(recorder.state);
  const hasTake = () => Boolean(recorder.blob && recorder.frames > 0);
  function render() {
    const state = recorder.state;
    $("record-enable").disabled = active() || saving || hasTake();
    $("record-device").disabled = state !== "ready" || saving;
    $("record-start").disabled = state !== "ready" || saving;
    $("record-stop").disabled = state !== "recording";
    $("record-adopt").disabled = !hasTake() || saving;
    $("record-download").hidden = !hasTake();
    $("record-discard").disabled = saving || state === "stopping";
    $("record-close").disabled = active() || saving;
    $("record-preview").hidden = !hasTake();
    $("record-target").textContent = target
      ? tr(
          `加入「${target.title}」· ${target.at.toFixed(2)} 秒`,
          `Add to “${target.title}” · ${target.at.toFixed(2)}s`,
        )
      : tr(
          "从当前播放头录制，新建音轨。",
          "Record at the playhead into a new track.",
        );
    const labels = {
      idle: tr(
        "启用输入后，先检查电平再开始。",
        "Enable input, check your level, then start.",
      ),
      requesting: tr(
        "等待浏览器麦克风授权…",
        "Waiting for microphone permission…",
      ),
      ready: tr("输入已就绪 · 尚未录音", "Input ready · not recording"),
      recording: tr("正在录音 · 停止后可试听", "Recording · stop to audition"),
      stopping: tr("正在完成录音…", "Finishing the recording…"),
      stopped: tr(
        "录音保留在当前页面；试听后加入工程或下载。",
        "Take kept in this page; audition, add it to the session or download it.",
      ),
      error: tr(
        "输入已停止。已有录音可试听或下载。",
        "Input stopped. Any captured take can be auditioned or downloaded.",
      ),
    };
    $("record-status").textContent = saving
      ? tr(
          "正在保存录音，请保留此页面…",
          "Saving your take; keep this page open…",
        )
      : message || labels[state];
    $("record-status").classList.toggle("error", Boolean(message));
    $("recording-dialog").classList.toggle(
      "is-recording",
      state === "recording",
    );
  }
  function releasePreview() {
    const player = $("record-preview");
    player.pause();
    player.removeAttribute("src");
    player.load();
    if (url) URL.revokeObjectURL(url);
    url = null;
  }
  function preview() {
    releasePreview();
    if (hasTake()) {
      url = URL.createObjectURL(recorder.blob);
      $("record-preview").src = url;
      $("record-download").href = url;
      $("record-download").download = takeName || "recording.wav";
    }
    $("record-time").textContent =
      (recorder.frames / (recorder.rate || 1)).toFixed(2) + "s";
  }
  recorder.onstate = (state) => {
    if (state === "idle" || state === "ready") {
      $("record-time").textContent = "0.00s";
      $("record-level").value = -60;
      $("record-peak").textContent = "−∞ dBFS";
      $("record-peak").classList.remove("error");
    }
    if (state === "stopped" || state === "error") preview();
    render();
  };
  recorder.onmeter = (peak, seconds) => {
    const db = peak > 0 ? 20 * Math.log10(peak) : -60;
    $("record-level").value = Math.max(-60, db);
    $("record-peak").textContent =
      peak >= 0.99
        ? tr("输入过大 · 降低设备增益", "Input too loud · lower device gain")
        : `${peak > 0 ? db.toFixed(1) : "−∞"} dBFS`;
    $("record-peak").classList.toggle("error", peak >= 0.99);
    if (recorder.state === "recording")
      $("record-time").textContent = seconds.toFixed(2) + "s";
  };
  recorder.onerror = (error) => {
    const errors = {
      NotAllowedError: tr(
        "麦克风授权被拒绝，请在浏览器站点设置中允许后重试。",
        "Microphone permission denied. Allow it in browser site settings and retry.",
      ),
      NotFoundError: tr(
        "没有找到音频输入设备。",
        "No audio input device found.",
      ),
      NotReadableError: tr(
        "设备无法打开，可能正被其他软件占用。",
        "Cannot open the device; another application may be using it.",
      ),
      OverconstrainedError: tr(
        "此输入设备不可用，请重新选择。",
        "This input device is unavailable. Select another.",
      ),
      RecordingUnsupported: tr(
        "此浏览器不支持录音，请使用本机地址上的 Chrome 或 Edge。",
        "Recording is unsupported. Use Chrome or Edge on localhost.",
      ),
      RecordingDeviceLost: tr(
        "输入设备已断开。已捕获的录音仍可下载。",
        "Input disconnected. Captured audio remains available to download.",
      ),
    };
    message =
      errors[error.name] ||
      errors[error.message] ||
      tr(
        "录音中断，请下载已捕获片段后重试。",
        "Recording interrupted. Download any captured audio before retrying.",
      );
    render();
  };
  async function devices() {
    const inputs = (await navigator.mediaDevices.enumerateDevices()).filter(
        (d) => d.kind === "audioinput",
      ),
      select = $("record-device"),
      current = recorder.stream?.getAudioTracks()[0]?.getSettings().deviceId;
    select.replaceChildren();
    for (const [index, device] of inputs.entries()) {
      const option = document.createElement("option");
      option.value = device.deviceId;
      option.textContent =
        device.label || tr(`输入 ${index + 1}`, `Input ${index + 1}`);
      select.append(option);
    }
    if (current) select.value = current;
  }
  async function enable(device = "") {
    message = "";
    if (await recorder.prepare(device)) {
      try {
        await devices();
      } catch (_) {
        /* Capture still works if enumeration fails. */
      }
    }
  }
  $("record").onclick = async () => {
    pause();
    if (!session()) return;
    message = "";
    render();
    dialog.showModal();
  };
  $("record-enable").onclick = () => enable();
  $("record-device").onchange = () => enable($("record-device").value);
  $("record-start").onclick = async () => {
    $("record-start").disabled = true;
    try {
      pause();
      await flush();
      const current = session(),
        at = position();
      if (!current || at < 0 || at > 599 || current.content.tracks.length >= 32)
        throw Error(
          tr(
            "请留出录音空间：播放头应在 599 秒前，且轨道少于 32 条。",
            "Leave space to record: playhead before 599s and fewer than 32 tracks.",
          ),
        );
      target = {
        id: current.id,
        title: current.content.title,
        at,
        importId: uid(),
      };
      takeName = `Take-${new Date().toISOString().replace(/[:.]/g, "-")}.wav`;
      message = "";
      recorder.start(600 - at);
    } catch (error) {
      message = error.message;
      render();
    }
  };
  $("record-stop").onclick = () => recorder.stop();
  $("record-discard").onclick = () => {
    message = "";
    recorder.cancel();
    releasePreview();
    target = null;
    $("record-level").value = -60;
    $("record-peak").textContent = "−∞ dBFS";
    $("record-time").textContent = "0.00s";
    render();
  };
  $("record-adopt").onclick = async () => {
    if (!hasTake() || saving) return;
    saving = true;
    message = "";
    $("record-preview").pause();
    render();
    try {
      if (session()?.id !== target?.id)
        throw Error(
          tr(
            "请返回录音时的工程后再加入，或先下载 WAV。",
            "Return to the recorded session to add this take, or download the WAV.",
          ),
        );
      await adopt(recorder.blob, takeName, target);
      recorder.cancel();
      releasePreview();
      target = null;
      dialog.close();
      toast(
        tr(
          "录音已入轨，可撤销、混音和导出。",
          "Recording added. Undo, mix and export as usual.",
        ),
      );
    } catch (error) {
      message =
        error.message +
        " · " +
        tr(
          "录音仍保留，可下载或重试。",
          "Your take is retained; download or retry.",
        );
    } finally {
      saving = false;
      render();
    }
  };
  $("record-close").onclick = () => dialog.close();
  dialog.addEventListener("cancel", (event) => {
    if (active() || saving) event.preventDefault();
  });
  dialog.addEventListener("close", () => {
    $("record-preview").pause();
    if (!hasTake()) recorder.cancel();
    render();
  });
  window.addEventListener("beforeunload", (event) => {
    if (active() || hasTake() || saving) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  window.addEventListener("pagehide", () => recorder.cancel());
  return { render, busy: () => active() || saving };
};
