(function (root) {
  "use strict";
  function mount({ $, tr, content, selectedClip, duration, apply, toggle }) {
    const settings = () => ({
      loop: { ...root.StationTiming.loopDefaults(), ...content().loop },
      metronome: {
        ...root.StationTiming.metronomeDefaults(),
        ...content().metronome,
      },
    });
    function render() {
      if (!content()) return;
      const { loop, metronome } = settings();
      for (const [id, enabled] of [
        ["loop", loop.enabled],
        ["metronome", metronome.enabled],
      ]) {
        $(id).classList.toggle("active", enabled);
        $(id).setAttribute("aria-pressed", String(enabled));
      }
      $("timing-range").textContent =
        `${+(1 + loop.start / 4).toFixed(3)} → ${+(1 + loop.end / 4).toFixed(3)}`;
      $("timing-settings").classList.toggle("active", loop.enabled);
      $("timing-clip").disabled = !selectedClip();
    }
    function populate(start, end) {
      $("timing-start").value = 1 + start / 4;
      $("timing-end").value = 1 + end / 4;
    }
    $("timing-settings").onclick = () => {
      const { loop, metronome } = settings();
      populate(loop.start, loop.end);
      $("timing-loop").checked = loop.enabled;
      $("timing-click").checked = metronome.enabled;
      $("timing-volume").value = metronome.volume_db;
      $("timing-accent").checked = metronome.accent;
      $("timing-volume").oninput();
      $("timing-error").textContent = "";
      render();
      $("timing-dialog").showModal();
    };
    $("timing-volume").oninput = () => {
      $("timing-db").textContent = `${$("timing-volume").value} dB`;
    };
    $("timing-clip").onclick = () => {
      const clip = selectedClip();
      if (!clip) return;
      const beat = 60 / content().bpm;
      populate(clip.start / beat, (clip.start + clip.duration) / beat);
    };
    $("timing-whole").onclick = () => {
      const beat = 60 / content().bpm;
      populate(
        0,
        Math.min(
          600 / beat,
          Math.max(16, Math.ceil(duration(content()) / (beat * 4)) * 4),
        ),
      );
    };
    $("metronome").onclick = () => toggle("metronome");
    $("loop").onclick = () => toggle("loop");
    $("timing-apply").onclick = async () => {
      const start = (Number($("timing-start").value) - 1) * 4,
        end = (Number($("timing-end").value) - 1) * 4,
        volume = Number($("timing-volume").value);
      if (
        !$("timing-start").value ||
        !$("timing-end").value ||
        ![start, end, volume].every(Number.isFinite) ||
        start < 0 ||
        end - start < 0.25 ||
        (end * 60) / content().bpm > 600 + 1e-9 ||
        volume < -48 ||
        volume > -6
      ) {
        $("timing-error").textContent = tr(
          "请设置有效区间：最短 1/4 拍，结束时间不超过 10 分钟。",
          "Choose a valid range: at least 1/4 beat, ending within 10 minutes.",
        );
        return;
      }
      const button = $("timing-apply");
      button.disabled = true;
      try {
        await apply({
          loop: { enabled: $("timing-loop").checked, start, end },
          metronome: {
            enabled: $("timing-click").checked,
            volume_db: volume,
            accent: $("timing-accent").checked,
          },
        });
        $("timing-dialog").close();
      } catch (error) {
        $("timing-error").textContent = error.message;
      } finally {
        button.disabled = false;
      }
    };
    return { render };
  }
  root.StationTimingUI = { mount };
})(typeof globalThis !== "undefined" ? globalThis : this);
