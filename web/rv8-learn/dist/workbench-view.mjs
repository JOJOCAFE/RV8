import { configurations, targetFor } from "./wiring-engine.mjs";
import { partInfo } from "./lab-course.mjs";
import { nextTestGoal } from "./learning-state.mjs";

export const setupName = (config) =>
  Object.keys(config).length
    ? Object.entries(config)
        .map(([id, closed]) => `${id} ${closed ? "closed" : "open"}`)
        .join(" · ")
    : "Current wiring";
const lamp = (on) => (on ? "On" : "Off");

export function goalMarkup(lab, evidence) {
  const goal = nextTestGoal(lab, evidence);
  if (goal)
    return `<div class="goal-steps">${[
      ["build", "Complete loop", true, "lit"],
      ["break", "Remove one wire", false, "broken"],
      ["repair", "Repair loop", true, "repaired"],
    ]
      .map(
        ([phase, title, target, proof], i) =>
          `<span class="goal-case ${goal.phase === phase ? "next-goal" : ""} ${evidence.proof[proof] ? "done-goal" : ""}"><small>${evidence.proof[proof] ? "✓" : i + 1} ${title}</small><b>Lamp ${lamp(target)}</b></span>`,
      )
      .join("")}</div>`;
  return `<div class="goal-cases">${configurations(lab.switches)
    .map(
      (config) =>
        `<span class="goal-case"><small>${setupName(config)}</small><b>Lamp ${lamp(targetFor(lab.id, config))}</b></span>`,
    )
    .join("")}</div>`;
}

export function shellMarkup({ lab, index, nav, message, goal }) {
  return /* HTML */ `${nav}
    <main id="lab-main" tabindex="-1">
      <div class="lab-intro">
        <span class="eyebrow"
          >EXPERIMENT ${String(index + 1).padStart(2, "0")}</span
        >
        <h1>${lab.title}</h1>
      </div>
      <section class="goal-banner" aria-label="Your circuit goal">
        <div>
          <span class="eyebrow">YOUR GOAL</span>
          <p>${lab.goal}</p>
        </div>
        <div id="goal-rules">${goal}</div>
      </section>
      <div class="lesson-brief">
        <p>${lab.task}</p>
        <details class="lesson-notes">
          <summary>Explain the idea</summary>
          <h2>${lab.concept}</h2>
          <p>${lab.teaching}</p>
        </details>
        <details class="hints">
          <summary>I’m stuck. Give me a hint.</summary>
          <div id="hint-body"></div>
          <button id="more-hint" class="plain-button">Show a hint →</button>
        </details>
      </div>
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
            ><button id="remove-wire" disabled>Remove selected</button>
          </div>
        </div>
        <div class="parts-tray" aria-label="Add a part">
          ${lab.parts
            .map(
              (key) =>
                `<button data-add="${key}"><span class="part-icon">${partInfo[key].icon}</span><span><b>Add ${partInfo[key].name}</b><small>${partInfo[key].detail}</small></span><span aria-hidden="true">＋</span></button>`,
            )
            .join("")}
        </div>
        <div class="board-instructions">
          <span id="board-message" role="status"
            >${
              message ||
              "Drag a component to move it. Drag between terminals to wire. Backspace removes the selection."
            }</span
          ><button id="cancel-wire" class="plain-button" hidden>
            Cancel wire
          </button>
        </div>
        <div
          id="live-inputs"
          class="live-inputs"
          aria-label="Switch inputs on the board"
        ></div>
        <div class="canvas-scroll">
          <div
            id="circuit-canvas"
            class="circuit-canvas"
            tabindex="0"
            aria-label="Circuit drawing. Drag component bodies to move; drag terminals to connect."
          >
            <svg
              id="wire-layer"
              viewBox="0 0 880 440"
              aria-label="Your wire connections"
            ></svg>
            <div id="node-layer"></div>
            <div class="empty-bench" id="empty-bench">
              <span class="empty-icon">＋ ─ ◯</span>
              <h3>No circuit yet.</h3>
              <p>Add a battery and lamp. You choose the connections.</p>
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
        <p class="wiring-legend">
          <span>● Joined wires</span><span>⌒ Crossing without a connection</span
          ><span>Drag parts anywhere on their body</span>
        </p>
      </section>
      <section class="experiments-section" aria-label="Predict and test">
        <div class="section-heading">
          <span class="eyebrow">TEST YOUR CIRCUIT</span>
          <h2>
            ${lab.switches.length ? "Predict, then apply the test inputs." : "Predict, then test your circuit."}
          </h2>
          <p>
            The goal is what your circuit should do. Your prediction is what you
            think your wiring will do.
          </p>
        </div>
        <div id="test-controls"></div>
        <div id="test-feedback" role="status"></div>
        <div class="section-heading evidence-heading">
          <h2>Recorded evidence</h2>
          <p>
            These are snapshots of completed tests. A new prediction does not
            change an earlier result.
          </p>
        </div>
        <div id="experiment-table"></div>
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
      <footer class="lab-footer">
        <div id="progress-explanation"></div>
        <button id="next-lab" class="next-lab" disabled>
          ${index === 4 ? "Download my notebook ↓" : "Next experiment →"}
        </button>
      </footer>
      <p class="scope-note">
        Ideal wire-and-switch model. The physical rules are in “How this
        workbench works”.
      </p>
    </main>`;
}

export function testControlsMarkup({
  lab,
  evidence,
  plannedCase,
  currentCase,
}) {
  const configs = configurations(lab.switches),
    config = configs[plannedCase],
    goal = nextTestGoal(lab, evidence),
    draft = evidence.predictions[plannedCase];
  return `<div class="test-console"><div class="test-input-choice"><span class="test-step-label">1 · INPUTS FOR THE NEXT TEST</span>${lab.switches.length ? `<div class="test-cases" role="group" aria-label="Choose test inputs">${configs.map((c, i) => `<button data-case="${i}" class="${i === plannedCase ? "picked" : ""}" aria-pressed="${i === plannedCase}">${setupName(c)}</button>`).join("")}</div>` : `<p>${goal.title} · goal: lamp <b>${lamp(goal.target)}</b></p>`}<small>${lab.switches.length ? (currentCase === plannedCase ? "These inputs are already on the board." : `The board will change to ${setupName(config)} when you apply this test.`) : "The test reads your wiring exactly as it is."}</small></div><div class="test-prediction"><span class="test-step-label">2 · MY NEXT PREDICTION</span><div class="prediction-options" role="group" aria-label="My prediction for the next test">${[false, true].map((on) => `<button data-draft="${on}" class="${draft === on ? "picked" : ""}" aria-pressed="${draft === on}">Lamp ${lamp(on)}</button>`).join("")}</div></div><div class="test-apply"><span class="test-step-label">3 · OBSERVE</span><button id="apply-test" class="run-experiment" ${typeof draft !== "boolean" ? "disabled" : ""}>${lab.switches.length ? "Apply inputs & test" : "Record this test"} →</button></div></div>`;
}

export function evidenceMarkup({
  lab,
  evidence,
  fingerprint,
  currentCase,
  plannedCase,
}) {
  if (lab.id === "loop") {
    const phases = [
      ["build", "Complete loop", true, "lit"],
      ["break", "Remove one wire", false, "broken"],
      ["repair", "Repair loop", true, "repaired"],
    ];
    return `<table class="experiment-table"><thead><tr><th>Step</th><th>Goal</th><th>Recorded prediction</th><th>Observed</th><th>Evidence</th></tr></thead><tbody>${phases
      .map(([phase, title, target, proof]) => {
        const r = [...evidence.history]
            .reverse()
            .find((r) => r.phase === phase),
          done = evidence.proof[proof];
        return `<tr><th scope="row">${title}</th><td data-label="Goal">Lamp ${lamp(target)}</td><td data-label="Recorded prediction">${r ? "Lamp " + lamp(r.prediction) : done ? "Earlier session" : "—"}</td><td data-label="Observed">${r ? observation(r) : done ? "Recorded" : "—"}</td><td data-label="Evidence"><span class="evidence-state ${done ? "matched" : ""}">${done ? "✓ Step established" : r ? "Step not yet established" : "Not tested"}</span>${r && r.valid ? `<small class="prediction-result">${r.prediction === r.on ? "Prediction matched" : "Prediction differed"}</small>` : ""}</td></tr>`;
      })
      .join("")}</tbody></table>`;
  }
  return `<table class="experiment-table"><thead><tr><th>Test inputs</th><th>Goal</th><th>Recorded prediction</th><th>Observed</th><th>Circuit goal</th></tr></thead><tbody>${configurations(
    lab.switches,
  )
    .map((config, i) => {
      const record = evidence.rows[i],
        r = record?.fingerprint === fingerprint ? record : null,
        target = targetFor(lab.id, config),
        meets = r?.valid && !r.short && r.on === target;
      return `<tr class="${i === currentCase ? "live-case" : ""} ${i === plannedCase ? "planned-case" : ""}"><th scope="row"><button class="case-link" data-case="${i}">${setupName(config)}</button>${i === currentCase ? '<small class="live-case-tag">On board now</small>' : ""}</th><td data-label="Goal"><b>Lamp ${lamp(target)}</b></td><td data-label="Recorded prediction">${r ? "Lamp " + lamp(r.prediction) : "—"}</td><td data-label="Observed">${r ? observation(r) : "Not recorded"}${r && r.valid ? `<small class="prediction-result">${r.prediction === r.on ? "✓ Prediction matched" : "Prediction differed"}</small>` : ""}</td><td data-label="Circuit goal"><span class="evidence-state ${meets ? "matched" : r ? "mismatch" : ""}">${meets ? "✓ Goal met" : r ? "Goal not met" : "Not tested"}</span></td></tr>`;
    })
    .join("")}</tbody></table>`;
}
function observation(r) {
  return r.short
    ? "Short circuit"
    : !r.valid
      ? "Incomplete setup"
      : "Lamp " + lamp(r.on);
}
