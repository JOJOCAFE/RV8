import {
  simulate,
  fingerprint,
  configurations,
  terminals,
  endpoint,
} from "./wiring-engine.mjs";
import { labs, partInfo } from "./lab-course.mjs";
import { routeWires } from "./wire-routing.mjs";
import { WIDTH, HEIGHT, constrainPartPosition } from "./workbench-geometry.mjs";
import {
  STORAGE_KEY,
  newNotebook,
  newEvidence,
  restoreNotebook,
  recordExperiment,
  designProven as checkDesign,
} from "./learning-state.mjs";
const $ = (s) => document.querySelector(s),
  $$ = (s) => [...document.querySelectorAll(s)];
const empty = () => ({ parts: [], wires: [] });
const blankEvidence = newEvidence;
let state = newNotebook(),
  storageAvailable = true,
  recovered = false;
try {
  const restored = restoreNotebook(localStorage.getItem(STORAGE_KEY));
  state = restored.notebook;
  recovered = restored.recovered;
} catch {
  storageAvailable = false;
}
let index = 0,
  pending = null,
  selectedWire = null,
  trace = false,
  undo = [],
  redo = [],
  message = "",
  drag = null,
  routeCache = { key: "", paths: new Map() };
const circuit = () => state.circuits[labs[index].id];
const evidence = () => state.evidence[labs[index].id];
const persist = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    storageAvailable = true;
  } catch {
    storageAvailable = false;
  }
  const status = $(".local-label");
  const notice = $("#storage-message");
  if (notice) {
    notice.hidden = storageAvailable && !recovered;
    notice.textContent = !storageAvailable
      ? "Browser storage is unavailable. Your work stays in this tab; download your notebook to keep a copy."
      : "Some saved data could not be restored. Valid circuits have been kept.";
  }
  if (status)
    status.textContent = !storageAvailable
      ? "THIS TAB ONLY · DOWNLOAD A NOTEBOOK TO KEEP IT"
      : recovered
        ? "SOME SAVED WORK COULD NOT BE RESTORED"
        : "YOUR CIRCUITS · SAVED IN THIS BROWSER";
};
const clone = (x) => JSON.parse(JSON.stringify(x));
const esc = (x) =>
  String(x).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const label = (id) =>
  id === "BAT" ? "Battery" : id === "L" ? "Lamp" : `Switch ${id}`;
function endLabel(port) {
  const [id, t] = port.split(".");
  return `${label(id)} ${t === "p" ? "+" : t === "n" ? "−" : t === "a" ? "left" : "right"}`;
}
function ensure() {
  const id = labs[index].id;
  if (!state.circuits[id])
    state.circuits[id] = index
      ? clone(state.circuits[labs[index - 1].id] || empty())
      : empty();
  if (!state.evidence[id]) state.evidence[id] = blankEvidence();
}
function recordEdit(before) {
  undo.push(before);
  if (undo.length > 40) undo.shift();
  redo = [];
}
function changed(before) {
  if (fingerprint(before) !== fingerprint(circuit())) {
    evidence().rows = {};
    evidence().reflection = null;
    trace = false;
    if (evidence().history.length)
      message =
        "Wiring changed. Previous observations stay in your notebook; test this version again.";
  }
  pending = null;
  selectedWire = null;
  persist();
  renderBoard();
  renderEvidence();
}
function mutate(fn) {
  const before = clone(circuit());
  fn(circuit());
  recordEdit(before);
  changed(before);
}
function announce(text) {
  message = text;
  const el = $("#board-message");
  if (el) el.textContent = text;
}
function nav() {
  return `<nav class="lab-nav" aria-label="Experiments">${labs
    .map((l, i) => {
      const unlocked = i === 0 || state.done.includes(labs[i - 1].id);
      return `<a href="#lab-${i + 1}" class="${index === i ? "current" : ""} ${state.done.includes(l.id) ? "proved" : ""}" ${!unlocked ? 'aria-disabled="true" tabindex="-1"' : ""} ${index === i ? 'aria-current="step"' : ""}><span>${state.done.includes(l.id) ? "✓" : String(i + 1).padStart(2, "0")}</span>${l.name}</a>`;
    })
    .join("")}</nav>`;
}
function render() {
  ensure();
  const l = labs[index];
  $("#lab-app").innerHTML = /* HTML */ `${nav()}
    <main id="lab-main" tabindex="-1">
      <div class="lab-intro">
        <span class="eyebrow"
          >EXPERIMENT ${String(index + 1).padStart(2, "0")} · BUILD → PREDICT →
          TEST → EXPLAIN</span
        >
        <h1>${l.title}</h1>
        <p class="lab-goal"><b>Your goal</b> ${l.goal}</p>
      </div>
      <div class="lab-layout">
        <aside class="lesson-guide">
          <span class="eyebrow">FIRST, AN IDEA TO USE</span>
          <h2>${l.concept}</h2>
          <p>${l.teaching}</p>
          <div class="your-task">
            <span class="eyebrow">YOUR TURN</span>
            <p>${l.task}</p>
          </div>
          <details class="hints">
            <summary>I’m stuck. Give me a hint.</summary>
            <div id="hint-body"></div>
            <button id="more-hint" class="plain-button">Show a hint →</button>
          </details>
          <p class="guide-note">
            Wires join only at the round terminals. Lines that cross on the
            drawing are not connected. On a phone, swipe the board to reach the
            other parts.
          </p>
        </aside>
        <div class="build-area">
          <section class="bench" aria-label="Your circuit workbench">
            <div class="bench-heading">
              <div>
                <span class="eyebrow">YOUR WORKBENCH</span
                ><span id="bench-count"></span>
              </div>
              <div class="bench-actions">
                <button id="undo-edit" aria-label="Undo last circuit edit">
                  ↶ Undo</button
                ><button id="redo-edit" aria-label="Redo circuit edit">
                  ↷ Redo</button
                ><button id="remove-wire" disabled>Remove wire</button>
              </div>
            </div>
            <div class="parts-tray" aria-label="Add a part">
              ${l.parts
                .map(
                  (key) =>
                    `<button data-add="${key}"><span class="part-icon">${partInfo[key].icon}</span><span><b>Add ${partInfo[key].name}</b><small>${partInfo[key].detail}</small></span><span aria-hidden="true">＋</span></button>`,
                )
                .join("")}
            </div>
            <div class="board-instructions">
              <span id="board-message" role="status"
                >${esc(
                  message ||
                    "Add parts above. Click one round terminal, then another to connect a wire.",
                )}</span
              ><button id="cancel-wire" class="plain-button" hidden>
                Cancel wire
              </button>
            </div>
            <div class="canvas-scroll">
              <div
                id="circuit-canvas"
                class="circuit-canvas"
                tabindex="0"
                aria-label="Circuit drawing. Parts start disconnected."
              >
                <svg
                  id="wire-layer"
                  viewBox="0 0 ${WIDTH} ${HEIGHT}"
                  aria-label="Your wire connections"
                ></svg>
                <div id="node-layer"></div>
                <div class="empty-bench" id="empty-bench">
                  <span class="empty-icon">＋ ─ ◯</span>
                  <h3>No circuit yet.</h3>
                  <p>
                    Choose a battery and a lamp from the tray.<br />You’ll
                    decide which terminals to connect.
                  </p>
                </div>
              </div>
            </div>
            <div class="bench-status">
              <span id="lamp-status"></span
              ><button id="trace-route" class="plain-button" disabled>
                Trace a route through my wiring
              </button>
            </div>
            <div id="fault-message" role="status"></div>
            <div id="wire-selection"></div>
          </section>
          <section class="experiments-section" aria-label="Predict and test">
            <div class="section-heading">
              <span class="eyebrow">COLLECT EVIDENCE</span>
              <h2>What do you think will happen?</h2>
              <p>
                Choose a prediction before running each setup. Testing sets the
                switch positions; it never changes your wires.
              </p>
            </div>
            <div id="experiment-table"></div>
            <div id="loop-checklist"></div>
            <details class="notebook">
              <summary id="notebook-title">Your experiment notebook</summary>
              <div id="notebook-records"></div>
              <label for="learner-note"
                >In your own words: what changed, and why?</label
              ><textarea
                id="learner-note"
                rows="3"
                placeholder="Write what your tests taught you…"
              ></textarea>
            </details>
          </section>
          <section id="reflection" aria-label="Explain your findings"></section>
        </div>
      </div>
      <footer class="lab-footer">
        <div id="progress-explanation"></div>
        <button id="next-lab" class="next-lab" disabled>
          ${index === labs.length - 1
            ? "Download my notebook ↓"
            : "Next experiment →"}
        </button>
      </footer>
      <p class="scope-note">
        Ideal wire-and-switch model · one source and one lamp · starting
        physical rules are explained in “How this workbench works”. No real
        current or timing measurements.
      </p>
    </main>`;
  bind();
  renderBoard();
  renderEvidence();
  renderHints();
}
function bind() {
  $$("[data-add]").forEach((b) => (b.onclick = () => addPart(b.dataset.add)));
  $("#cancel-wire").onclick = () => {
    pending = null;
    announce("Wire cancelled. Choose a terminal to start again.");
    renderBoard();
  };
  $("#remove-wire").onclick = () => removeWire();
  $("#undo-edit").onclick = () => {
    if (!undo.length) return;
    const before = clone(circuit());
    redo.push(before);
    state.circuits[labs[index].id] = undo.pop();
    changed(before);
  };
  $("#redo-edit").onclick = () => {
    if (!redo.length) return;
    const before = clone(circuit());
    undo.push(before);
    state.circuits[labs[index].id] = redo.pop();
    changed(before);
  };
  $("#trace-route").onclick = () => {
    trace = !trace;
    renderBoard();
    if (trace)
      announce(
        "Highlighted: one route found by following your actual wires and closed contacts.",
      );
  };
  $("#more-hint").onclick = () => {
    evidence().hint = Math.min(labs[index].hints.length, evidence().hint + 1);
    persist();
    renderHints();
  };
  $("#learner-note").value = evidence().note;
  $("#learner-note").oninput = (e) => {
    evidence().note = e.target.value;
    persist();
  };
  $("#next-lab").onclick = () => {
    if (index === labs.length - 1) {
      download();
      return;
    }
    location.hash = "lab-" + (index + 2);
  };
  $("#circuit-canvas").addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      pending = null;
      selectedWire = null;
      renderBoard();
    }
    if (e.key === "Delete" && selectedWire) {
      e.preventDefault();
      removeWire();
    }
  });
}
function renderHints() {
  const e = evidence(),
    l = labs[index];
  $("#hint-body").innerHTML = l.hints
    .slice(0, e.hint)
    .map((h, i) => `<p><b>Hint ${i + 1}.</b> ${h}</p>`)
    .join("");
  $("#more-hint").disabled = e.hint >= l.hints.length;
  $("#more-hint").textContent =
    e.hint >= l.hints.length
      ? "All hints shown"
      : "Show " + (e.hint ? "another " : "a ") + "hint →";
}
function addPart(key) {
  const id = key === "battery" ? "BAT" : key === "lamp" ? "L" : key;
  if (circuit().parts.some((p) => p.id === id)) return;
  const positions = {
      BAT: [75, 230],
      L: [625, 80],
      A: [330, 230],
      B: [330, 65],
      C: [610, 290],
    },
    [x, y] = positions[id];
  mutate((c) =>
    c.parts.push({
      id,
      type: key === "battery" || key === "lamp" ? key : "switch",
      x,
      y,
      closed: false,
    }),
  );
  announce(
    `${label(id)} added with no external connections. Its round terminals are where wires attach.`,
  );
  if (matchMedia("(max-width:760px)").matches)
    $(`[data-part="${id}"]`).scrollIntoView({
      block: "nearest",
      inline: "center",
      behavior: matchMedia("(prefers-reduced-motion:reduce)").matches
        ? "instant"
        : "smooth",
    });
}
function symbol(p, result) {
  if (p.type === "battery")
    return `<svg viewBox="0 0 150 100" aria-hidden="true"><path d="M0 50H65M81 50H150M65 33V67M81 19V81"/><text x="21" y="34">−</text><text x="119" y="34">+</text></svg>`;
  if (p.type === "lamp")
    return `<svg class="lamp-symbol ${result.on ? "lit" : ""}" viewBox="0 0 150 100" aria-hidden="true"><circle cx="75" cy="50" r="30" class="lamp-glass"/><path d="M0 50H45L52 42L60 58L68 42L76 58L84 42L92 58L100 50H150"/><text x="75" y="96">filament</text></svg>`;
  return `<svg class="switch-symbol ${p.closed ? "closed" : ""}" viewBox="0 0 150 100" aria-hidden="true"><path d="M0 50H43M107 50H150"/><path class="contact" d="${p.closed ? "M43 50H107" : "M43 50L99 20"}"/><circle cx="43" cy="50" r="4"/><circle cx="107" cy="50" r="4"/></svg>`;
}
function renderWires(result) {
  const active = new Set(trace ? result.path.map((e) => e.id) : []);
  const cacheKey = JSON.stringify({
    parts: circuit().parts.map((p) => [p.id, p.x, p.y]),
    wires: circuit().wires,
  });
  if (routeCache.key !== cacheKey)
    routeCache = { key: cacheKey, paths: routeWires(circuit(), WIDTH, HEIGHT) };
  $("#wire-layer").innerHTML = circuit()
    .wires.map(
      (w) =>
        `<g class="drawn-wire ${selectedWire === w.id ? "selected" : ""} ${active.has(w.id) ? "traced" : ""}" role="button" tabindex="0" aria-label="Wire from ${endLabel(w.from)} to ${endLabel(w.to)}" data-wire="${w.id}"><path class="wire-hit" d="${routeCache.paths.get(w.id)}"/><path class="wire-visible" d="${routeCache.paths.get(w.id)}"/></g>`,
    )
    .join("");
  $$("[data-wire]").forEach((g) => {
    const select = () => {
      selectedWire = g.dataset.wire;
      pending = null;
      renderBoard();
      $(`[data-wire="${selectedWire}"]`).focus({ preventScroll: true });
      announce(
        "Wire selected. Use Remove wire, or press Delete, to break this connection.",
      );
    };
    g.onclick = select;
    g.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        select();
      }
    };
  });
}
function renderBoard() {
  const c = circuit(),
    r = simulate(c);
  renderWires(r);
  $("#node-layer").innerHTML = c.parts
    .map(
      (p) =>
        `<div class="circuit-part ${p.type}" data-part="${p.id}" style="left:${p.x}px;top:${p.y}px"><button class="move-handle" data-move="${p.id}" aria-label="Move ${label(p.id)}. Drag, or use arrow keys.">${label(p.id)} <span aria-hidden="true">⠿</span></button><button class="delete-part" data-delete="${p.id}" aria-label="Remove ${label(p.id)}">×</button>${symbol(p, r)}${terminals(
          p,
        )
          .map((t) => {
            const port = endpoint(p.id, t);
            return `<button class="terminal ${t === "p" || t === "b" ? "right" : "left"} ${pending === port ? "pending" : ""}" data-port="${port}" aria-label="Connect ${endLabel(port)}" title="${endLabel(port)}"></button>`;
          })
          .join(
            "",
          )}${p.type === "switch" ? `<button class="switch-control" data-toggle="${p.id}" aria-pressed="${p.closed}">${p.closed ? "Open" : "Close"} ${p.id} <small>currently ${p.closed ? "closed" : "open"}</small></button>` : `<span class="part-caption">${p.type === "lamp" ? (r.on ? "ON" : "OFF") : "two different terminals"}</span>`}</div>`,
    )
    .join("");
  $("#empty-bench").hidden = c.parts.length > 0;
  $("#bench-count").textContent =
    `${c.parts.length} parts · ${c.wires.length} wires`;
  $("#lamp-status").innerHTML =
    `<i class="readout-dot ${r.on ? "on" : r.short ? "fault" : ""}"></i> ${r.state === "missing" ? "No complete setup" : r.short ? "Power cut · short circuit" : r.on ? "Lamp on" : "Lamp off"}`;
  $("#fault-message").textContent = r.message;
  $("#fault-message").classList.toggle("fault", r.short);
  $("#trace-route").disabled = !r.path.length;
  $("#trace-route").textContent = trace
    ? "Hide traced route"
    : "Trace a route through my wiring";
  $("#remove-wire").disabled = !selectedWire;
  $("#cancel-wire").hidden = !pending;
  const selected = c.wires.find((w) => w.id === selectedWire);
  $("#wire-selection").textContent = selected
    ? `Selected: ${endLabel(selected.from)} ↔ ${endLabel(selected.to)}`
    : "";
  $("#undo-edit").disabled = !undo.length;
  $("#redo-edit").disabled = !redo.length;
  $$("[data-add]").forEach((b) => {
    const id =
      b.dataset.add === "battery"
        ? "BAT"
        : b.dataset.add === "lamp"
          ? "L"
          : b.dataset.add;
    b.disabled = c.parts.some((p) => p.id === id);
  });
  $$("[data-port]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const port = b.dataset.port;
        if (!pending) {
          pending = port;
          selectedWire = null;
          renderBoard();
          $(`[data-port="${port}"]`).focus({ preventScroll: true });
          announce(`Start: ${endLabel(port)}. Now choose the other terminal.`);
          return;
        }
        if (pending === port) {
          pending = null;
          renderBoard();
          announce("Connection cancelled.");
          return;
        }
        const from = pending,
          to = port;
        if (
          c.wires.some(
            (w) =>
              (w.from === from && w.to === to) ||
              (w.from === to && w.to === from),
          )
        ) {
          pending = null;
          renderBoard();
          announce("Those terminals already have a wire.");
          return;
        }
        mutate((c) =>
          c.wires.push({ id: "w" + crypto.randomUUID().slice(0, 8), from, to }),
        );
        announce(`Connected ${endLabel(from)} to ${endLabel(to)}.`);
        $(`[data-port="${to}"]`).focus({ preventScroll: true });
      }),
  );
  $$("[data-toggle]").forEach(
    (b) =>
      (b.onclick = () => {
        const p = c.parts.find((p) => p.id === b.dataset.toggle);
        p.closed = !p.closed;
        persist();
        renderBoard();
        $(`[data-toggle="${p.id}"]`).focus({ preventScroll: true });
        announce(
          `${label(p.id)} is now ${p.closed ? "closed: its metal contact joins the two ends." : "open: the contact no longer joins its ends."}`,
        );
      }),
  );
  $$("[data-delete]").forEach(
    (b) =>
      (b.onclick = () => {
        const id = b.dataset.delete;
        mutate((c) => {
          c.parts = c.parts.filter((p) => p.id !== id);
          c.wires = c.wires.filter(
            (w) => !w.from.startsWith(id + ".") && !w.to.startsWith(id + "."),
          );
        });
        announce(`${label(id)} and its attached wires removed.`);
      }),
  );
  $$("[data-move]").forEach((b) => {
    b.onpointerdown = (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      const p = c.parts.find((p) => p.id === b.dataset.move);
      drag = {
        id: p.id,
        startX: e.clientX,
        startY: e.clientY,
        x: p.x,
        y: p.y,
        before: clone(c),
      };
      b.setPointerCapture(e.pointerId);
    };
    b.onpointermove = (e) => {
      if (!drag || drag.id !== b.dataset.move) return;
      const p = c.parts.find((p) => p.id === drag.id);
      Object.assign(
        p,
        constrainPartPosition(
          drag.x + e.clientX - drag.startX,
          drag.y + e.clientY - drag.startY,
          { snap: true },
        ),
      );
      const el = $(`[data-part="${p.id}"]`);
      el.style.left = p.x + "px";
      el.style.top = p.y + "px";
      renderWires(simulate(c));
    };
    b.onpointerup = () => {
      if (!drag) return;
      if (JSON.stringify(drag.before) !== JSON.stringify(c))
        recordEdit(drag.before);
      drag = null;
      persist();
      renderBoard();
    };
    b.onpointercancel = () => {
      if (drag) {
        state.circuits[labs[index].id] = drag.before;
        drag = null;
        persist();
      }
      renderBoard();
    };
    b.onkeydown = (e) => {
      const directions = {
        ArrowLeft: [-10, 0],
        ArrowRight: [10, 0],
        ArrowUp: [0, -10],
        ArrowDown: [0, 10],
      };
      if (!directions[e.key]) return;
      e.preventDefault();
      const [dx, dy] = directions[e.key],
        p = c.parts.find((p) => p.id === b.dataset.move);
      const before = clone(c);
      Object.assign(p, constrainPartPosition(p.x + dx, p.y + dy));
      recordEdit(before);
      persist();
      renderBoard();
      $(`[data-move="${p.id}"]`).focus();
    };
  });
}
function removeWire() {
  if (!selectedWire) return;
  const id = selectedWire;
  mutate((c) => (c.wires = c.wires.filter((w) => w.id !== id)));
  announce("Wire removed. Predict what changed, then test your circuit.");
}
function setupName(config) {
  const entries = Object.entries(config);
  return entries.length
    ? entries
        .map(([id, closed]) => `${id} ${closed ? "closed" : "open"}`)
        .join(" · ")
    : "Your current wiring";
}
function experiment(row) {
  const observation = recordExperiment(labs[index], circuit(), evidence(), row);
  if (!observation) return;
  const { result: r, required, prediction } = observation;
  persist();
  renderBoard();
  renderEvidence();
  $(`[data-test="${row}"]`).focus({ preventScroll: true });
  announce(
    r.short
      ? "Short circuit recorded. That does not meet the goal. Inspect the route that avoids the lamp."
      : !required
        ? "Some required parts are missing. Add them before checking this design."
        : prediction === r.on
          ? `Prediction matched: lamp ${r.on ? "on" : "off"}. What route explains that?`
          : `Prediction was ${prediction ? "on" : "off"}; observed ${r.on ? "on" : "off"}. Use the wiring to explain the difference.`,
  );
}
function designProven() {
  return checkDesign(labs[index], circuit(), evidence());
}
function renderEvidence() {
  const e = evidence(),
    l = labs[index],
    configs = configurations(l.switches),
    fp = fingerprint(circuit());
  $("#experiment-table").innerHTML =
    `<table class="experiment-table"><thead><tr><th scope="col">Input setup</th><th scope="col">My prediction</th><th scope="col">Observe</th><th scope="col">Evidence for the goal</th></tr></thead><tbody>${configs
      .map((config, i) => {
        const r = e.rows[i],
          fresh = r && r.fingerprint === fp,
          match = fresh && r.valid && r.on === r.target;
        return `<tr><th scope="row">${setupName(config)}</th><td><div class="prediction-options" role="group" aria-label="Prediction for ${setupName(config)}">${[false, true].map((on) => `<button data-predict="${i}" data-value="${on}" class="${e.predictions[i] === on ? "picked" : ""}" aria-pressed="${e.predictions[i] === on}">${on ? "On" : "Off"}</button>`).join("")}</div></td><td><button class="run-experiment" data-test="${i}" ${typeof e.predictions[i] !== "boolean" ? "disabled" : ""}>Test setup →</button>${fresh ? `<span class="observed">${r.short ? "Short circuit" : r.valid ? (r.on ? "Lamp on" : "Lamp off") : "Incomplete setup"}</span>` : ""}</td><td><span class="evidence-state ${match ? "matched" : fresh ? "mismatch" : ""}">${match ? "✓ Fits the goal" : fresh ? "Needs investigation" : "Not tested"}</span></td></tr>`;
      })
      .join("")}</tbody></table>`;
  $$("[data-predict]").forEach(
    (b) =>
      (b.onclick = () => {
        const row = b.dataset.predict,
          value = b.dataset.value;
        e.predictions[row] = value === "true";
        persist();
        renderEvidence();
        $(`[data-predict="${row}"][data-value="${value}"]`).focus({
          preventScroll: true,
        });
      }),
  );
  $$("[data-test]").forEach(
    (b) => (b.onclick = () => experiment(Number(b.dataset.test))),
  );
  $("#loop-checklist").innerHTML =
    l.id === "loop"
      ? `<div class="loop-proof"><h3>Don’t just get it working. Explain it by changing it.</h3>${[
          ["lit", "Make the lamp glow and record a test."],
          ["broken", "Remove one of your wires. Predict and test again."],
          ["repaired", "Repair the route. Test that the lamp glows again."],
        ]
          .map(
            ([key, text]) =>
              `<p class="${e.proof[key] ? "checked" : ""}"><span>${e.proof[key] ? "✓" : "○"}</span>${text}</p>`,
          )
          .join("")}</div>`
      : "";
  $("#notebook-title").textContent =
    `Your experiment notebook · ${e.history.length} observations`;
  $("#notebook-records").innerHTML = e.history.length
    ? e.history
        .slice(-8)
        .reverse()
        .map(
          (r, i) =>
            `<p><b>${e.history.length - i}. ${setupName(r.config)}</b><span>Predicted ${r.prediction ? "on" : "off"} → ${r.short ? "short circuit" : r.valid ? "observed " + (r.on ? "on" : "off") : "incomplete setup"}${r.fingerprint !== fp ? " · earlier wiring" : ""}</span></p>`,
        )
        .join("")
    : "<p>Your predictions and observations will be recorded here. Changing your mind is part of the experiment.</p>";
  const ready = designProven();
  $("#reflection").innerHTML = ready
    ? `<div class="reflection-box"><span class="eyebrow">TRY THE IDEA IN A NEW SITUATION</span><h2>${l.question}</h2><div class="reflection-options">${l.answers.map((a, i) => `<button data-reflect="${i}" class="${e.reflection === i ? "chosen" : ""}">${a}</button>`).join("")}</div><p id="reflection-feedback" role="status">${e.reflection === l.correct ? l.feedback : e.reflection !== null ? "Think about the route, rather than just the number of wires or closed switches." : ""}</p>${e.reflection === l.correct ? `<div class="takeaway"><b>${l.id === "both" ? "You built AND." : l.id === "either" ? "You built OR." : l.id === "transfer" ? "You built a combined rule." : "What you established"}</b><p>${l.takeaway}</p></div>` : ""}</div>`
    : "";
  $$("[data-reflect]").forEach(
    (b) =>
      (b.onclick = () => {
        e.reflection = Number(b.dataset.reflect);
        if (e.reflection === l.correct && !state.done.includes(l.id))
          state.done.push(l.id);
        persist();
        renderEvidence();
        $(`[data-reflect="${e.reflection}"]`).focus({ preventScroll: true });
      }),
  );
  const passed = ready && e.reflection === l.correct;
  $("#next-lab").disabled = !passed;
  $("#progress-explanation").textContent = passed
    ? index === labs.length - 1
      ? "You constructed and tested five circuits. Your notebook records the evidence."
      : l.takeaway
    : ready
      ? "Your circuit fits every tested case. Now use the idea to answer the new situation above."
      : l.id === "loop"
        ? "Build it, test it, break it, and repair it. Then explain what you learned."
        : "A working design must fit every row using the same wiring.";
  const old = $(".lab-nav");
  if (old) old.outerHTML = nav();
}
function download() {
  const data = {
    title: "My RV8 wiring notebook",
    model: "ideal connectivity",
    exported: new Date().toISOString(),
    ...state,
  };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  a.download = "my-rv8-wiring-notebook.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function route() {
  const m = location.hash.match(/^#lab-([1-5])$/),
    requested = m ? Number(m[1]) - 1 : 0;
  let unlocked = 0;
  while (unlocked < labs.length - 1 && state.done.includes(labs[unlocked].id))
    unlocked++;
  index = Math.min(requested, unlocked);
  if (location.hash !== `#lab-${index + 1}`)
    history.replaceState(null, "", `#lab-${index + 1}`);
  pending = null;
  selectedWire = null;
  trace = false;
  drag = null;
  undo = [];
  redo = [];
  message = "";
  render();
  persist();
}
document.addEventListener("click", (e) => {
  const link = e.target.closest('.lab-nav a[aria-disabled="true"]');
  if (link) {
    e.preventDefault();
    announce(
      "Build and investigate the current experiment first. The next one uses what you establish here.",
    );
  }
});
$("#download-notebook").onclick = download;
$("#open-help").onclick = () => $("#help-dialog").showModal();
$("#close-help").onclick = () => $("#help-dialog").close();
window.addEventListener("hashchange", () => {
  route();
  window.scrollTo(0, 0);
});
route();
