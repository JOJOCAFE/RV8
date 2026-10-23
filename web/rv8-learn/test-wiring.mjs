import assert from "node:assert/strict";
import {
  simulate,
  fingerprint,
  configurations,
  targetFor,
} from "./dist/wiring-engine.mjs";
import { test } from "node:test";
function circuit(wires, ids = []) {
  return {
    parts: [
      { id: "BAT", type: "battery" },
      { id: "L", type: "lamp" },
      ...ids.map((id) => ({ id, type: "switch", closed: false })),
    ],
    wires: wires.map(([from, to], i) => ({ id: "w" + i, from, to })),
  };
}
const loop = circuit([
  ["BAT.p", "L.a"],
  ["L.b", "BAT.n"],
]);
test("empty board and disconnected terminals do not light anything", () => {
  assert.equal(simulate({ parts: [], wires: [] }).state, "missing");
  assert.equal(simulate(circuit([])).on, false);
});
test("complete loop lights, reversed lamp polarity also lights", () => {
  assert(simulate(loop).on);
  assert(
    simulate(
      circuit([
        ["BAT.p", "L.b"],
        ["L.a", "BAT.n"],
      ]),
    ).on,
  );
});
test("one wire and both lamp ends at the same source terminal stay off", () => {
  assert(!simulate(circuit([["BAT.p", "L.a"]])).on);
  assert(
    !simulate(
      circuit([
        ["BAT.p", "L.a"],
        ["BAT.p", "L.b"],
      ]),
    ).on,
  );
});
test("remove and restore a wire changes the actual result", () => {
  const c = structuredClone(loop);
  const w = c.wires.pop();
  assert(!simulate(c).on);
  c.wires.push(w);
  assert(simulate(c).on);
});
test("short detection cuts power even with a lamp attached", () => {
  const c = structuredClone(loop);
  c.wires.push({ id: "bypass", from: "BAT.p", to: "BAT.n" });
  const r = simulate(c);
  assert(r.short);
  assert(!r.on);
  assert(r.path.some((e) => e.id === "bypass"));
});
const control = circuit(
  [
    ["BAT.p", "A.a"],
    ["A.b", "L.a"],
    ["L.b", "BAT.n"],
  ],
  ["A"],
);
test("open versus closed contact controls a complete route", () => {
  assert(!simulate(control, { A: false }).on);
  assert(simulate(control, { A: true }).on);
});
const both = circuit(
  [
    ["BAT.p", "A.a"],
    ["A.b", "B.a"],
    ["B.b", "L.a"],
    ["L.b", "BAT.n"],
  ],
  ["A", "B"],
);
const either = circuit(
  [
    ["BAT.p", "A.a"],
    ["A.b", "L.a"],
    ["BAT.p", "B.a"],
    ["B.b", "L.a"],
    ["L.b", "BAT.n"],
  ],
  ["A", "B"],
);
test("series wiring implements AND in all four settings", () => {
  for (const c of configurations(["A", "B"]))
    assert.equal(simulate(both, c).on, targetFor("both", c));
});
test("parallel wiring implements OR in all four settings", () => {
  for (const c of configurations(["A", "B"]))
    assert.equal(simulate(either, c).on, targetFor("either", c));
});
test("wrong wiring cannot pass the other rule’s full table", () => {
  assert(
    configurations(["A", "B"]).some(
      (c) => simulate(either, c).on !== targetFor("both", c),
    ),
  );
  assert(
    configurations(["A", "B"]).some(
      (c) => simulate(both, c).on !== targetFor("either", c),
    ),
  );
});
const transfer = circuit(
  [
    ["BAT.p", "A.a"],
    ["A.b", "B.a"],
    ["B.b", "L.a"],
    ["BAT.p", "C.a"],
    ["C.b", "L.a"],
    ["L.b", "BAT.n"],
  ],
  ["A", "B", "C"],
);
test("learner-composed (A AND B) OR C works in all eight settings", () => {
  for (const c of configurations(["A", "B", "C"]))
    assert.equal(simulate(transfer, c).on, targetFor("transfer", c));
});
test("a wire bypassing an open contact is modeled as a real alternative path", () => {
  const c = structuredClone(control);
  c.wires.push({ id: "bypass", from: "A.a", to: "A.b" });
  assert(simulate(c, { A: false }).on);
});
test("route trace traverses only actual wires, closed contacts and the filament", () => {
  const r = simulate(transfer, { A: false, B: false, C: true });
  assert(r.on);
  assert(r.path.some((e) => e.id === "inside:L"));
  assert(r.path.some((e) => e.id === "inside:C"));
  assert(!r.path.some((e) => e.id === "inside:A"));
  assert.equal(r.path[0].from, "BAT.p");
  assert.equal(r.path.at(-1).to, "BAT.n");
});
test("evidence fingerprint changes for rewiring, not for layout or input settings", () => {
  const c = structuredClone(control),
    fp = fingerprint(c);
  c.parts[0].x = 100;
  c.parts[2].closed = true;
  assert.equal(fingerprint(c), fp);
  c.wires.pop();
  assert.notEqual(fingerprint(c), fp);
});
test("all 64 source/lamp wire graphs agree with independent reachability", () => {
  const nodes = ["BAT.p", "BAT.n", "L.a", "L.b"],
    edges = [];
  for (let i = 0; i < 4; i++)
    for (let j = i + 1; j < 4; j++) edges.push([nodes[i], nodes[j]]);
  for (let mask = 0; mask < 64; mask++) {
    const wires = edges.filter((_, i) => mask & (1 << i));
    const reach = (a, b) => {
      const seen = new Set([a]),
        todo = [a];
      while (todo.length) {
        const n = todo.pop();
        for (const [x, y] of wires) {
          const other = x === n ? y : y === n ? x : null;
          if (other && !seen.has(other)) {
            seen.add(other);
            todo.push(other);
          }
        }
      }
      return seen.has(b);
    };
    const short = reach("BAT.p", "BAT.n");
    const lit =
      !short &&
      ((reach("BAT.p", "L.a") && reach("BAT.n", "L.b")) ||
        (reach("BAT.p", "L.b") && reach("BAT.n", "L.a")));
    const r = simulate(circuit(wires));
    assert.equal(r.short, short);
    assert.equal(r.on, lit);
  }
});
