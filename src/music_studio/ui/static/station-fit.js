"use strict";
const StationFit = (() => {
  function plan(clip, bpm, options) {
    const sourceBpm = Number(options.source_bpm),
      multiplier = Number(options.tempo_multiplier),
      anchor = Number(options.source_anchor),
      target = Number(options.target_beat);
    if (
      ![sourceBpm, multiplier, anchor, target, bpm].every(Number.isFinite) ||
      sourceBpm < 30 ||
      sourceBpm > 300 ||
      ![0.5, 1, 2].includes(multiplier) ||
      target < 0
    )
      throw Error("Invalid beat-fit parameters");
    const ratio = bpm / (sourceBpm * multiplier);
    if (ratio < 0.5 || ratio > 2)
      throw Error(
        "Tempo ratio must be between 0.5 and 2; check half/double-time",
      );
    if (anchor < clip.offset || anchor >= clip.offset + clip.duration)
      throw Error("Choose an anchor inside the selected clip");
    const start = (target * 60) / bpm - (anchor - clip.offset) / ratio,
      duration = clip.duration / ratio;
    if (
      [clip.fade_in || 0, clip.fade_out || 0].some((fade) => fade / ratio > 30)
    )
      throw Error(
        "Slowed fades would exceed 30 seconds; shorten the fades first",
      );
    if (start < -1e-9 || start + duration > 600 + 1e-9)
      throw Error(
        "Aligned clip exceeds the timeline; move the target or trim the pickup",
      );
    return {
      time_ratio: ratio,
      start: Math.max(0, start),
      offset: clip.offset / ratio,
      duration,
    };
  }
  function tappedBpm(first, last, intervals) {
    if (
      ![first, last, intervals].every(Number.isFinite) ||
      last <= first ||
      !Number.isInteger(intervals) ||
      intervals < 1 ||
      intervals > 256
    )
      throw Error(
        "Choose two beats and the number of beat intervals between them",
      );
    const bpm = (60 * intervals) / (last - first);
    if (bpm < 30 || bpm > 300)
      throw Error("Calibrated BPM must be between 30 and 300");
    return bpm;
  }
  return { plan, tappedBpm };
})();
if (typeof module !== "undefined") module.exports = StationFit;
