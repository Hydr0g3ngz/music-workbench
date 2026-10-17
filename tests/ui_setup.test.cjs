const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(
  "src/music_studio/ui/static/ai-setup.js",
  "utf8",
);
const settle = () => new Promise((resolve) => setImmediate(resolve));
function app(initial) {
  const nodes = new Map();
  let state = initial,
    loads = 0,
    poll,
    failure = false;
  const audio = {
    getAttribute: () => (loads ? "loaded" : null),
    set src(value) {
      loads++;
    },
  };
  const get = (id) => {
    if (!nodes.has(id))
      nodes.set(id, {
        textContent: "",
        classList: { toggle() {} },
        querySelector: () => audio,
      });
    return nodes.get(id);
  };
  vm.runInNewContext(source, {
    document: { getElementById: get, documentElement: {}, querySelector: get },
    localStorage: { getItem: () => "en", setItem() {} },
    addEventListener() {},
    clearInterval() {},
    setInterval(fn) {
      poll = fn;
      return 1;
    },
    fetch: async (url, options) => {
      if (options.method === "POST" && failure)
        return {
          ok: false,
          json: async () => ({ detail: "Another window is installing" }),
        };
      return {
        ok: true,
        json: async () =>
          url.endsWith("/preflight")
            ? {
                supported: true,
                reasons: [],
                gpus: [],
                free_bytes: 50 * 1024 ** 3,
                directory: "local",
              }
            : state,
      };
    },
  });
  return {
    get,
    loads: () => loads,
    poll: () => poll(),
    state: (x) => (state = x),
    fail: () => (failure = true),
  };
}
test("AI setup polling and language changes never reload verification audio", async () => {
  const a = app({
    state: "ready",
    generation: { available: true },
    preview: true,
  });
  await settle();
  assert.equal(a.loads(), 1);
  for (let i = 0; i < 6; i++) await a.poll();
  a.get("language").onclick();
  assert.equal(a.loads(), 1);
  assert.equal(a.get("create").hidden, false);
});
test("setup errors stay visible after controls redraw and incomplete jobs cannot create", async () => {
  const a = app({
    state: "idle",
    generation: { available: false },
    preview: false,
  });
  await settle();
  assert.equal(a.get("create").hidden, true);
  assert.equal(a.get("install").disabled, false);
  a.fail();
  await a.get("install").onclick();
  assert.match(a.get("reason").textContent, /Another window/);
  assert.equal(a.get("install").disabled, false);
  assert.equal(a.loads(), 0);
});
