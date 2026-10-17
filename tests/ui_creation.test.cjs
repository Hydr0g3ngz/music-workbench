const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

test("tempo edits scale MIDI positions and fades, preserve audio and reject oversized sessions", () => {
  const source = fs.readFileSync(
    require.resolve("../src/music_studio/ui/static/station.js"),
    "utf8",
  );
  const initial = {
    bpm: 120,
    tracks: [
      {
        kind: "midi",
        clips: [
          { start: 1, duration: 2, offset: 1, fade_in: 0.2, fade_out: 0.4 },
        ],
      },
      {
        kind: "audio",
        clips: [
          { start: 2, duration: 3, offset: 0.5, fade_in: 0.1, fade_out: 0.2 },
        ],
      },
    ],
  };
  const state = structuredClone(initial),
    field = { value: "240" };
  let errors = 0;
  const context = vm.createContext({
    $: () => field,
    content: () => state,
    mutate: (fn) => fn(),
    renderGenerationHealth() {},
    toast() {
      errors++;
    },
    tr: (a, b) => b,
  });
  const start = source.indexOf('$("bpm").onchange =');
  vm.runInContext(
    source.slice(start, source.indexOf('$("import").onclick', start)),
    context,
  );
  field.onchange();
  assert.equal(state.bpm, 240);
  assert.deepEqual(state.tracks[0].clips[0], {
    start: 0.5,
    duration: 1,
    offset: 0.5,
    fade_in: 0.1,
    fade_out: 0.2,
  });
  assert.deepEqual(state.tracks[1], initial.tracks[1]);
  state.tracks[0].clips[0].duration = 400;
  const snapshot = structuredClone(state);
  field.value = "30";
  field.onchange();
  assert.deepEqual(state, snapshot);
  assert.equal(field.value, 240);
  assert.equal(errors, 1);
});

test("the transport stop button also stops asset and generation auditions", () => {
  const source = fs.readFileSync(
      require.resolve("../src/music_studio/ui/static/station.js"),
      "utf8",
    ),
    field = {};
  let stopped = 0,
    paused = 0;
  const context = vm.createContext({
    $: () => field,
    stopPreview() {
      stopped++;
    },
    pause() {
      paused++;
    },
    s: { position: 3 },
    engine: { position: 3 },
  });
  const start = source.indexOf('$("stop").onclick =');
  vm.runInContext(
    source.slice(start, source.indexOf('$("rewind").onclick', start)),
    context,
  );
  field.onclick();
  assert.equal(stopped, 1);
  assert.equal(paused, 1);
  assert.equal(context.s.position, 0);
});

test("generation and stem polling preserve audition sources, time and playing state", async () => {
  const source = fs.readFileSync(
    require.resolve("../src/music_studio/ui/static/station.js"),
    "utf8",
  );
  const section = (start, end) =>
    source.slice(
      source.indexOf(start),
      source.indexOf(end, source.indexOf(start)),
    );
  const task = {
    id: "a123456789abcdef",
    model: "ACE-Step",
    status: "complete",
    parameters: { duration: 12, prompt: "Jazz piano", seed: 42 },
  };
  const state = {
    session: { id: "1234567890abcdef", assets: [] },
    tasks: [],
    generations: [task],
  };
  const elements = new Map();
  let loads = 0,
    plays = 0,
    paused = true;
  const audio = {
    currentTime: 0,
    pause() {
      paused = true;
    },
    async play() {
      paused = false;
      plays++;
    },
    set src(value) {
      loads++;
      this.url = value;
    },
  };
  const context = vm.createContext({
    WorkbenchNavigation: require("../src/music_studio/ui/static/workbench-navigation.js"),
    StationModelControls: require("../src/music_studio/ui/static/station-model-controls.js"),
    s: state,
    generationAudio: audio,
    fitPanel: { stop() {} },
    auditionPanel: { stop() {} },
    previewEngine: { pause() {} },
    pause() {},
    renderGrooves() {},
    renderInstruments() {},
    clearTimeout() {},
    setTimeout() {
      return 1;
    },
    previewTimer: undefined,
    previewKey: null,
    generationAudioKey: null,
    polling: false,
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
    tr: (zh, en) => en,
    esc: (x) => String(x ?? ""),
    base: () => "/api/workstation/projects/1234567890abcdef",
    request: async (url) =>
      url.endsWith("/generations") ? [task] : state.tasks,
    console,
  });
  vm.runInContext(
    section("function stopPreview()", "async function audition(") +
      section(
        "function renderGenerationTasks()",
        "async function projectDialog()",
      ) +
      ";globalThis.audition=auditionGeneration;globalThis.stem=auditionTask;globalThis.poll=pollTasks;globalThis.stop=stopPreview;",
    context,
  );
  await context.audition(task.id);
  audio.currentTime = 6.25;
  for (let i = 0; i < 30; i++) await context.poll();
  assert.equal(loads, 1);
  assert.equal(plays, 1);
  assert.equal(paused, false);
  assert.equal(audio.currentTime, 6.25);
  context.stop();
  assert.equal(paused, true);
  await context.audition(task.id);
  assert.equal(loads, 1);
  assert.equal(plays, 2);
  context.stop();
  state.tasks = [
    {
      id: "b123456789abcdef",
      model: "mel-band-roformer-kj",
      status: "complete",
      source_project: "c123456789abcdef",
      stage: "separate",
      source_clip: {
        name: "Trimmed mix",
        start: 2.5,
        offset: 0.5,
        duration: 2,
      },
      artifacts: [{ id: "d123456789abcdef", role: "vocals", kind: "audio" }],
    },
  ];
  await context.stem("c123456789abcdef", "d123456789abcdef");
  assert.equal(audio.currentTime, 0.5);
  audio.currentTime = 1.25;
  for (let i = 0; i < 30; i++) await context.poll();
  assert.equal(loads, 2);
  assert.equal(plays, 3);
  assert.equal(audio.currentTime, 1.25);
  assert.equal(paused, false);
  context.stop();
  await context.stem("c123456789abcdef", "d123456789abcdef");
  assert.equal(loads, 2);
  assert.equal(plays, 4);
});
