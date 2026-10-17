"use strict";
window.StationCompositionUI = {
  mount(api) {
    const {
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
    } = api;
    const C = StationComposition;
    const label = (pair) => tr(...pair);
    const option = (dict, value) =>
      Object.entries(dict)
        .map(
          ([k, v]) =>
            `<option value="${k}" ${k === value ? "selected" : ""}>${esc(label(v.name || v))}</option>`,
        )
        .join("");
    const button = document.createElement("button");
    button.id = "composition-open";
    $("section-settings").before(button);
    const dialog = document.createElement("dialog");
    dialog.id = "composition-dialog";
    dialog.innerHTML =
      '<div class="dialog-heading"><div><small>COMPOSE → DEVELOP → ARRANGE → REFINE</small><h2 id="composition-heading"></h2></div><button class="icon-button" aria-label="关闭 / Close" data-composition-close>×</button></div><div id="composition-body"></div>';
    document.body.append(dialog);
    dialog.querySelector("[data-composition-close]").onclick = () =>
      dialog.close();
    let activeTab = "blueprint";
    const open = (tab = "blueprint") => {
      activeTab = tab;
      draw();
      if (!dialog.open) dialog.showModal();
    };
    button.onclick = () => open();
    function draw() {
      $("composition-heading").textContent = tr(
        "把灵感发展成作品",
        "Turn an idea into a piece",
      );
      $("composition-body").innerHTML = `
        <nav class="composition-tabs" aria-label="${tr("创作流程", "Creative workflow")}">
          ${[
            ["blueprint", tr("1 · 创作蓝图", "1 · Blueprint")],
            ["sections", tr("2 · 段落发展", "2 · Development")],
            ["review", tr("3 · 编排与打磨", "3 · Arrange & refine")],
          ]
            .map(
              ([k, v]) =>
                `<button data-composition-tab="${k}" aria-pressed="${k === activeTab}">${v}</button>`,
            )
            .join("")}
        </nav><p class="composition-intro">${tr("先明确想表达什么，再生成素材、做变化并组织段落。这里的方法都可选，没有适用于所有风格的标准曲式。", "Set an intention, generate material, develop variations and arrange sections. These methods are optional; there is no universal song form.")}</p><div id="composition-tab-body"></div>`;
      $("composition-body")
        .querySelectorAll("[data-composition-tab]")
        .forEach(
          (b) =>
            (b.onclick = () => {
              activeTab = b.dataset.compositionTab;
              draw();
            }),
        );
      ({
        blueprint: drawBlueprint,
        sections: drawSections,
        review: drawReview,
      })[activeTab]();
    }
    function drawBlueprint() {
      const b = content().blueprint || {};
      $("composition-tab-body").innerHTML =
        `<div class="composition-columns"><form id="blueprint-form">
        ${[
          [
            "brief",
            320,
            tr("作品意图", "Creative brief"),
            tr(
              "例如：清晨城市醒来，从孤独走向明亮。",
              "e.g. A city waking up, moving from solitude into daylight.",
            ),
          ],
          [
            "palette",
            240,
            tr("音色与乐器", "Instrument palette"),
            tr(
              "例如：柔和电钢琴、拨弦贝斯、克制的鼓；给主旋律留空间。",
              "e.g. Soft electric piano, plucked bass, restrained drums; space for the melody.",
            ),
          ],
          [
            "motif",
            240,
            tr("贯穿作品的动机", "Motif to preserve"),
            tr(
              "例如：短短长的三音节奏；主题再现时换高八度。",
              "e.g. A short–short–long three-note rhythm; return an octave higher.",
            ),
          ],
          [
            "harmony",
            240,
            tr("和声方向（可留空）", "Harmonic direction (optional)"),
            tr(
              "例如：先稳定在主调，高潮前增加悬念。",
              "e.g. Establish the home key; add harmonic tension before the peak.",
            ),
          ],
        ]
          .map(
            ([k, max, title, placeholder]) =>
              `<label class="composition-field">${title}<textarea id="blueprint-${k}" maxlength="${max}" rows="2" placeholder="${esc(placeholder)}">${esc(b[k] || "")}</textarea></label>`,
          )
          .join("")}
        <button class="primary" type="submit">${tr("保存蓝图", "Save blueprint")}</button><span class="composition-save-hint">${tr("保存后可撤销，随便携工程一起带走。", "Undo is available after saving; included in portable projects.")}</span></form>
        <aside class="composition-note"><span class="composition-kicker">IDEA → MATERIAL</span><h3>${tr("让下一次生成有共同方向", "Give each generation a shared direction")}</h3><p>${tr("蓝图会和当前段落的目标一起进入 AI 提示词。先建立一个清楚的动机，再用同一片段做参考变奏，比每一段都重新抽卡更容易连贯。", "The blueprint and section intentions enter the AI prompt. Establish a clear motif, then use that clip for reference variation to help connect sections.")}</p><button type="button" id="blueprint-generate">${tr("保存并打开 AI 生成", "Save & open AI generation")} ↗</button><p>${tr("文字描述只是意图。精确保留音符需要 MIDI 编辑；参考变奏也要试听核验。", "Text expresses intent. Exact note retention needs MIDI editing; reference variations still need auditioning.")}</p><a href="https://online.berklee.edu/takenote/simple-tools-for-better-melodies/" target="_blank" rel="noreferrer">Berklee · ${tr("动机、重复与对比", "Motif, repetition & contrast")} ↗</a></aside></div>`;
      const save = async () => {
        const blueprint = Object.fromEntries(
          ["brief", "palette", "motif", "harmony"].map((k) => [
            k,
            $("blueprint-" + k).value.trim(),
          ]),
        );
        mutate(() => (content().blueprint = blueprint));
        await flush();
        toast(tr("创作蓝图已保存", "Blueprint saved"));
      };
      $("blueprint-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(save)();
      };
      $("blueprint-generate").onclick = guarded(async () => {
        await save();
        dialog.close();
        $("open-generation").click();
      });
    }
    function drawSections() {
      const sections = content().sections || [];
      $("composition-tab-body").innerHTML =
        `<div class="composition-columns"><div>
        <div class="composition-template"><h3>${tr("从结构草案开始", "Start with a structure sketch")}</h3><label>${tr("可选模板 · 4/4", "Optional template · 4/4")}<select id="composition-template">${option(C.templates, "arc")}</select></label><div id="composition-template-preview" class="composition-arc"></div><p id="composition-template-length" class="panel-copy"></p>
        ${sections.length ? `<label class="composition-check"><input id="composition-replace" type="checkbox">${tr("替换现有段落标记（保留音轨和音频）", "Replace existing section markers; keep tracks and audio")}</label>` : ""}
        <button type="button" id="composition-apply-template">${tr("采用结构草案", "Apply structure sketch")}</button><small>${tr("采用后可修改长度与顺序，也可一次撤销。", "Edit lengths and order afterward, or undo in one step.")}</small></div>
        <label class="composition-field">${tr("编辑段落目标", "Edit section intentions")}<select id="composition-section">${sections.map((m) => `<option value="${m.id}">${esc(m.name)} · ${m.start / 4 + 1} → ${m.end / 4 + 1}</option>`).join("")}</select></label><div id="composition-section-editor"></div></div>
        <aside class="composition-note"><span class="composition-kicker">MATERIAL → JOURNEY</span><h3>${tr("重复建立记忆，变化推动发展", "Repeat to establish, vary to develop")}</h3><p>${tr("每段先决定一个任务：引入、推进、对比或收束。能量表示作品内部的相对意图，不要求每首作品都逐步走向高潮。", "Give a section a purpose: introduce, develop, contrast or resolve. Energy is a relative intention within the piece; a rising climax is optional.")}</p><p>${tr("想做减法编曲，可以先复制一个丰富的段落，再逐段移除部分鼓、贝斯或铺底，留下主角。", "For subtractive arranging, copy a rich section, then remove some drums, bass or pads to make room for the foreground.")}</p><button type="button" id="composition-range-tools">${tr("打开段落位置与范围复制", "Open section timing & range copy")} ↗</button><a href="https://makingmusic.ableton.com/dramatic-arc" target="_blank" rel="noreferrer">Ableton · Dramatic Arc ↗</a><a href="https://makingmusic.ableton.com/arranging-as-a-subtractive-process" target="_blank" rel="noreferrer">Ableton · Subtractive Arranging ↗</a></aside></div>`;
      let candidate;
      const preview = () => {
        candidate = C.template(
          $("composition-template").value,
          content().bpm,
          uid,
          (role) => label(C.roles[role]),
        );
        $("composition-template-preview").innerHTML = candidate
          .map(
            (m) =>
              `<div style="flex:${m.end - m.start};--energy:${m.energy}"><span>${esc(m.name)}</span><b>${m.energy}/5</b><small>${(m.end - m.start) / 4}${tr("小节", " bars")}</small></div>`,
          )
          .join("");
        $("composition-template-length").textContent = tr(
          `共 ${candidate.at(-1).end / 4} 小节 · ${((candidate.at(-1).end * 60) / content().bpm).toFixed(1)} 秒；仅创建标记，不自动填充音乐。`,
          `Total ${candidate.at(-1).end / 4} bars · ${((candidate.at(-1).end * 60) / content().bpm).toFixed(1)} s; markers only, no music is filled in.`,
        );
        $("composition-apply-template").disabled =
          sections.length > 0 && !$("composition-replace").checked;
      };
      $("composition-template").onchange = guarded(preview);
      if ($("composition-replace")) $("composition-replace").onchange = preview;
      $("composition-apply-template").onclick = guarded(() => {
        mutate(() => (content().sections = candidate));
        drawSections();
        toast(
          tr("段落草案已采用，可撤销", "Structure applied; undo is available"),
        );
      });
      $("composition-range-tools").onclick = () => {
        dialog.close();
        $("section-settings").click();
      };
      $("composition-section").onchange = drawSectionEditor;
      preview();
      drawSectionEditor();
    }
    function drawSectionEditor() {
      const m = (content().sections || []).find(
        (x) => x.id === $("composition-section").value,
      );
      if (!m) {
        $("composition-section-editor").innerHTML =
          `<p class="panel-copy">${tr("先采用模板或添加段落标记。", "Apply a template or add section markers first.")}</p>`;
        return;
      }
      $("composition-section-editor").innerHTML =
        `<form id="section-intention-form"><div class="workflow-fields"><label>${tr("段落角色", "Section role")}<select id="composition-role">${option(C.roles, m.role || "free")}</select></label><label>${tr("预期能量 · 1–5", "Intended energy · 1–5")}<select id="composition-energy"><option value="">${tr("未指定", "Unspecified")}</option>${[1, 2, 3, 4, 5].map((v) => `<option ${v === m.energy ? "selected" : ""}>${v}</option>`).join("")}</select></label></div><label class="composition-field">${tr("这一段要发生什么？", "What should happen here?")}<textarea id="composition-intention" maxlength="240" rows="3" placeholder="${tr("例如：保留主题，移除鼓；最后一小节留白进入下一段。", "e.g. Keep the motif, remove drums; leave space in the last bar.")}">${esc(m.intention || "")}</textarea></label><div class="composition-actions"><button class="primary" type="submit">${tr("保存段落目标", "Save section intentions")}</button><button type="button" id="composition-section-generate">${tr("保存并为此段生成", "Save & generate for section")} ↗</button><button type="button" id="composition-section-listen">${tr("定位试听", "Locate section")}</button></div></form>`;
      const save = async () => {
        mutate(() =>
          Object.assign(m, {
            role: $("composition-role").value,
            energy: $("composition-energy").value
              ? Number($("composition-energy").value)
              : null,
            intention: $("composition-intention").value.trim(),
          }),
        );
        await flush();
        toast(tr("段落目标已保存", "Section intentions saved"));
      };
      $("section-intention-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(save)();
      };
      $("composition-section-generate").onclick = guarded(async () => {
        await save();
        dialog.close();
        seek((m.start * 60) / content().bpm);
        $("open-generation").click();
        $("generation-use-blueprint").checked = true;
        $("generation-section").value = m.id;
        refreshContext();
      });
      $("composition-section-listen").onclick = () => {
        dialog.close();
        seek((m.start * 60) / content().bpm);
      };
    }
    function drawReview() {
      const r = C.observe(content()),
        c = selectedClip();
      $("composition-tab-body").innerHTML =
        `<div class="composition-columns"><div><h3>${tr("意图与素材布局对照", "Intentions & material layout")}</h3><p class="panel-copy">${tr("层数是有效片段覆盖时长的平均值，音频静音处也会计入；MIDI 按可见音符计算。它不代表响度、能量或音乐质量。", "Layers average the duration covered by active clips, including silence within audio; MIDI uses visible note spans. This measures neither loudness, energy nor musical quality.")}</p>${r.rows.length ? `<div class="composition-table"><table><thead><tr><th>${tr("段落", "Section")}</th><th>${tr("意图", "Intent")}</th><th>${tr("覆盖", "Coverage")}</th><th>${tr("平均层数", "Avg layers")}</th></tr></thead><tbody>${r.rows.map((m) => `<tr><td><button data-composition-locate="${m.id}">${esc(m.name)}</button></td><td>${m.energy ?? "—"}/5</td><td>${(m.coverage * 100).toFixed(0)}%</td><td>${m.layers.toFixed(1)}</td></tr>`).join("")}</tbody></table></div>` : `<p>${tr("添加段落后，可以看到每段的素材覆盖。", "Add sections to inspect their material coverage.")}</p>`}
        <div class="composition-observations">${
          [
            [
              !r.rows.length,
              tr(
                "尚未划分段落，可先画结构草案。",
                "No section markers yet; sketch a structure first.",
              ),
            ],
            [
              r.rows.some((m) => m.coverage < 0.99),
              tr(
                "部分段落存在素材留白：确认这是有意的停顿，或继续生成 / 编排。",
                "Some sections contain gaps in material: keep intentional pauses, or generate / arrange more.",
              ),
            ],
            [
              r.gaps,
              tr(
                `段落标记之间有 ${r.gaps} 处留白；标记不覆盖音乐也可以。`,
                `${r.gaps} gaps between section markers; unmarked music is allowed.`,
              ),
            ],
            [
              r.overlaps,
              tr(
                `段落标记有 ${r.overlaps} 处重叠；确认范围是否符合预期。`,
                `${r.overlaps} overlapping section markers; check the intended ranges.`,
              ),
            ],
            [
              !content().blueprint?.motif,
              tr(
                "可以记录一个反复出现的动机，帮助后续 AI 变奏保持共同方向。",
                "Record a recurring motif to give later AI variations a shared direction.",
              ),
            ],
            [
              r.edges,
              tr(
                `${r.edges} 个音频片段至少一端未淡变，可试听接缝再决定是否处理。`,
                `${r.edges} audio clips have an unfaded edge; audition the joins before editing.`,
              ),
            ],
          ]
            .filter(([show]) => show)
            .map(([, text]) => `<p>○ ${text}</p>`)
            .join("") ||
          `<p>${tr("布局检查没有额外提示，继续用耳朵判断段落发展。", "No additional layout observations; audition the development.")}</p>`
        }</div>
        <div class="composition-template"><h3>${tr("处理选中片段的接缝", "Refine selected clip edges")}</h3><p>${c ? esc(c.name) : tr("先选中一个音频片段。", "Select an audio clip first.")}</p><p class="panel-copy">${tr("15 ms 防点击淡变只处理片段边缘，不是跨片段过渡。已有较长淡变会保留。", "15 ms edge fades may help clicks; they do not create a transition between clips. Existing longer fades are retained.")}</p><button id="composition-soften" ${!c || selectedTrack()?.kind !== "audio" ? "disabled" : ""}>${tr("为选中音频添加 15 ms 边缘淡变", "Add 15 ms edge fades to selected audio")}</button></div></div>
        <aside class="composition-note"><span class="composition-kicker">ARRANGE → REFINE</span><h3>${tr("每次只解决一个听感问题", "Focus each comparison")}</h3><p>${tr("先比较段落有没有推进，再关注主角是否清楚、低频是否拥挤、接缝是否自然。不要用更响来代替更好。", "Compare section development first, then foreground clarity, low-end balance and joins. A louder candidate is not necessarily better.")}</p><p>${tr("AI 分轨可帮助做减法；CREPE 可把单旋律转为 MIDI，再人工修正、变奏。素材适配里的 BPM / 调性分析是估计值。", "AI stem separation helps subtractive arranging. CREPE converts monophonic material to editable MIDI. Tempo / key analysis in Material / AI provides estimates.")}</p><button type="button" id="composition-material">${tr("打开素材适配 / AI", "Open Material / AI")} ↗</button><a href="https://www.izotope.com/en/learn/13-tips-for-using-references-while-mixing" target="_blank" rel="noreferrer">iZotope · ${tr("等响度参考试听方法", "Level-matched reference methods")} ↗</a></aside></div>`;
      $("composition-tab-body")
        .querySelectorAll("[data-composition-locate]")
        .forEach(
          (b) =>
            (b.onclick = () => {
              const m = content().sections.find(
                (x) => x.id === b.dataset.compositionLocate,
              );
              dialog.close();
              seek((m.start * 60) / content().bpm);
            }),
        );
      $("composition-soften").onclick = guarded(() => {
        mutate(() => Object.assign(c, C.soften(c)));
        drawReview();
        toast(
          tr("已添加边缘淡变，可撤销", "Edge fades applied; undo is available"),
        );
      });
      $("composition-material").disabled =
        !c || selectedTrack()?.kind !== "audio";
      $("composition-material").onclick = () => {
        dialog.close();
        $("material-tools").click();
      };
    }
    const generation = document.createElement("section");
    generation.className = "generation-blueprint";
    $("generation-context").before(generation);
    let previewSerial = 0;
    function prepareGeneration() {
      const beat = (s.position * content().bpm) / 60;
      const selected = (content().sections || []).find(
        (m) => m.start <= beat && m.end > beat,
      );
      const hasContext =
        Object.values(content().blueprint || {}).some((v) => v.trim()) ||
        (content().sections || []).length > 0;
      generation.innerHTML = `<label class="composition-check"><input id="generation-use-blueprint" type="checkbox" ${hasContext ? "checked" : ""}>${tr("使用已保存的创作蓝图与段落目标", "Use saved blueprint & section intentions")}</label><div class="workflow-fields"><label>${tr("目标段落（可选）", "Target section (optional)")}<select id="generation-section"><option value="">${tr("整首方向", "Whole-piece direction")}</option>${(content().sections || []).map((m) => `<option value="${m.id}" ${m.id === selected?.id ? "selected" : ""}>${esc(m.name)}</option>`).join("")}</select></label><label>${tr("这次生成的任务", "Purpose of this generation")}<select id="generation-development">${option(C.developments, "establish")}</select></label></div><div class="composition-actions"><button type="button" id="generation-use-section-duration">${tr("按段落设置时长", "Use section duration")}</button><button type="button" id="generation-preview-prompt">${tr("预览实际提示词", "Preview actual prompt")}</button></div><p id="generation-blueprint-hint" class="panel-copy"></p><pre id="generation-compiled-prompt" hidden></pre>`;
      generation
        .querySelectorAll("input,select")
        .forEach((n) => (n.onchange = refreshContext));
      $("generation-preview-prompt").onclick = guarded(async () => {
        const serial = ++previewSerial,
          project = s.session.id;
        await flush();
        if (project !== s.session.id) return;
        const payload = generationPayload();
        const result = await request(base() + "/generation-preview", {
          revision: s.session.revision,
          ...payload,
        });
        if (
          serial !== previewSerial ||
          project !== s.session.id ||
          JSON.stringify(payload) !== JSON.stringify(generationPayload())
        )
          return;
        $("generation-compiled-prompt").hidden = false;
        $("generation-compiled-prompt").textContent =
          `${result.bpm} BPM · ${result.key || "Auto"} · ${result.duration}s\n\n${result.prompt}`;
      });
      $("generation-use-section-duration").onclick = guarded(() => {
        const m = content().sections.find(
          (x) => x.id === $("generation-section").value,
        );
        if (!m) return;
        const exact = ((m.end - m.start) * 60) / content().bpm,
          seconds = Math.round(exact);
        if (seconds < 10 || seconds > 60)
          throw Error(
            tr(
              "当前模型每次支持 10–60 秒，请拆分段落或使用其他时长。",
              "This model supports 10–60 s per draft; split the section or use another duration.",
            ),
          );
        if (
          ![...$("generation-duration").options].some(
            (o) => o.value === String(seconds),
          )
        )
          $("generation-duration").add(
            new Option(`${seconds}s`, String(seconds)),
          );
        $("generation-duration").value = String(seconds);
        refreshContext();
        toast(
          tr(
            `计划 ${exact.toFixed(2)} 秒，生成 ${seconds} 秒；采用后可裁剪。`,
            `Planned ${exact.toFixed(2)} s, generating ${seconds} s; trim after adoption.`,
          ),
        );
      });
      refreshContext();
    }
    function refreshContext() {
      if (!$("generation-use-blueprint")) return;
      previewSerial++;
      const enabled = $("generation-use-blueprint").checked;
      const cover = $("generation-mode").value !== "text2music";
      $("repaint-options").hidden = $("generation-mode").value !== "repaint";
      $("generation-duration").disabled = cover;
      $("generation-use-region").disabled = cover;
      if (cover && selectedClip()) {
        const seconds = Math.round(selectedClip().duration);
        if (
          ![...$("generation-duration").options].some(
            (o) => o.value === String(seconds),
          )
        )
          $("generation-duration").add(
            new Option(`${seconds}s`, String(seconds)),
          );
        $("generation-duration").value = String(seconds);
      }
      $("generation-section").disabled = !enabled;
      $("generation-development").disabled = !enabled;
      $("generation-key").disabled = enabled;
      $("generation-use-section-duration").disabled =
        !enabled || !$("generation-section").value || cover;
      $("generation-compiled-prompt").hidden = true;
      $("generation-blueprint-hint").textContent = tr(
        enabled
          ? "蓝图启用：BPM 与调性使用工程设置。提示词由规则组装，ACE-Step 负责生成；文字意图不保证音符或节奏符合。参考变奏的时长跟随参考片段。"
          : "蓝图已关闭，使用当前手填描述。",
        enabled
          ? "Blueprint enabled: tempo and key follow the project. Rules assemble the prompt; ACE-Step generates the audio. Intentions do not guarantee note or tempo compliance. Reference variations follow source-clip duration."
          : "Blueprint off; using your description alone.",
      );
    }
    function generationPayload() {
      return {
        prompt: $("generation-prompt").value,
        lyrics: $("generation-lyrics").value,
        instrumental: $("generation-instrumental").checked,
        duration: Number($("generation-duration").value),
        bpm: Math.round(content().bpm),
        key: $("generation-key").value,
        mode: $("generation-mode").value,
        source_clip:
          $("generation-mode").value !== "text2music"
            ? selectedClip()?.id
            : null,
        repaint_start: Number($("repaint-start").value),
        repaint_end: Number($("repaint-end").value),
        reference_strength: Number($("generation-strength").value),
        seed: Number($("generation-seed").value),
        steps: Number($("generation-steps").value),
        language: $("generation-instrumental").checked
          ? "unknown"
          : $("generation-language").value,
        use_blueprint: $("generation-use-blueprint")?.checked || false,
        section_id: $("generation-use-blueprint")?.checked
          ? $("generation-section").value || null
          : null,
        development: $("generation-development")?.value || "establish",
      };
    }
    $("generation-form").addEventListener("input", () => {
      previewSerial++;
      if ($("generation-compiled-prompt"))
        $("generation-compiled-prompt").hidden = true;
    });
    $("generation-form").addEventListener("click", (event) => {
      if (
        event.target.closest("[data-generation-preset], #generation-use-region")
      )
        refreshContext();
    });
    $("generation-mode").addEventListener("change", refreshContext);
    return {
      render() {
        button.textContent = tr("创作蓝图", "Creative blueprint");
      },
      prepareGeneration,
      generationPayload,
      open,
    };
  },
};
