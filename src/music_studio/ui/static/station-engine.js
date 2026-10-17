(function (root) {
  "use strict";
  const Effects =
    typeof module !== "undefined" && module.exports
      ? require("./effects-dsp.js")
      : root.StationEffects;
  const Timing =
    typeof module !== "undefined" && module.exports
      ? require("./station-timing.js")
      : root.StationTiming;
  const Envelope =
    typeof module !== "undefined" && module.exports
      ? require("./station-envelope.js")
      : root.StationEnvelope;
  const Routing =
    typeof module !== "undefined" && module.exports
      ? require("./station-routing.js")
      : root.StationRouting;
  const uid = () =>
    typeof crypto !== "undefined"
      ? crypto.randomUUID().replaceAll("-", "").slice(0, 16)
      : Math.random().toString(16).slice(2).padEnd(16, "0");
  const duration = (content) =>
    Math.max(
      0,
      ...content.tracks.flatMap((t) =>
        t.clips.map(
          (c) =>
            c.start +
            c.duration +
            (audible(t, content.tracks) ? Routing.tail(t, content.buses) : 0),
        ),
      ),
    );
  const gain = (db) => 10 ** (db / 20);
  function audible(track, tracks) {
    return !track.mute && (!tracks.some((t) => t.solo) || track.solo);
  }
  function splitClip(clip, at) {
    const first = at - clip.start;
    if (first < 0.01 || clip.duration - first < 0.01) return null;
    const left = structuredClone(clip),
      right = structuredClone(clip);
    left.duration = first;
    left.fade_out = 0;
    left.fade_in = Math.min(left.fade_in, first);
    right.id = uid();
    right.start = at;
    right.offset += first;
    right.duration -= first;
    right.fade_in = 0;
    right.fade_out = Math.min(right.fade_out, right.duration);
    if ((clip.volume_points || []).length) {
      left.volume_points = Envelope.crop(clip, 0, first);
      right.volume_points = Envelope.crop(clip, first, right.duration);
    }
    return [left, right];
  }
  function midiBuffer(ctx, clip, bpm, instrument) {
    const rate = ctx.sampleRate,
      seconds = clip.offset + clip.duration;
    const buffer = ctx.createBuffer(2, Math.ceil(seconds * rate), rate);
    const data = buffer.getChannelData(0),
      beat = 60 / bpm;
    for (const note of clip.notes) {
      const start = Math.round(note.start * beat * rate),
        end = Math.min(
          data.length,
          Math.ceil((note.start + note.length) * beat * rate),
        );
      const frequency = 440 * 2 ** ((note.pitch - 69) / 12),
        length = note.length * beat;
      for (let i = start; i < end; i++) {
        const x = i / rate - note.start * beat;
        if (x < 0 || x >= length) continue;
        const phase = 2 * Math.PI * frequency * x;
        const tone =
          instrument === "bass"
            ? Math.sin(phase) * 0.85 + Math.sin(phase * 2) * 0.15
            : (Math.sin(phase) +
                0.25 * Math.sin(phase * 2) +
                0.12 * Math.sin(phase * 3)) /
              1.37;
        const attack = instrument === "pad" ? 0.08 : 0.008;
        let envelope =
          Math.min(x / attack, 1) * Math.min((length - x) / 0.04, 1);
        if (instrument === "keys") envelope *= Math.exp(-x * 2);
        data[i] += ((tone * 0.2 * note.velocity) / 127) * envelope;
      }
    }
    buffer.copyToChannel(data, 1);
    return buffer;
  }
  function sampleChoice(library, instrument, pitch) {
    const entries = library.samples.filter((s) => s.instrument === instrument);
    if (instrument === "vcsl-drums")
      return (
        entries.find((s) => s.keys.includes(pitch)) ||
        entries.find((s) => s.id === "closed-hat")
      );
    return entries.sort(
      (a, b) =>
        Math.abs(a.root - pitch) - Math.abs(b.root - pitch) || a.root - b.root,
    )[0];
  }
  function sampledBuffer(ctx, clip, bpm, instrument, library, samples) {
    const rate = ctx.sampleRate,
      length = Math.ceil((clip.offset + clip.duration) * rate),
      output = ctx.createBuffer(2, length, rate),
      beat = 60 / bpm;
    const hats = [
        ...new Set(
          clip.notes
            .filter((n) => [22, 26, 42, 44, 46].includes(n.pitch))
            .map((n) => n.start),
        ),
      ].sort((a, b) => a - b),
      nextHat = new Map(
        hats.slice(0, -1).map((start, index) => [start, hats[index + 1]]),
      );
    for (const note of clip.notes) {
      const entry = sampleChoice(library, instrument, note.pitch);
      if (!entry) throw Error(`No drum sample mapped to MIDI ${note.pitch}`);
      const sample = samples.get(entry.id),
        sourceRate = sample.sampleRate || rate,
        ratio =
          instrument === "vcsl-drums"
            ? 1
            : 2 ** ((note.pitch - entry.root) / 12),
        source = [sample.getChannelData(0), sample.getChannelData(1)];
      let gate =
        instrument === "vcsl-drums" ? entry.frames / 44100 : note.length * beat;
      if (
        instrument === "vcsl-drums" &&
        [22, 26, 42, 44, 46].includes(note.pitch)
      ) {
        if (nextHat.has(note.start))
          gate = Math.min(gate, (nextHat.get(note.start) - note.start) * beat);
      }
      const start = Math.round(note.start * beat * rate),
        end = Math.min(length, Math.ceil((note.start * beat + gate) * rate));
      for (let i = start; i < end; i++) {
        const x = i / rate - note.start * beat,
          position = x * ratio * sourceRate;
        if (x < 0 || x >= gate || position >= source[0].length - 1) continue;
        const low = Math.floor(position),
          blend = position - low,
          envelope =
            instrument === "vcsl-drums"
              ? 1
              : Math.max(
                  0,
                  Math.min(x / 0.003, 1) * Math.min((gate - x) / 0.04, 1),
                ),
          level = (note.velocity / 127) * 0.55 * envelope;
        for (let channel = 0; channel < 2; channel++)
          output.getChannelData(channel)[i] +=
            (source[channel][low] * (1 - blend) +
              source[channel][low + 1] * blend) *
            level;
      }
    }
    return output;
  }
  class StationEngine {
    constructor(makeContext = () => new AudioContext({ sampleRate: 44100 })) {
      this.makeContext = makeContext;
      this.ctx = null;
      this.cache = new Map();
      this.sampleCache = new Map();
      this.library = null;
      this.nodes = [];
      this.graphs = new Map();
      this.playing = false;
      this.position = 0;
      this.epoch = 0;
    }
    context() {
      if (!this.ctx) {
        this.ctx = this.makeContext();
        this.master = this.ctx.createGain();
        this.masterAnalyser = this.ctx.createAnalyser();
        this.masterAnalyser.fftSize = 256;
        this.masterData = new Float32Array(256);
        this.master.connect(this.masterAnalyser);
        this.masterAnalyser.connect(this.ctx.destination);
      }
      return this.ctx;
    }
    current() {
      if (!this.playing) return this.position;
      const raw =
        this.position + Math.max(0, this.ctx.currentTime - this.started);
      if (this.playRange?.loop && raw >= this.playRange.end)
        return (
          this.playRange.start +
          ((raw - this.playRange.end) %
            (this.playRange.end - this.playRange.start))
        );
      return raw;
    }
    pause() {
      this.position = this.current();
      this.playing = false;
      this.epoch++;
      clearInterval(this.timingTimer);
      this.timingTimer = null;
      this.clickGain?.disconnect();
      this.clickGain = null;
      this.playRange = null;
      this.playContent = null;
      this.playBuffers = null;
      for (const node of this.nodes) {
        try {
          node.stop();
        } catch (_) {}
        node.disconnect();
      }
      for (const graph of this.graphs.values())
        for (const node of graph.nodes) {
          if (node.port) node.port.postMessage({ dispose: true });
          node.disconnect();
        }
      if (this.masterEffect) {
        this.masterEffect.port.postMessage({ dispose: true });
        this.master.disconnect();
        this.masterEffect.disconnect();
        this.masterEffect = null;
        this.master.connect(this.masterAnalyser);
      }
      this.nodes = [];
      this.clickNodes = [];
      this.graphs.clear();
    }
    reset() {
      this.pause();
      this.position = 0;
      this.cache.clear();
    }
    async buffer(key, url) {
      if (!this.cache.has(key)) {
        this.cache.set(
          key,
          fetch(url)
            .then((r) => {
              if (!r.ok) throw Error(`Audio HTTP ${r.status}`);
              return r.arrayBuffer();
            })
            .then((b) => this.context().decodeAudioData(b))
            .catch((e) => {
              this.cache.delete(key);
              throw e;
            }),
        );
      }
      return this.cache.get(key);
    }
    setLibrary(library) {
      this.library = library;
    }
    async samples(instrument, notes) {
      if (!instrument.startsWith("vcsl-")) return new Map();
      if (!this.library) throw Error("Factory sound library is not loaded");
      const entries = new Map();
      for (const note of notes) {
        const entry = sampleChoice(this.library, instrument, note.pitch);
        if (!entry) throw Error(`No drum sample mapped to MIDI ${note.pitch}`);
        entries.set(entry.id, entry);
      }
      return new Map(
        await Promise.all(
          [...entries.values()].map(async (entry) => {
            const key = entry.sha256;
            if (!this.sampleCache.has(key))
              this.sampleCache.set(
                key,
                fetch(entry.url + `?v=${key}`)
                  .then((r) => {
                    if (!r.ok) throw Error(`Sample HTTP ${r.status}`);
                    return r.arrayBuffer();
                  })
                  .then((b) => this.context().decodeAudioData(b))
                  .catch((e) => {
                    this.sampleCache.delete(key);
                    throw e;
                  }),
              );
            return [entry.id, await this.sampleCache.get(key)];
          }),
        ),
      );
    }
    async renderMidi(clip, bpm, instrument) {
      return instrument.startsWith("vcsl-")
        ? sampledBuffer(
            this.context(),
            clip,
            bpm,
            instrument,
            this.library,
            await this.samples(instrument, clip.notes),
          )
        : midiBuffer(this.context(), clip, bpm, instrument);
    }
    async prepareEffects(content) {
      const ctx = this.context();
      if (!ctx.audioWorklet) {
        if (
          content.limiter?.enabled ||
          [...content.tracks, ...(content.buses || [])].some((t) => {
            const s = Effects.normalize(t.effects);
            return (
              !s.bypass &&
              (s.eq.enabled || s.compressor.enabled || s.reverb.enabled)
            );
          })
        )
          throw Error(
            "AudioWorklet is required for effects. Open in a current browser on localhost.",
          );
        return;
      }
      if (!this.workletPromise) {
        this.workletPromise = ctx.audioWorklet
          .addModule("/station-worklet.js")
          .catch((e) => {
            this.workletPromise = null;
            throw e;
          });
      }
      await this.workletPromise;
      this.workletsReady = true;
    }
    effectNode(settings, master = false) {
      const node = new AudioWorkletNode(this.context(), "studio-effects", {
        numberOfInputs: 1,
        numberOfOutputs: 1,
        outputChannelCount: [2],
        channelCount: 2,
        channelCountMode: "explicit",
        processorOptions: { settings, master },
      });
      node.reduction = 0;
      node.port.onmessage = (e) => {
        node.reduction = e.data.reduction;
        node.peak = e.data.peak;
      };
      node.onprocessorerror = () => {
        this.pause();
        this.onerror?.(
          Error("Audio effects processor failed. Pause and retry playback."),
        );
      };
      node.settingsKey = JSON.stringify(settings);
      return node;
    }
    configureEffect(node, settings) {
      if (!node) return;
      const key = JSON.stringify(settings);
      if (node.settingsKey !== key) {
        node.port.postMessage(settings);
        node.settingsKey = key;
      }
    }
    graph(track) {
      const ctx = this.context(),
        input = ctx.createGain(),
        splitter = ctx.createChannelSplitter(2);
      const left = ctx.createGain(),
        right = ctx.createGain(),
        merge = ctx.createChannelMerger(2);
      const level = ctx.createGain(),
        effect = this.workletsReady
          ? this.effectNode(Effects.normalize(track.effects))
          : null;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      if (effect) {
        input.connect(effect);
        effect.connect(level);
      } else input.connect(level);
      level.connect(splitter);
      splitter.connect(left, 0);
      splitter.connect(right, 1);
      left.connect(merge, 0, 0);
      right.connect(merge, 0, 1);
      merge.connect(analyser);
      analyser.connect(this.master);
      const graph = {
        input,
        level,
        effect,
        left,
        right,
        analyser,
        data: new Float32Array(256),
        nodes: [
          input,
          level,
          ...(effect ? [effect] : []),
          splitter,
          left,
          right,
          merge,
          analyser,
        ],
      };
      this.graphs.set(track.id, graph);
      return graph;
    }
    update(content) {
      if (!this.ctx) return;
      const metronome = { ...Timing.metronomeDefaults(), ...content.metronome };
      if (
        this.metronome?.enabled !== metronome.enabled ||
        this.metronome?.accent !== metronome.accent
      ) {
        for (const node of this.clickNodes || []) {
          try {
            node.stop();
          } catch (_) {}
          node.disconnect();
        }
        const clicks = new Set(this.clickNodes || []);
        this.nodes = this.nodes.filter((node) => !clicks.has(node));
        this.clickNodes = [];
        this.lastClick = -Infinity;
      }
      this.metronome = metronome;
      if (this.playing && this.metronome.enabled && !this.clickGain) {
        this.clickGain = this.ctx.createGain();
        this.clickGain.connect(this.ctx.destination);
      }
      this.clickGain?.gain.setTargetAtTime(
        this.metronome.enabled ? gain(this.metronome.volume_db) : 0,
        this.ctx.currentTime,
        0.005,
      );
      this.master.gain.setTargetAtTime(
        gain(content.master_db),
        this.ctx.currentTime,
        0.015,
      );
      this.configureEffect(this.masterEffect, {
        ...Effects.limiterDefaults(),
        ...content.limiter,
      });
      for (const t of [...content.tracks, ...(content.buses || [])]) {
        const g = this.graphs.get(t.id);
        if (!g) continue;
        this.configureEffect(g.effect, Effects.normalize(t.effects));
        g.level.gain.setTargetAtTime(
          (
            content.tracks.includes(t)
              ? audible(t, content.tracks)
              : Routing.busAudible(t, content.buses || [])
          )
            ? gain(t.gain_db)
            : 0,
          this.ctx.currentTime,
          0.015,
        );
        g.left.gain.setTargetAtTime(
          t.pan > 0 ? Math.cos((t.pan * Math.PI) / 2) : 1,
          this.ctx.currentTime,
          0.015,
        );
        g.right.gain.setTargetAtTime(
          t.pan < 0 ? Math.cos((-t.pan * Math.PI) / 2) : 1,
          this.ctx.currentTime,
          0.015,
        );
        if (g.direct)
          g.direct.gain.setTargetAtTime(
            !t.output && (content.buses || []).some((b) => b.solo) ? 0 : 1,
            this.ctx.currentTime,
            0.015,
          );
        for (const send of t.sends || []) {
          g.sends
            ?.get(send.bus)
            ?.gain.setTargetAtTime(
              send.enabled ? gain(send.gain_db) : 0,
              this.ctx.currentTime,
              0.015,
            );
        }
      }
    }
    async play(content, assets, project, at = this.position) {
      this.pause();
      const epoch = this.epoch,
        ctx = this.context();
      await ctx.resume();
      await this.prepareEffects(content);
      if (epoch !== this.epoch) return false;
      const needed = new Set(
        content.tracks.flatMap((t) =>
          t.clips.filter((c) => c.asset).map((c) => c.asset),
        ),
      );
      const keep = new Set([...needed].map((id) => project + ":" + id));
      for (const track of content.tracks)
        if (track.kind === "midi")
          for (const clip of track.clips)
            keep.add(
              JSON.stringify([
                content.bpm,
                track.instrument,
                clip.offset,
                clip.duration,
                clip.notes,
              ]),
            );
      for (const key of this.cache.keys())
        if (!keep.has(key)) this.cache.delete(key);
      const bytes =
        [...needed].reduce(
          (sum, id) =>
            sum + (assets.find((a) => a.id === id)?.duration || 0) * 44100 * 8,
          0,
        ) +
        content.tracks
          .flatMap((t) => (t.kind === "midi" ? t.clips : []))
          .reduce((s, c) => s + (c.offset + c.duration) * 44100 * 8, 0);
      if (bytes > 256 * 1024 * 1024)
        throw Error(
          "Preview memory limit (256 MiB). Use a shorter arrangement.",
        );
      const buffers = new Map();
      await Promise.all(
        [...needed].map(async (id) =>
          buffers.set(
            id,
            await this.buffer(
              project + ":" + id,
              `/api/workstation/projects/${project}/audio/${id}`,
            ),
          ),
        ),
      );
      if (epoch !== this.epoch) return false;
      for (const track of content.tracks)
        if (track.kind === "midi")
          for (const clip of track.clips) {
            const key = JSON.stringify([
              content.bpm,
              track.instrument,
              clip.offset,
              clip.duration,
              clip.notes,
            ]);
            if (!this.cache.has(key))
              this.cache.set(
                key,
                this.renderMidi(clip, content.bpm, track.instrument).catch(
                  (e) => {
                    this.cache.delete(key);
                    throw e;
                  },
                ),
              );
            buffers.set(clip.id, await this.cache.get(key));
          }
      if (epoch !== this.epoch) return false;
      this.playRange = Timing.range(content, duration(content), at);
      at = this.position = this.playRange.at;
      this.started = ctx.currentTime + 0.04;
      if (this.workletsReady) {
        this.masterEffect = this.effectNode(
          { ...Effects.limiterDefaults(), ...content.limiter },
          true,
        );
        this.master.disconnect();
        this.master.connect(this.masterEffect);
        this.masterEffect.connect(this.masterAnalyser);
      }
      this.master.gain.setValueAtTime(gain(content.master_db), ctx.currentTime);
      for (const track of content.tracks) {
        const graph = this.graph(track);
        graph.level.gain.value = audible(track, content.tracks)
          ? gain(track.gain_db)
          : 0;
        graph.left.gain.value =
          track.pan > 0 ? Math.cos((track.pan * Math.PI) / 2) : 1;
        graph.right.gain.value =
          track.pan < 0 ? Math.cos((-track.pan * Math.PI) / 2) : 1;
      }
      for (const bus of content.buses || []) {
        const g = this.graph(bus);
        g.level.gain.value = Routing.busAudible(bus, content.buses)
          ? gain(bus.gain_db)
          : 0;
        g.left.gain.value = bus.pan > 0 ? Math.cos((bus.pan * Math.PI) / 2) : 1;
        g.right.gain.value =
          bus.pan < 0 ? Math.cos((-bus.pan * Math.PI) / 2) : 1;
      }
      for (const track of content.tracks) {
        const g = this.graphs.get(track.id);
        g.analyser.disconnect();
        g.direct = ctx.createGain();
        g.nodes.push(g.direct);
        g.direct.gain.value =
          !track.output && (content.buses || []).some((b) => b.solo) ? 0 : 1;
        g.analyser.connect(g.direct);
        g.direct.connect(
          track.output ? this.graphs.get(track.output).input : this.master,
        );
        g.sends = new Map();
        for (const send of track.sends || []) {
          const level = ctx.createGain();
          level.gain.value = send.enabled ? gain(send.gain_db) : 0;
          g.analyser.connect(level);
          level.connect(this.graphs.get(send.bus).input);
          g.sends.set(send.bus, level);
          g.nodes.push(level);
        }
      }
      this.playContent = structuredClone(content);
      this.playBuffers = buffers;
      this.scheduleWindow(at, this.playRange.end, this.started);
      this.nextCycle = this.started + this.playRange.end - at;
      this.lastClick = -Infinity;
      this.playing = true;
      this.update(content);
      this.scheduleTiming();
      this.timingTimer = setInterval(() => {
        try {
          if (this.playing) this.scheduleTiming();
        } catch (error) {
          this.pause();
          this.onerror?.(error);
        }
      }, 100);
      this.timingTimer.unref?.();
      return true;
    }
    scheduleWindow(from, to, when) {
      const ctx = this.ctx;
      for (const track of this.playContent.tracks) {
        const graph = this.graphs.get(track.id);
        for (const clip of track.clips) {
          const start = Math.max(from, clip.start),
            skip = start - clip.start,
            length = Math.min(clip.start + clip.duration, to) - start;
          if (length <= 0) continue;
          if (this.nodes.length >= 16384)
            throw Error(
              "Too many simultaneous loop sources; use a longer loop or fewer clips.",
            );
          const source = ctx.createBufferSource(),
            level = ctx.createGain();
          source.buffer = this.playBuffers.get(clip.asset || clip.id);
          source.connect(level);
          level.connect(graph.input);
          source.onended = () => {
            source.disconnect();
            level.disconnect();
            this.nodes = this.nodes.filter((n) => n !== source);
          };
          const begins = when + start - from,
            amp = gain(clip.gain_db);
          const points = [
            ...new Set([
              skip,
              skip + length,
              Math.max(skip, clip.fade_in),
              Math.max(skip, clip.duration - clip.fade_out),
            ]),
          ]
            .filter((s) => s >= skip && s <= skip + length)
            .sort((a, b) => a - b);
          const envelope = (s) =>
            Math.max(
              0,
              Math.min(1, clip.fade_in ? s / clip.fade_in : 1) *
                Math.min(
                  1,
                  clip.fade_out ? (clip.duration - s) / clip.fade_out : 1,
                ),
            ) * amp;
          if (
            (clip.volume_points || []).length ||
            clip.fade_curve === "equal_power"
          ) {
            const count = Math.max(2, Math.ceil(length * 400) + 1);
            const curve = Float32Array.from({ length: count }, (_, i) =>
              Envelope.value(clip, skip + (i * length) / (count - 1)),
            );
            level.gain.setValueCurveAtTime(curve, begins, length);
          } else {
            level.gain.setValueAtTime(envelope(skip), begins);
            for (const s of points.slice(1))
              level.gain.linearRampToValueAtTime(
                envelope(s),
                begins + s - skip,
              );
          }
          source.start(begins, clip.offset + skip, length);
          this.nodes.push(source);
        }
      }
    }
    scheduleTiming() {
      const ctx = this.ctx,
        now = ctx.currentTime,
        horizon = now + 1.5,
        r = this.playRange;
      if (r.loop) {
        const length = r.end - r.start;
        if (this.nextCycle + length <= now)
          this.nextCycle +=
            Math.floor((now - this.nextCycle) / length) * length;
        while (this.nextCycle < horizon) {
          const when = Math.max(this.nextCycle, now + 0.005),
            skip = when - this.nextCycle;
          if (skip < length) this.scheduleWindow(r.start + skip, r.end, when);
          this.nextCycle += length;
        }
      }
      if (!this.metronome.enabled || !this.clickGain) return;
      for (const event of Timing.beatEvents(
        {
          ...r,
          at: this.position,
          started: this.started,
          bpm: this.playContent.bpm || 108,
        },
        Math.max(now + 0.005, this.lastClick + 1e-6),
        horizon,
      )) {
        const source = ctx.createBufferSource();
        source.buffer = this.clickBuffer(
          this.metronome.accent && event.beat % 4 === 0,
        );
        source.connect(this.clickGain);
        source.onended = () => {
          source.disconnect();
          this.nodes = this.nodes.filter((n) => n !== source);
          this.clickNodes = this.clickNodes.filter((n) => n !== source);
        };
        source.start(event.time);
        this.nodes.push(source);
        (this.clickNodes ||= []).push(source);
        this.lastClick = event.time;
      }
    }
    clickBuffer(accent) {
      this.clickBuffers ||= new Map();
      if (!this.clickBuffers.has(accent)) {
        const rate = this.ctx.sampleRate,
          size = Math.ceil(0.035 * rate),
          buffer = this.ctx.createBuffer(1, size, rate),
          data = buffer.getChannelData(0);
        for (let i = 0; i < size; i++) {
          const time = i / rate;
          data[i] =
            0.5 *
            Math.sin(2 * Math.PI * (accent ? 1600 : 1000) * time) *
            Math.exp(-time * 150) *
            Math.min(1, time / 0.001);
        }
        this.clickBuffers.set(accent, buffer);
      }
      return this.clickBuffers.get(accent);
    }
    meter(id) {
      const graph = this.graphs.get(id);
      if (!graph || !this.playing) return 0;
      graph.analyser.getFloatTimeDomainData(graph.data);
      return Math.sqrt(
        graph.data.reduce((n, x) => n + x * x, 0) / graph.data.length,
      );
    }
    async note(pitch, instrument = "keys") {
      // Audition uses the same basic synthesis as clips and offline export.
      const ctx = this.context();
      await ctx.resume();
      const source = ctx.createBufferSource();
      source.buffer = await this.renderMidi(
        {
          offset: 0,
          duration: 0.5,
          notes: [{ pitch, start: 0, length: 1, velocity: 85 }],
        },
        120,
        instrument,
      );
      source.connect(this.master);
      source.onended = () => source.disconnect();
      source.start();
    }
    masterMeter() {
      if (!this.masterAnalyser || !this.playing) return 0;
      this.masterAnalyser.getFloatTimeDomainData(this.masterData);
      return Math.sqrt(
        this.masterData.reduce((sum, x) => sum + x * x, 0) /
          this.masterData.length,
      );
    }
  }
  const api = {
    StationEngine,
    uid,
    duration,
    audible,
    splitClip,
    midiBuffer,
    sampledBuffer,
    sampleChoice,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Station = api;
})(typeof window !== "undefined" ? window : globalThis);
