const test = require("node:test");
const assert = require("node:assert/strict");
const Timing = require("../src/music_studio/ui/static/station-timing.js");
const {
  StationEngine,
} = require("../src/music_studio/ui/static/station-engine.js");
const fs = require("node:fs");
const vm = require("node:vm");
const approx = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);

test("play range normalizes seeks and allows four bars of empty-session clicks", () => {
  assert.deepEqual(
    Timing.range({ bpm: 120, metronome: { enabled: true } }, 0, 12),
    { loop: false, start: 0, end: 8, at: 0 },
  );
  const content = { bpm: 120, loop: { enabled: true, start: 4, end: 8 } };
  assert.equal(Timing.range(content, 20, 3).at, 3);
  assert.equal(Timing.range(content, 20, 4).at, 2);
  assert.equal(Timing.range(content, 20, 0).at, 2);
});

test("beat scheduling aligns seeks, loop boundaries and adjacent pumps without duplicates", () => {
  const timing = {
    started: 10,
    at: 2.25,
    start: 2,
    end: 4,
    loop: true,
    bpm: 120,
  };
  const all = Timing.beatEvents(timing, 10, 14);
  assert.deepEqual(
    all.map((e) => e.beat),
    [5, 6, 7, 4, 5, 6, 7, 4],
  );
  assert.deepEqual(
    all.map((e) => e.time),
    [10.25, 10.75, 11.25, 11.75, 12.25, 12.75, 13.25, 13.75],
  );
  assert.deepEqual(
    [
      ...Timing.beatEvents(timing, 10, 11.75),
      ...Timing.beatEvents(timing, 11.75, 14),
    ],
    all,
  );
  assert.deepEqual(
    Timing.beatEvents({ ...timing, loop: false }, 10, 14),
    all.slice(0, 3),
  );
});

test("fractional loop endpoints preserve absolute beat accents and catch up after a long stall", () => {
  const timing = {
    started: 1,
    at: 0.125,
    start: 0.125,
    end: 1.125,
    loop: true,
    bpm: 120,
  };
  assert.deepEqual(
    Timing.beatEvents(timing, 1, 3.5).map((e) => [e.beat, e.time]),
    [
      [1, 1.375],
      [2, 1.875],
      [1, 2.375],
      [2, 2.875],
      [1, 3.375],
    ],
  );
  const late = Timing.beatEvents(timing, 36001.1, 36002.1);
  assert.deepEqual(
    late.map((e) => e.beat),
    [1, 2],
  );
  approx(late[0].time, 36001.375);
});

class Context {
  currentTime = 0;
  sampleRate = 1000;
  destination = {};
  sources = [];
  decodes = 0;
  async resume() {}
  node() {
    return {
      gain: {
        value: 1,
        setValueAtTime(v) {
          this.value = v;
        },
        setTargetAtTime(v) {
          this.value = v;
        },
        linearRampToValueAtTime() {},
      },
      connect(dest) {
        this.destination = dest;
      },
      disconnect() {
        this.disconnected = true;
      },
      getFloatTimeDomainData(data) {
        data.fill(0);
      },
    };
  }
  createGain() {
    return this.node();
  }
  createAnalyser() {
    return this.node();
  }
  createChannelSplitter() {
    return this.node();
  }
  createChannelMerger() {
    return this.node();
  }
  createBuffer(channels, length) {
    const data = Array.from(
      { length: channels },
      () => new Float32Array(length),
    );
    return { getChannelData: (i) => data[i] };
  }
  createBufferSource() {
    const node = this.node();
    node.start = (...args) => {
      node.started = args;
    };
    node.stop = () => {
      node.stopped = true;
    };
    this.sources.push(node);
    return node;
  }
  async decodeAudioData() {
    this.decodes++;
    return this.createBuffer(2, 10000);
  }
}
function fixture() {
  const ctx = new Context(),
    engine = new StationEngine(() => ctx),
    content = {
      bpm: 120,
      master_db: -6,
      loop: { enabled: true, start: 2, end: 4 },
      metronome: { enabled: true, volume_db: -18, accent: true },
      tracks: [
        {
          id: "track",
          kind: "audio",
          gain_db: 0,
          pan: 0,
          clips: [
            {
              id: "clip",
              asset: "source",
              start: 0,
              offset: 2,
              duration: 8,
              fade_in: 0,
              fade_out: 0,
              gain_db: 0,
            },
          ],
        },
      ],
    };
  let loads = 0;
  engine.buffer = async (...args) => {
    if (!engine.cache.has(args[0])) {
      loads++;
      engine.cache.set(args[0], ctx.decodeAudioData());
    }
    return engine.cache.get(args[0]);
  };
  return { ctx, engine, content, loads: () => loads };
}
test("engine pre-schedules exact loop joins, correct source offsets, and reuses buffers and effects", async () => {
  const { ctx, engine, content, loads } = fixture();
  try {
    await engine.play(content, [], "p", 1.5);
    const buffer = engine.playBuffers.get("source"),
      graph = engine.graphs.get("track");
    let clips = ctx.sources.filter((n) => n.buffer === buffer);
    assert.equal(clips.length, 2);
    [
      [0.04, 3.5, 0.5],
      [0.54, 3, 1],
    ].forEach((expected, i) =>
      expected.forEach((value, j) => approx(clips[i].started[j], value)),
    );
    ctx.currentTime = 1.2;
    approx(engine.current(), 1.66);
    engine.scheduleTiming();
    clips = ctx.sources.filter((n) => n.buffer === buffer);
    approx(clips[1].started[0] + clips[1].started[2], clips[2].started[0]);
    assert.equal(engine.graphs.get("track"), graph);
    assert.equal(loads(), 1);
    assert.equal(ctx.decodes, 1);
    const total = ctx.sources.length;
    engine.scheduleTiming();
    assert.equal(ctx.sources.length, total);
    clips[0].onended();
    assert.ok(!engine.nodes.includes(clips[0]));
    assert.equal(clips[0].disconnected, true);
    const scheduled = [...engine.nodes];
    engine.pause();
    assert.ok(scheduled.every((n) => n.stopped && n.disconnected));
    assert.equal(engine.timingTimer, null);
    assert.equal(engine.playBuffers, null);
    assert.equal(engine.playContent, null);
  } finally {
    engine.pause();
  }
});

test("live click volume and toggle changes preserve the running audio and timeline", async () => {
  const { ctx, engine, content, loads } = fixture();
  try {
    await engine.play(content, [], "p");
    const buffer = engine.playBuffers.get("source"),
      clips = ctx.sources.filter((n) => n.buffer === buffer),
      anchor = engine.started;
    content.metronome.volume_db = -12;
    engine.update(content);
    approx(engine.clickGain.gain.value, 10 ** (-12 / 20));
    const oldClicks = [...engine.clickNodes];
    content.metronome.enabled = false;
    engine.update(content);
    assert.ok(oldClicks.every((n) => n.stopped));
    assert.equal(engine.clickGain.gain.value, 0);
    content.metronome.enabled = true;
    content.metronome.accent = false;
    engine.update(content);
    engine.scheduleTiming();
    assert.ok(
      engine.clickNodes.every((n) => n.buffer === engine.clickBuffer(false)),
    );
    assert.ok(clips.every((n) => !n.stopped));
    assert.equal(loads(), 1);
    assert.equal(engine.started, anchor);
    const click = engine.clickNodes[0];
    click.onended();
    assert.ok(!engine.clickNodes.includes(click));
  } finally {
    engine.pause();
  }
});

test("loop scheduler recovers clock phase after missed pumps without queuing past cycles", async () => {
  const { ctx, engine, content } = fixture();
  try {
    await engine.play(content, [], "p");
    const buffer = engine.playBuffers.get("source"),
      count = ctx.sources.length;
    ctx.currentTime = 100;
    engine.scheduleTiming();
    const newClips = ctx.sources
      .slice(count)
      .filter((n) => n.buffer === buffer);
    assert.equal(newClips.length, 3);
    approx(newClips[0].started[0], 100.005);
    approx(newClips[0].started[1], 3.965);
    approx(newClips[1].started[0], 100.04);
    approx(engine.current(), 1.96);
    assert.ok(ctx.sources.slice(count).every((n) => n.started[0] > 100));
  } finally {
    engine.pause();
  }
});

test("empty-session playback produces clicks for four bars and pause cancels all", async () => {
  const ctx = new Context(),
    engine = new StationEngine(() => ctx);
  try {
    await engine.play(
      { bpm: 120, tracks: [], master_db: -6, metronome: { enabled: true } },
      [],
      "p",
    );
    assert.equal(engine.playRange.end, 8);
    assert.deepEqual(
      engine.clickNodes.map((n) => n.started[0]),
      [0.04, 0.54, 1.04],
    );
    assert.equal(engine.clickNodes[0].buffer, engine.clickBuffer(true));
    assert.equal(engine.clickNodes[1].destination, engine.clickGain);
    assert.equal(engine.clickGain.destination, ctx.destination);
    ctx.currentTime = 0.01;
    assert.equal(engine.current(), 0);
  } finally {
    engine.pause();
  }
});

test("timing dialog validates before applying, preserves drafts during rerenders and converts bars to beats", async () => {
  const elements = new Map(),
    applied = [],
    toggles = [],
    content = { bpm: 120 },
    clip = { start: 1, duration: 2 };
  const $ = (id) => {
    if (!elements.has(id))
      elements.set(id, {
        value: "",
        classList: { toggle() {} },
        setAttribute() {},
        showModal() {
          this.open = true;
        },
        close() {
          this.open = false;
        },
      });
    return elements.get(id);
  };
  const env = { StationTiming: Timing };
  vm.runInNewContext(
    fs.readFileSync(
      require.resolve("../src/music_studio/ui/static/station-timing-ui.js"),
      "utf8",
    ),
    env,
  );
  const ui = env.StationTimingUI.mount({
    $,
    tr: (zh, en) => en,
    content: () => content,
    selectedClip: () => clip,
    duration: () => 8,
    apply: async (settings) =>
      applied.push(JSON.parse(JSON.stringify(settings))),
    toggle: (kind) => toggles.push(kind),
  });
  $("timing-settings").onclick();
  $("timing-start").value = "3";
  $("timing-end").value = "2";
  ui.render();
  assert.equal($("timing-start").value, "3");
  await $("timing-apply").onclick();
  assert.equal(applied.length, 0);
  assert.ok($("timing-error").textContent);
  $("timing-clip").onclick();
  assert.equal($("timing-start").value, 1.5);
  assert.equal($("timing-end").value, 2.5);
  $("timing-loop").checked = true;
  $("timing-click").checked = true;
  await $("timing-apply").onclick();
  assert.deepEqual(applied[0].loop, { enabled: true, start: 2, end: 6 });
  assert.equal($("timing-dialog").open, false);
  $("metronome").onclick();
  assert.deepEqual(toggles, ["metronome"]);
  assert.equal(content.loop, undefined);
});
