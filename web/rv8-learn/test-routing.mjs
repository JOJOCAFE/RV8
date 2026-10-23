import assert from "node:assert/strict";
import { test } from "node:test";
import { layoutWires, previewWirePaths } from "./dist/wire-routing.mjs";
import { fingerprint, simulate } from "./dist/wiring-engine.mjs";

const parts = () => [
  { id: "BAT", type: "battery", x: 75, y: 230, closed: false },
  { id: "L", type: "lamp", x: 625, y: 80, closed: false },
  { id: "A", type: "switch", x: 330, y: 230, closed: true },
  { id: "B", type: "switch", x: 330, y: 65, closed: true },
  { id: "C", type: "switch", x: 610, y: 290, closed: true },
];
const circuit = (pairs, placement = parts()) => ({
  parts: placement,
  wires: pairs.map(([from, to], i) => ({ id: "w" + i, from, to })),
});
const combined = () =>
  circuit([
    ["BAT.p", "A.a"],
    ["A.b", "B.a"],
    ["B.b", "L.a"],
    ["BAT.p", "C.a"],
    ["C.b", "L.a"],
    ["L.b", "BAT.n"],
  ]);
const compact = () =>
  circuit(
    [
      ["BAT.n", "B.b"],
      ["BAT.n", "A.b"],
      ["L.b", "B.a"],
      ["L.b", "A.a"],
      ["L.a", "BAT.p"],
    ],
    [
      { id: "BAT", type: "battery", x: 350, y: 40, closed: false },
      { id: "L", type: "lamp", x: 40, y: 60, closed: false },
      { id: "A", type: "switch", x: 190, y: 300, closed: true },
      { id: "B", type: "switch", x: 200, y: 200, closed: true },
    ],
  );
const crossingCircuit = () =>
  circuit([
    ["BAT.p", "L.a"],
    ["A.b", "B.a"],
    ["L.b", "BAT.n"],
    ["C.a", "A.a"],
  ]);
function endpoint(c, port) {
  const [id, end] = port.split("."),
    p = c.parts.find((p) => p.id === id);
  return { x: p.x + (["p", "b"].includes(end) ? 150 : 0), y: p.y + 50 };
}
function segments(layout) {
  return [...layout.points].flatMap(([id, points]) =>
    points
      .slice(1)
      .map((b, i) => ({ a: points[i], b, net: layout.nets.get(id) })),
  );
}
test("routes preserve terminal endpoints and connectivity while avoiding diagonal segments", () => {
  for (const c of [combined(), compact(), crossingCircuit()]) {
    const before = structuredClone(c),
      fp = fingerprint(c),
      result = simulate(c),
      layout = layoutWires(c);
    for (const w of c.wires) {
      const points = layout.points.get(w.id);
      assert.deepEqual({ x: points[0].x, y: points[0].y }, endpoint(c, w.from));
      assert.deepEqual(
        { x: points.at(-1).x, y: points.at(-1).y },
        endpoint(c, w.to),
      );
      for (let i = 1; i < points.length; i++)
        assert(
          points[i].x === points[i - 1].x || points[i].y === points[i - 1].y,
        );
    }
    assert.deepEqual(c, before);
    assert.equal(fingerprint(c), fp);
    assert.deepEqual(simulate(c), result);
  }
});
test("unconnected nets never share a drawn line segment", () => {
  for (const c of [combined(), compact(), crossingCircuit()]) {
    const all = segments(layoutWires(c));
    for (let i = 0; i < all.length; i++)
      for (const b of all.slice(i + 1)) {
        const a = all[i];
        if (a.net === b.net) continue;
        if (a.a.y === a.b.y && b.a.y === b.b.y && a.a.y === b.a.y)
          assert(
            Math.min(Math.max(a.a.x, a.b.x), Math.max(b.a.x, b.b.x)) <=
              Math.max(Math.min(a.a.x, a.b.x), Math.min(b.a.x, b.b.x)),
          );
        if (a.a.x === a.b.x && b.a.x === b.b.x && a.a.x === b.a.x)
          assert(
            Math.min(Math.max(a.a.y, a.b.y), Math.max(b.a.y, b.b.y)) <=
              Math.max(Math.min(a.a.y, a.b.y), Math.min(b.a.y, b.b.y)),
          );
      }
  }
});
test("compact parallel wiring uses joined trunks without unnecessary crossings or excessive bends", () => {
  const layout = layoutWires(compact());
  assert.equal(layout.crossings.length, 0);
  assert(layout.junctions.length >= 2);
  for (const points of layout.points.values())
    assert(points.length <= 6, "A wire has more than four bends");
  for (const j of layout.junctions)
    assert([...layout.nets.values()].includes(j.net));
});
test("unavoidable crossings carry explicit hop metadata for distinct nets", () => {
  const layout = layoutWires(crossingCircuit());
  assert(layout.crossings.length > 0);
  for (const c of layout.crossings) {
    assert.notEqual(c.horizontalNet, c.verticalNet);
    assert(
      c.horizontalWires.every((id) => layout.nets.get(id) === c.horizontalNet),
    );
    assert(
      c.verticalWires.every((id) => layout.nets.get(id) === c.verticalNet),
    );
    assert(!layout.junctions.some((j) => j.x === c.x && j.y === c.y));
  }
});
test("live drag tethers follow moved terminals without changing the wire graph", () => {
  const c = combined(),
    fp = fingerprint(c),
    before = previewWirePaths(c);
  c.parts.find((p) => p.id === "L").x -= 90;
  const after = previewWirePaths(c);
  assert.notEqual(after.get("w2"), before.get("w2"));
  assert.equal(after.get("w0"), before.get("w0"));
  assert.equal(fingerprint(c), fp);
});
test("crossing hops stay on straight segments across thirty component arrangements", () => {
  const slots = parts().map((p) => ({ x: p.x, y: p.y }));
  let crossings = 0;
  for (let k = 0; k < 30; k++) {
    const placement = [...slots];
    let seed = k + 91;
    for (let i = 4; i > 0; i--) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      const j = seed % (i + 1);
      [placement[i], placement[j]] = [placement[j], placement[i]];
    }
    const c = crossingCircuit();
    c.parts.forEach((p, i) => Object.assign(p, placement[i]));
    const layout = layoutWires(c);
    for (const crossing of layout.crossings) {
      crossings++;
      for (const id of [
        ...crossing.horizontalWires,
        ...crossing.verticalWires,
      ]) {
        const ps = layout.points.get(id);
        const straight = ps.some((b, i) => {
          if (!i) return false;
          const a = ps[i - 1];
          return a.x === b.x
            ? crossing.x === a.x &&
                crossing.y > Math.min(a.y, b.y) &&
                crossing.y < Math.max(a.y, b.y)
            : crossing.y === a.y &&
                crossing.x > Math.min(a.x, b.x) &&
                crossing.x < Math.max(a.x, b.x);
        });
        assert(straight, `Crossing landed on ${id}'s bend in arrangement ${k}`);
      }
    }
  }
  assert(crossings > 0);
});
test("routes leave clearance around switch buttons as well as the symbol", () => {
  const c = combined(),
    layout = layoutWires(c);
  for (const p of c.parts.filter((p) => p.type === "switch")) {
    const box = {
      left: p.x + 30,
      right: p.x + 120,
      top: p.y + 96,
      bottom: p.y + 136,
    };
    for (const { a, b } of segments(layout)) {
      const intersects =
        a.y === b.y
          ? a.y > box.top &&
            a.y < box.bottom &&
            Math.max(a.x, b.x) > box.left &&
            Math.min(a.x, b.x) < box.right
          : a.x > box.left &&
            a.x < box.right &&
            Math.max(a.y, b.y) > box.top &&
            Math.min(a.y, b.y) < box.bottom;
      assert.equal(intersects, false, `Wire crosses ${p.id}'s switch control`);
    }
  }
});
