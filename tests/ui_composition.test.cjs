const test = require("node:test");
const assert = require("node:assert/strict");
const C = require("../src/music_studio/ui/static/station-composition.js");

test("notifications are visible in the current modal and return to the page afterward", () => {
  const fs = require("node:fs"),
    vm = require("node:vm");
  const source = fs.readFileSync(
    require.resolve("../src/music_studio/ui/static/station.js"),
    "utf8",
  );
  const makeItem = () => ({
    hidden: true,
    classList: { toggle() {} },
    parentElement: null,
    setAttribute(key, value) {
      this[key] = value;
    },
  });
  let item = makeItem();
  const original = item,
    timers = [];
  const host = () => ({
    append(node) {
      node.parentElement = this;
    },
  });
  const modal = host(),
    body = host();
  let open = modal;
  const context = vm.createContext({
    document: {
      querySelector: () => open,
      body,
      createElement: () => (item = makeItem()),
    },
    $: () => item,
    toastTimer: null,
    clearTimeout() {},
    setTimeout(callback) {
      timers.push(callback);
    },
  });
  const start = source.indexOf("function toast(");
  vm.runInContext(
    source.slice(start, source.indexOf("async function request(", start)),
    context,
  );
  context.toast("Cannot generate an 8 second draft", true);
  assert.equal(item.parentElement, modal);
  assert.equal(item.hidden, false);
  open = null;
  context.toast("Saved");
  assert.equal(item.parentElement, body);
  item = null; // A dialog rebuild removed the previous notice from the DOM.
  open = modal;
  context.toast("Invalid fade", true);
  assert.notEqual(item, original);
  assert.equal(item.parentElement, modal);
  assert.equal(item.role, "status");
  assert.equal(item.hidden, false);
  timers[0](); // An old timer closes only its own detached notice.
  assert.equal(item.hidden, false);
});

test("structure sketches have continuous bounded timing, unique IDs and optional energy", () => {
  let id = 0;
  const rows = C.template("arc", 120, () => String(++id));
  assert.equal(rows.at(-1).end, 128);
  assert.equal(new Set(rows.map((s) => s.id)).size, rows.length);
  rows.forEach((s, i) => {
    assert.equal(s.start, rows[i - 1]?.end || 0);
    assert.ok(s.energy >= 1 && s.energy <= 5);
  });
  assert.throws(() => C.template("not-real", 120, () => "id"));
  assert.throws(() => C.template("song", 0, () => "id"));
  assert.equal(C.template("texture", 120, () => "id").at(-1).end, 96);
});

const clip = (start, duration, extra = {}) => ({
  start,
  duration,
  offset: 0,
  fade_in: 0,
  fade_out: 0,
  gain_db: 0,
  notes: [],
  ...extra,
});
const track = (id, clips, extra = {}) => ({
  id,
  kind: "audio",
  gain_db: 0,
  mute: false,
  solo: false,
  clips,
  ...extra,
});
test("coverage merges overlaps per track and respects solo, mute and trimmed MIDI notes", () => {
  const project = {
    bpm: 120,
    sections: [{ id: "a", start: 0, end: 8 }],
    tracks: [
      track("audio", [clip(0, 2), clip(1, 2)]),
      track("muted", [clip(0, 4)], { mute: true }),
      track(
        "midi",
        [
          clip(0, 4, {
            offset: 1,
            notes: [
              { start: 0, length: 1 },
              { start: 3, length: 1 },
              { start: 20, length: 1 },
            ],
          }),
        ],
        { kind: "midi" },
      ),
    ],
  };
  const r = C.observe(project).rows[0];
  assert.equal(r.coverage, 0.75);
  assert.equal(r.layers, 0.875); // audio union 3s + one visible .5s note, divided by 4s
  assert.deepEqual(r.trackIds, ["audio", "midi"]);
  project.tracks[2].solo = true;
  assert.equal(C.observe(project).rows[0].coverage, 0.125);
  project.tracks[2].gain_db = -60;
  assert.equal(C.observe(project).rows[0].coverage, 0);
  project.tracks[2].mute = true;
  assert.equal(C.observe(project).rows[0].coverage, 0.75); // muted solo does not suppress other tracks
});
test("section observations expose gaps and overlaps without changing project data", () => {
  const project = {
    bpm: 120,
    tracks: [],
    sections: [
      { start: 4, end: 12 },
      { start: 8, end: 16 },
      { start: 20, end: 24 },
    ],
  };
  const before = JSON.stringify(project),
    r = C.observe(project);
  assert.equal(r.gaps, 2);
  assert.equal(r.overlaps, 1);
  assert.ok(r.rows.every((s) => s.coverage === 0));
  assert.equal(JSON.stringify(project), before);
});
test("edge fade action preserves longer fades and bounds very short clips", () => {
  for (const c of [
    clip(0, 1),
    clip(0, 0.01),
    clip(0, 1, { fade_in: 0.7, fade_out: 0.1 }),
    clip(0, 1, { fade_in: 0, fade_out: 0.99 }),
  ]) {
    const result = C.soften(c);
    assert.ok(result.fade_in >= c.fade_in && result.fade_out >= c.fade_out);
    assert.ok(result.fade_in + result.fade_out <= c.duration + 1e-12);
  }
  assert.deepEqual(C.soften(clip(0, 2)), { fade_in: 0.015, fade_out: 0.015 });
  assert.throws(() => C.soften(clip(0, 1), NaN));
});
