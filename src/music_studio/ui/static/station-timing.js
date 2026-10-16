(function (root) {
  "use strict";
  const loopDefaults = () => ({ enabled: false, start: 0, end: 16 });
  const metronomeDefaults = () => ({
    enabled: false,
    volume_db: -18,
    accent: true,
  });
  function range(content, end, at = 0) {
    const loop = { ...loopDefaults(), ...content.loop },
      beat = 60 / (content.bpm || 108);
    if (loop.enabled) {
      const start = loop.start * beat,
        finish = loop.end * beat;
      return {
        loop: true,
        start,
        end: finish,
        at: at >= start && at < finish ? at : start,
      };
    }
    const finish = Math.max(end, content.metronome?.enabled ? beat * 16 : 0);
    return {
      loop: false,
      start: 0,
      end: finish,
      at: at >= finish ? 0 : Math.max(0, at),
    };
  }
  // Windows are half-open; a beat at a loop end belongs only to the following cycle.
  function beatEvents(timing, from, to) {
    const { started, at, end, loop, start, bpm } = timing,
      beat = 60 / bpm,
      firstEnd = started + end - at,
      events = [];
    function window(position, finish, when) {
      const low = Math.max(position, position + from - when),
        high = Math.min(finish, position + to - when);
      for (let i = Math.ceil(low / beat - 1e-8); i * beat < high - 1e-9; i++) {
        const time = when + i * beat - position;
        if (time >= from - 1e-9) events.push({ beat: i, time });
      }
    }
    if (from < firstEnd) window(at, end, started);
    if (loop) {
      const length = end - start;
      let cycle = Math.max(0, Math.floor((from - firstEnd) / length));
      for (
        let when = firstEnd + cycle * length;
        when < to;
        when = firstEnd + ++cycle * length
      )
        window(start, end, when);
    }
    return events;
  }
  const api = { loopDefaults, metronomeDefaults, range, beatEvents };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.StationTiming = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
