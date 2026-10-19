// Visual layout only. Connectivity is determined exclusively by wire endpoints.
import { WIDTH, HEIGHT } from "./workbench-geometry.mjs";

export function routeWires(circuit, width = WIDTH, height = HEIGHT) {
  const step = 10,
    cols = Math.floor(width / step),
    rows = Math.floor(height / step),
    occupied = new Set();
  const pos = (port) => {
    const [id, t] = port.split("."),
      p = circuit.parts.find((p) => p.id === id);
    return p
      ? {
          x: p.x + (t === "p" || t === "b" ? 150 : 0),
          y: p.y + 50,
          dir: t === "p" || t === "b" ? 1 : -1,
        }
      : null;
  };
  const key = (x, y) => y * cols + x;
  const blocked = (x, y) => {
    const px = x * step,
      py = y * step;
    return circuit.parts.some(
      (p) => px > p.x - 18 && px < p.x + 168 && py > p.y - 25 && py < p.y + 126,
    );
  };
  const paths = new Map();
  for (const wire of circuit.wires) {
    const a = pos(wire.from),
      b = pos(wire.to);
    if (!a || !b) {
      paths.set(wire.id, "");
      continue;
    }
    const sx = Math.max(
        1,
        Math.min(cols - 2, Math.round((a.x + a.dir * 34) / step)),
      ),
      sy = Math.round(a.y / step),
      tx = Math.max(
        1,
        Math.min(cols - 2, Math.round((b.x + b.dir * 34) / step)),
      ),
      ty = Math.round(b.y / step);
    const start = key(sx, sy),
      goal = key(tx, ty),
      g = new Map([[start, 0]]),
      previous = new Map(),
      heap = [];
    const push = (v) => {
      heap.push(v);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p].f <= v.f) break;
        heap[i] = heap[p];
        i = p;
      }
      heap[i] = v;
    };
    const pop = () => {
      const first = heap[0],
        last = heap.pop();
      if (heap.length) {
        let i = 0;
        while (i * 2 + 1 < heap.length) {
          let j = i * 2 + 1;
          if (j + 1 < heap.length && heap[j + 1].f < heap[j].f) j++;
          if (heap[j].f >= last.f) break;
          heap[i] = heap[j];
          i = j;
        }
        heap[i] = last;
      }
      return first;
    };
    push({ id: start, x: sx, y: sy, f: 0, cost: 0 });
    let found = false;
    while (heap.length) {
      const n = pop();
      if (n.cost !== g.get(n.id)) continue;
      if (n.id === goal) {
        found = true;
        break;
      }
      for (const [dx, dy] of [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ]) {
        const x = n.x + dx,
          y = n.y + dy;
        if (x < 1 || x >= cols - 1 || y < 2 || y >= rows - 1) continue;
        const id = key(x, y);
        if (id !== goal && id !== start && blocked(x, y)) continue;
        const cost = n.cost + 1 + (occupied.has(id) ? 4 : 0);
        if (cost >= (g.get(id) ?? Infinity)) continue;
        g.set(id, cost);
        previous.set(id, n.id);
        push({ id, x, y, cost, f: cost + Math.abs(x - tx) + Math.abs(y - ty) });
      }
    }
    let points = [];
    if (found) {
      let n = goal;
      while (n !== undefined) {
        points.unshift({
          x: (n % cols) * step,
          y: Math.floor(n / cols) * step,
        });
        occupied.add(n);
        n = previous.get(n);
      }
    } else
      points = [
        { x: a.x + a.dir * 34, y: a.y },
        { x: a.x + a.dir * 34, y: 20 },
        { x: b.x + b.dir * 34, y: 20 },
        { x: b.x + b.dir * 34, y: b.y },
      ];
    // Exact horizontal leads keep the visual wires attached to their actual terminals.
    points = [
      a,
      { x: points[0].x, y: a.y },
      ...points,
      { x: points.at(-1).x, y: b.y },
      b,
    ];
    const clean = points.filter(
      (p, i) => i === 0 || p.x !== points[i - 1].x || p.y !== points[i - 1].y,
    );
    const simplified = clean.filter(
      (p, i) =>
        i === 0 ||
        i === clean.length - 1 ||
        !(
          (clean[i - 1].x === p.x && p.x === clean[i + 1].x) ||
          (clean[i - 1].y === p.y && p.y === clean[i + 1].y)
        ),
    );
    paths.set(
      wire.id,
      simplified.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" "),
    );
  }
  return paths;
}
