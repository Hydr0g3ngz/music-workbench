"use strict";
window.StationAudition = {
  mount(api) {
    const {
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
    } = api;
    const dialog = document.createElement("dialog");
    dialog.id = "audition-dialog";
    dialog.innerHTML =
      '<div class="dialog-heading"><div><small>COMPARE MATERIAL · ATTENUATION ONLY</small><h2 id="audition-heading"></h2></div><button class="icon-button" data-audition-close aria-label="关闭 / Close">×</button></div><div id="audition-body"></div>';
    document.body.append(dialog);
    const button = document.createElement("button");
    button.id = "candidate-compare";
    $("material-tools").before(button);
    let player,
      project,
      serial = 0,
      prepared,
      preparing = false;
    const stop = () => player?.pause();
    function release() {
      ++serial;
      player?.dispose();
      player = null;
      prepared = null;
    }
    const close = () => {
      release();
      dialog.close();
    };
    dialog.querySelector("[data-audition-close]").onclick = close;
    dialog.addEventListener("close", release);
    button.onclick = guarded(() => open());
    function choices() {
      const clips = content().tracks.flatMap((t) =>
        t.clips
          .filter((c) => c.asset)
          .map((c) => ({
            id: "clip:" + c.id,
            name: `${tr("片段", "Clip")} · ${t.name} / ${c.name}`,
            duration: c.duration,
          })),
      );
      const generations = s.generations
        .filter((t) => t.status === "complete")
        .map((t) => ({
          id: "generation:" + t.id,
          name: `ACE · ${t.composition_context?.section?.name || t.id} · ${t.parameters.mode}`,
          duration: t.audio.duration,
        }));
      const processing = s.tasks
        .filter((t) => t.status === "complete" && t.source_clip)
        .flatMap((t) =>
          t.artifacts
            .filter((a) => a.kind === "audio")
            .map((a) => ({
              id: `processing:${t.id}:${a.id}`,
              name: `${t.model} · ${a.role} · ${t.source_clip.name}`,
              duration: StationModelControls.clipWindow(t).duration,
              fit: t.fit,
              sourceClip: t.source_clip,
            })),
        );
      return [...clips, ...generations, ...processing];
    }
    async function open(preselect = null) {
      ++serial;
      project = s.session.id;
      pause();
      stopPreview();
      release();
      const opening = serial;
      await flush();
      await pollTasks();
      if (s.session.id !== project || opening !== serial) return;
      const rows = choices();
      $("audition-heading").textContent = tr(
        "在相同响度下比较候选",
        "Compare candidates at matched loudness",
      );
      const selected = selectedClip() ? "clip:" + selectedClip().id : null;
      const a = rows.some((r) => r.id === selected) ? selected : rows[0]?.id;
      const b = preselect || rows.find((r) => r.id !== a)?.id || a;
      const options = (value) =>
        rows
          .map(
            (r) =>
              `<option value="${r.id}" ${r.id === value ? "selected" : ""}>${esc(r.name)} · ${r.duration.toFixed(2)} s</option>`,
          )
          .join("");
      $("audition-body").innerHTML =
        `<p class="panel-copy">${tr("比较素材原音，不包含轨道音量、淡变或效果。两侧取相同长度的窗口，起点由你设置；系统不会自动匹配音乐内容或强拍。", "Compare source audio before track gain, fades or effects. Both sides use equal-length windows with your offsets; musical content and downbeats are not automatically aligned.")}</p>
      <form id="audition-form"><div class="audition-pair"><label>A<select id="audition-a">${options(a)}</select></label><label>B<select id="audition-b">${options(b)}</select></label></div><div class="workflow-fields"><label>${tr("A 起点 · 片段内秒数", "A offset · seconds in clip")}<input id="audition-a-offset" type="number" min="0" max="600" step="any" value="0" required></label><label>${tr("B 起点 · 片段内秒数", "B offset · seconds in clip")}<input id="audition-b-offset" type="number" min="0" max="600" step="any" value="0" required></label><label>${tr("试听窗口 · 秒", "Window · seconds")}<input id="audition-duration" type="number" min=".4" max="60" step=".001" value="12" required></label></div><button type="submit" id="audition-prepare" class="primary" ${rows.length < 2 ? "disabled" : ""}>${tr("准备比较", "Prepare comparison")}</button></form>
      <p id="audition-error" role="alert"></p><div id="audition-player" hidden><div class="audition-switch"><button type="button" id="audition-side-a">A</button><button type="button" id="audition-play">▶</button><button type="button" id="audition-side-b">B</button></div><input id="audition-seek" type="range" min="0" step=".01" value="0" aria-label="${tr("试听位置", "Audition position")}"><div class="audition-time"><span id="audition-time"></span><label><input type="checkbox" id="audition-match" checked> ${tr("LUFS 响度匹配", "LUFS loudness matching")}</label></div><label class="field-row">${tr("监听音量", "Monitor level")}<input id="audition-volume" type="range" min="0" max="1" step=".01" value=".7"></label><div id="audition-measurements"></div><p id="audition-match-hint" class="panel-copy"></p></div>`;
      const invalidate = () => {
        release();
        $("audition-player").hidden = true;
      };
      const align = document.createElement("button");
      align.id = "audition-align-fit";
      align.type = "button";
      align.textContent = tr(
        "以对拍参考拍作为两侧起点",
        "Start both sides at the beat-fit anchor",
      );
      $("audition-prepare").before(align);
      const paired = () => {
        const a = rows.find((r) => r.id === $("audition-a").value);
        const b = rows.find((r) => r.id === $("audition-b").value);
        if (a?.fit && b?.id === "clip:" + a.sourceClip.id)
          return [b, a, "b", "a"];
        if (b?.fit && a?.id === "clip:" + b.sourceClip.id)
          return [a, b, "a", "b"];
        return null;
      };
      align.onclick = () => {
        const pair = paired();
        if (!pair) return;
        const [, candidate, originalSide, candidateSide] = pair;
        const relative =
          candidate.fit.options.source_anchor - candidate.sourceClip.offset;
        $("audition-" + originalSide + "-offset").value = relative.toFixed(6);
        $("audition-" + candidateSide + "-offset").value = (
          relative / candidate.fit.time_ratio
        ).toFixed(6);
        invalidate();
      };
      const updatePair = () => {
        align.disabled = !paired();
      };
      $("audition-form").addEventListener("change", updatePair);
      updatePair();
      $("audition-form").addEventListener("input", invalidate);
      $("audition-form").addEventListener("change", invalidate);
      $("audition-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(async () => {
          if (preparing) return;
          preparing = true;
          release();
          const token = serial,
            currentProject = project;
          $("audition-prepare").disabled = true;
          $("audition-error").textContent = "";
          try {
            await flush();
            if (currentProject !== s.session.id) return;
            const metadata = await request(base() + "/comparisons", {
              revision: s.session.revision,
              a: $("audition-a").value,
              b: $("audition-b").value,
              a_offset: Number($("audition-a-offset").value),
              b_offset: Number($("audition-b-offset").value),
              duration: Number($("audition-duration").value),
            });
            if (
              token !== serial ||
              !dialog.open ||
              currentProject !== s.session.id
            )
              return;
            prepared = metadata;
            player = new MatchedABPlayer(
              new Audio(),
              new Audio(),
              metadata,
              paint,
            );
            player.setVolume(Number($("audition-volume").value));
            $("audition-seek").max = String(metadata.duration);
            $("audition-player").hidden = false;
            $("audition-match").checked = metadata.matching_available;
            $("audition-match").disabled = !metadata.matching_available;
            $("audition-match-hint").textContent = metadata.matching_available
              ? tr(
                  `相同窗口 ${metadata.duration.toFixed(3)} 秒，匹配到 ${metadata.target_lufs.toFixed(2)} LUFS；仅衰减，不写回工程。`,
                  `Equal ${metadata.duration.toFixed(3)} s windows, matched to ${metadata.target_lufs.toFixed(2)} LUFS; attenuation only, never written to the project.`,
                )
              : tr(
                  "当前窗口无法测量 LUFS（静音、低于门限或未安装响度依赖）；仍可原音比较。",
                  "LUFS is unavailable for this window (silence, below gate or missing runtime); raw comparison remains available.",
                );
            $("audition-measurements").innerHTML = ["a", "b"]
              .map(
                (side) =>
                  `<p><b>${side.toUpperCase()}</b> ${esc(metadata[side].name)}<span>${metadata[side].measurement.integrated_lufs?.toFixed(2) ?? "—"} LUFS · ${metadata[side].gain_db.toFixed(2)} dB</span></p>`,
              )
              .join("");
            paint();
          } catch (e) {
            if (token === serial) $("audition-error").textContent = e.message;
          } finally {
            preparing = false;
            if ($("audition-prepare")) $("audition-prepare").disabled = false;
          }
        })();
      };
      $("audition-side-a").onclick = guarded(() => player?.select("a"));
      $("audition-side-b").onclick = guarded(() => player?.select("b"));
      $("audition-play").onclick = guarded(async () => {
        if (!player) return;
        if (player.desiredPlaying) player.pause();
        else await player.play();
        paint();
      });
      $("audition-seek").oninput = () =>
        player?.seek(Number($("audition-seek").value));
      $("audition-match").onchange = () =>
        player?.setMatching($("audition-match").checked);
      $("audition-volume").oninput = () =>
        player?.setVolume(Number($("audition-volume").value));
      if (!dialog.open) dialog.showModal();
    }
    function paint() {
      if (!player || !$("audition-player")) return;
      $("audition-side-a").setAttribute(
        "aria-pressed",
        String(player.side === "a"),
      );
      $("audition-side-b").setAttribute(
        "aria-pressed",
        String(player.side === "b"),
      );
      $("audition-play").textContent = player.desiredPlaying ? "Ⅱ" : "▶";
      $("audition-time").textContent =
        `${player.current.currentTime.toFixed(2)} / ${player.duration.toFixed(2)} s`;
      $("audition-seek").value = String(player.current.currentTime);
    }
    return {
      open,
      stop,
      render() {
        button.textContent = tr("候选 A/B", "Candidate A/B");
        if (dialog.open && project !== s.session.id) close();
      },
      diagnostics() {
        return {
          metadata: prepared,
          side: player?.side,
          time: player?.current.currentTime,
          playing: player?.desiredPlaying,
        };
      },
    };
  },
};
