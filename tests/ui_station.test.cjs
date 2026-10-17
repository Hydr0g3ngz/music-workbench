const test = require("node:test");
const assert = require("node:assert/strict");
const {
  StationEngine,
  splitClip,
  audible,
  midiBuffer,
  sampledBuffer,
  duration,
} = require("../src/music_studio/ui/static/station-engine.js");

const Effects = require("../src/music_studio/ui/static/effects-dsp.js");

test("mix duration retains audible effect tails and skips muted or bypassed tails", () => {
  const track = {
    id: "a",
    clips: [{ start: 1, duration: 2 }],
    effects: {
      reverb: { enabled: true, decay: 1.2, mix: 0.2 },
    },
  };
  assert.equal(duration({ tracks: [track] }), 4.3);
  track.effects.bypass = true;
  assert.equal(duration({ tracks: [track] }), 3);
  track.effects.bypass = false;
  track.mute = true;
  assert.equal(duration({ tracks: [track] }), 3);
});

test("live A/B crossfades without resetting compressor history", () => {
  const settings = Effects.normalize({
    compressor: { enabled: true, threshold_db: -30, ratio: 4 },
  });
  const rack = new Effects.Rack(settings),
    source = new Float64Array(44100).fill(0.5),
    out = new Float64Array(44100);
  rack.process(source, source, out, new Float64Array(44100));
  const previous = out.at(-1),
    held = rack.held;
  rack.configure({ ...settings, bypass: true });
  rack.process(source, source, out, new Float64Array(44100));
  assert.ok(Math.abs(out[0] - previous) < 0.002);
  assert.equal(out[1000], 0.5);
  assert.equal(rack.held, held);
});

test("the actual worklet wrapper handles stereo, silence and explicit disposal", () => {
  const fs = require("node:fs"),
    vm = require("node:vm");
  let Worklet;
  const code = fs
    .readFileSync(
      require.resolve("../src/music_studio/ui/static/station-worklet.js"),
      "utf8",
    )
    .replace(/^import .*;\r?\n/, "");
  vm.runInNewContext(code, {
    StationEffects: Effects,
    sampleRate: 44100,
    AudioWorkletProcessor: class {
      constructor() {
        this.port = {
          postMessage() {},
          close() {
            this.closed = true;
          },
        };
      }
    },
    registerProcessor(name, klass) {
      assert.equal(name, "studio-effects");
      Worklet = klass;
    },
  });
  const processor = new Worklet({
    processorOptions: {
      settings: { enabled: true, ceiling_db: -1 },
      master: true,
    },
  });
  const left = new Float32Array(128).fill(2),
    right = new Float32Array(128).fill(0.5),
    out = [new Float32Array(128), new Float32Array(128)];
  assert.equal(processor.process([[left, right]], [out]), true);
  assert.ok(out[0].every((x) => x <= 10 ** (-1 / 20) + 1e-7));
  assert.ok(out[0].every((x, i) => Math.abs(x / 4 - out[1][i]) < 1e-7));
  processor.process([[]], [out]);
  assert.ok(out[0].every((x) => x === 0));
  processor.port.onmessage({ data: { dispose: true } });
  assert.equal(processor.port.closed, true);
  assert.equal(processor.process([[]], [out]), false);
});

test("splitting retains source offset and notes, with no overlapping fades", () => {
  const clip = {
    id: "0123456789abcdef",
    start: 2,
    offset: 3,
    duration: 5,
    fade_in: 0.5,
    fade_out: 1,
    notes: [{ pitch: 60, start: 0, length: 1, velocity: 90 }],
  };
  const parts = splitClip(clip, 4);
  assert.equal(parts[0].duration, 2);
  assert.equal(parts[1].start, 4);
  assert.equal(parts[1].offset, 5);
  assert.equal(parts[1].duration, 3);
  assert.equal(parts[0].fade_out, 0);
  assert.equal(parts[1].fade_in, 0);
  assert.deepEqual(parts[1].notes, clip.notes);
  assert.equal(clip.duration, 5);
  assert.equal(splitClip(clip, 2), null);
  assert.equal(splitClip(clip, 7), null);
});

test("sampled notes interpolate stereo, transpose and stop at note-off", () => {
  const ctx = new FakeContext(),
    source = ctx.createBuffer(2, 1000);
  source.sampleRate = 1000;
  for (let i = 0; i < 1000; i++) {
    source.getChannelData(0)[i] = i / 1000;
    source.getChannelData(1)[i] = -i / 1000;
  }
  const lib = {
    samples: [{ id: "p", instrument: "vcsl-piano", root: 60, frames: 44100 }],
  };
  const audio = sampledBuffer(
    ctx,
    {
      offset: 0,
      duration: 0.3,
      notes: [{ pitch: 72, start: 0, length: 0.2, velocity: 127 }],
    },
    120,
    "vcsl-piano",
    lib,
    new Map([["p", source]]),
  );
  assert.ok(Math.abs(audio.getChannelData(0)[4] - 0.008 * 0.55) < 1e-8);
  assert.ok(Math.abs(audio.getChannelData(1)[4] + 0.008 * 0.55) < 1e-8);
  assert.ok(
    audio
      .getChannelData(0)
      .slice(100)
      .every((x) => x === 0),
  );
});

test("drum hits keep one-shot tails and a subsequent hat chokes the earlier hit", () => {
  const ctx = new FakeContext(),
    source = ctx.createBuffer(2, 1000);
  source.sampleRate = 1000;
  source.getChannelData(0).fill(0.5);
  source.getChannelData(1).fill(0.5);
  const lib = {
    samples: [
      {
        id: "closed-hat",
        instrument: "vcsl-drums",
        root: 42,
        keys: [42, 46],
        frames: 44100,
      },
    ],
  };
  const notes = [
    { pitch: 46, start: 0, length: 0.001, velocity: 127 },
    { pitch: 42, start: 0.2, length: 0.001, velocity: 127 },
  ];
  const audio = sampledBuffer(
    ctx,
    { offset: 0, duration: 0.4, notes },
    120,
    "vcsl-drums",
    lib,
    new Map([["closed-hat", source]]),
  );
  // The open hat ends exactly at 100ms and the closed hit replaces it at the same level.
  for (const at of [10, 99, 100, 150])
    assert.ok(Math.abs(audio.getChannelData(0)[at] - 0.275) < 1e-6);
});

test("sample loading is shared by notes and playback, never by mixer refresh", async () => {
  const oldFetch = global.fetch;
  let loads = 0;
  global.fetch = async () => {
    loads++;
    return { ok: true, arrayBuffer: async () => new ArrayBuffer(4) };
  };
  try {
    const engine = new StationEngine(() => new FakeContext());
    engine.setLibrary({
      samples: [
        {
          id: "p",
          instrument: "vcsl-piano",
          root: 60,
          frames: 44100,
          sha256: "abc",
          url: "/sample",
        },
      ],
    });
    const notes = [
      { pitch: 60, start: 0, length: 0.5, velocity: 90 },
      { pitch: 64, start: 0.5, length: 0.5, velocity: 80 },
    ];
    const track = {
      id: "t",
      kind: "midi",
      instrument: "vcsl-piano",
      gain_db: 0,
      pan: 0,
      mute: false,
      solo: false,
      clips: [
        {
          id: "c",
          offset: 0,
          start: 0,
          duration: 1,
          notes,
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
        },
      ],
    };
    const content = { bpm: 120, master_db: -6, tracks: [track] };
    await engine.note(60, "vcsl-piano");
    await engine.play(content, [], "project", 0);
    for (let i = 0; i < 100; i++) engine.update(content);
    engine.pause();
    await engine.play(content, [], "project", 0.2);
    assert.equal(loads, 1);
  } finally {
    global.fetch = oldFetch;
  }
});
test("mute overrides solo, and solo excludes other tracks", () => {
  const a = { mute: false, solo: false },
    b = { mute: false, solo: true };
  assert.equal(audible(a, [a, b]), false);
  assert.equal(audible(b, [a, b]), true);
  b.mute = true;
  assert.equal(audible(b, [a, b]), false);
});
test("live effect changes reuse sources and modules, then dispose every worklet on pause", async () => {
  const oldFetch = global.fetch,
    oldNode = global.AudioWorkletNode;
  let loads = 0,
    modules = 0;
  const created = [];
  global.fetch = async () => {
    loads++;
    return { ok: true, arrayBuffer: async () => new ArrayBuffer(4) };
  };
  global.AudioWorkletNode = class {
    constructor() {
      this.messages = [];
      this.port = { postMessage: (value) => this.messages.push(value) };
      created.push(this);
    }
    connect() {}
    disconnect() {
      this.disconnected = true;
    }
  };
  try {
    const ctx = new FakeContext();
    ctx.audioWorklet = {
      async addModule() {
        modules++;
      },
    };
    const engine = new StationEngine(() => ctx),
      track = {
        id: "a",
        kind: "audio",
        gain_db: 0,
        pan: 0,
        effects: Effects.defaults(),
        clips: [
          {
            id: "c",
            asset: "audio",
            start: 0,
            offset: 0,
            duration: 1,
            gain_db: 0,
            fade_in: 0,
            fade_out: 0,
          },
        ],
      },
      content = { tracks: [track], master_db: -6 },
      assets = [{ id: "audio", duration: 1 }];
    await engine.play(content, assets, "project");
    const rack = engine.graphs.get("a").effect;
    for (let i = 0; i < 100; i++) {
      track.gain_db = -i / 10;
      engine.update(content);
    }
    assert.equal(rack.messages.length, 0);
    track.effects = Effects.normalize(Effects.presets.warm.settings);
    engine.update(content);
    assert.equal(rack.messages.length, 1);
    assert.equal(ctx.sources.length, 1);
    assert.equal(loads, 1);
    engine.pause();
    assert.ok(
      created.every(
        (node) => node.disconnected && node.messages.at(-1).dispose,
      ),
    );
    await engine.play(content, assets, "project");
    assert.equal(modules, 1);
    assert.equal(loads, 1);
    engine.pause();
  } finally {
    global.fetch = oldFetch;
    global.AudioWorkletNode = oldNode;
  }
});

test("pause during worklet module loading cancels the pending start", async () => {
  const ctx = new FakeContext();
  let release;
  ctx.audioWorklet = {
    addModule: () => new Promise((resolve) => (release = resolve)),
  };
  const engine = new StationEngine(() => ctx);
  const pending = engine.play({ tracks: [], master_db: -6 }, [], "p");
  await new Promise((resolve) => setImmediate(resolve));
  engine.pause();
  release();
  assert.equal(await pending, false);
  assert.equal(ctx.sources.length, 0);
  assert.equal(engine.masterEffect, undefined);
});

class FakeContext {
  constructor() {
    this.sampleRate = 1000;
    this.currentTime = 0;
    this.destination = {};
    this.sources = [];
  }
  async resume() {}
  createBuffer(ch, length) {
    const data = Array.from({ length: ch }, () => new Float32Array(length));
    return {
      getChannelData: (i) => data[i],
      copyToChannel: (d, i) => data[i].set(d),
    };
  }
  node() {
    return {
      gain: {
        value: 1,
        setValueAtTime() {},
        setTargetAtTime() {},
        linearRampToValueAtTime() {},
      },
      connect() {},
      disconnect() {},
      getFloatTimeDomainData(a) {
        a.fill(0);
      },
    };
  }
  createGain() {
    return this.node();
  }
  createChannelSplitter() {
    return this.node();
  }
  createChannelMerger() {
    return this.node();
  }
  createAnalyser() {
    return this.node();
  }
  createBufferSource() {
    const node = this.node();
    node.start = (...args) => (node.started = args);
    node.stop = () => (node.stopped = true);
    this.sources.push(node);
    return node;
  }
  async decodeAudioData() {
    return this.createBuffer(2, 1000);
  }
}
test("MIDI synthesis makes finite identical stereo channels and keeps silence around notes", () => {
  const ctx = new FakeContext();
  const b = midiBuffer(
    ctx,
    {
      offset: 0,
      duration: 1,
      notes: [{ pitch: 60, start: 0.5, length: 0.5, velocity: 100 }],
    },
    120,
    "keys",
  );
  const data = b.getChannelData(0);
  assert.ok(data.every(Number.isFinite));
  assert.ok(data.slice(0, 250).every((x) => x === 0));
  assert.ok(data.some((x) => Math.abs(x) > 0.01));
  assert.deepEqual(data, b.getChannelData(1));
  assert.ok(data.slice(500).every((x) => x === 0));
});
test("task/UI refresh and live mix updates never reload audio; pause cancels an in-flight start", async () => {
  const oldFetch = global.fetch;
  let loads = 0,
    release;
  global.fetch = async () => {
    loads++;
    return { ok: true, arrayBuffer: async () => new ArrayBuffer(4) };
  };
  try {
    const ctx = new FakeContext(),
      engine = new StationEngine(() => ctx);
    const track = {
      id: "a",
      gain_db: 0,
      pan: 0,
      mute: false,
      solo: false,
      kind: "audio",
      clips: [
        {
          id: "c",
          asset: "source",
          start: 1,
          offset: 0,
          duration: 1,
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
        },
      ],
    };
    const content = { tracks: [track], master_db: -6 },
      assets = [{ id: "source", duration: 1 }];
    await engine.play(content, assets, "project", 0);
    assert.equal(ctx.sources[0].started[0], 1.04);
    for (let i = 0; i < 100; i++) {
      track.gain_db = -i / 10;
      engine.update(content);
    }
    assert.equal(loads, 1);
    assert.equal(ctx.sources.length, 1);
    engine.pause();
    await engine.play(content, assets, "project", 0.5);
    assert.equal(loads, 1);
    engine.reset();
    global.fetch = () => new Promise((resolve) => (release = resolve));
    const pending = engine.play(content, assets, "project", 0);
    await new Promise((r) => setImmediate(r));
    engine.pause();
    release({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) });
    assert.equal(await pending, false);
    assert.equal(engine.playing, false);
  } finally {
    global.fetch = oldFetch;
  }
});

test("buses receive only routed post-fader paths; live sends/solo keep the same audio source", async () => {
  const oldFetch = global.fetch;
  let loads = 0;
  global.fetch = async () => {
    loads++;
    return { ok: true, arrayBuffer: async () => new ArrayBuffer(4) };
  };
  const ctx = new FakeContext();
  const originalNode = ctx.node.bind(ctx);
  ctx.node = () => {
    const node = originalNode();
    node.connections = [];
    node.connect = (target) => node.connections.push(target);
    node.disconnect = () => {
      node.connections = [];
    };
    node.gain.setTargetAtTime = (value) => {
      node.gain.value = value;
    };
    return node;
  };
  const engine = new StationEngine(() => ctx);
  try {
    const track = {
      id: "source",
      kind: "audio",
      gain_db: -6,
      pan: 0,
      output: "group",
      sends: [{ bus: "return", enabled: true, gain_db: -12 }],
      clips: [
        {
          id: "c",
          asset: "a",
          start: 0,
          offset: 0,
          duration: 1,
          gain_db: 0,
          fade_in: 0,
          fade_out: 0,
        },
      ],
    };
    const bus = (id) => ({
      id,
      name: id,
      gain_db: 0,
      pan: 0,
      mute: false,
      solo: false,
    });
    const content = {
      tracks: [track],
      buses: [bus("group"), bus("return")],
      master_db: -6,
    };
    await engine.play(content, [{ id: "a", duration: 1 }], "project");
    const source = ctx.sources[0],
      graph = engine.graphs.get("source"),
      group = engine.graphs.get("group"),
      wet = engine.graphs.get("return");
    assert.deepEqual(graph.analyser.connections, [
      graph.direct,
      graph.sends.get("return"),
    ]);
    assert.deepEqual(graph.direct.connections, [group.input]);
    assert.deepEqual(graph.sends.get("return").connections, [wet.input]);
    assert.deepEqual(group.analyser.connections, [engine.master]);
    assert.ok(
      Math.abs(graph.sends.get("return").gain.value - 10 ** (-12 / 20)) < 1e-10,
    );
    for (let i = 0; i < 100; i++) {
      content.buses[0].gain_db = -i / 10;
      track.sends[0].gain_db = -i / 20;
      engine.update(content);
    }
    track.sends[0].enabled = false;
    content.buses[1].solo = true;
    engine.update(content);
    assert.equal(graph.sends.get("return").gain.value, 0);
    assert.equal(group.level.gain.value, 0);
    assert.equal(wet.level.gain.value, 1);
    content.buses[1].mute = true;
    engine.update(content);
    assert.equal(wet.level.gain.value, 0);
    assert.equal(loads, 1);
    assert.equal(ctx.sources.length, 1);
    assert.equal(ctx.sources[0], source);
    engine.pause();
    assert.equal(source.stopped, true);
    for (const g of [graph, group, wet])
      assert.ok(g.nodes.every((n) => !n.connections.length));
  } finally {
    engine.pause();
    global.fetch = oldFetch;
  }
});
