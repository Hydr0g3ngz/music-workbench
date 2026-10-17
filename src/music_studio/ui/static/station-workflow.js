/* Editing tools share the same autosave, undo and playback operations as the workstation. */
"use strict";
window.StationWorkflow = {
  mount(api) {
    const {
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
    } = api;
    let clipId,
      selection = new Set(),
      copied = [],
      dragging,
      suppressClick = false;
    const pianoSettings = { grid: 0.25, paste: 0 };
    const step = () => Number($("note-grid-step")?.value || 0.25);
    const clipEnd = () =>
      ((selectedClip().offset + selectedClip().duration) * content().bpm) / 60;
    const selected = () => [...selection];
    const root = $("piano");
    root.tabIndex = 0;
    const keys = () =>
      `<option value="">${tr("未指定", "Unspecified")}</option>` +
      StationEdit.keyNames
        .flatMap((k) =>
          ["major", "minor"].map(
            (mode) =>
              `<option value="${k} ${mode}" ${content().key === k + " " + mode ? "selected" : ""}>${k} ${tr(mode === "major" ? "大调" : "小调", mode)}</option>`,
          ),
        )
        .join("");
    const button = (action, label, title = label) =>
      `<button type="button" data-note-action="${action}" title="${title}">${label}</button>`;
    function paintSelection() {
      root.querySelectorAll("[data-note]").forEach((n) => {
        n.classList.toggle(
          "note-selected",
          selection.has(Number(n.dataset.note)),
        );
        n.setAttribute(
          "aria-pressed",
          String(selection.has(Number(n.dataset.note))),
        );
      });
      if ($("note-selection-count"))
        $("note-selection-count").textContent =
          `${selection.size} ${tr("个选中", "selected")}`;
    }
    function enhancePiano() {
      const c = selectedClip(),
        t = selectedTrack();
      if (c?.id !== clipId) {
        clipId = c?.id;
        selection.clear();
        pianoSettings.paste = c
          ? Math.round(((c.offset * content().bpm) / 60) * 4) / 4
          : 0;
      }
      if (!c || t?.kind !== "midi") return;
      selection = new Set(selected().filter((i) => i < c.notes.length));
      const velocity = c.notes[selected()[0]]?.velocity || 90;
      root.insertAdjacentHTML(
        "afterbegin",
        `<div class="note-tools">
        <span id="note-selection-count"></span>
        ${button("all", tr("全选", "All"), "Ctrl+A")}${button("copy", tr("复制", "Copy"), "Ctrl+C")}${button("paste", tr("粘贴", "Paste"), "Ctrl+V")}${button("duplicate", tr("重复", "Repeat"), "Ctrl+D")}
        <label>${tr("粘贴到拍", "Paste at beat")} <input id="note-paste-at" type="number" min="0" max="3000" step=".25" value="${pianoSettings.paste}"></label>
        <select id="note-grid-step" aria-label="${tr("量化网格", "Quantization grid")}"><option value=".25">1/16</option><option value=".5">1/8</option><option value="1">1/4</option></select>
        ${button("quantize", tr("量化", "Quantize"))}${button("down", "−1 ♩", tr("降半音", "Semitone down"))}${button("up", "+1 ♩", tr("升半音", "Semitone up"))}
        <label>${tr("力度", "Velocity")} <input id="note-group-velocity" type="number" min="1" max="127" step="1" value="${velocity}"></label>
        ${button("delete", "×", tr("删除选中音符", "Delete selected notes"))}
        <small>${tr("拖动移动 · 右边缘拉长 · Shift 多选 / 空白拖动框选", "Drag to move · right edge to resize · Shift select / drag empty grid to select")}</small>
      </div>`,
      );
      const grid = root.querySelector(".piano-grid"),
        high = Number(grid.dataset.high),
        low = Number(grid.dataset.low);
      $("note-grid-step").value = String(pianoSettings.grid).replace(
        /^0\./,
        ".",
      );
      if (content().key && t.instrument !== "vcsl-drums") {
        for (let pitch = low; pitch <= high; pitch++)
          if (StationEdit.inKey(pitch, content().key))
            grid.insertAdjacentHTML(
              "afterbegin",
              `<span class="scale-row" style="top:${(high - pitch) * 14}px"></span>`,
            );
      }
      root.querySelectorAll("[data-note]").forEach((n) => {
        n.title = tr(
          "拖动移动；右边缘改时值；Shift 多选；双击删除",
          "Drag to move; right edge to resize; Shift select; double-click deletes",
        );
        n.style.setProperty(
          "--velocity",
          c.notes[Number(n.dataset.note)].velocity / 127,
        );
        n.insertAdjacentHTML("beforeend", '<span class="note-resize"></span>');
      });
      paintSelection();
    }
    function editNotes(op, value) {
      const c = selectedClip();
      if (!c || selectedTrack()?.kind !== "midi") return;
      const result = StationEdit.notes(
        c.notes,
        selected(),
        op,
        value,
        clipEnd(),
      );
      mutate(() => {
        c.notes = result;
        if (op === "delete") {
          selection.clear();
          s.noteClip = null;
        }
      });
    }
    function action(name) {
      const c = selectedClip();
      if (!c || selectedTrack()?.kind !== "midi") return;
      if (name === "all") {
        selection = new Set(c.notes.map((_, i) => i));
        paintSelection();
        return;
      }
      if (name === "copy") {
        copied = selected().map((i) => ({ ...c.notes[i] }));
        return;
      }
      if (name === "paste" || name === "duplicate") {
        const group =
          name === "duplicate" ? selected().map((i) => c.notes[i]) : copied;
        if (!group.length) return;
        const at =
          name === "duplicate"
            ? Math.ceil(
                Math.max(...group.map((n) => n.start + n.length)) / step(),
              ) * step()
            : Number($("note-paste-at").value);
        const result = StationEdit.paste(c.notes, group, at, clipEnd()),
          first = c.notes.length;
        mutate(() => {
          c.notes = result;
          selection = new Set(result.slice(first).map((_, i) => first + i));
        });
        return;
      }
      if (!selection.size) return;
      if (name === "delete") editNotes("delete", 0);
      if (name === "up" || name === "down")
        editNotes("transpose", name === "up" ? 1 : -1);
      if (name === "quantize") editNotes("quantize", step());
    }
    root.onclick = guarded(async (e) => {
      if (suppressClick) {
        suppressClick = false;
        return;
      }
      const tool = e.target.closest("[data-note-action]");
      if (tool) return action(tool.dataset.noteAction);
      const key = e.target.closest("[data-note-key]");
      if (key)
        return engine.note(
          Number(key.dataset.noteKey),
          selectedTrack()?.instrument,
        );
      const n = e.target.closest("[data-note]");
      if (n) {
        const i = Number(n.dataset.note);
        s.noteClip = selectedClip().id;
        s.noteIndex = i;
        renderInspector();
        await engine.note(
          selectedClip().notes[i].pitch,
          selectedTrack().instrument,
        );
      }
    });
    root.onchange = guarded((e) => {
      if (e.target.id === "note-grid-step")
        pianoSettings.grid = Number(e.target.value);
      if (e.target.id === "note-paste-at")
        pianoSettings.paste = Number(e.target.value);
      if (e.target.id === "note-group-velocity" && e.target.checkValidity())
        editNotes("velocity", Number(e.target.value));
    });
    root.addEventListener(
      "keydown",
      guarded((e) => {
        if (e.target.matches("input,select,textarea")) return;
        const ctrl = e.ctrlKey || e.metaKey,
          key = e.key.toLowerCase();
        const op = ctrl
          ? { a: "all", c: "copy", v: "paste", d: "duplicate" }[key]
          : { delete: "delete", backspace: "delete" }[key];
        if (op) {
          e.preventDefault();
          e.stopPropagation();
          action(op);
        }
        if (
          ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key) &&
          selection.size
        ) {
          e.preventDefault();
          e.stopPropagation();
          editNotes(
            e.key === "ArrowUp" || e.key === "ArrowDown" ? "transpose" : "move",
            (e.key === "ArrowDown" || e.key === "ArrowLeft" ? -1 : 1) *
              (e.key.includes("Up") || e.key.includes("Down")
                ? e.shiftKey
                  ? 12
                  : 1
                : step()),
          );
        }
      }),
    );
    root.onpointerdown = (e) => {
      if (e.button !== 0 || e.target.closest(".note-tools,[data-note-key]"))
        return;
      const grid = e.target.closest(".piano-grid"),
        c = selectedClip();
      if (!grid || !c) return;
      const note = e.target.closest("[data-note]"),
        index = note ? Number(note.dataset.note) : null;
      if (note) {
        if (e.shiftKey) {
          if (selection.has(index)) selection.delete(index);
          else selection.add(index);
        } else if (!selection.has(index)) selection = new Set([index]);
      } else if (!e.shiftKey) selection.clear();
      paintSelection();
      root.focus({ preventScroll: true });
      dragging = {
        x: e.clientX,
        y: e.clientY,
        grid,
        rect: grid.getBoundingClientRect(),
        c,
        before: structuredClone(c.notes),
        selected: selected(),
        index,
        resize: !!e.target.closest(".note-resize"),
        moved: false,
        pointer: e.pointerId,
        gridStep: step(),
      };
      root.setPointerCapture(e.pointerId);
      e.preventDefault();
    };
    root.onpointermove = (e) => {
      if (!dragging) return;
      const d = dragging,
        dx = e.clientX - d.x,
        dy = e.clientY - d.y,
        bw = Number(d.grid.dataset.beatWidth);
      if (Math.abs(dx) + Math.abs(dy) < 4 && !d.moved) return;
      d.moved = true;
      if (d.index === null) {
        const left = Math.min(d.x, e.clientX) - d.rect.left,
          right = Math.max(d.x, e.clientX) - d.rect.left,
          top = Math.min(d.y, e.clientY) - d.rect.top,
          bottom = Math.max(d.y, e.clientY) - d.rect.top;
        let box = d.grid.querySelector(".note-marquee");
        if (!box) {
          box = document.createElement("span");
          box.className = "note-marquee";
          d.grid.append(box);
        }
        Object.assign(box.style, {
          left: left + "px",
          top: top + "px",
          width: right - left + "px",
          height: bottom - top + "px",
        });
        selection = new Set(d.selected);
        d.before.forEach((n, i) => {
          const y = (Number(d.grid.dataset.high) - n.pitch) * 14;
          if (
            n.start * bw <= right &&
            (n.start + n.length) * bw >= left &&
            y <= bottom &&
            y + 14 >= top
          )
            selection.add(i);
        });
        paintSelection();
        return;
      }
      const beats = Math.round(dx / bw / d.gridStep) * d.gridStep,
        pitch = -Math.round(dy / 14);
      try {
        let candidate = StationEdit.notes(
          d.before,
          d.selected,
          d.resize ? "length" : "move",
          beats,
          clipEnd(),
        );
        if (!d.resize)
          candidate = StationEdit.notes(
            candidate,
            d.selected,
            "transpose",
            pitch,
            clipEnd(),
          );
        d.candidate = candidate;
        d.selected.forEach((i) => {
          const el = d.grid.querySelector(`[data-note="${i}"]`),
            n = candidate[i];
          if (el)
            Object.assign(el.style, {
              left: n.start * bw + "px",
              top: (Number(d.grid.dataset.high) - n.pitch) * 14 + 1 + "px",
              width: Math.max(4, n.length * bw - 2) + "px",
            });
        });
      } catch {
        /* Keep the last valid preview at the boundary. */
      }
    };
    root.onpointerup = guarded(() => {
      const d = dragging;
      dragging = null;
      if (!d) return;
      if (root.hasPointerCapture(d.pointer))
        root.releasePointerCapture(d.pointer);
      d.grid.querySelector(".note-marquee")?.remove();
      suppressClick = d.moved;
      setTimeout(() => {
        suppressClick = false;
      }, 0);
      if (d.moved && d.candidate)
        mutate(() => {
          d.c.notes = d.candidate;
        });
      else paintSelection();
    });
    root.onpointercancel = () => {
      dragging = null;
      renderPiano();
    };

    const toolbar = document.createElement("div");
    toolbar.className = "workflow-toolbar";
    toolbar.innerHTML =
      '<button id="section-settings"></button><button id="fit-project"></button><button id="material-tools"></button>';
    document.querySelector(".arranger-toolbar").after(toolbar);
    const dialog = document.createElement("dialog");
    dialog.id = "section-dialog";
    dialog.innerHTML =
      '<div class="dialog-heading"><h2 id="section-heading"></h2><button class="icon-button" data-workflow-close>×</button></div><div id="section-editor"></div>';
    document.body.append(dialog);
    const material = document.createElement("dialog");
    material.id = "material-dialog";
    material.innerHTML =
      '<div class="dialog-heading"><h2 id="material-heading"></h2><button class="icon-button" data-workflow-close>×</button></div><div id="material-body"></div>';
    document.body.append(material);
    [dialog, material].forEach(
      (d) =>
        (d.querySelector("[data-workflow-close]").onclick = () => d.close()),
    );
    const restore = document.createElement("button");
    restore.className = "quiet";
    restore.id = "restore-project-pack";
    const packInput = document.createElement("input");
    packInput.type = "file";
    packInput.accept = ".mwb";
    packInput.hidden = true;
    packInput.id = "project-pack-file";
    $("project-dialog").append(restore, packInput);
    restore.onclick = () => packInput.click();
    packInput.onchange = guarded(async () => {
      if (!packInput.files.length) return;
      pause();
      await flush();
      restore.disabled = true;
      try {
        const form = new FormData();
        form.append("file", packInput.files[0]);
        accept(await request("/api/workstation/projects/import-pack", form));
        $("project-dialog").close();
        toast(
          tr(
            "工程与音频已恢复为新工程",
            "Project and audio restored as a new session",
          ),
        );
      } finally {
        restore.disabled = false;
        packInput.value = "";
      }
    });
    function render() {
      if (!s.session) return;
      $("section-settings").textContent = tr("段落与调性", "Sections & key");
      restore.textContent = tr(
        "恢复便携工程 .mwb",
        "Restore portable project .mwb",
      );
      $("fit-project").textContent = tr("适配整首", "Fit song");
      $("material-tools").textContent = tr("素材适配 / AI", "Material / AI");
      $("material-tools").disabled =
        selectedTrack()?.kind !== "audio" || !selectedClip();
      $("ruler-ticks")
        .querySelectorAll(".section-band")
        .forEach((n) => n.remove());
      (content().sections || []).forEach((m) =>
        $("ruler-ticks").insertAdjacentHTML(
          "beforeend",
          `<button class="section-band" data-section="${m.id}" title="${esc(m.name)}" style="left:${((m.start * 60) / content().bpm) * s.zoom}px;width:${(((m.end - m.start) * 60) / content().bpm) * s.zoom}px">${esc(m.name)}</button>`,
        ),
      );
    }
    $("ruler-ticks").addEventListener("click", (e) => {
      const el = e.target.closest("[data-section]");
      if (!el) return;
      e.stopPropagation();
      const m = content().sections.find((x) => x.id === el.dataset.section);
      seek((m.start * 60) / content().bpm);
    });
    $("fit-project").onclick = () => {
      const end = Math.max(
        (8 * 60) / content().bpm,
        ...content().tracks.flatMap((t) =>
          t.clips.map((c) => c.start + c.duration),
        ),
        ...(content().sections || []).map((m) => (m.end * 60) / content().bpm),
      );
      s.zoom = Math.max(
        0.5,
        Math.min(
          150,
          ($("arranger").clientWidth - api.headWidth() - 30) /
            (end + (8 * 60) / content().bpm),
        ),
      );
      $("arranger").scrollLeft = 0;
      renderAll();
    };
    function showSections() {
      $("section-heading").textContent = tr(
        "段落、复制与工程调性",
        "Sections, duplication & project key",
      );
      $("section-editor").innerHTML =
        `<p class="panel-copy">${tr("所有位置按小节填写，结束小节不包含在内。复制会裁剪边界并保留素材起点，一次撤销。", "Enter bar positions; end bar is exclusive. Copy trims boundaries, retains source offsets and can be undone in one step.")}</p>
        <label class="field-row">${tr("工程调性", "Project key")}<select id="project-key">${keys()}</select></label>
        <div class="section-list">${(content().sections || []).map((m) => `<div><button data-seek-section="${m.id}">${esc(m.name)} · ${m.start / 4 + 1} → ${m.end / 4 + 1}</button><button data-remove-section="${m.id}">×</button></div>`).join("")}</div>
        <form id="section-form"><label>${tr("段落名称", "Section name")}<input id="section-name" maxlength="80" value="${tr("新段落", "New section")}" required></label>
        <div class="workflow-fields"><label>${tr("开始小节", "Start bar")}<input id="section-start" type="number" min="1" step=".0625" value="${Math.floor((s.position * content().bpm) / 60 / 4) + 1}" required></label>
        <label>${tr("结束小节", "End bar")}<input id="section-end" type="number" min="1.0625" step=".0625" value="${Math.floor((s.position * content().bpm) / 60 / 4) + 5}" required></label></div>
        <button class="primary" type="submit">${tr("添加段落标记", "Add section marker")}</button></form>
        <div class="workflow-fields"><label>${tr("复制到小节", "Copy to bar")}<input id="section-destination" type="number" min="1" step=".0625" value="9"></label><button id="copy-section">${tr("复制该范围的所有轨道", "Copy range across all tracks")}</button></div><p id="section-feedback" role="status"></p>`;
      $("project-key").onchange = () =>
        mutate(() => (content().key = $("project-key").value));
      $("section-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(() => {
          const start = (Number($("section-start").value) - 1) * 4,
            end = (Number($("section-end").value) - 1) * 4;
          if (
            end - start < 0.25 ||
            (end * 60) / content().bpm > 600 ||
            (content().sections || []).length >= 64
          )
            throw Error(tr("段落范围不正确", "Invalid section range"));
          const name = $("section-name").value.trim();
          if (!name) return;
          mutate(() => {
            content().sections = [
              ...(content().sections || []),
              { id: uid(), name, start, end },
            ];
          });
          showSections();
        })();
      };
      $("copy-section").onclick = guarded(() => {
        const result = StationEdit.section(
          content(),
          (Number($("section-start").value) - 1) * 4,
          (Number($("section-end").value) - 1) * 4,
          (Number($("section-destination").value) - 1) * 4,
          uid,
        );
        mutate(() => Object.assign(content(), result));
        $("section-feedback").textContent = tr(
          "已复制，关闭窗口可查看；可撤销。",
          "Copied. Close to view; undo is available.",
        );
      });
      $("section-editor").onclick = (e) => {
        const remove = e.target.closest("[data-remove-section]"),
          go = e.target.closest("[data-seek-section]");
        if (remove) {
          mutate(
            () =>
              (content().sections = content().sections.filter(
                (x) => x.id !== remove.dataset.removeSection,
              )),
          );
          showSections();
        }
        if (go) {
          const m = content().sections.find(
            (x) => x.id === go.dataset.seekSection,
          );
          $("section-start").value = m.start / 4 + 1;
          $("section-end").value = m.end / 4 + 1;
          seek((m.start * 60) / content().bpm);
        }
      };
      if (!dialog.open) dialog.showModal();
    }
    $("section-settings").onclick = showSections;
    function enhanceInspector() {
      const c = selectedClip();
      if (!c) return;
      $("inspector-content").insertAdjacentHTML(
        "afterbegin",
        `<section class="inspector-section musical-position"><h3>${tr("音乐位置 · 4/4", "MUSICAL POSITION · 4/4")}</h3>
        <label class="field-row">${tr("片段名称", "Clip name")}<input data-clip-name type="text" maxlength="150" value="${esc(c.name)}"></label>
        <label class="field-row">${tr("开始小节", "Start bar")}<input data-musical-start type="number" min="1" step=".0625" value="${+((c.start * content().bpm) / 240 + 1).toFixed(6)}"></label>
        <label class="field-row">${tr("长度 · 小节", "Length · bars")}<input data-musical-length type="number" min=".0625" step=".0625" value="${+((c.duration * content().bpm) / 240).toFixed(6)}"></label></section>`,
      );
    }
    $("inspector-content").addEventListener(
      "change",
      guarded((e) => {
        const el = e.target,
          c = selectedClip();
        if (!c || !el.checkValidity()) return;
        if (el.hasAttribute("data-clip-name")) {
          const name = el.value.trim();
          if (name) mutate(() => (c.name = name));
          else renderInspector();
          return;
        }
        if (!el.matches("[data-musical-start],[data-musical-length]")) return;
        const candidate = { ...c };
        if (el.hasAttribute("data-musical-start"))
          candidate.start = ((Number(el.value) - 1) * 240) / content().bpm;
        else candidate.duration = (Number(el.value) * 240) / content().bpm;
        const a = s.session.assets.find((a) => a.id === c.asset);
        if (
          candidate.start + candidate.duration > 600 ||
          candidate.duration <= 0 ||
          candidate.fade_in + candidate.fade_out > candidate.duration ||
          (a && candidate.offset + candidate.duration > a.duration + 1 / 44100)
        ) {
          renderInspector();
          throw Error(
            tr(
              "片段超出素材或工程范围",
              "Clip exceeds source or session bounds",
            ),
          );
        }
        if (candidate.duration !== c.duration)
          candidate.volume_points = StationEnvelope.crop(
            c,
            0,
            candidate.duration,
          );
        mutate(() => Object.assign(c, candidate));
      }),
    );
    async function run(model, extra = {}) {
      const project = s.session.id,
        c = selectedClip();
      if (!c?.asset) throw Error(tr("先选择音频片段", "Select an audio clip"));
      await flush();
      if (s.session.id !== project) return;
      await request(base() + "/process", {
        revision: s.session.revision,
        clip: c.id,
        model,
        ...extra,
      });
      material.close();
      dock("tasks");
      await pollTasks();
      toast(tr("任务已提交；原素材保留", "Task queued; original retained"));
    }
    $("material-tools").onclick = () => {
      const c = selectedClip();
      if (!c?.asset) return;
      $("material-heading").textContent = tr(
        "让素材进入作品",
        "Make this material fit",
      );
      $("material-body").innerHTML =
        `<p class="panel-copy">${esc(c.name)} · ${tr("只处理当前片段；采用时放回工程原位置。速度和调性分析使用 DSP 估计。", "Only the selected clip is processed; adoption retains its session position. Tempo and key analysis uses DSP estimates.")}</p>
        <div class="workflow-models"><button data-workflow-model="musical-analysis">${tr("分析速度 / 调性 / 电平", "Analyze tempo / key / levels")}<small>librosa · DSP</small></button>
        <button data-workflow-model="demucs-four-stems">${tr("拆成鼓 / 贝斯 / 人声 / 其他", "Separate drums / bass / vocals / other")}<small>Demucs · AI</small></button>
        <button data-workflow-model="crepe-rest">${tr("提取可编辑旋律 MIDI", "Extract editable melody MIDI")}<small>CREPE · AI · ${tr("单旋律实验", "monophonic, experimental")}</small></button></div>
        <h3>${tr("独立变速与变调", "Independent time & pitch")}</h3><p class="panel-copy">${tr("这是 DSP，保留原音；在任务中试听后替换。速度倍数大于 1 会缩短时长，不改变音高。", "DSP, with the original retained. Audition the task before replacement. Speed above 1 shortens duration without changing pitch.")}</p>
        <form id="transform-form"><div class="workflow-fields"><label>${tr("速度倍数", "Speed ratio")}<input id="transform-rate" type="number" min=".5" max="2" step=".001" value="1" required></label>
        <label>${tr("移调 · 半音", "Pitch · semitones")}<input id="transform-pitch" type="number" min="-12" max="12" step="1" value="0" required></label></div>
        <button class="primary" type="submit">${tr("制作适配候选", "Create fitted candidate")}</button></form>
        <p class="panel-copy">${tr("已知素材 BPM 时，速度倍数 = 工程 BPM ÷ 素材 BPM。短片段和无鼓音乐可能误判半速/倍速，请试听确认。", "For known source tempo: ratio = project BPM / source BPM. Short or beatless clips can produce half/double-time errors; audition first.")}</p>`;
      $("material-body").onclick = guarded((e) => {
        const b = e.target.closest("[data-workflow-model]");
        if (b) return run(b.dataset.workflowModel);
      });
      $("transform-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(() =>
          run("time-pitch", {
            time_ratio: Number($("transform-rate").value),
            pitch_shift: Number($("transform-pitch").value),
          }),
        )();
      };
      material.showModal();
    };
    async function showReport(project, artifact) {
      const r = await request(
        `/api/projects/${project}/studio/artifacts/${artifact}`,
      );
      $("material-heading").textContent = tr(
        "素材分析 · 估计值",
        "Material analysis · estimates",
      );
      $("material-body").innerHTML =
        `<div class="analysis-summary"><strong>${r.tempo_bpm ? r.tempo_bpm.toFixed(1) + " BPM" : tr("未检测到节拍", "No tempo detected")}</strong><strong>${r.key ? tr("调性候选：", "Key candidate: ") + esc(r.key) : tr("调性不确定", "Uncertain key")}</strong></div>
        ${r.beat_grid_fit ? `<p class="panel-copy">${tr("节拍网格拟合", "Beat-grid fit")}: ${r.beat_grid_fit.bpm.toFixed(2)} BPM · ${tr("残差", "residual")} ${(r.beat_grid_fit.residual_seconds * 1000).toFixed(1)} ms</p>` : ""}
        <p class="panel-copy">${tr("调性相关性分差", "Key correlation margin")}: ${r.key_margin?.toFixed(3)} · ${tr("首个估计节拍", "First estimated beat")}: ${r.beats?.[0]?.toFixed(3) ?? "—"} s</p>
        <p class="panel-copy">${tr("整段全局估计，无法证明和弦、转调或主旋律正确。节拍可能存在半速/倍速与起拍误差。", "Global estimates do not verify chords, modulations or melody. Tempo may have half/double-time and downbeat errors.")}</p>
        <pre>${esc(JSON.stringify(r.levels, null, 2))}</pre>`;
      const task = s.tasks.find(
        (t) =>
          t.source_project === project &&
          t.artifacts.some((a) => a.id === artifact),
      );
      const matchingClip = content()
        .tracks.flatMap((t) => t.clips)
        .find((c) => c.asset && c.id === task?.source_clip?.id &&
          JSON.stringify(c) === JSON.stringify(task.source_clip));
      if (matchingClip) {
        $("material-body").insertAdjacentHTML(
          "beforeend",
          `<button id="report-beat-fit" class="primary">${tr("用这些估计打开对拍校准", "Open beat fitting with these estimates")}</button>`,
        );
        $("report-beat-fit").onclick = guarded(() => {
          material.close();
          return api.openBeatFit(StationModelControls.sourceReport(task, r), matchingClip);
        });
      }
      if (!material.open) material.showModal();
    }
    return { render, enhancePiano, enhanceInspector, showReport };
  },
};
