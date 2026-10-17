/* Optional arrangement methods. All observations describe clip layout, not audio quality. */
"use strict";
const StationComposition = (() => {
  const roles = {
    free: ["自由", "Free"],
    intro: ["引入", "Intro"],
    theme: ["主题", "Theme"],
    build: ["推进", "Build"],
    peak: ["高潮", "Peak"],
    contrast: ["对比", "Contrast"],
    return: ["再现", "Return"],
    outro: ["收束", "Outro"],
  };
  const developments = {
    establish: ["建立动机", "Establish motif"],
    repeat: ["保留与重复", "Keep & repeat"],
    develop: ["发展变奏", "Develop variation"],
    contrast: ["制造对比", "Create contrast"],
    resolve: ["回归与收束", "Return & resolve"],
    transition: ["连接下一段", "Connect sections"],
  };
  const templates = {
    arc: {
      name: ["32 小节 · 起承转合", "32 bars · Dramatic arc"],
      rows: [
        ["intro", 4, 1],
        ["theme", 8, 3],
        ["build", 4, 4],
        ["peak", 8, 5],
        ["return", 4, 3],
        ["outro", 4, 1],
      ],
    },
    texture: {
      name: ["24 小节 · 氛围发展", "24 bars · Evolving texture"],
      rows: [
        ["intro", 8, 2],
        ["contrast", 8, 3],
        ["outro", 8, 1],
      ],
    },
    song: {
      name: ["48 小节 · 双主题", "48 bars · Two themes"],
      rows: [
        ["intro", 4, 1],
        ["theme", 8, 2],
        ["build", 4, 3],
        ["peak", 8, 4],
        ["contrast", 8, 2],
        ["return", 12, 5],
        ["outro", 4, 1],
      ],
    },
  };
  function template(name, bpm, uid, label = (role) => roles[role][1]) {
    if (!templates[name] || !(bpm >= 30 && bpm <= 300))
      throw Error("Invalid structure template");
    let beat = 0;
    return templates[name].rows.map(([role, bars, energy]) => {
      const start = beat;
      beat += bars * 4;
      if ((beat * 60) / bpm > 600) throw Error("Structure exceeds 10 minutes");
      return {
        id: uid(),
        name: label(role),
        start,
        end: beat,
        role,
        energy,
        intention: "",
      };
    });
  }
  function unionLength(ranges) {
    let end = -Infinity,
      length = 0;
    for (const [a, b] of ranges
      .filter(([a, b]) => b > a)
      .sort((a, b) => a[0] - b[0])) {
      length += Math.max(0, b - Math.max(a, end));
      end = Math.max(end, b);
    }
    return length;
  }
  function observe(project) {
    const solo = project.tracks.some((t) => t.solo && !t.mute);
    const tracks = project.tracks.filter(
      (t) => !t.mute && (!solo || t.solo) && t.gain_db > -60,
    );
    const audible = (t, c) => {
      if (c.gain_db <= -60) return [];
      if (t.kind !== "midi") return [[c.start, c.start + c.duration]];
      return c.notes
        .map((n) => {
          const start = c.start + (n.start * 60) / project.bpm - c.offset;
          return [
            Math.max(c.start, start),
            Math.min(
              c.start + c.duration,
              start + (n.length * 60) / project.bpm,
            ),
          ];
        })
        .filter(([a, b]) => b > a);
    };
    const rows = (project.sections || [])
      .slice()
      .sort((a, b) => a.start - b.start)
      .map((s) => {
        const start = (s.start * 60) / project.bpm,
          end = (s.end * 60) / project.bpm;
        const ranges = tracks.map((t) =>
          t.clips
            .flatMap((c) => audible(t, c))
            .map(([a, b]) => [Math.max(a, start), Math.min(b, end)]),
        );
        return {
          ...s,
          coverage: unionLength(ranges.flat()) / (end - start),
          layers: ranges.reduce(
            (n, r) => n + unionLength(r) / (end - start),
            0,
          ),
          trackIds: tracks
            .filter((t, i) => unionLength(ranges[i]) > 0)
            .map((t) => t.id),
        };
      });
    let previousEnd = 0,
      gaps = 0,
      overlaps = 0;
    for (const s of rows) {
      if (s.start > previousEnd + 1e-6) gaps++;
      if (s.start < previousEnd - 1e-6) overlaps++;
      previousEnd = Math.max(previousEnd, s.end);
    }
    const edges = tracks
      .flatMap((t) => (t.kind === "audio" ? t.clips : []))
      .filter((c) => c.gain_db > -60 && (!c.fade_in || !c.fade_out)).length;
    return { rows, gaps, overlaps, edges };
  }
  function soften(clip, seconds = 0.015) {
    if (!(Number.isFinite(seconds) && seconds >= 0 && seconds <= 30))
      throw Error("Invalid fade");
    const half = clip.duration / 2;
    return {
      fade_in: Math.max(
        clip.fade_in,
        Math.min(seconds, half, clip.duration - clip.fade_out),
      ),
      fade_out: Math.max(
        clip.fade_out,
        Math.min(seconds, half, clip.duration - clip.fade_in),
      ),
    };
  }
  return { roles, developments, templates, template, observe, soften };
})();
if (typeof module !== "undefined") module.exports = StationComposition;
