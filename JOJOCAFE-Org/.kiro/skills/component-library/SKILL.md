---
name: component-library
description: Shared component-library and Board engine for RV8/JOJOCAFE hardware projects. Use when working with 74HC models, memory models, Board visual editor, or component circuit simulation.
---

# Component Library & Board Engine

## Repository

- Local path: `/home/jo/kiro/Components`
- GitHub: `git@github.com:JOJOCAFE/Components.git`
- Branch: `main`

## What's In It

| Area | Path | Status |
|------|------|--------|
| **Board Engine** | `board/src/` | ✅ 969 tests, feature-complete |
| **Browser Client** | `board/app.html` | ✅ Interactive (drag, connect, edit, file menu) |
| **Chip Definitions** | `lib/standard/` | Active (74xx, memory, passive) |
| **Python Models** | `python/chiplib/` | Active (behavior, sim, circuit runner) |
| **Verilog Models** | `verilog/` | Active (74xx + memory) |
| **Datasheets** | `source/` | 60+ manufacturer PDFs |
| **Language Spec** | `Language/` | 23 docs, frozen v1.0 |
| **Circuit Examples** | `examples/circuits/` | RV8GR integration tests |

## Board Engine Architecture (2026-08-02)

```
Engine (headless, 969 tests) → JSON state → Any client
  ├── Browser (app.html)     ← thin SVG renderer + input capture
  ├── CLI (future)           ← pipe commands, text output
  ├── AI / MCP (future)     ← tool_use integration
  └── 3D / VR (future)      ← WebGL/XR renderer
```

### Key Design
- **Headless engine**: zero DOM, runs in Node.js, all state as JSON
- **Twin sync**: Visual ↔ Components:circuit ↔ Components:board (edit one → others auto-update)
- **Command registry**: OOP groups (`file.save`, `board.place`, `tool.connect`), progressive disclosure
- **Plugin architecture**: `registry.register(group)` adds new command libraries at runtime

### Three Project Files (Twins)
- `Components:circuit` — devices, nets, connections
- `Components:board` — placements, routes, labels
- `Components:command` — command history/log

### Phases (all complete)
1. Foundation: engine, parser, executor, viewport, config (348 tests)
2. Text Editors: file model, editor state, page sync (256 tests)
3. Tool Plugins: select, connect, tray, guide, eraser, label, inspect (158 tests)
4. Print & Export: SVG, PNG meta, fold marks, tiling (73 tests)
5. Integration: presentation, history, twin sync, registry (134 tests)

## Team Responsibility

| Agent | Board Role |
|-------|-----------|
| Bam | Board engine code, tools, CLI, twin sync |
| Fern | Verify all code, audit docs, regression |
| Bank | Architecture decisions, plugin contracts |
| Noon | Student docs, UI labels, help text |
| Ohm | Pinout truth, DIP evidence, chip frames |
| Mint | Verilog models, chip export |
| Pim | Route tasks, commits, pushes |

## Verification Commands

```bash
# Board engine (969 tests, ~3 seconds)
cd /home/jo/kiro/Components/board
for f in test/*.test.js; do node "$f"; done

# Serve browser client
cd board && python3 -m http.server 8080
# http://localhost:8080/app.html

# Python chiplib
cd /home/jo/kiro/Components
PYTHONPATH=python python3 -B -m pytest tests/ -q

# Verilog smoke
iverilog -g2012 -Wall -o /tmp/tb.vvp verilog/74xx/*.v verilog/74xx/tests/*.v && vvp /tmp/tb.vvp
```

## Non-Negotiable Rules
1. Engine is headless — zero DOM in `board/src/`
2. All UI actions = commands (logged, undoable, twin-synced)
3. DB, Python, Verilog, pinout evidence, and docs must stay aligned
4. Pinouts require manufacturer datasheet + DIP package proof
5. No specialist verifies only their own work — Fern reviews
6. Student clarity is a hard requirement

## Datasheet Policy
- Manufacturer PDFs only (DIP/PDIP proof required)
- AllDatasheet as locator, not authority
- Keep cited PDFs in `source/`, remove failed/duplicate downloads
