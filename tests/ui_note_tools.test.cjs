const test = require("node:test"),
  assert = require("node:assert/strict");
const {
  simplify,
} = require("../src/music_studio/ui/static/station-note-tools.js");
const note = (pitch, start = 0, velocity = 80) => ({
  pitch,
  start,
  velocity,
  length: 0.5,
});
test("editorial thinning preserves note coordinates and is deterministic without mutating source", () => {
  const source = [
    note(48),
    note(64, 0.03, 70),
    note(72, 0.07, 55),
    note(76, 0.24, 30),
    note(67, 0.4, 60),
  ];
  const before = structuredClone(source);
  assert.deepEqual(
    simplify(source, {
      low: 60,
      high: 90,
      velocity: 45,
      voice: "highest",
      tolerance: 0.125,
    }),
    [source[2], source[4]],
  );
  assert.deepEqual(source, before);
  assert.deepEqual(simplify(source, { voice: "lowest", tolerance: 0.125 }), [
    source[0],
    source[3],
    source[4],
  ]);
  assert.deepEqual(simplify(source, {}), source);
});
test("onset groups use a fixed anchor, not chained near-onset matches; invalid and empty choices are explicit", () => {
  const source = [note(60, 0), note(64, 0.1), note(67, 0.2)];
  assert.deepEqual(simplify(source, { voice: "highest", tolerance: 0.125 }), [
    source[1],
    source[2],
  ]);
  assert.deepEqual(simplify(source, { low: 100 }), []);
  assert.throws(() => simplify(source, { low: 80, high: 60 }));
  assert.throws(() => simplify(source, { velocity: 0 }));
});
