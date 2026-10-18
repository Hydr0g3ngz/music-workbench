window.StationNoteToolsUI = {
  mount({
    $,
    s,
    tr,
    selectedClip,
    selectedTrack,
    content,
    flush,
    mutate,
    pause,
    guarded,
    onApply,
    toast,
  }) {
    const dialog = document.createElement("dialog");
    dialog.id = "note-cleanup-dialog";
    document.body.append(dialog);
    const preview = new Station.StationEngine();
    let previewTimer,
      previewToken = 0;
    function stop() {
      previewToken++;
      clearTimeout(previewTimer);
      preview.pause();
    }
    preview.onerror = (error) => {
      stop();
      toast(error.message, true);
    };
    let original,
      clipId,
      notes,
      busy = false;
    const fields = () => ({
      low: Number($("cleanup-low").value),
      high: Number($("cleanup-high").value),
      velocity: Number($("cleanup-velocity").value),
      voice: $("cleanup-voice").value,
      tolerance: Number($("cleanup-tolerance").value),
    });
    function update() {
      try {
        for (const el of dialog.querySelectorAll("input"))
          if (!el.checkValidity())
            throw Error(tr("请检查输入范围", "Check the input range"));
        notes = StationNoteTools.simplify(original, fields());
        $("cleanup-count").textContent = tr(
          `${original.length} → ${notes.length} 个音符；这是规则整理，可撤销。`,
          `${original.length} → ${notes.length} notes; editorial rules, undoable.`,
        );
        $("cleanup-apply").disabled = busy || !notes.length;
        $("cleanup-preview").disabled = busy || !notes.length;
      } catch (error) {
        $("cleanup-count").textContent = error.message;
        $("cleanup-apply").disabled = $("cleanup-preview").disabled = true;
      }
    }
    async function open() {
      await flush();
      const clip = selectedClip();
      if (!clip || selectedTrack()?.kind !== "midi") return;
      pause();
      original = structuredClone(clip.notes);
      clipId = clip.id;
      dialog.innerHTML = `<div class="dialog-heading"><h2>${tr("整理音符声部", "Simplify note part")}</h2><button data-close>×</button></div>
      <p>${tr("筛选音区和弱音，或为相近起音保留一个最高/最低音。原录音保留；这不是 AI 自动纠错。先试听，再应用。", "Filter register and quiet notes, or keep the highest/lowest note at nearby onsets. Original recordings stay intact. This is editorial thinning, not AI correction. Audition first.")}</p>
      <div class="production-actions"><button id="cleanup-preset">${tr("高音回声预设", "Upper echoes preset")}</button></div>
      <div class="production-actions"><label>${tr("最低 MIDI 音高", "Lowest MIDI pitch")}<input id="cleanup-low" type="number" min="0" max="127" step="1" value="0"></label><label>${tr("最高 MIDI 音高", "Highest MIDI pitch")}<input id="cleanup-high" type="number" min="0" max="127" step="1" value="127"></label><label>${tr("最小力度", "Minimum velocity")}<input id="cleanup-velocity" type="number" min="1" max="127" step="1" value="1"></label></div>
      <label class="field-row">${tr("声部规则", "Voice rule")}<select id="cleanup-voice"><option value="all">${tr("保留所有符合条件的音", "Keep all matching notes")}</option><option value="highest">${tr("相近起音只保留最高音", "Highest note at nearby onsets")}</option><option value="lowest">${tr("相近起音只保留最低音", "Lowest note at nearby onsets")}</option></select></label>
      <label class="field-row">${tr("起音分组容差 · 拍", "Onset grouping tolerance · beats")}<input id="cleanup-tolerance" type="number" min="0" max="1" step=".03125" value=".125"></label>
      <p id="cleanup-count" role="status"></p><div class="production-actions"><button id="cleanup-preview">${tr("试听整理后的声部", "Audition simplified part")}</button><button id="cleanup-stop">${tr("停止试听", "Stop audition")}</button><button id="cleanup-apply" class="primary">${tr("应用到当前片段", "Apply to current clip")}</button></div>`;
      dialog.oninput = () => {
        stop();
        update();
      };
      dialog.querySelector("[data-close]").onclick = () => dialog.close();
      $("cleanup-preset").onclick = () => {
        stop();
        $("cleanup-low").value = 60;
        $("cleanup-high").value = 108;
        $("cleanup-velocity").value = 45;
        $("cleanup-voice").value = "highest";
        update();
      };
      $("cleanup-stop").onclick = stop;
      $("cleanup-preview").onclick = guarded(async () => {
        stop();
        const token = previewToken;
        pause();
        const copy = structuredClone(content()),
          track = copy.tracks.find((t) => t.clips.some((c) => c.id === clipId)),
          clip = track?.clips.find((c) => c.id === clipId);
        if (!clip)
          throw Error(
            tr("片段已改变，请重新打开", "Clip changed; reopen this tool"),
          );
        clip.notes = structuredClone(notes);
        track.clips = [clip];
        track.solo = true;
        track.mute = false;
        copy.tracks = [track];
        for (const bus of copy.buses || []) bus.solo = false;
        copy.loop = { enabled: false, start: 0, end: 16 };
        copy.metronome.enabled = false;
        preview.setLibrary(s.library);
        await preview.play(copy, s.session.assets, s.session.id, clip.start);
        if (token !== previewToken || !dialog.open) return preview.pause();
        previewTimer = setTimeout(
          stop,
          (Station.duration(copy) - clip.start + 0.1) * 1000,
        );
      });
      $("cleanup-apply").onclick = guarded(async () => {
        busy = true;
        update();
        stop();
        try {
          await flush();
          const clip = selectedClip();
          if (
            clip?.id !== clipId ||
            JSON.stringify(clip.notes) !== JSON.stringify(original)
          )
            throw Error(
              tr(
                "音符已改变，请重新打开整理工具",
                "Notes changed; reopen this tool",
              ),
            );
          onApply?.();
          mutate(() => {
            clip.notes = structuredClone(notes);
            s.noteClip = null;
          });
          await flush();
          dialog.close();
        } finally {
          busy = false;
          if (dialog.open) update();
        }
      });
      update();
      dialog.showModal();
    }
    dialog.addEventListener("close", stop);
    return { open };
  },
};
