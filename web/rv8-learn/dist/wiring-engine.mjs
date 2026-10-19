// Topology model for one ideal source, one resistive lamp and ideal switches.
// No current/voltage magnitude or analogue/timing claims are made.
export const endpoint = (id, end) => `${id}.${end}`;
export function terminals(part) {
  return part.type === "battery" ? ["n", "p"] : ["a", "b"];
}
export function fingerprint(circuit) {
  return JSON.stringify({
    parts: circuit.parts.map((p) => [p.id, p.type]).sort(),
    wires: circuit.wires.map((w) => [w.from, w.to].sort()).sort(),
  });
}
export function simulate(circuit, overrides = {}) {
  const parent = new Map(),
    graph = new Map();
  const add = (p) => {
    parent.set(p, p);
    graph.set(p, []);
  };
  const find = (p) => {
    if (parent.get(p) !== p) parent.set(p, find(parent.get(p)));
    return parent.get(p);
  };
  const join = (a, b) => parent.set(find(a), find(b));
  const edge = (a, b, id) => {
    graph.get(a).push({ to: b, id });
    graph.get(b).push({ to: a, id });
  };
  for (const p of circuit.parts)
    for (const t of terminals(p)) add(endpoint(p.id, t));
  for (const w of circuit.wires) {
    if (!parent.has(w.from) || !parent.has(w.to)) continue;
    join(w.from, w.to);
    edge(w.from, w.to, w.id);
  }
  for (const p of circuit.parts)
    if (p.type === "switch" && (overrides[p.id] ?? p.closed)) {
      join(endpoint(p.id, "a"), endpoint(p.id, "b"));
      edge(endpoint(p.id, "a"), endpoint(p.id, "b"), `inside:${p.id}`);
    }
  const sources = circuit.parts.filter((p) => p.type === "battery"),
    lamps = circuit.parts.filter((p) => p.type === "lamp");
  if (sources.length !== 1 || lamps.length !== 1)
    return {
      state: "missing",
      on: false,
      short: false,
      path: [],
      message:
        sources.length !== 1
          ? "Add one battery to supply the circuit."
          : "Add one lamp so you can observe the circuit.",
    };
  const source = sources[0],
    lamp = lamps[0],
    pos = endpoint(source.id, "p"),
    neg = endpoint(source.id, "n"),
    left = endpoint(lamp.id, "a"),
    right = endpoint(lamp.id, "b");
  const path = (start, end) => {
    const queue = [start],
      prev = new Map([[start, null]]);
    for (let i = 0; i < queue.length; i++)
      for (const e of graph.get(queue[i]) || [])
        if (!prev.has(e.to)) {
          prev.set(e.to, { node: queue[i], id: e.id });
          queue.push(e.to);
        }
    if (!prev.has(end)) return [];
    const out = [];
    let node = end;
    while (prev.get(node)) {
      const e = prev.get(node);
      out.unshift({ from: e.node, to: node, id: e.id });
      node = e.node;
    }
    return out;
  };
  if (find(pos) === find(neg))
    return {
      state: "short",
      on: false,
      short: true,
      path: path(pos, neg),
      message:
        "Short circuit: + reaches − through wires or closed switches without going through the lamp. The model cuts power. Find and remove that bypass.",
    };
  const on =
    (find(left) === find(pos) && find(right) === find(neg)) ||
    (find(right) === find(pos) && find(left) === find(neg));
  if (on) {
    edge(left, right, `inside:${lamp.id}`);
    return {
      state: "on",
      on: true,
      short: false,
      path: path(pos, neg),
      message:
        "There is a continuous route from +, through the lamp, back to −. The lamp is on.",
    };
  }
  let message =
    "The route is incomplete. Follow it from +, through the lamp: where does it stop before reaching −?";
  if (find(left) === find(right))
    message =
      "Both lamp ends belong to the same connection. There is no difference between its ends, so it stays off.";
  return { state: "off", on: false, short: false, path: [], message };
}
export function configurations(ids) {
  return Array.from({ length: 2 ** ids.length }, (_, n) =>
    Object.fromEntries(
      ids.map((id, i) => [id, !!(n & (1 << (ids.length - 1 - i)))]),
    ),
  );
}
export function targetFor(kind, config) {
  if (kind === "loop") return true;
  if (kind === "control") return !!config.A;
  if (kind === "both") return !!config.A && !!config.B;
  if (kind === "either") return !!config.A || !!config.B;
  if (kind === "transfer") return (!!config.A && !!config.B) || !!config.C;
  throw Error("Unknown experiment");
}
