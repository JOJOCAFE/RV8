import assert from "node:assert/strict";
import { test } from "node:test";
import { labs } from "./dist/lab-course.mjs";
import { constrainPartPosition } from "./dist/workbench-geometry.mjs";
import { fingerprint } from "./dist/wiring-engine.mjs";
import {
  newEvidence,
  newNotebook,
  recordExperiment,
  designProven,
  restoreNotebook,
  nextTestGoal,
  currentCaseIndex,
  recordedRowsForCircuit,
} from "./dist/learning-state.mjs";
import { evidenceMarkup } from "./dist/workbench-view.mjs";

const positions = {
  BAT: [75, 230],
  L: [625, 80],
  A: [330, 230],
  B: [330, 65],
  C: [610, 290],
};
function circuit(wires, switches = []) {
  return {
    parts: ["BAT", "L", ...switches].map((id) => ({
      id,
      type: id === "BAT" ? "battery" : id === "L" ? "lamp" : "switch",
      x: positions[id][0],
      y: positions[id][1],
      closed: false,
    })),
    wires: wires.map(([from, to], i) => ({ id: "wire" + i, from, to })),
  };
}
const loop = () =>
  circuit([
    ["BAT.p", "L.a"],
    ["L.b", "BAT.n"],
  ]);
const control = () =>
  circuit(
    [
      ["BAT.p", "A.a"],
      ["A.b", "L.a"],
      ["L.b", "BAT.n"],
    ],
    ["A"],
  );
const both = () =>
  circuit(
    [
      ["BAT.p", "A.a"],
      ["A.b", "B.a"],
      ["B.b", "L.a"],
      ["L.b", "BAT.n"],
    ],
    ["A", "B"],
  );
function run(lab, c, e, row, prediction) {
  e.predictions[row] = prediction;
  return recordExperiment(lab, c, e, row);
}
function completeLoop() {
  const c = loop(),
    e = newEvidence();
  run(labs[0], c, e, 0, true);
  const wire = c.wires.pop();
  run(labs[0], c, e, 0, false);
  c.wires.push(wire);
  run(labs[0], c, e, 0, true);
  e.reflection = 1;
  return { c, e };
}

test("a prediction is required and testing never changes wiring", () => {
  const c = control(),
    e = newEvidence(),
    before = JSON.stringify(c);
  assert.equal(recordExperiment(labs[1], c, e, 0), null);
  assert.equal(JSON.stringify(c), before);
  const fp = fingerprint(c);
  run(labs[1], c, e, 1, true);
  assert.equal(fingerprint(c), fp);
  assert.equal(c.parts.find((p) => p.id === "A").closed, true);
});
test("missing required switch cannot earn evidence for its goal", () => {
  const c = loop(),
    e = newEvidence();
  run(labs[1], c, e, 0, false);
  run(labs[1], c, e, 1, true);
  assert.equal(e.rows[1].valid, false);
  assert.equal(designProven(labs[1], c, e), false);
});
test("an incorrect prediction is preserved as useful evidence", () => {
  const c = control(),
    e = newEvidence();
  run(labs[1], c, e, 0, true);
  run(labs[1], c, e, 1, false);
  assert.equal(e.history[0].prediction, true);
  assert.equal(e.history[0].on, false);
  assert(designProven(labs[1], c, e));
});
test("draft predictions cannot rewrite the prediction paired with an observation", () => {
  const c = control(),
    e = newEvidence();
  run(labs[1], c, e, 0, true);
  const record = structuredClone(e.rows[0]);
  e.predictions[0] = false;
  const view = evidenceMarkup({
    lab: labs[1],
    evidence: e,
    fingerprint: fingerprint(c),
    currentCase: 0,
    plannedCase: 0,
  });
  assert.deepEqual(e.rows[0], record);
  assert.equal(e.history[0].prediction, true);
  assert.match(view, /data-label="Recorded prediction">Lamp On/);
  assert.match(view, /Prediction differed/);
  assert.match(view, /✓ Goal met/);
});
test("the required break has an Off goal and must remove exactly one wire", () => {
  const c = loop(),
    e = newEvidence();
  assert.equal(nextTestGoal(labs[0], e).target, true);
  run(labs[0], c, e, 0, true);
  assert.deepEqual(nextTestGoal(labs[0], e), {
    phase: "break",
    title: "Remove exactly one wire",
    target: false,
  });
  const wires = c.wires;
  c.wires = [];
  assert.equal(run(labs[0], c, e, 0, false).goalMet, false);
  c.wires = wires.slice(0, 1);
  assert.equal(run(labs[0], c, e, 0, false).goalMet, true);
  assert.equal(e.rows[0].target, false);
  assert.equal(e.rows[0].phase, "break");
  assert.equal(nextTestGoal(labs[0], e).phase, "repair");
  c.wires = wires;
  assert.equal(run(labs[0], c, e, 0, true).goalMet, true);
  assert.deepEqual(
    e.history.map((r) => r.phase),
    ["build", "break", "break", "repair"],
  );
});
test("live inputs follow actual switch contacts, independent of next test predictions", () => {
  const c = both(),
    e = newEvidence();
  assert.equal(currentCaseIndex(labs[2], c), 0);
  e.predictions[3] = true;
  assert.equal(currentCaseIndex(labs[2], c), 0);
  run(labs[2], c, e, 3, true);
  assert.equal(currentCaseIndex(labs[2], c), 3);
  c.parts.find((p) => p.id === "A").closed = false;
  assert.equal(currentCaseIndex(labs[2], c), 1);
  c.parts = c.parts.filter((p) => p.id !== "B");
  assert.equal(currentCaseIndex(labs[2], c), -1);
});
test("undo restores evidence only for the matching wiring and recorded input case", () => {
  const c = control(),
    e = newEvidence();
  run(labs[1], c, e, 0, false);
  run(labs[1], c, e, 1, true);
  const original = structuredClone(c);
  c.wires.pop();
  e.rows = recordedRowsForCircuit(labs[1], c, e);
  assert.deepEqual(e.rows, {});
  e.rows = recordedRowsForCircuit(labs[1], original, e);
  assert.deepEqual(Object.keys(e.rows), ["0", "1"]);
  assert(designProven(labs[1], original, e));
  original.parts[0].x += 10;
  assert.deepEqual(recordedRowsForCircuit(labs[1], original, e), e.rows);
});
test("lighting the lamp alone is not enough; a controlled break and repair is required", () => {
  const c = loop(),
    e = newEvidence();
  run(labs[0], c, e, 0, true);
  assert.equal(designProven(labs[0], c, e), false);
  const wire = c.wires.pop();
  run(labs[0], c, e, 0, false);
  assert(e.proof.broken);
  assert.equal(e.proof.repaired, false);
  c.wires.push(wire);
  run(labs[0], c, e, 0, true);
  assert(designProven(labs[0], c, e));
});
test("removing two connections or shorting the source does not count as the one-wire experiment", () => {
  const c = loop(),
    e = newEvidence();
  run(labs[0], c, e, 0, true);
  c.wires = [];
  run(labs[0], c, e, 0, false);
  assert.equal(e.proof.broken, false);
  c.wires.push({ id: "short", from: "BAT.p", to: "BAT.n" });
  run(labs[0], c, e, 0, false);
  assert.equal(e.proof.broken, false);
  assert.equal(e.rows[0].valid, false);
});
test("all four switch settings are required on a single version of the design", () => {
  const c = both(),
    e = newEvidence();
  [false, false, false, true].forEach((p, i) => run(labs[2], c, e, i, p));
  assert(designProven(labs[2], c, e));
  const wire = c.wires.pop();
  assert.equal(designProven(labs[2], c, e), false);
  c.wires.push(wire);
  delete e.rows[1];
  assert.equal(designProven(labs[2], c, e), false);
});
test("assessment recomputes the actual circuit and does not trust saved target flags", () => {
  const c = both(),
    e = newEvidence();
  [false, false, false, true].forEach((p, i) => run(labs[2], c, e, i, p));
  c.wires.push({ id: "bypass", from: "A.a", to: "A.b" });
  for (const record of Object.values(e.rows)) {
    record.fingerprint = fingerprint(c);
    record.target = record.on;
  }
  assert.equal(designProven(labs[2], c, e), false);
});
test("evidence cannot be moved to a different input row", () => {
  const c = both(),
    e = newEvidence();
  [false, false, false, true].forEach((p, i) => run(labs[2], c, e, i, p));
  e.rows[0] = structuredClone(e.rows[1]);
  assert.equal(designProven(labs[2], c, e), false);
});
test("a valid notebook restores wiring, observations, completion, and the learner’s explanation", () => {
  const { c, e } = completeLoop(),
    saved = newNotebook();
  e.note = "One missing connection interrupts the route.";
  saved.circuits.loop = c;
  saved.evidence.loop = e;
  saved.done = ["loop"];
  const restored = restoreNotebook(JSON.stringify(saved));
  assert.equal(restored.recovered, false);
  assert.deepEqual(restored.notebook, saved);
  assert(
    designProven(
      labs[0],
      restored.notebook.circuits.loop,
      restored.notebook.evidence.loop,
    ),
  );
});
test("notebooks from before phase-specific evidence retain their circuit and progress", () => {
  const { c, e } = completeLoop(),
    saved = newNotebook();
  for (const r of e.history) {
    delete r.phase;
    r.target = true;
  }
  saved.circuits.loop = c;
  saved.evidence.loop = e;
  saved.done = ["loop"];
  const restored = restoreNotebook(JSON.stringify(saved));
  assert.equal(restored.recovered, false);
  assert.deepEqual(restored.notebook.circuits.loop, c);
  assert.deepEqual(restored.notebook.done, ["loop"]);
  const evidence = restored.notebook.evidence.loop;
  assert(designProven(labs[0], c, evidence));
  const view = evidenceMarkup({
    lab: labs[0],
    evidence,
    fingerprint: fingerprint(c),
    currentCase: 0,
    plannedCase: 0,
  });
  assert.match(view, /Earlier session/);
  assert.doesNotMatch(view, /Prediction differed/);
});
test("invalid JSON and malformed top-level storage recover to an empty notebook", () => {
  for (const raw of [
    "{",
    "null",
    "[]",
    "{}",
    '{"circuits":[],"evidence":{},"done":[]}',
  ]) {
    const restored = restoreNotebook(raw);
    assert(restored.recovered);
    assert.deepEqual(restored.notebook, newNotebook());
  }
  assert.equal(restoreNotebook(null).recovered, false);
});
test("malformed circuits cannot crash or inject identifiers into the rendered board", () => {
  for (const corrupt of [
    (c) => {
      c.parts[0].id = "<script>";
    },
    (c) => {
      c.parts[0].x = null;
    },
    (c) => {
      c.parts[0].y = 999;
    },
    (c) => {
      c.parts[0].closed = "false";
    },
    (c) => c.parts.push({ ...c.parts[0] }),
    (c) => {
      c.wires[0].to = "missing.a";
    },
    (c) => {
      c.wires[0].id = "invalid id";
    },
    (c) => c.wires.push({ ...c.wires[0], id: "duplicate" }),
  ]) {
    const saved = newNotebook();
    saved.circuits.loop = loop();
    saved.evidence.loop = newEvidence();
    corrupt(saved.circuits.loop);
    const restored = restoreNotebook(JSON.stringify(saved));
    assert(restored.recovered);
    assert.equal(restored.notebook.circuits.loop, undefined);
  }
});
test("partial evidence is repaired without discarding the valid circuit", () => {
  const saved = newNotebook();
  saved.circuits.loop = loop();
  saved.evidence.loop = {
    note: "Keep this observation.",
    predictions: { 0: true },
    history: [{ config: { unexpected: "<b>" } }],
  };
  const e = restoreNotebook(JSON.stringify(saved)).notebook.evidence.loop;
  assert.equal(e.note, "Keep this observation.");
  assert.deepEqual(e.history, []);
  assert.equal(e.predictions[0], true);
  assert.equal(e.proof.repaired, false);
});
test("completion is restored only as a consecutive sequence with saved work", () => {
  const saved = newNotebook();
  saved.circuits.loop = loop();
  saved.evidence.loop = newEvidence();
  saved.done = ["loop", "either", "transfer"];
  assert.deepEqual(restoreNotebook(JSON.stringify(saved)).notebook.done, [
    "loop",
  ]);
});
test("the notebook keeps the most recent forty observations", () => {
  const c = control(),
    e = newEvidence();
  for (let i = 0; i < 45; i++) run(labs[1], c, e, i % 2, !!(i % 2));
  assert.equal(e.history.length, 40);
});

test("snapped placements at all board edges remain valid after a reload", () => {
  for (const x of [-10000, 24, 25, 75, 704, 10000]) {
    for (const y of [-10000, 28, 29, 80, 300, 10000]) {
      const position = constrainPartPosition(x, y, { snap: true });
      assert(position.x >= 24 && position.x <= 704);
      assert(position.y >= 28 && position.y <= 300);
      const saved = newNotebook();
      saved.circuits.loop = loop();
      Object.assign(saved.circuits.loop.parts[0], position);
      saved.evidence.loop = newEvidence();
      const restored = restoreNotebook(JSON.stringify(saved));
      assert.equal(restored.recovered, false);
      assert.equal(restored.notebook.circuits.loop.parts.length, 2);
    }
  }
  assert.deepEqual(constrainPartPosition(-100, -100, { snap: true }), {
    x: 24,
    y: 28,
  });
});
