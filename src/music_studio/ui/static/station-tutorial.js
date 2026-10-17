/* A local, project-scoped lesson. Evidence comes from working controls, never simulated edits. */
(function (root) {
  "use strict";
  const steps = ["listen", "layers", "melody", "balance", "export"];
  const key = (id) => `workbench-lesson-v1:${id}`;
  function load(storage, id) {
    let saved;
    try {
      saved = JSON.parse(storage.getItem(key(id)));
    } catch {
      /* Private storage is optional. */
    }
    return {
      step: Number.isInteger(saved?.step)
        ? Math.max(0, Math.min(5, saved.step))
        : 0,
      open: saved?.open === true,
      outcomes: Object.fromEntries(
        steps.map((s) => [
          s,
          ["done", "skipped"].includes(saved?.outcomes?.[s])
            ? saved.outcomes[s]
            : null,
        ]),
      ),
    };
  }
  function snapshot(content) {
    return {
      master: content.master_db,
      tracks: content.tracks.map((t) => ({
        id: t.id,
        mute: !!t.mute,
        solo: !!t.solo,
        gain: t.gain_db,
        pan: t.pan,
        clips: t.clips.map((c) => ({
          id: c.id,
          notes: JSON.stringify(c.notes),
        })),
      })),
    };
  }
  function evidence(before, after) {
    const found = new Set();
    if (!before || !after) return found;
    if (before.master !== after.master) found.add("balance");
    for (const t of after.tracks) {
      const old = before.tracks.find((x) => x.id === t.id);
      if (!old) continue;
      if (old.mute !== t.mute || old.solo !== t.solo) found.add("layers");
      if (old.gain !== t.gain || old.pan !== t.pan) found.add("balance");
      for (const c of t.clips) {
        const prior = old.clips.find((x) => x.id === c.id);
        if (prior && prior.notes !== c.notes) found.add("melody");
      }
    }
    return found;
  }
  function mount({ document: doc, storage, tr, content, action }) {
    const panel = doc.createElement("aside");
    panel.id = "creation-lesson";
    panel.className = "creation-lesson";
    panel.setAttribute("aria-label", tr("创作入门", "First creation"));
    panel.hidden = true;
    doc.body.append(panel);
    let id,
      state,
      baseline,
      collapsed = false;
    const texts = [
      [
        "先听见一段音乐",
        "Listen to a musical sketch",
        "点播放 ▶，听完几拍。鼓给出脉搏，贝斯托住低音，键盘与铺底带来和声。这个八小节示例可完全修改，无需模型。",
        "Press Play ▶ and listen for a few beats. Drums give the pulse, bass the low end, keys and pad the harmony. This eight-bar sketch is fully editable and needs no models.",
        "定位播放按钮",
        "Find Play",
        "播放成功后，这一步就会点亮。",
        "This step lights up after playback starts.",
      ],
      [
        "拆开听，认识每一层",
        "Hear the layers",
        "在任一音轨点 M（静音）或 S（独奏），比较前后。试着只听鼓，再把它还原。继续前记得关掉独奏、恢复想听的轨道。",
        "Use M (mute) or S (solo) on a track and compare. Try listening to just the drums, then restore the mix. Turn off solo and restore the tracks you want before continuing.",
        "定位音轨开关",
        "Find track switches",
        "实际切换一次静音或独奏即可。",
        "Change a mute or solo switch to continue.",
      ],
      [
        "把一个音变成自己的",
        "Make a note your own",
        "打开键盘片段，在下方钢琴卷帘里点一个音，再用 ↑ / ↓ 移半音，或拖动音符。先改一个就够；不喜欢就点 ↶ 撤销。",
        "Open a keys clip. In the piano roll, select a note and press ↑ / ↓ to move a semitone, or drag it. Start with one note; use ↶ Undo if you prefer the original.",
        "打开可编辑音符",
        "Open editable notes",
        "改动一个已有片段中的音符即可。",
        "Edit the notes in an existing clip to continue.",
      ],
      [
        "给每个声音留点空间",
        "Find a balance",
        "打开混音台，试着把贝斯推子降低 2–3 dB，播放比较。推子决定响度，声像决定左右位置。避免所有声音都挤在最前面。",
        "Open the mixer and lower the bass by 2–3 dB, then play and compare. Faders set level; pan sets left/right position. Give the other sounds room.",
        "打开混音台",
        "Open the mixer",
        "调整一次轨道音量、声像或主音量即可。",
        "Change a track level, pan or master level to continue.",
      ],
      [
        "导出第一份作品",
        "Export your first piece",
        "点导出作品，选择 WAV。它是一份可播放的混音；MWB 则保存可继续编辑的工程与音频。工程会自动保存，导出后确认下载或保存位置。",
        "Choose Export, then WAV for a playable mix. MWB keeps the editable project and audio. Projects save automatically; check your download or save location after exporting.",
        "打开 WAV 导出",
        "Open WAV export",
        "成功渲染 WAV 后即可完成；教程无法确认你是否保存了文件。",
        "Complete a WAV render to finish. The lesson cannot confirm that you saved the file.",
      ],
    ];
    function persist() {
      try {
        storage.setItem(key(id), JSON.stringify(state));
      } catch {
        /* The lesson still works. */
      }
    }
    function clearHighlight() {
      doc
        .querySelectorAll(".lesson-highlight")
        .forEach((el) => el.classList.remove("lesson-highlight"));
    }
    function render() {
      if (!state) return;
      panel.setAttribute("aria-label", tr("创作入门", "First creation"));
      panel.hidden = !state.open;
      const opener = doc.getElementById("open-tutorial");
      if (opener) {
        opener.textContent = tr("入门", "Learn");
        opener.setAttribute("aria-expanded", String(state.open));
      }
      if (!state.open) {
        clearHighlight();
        return;
      }
      panel.classList.toggle("collapsed", collapsed);
      const completed = steps.filter(
        (s) => state.outcomes[s] === "done",
      ).length;
      const skipped = steps.filter(
        (s) => state.outcomes[s] === "skipped",
      ).length;
      const finished = state.step === steps.length,
        step = steps[state.step],
        text = texts[state.step];
      panel.innerHTML = `<header><span>${tr("第一段音乐", "Your first sketch")} · ${finished ? "5 / 5" : `${state.step + 1} / 5`}</span><div><button data-lesson="collapse" aria-label="${tr("收起或展开教程", "Collapse or expand lesson")}">${collapsed ? "＋" : "−"}</button><button data-lesson="close" aria-label="${tr("关闭教程", "Close lesson")}">×</button></div></header>
        <div class="lesson-body"><div class="lesson-dots" aria-hidden="true">${steps.map((s, i) => `<i class="${state.outcomes[s] || (i === state.step ? "current" : "")}"></i>`).join("")}</div>
        <h2>${finished ? tr("让这个灵感继续长大", "Keep this idea growing") : tr(text[0], text[1])}</h2>
        <p>${finished ? tr(`完成 ${completed} 项操作${skipped ? `，跳过 ${skipped} 项` : ""}。你可以继续改编、录入自己的声音，再尝试本地 AI。`, `${completed} actions completed${skipped ? `, ${skipped} skipped` : ""}. Keep arranging, record your own sound, then try local AI.`) : tr(text[2], text[3])}</p>
        ${finished ? `<button data-lesson="ai" class="lesson-primary">${tr("探索本地 AI", "Explore local AI")} ↗</button><button data-lesson="restart">${tr("重新跟练（保留作品）", "Repeat lesson (keep music)")}</button>` : `<button data-lesson="locate" class="lesson-primary">${tr(text[4], text[5])} ↗</button><p class="lesson-evidence" role="status">${state.outcomes[step] === "done" ? tr("✓ 已检测到这项操作", "✓ Action detected") : tr(text[6], text[7])}</p><div class="lesson-nav"><button data-lesson="back" ${state.step === 0 ? "disabled" : ""}>${tr("上一步", "Back")}</button><button data-lesson="skip">${tr("稍后做", "Skip for now")}</button><button data-lesson="next" ${state.outcomes[step] !== "done" ? "disabled" : ""}>${state.step === 4 ? tr("完成", "Finish") : tr("下一步", "Next")} →</button></div>`}
        <button data-lesson="manual" class="lesson-manual">${tr("查看完整入门手册", "Read the full beginner guide")} ↗</button>
        <small>${tr("学习进度保存在本机。关闭教程不会删除作品。", "Lesson progress stays on this computer. Closing keeps your music.")}</small></div>`;
    }
    function attach(projectId, start = false) {
      if (id !== projectId) {
        id = projectId;
        state = load(storage, id);
        collapsed = false;
        baseline = snapshot(content());
        clearHighlight();
      }
      if (start) {
        state.open = true;
        persist();
      }
      render();
    }
    function observe(event, projectId = id) {
      if (!state || projectId !== id) return;
      const now = snapshot(content()),
        events = evidence(baseline, now);
      baseline = now;
      if (event) events.add(event);
      const step = steps[state.step];
      if (state.open && events.has(step) && state.outcomes[step] !== "done") {
        state.outcomes[step] = "done";
        persist();
        render();
      }
    }
    function show() {
      if (state) {
        state.open = true;
        collapsed = false;
        persist();
        render();
      }
    }
    panel.onclick = async (e) => {
      const button = e.target.closest("[data-lesson]");
      if (!button || button.disabled) return;
      const kind = button.dataset.lesson;
      if (kind === "close") {
        state.open = false;
        clearHighlight();
      }
      if (kind === "collapse") {
        collapsed = !collapsed;
        clearHighlight();
      }
      if (kind === "back") state.step = Math.max(0, state.step - 1);
      if (kind === "next" && state.outcomes[steps[state.step]] === "done")
        state.step++;
      if (kind === "skip") {
        // Visiting a completed step must not overwrite its evidence with "skipped".
        state.outcomes[steps[state.step]] ||= "skipped";
        state.step++;
      }
      if (kind === "restart") {
        state = load({ getItem: () => null }, id);
        state.open = true;
      }
      if (["next", "back", "skip", "restart"].includes(kind)) {
        clearHighlight();
        baseline = snapshot(content());
      }
      if (["locate", "ai", "manual"].includes(kind)) {
        clearHighlight();
        // Navigation/selecting tools uses the workstation's existing controls. No score is injected.
        const selector = await action(
          kind === "locate" ? steps[state.step] : kind,
        );
        const target = selector && doc.querySelector(selector);
        if (target) {
          target.classList.add("lesson-highlight");
          target.scrollIntoView({ block: "nearest", inline: "nearest" });
          target.focus({ preventScroll: true });
        }
      }
      persist();
      render();
    };
    return { attach, observe, render, show };
  }
  const exported = { steps, key, load, snapshot, evidence, mount };
  if (typeof module !== "undefined" && module.exports)
    module.exports = exported;
  else root.StationTutorial = exported;
})(typeof window !== "undefined" ? window : globalThis);
