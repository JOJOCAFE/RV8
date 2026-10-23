import {
  simulate,
  fingerprint,
  terminals,
  endpoint,
} from "./wiring-engine.mjs";
import { labs } from "./lab-course.mjs";
import { layoutWires, previewWirePaths } from "./wire-routing.mjs";
import {
  attachBoardInteractions,
  isTextEditing,
} from "./board-interactions.mjs";
import {
  shellMarkup,
  goalMarkup,
  testControlsMarkup,
  evidenceMarkup,
  setupName,
} from "./workbench-view.mjs";
import { WIDTH, HEIGHT, constrainPartPosition } from "./workbench-geometry.mjs";
import {
  STORAGE_KEY,
  newNotebook,
  newEvidence,
  restoreNotebook,
  recordExperiment,
  designProven as checkDesign,
  currentCaseIndex,
  recordedRowsForCircuit,
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
  selectedPart = null,
  plannedCase = null,
  boardController = null,
  trace = false,
  undo = [],
  redo = [],
  message = "",
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
    evidence().rows = recordedRowsForCircuit(
      labs[index],
      circuit(),
      evidence(),
    );
    evidence().reflection = null;
    trace = false;
    if (evidence().history.length)
      message =
        "Wiring changed. Previous observations stay in your notebook; test this version again.";
  }
  pending = null;
  selectedWire = null;
  selectedPart = null;
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
  if (plannedCase === null)
    plannedCase = Math.max(0, currentCaseIndex(labs[index], circuit()));
  const lab = labs[index];
  $("#lab-app").innerHTML = shellMarkup({
    lab,
    index,
    nav: nav(),
    message: esc(message),
    goal: goalMarkup(lab, evidence()),
  });
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
  $("#remove-wire").onclick = () => removeSelection();
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
  const canvas = $("#circuit-canvas");
  boardController = attachBoardInteractions(canvas, {
    getCircuit: circuit,
    selectPart,
    clearSelection,
    clickPort,
    beginWire(port) {
      selectedPart = null;
      selectedWire = null;
      paintSelection();
      announce(
        `Start: ${endLabel(port)}. Drag to another terminal, or click it.`,
      );
    },
    movePart(id, point) {
      const p = circuit().parts.find((p) => p.id === id);
      Object.assign(p, point);
      const el = $(`[data-part="${id}"]`);
      el.style.left = p.x + "px";
      el.style.top = p.y + "px";
      renderWires(simulate(circuit()), { preview: true });
    },
    finishPart(id, before) {
      if (JSON.stringify(before) !== JSON.stringify(circuit()))
        recordEdit(before);
      persist();
      renderBoard();
      $(`[data-part="${id}"]`)?.focus({ preventScroll: true });
    },
    cancelPart(before) {
      state.circuits[labs[index].id] = before;
      persist();
      renderBoard();
    },
    finishWire(from, to) {
      if (to) connectWire(from, to);
      else {
        pending = from;
        renderBoard();
        announce(
          "No wire added. Drop on a round terminal, or click the other terminal to finish.",
        );
      }
    },
    cancelWire() {
      pending = null;
      renderBoard();
      announce("Wire cancelled.");
    },
  });
  canvas.addEventListener("focusin", (e) => {
    if (e.target.matches("[data-part], [data-move]"))
      selectPart(e.target.closest("[data-part]").dataset.part);
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
function renderWires(result, { preview = false } = {}) {
  const active = new Set(trace ? result.path.map((edge) => edge.id) : []);
  const cacheKey = JSON.stringify({
    parts: circuit().parts.map((p) => [p.id, p.x, p.y]),
    wires: circuit().wires,
  });
  if (!preview && routeCache.key !== cacheKey)
    routeCache = { key: cacheKey, ...layoutWires(circuit(), WIDTH, HEIGHT) };
  const layout = preview
    ? {
        paths: previewWirePaths(circuit()),
        nets: routeCache.nets || new Map(),
        crossings: [],
        junctions: [],
      }
    : routeCache;
  const selectedNet = selectedWire ? layout.nets.get(selectedWire) : null;
  const paths = [...circuit().wires]
    .sort(
      (a, b) => Number(a.id === selectedWire) - Number(b.id === selectedWire),
    )
    .map(
      (w) =>
        `<g class="drawn-wire ${selectedWire === w.id ? "selected" : ""} ${active.has(w.id) ? "traced" : ""}" role="button" tabindex="0" aria-label="Wire from ${endLabel(w.from)} to ${endLabel(w.to)}" data-wire="${w.id}"><path class="wire-hit" d="${layout.paths.get(w.id)}"/><path class="wire-visible" d="${layout.paths.get(w.id)}"/></g>`,
    )
    .join("");
  const crossings = layout.crossings
    .map((c) => {
      const chosen = c.horizontalWires.includes(selectedWire),
        underChosen = c.verticalWires.includes(selectedWire),
        lit = c.horizontalWires.some((id) => active.has(id)),
        underLit = c.verticalWires.some((id) => active.has(id));
      return `<g class="wire-crossing ${chosen ? "selected" : ""} ${underChosen ? "under-selected" : ""} ${lit ? "traced" : ""} ${underLit ? "under-traced" : ""}" aria-hidden="true"><path class="bridge-clear" d="M${c.x - 7},${c.y}H${c.x + 7}"/><path class="bridge-under" d="M${c.x},${c.y - 8}V${c.y + 8}"/><path class="bridge-halo" d="M${c.x - 7},${c.y}Q${c.x},${c.y - 14} ${c.x + 7},${c.y}"/><path class="bridge-line" d="M${c.x - 7},${c.y}Q${c.x},${c.y - 14} ${c.x + 7},${c.y}"/></g>`;
    })
    .join("");
  const junctions = layout.junctions
    .map(
      (j) =>
        `<circle class="wire-junction ${selectedNet === j.net ? "selected" : ""}" cx="${j.x}" cy="${j.y}" r="3.5" aria-hidden="true"/>`,
    )
    .join("");
  $("#wire-layer").innerHTML =
    paths + `<g class="wire-decoration">${crossings}${junctions}</g>`;
  $$("[data-wire]").forEach((g) => {
    const select = () => {
      selectedWire = g.dataset.wire;
      selectedPart = null;
      pending = null;
      renderBoard();
      $(`[data-wire="${selectedWire}"]`).focus({ preventScroll: true });
      announce("Wire selected. Backspace or Delete removes it.");
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
        `<div class="circuit-part ${p.type} ${selectedPart === p.id ? "selected-part" : ""}" role="group" tabindex="0" aria-label="${label(p.id)} component. Drag anywhere on its body to move." data-part="${p.id}" style="left:${p.x}px;top:${p.y}px"><button class="move-handle" data-move="${p.id}" aria-label="Move ${label(p.id)}. Drag the component body, or use arrow keys.">${label(p.id)} <span aria-hidden="true">⠿</span></button><button class="delete-part" data-delete="${p.id}" aria-label="Remove ${label(p.id)}">×</button>${symbol(p, r)}${terminals(
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
  $("#remove-wire").disabled = !selectedWire && !selectedPart;
  $("#cancel-wire").hidden = !pending;
  const selected = c.wires.find((w) => w.id === selectedWire);
  $("#wire-selection").textContent = selected
    ? `Selected: ${endLabel(selected.from)} ↔ ${endLabel(selected.to)}`
    : selectedPart
      ? `Selected: ${label(selectedPart)}. Backspace or Delete removes it and its attached wires.`
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
  $("#live-inputs").innerHTML = labs[index].switches.length
    ? `<span>ON THE BOARD NOW</span>${labs[index].switches
        .map((id) => {
          const p = c.parts.find((p) => p.id === id);
          return `<button data-live-toggle="${id}" ${!p ? "disabled" : ""} aria-pressed="${!!p?.closed}">${id}: <b>${!p ? "not added" : p.closed ? "closed" : "open"}</b></button>`;
        })
        .join("")}`
    : "<span>YOUR WIRES DETERMINE THE LAMP STATE</span>";
  bindRenderedParts();
  paintSelection();
}
function paintSelection() {
  if (!selectedWire) {
    $$(".wire-crossing, .wire-junction").forEach((el) =>
      el.classList.remove("selected", "under-selected"),
    );
  }
  $$("[data-part]").forEach((el) =>
    el.classList.toggle("selected-part", el.dataset.part === selectedPart),
  );
  $$("[data-wire]").forEach((el) =>
    el.classList.toggle("selected", el.dataset.wire === selectedWire),
  );
  $$("[data-port]").forEach((el) =>
    el.classList.toggle("pending", el.dataset.port === pending),
  );
  const button = $("#remove-wire");
  if (button) button.disabled = !selectedWire && !selectedPart;
  const wire = circuit().wires.find((w) => w.id === selectedWire),
    summary = $("#wire-selection");
  if (summary)
    summary.textContent = wire
      ? `Selected wire: ${endLabel(wire.from)} ↔ ${endLabel(wire.to)}. Backspace removes it.`
      : selectedPart
        ? `Selected ${label(selectedPart)}. Drag its body to move. Backspace removes it.`
        : "";
  if ($("#cancel-wire")) $("#cancel-wire").hidden = !pending;
}
function selectPart(id) {
  selectedPart = id;
  selectedWire = null;
  pending = null;
  paintSelection();
  announce(
    `${label(id)} selected. Drag its body to move it; Backspace or Delete removes it.`,
  );
}
function clearSelection() {
  const hadSelection = selectedPart || selectedWire || pending;
  selectedPart = null;
  selectedWire = null;
  pending = null;
  paintSelection();
  if (hadSelection)
    announce(
      "Selection cleared. Drag a component to move it, or drag between terminals to wire.",
    );
}
function connectWire(from, to) {
  if (from === to) {
    pending = null;
    paintSelection();
    return;
  }
  if (
    circuit().wires.some(
      (w) =>
        (w.from === from && w.to === to) || (w.from === to && w.to === from),
    )
  ) {
    pending = null;
    renderBoard();
    announce("Those terminals already have a wire.");
    return;
  }
  const id = "w" + crypto.randomUUID().slice(0, 8);
  mutate((c) => c.wires.push({ id, from, to }));
  selectedWire = id;
  selectedPart = null;
  renderBoard();
  $(`[data-port="${to}"]`)?.focus({ preventScroll: true });
  announce(
    `Connected ${endLabel(from)} to ${endLabel(to)}. Backspace removes the selected wire.`,
  );
}
function clickPort(port) {
  selectedPart = null;
  selectedWire = null;
  if (pending === port) {
    pending = null;
    paintSelection();
    announce("Wire cancelled.");
    return;
  }
  if (pending) {
    connectWire(pending, port);
    return;
  }
  pending = port;
  paintSelection();
  $(`[data-port="${port}"]`)?.focus({ preventScroll: true });
  announce(`Start: ${endLabel(port)}. Drag or click the other terminal.`);
}
function toggleSwitch(id, focusSelector) {
  const p = circuit().parts.find((p) => p.id === id);
  if (!p) return;
  clearSelection();
  p.closed = !p.closed;
  plannedCase = Math.max(0, currentCaseIndex(labs[index], circuit()));
  persist();
  renderBoard();
  renderEvidence();
  $(focusSelector || `[data-toggle="${id}"]`)?.focus({ preventScroll: true });
  announce(
    `${id} is now ${p.closed ? "closed" : "open"}. The live input row follows the board.`,
  );
}
function deletePart(id) {
  mutate((c) => {
    c.parts = c.parts.filter((p) => p.id !== id);
    c.wires = c.wires.filter(
      (w) => !w.from.startsWith(id + ".") && !w.to.startsWith(id + "."),
    );
  });
  announce(`${label(id)} and its attached wires removed.`);
  $("#circuit-canvas").focus({ preventScroll: true });
}
function removeSelection() {
  if (selectedWire) {
    const id = selectedWire;
    mutate((c) => (c.wires = c.wires.filter((w) => w.id !== id)));
    announce("Wire removed. Predict what changed, then test your circuit.");
    $("#circuit-canvas").focus({ preventScroll: true });
  } else if (selectedPart) deletePart(selectedPart);
}
function bindRenderedParts() {
  $$("[data-port]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        if (e.detail === 0) clickPort(b.dataset.port);
      }),
  );
  $$("[data-toggle]").forEach(
    (b) => (b.onclick = () => toggleSwitch(b.dataset.toggle)),
  );
  $$("[data-live-toggle]").forEach(
    (b) =>
      (b.onclick = () =>
        toggleSwitch(
          b.dataset.liveToggle,
          `[data-live-toggle="${b.dataset.liveToggle}"]`,
        )),
  );
  $$("[data-delete]").forEach(
    (b) => (b.onclick = () => deletePart(b.dataset.delete)),
  );
  $$("[data-move]").forEach(
    (b) =>
      (b.onclick = (e) => {
        if (e.detail === 0) selectPart(b.dataset.move);
      }),
  );
}
function experiment(row) {
  const observation = recordExperiment(labs[index], circuit(), evidence(), row);
  if (!observation) return;
  const { result: r, required, prediction, goalMet } = observation;
  const record = evidence().rows[row];
  delete evidence().predictions[row];
  persist();
  renderBoard();
  renderEvidence();
  $("#test-feedback").textContent =
    `Recorded ${setupName(record.config)}: predicted lamp ${prediction ? "On" : "Off"}, observed ${r.short ? "a short circuit" : !required ? "an incomplete setup" : r.on ? "On" : "Off"}. ${goalMet ? "Goal for this test met." : "Goal for this test not yet met."}${record.phase === "break" && !goalMet && r.state === "off" ? " Remove exactly one wire from the loop you recorded working." : ""}`;
  $("[data-draft]")?.focus({ preventScroll: true });
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
    fp = fingerprint(circuit());
  const currentCase = currentCaseIndex(l, circuit());
  $("#goal-rules").innerHTML = goalMarkup(l, e);
  $("#test-controls").innerHTML = testControlsMarkup({
    lab: l,
    evidence: e,
    plannedCase,
    currentCase,
  });
  $("#experiment-table").innerHTML = evidenceMarkup({
    lab: l,
    evidence: e,
    fingerprint: fp,
    currentCase,
    plannedCase,
  });
  $$("[data-case]").forEach(
    (b) =>
      (b.onclick = () => {
        plannedCase = Number(b.dataset.case);
        renderEvidence();
        $(`[data-case="${plannedCase}"]`)?.focus({ preventScroll: true });
      }),
  );
  $$("[data-draft]").forEach(
    (b) =>
      (b.onclick = () => {
        const value = b.dataset.draft;
        e.predictions[plannedCase] = value === "true";
        persist();
        renderEvidence();
        $(`[data-draft="${value}"]`).focus({ preventScroll: true });
      }),
  );
  $("#apply-test").onclick = () => experiment(plannedCase);
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
  boardController?.dispose();
  boardController = null;
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
  selectedPart = null;
  plannedCase = null;
  undo = [];
  redo = [];
  message = "";
  render();
  persist();
}
document.addEventListener("keydown", (event) => {
  if (isTextEditing(event.target) || $("#help-dialog").open) return;
  const inBench =
    !!event.target.closest?.(".bench") ||
    event.target === document.body ||
    event.target === document.documentElement;
  if (!inBench) return;
  if (event.key === "Escape") {
    boardController?.cancel();
    clearSelection();
    renderBoard();
    $("#circuit-canvas").focus({ preventScroll: true });
    return;
  }
  if (
    (event.metaKey || event.ctrlKey) &&
    !event.altKey &&
    event.key.toLowerCase() === "z"
  ) {
    event.preventDefault();
    $(event.shiftKey ? "#redo-edit" : "#undo-edit").click();
    return;
  }
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === "Backspace" || event.key === "Delete") {
    if (boardController?.cancel()) {
      event.preventDefault();
      clearSelection();
      return;
    }
    if (pending) {
      event.preventDefault();
      pending = null;
      renderBoard();
      announce("Wire cancelled.");
      return;
    }
    if (selectedWire || selectedPart) {
      event.preventDefault();
      removeSelection();
    }
    return;
  }
  const directions = {
    ArrowLeft: [-10, 0],
    ArrowRight: [10, 0],
    ArrowUp: [0, -10],
    ArrowDown: [0, 10],
  };
  if (
    !directions[event.key] ||
    !event.target.matches?.("[data-part], [data-move]")
  )
    return;
  const id = event.target.closest("[data-part]").dataset.part,
    p = circuit().parts.find((p) => p.id === id),
    [dx, dy] = directions[event.key];
  event.preventDefault();
  selectPart(id);
  recordEdit(clone(circuit()));
  Object.assign(p, constrainPartPosition(p.x + dx, p.y + dy));
  persist();
  renderBoard();
  $(`[data-part="${id}"]`).focus({ preventScroll: true });
});
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
