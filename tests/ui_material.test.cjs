const test = require("node:test"),
  assert = require("node:assert/strict");
const Fit = require("../src/music_studio/ui/static/station-fit.js");
test("beat fitting preserves pickup and anchors the source at the target grid without pitch edits", () => {
  const clip = { offset: 0.2, duration: 12 };
  const options = {
    source_bpm: 100,
    tempo_multiplier: 1,
    source_anchor: 0.7,
    target_beat: 16,
  };
  const p = Fit.plan(clip, 120, options);
  assert.equal(p.time_ratio, 1.2);
  assert.equal(p.start + (0.7 - 0.2) / p.time_ratio, 8);
  assert.equal(p.duration, 10);
  assert.equal(
    Fit.plan(clip, 120, { ...options, source_bpm: 200, tempo_multiplier: 0.5 })
      .time_ratio,
    1.2,
  );
  for (const change of [
    { target_beat: 0 },
    { source_anchor: 12.2 },
    { source_bpm: 30 },
    { tempo_multiplier: 3 },
    { source_bpm: NaN },
    { target_beat: 1200 },
  ])
    assert.throws(() => Fit.plan(clip, 120, { ...options, ...change }));
  assert.deepEqual(clip, { offset: 0.2, duration: 12 });
});
test("two beat calibration uses interval count rather than inclusive beat numbering", () => {
  assert.ok(Math.abs(Fit.tappedBpm(0.37, 9.97, 16) - 100) < 1e-10);
  for (const args of [
    [1, 1, 16],
    [2, 1, 16],
    [0, 4, 0],
    [0, 1, 8],
    [0, 4, 1.5],
  ])
    assert.throws(() => Fit.tappedBpm(...args));
});
