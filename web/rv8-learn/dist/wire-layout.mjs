import { WIDTH, HEIGHT } from "./workbench-geometry.mjs";

// Route by electrical net: already-connected wires can share a trunk. Distinct
// nets may cross with a hop, but never silently overlap along a segment.
export function layoutWires(circuit, width = WIDTH, height = HEIGHT) {
  const step = 10,
    cols = Math.floor(width / step),
    rows = Math.floor(height / step);
  const parent = new Map(),
    horizontal = new Map(),
    vertical = new Map(),
    edges = new Map();
  const find = (id) => {
    if (!parent.has(id)) parent.set(id, id);
    if (parent.get(id) !== id) parent.set(id, find(parent.get(id)));
    return parent.get(id);
  };
  for (const w of circuit.wires) {
    const a = find(w.from),
      b = find(w.to);
    parent.set(a, b);
  }
  const nets = new Map();
  for (const w of circuit.wires) nets.set(w.id, find(w.from));
  const position = (port) => {
    const [id, end] = port.split("."),
      p = circuit.parts.find((p) => p.id === id);
    return p
      ? {
          x: p.x + (end === "p" || end === "b" ? 150 : 0),
          y: p.y + 50,
          dir: end === "p" || end === "b" ? 1 : -1,
        }
      : null;
  };
  const cell = (x, y) => y * cols + x;
  const edgeKey = (a, b) => (a < b ? `${a}:${b}` : `${b}:${a}`);
  // Reserve the exits before routing any wire. Otherwise a later wire's final
  // bend could land on an earlier route right beside its own terminal.
  const reserved = new Map();
  for (const port of new Set(circuit.wires.flatMap((w) => [w.from, w.to]))) {
    const p = position(port);
    if (!p) continue;
    const end = p.x + p.dir * 30,
      net = find(port);
    for (
      let x = Math.max(1, Math.floor((Math.min(p.x, end) - 8) / step));
      x < cols && x * step <= Math.max(p.x, end) + 8;
      x++
    )
      for (
        let y = Math.max(1, Math.floor((p.y - 8) / step));
        y < rows && y * step <= p.y + 8;
        y++
      ) {
        if (Math.abs(y * step - p.y) > 8) continue;
        const key = cell(x, y);
        if (!reserved.has(key)) reserved.set(key, new Set());
        reserved.get(key).add(net);
      }
  }
  const blocked = (x, y) =>
    circuit.parts.some((p) => {
      const px = x * step - p.x,
        py = y * step - p.y;
      if (px > -10 && px < 160 && py > 12 && py < 88) return true;
      if (px > 0 && px < 150 && py > -22 && py < 14) return true;
      if (p.type === "switch")
        return px > 20 && px < 130 && py > 86 && py < 146;
      if (p.type === "lamp") return px > 45 && px < 105 && py > 86 && py < 122;
      return px > 5 && px < 145 && py > 92 && py < 122;
    });
  const netCounts = new Map();
  for (const net of nets.values())
    netCounts.set(net, (netCounts.get(net) || 0) + 1);
  const ordered = [...circuit.wires].sort(
    (a, b) =>
      netCounts.get(nets.get(b.id)) - netCounts.get(nets.get(a.id)) ||
      [a.from, a.to].sort().join().localeCompare([b.from, b.to].sort().join()),
  );
  const paths = new Map(),
    pointsByWire = new Map();
  for (const wire of ordered) {
    const a = position(wire.from),
      b = position(wire.to),
      net = nets.get(wire.id);
    if (!a || !b) {
      paths.set(wire.id, "");
      continue;
    }
    const sx = Math.max(
        1,
        Math.min(cols - 1, Math.round((a.x + a.dir * 28) / step)),
      ),
      sy = Math.round(a.y / step);
    const tx = Math.max(
        1,
        Math.min(cols - 1, Math.round((b.x + b.dir * 28) / step)),
      ),
      ty = Math.round(b.y / step);
    const start = cell(sx, sy),
      goal = cell(tx, ty),
      initialDirection = a.dir === 1 ? 0 : 1;
    const costs = new Map(),
      previous = new Map(),
      states = new Map(),
      heap = [];
    const push = (value) => {
      heap.push(value);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p].f <= value.f) break;
        heap[i] = heap[p];
        i = p;
      }
      heap[i] = value;
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
    const first = {
      id: start * 4 + initialDirection,
      point: start,
      x: sx,
      y: sy,
      direction: initialDirection,
      cost: 0,
      f: 0,
    };
    costs.set(first.id, 0);
    states.set(first.id, first);
    push(first);
    let found = null;
    while (heap.length) {
      const node = pop();
      if (node.cost !== costs.get(node.id)) continue;
      if (node.point === goal) {
        found = node;
        break;
      }
      const onForeignWire = [horizontal, vertical].some((axis) =>
        [...(axis.get(node.point) || [])].some((other) => other !== net),
      );
      for (const [direction, [dx, dy]] of [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ].entries()) {
        // A crossing must pass straight through. Turning on another net's
        // corner would draw a misleading T-junction or an incomplete hop.
        if (onForeignWire && direction !== node.direction) continue;
        const x = node.x + dx,
          y = node.y + dy;
        if (x < 1 || x >= cols || y < 1 || y >= rows) continue;
        const point = cell(x, y),
          id = point * 4 + direction;
        if ([...(reserved.get(point) || [])].some((other) => other !== net))
          continue;
        if (point !== start && point !== goal && blocked(x, y)) continue;
        const edge = edgeKey(node.point, point),
          owner = edges.get(edge);
        if (owner && owner !== net) continue;
        const axis = direction < 2 ? horizontal : vertical,
          perpendicular = direction < 2 ? vertical : horizontal;
        const crossing = [...(perpendicular.get(point) || [])].some(
          (other) => other !== net,
        );
        const parallel = [...(axis.get(point) || [])].some(
          (other) => other !== net,
        );
        if (parallel) continue;
        const cost =
          node.cost +
          (owner === net ? 0.35 : 1) +
          (node.direction !== direction ? 8 : 0) +
          (crossing ? 45 : 0);
        if (cost >= (costs.get(id) ?? Infinity)) continue;
        const value = {
          id,
          point,
          x,
          y,
          direction,
          cost,
          f: cost + 0.35 * (Math.abs(x - tx) + Math.abs(y - ty)),
        };
        costs.set(id, cost);
        previous.set(id, node.id);
        states.set(id, value);
        push(value);
      }
    }
    let points = [];
    if (found) {
      const route = [];
      let id = found.id;
      while (id !== undefined) {
        route.unshift(states.get(id));
        id = previous.get(id);
      }
      for (let i = 1; i < route.length; i++) {
        const p = route[i - 1],
          q = route[i],
          axis = p.y === q.y ? horizontal : vertical;
        edges.set(edgeKey(p.point, q.point), net);
        for (const node of [p, q]) {
          if (!axis.has(node.point)) axis.set(node.point, new Set());
          axis.get(node.point).add(net);
        }
      }
      points = route.map((p) => ({ x: p.x * step, y: p.y * step }));
    } else {
      // Overlapping parts can block the grid. Keep the connection visible with
      // a simple perimeter route; moving the parts apart restores clean routing.
      points = [
        { x: sx * step, y: a.y },
        { x: sx * step, y: 10 },
        { x: tx * step, y: 10 },
        { x: tx * step, y: b.y },
      ];
    }
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
    pointsByWire.set(wire.id, simplified);
    paths.set(
      wire.id,
      simplified.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" "),
    );
  }
  const segments = [];
  for (const [id, points] of pointsByWire)
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1],
        b = points[i];
      if (a.x === b.x || a.y === b.y)
        segments.push({ a, b, id, net: nets.get(id), horizontal: a.y === b.y });
    }
  const candidates = new Map(),
    crossings = new Map();
  const addCandidate = (p) => candidates.set(`${p.x},${p.y}`, p);
  for (const points of pointsByWire.values()) points.forEach(addCandidate);
  for (const h of segments.filter((s) => s.horizontal))
    for (const v of segments.filter((s) => !s.horizontal)) {
      const x = v.a.x,
        y = h.a.y;
      if (
        x < Math.min(h.a.x, h.b.x) ||
        x > Math.max(h.a.x, h.b.x) ||
        y < Math.min(v.a.y, v.b.y) ||
        y > Math.max(v.a.y, v.b.y)
      )
        continue;
      const p = { x, y };
      addCandidate(p);
      if (h.net !== v.net) {
        const key = `${x},${y}:${h.net}:${v.net}`;
        if (!crossings.has(key))
          crossings.set(key, {
            x,
            y,
            horizontalNet: h.net,
            verticalNet: v.net,
            horizontalWires: [],
            verticalWires: [],
          });
        const crossing = crossings.get(key);
        if (!crossing.horizontalWires.includes(h.id))
          crossing.horizontalWires.push(h.id);
        if (!crossing.verticalWires.includes(v.id))
          crossing.verticalWires.push(v.id);
      }
    }
  const ports = circuit.parts.flatMap((p) =>
    (p.type === "battery" ? ["n", "p"] : ["a", "b"]).map((end) =>
      position(`${p.id}.${end}`),
    ),
  );
  const junctions = [];
  for (const p of candidates.values()) {
    if (ports.some((port) => Math.hypot(port.x - p.x, port.y - p.y) < 11))
      continue;
    const directions = new Map();
    for (const s of segments) {
      const hit = s.horizontal
        ? p.y === s.a.y &&
          p.x >= Math.min(s.a.x, s.b.x) &&
          p.x <= Math.max(s.a.x, s.b.x)
        : p.x === s.a.x &&
          p.y >= Math.min(s.a.y, s.b.y) &&
          p.y <= Math.max(s.a.y, s.b.y);
      if (!hit) continue;
      if (!directions.has(s.net)) directions.set(s.net, new Set());
      const d = directions.get(s.net);
      if (s.horizontal) {
        if (p.x > Math.min(s.a.x, s.b.x)) d.add("left");
        if (p.x < Math.max(s.a.x, s.b.x)) d.add("right");
      } else {
        if (p.y > Math.min(s.a.y, s.b.y)) d.add("up");
        if (p.y < Math.max(s.a.y, s.b.y)) d.add("down");
      }
    }
    for (const [net, d] of directions)
      if (d.size >= 3) junctions.push({ ...p, net });
  }
  return {
    paths,
    nets,
    crossings: [...crossings.values()],
    junctions,
    points: pointsByWire,
  };
}

export function routeWires(circuit, width = WIDTH, height = HEIGHT) {
  return layoutWires(circuit, width, height).paths;
}

// While a component is moving, tether the endpoints cheaply. Full obstacle-
// aware routing happens on release, keeping pointer movement responsive.
export function previewWirePaths(circuit) {
  const port = (value) => {
    const [id, end] = value.split("."),
      p = circuit.parts.find((p) => p.id === id);
    return p
      ? { x: p.x + (end === "p" || end === "b" ? 150 : 0), y: p.y + 50 }
      : null;
  };
  return new Map(
    circuit.wires.map((w) => {
      const a = port(w.from),
        b = port(w.to);
      if (!a || !b) return [w.id, ""];
      const mid = (a.x + b.x) / 2;
      return [w.id, `M${a.x},${a.y}L${mid},${a.y}L${mid},${b.y}L${b.x},${b.y}`];
    }),
  );
}
