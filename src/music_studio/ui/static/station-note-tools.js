/* Deterministic editorial thinning, never a transcription accuracy claim. */
((root) => {
  "use strict";
  function simplify(notes, options) {
    const {
      low = 0,
      high = 127,
      velocity = 1,
      voice = "all",
      tolerance = 0.125,
    } = options;
    if (
      !Number.isInteger(low) ||
      !Number.isInteger(high) ||
      low < 0 ||
      high > 127 ||
      low > high ||
      !Number.isInteger(velocity) ||
      velocity < 1 ||
      velocity > 127 ||
      !["all", "highest", "lowest"].includes(voice) ||
      !Number.isFinite(tolerance) ||
      tolerance < 0 ||
      tolerance > 1
    )
      throw Error("Check note range and thresholds / 请检查音符范围与阈值");
    const candidates = notes
      .map((n, index) => ({ ...n, index }))
      .filter(
        (n) => n.pitch >= low && n.pitch <= high && n.velocity >= velocity,
      )
      .sort((a, b) => a.start - b.start || a.index - b.index);
    let kept = candidates;
    if (voice !== "all") {
      kept = [];
      let cluster = [],
        anchor;
      const emit = () => {
        if (!cluster.length) return;
        cluster.sort(
          (a, b) =>
            (voice === "highest" ? b.pitch - a.pitch : a.pitch - b.pitch) ||
            b.velocity - a.velocity ||
            a.index - b.index,
        );
        kept.push(cluster[0]);
      };
      for (const n of candidates) {
        if (!cluster.length || n.start - anchor > tolerance + 1e-9) {
          emit();
          cluster = [];
          anchor = n.start;
        }
        cluster.push(n);
      }
      emit();
    }
    return kept.sort((a, b) => a.index - b.index).map(({ index, ...n }) => n);
  }
  const api = { simplify };
  if (typeof module !== "undefined") module.exports = api;
  else root.StationNoteTools = api;
})(typeof window === "undefined" ? globalThis : window);
