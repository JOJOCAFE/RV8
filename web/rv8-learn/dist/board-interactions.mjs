import { constrainPartPosition } from "./workbench-geometry.mjs";

// Pointer capture belongs to the stable canvas, not a label or rebuilt terminal.
export function attachBoardInteractions(canvas, callbacks) {
  let active = null,
    frame = null;
  const scroll = canvas.parentElement;
  const local = (x, y) => {
    const r = canvas.getBoundingClientRect();
    return { x: x - r.left, y: y - r.top };
  };
  function targetAt(x, y, from) {
    const direct = document.elementFromPoint(x, y)?.closest("[data-port]");
    if (direct && canvas.contains(direct) && direct.dataset.port !== from)
      return direct;
    let best = null,
      distance = active?.pointerType === "touch" ? 32 : 25;
    const viewport = scroll.getBoundingClientRect();
    for (const button of canvas.querySelectorAll("[data-port]")) {
      if (button.dataset.port === from) continue;
      const r = button.getBoundingClientRect(),
        d = Math.hypot(x - r.left - r.width / 2, y - r.top - r.height / 2);
      if (
        r.right < viewport.left ||
        r.left > viewport.right ||
        r.bottom < 0 ||
        r.top > innerHeight
      )
        continue;
      if (d < distance) {
        best = button;
        distance = d;
      }
    }
    return best;
  }
  function clearPreview() {
    canvas.querySelector(".draft-wire")?.remove();
    canvas
      .querySelectorAll(".snap-target, .wire-source")
      .forEach((el) => el.classList.remove("snap-target", "wire-source"));
    canvas.classList.remove("drawing-wire", "moving-part");
  }
  function previewWire() {
    const source = canvas.querySelector(`[data-port="${active.from}"]`);
    if (!source) return;
    const start = source.getBoundingClientRect(),
      target = targetAt(active.clientX, active.clientY, active.from);
    const a = local(start.left + start.width / 2, start.top + start.height / 2);
    const tr = target?.getBoundingClientRect();
    const b = tr
      ? local(tr.left + tr.width / 2, tr.top + tr.height / 2)
      : local(active.clientX, active.clientY);
    let path = canvas.querySelector(".draft-wire");
    if (!path) {
      path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.classList.add("draft-wire");
      canvas.querySelector("#wire-layer").append(path);
    }
    const direction = /\.(p|b)$/.test(active.from) ? 1 : -1,
      reach = Math.max(35, Math.abs(b.x - a.x) / 2);
    path.setAttribute(
      "d",
      `M${a.x},${a.y} C${a.x + direction * reach},${a.y} ${b.x - direction * reach},${b.y} ${b.x},${b.y}`,
    );
    canvas
      .querySelectorAll(".snap-target")
      .forEach((el) => el.classList.remove("snap-target"));
    target?.classList.add("snap-target");
    source.classList.add("wire-source");
    canvas.classList.add("drawing-wire");
  }
  function update() {
    if (!active?.moved) return;
    if (active.kind === "wire") previewWire();
    else {
      const point = local(active.clientX, active.clientY);
      callbacks.movePart(
        active.id,
        constrainPartPosition(
          active.x + point.x - active.start.x,
          active.y + point.y - active.start.y,
          { snap: true },
        ),
      );
      canvas.classList.add("moving-part");
    }
  }
  function autoPan() {
    if (!active?.moved) {
      frame = null;
      return;
    }
    const r = scroll.getBoundingClientRect(),
      margin = 36,
      snapped =
        active.kind === "wire" &&
        targetAt(active.clientX, active.clientY, active.from);
    const dx = snapped
      ? 0
      : active.clientX < r.left + margin
        ? -8
        : active.clientX > r.right - margin
          ? 8
          : 0;
    const dy = snapped
      ? 0
      : active.clientY < 28
        ? -12
        : active.clientY > innerHeight - 28
          ? 12
          : 0;
    if (dx) scroll.scrollLeft += dx;
    if (dy) window.scrollBy(0, dy);
    if (dx || dy) update();
    frame = requestAnimationFrame(autoPan);
  }
  function release() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    if (active && canvas.hasPointerCapture?.(active.pointerId))
      canvas.releasePointerCapture(active.pointerId);
    clearPreview();
  }
  function down(event) {
    if (event.button !== 0 || active) return;
    const terminal = event.target.closest("[data-port]"),
      part = event.target.closest("[data-part]");
    if (terminal) {
      event.preventDefault();
      callbacks.beginWire?.(terminal.dataset.port);
      active = {
        kind: "wire",
        from: terminal.dataset.port,
        pointerId: event.pointerId,
        pointerType: event.pointerType,
        startClientX: event.clientX,
        startClientY: event.clientY,
        clientX: event.clientX,
        clientY: event.clientY,
        moved: false,
      };
    } else if (part && !event.target.closest("[data-delete], [data-toggle]")) {
      event.preventDefault();
      const p = callbacks
        .getCircuit()
        .parts.find((p) => p.id === part.dataset.part);
      active = {
        kind: "part",
        id: p.id,
        pointerId: event.pointerId,
        x: p.x,
        y: p.y,
        start: local(event.clientX, event.clientY),
        startClientX: event.clientX,
        startClientY: event.clientY,
        clientX: event.clientX,
        clientY: event.clientY,
        before: structuredClone(callbacks.getCircuit()),
        moved: false,
      };
      callbacks.selectPart(p.id);
    } else {
      if (!event.target.closest("[data-wire], [data-toggle], [data-delete]"))
        callbacks.clearSelection();
      return;
    }
    canvas.focus({ preventScroll: true });
    canvas.setPointerCapture(event.pointerId);
  }
  function move(event) {
    if (!active || active.pointerId !== event.pointerId) return;
    active.clientX = event.clientX;
    active.clientY = event.clientY;
    if (
      Math.hypot(
        event.clientX - active.startClientX,
        event.clientY - active.startClientY,
      ) >= 4
    )
      active.moved = true;
    if (!active.moved) return;
    event.preventDefault();
    update();
    if (frame === null) frame = requestAnimationFrame(autoPan);
  }
  function up(event) {
    if (!active || active.pointerId !== event.pointerId) return;
    active.clientX = event.clientX;
    active.clientY = event.clientY;
    const gesture = active,
      target =
        gesture.kind === "wire" && gesture.moved
          ? targetAt(event.clientX, event.clientY, gesture.from)?.dataset.port
          : null;
    release();
    active = null;
    if (gesture.kind === "part")
      callbacks.finishPart(gesture.id, gesture.before);
    else if (gesture.moved) callbacks.finishWire(gesture.from, target);
    else callbacks.clickPort(gesture.from);
  }
  function cancel() {
    if (!active) return false;
    const gesture = active;
    release();
    active = null;
    if (gesture.kind === "part") callbacks.cancelPart(gesture.before);
    else callbacks.cancelWire();
    return true;
  }
  canvas.addEventListener("pointerdown", down);
  canvas.addEventListener("pointermove", move);
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", cancel);
  return {
    cancel,
    dispose() {
      cancel();
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", cancel);
    },
  };
}

export function isTextEditing(target) {
  return !!target?.closest?.(
    'input, textarea, select, [contenteditable]:not([contenteditable="false"])',
  );
}
