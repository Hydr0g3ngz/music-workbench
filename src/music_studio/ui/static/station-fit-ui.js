"use strict";
window.StationFitUI = {
  mount(api) {
    const {
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
    } = api;
    const dialog = document.createElement("dialog");
    dialog.id = "fit-dialog";
    dialog.innerHTML =
      '<div class="dialog-heading"><div><small>ANALYZE → ANCHOR → FIT → AUDITION</small><h2 id="fit-heading"></h2></div><button class="icon-button" data-fit-close aria-label="关闭 / Close">×</button></div><div id="fit-body"></div>';
    document.body.append(dialog);
    const audio = new Audio();
    let snapshot,
      report,
      clip,
      asset,
      sourceKey,
      loaded = 0,
      playSerial = 0,
      timer,
      busy = false;
    const stop = () => {
      ++playSerial;
      audio.pause();
      clearTimeout(timer);
    };
    const close = () => {
      stop();
      dialog.close();
    };
    dialog.querySelector("[data-fit-close]").onclick = close;
    dialog.addEventListener("close", () => {
      stop();
      audio.removeAttribute("src");
      audio.load();
      sourceKey = null;
    });
    const button = document.createElement("button");
    button.id = "beat-fit-open";
    $("material-tools").before(button);
    button.onclick = guarded(() => open());
    function opts() {
      return {
        source_bpm: Number($("fit-source-bpm").value),
        tempo_multiplier: Number($("fit-tempo-multiplier").value),
        source_anchor: Number($("fit-anchor").value),
        target_beat: (Number($("fit-target-bar").value) - 1) * 4,
      };
    }
    function checkSnapshot() {
      const current = content()
        .tracks.flatMap((t) => t.clips)
        .find((c) => c.id === clip.id);
      if (
        s.session.id !== snapshot.project ||
        JSON.stringify(current) !== snapshot.clip
      )
        throw Error(
          tr(
            "源片段已经变化，请重新打开对拍校准。",
            "Source clip changed; reopen beat fitting.",
          ),
        );
    }
    async function open(chosenReport = null, reportClip = null) {
      pause();
      stopPreview();
      stop();
      const current = reportClip || selectedClip();
      if (!current?.asset)
        throw Error(tr("请选择音频片段", "Select an audio clip"));
      clip = structuredClone(current);
      asset = s.session.assets.find((a) => a.id === clip.asset);
      report = chosenReport;
      snapshot = { project: s.session.id, clip: JSON.stringify(current) };
      if (!report) {
        const row = s.tasks.find(
          (t) =>
            t.status === "complete" &&
            t.model === "musical-analysis" &&
            t.source_clip?.asset === clip.asset,
        );
        const a = row?.artifacts.find((a) => a.role === "musical-analysis");
        if (a)
          report = await request(
            `/api/projects/${row.source_project}/studio/artifacts/${a.id}`,
          );
        if (s.session.id !== snapshot.project) return;
      }
      $("fit-heading").textContent = tr(
        "把一拍对到目标小节",
        "Align a beat to a target bar",
      );
      const estimate =
        report?.beat_grid_fit?.bpm || report?.tempo_bpm || content().bpm;
      const estimatedAnchor = report?.beats?.find(
        (b) => b >= clip.offset && b < clip.offset + clip.duration,
      );
      const anchor = estimatedAnchor ?? clip.offset;
      const targetBar = Math.max(
        2,
        Math.round((s.position * content().bpm) / 240) + 1,
      );
      $("fit-body").innerHTML =
        `<p class="panel-copy">${esc(clip.name)} · ${tr("波形显示当前片段。点击波形选择你确认的强拍，再指定它要落到哪个小节。白线为估计拍点，紫线是按当前 BPM 展开的参考网格。", "The waveform shows the current trim. Click a beat you confirm by ear, then choose its target bar. White lines are estimated beats; purple lines show the current tempo grid.")}</p>
      <canvas id="fit-wave" width="960" height="160" tabindex="0" role="img" aria-label="${tr("点击波形选择参考拍；也可输入源时间", "Click waveform to select an anchor, or enter its source time")}"></canvas>
      <div class="fit-wave-caption"><span>${clip.offset.toFixed(3)} s</span><span>${(clip.offset + clip.duration).toFixed(3)} s</span></div>
      <form id="beat-fit-form"><div class="workflow-fields"><label>${tr("素材 BPM", "Source BPM")}<input id="fit-source-bpm" type="number" min="30" max="300" step="any" value="${estimate.toFixed(6)}" required></label><label>${tr("节拍解释", "Tempo interpretation")}<select id="fit-tempo-multiplier"><option value=".5">½ · ${tr("半速", "Half-time")}</option><option value="1" selected>1×</option><option value="2">2× · ${tr("倍速", "Double-time")}</option></select></label><label>${tr("源参考拍 · 秒", "Source anchor · seconds")}<input id="fit-anchor" type="number" min="${clip.offset}" max="${clip.offset + clip.duration - 1 / 44100}" step="any" value="${anchor.toFixed(6)}" required></label><label>${tr("对齐到小节 · 4/4", "Align to bar · 4/4")}<input id="fit-target-bar" type="number" min="1" step=".0625" value="${targetBar}" required></label></div>
      <div class="fit-actions"><button type="button" id="fit-audition">▶ ${tr("从参考拍试听 4 秒", "Audition 4 s from anchor")}</button><button type="button" id="fit-use-playhead">${tr("目标设为播放头所在小节", "Use playhead bar")}</button></div>
      <details><summary>${tr("用两拍校准 BPM", "Calibrate BPM from two beats")}</summary><p class="panel-copy">${tr("先选第一拍，再选较远的一拍并输入两者之间的拍数间隔。第 1 拍到第 17 拍是 16 个间隔。此处仅计算，不检测强拍。", "Choose a first beat and a later beat, then enter the number of intervals. Beat 1 to beat 17 is 16 intervals. This calculates tempo; it does not detect downbeats.")}</p><div class="workflow-fields"><label>${tr("较晚一拍 · 源秒数", "Later beat · source seconds")}<input id="fit-last-anchor" type="number" step="any" value="${Math.min(clip.offset + clip.duration - 0.01, anchor + 8).toFixed(6)}"></label><label>${tr("拍数间隔", "Beat intervals")}<input id="fit-intervals" type="number" min="1" max="256" step="1" value="16"></label></div><button type="button" id="fit-calculate-bpm">${tr("计算并使用 BPM", "Calculate & use BPM")}</button></details>
      <div id="fit-summary" class="fit-summary" role="status"></div><p class="panel-copy">${report?.beat_grid_fit ? tr(`估计拟合残差 ${(report.beat_grid_fit.residual_seconds * 1000).toFixed(1)} ms。`, `Estimated fit residual ${(report.beat_grid_fit.residual_seconds * 1000).toFixed(1)} ms. `) : ""}${tr("这些拍点不是强拍真值；自由速度、变速音乐可能无法用恒定速度对齐。生成的是 DSP 变速候选，不改变音高。原片段保留，试听后再采用。", "Beat estimates are not downbeat truth. A single tempo may not fit free or varying timing. This creates a DSP time-stretch candidate without changing pitch; audition before replacing the original.")}</p><p id="fit-error" role="alert"></p><button id="fit-submit" class="primary" type="submit">${tr("制作对拍候选", "Create beat-fit candidate")}</button></form>`;
      $("fit-wave").onclick = (e) => {
        const box = e.currentTarget.getBoundingClientRect(),
          fraction = Math.max(
            0,
            Math.min(
              1 - 1 / (44100 * clip.duration),
              (e.clientX - box.left) / box.width,
            ),
          );
        $("fit-anchor").value = (
          clip.offset +
          clip.duration * fraction
        ).toFixed(6);
        update();
      };
      $("beat-fit-form").addEventListener("input", update);
      $("fit-audition").onclick = guarded(async () => {
        stop();
        checkSnapshot();
        const at = Number($("fit-anchor").value);
        if (at < clip.offset || at >= clip.offset + clip.duration)
          throw Error(
            tr("请选择片段内的参考拍", "Choose an anchor inside the clip"),
          );
        await play(at);
      });
      $("fit-use-playhead").onclick = () => {
        $("fit-target-bar").value =
          Math.floor((s.position * content().bpm) / 240) + 1;
        update();
      };
      $("fit-calculate-bpm").onclick = guarded(() => {
        const later = Number($("fit-last-anchor").value);
        if (later < clip.offset || later >= clip.offset + clip.duration)
          throw Error(
            tr(
              "较晚一拍也需要位于当前片段内",
              "The later beat must also be inside the current clip",
            ),
          );
        $("fit-source-bpm").value = StationFit.tappedBpm(
          Number($("fit-anchor").value),
          later,
          Number($("fit-intervals").value),
        ).toFixed(6);
        $("fit-tempo-multiplier").value = "1";
        update();
      });
      $("beat-fit-form").onsubmit = (e) => {
        e.preventDefault();
        guarded(async () => {
          if (busy) return;
          busy = true;
          $("fit-submit").disabled = true;
          try {
            checkSnapshot();
            await flush();
            checkSnapshot();
            const fit = opts();
            await request(base() + "/fit-preview", {
              revision: s.session.revision,
              clip: clip.id,
              fit,
            });
            await request(base() + "/process", {
              revision: s.session.revision,
              clip: clip.id,
              model: "time-pitch",
              fit,
            });
            close();
            dock("tasks");
            await pollTasks();
            toast(
              tr(
                "对拍候选已排队；完成后先 A/B 再采用",
                "Beat-fit candidate queued; compare A/B before adoption",
              ),
            );
          } finally {
            busy = false;
            if ($("fit-submit")) update();
          }
        })();
      };
      update();
      if (!dialog.open) dialog.showModal();
    }
    async function play(at) {
      const serial = ++playSerial;
      const key = snapshot.project + ":" + clip.asset;
      if (sourceKey !== key) {
        audio.src = `/api/workstation/projects/${snapshot.project}/audio/${clip.asset}`;
        sourceKey = key;
        loaded++;
      }
      audio.currentTime = at;
      await audio.play();
      if (serial !== playSerial || !dialog.open) {
        audio.pause();
        return;
      }
      timer = setTimeout(
        stop,
        Math.min(4, clip.offset + clip.duration - at) * 1000,
      );
    }
    function update() {
      try {
        const p = StationFit.plan(clip, content().bpm, opts());
        $("fit-summary").textContent = tr(
          `有效素材 ${(content().bpm / p.time_ratio).toFixed(3)} BPM → 工程 ${content().bpm} BPM · 速度 ×${p.time_ratio.toFixed(5)}；片段将从 ${p.start.toFixed(3)} 秒开始，时长 ${p.duration.toFixed(3)} 秒。`,
          `Effective source ${(content().bpm / p.time_ratio).toFixed(3)} BPM → project ${content().bpm} BPM · speed ×${p.time_ratio.toFixed(5)}; clip starts at ${p.start.toFixed(3)} s, lasts ${p.duration.toFixed(3)} s.`,
        );
        $("fit-error").textContent = "";
        $("fit-submit").disabled = busy;
      } catch (e) {
        $("fit-summary").textContent = "";
        $("fit-error").textContent = e.message;
        $("fit-submit").disabled = true;
      }
      draw();
    }
    function draw() {
      const canvas = $("fit-wave"),
        ctx = canvas.getContext("2d"),
        rect = canvas.getBoundingClientRect(),
        w = Math.max(1, rect.width),
        h = Math.max(1, rect.height),
        dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#191821";
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = "#7ca99d";
      const peaks = asset.waveform || [];
      for (let x = 0; x < w; x++) {
        const i = Math.min(
          peaks.length - 1,
          Math.floor(
            ((clip.offset + (x / w) * clip.duration) / asset.duration) *
              peaks.length,
          ),
        );
        const p = Number(peaks[i] || 0);
        ctx.fillRect(
          x,
          h / 2 - Math.abs(p) * h * 0.42,
          1,
          Math.max(1, Math.abs(p) * h * 0.84),
        );
      }
      const line = (time, color, width = 1) => {
        const x = ((time - clip.offset) / clip.duration) * w;
        if (x < 0 || x > w) return;
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      };
      (report?.beats || []).forEach((b) => line(b, "#d9e7df55"));
      const o = opts(),
        period = 60 / (o.source_bpm * o.tempo_multiplier);
      if (
        Number.isFinite(period) &&
        period > 0 &&
        Number.isFinite(o.source_anchor)
      ) {
        for (
          let i = Math.ceil((clip.offset - o.source_anchor) / period);
          i < (clip.offset + clip.duration - o.source_anchor) / period &&
          i < 2000;
          i++
        )
          line(
            o.source_anchor + i * period,
            i % 4 === 0 ? "#ba96ee88" : "#9b76c633",
          );
        line(o.source_anchor, "#ecd6ff", 3);
      }
    }
    return {
      open,
      stop,
      render() {
        button.textContent = tr("对拍校准", "Beat fit");
        button.disabled = !selectedClip()?.asset;
        if (dialog.open && snapshot?.project !== s.session.id) close();
      },
      diagnostics() {
        return { sourceLoads: loaded };
      },
    };
  },
};
