const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("src/music_studio/ui/static/model-setup.js", "utf8");
const settle = () => new Promise((resolve) => setImmediate(resolve));

function node() {
  const fields = new Map(), handlers = {};
  return {
    children: [], handlers, textContent: "", hidden: false,
    addEventListener(type, handler) { handlers[type] = handler; },
    appendChild(child) { this.children.push(child); },
    scrollIntoView() {},
    querySelector(key) {
      if (!fields.has(key)) fields.set(key, node());
      return fields.get(key);
    },
  };
}
function app() {
  const ids = new Map();
  const get = (id) => { if (!ids.has(id)) ids.set(id, node()); return ids.get(id); };
  let poll, failure = false, calls = 0;
  let row = {
    id: "music-tools", title: ["音乐工具", "Music tools"], description: ["说明", "Description"],
    state: "ready", installed: true, checked: true, preflight: { supported: true, reasons: [], directory: "tools" },
    download_estimate: "1–2 GB", required_free_bytes: 6 * 1024 ** 3,
    backend: "Demucs", license: "MIT", source: "https://github.com/facebookresearch/demucs",
    entry: "/station.html?tools=music-tools", capabilities: [],
  };
  vm.runInNewContext(source, {
    document: { getElementById: get, createElement: node },
    localStorage: { getItem: () => "en" }, location: { hash: "" },
    addEventListener() {}, clearInterval() {},
    setInterval(fn) { poll = fn; return 1; },
    fetch: async (url, options) => {
      calls++;
      return { ok: !failure, json: async () => failure ? { detail: "Download interrupted" } : options.method === "POST" ? row : [row] };
    },
  });
  return {
    get, poll: () => poll(), calls: () => calls,
    row: (value) => { row = { ...row, ...value }; }, fail: (value) => { failure = value; },
    click: async (operation) => {
      const card = get("tool-pack-list").children[0];
      await card.handlers.click({ target: { closest: () => ({ dataset: { action: operation } }) } });
      await settle();
    },
  };
}

test("polling preserves tool cards, expanded details and controls", async () => {
  const a = app();
  await settle();
  const card = a.get("tool-pack-list").children[0];
  card.querySelector("details").open = true;
  for (let i = 0; i < 4; i++) await a.poll();
  assert.equal(a.get("tool-pack-list").children.length, 1);
  assert.equal(a.get("tool-pack-list").children[0], card);
  assert.equal(card.querySelector("details").open, true);
  assert.equal(card.querySelector('[data-action="use"]').hidden, false);
});

test("failed checks remove availability and show the actual diagnostic", async () => {
  const a = app();
  await settle();
  a.row({ installed: false, checked: false, capabilities: [{ title: ["旋律", "Melody"], runnable: false, health: { state: "missing", error: "Tool checkpoint changed" } }] });
  await a.click("check");
  const card = a.get("tool-pack-list").children[0];
  assert.equal(card.querySelector('[data-action="use"]').hidden, true);
  assert.match(card.querySelector('[data-field="error"]').textContent, /checkpoint changed/);
});

test("action failures survive polling and allow retry", async () => {
  const a = app();
  await settle();
  a.fail(true);
  await a.click("start");
  a.fail(false);
  await a.poll();
  const card = a.get("tool-pack-list").children[0];
  assert.match(card.querySelector('[data-field="error"]').textContent, /Download interrupted/);
  assert.equal(card.querySelector('[data-action="start"]').disabled, false);
});
