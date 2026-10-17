(function (root) {
  "use strict";
  const amplitude = (db) => 10 ** (db / 20);
  function value(clip, time) {
    let fadeIn = clip.fade_in
      ? Math.max(0, Math.min(1, time / clip.fade_in))
      : 1;
    let fadeOut = clip.fade_out
      ? Math.max(0, Math.min(1, (clip.duration - time) / clip.fade_out))
      : 1;
    if (clip.fade_curve === "equal_power") {
      fadeIn = Math.sin((fadeIn * Math.PI) / 2);
      fadeOut = Math.sin((fadeOut * Math.PI) / 2);
    }
    const points = clip.volume_points || [];
    let level = 1;
    if (points.length) {
      if (time <= points[0].time) level = amplitude(points[0].db);
      else if (time >= points.at(-1).time) level = amplitude(points.at(-1).db);
      else {
        const i = points.findIndex((p) => p.time >= time),
          a = points[i - 1],
          b = points[i];
        const fraction = (time - a.time) / (b.time - a.time);
        level =
          amplitude(a.db) + (amplitude(b.db) - amplitude(a.db)) * fraction;
      }
    }
    return fadeIn * fadeOut * level * amplitude(clip.gain_db || 0);
  }
  function crop(clip, from, duration) {
    if (!(clip.volume_points || []).length) return [];
    // Crop automation without baking fades or fixed clip gain into the points.
    const bare = { ...clip, fade_in: 0, fade_out: 0, gain_db: 0 };
    const point = (t) => ({
      time: t - from,
      db: 20 * Math.log10(Math.max(1e-3, value(bare, t))),
    });
    const result = [
      point(from),
      ...clip.volume_points
        .filter((p) => p.time > from && p.time < from + duration)
        .map((p) => ({ ...p, time: p.time - from })),
      point(from + duration),
    ];
    // Repeated crops at the same endpoints do not grow the point count.
    if (result.length > 128) throw Error("Volume curve exceeds 128 points");
    return result;
  }
  function crossfade(content, aId, bId, seconds, curve = "equal_power") {
    if (
      aId === bId ||
      !Number.isFinite(seconds) ||
      seconds <= 0 ||
      seconds > 30 ||
      !["linear", "equal_power"].includes(curve)
    )
      throw Error("Choose two different clips and a valid overlap");
    const next = structuredClone(content),
      clips = next.tracks.flatMap((t) => t.clips),
      a = clips.find((c) => c.id === aId),
      b = clips.find((c) => c.id === bId);
    if (
      !a ||
      !b ||
      seconds > a.duration - a.fade_in ||
      seconds > b.duration - b.fade_out
    )
      throw Error("Overlap does not fit the clips and their existing fades");
    b.start = a.start + a.duration - seconds;
    if (b.start < 0 || b.start + b.duration > 600)
      throw Error("Transition exceeds the timeline");
    a.fade_out = seconds;
    b.fade_in = seconds;
    a.fade_curve = curve;
    b.fade_curve = curve;
    return next;
  }
  const api = { value, crop, crossfade };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.StationEnvelope = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
