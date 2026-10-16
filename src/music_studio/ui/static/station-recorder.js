"use strict";
(() => {
  function wav(chunks, rate) {
    const frames = chunks.reduce((n, c) => n + c.length, 0),
      buffer = new ArrayBuffer(44 + frames * 2),
      view = new DataView(buffer);
    function text(offset, value) {
      for (let i = 0; i < value.length; i++)
        view.setUint8(offset + i, value.charCodeAt(i));
    }
    text(0, "RIFF");
    view.setUint32(4, 36 + frames * 2, true);
    text(8, "WAVEfmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, rate, true);
    view.setUint32(28, rate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    text(36, "data");
    view.setUint32(40, frames * 2, true);
    let offset = 44;
    for (const chunk of chunks)
      for (const raw of chunk) {
        const value = Math.max(-1, Math.min(1, Number.isFinite(raw) ? raw : 0));
        view.setInt16(
          offset,
          Math.round(value * (value < 0 ? 32768 : 32767)),
          true,
        );
        offset += 2;
      }
    return new Blob([buffer], { type: "audio/wav" });
  }

  class Recorder {
    constructor() {
      this.state = "idle";
      this.serial = 0;
      this.chunks = [];
      this.frames = 0;
    }
    change(state) {
      this.state = state;
      this.onstate?.(state);
    }
    async prepare(deviceId = "") {
      this.cancel();
      const serial = this.serial;
      this.change("requesting");
      try {
        if (
          !navigator.mediaDevices?.getUserMedia ||
          !globalThis.AudioWorkletNode
        )
          throw new Error("RecordingUnsupported");
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
            channelCount: 1,
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
          },
        });
        if (serial !== this.serial) {
          stream.getTracks().forEach((track) => track.stop());
          return false;
        }
        this.stream = stream;
        for (const track of stream.getAudioTracks())
          track.onended = () => this.fail(new Error("RecordingDeviceLost"));
        const ctx = new AudioContext();
        this.ctx = ctx;
        await ctx.resume();
        await ctx.audioWorklet.addModule("/station-recorder-worklet.js");
        if (serial !== this.serial) return false;
        this.rate = ctx.sampleRate;
        this.source = ctx.createMediaStreamSource(stream);
        this.node = new AudioWorkletNode(ctx, "workbench-capture");
        this.node.onprocessorerror = () =>
          this.fail(new Error("RecordingProcessorFailed"));
        this.node.port.onmessage = ({ data }) => {
          if (serial !== this.serial) return;
          if (data.type === "chunk") {
            this.chunks.push(data.samples);
            this.frames += data.samples.length;
          } else if (data.type === "meter") {
            this.onmeter?.(data.peak, data.frames / this.rate);
          } else if (data.type === "stopped") {
            if (this.state !== "recording" && this.state !== "stopping") return;
            clearTimeout(this.stopTimer);
            this.blob = wav(this.chunks, this.rate);
            this.chunks = [];
            this.release();
            this.change("stopped");
          }
        };
        // The processor leaves its output silent; connecting it keeps capture running.
        this.source.connect(this.node);
        this.node.connect(ctx.destination);
        this.change("ready");
        return true;
      } catch (error) {
        if (serial === this.serial) this.fail(error);
        return false;
      }
    }
    start(seconds) {
      if (
        this.state !== "ready" ||
        !Number.isFinite(seconds) ||
        seconds <= 0 ||
        seconds > 600
      )
        throw new Error("RecordingNotReady");
      this.frames = 0;
      this.chunks = [];
      this.blob = null;
      this.node.port.postMessage({ type: "start", seconds });
      this.change("recording");
    }
    stop() {
      if (this.state !== "recording") return;
      this.change("stopping");
      this.node.port.postMessage({ type: "stop" });
      this.stopTimer = setTimeout(
        () => this.fail(new Error("RecordingStopFailed")),
        3000,
      );
    }
    release() {
      clearTimeout(this.stopTimer);
      this.node?.disconnect();
      this.source?.disconnect();
      this.stream?.getTracks().forEach((track) => {
        track.onended = null;
        track.stop();
      });
      this.ctx?.close().catch(() => {});
      this.node = this.source = this.stream = this.ctx = null;
    }
    fail(error) {
      // Keep already delivered PCM recoverable when a device is disconnected.
      this.blob = this.frames ? wav(this.chunks, this.rate) : null;
      this.chunks = [];
      this.serial++;
      this.release();
      this.change("error");
      this.onerror?.(error);
    }
    cancel() {
      this.serial++;
      this.release();
      this.chunks = [];
      this.frames = 0;
      this.blob = null;
      this.change("idle");
    }
  }
  globalThis.StationRecording = { Recorder, wav };
})();
