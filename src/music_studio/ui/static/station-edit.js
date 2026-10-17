/* Musical edits are pure: validate a complete candidate before replacing live state. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.StationEdit = api;
})(typeof globalThis === "object" ? globalThis : this, () => {
  "use strict";
  const clone = (value) => structuredClone(value);
  function notes(source, indices, op, value, end = 3000) {
    const selected = new Set(indices),
      result = clone(source);
    if (!selected.size) return result;
    if (!Number.isFinite(value)) throw Error("Invalid edit value");
    if (op === "delete") return result.filter((_, i) => !selected.has(i));
    const group = result.filter((_, i) => selected.has(i));
    if (op === "move")
      value = Math.max(value, -Math.min(...group.map((n) => n.start)));
    if (op === "transpose") {
      value = Math.round(value);
      if (group.some((n) => n.pitch + value < 0 || n.pitch + value > 127))
        throw Error("MIDI pitch must stay between 0 and 127");
    }
    result.forEach((n, i) => {
      if (!selected.has(i)) return;
      if (op === "move") n.start += value;
      if (op === "transpose") n.pitch += value;
      if (op === "length") n.length = Math.max(0.25, n.length + value);
      if (op === "quantize") {
        if (value <= 0) throw Error("Invalid grid");
        n.start = Math.round(n.start / value) * value;
      }
      if (op === "velocity")
        n.velocity = Math.max(1, Math.min(127, Math.round(value)));
      if (n.start >= end || n.start + n.length > end + 1e-7)
        throw Error(
          "Notes would extend beyond the clip. Extend the clip first.",
        );
    });
    return result;
  }
  function paste(source, copied, at, end) {
    if (!copied.length) return clone(source);
    const first = Math.min(...copied.map((n) => n.start));
    const added = copied.map((n) => ({ ...n, start: at + n.start - first }));
    if (
      source.length + added.length > 512 ||
      added.some((n) => n.start < 0 || n.start + n.length > end + 1e-7)
    )
      throw Error("Paste exceeds the clip length or 512-note limit");
    return [...clone(source), ...added];
  }
  function section(content, from, to, destination, uid) {
    if (
      ![from, to, destination].every(Number.isFinite) ||
      from < 0 ||
      to <= from ||
      destination < 0
    )
      throw Error("Invalid section range");
    const next = clone(content),
      beat = 60 / next.bpm,
      start = from * beat,
      end = to * beat,
      target = destination * beat;
    if (target + end - start > 600 + 1e-7)
      throw Error("Session limit is 10 minutes");
    let count = 0;
    const groups = new Map();
    for (const track of next.tracks) {
      const additions = [];
      for (const c of track.clips) {
        const left = Math.max(start, c.start),
          right = Math.min(end, c.start + c.duration);
        if (right - left <= 1e-7) continue;
        const copy = clone(c);
        copy.id = uid();
        if (copy.group) {
          if (!groups.has(copy.group)) groups.set(copy.group, uid());
          copy.group = groups.get(copy.group);
        }
        copy.start = target + left - start;
        copy.offset += left - c.start;
        copy.duration = right - left;
        if ((c.volume_points || []).length) {
          const E = typeof module !== "undefined" && module.exports
            ? require("./station-envelope.js") : StationEnvelope;
          copy.volume_points = E.crop(c, left - c.start, copy.duration);
        }
        copy.fade_in =
          left > c.start + 1e-7 ? 0 : Math.min(c.fade_in, copy.duration);
        copy.fade_out =
          right < c.start + c.duration - 1e-7
            ? 0
            : Math.min(c.fade_out, copy.duration - copy.fade_in);
        additions.push(copy);
        count++;
      }
      if (track.clips.length + additions.length > 128)
        throw Error("Track limit is 128 clips");
      track.clips.push(...additions);
    }
    if (!count) throw Error("No clips in this section");
    if (
      next.tracks
        .flatMap((t) => t.clips)
        .reduce((n, c) => n + c.notes.length, 0) > 8192
    )
      throw Error("Session limit is 8192 notes");
    const markers = (next.sections || [])
      .filter((m) => m.start >= from && m.start < to)
      .map((m) => ({
        ...m,
        id: uid(),
        start: destination + m.start - from,
        end: Math.min(destination + m.end - from, destination + to - from),
      }));
    next.sections = [...(next.sections || []), ...markers];
    if (next.sections.length > 64) throw Error("Section limit is 64");
    return next;
  }
  const keyNames = [
    "C",
    "C#",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
  ];
  function inKey(pitch, key) {
    if (!key) return true;
    const [root, mode] = key.split(" "),
      tonic = keyNames.indexOf(root);
    return (
      mode === "minor" ? [0, 2, 3, 5, 7, 8, 10] : [0, 2, 4, 5, 7, 9, 11]
    ).includes((pitch - tonic + 120) % 12);
  }
  return { notes, paste, section, inKey, keyNames };
});
