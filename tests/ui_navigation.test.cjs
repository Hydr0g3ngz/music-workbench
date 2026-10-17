const test = require("node:test");
const assert = require("node:assert/strict");
const navigation = require("../src/music_studio/ui/static/workbench-navigation.js");

test("asset details keep a distinct source identity and a return path to the arrangement", () => {
  const source = "1234567890abcdef", session = "fedcba0987654321";
  const url = new URL(navigation.editor(source, session), "http://127.0.0.1");
  assert.equal(url.pathname, "/next.html");
  assert.equal(url.searchParams.get("project"), source);
  assert.equal(url.searchParams.get("session"), session);
  assert.equal(navigation.workstation(url.searchParams.get("session")), "/station.html?session=" + session);
  assert.equal(navigation.editor(null, session), "/next.html?session=" + session);
  assert.equal(navigation.editor(source), "/next.html?project=" + source);
});

test("return navigation stays local and does not interpret an asset as an arrangement", () => {
  for (const value of [null, undefined, "", "//external.test", "https://external.test", "../../other", "abcd<script>", 123]) {
    assert.equal(navigation.workstation(value), "/welcome.html");
    assert.equal(navigation.editor(value, value), "/next.html");
  }
});
