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

## Reproduce the automated checks

```sh
node --test web/rv8-learn/test-*.mjs
for file in web/rv8-learn/dist/*.js web/rv8-learn/dist/*.mjs; do
  node --check "$file"
done
```

For browser verification, start a separate private window, construct the circuits yourself, and follow the walkthrough above. Do not clear an existing learner's notebook to run the checks.

These checks establish software behavior. Learning outcomes with beginners and real hardware behavior have not been validated. The workbench explicitly models ideal connectivity, not analogue current, timing, component ratings, or the full RV8GR CPU.
