import {
  configurations,
  fingerprint,
  simulate,
  targetFor,
  terminals,
} from "./wiring-engine.mjs";
import { labs } from "./lab-course.mjs";
import { constrainPartPosition } from "./workbench-geometry.mjs";

export const STORAGE_KEY = "rv8-wiring-workbook-v1";
export const newNotebook = () => ({ circuits: {}, evidence: {}, done: [] });
export const newEvidence = () => ({
  rows: {},
  predictions: {},
  history: [],
  hint: 0,
  reflection: null,
  note: "",
  proof: { lit: false, broken: false, repaired: false, litWires: [] },
});
const object = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const wireId = (value) =>
  typeof value === "string" && /^[a-zA-Z0-9_-]{1,64}$/.test(value);
const partId = (key) =>
  key === "battery" ? "BAT" : key === "lamp" ? "L" : key;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export function nextTestGoal(lab, evidence) {
  if (lab.id !== "loop") return null;
  if (!evidence.proof.lit)
    return { phase: "build", title: "Complete the loop", target: true };
  if (!evidence.proof.broken)
    return { phase: "break", title: "Remove exactly one wire", target: false };
  if (!evidence.proof.repaired)
    return { phase: "repair", title: "Repair the loop", target: true };
  return { phase: "explore", title: "Explore your circuit", target: true };
}

export function currentCaseIndex(lab, circuit) {
  return configurations(lab.switches).findIndex((config) =>
    lab.switches.every((id) => {
      const part = circuit.parts.find((p) => p.id === id);
      return part && part.closed === config[id];
    }),
  );
}

export function recordedRowsForCircuit(lab, circuit, evidence) {
  const fp = fingerprint(circuit),
    configs = configurations(lab.switches),
    rows = {};
  for (const record of evidence.history) {
    if (record.fingerprint !== fp) continue;
    const row = configs.findIndex(
      (config) => JSON.stringify(config) === JSON.stringify(record.config),
    );
    if (row >= 0) rows[row] = record;
  }
  return rows;
}

function validCircuit(circuit, lab) {
  if (
    !object(circuit) ||
    !Array.isArray(circuit.parts) ||
    !Array.isArray(circuit.wires)
  )
    return false;
  const allowed = new Map(
    lab.parts.map((key) => [
      partId(key),
      key === "battery" || key === "lamp" ? key : "switch",
    ]),
  );
  const ids = new Set(),
    ports = new Set(),
    wires = new Set(),
    connections = new Set();
  if (circuit.parts.length > allowed.size || circuit.wires.length > 45)
    return false;
  for (const p of circuit.parts) {
    if (
      !object(p) ||
      allowed.get(p.id) !== p.type ||
      ids.has(p.id) ||
      !Number.isFinite(p.x) ||
      !Number.isFinite(p.y) ||
      typeof p.closed !== "boolean"
    )
      return false;
    const position = constrainPartPosition(p.x, p.y);
    if (position.x !== p.x || position.y !== p.y) return false;
    ids.add(p.id);
    for (const terminal of terminals(p)) ports.add(`${p.id}.${terminal}`);
  }
  for (const w of circuit.wires) {
    if (
      !object(w) ||
      !wireId(w.id) ||
      wires.has(w.id) ||
      !ports.has(w.from) ||
      !ports.has(w.to) ||
      w.from === w.to
    )
      return false;
    const key = [w.from, w.to].sort().join("|");
    if (connections.has(key)) return false;
    wires.add(w.id);
    connections.add(key);
  }
  return true;
}

function cleanRecord(record, lab) {
  if (!object(record) || !object(record.config)) return null;
  if (
    Object.keys(record.config).length !== lab.switches.length ||
    !lab.switches.every((id) => typeof record.config[id] === "boolean")
  )
    return null;
  if (
    !["prediction", "on", "short", "valid"].every(
      (key) => typeof record[key] === "boolean",
    )
  )
    return null;
  if (
    typeof record.fingerprint !== "string" ||
    record.fingerprint.length > 10000
  )
    return null;
  const config = Object.fromEntries(
    lab.switches.map((id) => [id, record.config[id]]),
  );
  const phase =
    lab.id === "loop" &&
    ["build", "break", "repair", "explore"].includes(record.phase)
      ? record.phase
      : null;
  return {
    config,
    prediction: record.prediction,
    on: record.on,
    short: record.short,
    valid: record.valid,
    target: phase === "break" ? false : targetFor(lab.id, config),
    fingerprint: record.fingerprint,
    ...(phase ? { phase } : {}),
  };
}

// Browser storage is fallible. Reject malformed circuits before they reach the UI.
export function restoreNotebook(raw) {
  const notebook = newNotebook();
  if (raw === null) return { notebook, recovered: false };
  let saved;
  try {
    saved = JSON.parse(raw);
  } catch {
    return { notebook, recovered: true };
  }
  if (
    !object(saved) ||
    !object(saved.circuits) ||
    !object(saved.evidence) ||
    !Array.isArray(saved.done)
  )
    return { notebook, recovered: true };
  let recovered = false;
  for (const lab of labs) {
    if (!(lab.id in saved.circuits)) continue;
    const c = saved.circuits[lab.id];
    if (!validCircuit(c, lab)) {
      recovered = true;
      continue;
    }
    notebook.circuits[lab.id] = structuredClone(c);
    const e = newEvidence(),
      original = saved.evidence[lab.id];
    if (object(original)) {
      const configs = configurations(lab.switches);
      for (let i = 0; i < configs.length; i++) {
        if (typeof original.predictions?.[i] === "boolean")
          e.predictions[i] = original.predictions[i];
        const record = cleanRecord(original.rows?.[i], lab);
        if (
          record &&
          JSON.stringify(record.config) === JSON.stringify(configs[i])
        )
          e.rows[i] = record;
      }
      if (Array.isArray(original.history))
        e.history = original.history
          .map((r) => cleanRecord(r, lab))
          .filter(Boolean)
          .slice(-40);
      e.hint = Number.isInteger(original.hint)
        ? clamp(original.hint, 0, lab.hints.length)
        : 0;
      e.reflection =
        Number.isInteger(original.reflection) &&
        original.reflection >= 0 &&
        original.reflection < lab.answers.length
          ? original.reflection
          : null;
      e.note =
        typeof original.note === "string" ? original.note.slice(0, 20000) : "";
      if (object(original.proof)) {
        const ids = Array.isArray(original.proof.litWires)
          ? original.proof.litWires.filter(wireId).slice(0, 45)
          : [];
        const lit = original.proof.lit === true && ids.length > 0;
        const broken = lit && original.proof.broken === true;
        e.proof = {
          lit,
          broken,
          repaired: broken && original.proof.repaired === true,
          litWires: [...new Set(ids)],
        };
      }
    } else recovered = true;
    notebook.evidence[lab.id] = e;
  }
  // Only restore a consecutive set of completed experiments with their saved work.
  for (const lab of labs) {
    if (!saved.done.includes(lab.id) || !notebook.circuits[lab.id]) break;
    notebook.done.push(lab.id);
  }
  return { notebook, recovered };
}

export function recordExperiment(lab, circuit, evidence, row) {
  const config = configurations(lab.switches)[row],
    prediction = evidence.predictions[row];
  if (!config || typeof prediction !== "boolean") return null;
  for (const [id, closed] of Object.entries(config)) {
    const part = circuit.parts.find((p) => p.id === id);
    if (part) part.closed = closed;
  }
  const goal = nextTestGoal(lab, evidence);
  const result = simulate(circuit);
  const required = lab.parts.every((key) =>
    circuit.parts.some((p) => p.id === partId(key)),
  );
  const valid = required && result.state !== "missing" && !result.short;
  const record = {
    config,
    prediction,
    on: result.on,
    short: result.short,
    valid,
    target: goal ? goal.target : targetFor(lab.id, config),
    fingerprint: fingerprint(circuit),
    ...(goal ? { phase: goal.phase } : {}),
  };
  evidence.rows[row] = record;
  evidence.history.push(record);
  if (evidence.history.length > 40) evidence.history.shift();
  if (lab.id === "loop") {
    const p = evidence.proof;
    if (valid && result.on) {
      if (p.broken) p.repaired = true;
      p.lit = true;
      p.litWires = circuit.wires.map((w) => w.id);
    } else if (
      valid &&
      result.state === "off" &&
      p.lit &&
      circuit.wires.length === p.litWires.length - 1 &&
      circuit.wires.every((w) => p.litWires.includes(w.id))
    )
      p.broken = true;
  }
  const goalMet =
    valid &&
    result.on === record.target &&
    (goal?.phase !== "break" || evidence.proof.broken);
  return { result, required, prediction, goalMet };
}

export function designProven(lab, circuit, evidence) {
  const fp = fingerprint(circuit);
  return (
    configurations(lab.switches).every((config, i) => {
      const record = evidence.rows[i];
      if (
        !record ||
        !record.valid ||
        record.short ||
        record.fingerprint !== fp ||
        JSON.stringify(record.config) !== JSON.stringify(config)
      )
        return false;
      const result = simulate(circuit, config),
        target = targetFor(lab.id, config);
      return (
        result.state !== "missing" &&
        !result.short &&
        result.on === target &&
        record.on === target
      );
    }) &&
    lab.parts.every((key) => circuit.parts.some((p) => p.id === partId(key))) &&
    (lab.id !== "loop" || evidence.proof.repaired)
  );
}
