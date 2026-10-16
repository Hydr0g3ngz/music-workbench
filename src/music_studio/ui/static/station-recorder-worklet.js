/* Capture mono PCM on the audio thread. No microphone audio reaches the speakers. */
class CaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(4096);
    this.used = 0;
    this.frames = 0;
    this.recording = false;
    this.meterFrames = 0;
    this.peak = 0;
    this.port.onmessage = ({ data }) => {
      if (data.type === "start") {
        this.frames = this.used = 0;
        this.limit = Math.max(1, Math.floor(data.seconds * sampleRate));
        this.recording = true;
      } else if (data.type === "stop") this.finish();
    };
  }
  flush() {
    if (!this.used) return;
    const chunk = this.buffer.slice(0, this.used);
    this.port.postMessage({ type: "chunk", samples: chunk }, [chunk.buffer]);
    this.used = 0;
  }
  finish() {
    if (!this.recording) return;
    this.recording = false;
    this.flush();
    this.port.postMessage({ type: "stopped", frames: this.frames });
  }
  process(inputs) {
    const channels = inputs[0];
    if (!channels?.length) return true;
    for (let i = 0; i < channels[0].length; i++) {
      let value = 0;
      for (const channel of channels) value += channel[i] / channels.length;
      this.peak = Math.max(this.peak, Math.abs(value));
      if (this.recording) {
        this.buffer[this.used++] = value;
        this.frames++;
        if (this.used === this.buffer.length) this.flush();
        if (this.frames >= this.limit) this.finish();
      }
    }
    this.meterFrames += channels[0].length;
    if (this.meterFrames >= sampleRate / 15) {
      this.port.postMessage({
        type: "meter",
        peak: this.peak,
        frames: this.frames,
      });
      this.peak = this.meterFrames = 0;
    }
    return true;
  }
}
registerProcessor("workbench-capture", CaptureProcessor);
