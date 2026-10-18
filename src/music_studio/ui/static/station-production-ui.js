/* Group editing and one-level routing share the project's ordinary save/history path. */
window.StationProduction = {
  mount(api) {
    const {
      $,
      s,
      tr,
      esc,
      content,
      uid,
      mutate,
      guarded,
      renderAll,
      selectedClip,
      selectedTrack,
      pause,
      snap,
      flush,
    } = api;
    let selected = new Set(),
      project = null;
    const tools = document.createElement("button");
    tools.id = "production-tools";
    $("duplicate").after(tools);
    const dialog = document.createElement("dialog");
    dialog.id = "production-dialog";
    document.body.append(dialog);
    const set = (next) => mutate(() => Object.assign(content(), next));
    function ids() {
      const known = new Set(
        content().tracks.flatMap((t) => t.clips.map((c) => c.id)),
      );
      selected = new Set([...selected].filter((id) => known.has(id)));
      return StationGroups.expand(
        content(),
        selected.size ? [...selected] : s.clip ? [s.clip] : [],
      );
    }
    function mark() {
      const values = new Set(ids());
      $("track-list")
        .querySelectorAll("[data-clip]")
        .forEach((el) => {
          el.classList.toggle("group-selected", values.has(el.dataset.clip));
          const c = content()
            .tracks.flatMap((t) => t.clips)
            .find((c) => c.id === el.dataset.clip);
          el.classList.toggle("group-member", !!c?.group);
        });
    }
    let applying = false;
    async function apply(operation, delta = 0) {
      if (applying) return;
      applying = true;
      try {
        await flush();
        const known = new Set(
          content().tracks.flatMap((t) => t.clips.map((c) => c.id)),
        );
        const next = StationGroups.edit(
          content(),
          ids(),
          operation,
          delta,
          uid,
        );
        if (operation === "copy")
          selected = new Set(
            next.tracks
              .flatMap((t) => t.clips)
              .filter((c) => !known.has(c.id))
              .map((c) => c.id),
          );
        if (operation === "delete") {
          selected.clear();
          s.clip = null;
        }
        if (operation === "copy") {
          s.clip = [...selected][0];
          s.track = next.tracks.find((t) =>
            t.clips.some((c) => c.id === s.clip),
          )?.id;
        }
        set(next);
        await flush();
      } finally {
        applying = false;
      }
    }
    async function groupAction(operation, delta = 0) {
      dialog
        .querySelectorAll("[data-group-op], #group-destination")
        .forEach((el) => (el.disabled = true));
      try {
        await apply(operation, delta);
      } finally {
        show("clips");
      }
    }
    function fxNumber(label, path, value, min, max, step) {
      return `<label>${label}<input data-bus-fx="${path}" type="number" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
    }
    function show(tab = "clips") {
      const count = ids().length;
      dialog.innerHTML = `<div class="dialog-heading"><h2>${tr("编排与路由", "Arrange & route")}</h2><button data-close>×</button></div>
      <nav class="production-tabs"><button data-tab="clips">${tr("成组编排", "Clip groups")}</button><button data-tab="routing">${tr("总线与发送", "Buses & sends")}</button></nav><div id="production-body"></div>`;
      const body = dialog.querySelector("#production-body");
      if (tab === "clips") {
        body.innerHTML = `<p class="panel-copy">${tr("Shift 点击可多选；已成组的片段会一起选择和移动。源裁切、音符与淡变保持不变。", "Shift-click to select more. Grouped clips select and move together; source crops, notes and fades stay intact.")}</p>
        <div class="production-count">${count} ${tr("个片段已选择", "clips selected")}</div><div class="production-actions"><button data-select-all>${tr("选择所有片段", "Select all clips")}</button><button data-select-section>${tr("选择当前段落", "Select current section")}</button><button data-clear>${tr("清除多选", "Clear selection")}</button></div>
        <div class="production-actions"><button data-group-op="group" ${count < 2 ? "disabled" : ""}>${tr("组成一组", "Group")}</button><button data-group-op="ungroup" ${!count ? "disabled" : ""}>${tr("解除分组", "Ungroup")}</button></div>
        <label class="field-row">${tr("放到第几小节", "Destination bar")}<input id="group-destination" type="number" min="1" step=".0625" value="${
          count
            ? +(
                (Math.min(
                  ...content()
                    .tracks.flatMap((t) => t.clips)
                    .filter((c) => ids().includes(c.id))
                    .map((c) => c.start),
                ) *
                  content().bpm) /
                  240 +
                9
              ).toFixed(4)
            : 9
        }"></label>
        <div class="production-actions"><button data-group-op="move" ${!count ? "disabled" : ""}>${tr("整体移动", "Move selection")}</button><button class="primary" data-group-op="copy" ${!count ? "disabled" : ""}>${tr("复制到这里", "Copy here")}</button><button data-group-op="delete" ${!count ? "disabled" : ""}>${tr("删除所选", "Delete selection")}</button></div>
        <h3>${tr("批量调整片段", "Batch clip properties")}</h3>
        <div class="production-actions"><label>${tr("片段音量 dB", "Clip gain dB")}<input id="group-gain" type="number" min="-60" max="12" step=".5" value="-3"></label><button data-group-op="gain" ${!count ? "disabled" : ""}>${tr("应用音量", "Apply gain")}</button></div>
        <div class="production-actions"><label>${tr("淡变秒数", "Fade seconds")}<input id="group-fade" type="number" min="0" max="30" step=".1" value="1"></label><button data-group-op="fade-in" ${!count ? "disabled" : ""}>${tr("应用淡入", "Apply fade in")}</button><button data-group-op="fade-out" ${!count ? "disabled" : ""}>${tr("应用淡出", "Apply fade out")}</button></div>`;
      } else {
        body.innerHTML = `<p class="panel-copy">${tr("把相关轨道输出到一个总线统一混音；用发送共享混响。发送位于推子后，总线直接进入主输出。", "Route related tracks through a bus. Use post-fader sends for shared effects; buses feed the master.")}</p>
        <div class="production-actions"><button data-add-bus="group" ${(content().buses || []).length >= 8 ? "disabled" : ""}>＋ ${tr("分组总线", "Group bus")}</button><button data-add-bus="reverb" ${(content().buses || []).length >= 8 ? "disabled" : ""}>＋ ${tr("共享混响", "Shared reverb")}</button></div>
        <div class="bus-list">${(content().buses || [])
          .map(
            (
              b,
            ) => `<section class="bus-card" data-bus="${b.id}"><label>${tr("总线名称", "Bus name")}<input data-bus-field="name" maxlength="150" value="${esc(b.name)}"></label><div class="production-actions"><label>${tr("音量 dB", "Gain dB")}<input data-bus-field="gain_db" type="number" min="-60" max="12" step=".5" value="${b.gain_db}"></label><label>${tr("声像", "Pan")}<input data-bus-field="pan" type="number" min="-1" max="1" step=".05" value="${b.pan}"></label><label><input data-bus-field="mute" type="checkbox" ${b.mute ? "checked" : ""}> M</label><label><input data-bus-field="solo" type="checkbox" ${b.solo ? "checked" : ""}> S</label></div>
        <div class="production-actions"><label><input data-bus-fx="bypass" type="checkbox" ${b.effects?.bypass ? "checked" : ""}> ${tr("旁路效果", "Bypass FX")}</label><label><input data-bus-fx="eq.enabled" type="checkbox" ${b.effects?.eq?.enabled ? "checked" : ""}> EQ</label><label><input data-bus-fx="compressor.enabled" type="checkbox" ${b.effects?.compressor?.enabled ? "checked" : ""}> ${tr("压缩", "Compression")}</label><label><input data-bus-fx="reverb.enabled" type="checkbox" ${b.effects?.reverb?.enabled ? "checked" : ""}> ${tr("混响", "Reverb")}</label></div>
        <div class="production-actions">${["low", "mid", "high"].map((band, i) => fxNumber(tr(["低频 dB", "中频 dB", "高频 dB"][i], ["Low dB", "Mid dB", "High dB"][i]), `eq.${band}_db`, b.effects?.eq?.[`${band}_db`] ?? 0, -12, 12, 0.5)).join("")}</div>
        <div class="production-actions">${fxNumber(tr("压缩阈值 dB", "Threshold dB"), "compressor.threshold_db", b.effects?.compressor?.threshold_db ?? -18, -48, 0, 1)}${fxNumber(tr("压缩比", "Ratio"), "compressor.ratio", b.effects?.compressor?.ratio ?? 3, 1, 12, 0.5)}${fxNumber(tr("补偿 dB", "Makeup dB"), "compressor.makeup_db", b.effects?.compressor?.makeup_db ?? 0, 0, 12, 0.5)}</div>
        <div class="production-actions"><label>${tr("湿声比例", "Wet mix")}<input data-bus-fx="reverb.mix" type="number" min="0" max="1" step=".01" value="${b.effects?.reverb?.mix ?? 0.15}"></label><label>${tr("衰减秒数", "Decay seconds")}<input data-bus-fx="reverb.decay" type="number" min=".2" max="3" step=".1" value="${b.effects?.reverb?.decay ?? 1.2}"></label><button data-remove-bus="${b.id}">${tr("移除总线", "Remove bus")}</button></div></section>`,
          )
          .join("")}</div>
        <h3>${tr("轨道输出与发送", "Track outputs & sends")}</h3>${content()
          .tracks.map(
            (t) =>
              `<section class="route-card" data-route="${t.id}"><strong>${esc(t.name)}</strong><label>${tr("输出", "Output")}<select data-route-output><option value="">Master</option>${(content().buses || []).map((b) => `<option value="${b.id}" ${t.output === b.id ? "selected" : ""}>${esc(b.name)}</option>`).join("")}</select></label>${(
                content().buses || []
              )
                .map((b) => {
                  const send = (t.sends || []).find((x) => x.bus === b.id);
                  return `<label class="send-row"><input type="checkbox" data-send-enabled="${b.id}" ${send?.enabled ? "checked" : ""}>${esc(b.name)}<input type="number" min="-60" max="6" step="1" value="${send?.gain_db ?? -12}" data-send-gain="${b.id}"> dB</label>`;
                })
                .join("")}</section>`,
          )
          .join("")}`;
      }
      dialog.querySelector("[data-close]").onclick = () => dialog.close();
      dialog
        .querySelectorAll("[data-tab]")
        .forEach((b) => (b.onclick = () => show(b.dataset.tab)));
      if (tab === "clips") {
        body.querySelector("[data-select-all]").onclick = () => {
          selected = new Set(
            content().tracks.flatMap((t) => t.clips.map((c) => c.id)),
          );
          mark();
          show();
        };
        body.querySelector("[data-clear]").onclick = () => {
          selected.clear();
          s.clip = null;
          renderAll();
          show();
        };
        body.querySelector("[data-select-section]").onclick = () => {
          const section = (content().sections || []).find(
            (m) =>
              m.start <= (s.position * content().bpm) / 60 &&
              m.end > (s.position * content().bpm) / 60,
          );
          if (!section) return;
          selected = new Set(
            content()
              .tracks.flatMap((t) => t.clips)
              .filter(
                (c) =>
                  c.start >= (section.start * 60) / content().bpm - 1e-7 &&
                  c.start + c.duration <=
                    (section.end * 60) / content().bpm + 1e-7,
              )
              .map((c) => c.id),
          );
          mark();
          show();
        };
        body.querySelectorAll("[data-group-op]").forEach(
          (b) =>
            (b.onclick = guarded(async () => {
              const operation = b.dataset.groupOp;
              if (["gain", "fade-in", "fade-out"].includes(operation)) {
                const input = $(
                  operation === "gain" ? "group-gain" : "group-fade",
                );
                if (!input.checkValidity()) {
                  input.reportValidity();
                  return;
                }
                return groupAction(operation, Number(input.value));
              }
              const destination = Number($("group-destination").value);
              const first = Math.min(
                ...content()
                  .tracks.flatMap((t) => t.clips)
                  .filter((c) => ids().includes(c.id))
                  .map((c) => c.start),
              );
              await groupAction(
                operation,
                ((destination - 1) * 240) / content().bpm - first,
              );
            })),
        );
      } else {
        body.querySelectorAll("[data-add-bus]").forEach(
          (b) =>
            (b.onclick = () => {
              mutate(() => {
                content().buses ??= [];
                const effects = StationEffects.defaults();
                if (b.dataset.addBus === "reverb") {
                  effects.reverb.enabled = true;
                  effects.reverb.mix = 1;
                }
                content().buses.push({
                  id: uid(),
                  name:
                    b.dataset.addBus === "reverb"
                      ? tr("共享空间", "Shared room")
                      : tr("声部分组", "Part group"),
                  gain_db: 0,
                  pan: 0,
                  mute: false,
                  solo: false,
                  effects,
                });
              });
              show("routing");
            }),
        );
        body.querySelectorAll("[data-remove-bus]").forEach(
          (b) =>
            (b.onclick = () => {
              mutate(() => {
                const id = b.dataset.removeBus;
                content().buses = content().buses.filter((x) => x.id !== id);
                for (const t of content().tracks) {
                  if (t.output === id) t.output = null;
                  t.sends = (t.sends || []).filter((x) => x.bus !== id);
                }
              });
              show("routing");
            }),
        );
        body.onchange = guarded((e) => {
          const el = e.target;
          if (!el.checkValidity()) return;
          const bus = content().buses?.find(
            (b) => b.id === el.closest("[data-bus]")?.dataset.bus,
          );
          const track = content().tracks.find(
            (t) => t.id === el.closest("[data-route]")?.dataset.route,
          );
          const structural =
            track &&
            (el.hasAttribute("data-route-output") ||
              !(track.sends || []).some(
                (send) =>
                  send.bus === (el.dataset.sendEnabled || el.dataset.sendGain),
              ));
          mutate(
            () => {
              if (bus) {
                const value =
                  el.type === "checkbox"
                    ? el.checked
                    : el.type === "number"
                      ? Number(el.value)
                      : el.value.trim();
                if (el.dataset.busField) {
                  if (value !== "") bus[el.dataset.busField] = value;
                } else if (el.dataset.busFx) {
                  bus.effects = StationEffects.normalize(bus.effects);
                  const path = el.dataset.busFx.split(".");
                  if (path.length === 1) bus.effects[path[0]] = value;
                  else bus.effects[path[0]][path[1]] = value;
                }
              }
              if (track) {
                if (el.hasAttribute("data-route-output"))
                  track.output = el.value || null;
                else {
                  const id = el.dataset.sendEnabled || el.dataset.sendGain;
                  track.sends ??= [];
                  let send = track.sends.find((x) => x.bus === id);
                  if (!send) {
                    send = { bus: id, gain_db: -12, enabled: false };
                    track.sends.push(send);
                  }
                  if (el.dataset.sendEnabled) send.enabled = el.checked;
                  else send.gain_db = Number(el.value);
                }
              }
            },
            { live: !structural },
          );
          if (bus && el.dataset.busField === "name") {
            body.querySelectorAll("[data-route-output] option").forEach((o) => {
              if (o.value === bus.id) o.textContent = bus.name;
            });
            body.querySelectorAll("[data-send-enabled]").forEach((input) => {
              if (input.dataset.sendEnabled === bus.id)
                input.nextSibling.textContent = bus.name;
            });
          }
        });
      }
      if (!dialog.open) dialog.showModal();
    }
    tools.onclick = () => show();
    function pointer(e) {
      const el = e.target.closest("[data-clip]");
      if (!el || e.button !== 0) return false;
      const c = content()
        .tracks.flatMap((t) => t.clips)
        .find((c) => c.id === el.dataset.clip);
      if (e.shiftKey) {
        selected = new Set(ids());
        const members = StationGroups.expand(content(), [c.id]);
        const remove = members.every((id) => selected.has(id));
        for (const id of members)
          remove ? selected.delete(id) : selected.add(id);
        if (!selected.size) s.clip = null;
        mark();
        return true;
      }
      if (!selected.size || !ids().includes(c.id)) selected = new Set([c.id]);
      const values = StationGroups.expand(content(), [...selected]);
      if (values.length < 2 || e.target.classList.contains("clip-handle")) {
        mark();
        return false;
      }
      const initial = structuredClone(content()),
        firstX = e.clientX;
      let moved = false;
      const move = (event) => {
        if (Math.abs(event.clientX - firstX) < 3 && !moved) return;
        pause();
        moved = true;
        try {
          const delta =
            snap(c.start + (event.clientX - firstX) / s.zoom) - c.start;
          const next = StationGroups.edit(initial, values, "move", delta, uid);
          s.session.content = next;
          mark();
          for (const t of next.tracks)
            for (const item of t.clips) {
              const node = $("track-list").querySelector(
                `[data-clip="${item.id}"]`,
              );
              if (node) node.style.left = `${item.start * s.zoom}px`;
            }
        } catch (_) {}
      };
      const up = () => {
        window.removeEventListener("pointermove", move);
        if (moved) {
          const next = content();
          s.session.content = initial;
          mutate(() => {
            s.session.content = next;
          });
        }
      };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up, { once: true });
      return true;
    }
    $("track-list").addEventListener(
      "click",
      (e) => {
        if (e.shiftKey && e.target.closest("[data-clip]")) {
          e.stopImmediatePropagation();
          e.preventDefault();
        }
      },
      true,
    );
    function mixer() {
      if (!s.session) return;
      $("mixer")
        .querySelectorAll("[data-production-channel]")
        .forEach((el) => el.remove());
      const master = $("mixer").querySelector(".master-channel");
      for (const b of content().buses || []) {
        const el = document.createElement("div");
        el.className = "channel bus-channel";
        el.dataset.productionChannel = b.id;
        el.innerHTML = `<span class="channel-name">${esc(b.name)}</span><small>BUS → MASTER</small><div class="fader-row"><input type="range" min="-60" max="12" step=".5" data-bus-level="${b.id}" aria-label="${esc(b.name)} ${tr("总线音量", "bus gain")}" value="${b.gain_db}"><div class="vu"><span data-vu="${b.id}"></span></div></div><span data-bus-db="${b.id}" class="channel-db">${b.gain_db.toFixed(1)} dB</span><button data-routing>${tr("路由与效果", "Routing & FX")}</button><div class="channel-buttons"><button data-bus-toggle="mute" data-id="${b.id}" class="mini-toggle ${b.mute ? "active" : ""}">M</button><button data-bus-toggle="solo" data-id="${b.id}" class="mini-toggle ${b.solo ? "active" : ""}">S</button></div>`;
        master.before(el);
      }
      const add = document.createElement("button");
      add.dataset.productionChannel = "add";
      add.dataset.routing = "";
      add.className = "routing-open";
      add.textContent = tr("＋ 总线 / 发送", "＋ Bus / sends");
      master.before(add);
      $("mixer")
        .querySelectorAll("[data-routing]")
        .forEach((b) => (b.onclick = () => show("routing")));
      $("mixer")
        .querySelectorAll("[data-bus-toggle]")
        .forEach(
          (b) =>
            (b.onclick = () =>
              mutate(
                () => {
                  const bus = content().buses.find(
                    (x) => x.id === b.dataset.id,
                  );
                  bus[b.dataset.busToggle] = !bus[b.dataset.busToggle];
                },
                { live: true },
              )),
        );
      $("mixer")
        .querySelectorAll("[data-bus-level]")
        .forEach(
          (input) =>
            (input.oninput = () => {
              mutate(
                () => {
                  content().buses.find(
                    (b) => b.id === input.dataset.busLevel,
                  ).gain_db = Number(input.value);
                },
                { live: true, render: false },
              );
              $("mixer").querySelector(
                `[data-bus-db="${input.dataset.busLevel}"]`,
              ).textContent = Number(input.value).toFixed(1) + " dB";
            }),
        );
    }
    return {
      pointer,
      apply: guarded(apply),
      selection: ids,
      mixer,
      render() {
        if (project !== s.session?.id) {
          selected.clear();
          project = s.session?.id;
        }
        tools.textContent = tr("编排 / 路由", "Arrange / route");
        if (s.session) mark();
      },
      select(ids) {
        selected = new Set(ids);
        mark();
      },
      show,
    };
  },
};
