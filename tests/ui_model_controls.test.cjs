const test = require("node:test");
const assert = require("node:assert/strict");
const controls = require("../src/music_studio/ui/static/station-model-controls.js");

test("cropped previews and tempo reports use their own origin, including old tasks", () => {
  const task = {source_clip: {offset: 12, duration: 8}, stage: "transform", time_ratio: 2};
  assert.deepEqual(controls.clipWindow(task), {offset: 6, duration: 4});
  task.source_range = {start: 12};
  assert.deepEqual(controls.clipWindow(task), {offset: 0, duration: 4});
  const report = {tempo_bpm: 120, beats: [0.1, 0.6]};
  assert.deepEqual(controls.sourceReport(task, report).beats, [12.1, 12.6]);
  assert.deepEqual(report.beats, [0.1, 0.6]);
  task.source_range.scope = "clip";
  task.input_audio = {frames: 176401, sample_rate: 44100};
  assert.deepEqual(controls.clipWindow(task), {offset: 0, duration: Math.round(176401 / 2) / 44100});
});

test("main workstation offers controls relevant to the actual model and runtime", () => {
  const whisper = controls.controls({ stage: "lyrics", devices: ["cpu", "cuda"] }, {device: "cuda", language: "zh"}, "en");
  assert.match(whisper, /value="cuda" selected/);
  assert.match(whisper, /value="zh" selected/);
  assert.doesNotMatch(whisper, /Cleanup strength/);
  assert.doesNotMatch(whisper, /data-model-option="alignment"/);
  for (const lang of ["zh", "en"]) {
    const qwen = controls.controls({ id: "qwen3-asr", stage: "lyrics", devices: ["cpu", "cuda"] }, {alignment: "native"}, lang);
    assert.match(qwen, /value="native" selected/);
    assert.match(qwen, /data-model-option="alignment"/);
  }
  const cleanup = controls.controls({ stage: "denoise", device: "cpu" }, {strength: 0.35}, "en");
  assert.match(cleanup, /value="0.35"/);
  assert.doesNotMatch(cleanup, /data-model-option="device"/);
  assert.doesNotMatch(controls.controls({stage: "melody", devices: ["cpu"]}, {}, "en"), /value="cuda"/);
});

test("controls submit typed values and reject invalid strength before queuing", () => {
  const fields = [
    {dataset: {modelOption: "device"}, value: "cuda"},
    {dataset: {modelOption: "language"}, value: ""},
    {dataset: {modelOption: "alignment"}, value: "qwen"},
    {dataset: {modelOption: "strength"}, value: "0.35", checkValidity: () => true},
  ];
  const card = {querySelectorAll: () => fields};
  assert.deepEqual(controls.read(card), {device: "cuda", language: null, alignment: "qwen", strength: 0.35});
  let reported = false;
  fields[3].checkValidity = () => false;
  fields[3].reportValidity = () => { reported = true; };
  assert.throws(() => controls.read(card));
  assert.equal(reported, true);
});
