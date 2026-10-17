const test = require("node:test"),
  assert = require("node:assert/strict");
const Edit = require("../src/music_studio/ui/static/station-edit.js");
const n = (start, pitch = 60, length = 0.5) => ({
  start,
  pitch,
  length,
  velocity: 90,
});
test("group edits preserve intervals, source notes, bounds and integer velocity", () => {
  const source = [n(0), n(1, 64), n(3, 67)];
  const moved = Edit.notes(source, [0, 1], "move", -0.5, 8);
  assert.deepEqual(moved, source);
  const transposed = Edit.notes(moved, [0, 1], "transpose", 12, 8);
  assert.deepEqual(
    transposed.map((n) => n.pitch),
    [72, 76, 67],
  );
  assert.equal(source[0].pitch, 60);
  assert.throws(() => Edit.notes(source, [0], "transpose", 80, 8));
  assert.throws(() => Edit.notes(source, [2], "length", 5, 8));
  assert.equal(Edit.notes(source, [0], "velocity", 200, 8)[0].velocity, 127);
  assert.equal(Edit.notes([n(0.38)], [0], "quantize", 0.25, 8)[0].start, 0.5);
});
test("copy paste retains relative rhythm and rejects overflow without mutation", () => {
  const source = [n(0.5), n(1.75, 64)];
  const result = Edit.paste(source, source, 4, 8);
  assert.deepEqual(
    result.slice(2).map((n) => n.start),
    [4, 5.25],
  );
  assert.equal(source.length, 2);
  assert.throws(() => Edit.paste(source, source, 7.5, 8));
  assert.throws(() =>
    Edit.paste(
      Array.from({ length: 512 }, () => n(0)),
      source,
      4,
      8,
    ),
  );
});
test("section duplication crops across tracks retaining offsets, fades and note time", () => {
  const c = {
    id: "clip",
    start: 1,
    offset: 0.5,
    duration: 5,
    fade_in: 0.3,
    fade_out: 0.4,
    notes: [n(2)],
  };
  const project = {
    bpm: 120,
    tracks: [
      { clips: [c] },
      { clips: [{ ...c, id: "other", start: 2, duration: 1 }] },
    ],
    sections: [{ id: "s", name: "A", start: 4, end: 12 }],
  };
  let id = 0;
  const result = Edit.section(project, 4, 8, 16, () => String(++id));
  const copied = result.tracks[0].clips[1];
  assert.equal(copied.start, 8);
  assert.equal(copied.offset, 1.5);
  assert.equal(copied.duration, 2);
  assert.equal(copied.fade_in, 0);
  assert.equal(copied.fade_out, 0);
  assert.deepEqual(copied.notes, c.notes);
  assert.equal(project.tracks[0].clips.length, 1);
  assert.equal(result.tracks[1].clips[1].start, 8);
  assert.deepEqual(result.sections[1], {
    id: "3",
    name: "A",
    start: 16,
    end: 20,
  });
  assert.throws(() => Edit.section(project, 4, 8, 1199, () => "x"));
});
test("scale hints distinguish parallel major and minor", () => {
  assert.ok(Edit.inKey(65, "D minor"));
  assert.ok(!Edit.inKey(66, "D minor"));
  assert.ok(Edit.inKey(66, "D major"));
  assert.ok(Edit.inKey(61, ""));
});
