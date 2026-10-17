/* Two preloaded immutable sources. A/B switching never rebinds either source. */
(function (root) {
  "use strict";
  class MatchedABPlayer {
    constructor(a, b, metadata, onChange = () => {}) {
      this.media = { a, b };
      this.metadata = metadata;
      this.side = "b";
      this.matching = metadata.matching_available;
      this.volume = 0.7;
      this.onChange = onChange;
      this.switchToken = 0;
      this.disposed = false;
      this.desiredPlaying = false;
      for (const [side, audio] of Object.entries(this.media)) {
        audio.preload = "auto";
        audio.addEventListener("timeupdate", () => {
          if (this.side === side) this.onChange(this);
        });
        audio.addEventListener("play", () => this.onChange(this));
        audio.addEventListener("pause", () => this.onChange(this));
        audio.addEventListener("ended", () => {
          if (this.side === side) this.desiredPlaying = false;
          this.onChange(this);
        });
        audio.src = metadata[side].url;
        audio.load();
      }
      this.updateVolumes();
    }
    get current() {
      return this.media[this.side];
    }
    get duration() {
      return this.metadata.duration;
    }
    pause() {
      this.desiredPlaying = false;
      for (const media of Object.values(this.media)) media.pause();
    }
    async play() {
      if (this.disposed) return;
      if (this.current.currentTime >= this.duration - 0.02) this.seek(0);
      this.desiredPlaying = true;
      const media = this.current;
      try {
        await media.play();
      } catch (error) {
        if (!this.disposed && media === this.current) {
          this.desiredPlaying = false;
          this.onChange(this);
        }
        if (
          error.name !== "AbortError" ||
          (!this.disposed && this.desiredPlaying && media === this.current)
        )
          throw error;
      }
      if (this.disposed || !this.desiredPlaying || media !== this.current)
        media.pause();
    }
    seek(time) {
      const value = Math.max(
        0,
        Math.min(time, Math.max(0, this.duration - 0.00001)),
      );
      for (const media of Object.values(this.media)) media.currentTime = value;
      this.onChange(this);
    }
    async select(side) {
      if (this.disposed || side === this.side) return;
      if (!Object.hasOwn(this.media, side)) throw new Error("Unknown A/B side");
      const token = ++this.switchToken;
      const playing = this.desiredPlaying || !this.current.paused;
      const time = this.current.currentTime;
      this.pause();
      this.side = side;
      this.seek(time);
      this.updateVolumes();
      if (playing) {
        await this.play();
        if (this.disposed || (token !== this.switchToken && side !== this.side))
          this.media[side].pause();
      }
      this.onChange(this);
    }
    setMatching(value) {
      this.matching = Boolean(value) && this.metadata.matching_available;
      this.updateVolumes();
      this.onChange(this);
    }
    setVolume(value) {
      this.volume = Math.max(0, Math.min(1, value));
      this.updateVolumes();
    }
    updateVolumes() {
      for (const [side, audio] of Object.entries(this.media)) {
        audio.volume =
          this.volume * (this.matching ? this.metadata[side].matched_gain : 1);
      }
    }
    dispose() {
      this.disposed = true;
      ++this.switchToken;
      this.pause();
      for (const media of Object.values(this.media)) {
        media.removeAttribute("src");
        media.load();
      }
    }
  }
  if (typeof module !== "undefined" && module.exports)
    module.exports = { MatchedABPlayer };
  else root.MatchedABPlayer = MatchedABPlayer;
})(typeof window !== "undefined" ? window : globalThis);
