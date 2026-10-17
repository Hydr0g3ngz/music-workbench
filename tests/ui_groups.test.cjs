const test = require("node:test");
const assert = require("node:assert/strict");
const G = require("../src/music_studio/ui/static/station-groups.js");
const E = require("../src/music_studio/ui/static/station-edit.js");
let serial=10;
const uid=()=> (++serial).toString(16).padStart(16,"0");
function content(){return {bpm:120,sections:[],tracks:[{id:uid(),clips:[{id:"a",start:1,offset:2,duration:3,fade_in:.1,fade_out:.3,volume_points:[{time:1,gain_db:-6}],notes:[]}]},{id:uid(),clips:[{id:"b",start:2,offset:.5,duration:2,fade_in:0,fade_out:.2,notes:[{pitch:60,start:1,length:2,velocity:72}]}]}]};}
test("group move keeps relative positions, source crops, MIDI coordinates and envelopes",()=>{
  const original=content(), grouped=G.edit(original,["a","b"],"group",0,uid);
  assert.deepEqual(G.expand(grouped,["b"]),["a","b"]);
  const moved=G.edit(grouped,["b"],"move",4,uid);
  assert.equal(moved.tracks[0].clips[0].start,5);assert.equal(moved.tracks[1].clips[0].start,6);
  for(let t=0;t<2;t++){const a=structuredClone(grouped.tracks[t].clips[0]),b=structuredClone(moved.tracks[t].clips[0]);delete a.start;delete b.start;assert.deepEqual(a,b);}
  assert.equal(original.tracks[0].clips[0].group,undefined);
});
test("group copy makes a new independent group and removal never deletes the original",()=>{
  const initial=G.edit(content(),["a","b"],"group",0,uid),copied=G.edit(initial,["a"],"copy",8,uid);
  const a=copied.tracks[0].clips[1],b=copied.tracks[1].clips[1];assert.equal(a.group,b.group);assert.notEqual(a.group,initial.tracks[0].clips[0].group);
  const removed=G.edit(copied,[a.id],"delete",0,uid);assert.deepEqual(removed,initial);
  const ungrouped=G.edit(copied,[a.id],"ungroup",0,uid);assert.equal(ungrouped.tracks[1].clips[1].group,null);
});
test("invalid group move/copy is atomic, including whole-group bounds",()=>{
  const initial=G.edit(content(),["a","b"],"group",0,uid),before=structuredClone(initial);
  for(const delta of [-2,599,NaN])assert.throws(()=>G.edit(initial,["b"],"move",delta,uid));
  assert.deepEqual(initial,before);
});
test("section copies remap shared groups independently from their source",()=>{
  const initial=G.edit(content(),["a","b"],"group",0,uid),next=E.section(initial,0,16,16,uid);
  assert.equal(next.tracks[0].clips[1].group,next.tracks[1].clips[1].group);
  assert.notEqual(next.tracks[0].clips[1].group,initial.tracks[0].clips[0].group);
});
