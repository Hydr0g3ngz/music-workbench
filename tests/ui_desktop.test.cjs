const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const source = fs.readFileSync("src/music_studio/ui/static/station.js", "utf8");
const start = source.indexOf("  window.WorkbenchDesktop = {");
const end = source.indexOf("  engine.onerror", start);

test("desktop close waits for save and does not dismiss a failed save", async () => {
  let finish;
  const context = {window:{}, recordingPanel:{busy:()=>false,hasUnsavedTake:()=>false},
    flush:()=>new Promise(resolve=>finish=resolve),tr:x=>x};
  vm.runInNewContext(source.slice(start,end),context);
  let closed=false;
  const close=context.window.WorkbenchDesktop.prepareClose().then(()=>closed=true);
  await Promise.resolve();
  assert.equal(closed,false);
  finish();await close;assert.equal(closed,true);
  context.flush=async()=>{throw Error("network unavailable");};
  await assert.rejects(context.window.WorkbenchDesktop.prepareClose(),/network unavailable/);
});

test("desktop close protects both an active recording and an unadopted take", async () => {
  let saves=0,active=false,take=true;
  const context={window:{},recordingPanel:{busy:()=>active,hasUnsavedTake:()=>take},
    flush:async()=>saves++,tr:x=>x};
  vm.runInNewContext(source.slice(start,end),context);
  await assert.rejects(context.window.WorkbenchDesktop.prepareClose());
  take=false;active=true;
  await assert.rejects(context.window.WorkbenchDesktop.prepareClose());
  assert.equal(saves,0);
  active=false;
  await context.window.WorkbenchDesktop.prepareClose();
  assert.equal(saves,1);
});
