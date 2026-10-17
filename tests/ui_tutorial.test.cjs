const { test } = require("node:test");
const assert = require("node:assert/strict");
const Guide = require("../src/music_studio/ui/static/station-tutorial.js");
const sketch = () => ({
  master_db: -3,
  tracks: [
    {
      id: "keys",
      kind: "midi",
      gain_db: -1,
      pan: 0,
      mute: false,
      solo: false,
      clips: [{ id: "clip", start: 0, notes: [{ pitch: 60, length: 1 }] }],
    },
  ],
});

function harness(storage) {
  const values = new Map();
  storage ||= {
    getItem: (k) => values.get(k),
    setItem: (k, v) => values.set(k, v),
  };
  let panel,
    music = sketch(),
    actions = [],
    highlighted = false;
  const target = {
    classList: { add: () => (highlighted = true) },
    scrollIntoView() {},
    focus() {},
  };
  const doc = {
    body: {
      append(el) {
        panel = el;
      },
    },
    getElementById() {
      return null;
    },
    querySelector: () => target,
    querySelectorAll: () => [],
    createElement: () => ({ classList: { toggle() {} }, setAttribute() {} }),
  };
  const guide = Guide.mount({
    document: doc,
    storage,
    tr: (zh) => zh,
    content: () => music,
    action: async (step) => {
      actions.push(step);
      return "#real-control";
    },
  });
  const click = (kind) =>
    panel.onclick({
      target: { closest: () => ({ dataset: { lesson: kind } }) },
    });
  const saved = (id) => JSON.parse(values.get(Guide.key(id)));
  return {
    guide,
    click,
    saved,
    actions,
    values,
    music,
    panel: () => panel,
    highlighted: () => highlighted,
  };
}

test("lesson evidence distinguishes edits from selecting, renaming, moving or deleting tracks", () => {
  const music = sketch(),
    initial = Guide.snapshot(music);
  music.tracks[0].name = "another name";
  music.tracks[0].clips[0].start = 4;
  assert.equal(Guide.evidence(initial, Guide.snapshot(music)).size, 0);
  assert.equal(
    Guide.evidence(initial, Guide.snapshot({ master_db: -3, tracks: [] })).size,
    0,
  );
  music.tracks[0].solo = true;
  music.tracks[0].gain_db = -4;
  music.tracks[0].clips[0].notes[0].pitch++;
  assert.deepEqual([...Guide.evidence(initial, Guide.snapshot(music))].sort(), [
    "balance",
    "layers",
    "melody",
  ]);
});

test("opening controls does not complete a lesson; real operations unlock progression", async () => {
  const h = harness();
  h.guide.attach("one", true);
  await h.click("locate");
  await h.click("next");
  assert.deepEqual(h.actions, ["listen"]);
  assert.equal(h.highlighted(), true);
  assert.equal(h.saved("one").step, 0);
  h.guide.observe("listen", "one");
  await h.click("next");
  assert.equal(h.saved("one").step, 1);
  h.guide.observe();
  assert.equal(h.saved("one").outcomes.layers, null);
  h.music.tracks[0].mute = true;
  h.guide.observe();
  assert.equal(h.saved("one").outcomes.layers, "done");
  await h.click("next");
  h.music.tracks[0].clips[0].notes[0].pitch++;
  h.guide.observe();
  assert.equal(h.saved("one").outcomes.melody, "done");
  await h.click("next");
  h.music.tracks[0].pan = 0.25;
  h.guide.observe();
  await h.click("next");
  // A failed render sends no success event; opening the export dialog is insufficient.
  await h.click("locate");
  await h.click("next");
  assert.equal(h.saved("one").step, 4);
  h.guide.observe("export", "one");
  await h.click("next");
  assert.equal(h.saved("one").step, 5);
  assert.ok(Object.values(h.saved("one").outcomes).every((x) => x === "done"));
});

test("reload, translation redraw and project switches preserve only the right lesson", async () => {
  const h = harness();
  h.guide.attach("a", true);
  h.guide.observe("listen");
  await h.click("next");
  const h2 = harness({
    getItem: (k) => h.values.get(k),
    setItem: (k, v) => h.values.set(k, v),
  });
  h2.guide.attach("a");
  h2.guide.render();
  assert.equal(h2.panel().hidden, false);
  assert.equal(h.saved("a").step, 1);
  h2.guide.attach("b", true);
  h2.guide.observe("listen", "a");
  assert.equal(
    h.saved("b").outcomes.listen,
    null,
    "late completion from project a must not credit b",
  );
  h2.guide.attach("a");
  assert.equal(h.saved("a").step, 1);
});

test("skip and repeat never change the arrangement or claim skipped actions were performed", async () => {
  const h = harness(),
    original = JSON.stringify(h.music);
  h.guide.attach("one", true);
  for (let i = 0; i < 5; i++) await h.click("skip");
  assert.equal(h.saved("one").step, 5);
  assert.ok(
    Object.values(h.saved("one").outcomes).every((x) => x === "skipped"),
  );
  await h.click("restart");
  assert.equal(h.saved("one").step, 0);
  assert.ok(Object.values(h.saved("one").outcomes).every((x) => x === null));
  assert.equal(JSON.stringify(h.music), original);
});

test("closing suppresses progress and reopening keeps prior work; denied storage stays usable", async () => {
  const h = harness();
  h.guide.attach("one", true);
  await h.click("close");
  h.guide.observe("listen");
  assert.equal(h.saved("one").outcomes.listen, null);
  h.guide.show();
  h.guide.observe("listen");
  assert.equal(h.saved("one").outcomes.listen, "done");
  const denied = harness({
    getItem() {
      throw Error("denied");
    },
    setItem() {
      throw Error("denied");
    },
  });
  denied.guide.attach("x", true);
  denied.guide.observe("listen");
  await denied.click("next");
  assert.equal(denied.panel().hidden, false);
});

test("corrupt or future stored state cannot break lesson navigation", () => {
  for (const raw of [
    "not json",
    "null",
    "[]",
    '{"step":999,"outcomes":{"listen":"claimed"}}',
  ]) {
    const state = Guide.load({ getItem: () => raw }, "one");
    assert.ok(state.step >= 0 && state.step <= 5);
    assert.equal(state.outcomes.listen, null);
  }
});
