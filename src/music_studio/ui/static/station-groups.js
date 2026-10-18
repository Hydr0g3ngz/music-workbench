/* Clip groups preserve source windows, note coordinates and automation. */
((root) => {
  "use strict";
  const clips = (c) => c.tracks.flatMap((t) => t.clips);
  function expand(content, ids) {
    const selected = new Set(ids),
      groups = new Set(
        clips(content)
          .filter((c) => selected.has(c.id) && c.group)
          .map((c) => c.group),
      );
    return clips(content)
      .filter((c) => selected.has(c.id) || groups.has(c.group))
      .map((c) => c.id);
  }
  function edit(content, ids, operation, value, uid) {
    const next = structuredClone(content),
      selected = new Set(expand(next, ids));
    const items = clips(next).filter((c) => selected.has(c.id));
    if (!items.length) throw Error("Select clips first / 请先选择片段");
    if (["gain", "fade-in", "fade-out"].includes(operation)) {
      if (
        !Number.isFinite(value) ||
        (operation === "gain"
          ? value < -60 || value > 12
          : value < 0 || value > 30)
      )
        throw Error("Invalid level or fade / 音量或淡变数值无效");
      const key = {
        gain: "gain_db",
        "fade-in": "fade_in",
        "fade-out": "fade_out",
      }[operation];
      for (const c of items) {
        c[key] = value;
        if (c.fade_in + c.fade_out > c.duration)
          throw Error(
            "Fades exceed a selected clip / 淡入与淡出之和超出某个所选片段长度",
          );
      }
      return next;
    }
    if (["move", "copy"].includes(operation)) {
      if (!Number.isFinite(value)) throw Error("Invalid position");
      if (
        items.some(
          (c) =>
            c.start + value < -1e-7 ||
            c.start + c.duration + value > 600 + 1e-7,
        )
      )
        throw Error(
          "Selection exceeds the 10-minute timeline / 选区超出时间线",
        );
    }
    const groups = new Map(),
      newGroup = operation === "group" ? uid() : null;
    for (const t of next.tracks) {
      const added = [];
      for (const c of t.clips) {
        if (!selected.has(c.id)) continue;
        if (operation === "move") c.start = Math.max(0, c.start + value);
        else if (operation === "group") c.group = newGroup;
        else if (operation === "ungroup") c.group = null;
        else if (operation === "copy") {
          const copy = structuredClone(c);
          copy.id = uid();
          copy.start = Math.max(0, c.start + value);
          if (c.group) {
            if (!groups.has(c.group)) groups.set(c.group, uid());
            copy.group = groups.get(c.group);
          }
          added.push(copy);
        } else if (operation !== "delete")
          throw Error("Unknown clip operation");
      }
      t.clips =
        operation === "delete"
          ? t.clips.filter((c) => !selected.has(c.id))
          : [...t.clips, ...added];
      if (t.clips.length > 128) throw Error("Track limit is 128 clips");
    }
    if (clips(next).reduce((n, c) => n + c.notes.length, 0) > 8192)
      throw Error("Session limit is 8192 notes");
    return next;
  }
  const api = { expand, edit };
  if (typeof module !== "undefined") module.exports = api;
  else root.StationGroups = api;
})(typeof window === "undefined" ? globalThis : window);
