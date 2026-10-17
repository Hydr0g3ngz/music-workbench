"use strict";
window.StationEnvelopeUI = {
  mount({ $, tr, esc, content, selectedClip, mutate, flush, guarded, toast }) {
    const button = document.createElement("button");
    button.id = "volume-open";
    $("material-tools").before(button);
    const dialog = document.createElement("dialog");
    dialog.id = "volume-dialog";
    dialog.className = "volume-dialog";
    document.body.append(dialog);
    let draft, source;
    function plot() {
      const points = draft.volume_points || [];
      const x = (t) => 22 + (t / draft.duration) * 716;
      const y = (db) => 22 + ((12 - db) / 72) * 156;
      const times = [
        ...new Set([
          0,
          draft.duration,
          ...points.map((p) => p.time),
          ...Array.from({ length: 100 }, (_, i) => (i * draft.duration) / 99),
        ]),
      ].sort((a, b) => a - b);
      const bare = { ...draft, fade_in: 0, fade_out: 0, gain_db: 0 };
      const line = times
        .map(
          (t) =>
            `${x(t)},${y(20 * Math.log10(Math.max(0.001, StationEnvelope.value(bare, t))))}`,
        )
        .join(" ");
      $("volume-plot").innerHTML =
        `<line x1="22" x2="738" y1="${y(0)}" y2="${y(0)}" stroke="#596575" stroke-dasharray="4"/><polyline fill="none" stroke="#87d8bc" stroke-width="3" points="${(points.length
          ? points
          : [
              { time: 0, db: 0 },
              { time: draft.duration, db: 0 },
            ]
        )
          .map((p) => `${x(p.time)},${y(p.db)}`)
          .join(
            " ",
          )}"/>${points.map((p, i) => `<circle data-point="${i}" cx="${x(p.time)}" cy="${y(p.db)}" r="6" fill="#e7f7f0"/>`).join("")}`;
      $("volume-plot").insertAdjacentHTML(
        "beforeend",
        `<g fill="#9dafb7" font-size="11"><text x="24" y="14">+12 dB</text><text x="24" y="${y(0) - 5}">0 dB</text><text x="24" y="174">−60 dB</text><text x="24" y="194">0 s</text><text x="735" y="194" text-anchor="end">${draft.duration.toFixed(2)} s</text></g>`,
      );
      $("volume-plot").querySelector("polyline").setAttribute("points", line);
      $("volume-points").innerHTML = points
        .map(
          (p, i) =>
            `<div class="volume-row"><label>${tr("秒", "Seconds")}<input data-time="${i}" type="number" min="0" max="${draft.duration}" step="any" value="${Math.min(draft.duration, Number(p.time.toFixed(3)))}"></label><label>dB<input data-db="${i}" type="number" min="-60" max="12" step="any" value="${p.db.toFixed(1)}"></label><button data-delete-point="${i}">${tr("移除", "Remove")}</button></div>`,
        )
        .join("");
    }
    function open() {
      const clip = selectedClip();
      if (!clip) return toast(tr("先选一个片段", "Select a clip first"));
      source = structuredClone(clip);
      draft = structuredClone(clip);
      draft.volume_points ||= [];
      dialog.innerHTML = `<div class="dialog-heading"><h2>${tr("音量与过渡", "Volume & transitions")} · ${esc(clip.name)}</h2><button id="volume-close">×</button></div><div class="volume-body"><h3>${tr("片段音量曲线", "Clip volume curve")}</h3><p>${tr("双击图表添加点，拖动圆点调整；曲线随片段移动。所有变化在应用后生效，可一次撤销。", "Double-click to add a point; drag to adjust. The curve follows the clip. Apply to hear changes; undo in one step.")}</p><svg id="volume-plot" viewBox="0 0 760 200" role="img" aria-label="${tr("音量包络", "Volume envelope")}"></svg><div class="volume-presets"><button data-volume-preset="rise">${tr("渐强", "Build up")}</button><button data-volume-preset="dip">${tr("留出空间", "Make space")}</button><button data-volume-preset="clear">${tr("清除曲线", "Clear curve")}</button></div><div id="volume-points"></div><button id="volume-apply" class="primary">${tr("应用音量曲线", "Apply volume curve")}</button><hr><h3>${tr("与下一片段交叉淡化", "Crossfade into another clip")}</h3><p>${tr("将下一片段的起点移到重叠处，只移动该片段。等功率淡化适合不相关素材，相关音频可能叠加变响；请试听后调整。", "Moves only the next clip to create an overlap. Equal-power fades suit unrelated material; correlated audio can become louder. Audition and adjust.")}</p><label>${tr("下一片段", "Next clip")}<select id="transition-next">${content()
        .tracks.flatMap((t) =>
          t.clips
            .filter((c) => c.id !== clip.id)
            .map(
              (c) =>
                `<option value="${c.id}">${esc(t.name)} · ${esc(c.name)}</option>`,
            ),
        )
        .join(
          "",
        )}</select></label><div class="volume-row"><label>${tr("重叠拍数", "Overlap beats")}<input id="transition-beats" type="number" min=".125" max="16" step=".25" value="1"></label><label>${tr("淡化曲线", "Fade curve")}<select id="transition-curve"><option value="equal_power">${tr("等功率", "Equal power")}</option><option value="linear">${tr("线性", "Linear")}</option></select></label></div><p id="transition-preview"></p><button id="transition-apply">${tr("应用交叉淡化", "Apply crossfade")}</button></div>`;
      $("volume-close").onclick = () => dialog.close();
      const ai = document.createElement("button");
      ai.id = "transition-ai";
      ai.textContent = tr(
        "用 AI 重绘片段尾部过渡",
        "Repaint the ending transition with AI",
      );
      ai.disabled = !clip.asset || clip.duration < 10 || clip.duration > 60;
      ai.title = tr(
        "需要 10–60 秒音频片段与本地 ACE-Step；先生成候选，再试听采用",
        "Needs a 10–60 s audio clip and local ACE-Step; generate a candidate, then audition and adopt",
      );
      $("transition-apply").after(ai);
      ai.onclick = guarded(() => {
        dialog.close();
        $("open-generation").click();
        $("generation-mode").value = "repaint";
        $("repaint-start").value = Math.max(0, clip.duration - 4);
        $("repaint-end").value = clip.duration;
        $("generation-development").value = "transition";
        $("generation-use-blueprint").checked = true;
        $("generation-prompt").value =
          "A short connective musical gesture at the end, preserving the surrounding style and harmonic direction, instrumental";
        $("generation-mode").dispatchEvent(new Event("change"));
      });
      const sort = () => draft.volume_points.sort((a, b) => a.time - b.time);
      const coords = (e) => {
        const r = $("volume-plot").getBoundingClientRect();
        return {
          time: Math.max(
            0,
            Math.min(
              draft.duration,
              ((((e.clientX - r.left) / r.width) * 760 - 22) / 716) *
                draft.duration,
            ),
          ),
          db: Math.max(
            -60,
            Math.min(
              12,
              12 - ((((e.clientY - r.top) / r.height) * 200 - 22) / 156) * 72,
            ),
          ),
        };
      };
      $("volume-plot").ondblclick = (e) => {
        if ((draft.volume_points || []).length >= 64) return;
        const p = coords(e);
        if (draft.volume_points.some((q) => Math.abs(q.time - p.time) < 0.01))
          return;
        draft.volume_points.push(p);
        sort();
        plot();
      };
      $("volume-plot").onpointerdown = (e) => {
        if (!e.target.hasAttribute("data-point")) return;
        const p = draft.volume_points[Number(e.target.dataset.point)];
        const move = (ev) => {
          const next = coords(ev);
          if (
            !draft.volume_points.some(
              (q) => q !== p && Math.abs(q.time - next.time) < 0.005,
            )
          ) {
            Object.assign(p, next);
            sort();
            plot();
          }
        };
        const up = () => {
          window.removeEventListener("pointermove", move);
          window.removeEventListener("pointerup", up);
        };
        window.addEventListener("pointermove", move);
        window.addEventListener("pointerup", up);
      };
      $("volume-points").onchange = (e) => {
        const i = Number(e.target.dataset.time ?? e.target.dataset.db);
        if (!e.target.checkValidity()) return;
        const key = e.target.hasAttribute("data-time") ? "time" : "db";
        const value = Number(e.target.value);
        if (
          key === "time" &&
          draft.volume_points.some((p, j) => j !== i && p.time === value)
        )
          return plot();
        draft.volume_points[i][key] = value;
        sort();
        plot();
      };
      $("volume-points").onclick = (e) => {
        if (e.target.hasAttribute("data-delete-point")) {
          draft.volume_points.splice(Number(e.target.dataset.deletePoint), 1);
          plot();
        }
      };
      dialog.querySelectorAll("[data-volume-preset]").forEach(
        (b) =>
          (b.onclick = () => {
            draft.volume_points =
              b.dataset.volumePreset === "rise"
                ? [
                    { time: 0, db: -18 },
                    { time: draft.duration, db: 0 },
                  ]
                : b.dataset.volumePreset === "dip"
                  ? [
                      { time: 0, db: 0 },
                      { time: draft.duration * 0.35, db: -12 },
                      { time: draft.duration * 0.7, db: -12 },
                      { time: draft.duration, db: 0 },
                    ]
                  : [];
            plot();
          }),
      );
      const check = () => {
        const c = content()
          .tracks.flatMap((t) => t.clips)
          .find((c) => c.id === source.id);
        if (JSON.stringify(c) !== JSON.stringify(source))
          throw Error(
            tr("片段已改变，请重新打开", "Clip changed; reopen this dialog"),
          );
        return c;
      };
      $("volume-apply").onclick = guarded(async () => {
        const c = check();
        mutate(() => (c.volume_points = structuredClone(draft.volume_points)));
        await flush();
        dialog.close();
      });
      const preview = () => {
        const next = StationEnvelope.crossfade(
          content(),
          source.id,
          $("transition-next").value,
          (Number($("transition-beats").value) * 60) / content().bpm,
          $("transition-curve").value,
        );
        const b = next.tracks
          .flatMap((t) => t.clips)
          .find((c) => c.id === $("transition-next").value);
        $("transition-preview").textContent = tr(
          `下一片段将从 ${b.start.toFixed(3)} 秒开始。`,
          `Next clip will start at ${b.start.toFixed(3)} s.`,
        );
        return next;
      };
      for (const id of [
        "transition-next",
        "transition-beats",
        "transition-curve",
      ])
        $(id).onchange = () => {
          try {
            preview();
            $("transition-apply").disabled = false;
          } catch (e) {
            $("transition-preview").textContent = e.message;
            $("transition-apply").disabled = true;
          }
        };
      $("transition-apply").onclick = guarded(async () => {
        check();
        const next = preview();
        mutate(() => (content().tracks = next.tracks));
        await flush();
        dialog.close();
      });
      $("transition-next").onchange();
      plot();
      dialog.showModal();
    }
    button.onclick = guarded(open);
    return {
      render() {
        button.textContent = tr("音量与过渡", "Volume & transitions");
        button.disabled = !selectedClip();
      },
    };
  },
};
