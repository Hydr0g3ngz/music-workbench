((root) => {
  "use strict";
  const E =
    typeof module !== "undefined" && module.exports
      ? require("./effects-dsp.js")
      : root.StationEffects;
  const audible = (t, tracks) =>
    !t.mute && (!tracks.some((t) => t.solo) || t.solo);
  const busAudible = (b, buses) =>
    !b.mute && (!buses.some((b) => b.solo) || b.solo);
  function tail(track, buses = []) {
    const targets = new Set([
      track.output,
      ...(track.sends || []).filter((s) => s.enabled).map((s) => s.bus),
    ]);
    return (
      E.tail(track.effects) +
      Math.max(
        0,
        ...buses
          .filter((b) => targets.has(b.id) && busAudible(b, buses))
          .map((b) => E.tail(b.effects)),
      )
    );
  }
  const api = { audible, busAudible, tail };
  if (typeof module !== "undefined") module.exports = api;
  else root.StationRouting = api;
})(typeof window === "undefined" ? globalThis : window);
