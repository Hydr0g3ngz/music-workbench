const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const root = "../src/music_studio/ui/static/";

function worklet() {
  let Processor;
  const messages = [];
  vm.runInNewContext(
    fs.readFileSync(
      require.resolve(root + "station-recorder-worklet.js"),
      "utf8",
    ),
    {
      AudioWorkletProcessor: class {
        constructor() {
          this.port = { postMessage: (data) => messages.push(data) };
        }
      },
      sampleRate: 48000,
      registerProcessor: (_, value) => {
        Processor = value;
      },
      Float32Array,
    },
  );
  const instance = new Processor();
  return {
    instance,
    messages,
    command: (data) => instance.port.onmessage({ data }),
  };
}

test("capture preserves tail frames, averages channels and stops at the exact frame limit", () => {
  const { instance, messages, command } = worklet();
  command({ type: "start", seconds: 5001 / 48000 });
  for (let i = 0; i < 50; i++)
    instance.process([
      [new Float32Array(128).fill(0.6), new Float32Array(128).fill(0.2)],
    ]);
  const chunks = messages.filter((m) => m.type === "chunk");
  assert.deepEqual(
    chunks.map((c) => c.samples.length),
    [4096, 905],
  );
  assert.ok(
    chunks.every((c) => c.samples.every((v) => Math.abs(v - 0.4) < 1e-7)),
  );
  assert.equal(messages.filter((m) => m.type === "stopped").length, 1);
  assert.equal(messages.find((m) => m.type === "stopped").frames, 5001);
  command({ type: "stop" });
  assert.equal(messages.filter((m) => m.type === "stopped").length, 1);
});

test("manual stop flushes a partial block and input metering never records before start", () => {
  const { instance, messages, command } = worklet();
  for (let i = 0; i < 30; i++)
    instance.process([[new Float32Array(128).fill(0.9)]]);
  assert.ok(
    messages.some((m) => m.type === "meter" && Math.abs(m.peak - 0.9) < 1e-6),
  );
  assert.equal(messages.filter((m) => m.type === "chunk").length, 0);
  command({ type: "start", seconds: 10 });
  instance.process([[new Float32Array(128).fill(0.25)]]);
  command({ type: "stop" });
  assert.equal(messages.find((m) => m.type === "chunk").samples.length, 128);
  assert.equal(messages.find((m) => m.type === "stopped").frames, 128);
});

function runtime(media = {}) {
  let node,
    streamStops = 0,
    closes = 0;
  const track = {
    stop() {
      streamStops++;
    },
  };
  const stream = { getTracks: () => [track], getAudioTracks: () => [track] };
  const context = {
    Blob,
    Float32Array,
    DataView,
    ArrayBuffer,
    setTimeout,
    clearTimeout,
    navigator: { mediaDevices: { getUserMedia: async () => stream, ...media } },
    AudioContext: class {
      constructor() {
        this.sampleRate = 48000;
        this.audioWorklet = { addModule: async () => {} };
      }
      async resume() {}
      async close() {
        closes++;
      }
      createMediaStreamSource() {
        return { connect() {}, disconnect() {} };
      }
    },
    AudioWorkletNode: class {
      constructor() {
        node = this;
        this.port = { postMessage() {} };
      }
      connect() {}
      disconnect() {}
    },
  };
  vm.runInNewContext(
    fs.readFileSync(require.resolve(root + "station-recorder.js"), "utf8"),
    context,
  );
  return {
    ...context.StationRecording,
    track,
    stream,
    node: () => node,
    stops: () => streamStops,
    closes: () => closes,
  };
}

test("WAV export keeps the actual device sample rate, frame count and PCM bounds", async () => {
  const { wav } = runtime();
  const view = new DataView(
    await wav(
      [new Float32Array([-2, -0.5, 0, 0.5, 2, NaN])],
      48000,
    ).arrayBuffer(),
  );
  assert.equal(view.byteLength, 56);
  assert.equal(view.getUint32(24, true), 48000);
  assert.equal(view.getUint16(22, true), 1);
  assert.equal(view.getUint32(40, true), 12);
  assert.deepEqual(
    Array.from({ length: 6 }, (_, i) => view.getInt16(44 + i * 2, true)),
    [-32768, -16384, 0, 16384, 32767, 0],
  );
});

test("cancelled permission requests release a late stream without starting capture", async () => {
  let grant;
  const env = runtime({
    getUserMedia: () =>
      new Promise((resolve) => {
        grant = resolve;
      }),
  });
  const recorder = new env.Recorder();
  const preparing = recorder.prepare();
  recorder.cancel();
  grant(env.stream);
  assert.equal(await preparing, false);
  assert.equal(recorder.state, "idle");
  assert.equal(env.stops(), 1);
  assert.equal(env.node(), undefined);
});

test("stop releases all microphone resources and keeps a downloadable take; cancel clears it", async () => {
  const env = runtime(),
    recorder = new env.Recorder();
  assert.equal(await recorder.prepare(), true);
  recorder.start(10);
  env
    .node()
    .port.onmessage({
      data: { type: "chunk", samples: new Float32Array(256) },
    });
  recorder.stop();
  assert.equal(recorder.state, "stopping");
  env.node().port.onmessage({ data: { type: "stopped", frames: 256 } });
  assert.equal(recorder.state, "stopped");
  assert.equal(recorder.blob.size, 44 + 256 * 2);
  assert.equal(env.stops(), 1);
  assert.equal(env.closes(), 1);
  recorder.cancel();
  assert.equal(recorder.blob, null);
});

test("device disconnection releases resources and preserves already delivered PCM", async () => {
  const env = runtime(),
    recorder = new env.Recorder();
  let error;
  recorder.onerror = (e) => {
    error = e.message;
  };
  await recorder.prepare();
  recorder.start(10);
  env
    .node()
    .port.onmessage({
      data: { type: "chunk", samples: new Float32Array(128).fill(0.25) },
    });
  env.track.onended();
  assert.equal(recorder.state, "error");
  assert.equal(error, "RecordingDeviceLost");
  assert.equal(recorder.blob.size, 44 + 128 * 2);
  assert.equal(env.stops(), 1);
});

test("permission denial does not create a take or leave an input running", async () => {
  const env = runtime({
    getUserMedia: async () => {
      throw Object.assign(new Error("denied"), { name: "NotAllowedError" });
    },
  });
  const recorder = new env.Recorder();
  assert.equal(await recorder.prepare(), false);
  assert.equal(recorder.state, "error");
  assert.equal(recorder.blob, null);
  assert.equal(env.stops(), 0);
});
