# RV8 learning lab

Learn by constructing connections and investigating their effects. The default experience starts with an empty circuit board, not a prepared CPU or a button that supplies an answer.

![A learner-built switch circuit, with its goal above the board](preview.png)

## Run locally

From the RV8 repository root:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory web/rv8-learn/dist
```

Open http://localhost:4173/#lab-1. Keep the terminal running. There is no login, installation, or build step. This revision is local-only; it has not been published to the hosted copy.

## Learning sequence

1. Construct a closed route using a battery, a lamp, and your own wires. Predict and test it; remove a wire, then repair the route. Explain a different connection case.
2. Add a switch to your own circuit. Prove it controls the lamp in both positions; an unused or bypassed switch does not meet the goal.
3. Make two switches both necessary. Test all four configurations before naming the behavior AND.
4. Rewire the same components so either switch is enough. Test all four configurations before naming the behavior OR.
5. Build the new rule `(A AND B) OR C` without a prepared circuit. Test all eight configurations and explain the alternative route.

Predictions can be wrong: the observations are evidence to investigate. Each recorded test keeps its original inputs, prediction, and observation. The table reports prediction accuracy separately from whether the circuit meets its goal. Changing connections invalidates the current design's table, but preserves previous observations in the notebook. Undoing that change restores observations for the matching wiring. Moving parts does not invalidate evidence. Completion requires the full behavior table plus a transfer question; clicking every control is not sufficient.

The first board is empty. Later boards inherit only the learner's own previous construction. Staged hints are available on request and never create wires automatically. The notebook, circuits, explanations, and progress stay in localStorage, with an in-memory fallback when storage is blocked. A completed notebook can be downloaded as JSON.

## Model and controls

`dist/wiring-engine.mjs` derives circuit behavior from the wire graph and switch contacts. Battery terminals have different levels. A lamp turns on when its ends connect to different source terminals. A direct source-to-source connection cuts power and reports a short. An open switch does not join its ends; a closed switch does. The lamp filament and switch contact are drawn explicitly.

This is an **ideal connectivity model** for one source, one lamp and up to three switches. It does not calculate physical current, voltage magnitude, resistance, brightness, analogue behavior, or real hardware ratings. It is an introduction to constructing and reasoning about circuits, not physical signoff or a full RV8GR simulation. Real transistors and TTL gates require further teaching.

`dist/wire-routing.mjs` and `dist/wire-layout.mjs` route the drawing around symbols, labels, and switch controls. They have no authority over electrical connectivity. Wires already on the same net can share a trunk, with dots marking joined branches. Hops mark crossings between separate nets. New connections are made at terminals. Overlapping components can obstruct routing; move their bodies apart to make space.

Add a part from the tray. Drag between terminal dots to connect them; a live wire and highlighted target show where it will attach. Clicking two terminals and Enter activation also work. Drag any part's body to move it, or focus it and use the arrow keys. Select a wire or component and use Remove selected, Backspace, or Delete. Text editing keeps its normal controls. Escape cancels a gesture. On narrow screens, dragging near an edge pans the board; panning pauses over a wire target. Undo/redo restores placement, wiring, and removed parts with their attached wires.

The goal and required lamp outcomes sit above the full-width board. The live input row shows actual switch positions. Choosing the next test case does not change the board until **Apply inputs & test**. Manual switch changes update the live row immediately. The first experiment instead reads the current wiring and advances through On → remove one wire / Off → repair / On.

## Verify

Node.js 24 or later runs the tests without installing dependencies:

```sh
node --test web/rv8-learn/test-*.mjs
```

The 41 tests cover circuit behavior, learning progression, and visual routing, including all 64 source/lamp wire graphs, all AND/OR and combined-rule settings, controlled break/repair, immutable predictions, live inputs, undo evidence, invalid designs, malformed and older notebooks, joined trunks, separate-net crossings across 30 component arrangements, and switch-control clearance. The same command runs in the Learning lab GitHub Actions workflow. See [VERIFICATION.md](VERIFICATION.md) for the review passes and browser checks.

## Continue learning

The [original RV8GR hardware labs](../../RV8GR/doc/labs/README.md), [Thai module tutorial](../../RV8GR/doc/04_understand_by_module.md), and [wiring guide](../../RV8GR/doc/01_wiring_guide.md) remain the hardware references. The browser help links to those guides. This first web module teaches circuit construction and logic rules; it does not yet teach transistor internals, memory construction, or the complete RV8GR CPU.
