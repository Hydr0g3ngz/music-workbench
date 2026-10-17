const test = require("node:test");
const assert = require("node:assert/strict");
const {
  MatchedABPlayer,
} = require("../src/music_studio/ui/static/comparison.js");
function media() {
  return {
    src: "",
    currentTime: 0,
    paused: true,
    loads: 0,
    volume: 1,
    addEventListener() {},
    load() {
      this.loads++;
      this.currentTime = 0;
    },
    pause() {
      this.paused = true;
    },
    async play() {
      this.paused = false;
    },
    removeAttribute() {
      this.src = "";
    },
  };
}
function setup() {
  const a = media(),
    b = media();
  return {
    a,
    b,
    player: new MatchedABPlayer(a, b, {
      duration: 30,
      matching_available: true,
      a: { url: "/immutable/a", matched_gain: 0.5 },
      b: { url: "/immutable/b", matched_gain: 1 },
    }),
  };
}
test("A/B preserves running position, pauses the other side and loads each source only once", async () => {
  const { a, b, player } = setup();
  await player.play();
  b.currentTime = 7.25;
  await player.select("a");
  assert.equal(a.currentTime, 7.25);
  assert.equal(a.paused, false);
  assert.equal(b.paused, true);
  a.currentTime = 11.75;
  await player.select("b");
  assert.equal(b.currentTime, 11.75);
  assert.equal(b.paused, false);
  assert.equal(a.paused, true);
  assert.equal(a.loads, 1);
  assert.equal(b.loads, 1);
});
test("loudness matching uses attenuation and changes neither time nor paused state", () => {
  const { a, b, player } = setup();
  assert.equal(a.volume, 0.35);
  assert.equal(b.volume, 0.7);
  b.currentTime = 12;
  player.setMatching(false);
  player.setVolume(0.4);
  assert.equal(a.volume, 0.4);
  assert.equal(b.volume, 0.4);
  assert.equal(b.currentTime, 12);
  assert.equal(b.paused, true);
  player.setMatching(true);
  assert.equal(a.volume, 0.2);
  assert.equal(b.volume, 0.4);
});
test("closing releases both sources and a late playback promise cannot continue", async () => {
  const { a, b, player } = setup();
  await player.play();
  let resolvePlay;
  b.pause();
  a.play = () =>
    new Promise((resolve) => {
      resolvePlay = () => {
        a.paused = false;
        resolve();
      };
    });
  b.paused = false;
  const switching = player.select("a");
  player.dispose();
  resolvePlay();
  await switching;
  assert.equal(a.paused, true);
  assert.equal(b.paused, true);
  assert.equal(a.src, "");
  assert.equal(b.src, "");
});

test("switching at the end permits replay and failed playback clears the playing state", async () => {
  const { a, b, player } = setup();
  b.currentTime = 30;
  await player.select("a");
  await player.play();
  assert.equal(a.currentTime, 0);
  assert.equal(player.desiredPlaying, true);
  player.pause();
  a.play = async () => {
    throw new Error("decode failed");
  };
  await assert.rejects(() => player.play(), /decode failed/);
  assert.equal(player.desiredPlaying, false);
});
