# Three-pass review

Reviewed on 2026-10-20. The lab runs at `http://localhost:4173/#lab-1` with the command in [README.md](README.md).

## Pass 1: correctness and maintainability

Reviewed the connectivity model, goal assessment, saved state, lesson progression, and final source scope.

- Kept electrical connectivity independent from visual wire routing.
- Checked every source/lamp wire graph against an independent reachability implementation (64 graphs).
- Checked all input configurations for control, AND, OR, and `(A AND B) OR C`.
- Required prediction records, all input cases on the same wiring version, and a transfer explanation.
- Kept a wrong prediction as evidence rather than treating it as a failed learning attempt.
- Required the first break experiment to remove exactly one wire from an observed working circuit.
- Recomputed circuit behavior during assessment instead of trusting stored goal flags.
- Added validation and recovery for malformed saved circuits and partial evidence.
- Fixed lost keyboard focus after rendering terminals, wires, switch controls, experiment rows, and explanations.
- Reported actual storage failures and exposed notebook download before course completion.
- Kept only the current local learning lab in the proposed source changes.

## Pass 2: complete browser walkthrough

Used a separate private browser profile so test work did not replace a learner's saved circuits. Exercised the actual part, terminal, wire, switch, prediction, and explanation controls.

1. Started from an empty board. Added a battery and a lamp and connected their terminals using keyboard activation and Tab.
2. Confirmed one wire left the lamp off and a complete route lit it. Confirmed lighting alone did not complete the experiment.
3. Selected a wire with Enter and removed it with Delete. Predicted, tested, repaired, and answered the transfer question. An incorrect explanation did not unlock the next lesson.
4. Added a switch without using it and confirmed this failed the control goal. Rewired it into the route and tested both input settings.
5. Built the two-switch AND route and tested all four cases. Removed a connection and confirmed previous proof no longer counted for the changed wiring. Repaired it and repeated the observations.
6. Rewired the same parts into OR and checked all four cases.
7. Added C, built the combined rule, and checked all eight cases.
8. Checked native dragging, undo, cancelled-drag rollback, and preservation of evidence after layout-only edits.
9. Checked every lesson at 320 px without page-level horizontal overflow. The board and experiment table pan within their own regions.
10. Simulated a storage quota failure: the notice was visible on mobile and work remained usable in the tab. Restored storage and confirmed the notice cleared.
11. Loaded malformed storage and confirmed an explained recovery to a usable board. Restored a valid notebook and kept all circuits, observations, completion, and written notes.
12. Downloaded the notebook through the browser and parsed the resulting JSON. Its five circuits restored and passed their recorded design assessments.

## Pass 3: final regression and packaging

- Found and fixed a snapped-position mismatch at the left edge: the drag logic could produce x=20 while reload required x>=24.
- Shared placement bounds between dragging, keyboard movement, restoration, and routing dimensions. Added an edge-placement regression over 36 coordinate pairs.
- Dragged a part to the top-left limit in the browser, reloaded, and retained the part, all five circuits, and their evidence.
- Ran the full suite on Node 24: **29 tests passed, zero failures**.
- Checked every browser module's syntax and resolved every local HTML asset and module import.
- Loaded the final empty-board page with no browser console errors or failed module requests.
- Checked the source diff for whitespace errors, unintended hosting metadata, and obsolete demos.
- Added a GitHub Actions workflow that runs module syntax checks and the same Node 24 test suite for relevant changes.

## Interaction follow-up · 2026-10-23

Three further passes addressed the learner's reports about moving parts, drag wiring, Backspace, confusing predictions/evidence, hidden goals, the left column, and crossed wires.

1. **Behavior and evidence:** separated the pending test from the board's actual inputs, kept recorded predictions immutable, separated prediction accuracy from circuit-goal success, and gave the required wire-break experiment an Off goal. Verified that removing two wires does not meet the one-wire goal, undo recovers matching observations, and older notebooks retain circuits and progress. The goal and required outcomes now sit above the full-width board; the left column and duplicate first-lesson checklist were removed.
2. **Browser interactions and complete course:** in a separate test session, dragged a component by its symbol body; connected terminals by native mouse drag with live preview and magnetic targeting; used click and Enter wiring; removed selected wires and components with Backspace/Delete; undid removal with attached wires; edited notebook text with Backspace without deleting a circuit; cancelled moves with Escape and wires with Backspace; and verified evidence after reload. Completed all five lessons again, including every AND, OR, and combined-rule case and their transfer questions. Changing a draft did not rewrite the recorded prediction. Selecting future inputs did not change switch positions until applying the test; manual switch changes immediately updated live inputs.
3. **Routing, narrow layouts, and final regression:** added tests for terminal endpoints, orthogonal segments, unchanged connectivity, separate-net line overlap, joined branch dots, crossing-hop metadata, compact parallel wiring, live drag tethers, and switch-button clearance. Visual review caught a route behind a switch control; the router now clears the full control. Checked every lesson at 320 px with no page-level horizontal overflow. Used Chromium touch emulation at 390 px to verify component-body dragging, magnetic wire drops, edge panning, cancellation, and panning stopping on release. Slowed edge panning and paused it over a wire target. Reserved terminal exits and required straight-through crossings after a 30-arrangement sweep found misleading hops at bends. Ran all **41 tests on Node 24**, browser-module syntax checks, asset/import checks, and whitespace checks.

The T3 preview screenshot operation timed out twice, so these follow-up browser checks used the Playwright CLI in isolated test sessions. Touch results are browser emulation, not a physical-device test. The learner's default browser notebook was not reset or overwritten.

## Reproduce the automated checks

```sh
node --test web/rv8-learn/test-*.mjs
for file in web/rv8-learn/dist/*.js web/rv8-learn/dist/*.mjs; do
  node --check "$file"
done
```

For browser verification, start a separate private window, construct the circuits yourself, and follow the walkthrough above. Do not clear an existing learner's notebook to run the checks.

These checks establish software behavior. Learning outcomes with beginners and real hardware behavior have not been validated. The workbench explicitly models ideal connectivity, not analogue current, timing, component ratings, or the full RV8GR CPU.
