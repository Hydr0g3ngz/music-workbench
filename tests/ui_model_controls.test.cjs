const test = require("node:test");
const assert = require("node:assert/strict");
const controls = require("../src/music_studio/ui/static/station-model-controls.js");

test("main workstation offers controls relevant to the actual model and runtime", () => {
  const whisper = controls.controls({ stage: "lyrics", devices: ["cpu", "cuda"] }, {device: "cuda", language: "zh"}, "en");
  assert.match(whisper, /value="cuda" selected/);
  assert.match(whisper, /value="zh" selected/);
  assert.doesNotMatch(whisper, /Cleanup strength/);
  const cleanup = controls.controls({ stage: "denoise", device: "cpu" }, {strength: 0.35}, "en");
  assert.match(cleanup, /value="0.35"/);
  assert.doesNotMatch(cleanup, /data-model-option="device"/);
  assert.doesNotMatch(controls.controls({stage: "melody", devices: ["cpu"]}, {}, "en"), /value="cuda"/);
});

test("controls submit typed values and reject invalid strength before queuing", () => {
  const fields = [
    {dataset: {modelOption: "device"}, value: "cuda"},
    {dataset: {modelOption: "language"}, value: ""},
    {dataset: {modelOption: "strength"}, value: "0.35", checkValidity: () => true},
  ];
  const card = {querySelectorAll: () => fields};
  assert.deepEqual(controls.read(card), {device: "cuda", language: null, strength: 0.35});
  let reported = false;
  fields[2].checkValidity = () => false;
  fields[2].reportValidity = () => { reported = true; };
  assert.throws(() => controls.read(card));
  assert.equal(reported, true);
});
