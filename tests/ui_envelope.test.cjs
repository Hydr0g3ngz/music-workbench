const test = require("node:test"),
  assert = require("node:assert/strict");
const E = require("../src/music_studio/ui/static/station-envelope.js");
const clip = {
  id: "a",
  start: 0,
  duration: 8,
  fade_in: 0,
  fade_out: 0,
  gain_db: 0,
  volume_points: [
    { time: 0, db: -20 },
    { time: 8, db: 0 },
  ],
};
test("automation interpolates amplitude and crop preserves the original envelope", () => {
  assert.equal(E.value(clip, 4), 0.55);
  const part = { ...clip, duration: 4, volume_points: E.crop(clip, 2, 4) };
  for (let t = 0; t <= 4; t += 0.125)
    assert.ok(Math.abs(E.value(part, t) - E.value(clip, t + 2)) < 1e-10);
  const extended = {
    ...clip,
    duration: 12,
    volume_points: E.crop(clip, 0, 12),
  };
  assert.equal(E.value(extended, 11), 1);
});
test("equal-power crossfade moves only B and keeps undo input immutable", () => {
  const b = { ...clip, id: "b", start: 10, volume_points: [] };
  const content = {
    tracks: [
      {
        clips: [
          { ...clip, volume_points: [] },
          b,
          { ...b, id: "c", start: 20 },
        ],
      },
    ],
  };
  const result = E.crossfade(content, "a", "b", 2);
  assert.equal(b.start, 10);
  assert.equal(result.tracks[0].clips[1].start, 6);
  assert.equal(result.tracks[0].clips[2].start, 20);
  const [a, next] = result.tracks[0].clips;
  for (let t = 0; t <= 2; t += 0.1)
    assert.ok(
      Math.abs(E.value(a, 6 + t) ** 2 + E.value(next, t) ** 2 - 1) < 1e-10,
    );
  assert.throws(() => E.crossfade(content, "a", "b", 9));
});
