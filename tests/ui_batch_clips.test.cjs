const test = require("node:test"),
  assert = require("node:assert/strict");
const Groups = require("../src/music_studio/ui/static/station-groups.js");
test("batch gain and fades preserve source crops, groups, notes and reject the whole edit on short clips", () => {
  const content = {
    tracks: [
      {
        clips: [
          {
            id: "one",
            group: "g",
            start: 0,
            offset: 3,
            duration: 2,
            fade_in: 0.2,
            fade_out: 0.1,
            gain_db: 0,
            notes: [{ pitch: 60, start: 6 }],
          },
          {
            id: "two",
            group: "g",
            start: 3,
            offset: 0,
            duration: 4,
            fade_in: 0,
            fade_out: 0,
            gain_db: 0,
            notes: [],
          },
        ],
      },
    ],
  };
  const snapshot = structuredClone(content);
  const next = Groups.edit(content, ["one"], "gain", -4, () => "id");
  assert.deepEqual(
    next.tracks[0].clips.map((c) => c.gain_db),
    [-4, -4],
  );
  assert.equal(next.tracks[0].clips[0].offset, 3);
  assert.deepEqual(
    next.tracks[0].clips[0].notes,
    snapshot.tracks[0].clips[0].notes,
  );
  const faded = Groups.edit(next, ["one"], "fade-out", 1, () => "id");
  assert.deepEqual(
    faded.tracks[0].clips.map((c) => c.fade_out),
    [1, 1],
  );
  assert.throws(() => Groups.edit(content, ["one"], "fade-out", 3, () => "id"));
  assert.deepEqual(content, snapshot);
  assert.throws(() =>
    Groups.edit(content, ["one"], "gain", Infinity, () => "id"),
  );
});
