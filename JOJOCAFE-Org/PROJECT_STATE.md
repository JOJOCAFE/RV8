# Project State

## Owner: Team JOJOCAFE-Org

The team owns the entire RV8 project. All variants, all deliverables.

## Active Target: RV8-GR (Student Baseline)

- **Status**: Architecture frozen v1.0 — ready for physical build
- **Chips**: 34 logic + ROM + RAM = 36 packages
- **ISA**: 18 instructions (17 + SETDP), all verified
- **Verification**: behavioral + chip-level Verilog TBs pass, 512-opcode sweep, gate-level sim 8/8, soft_debug 4/4
- **Labs**: 14 hardware labs written (Thai, middle school level)
- **Clock**: 1 MHz breadboard target

## Current Sprint & Backlog

- **Backlog**: see `BACKLOG.md` (19 items, prioritized P0-P3)
- **Sprint 1**: see `SPRINT.md` (Physical Build Kickoff, individual task lists)

### Sprint 1 Summary
- [ ] Order parts for physical build
- [ ] Build Labs 01-14 on breadboard (sequential, verify each)
- [ ] Flash test ROM via Programmer
- [ ] Write example .asm programs
- [ ] Full ISA test on physical hardware

## Next Projects (queued)

- RV8-R FullHW: 49 logic chips / 53 total packages, full RV8-style ISA investigation path
- RV8-G: 38 logic chips, full ISA, no microcode concept/history item

## Recent Decisions

| Date | Decision | By |
|------|----------|----|
| 2026-07-09 | Shared Components repo created and pushed to `git@github.com:JOJOCAFE/Components.git`; component-library skill added for agent ownership and datasheet workflow | Pim |
| 2026-07-09 | Components Python simulator added/updated with DIP pin models, ROM/RAM image loading, 64 input stimulus channels, 8 clocks, and edge-aware clock dispatch; pushed through `f4ea985` | Pim |
| 2026-07-09 | Components Python schematic backend, buses, pull defaults, probes/test logic, netlist, and Verilog export path added; pushed through `6bc7ee0` | Pim |
| 2026-07-09 | RV8GR canonical rename/docs/labs cleanup and top-level README status fixes pushed through `1470963` | Pim |
| 2026-06-15 | Memory map swapped: ROM $0000-$7FFF, RAM $8000-$FFFF | architect |
| 2026-06-14 | Architecture frozen v1.0 — no more changes until physical build | architect |
| 2026-06-14 | Programmer design finalized (ESP32 + TXS0108E + 74HC595) | hw-coder |

## Known Issues

No RV8-GR design blockers. Shared Components removed `74hc150` and `74hc260`
from the active catalog because manufacturer-verified HC-family DIP evidence
was not available.

Shared Components known follow-ups:

- Keep Components Python schematic backend compatible with future UI/block/JSON editing and RV8GR chip-level netlist/Verilog export.
- SST39SF010A Python/Verilog write-trigger semantics are now aligned for the simplified flash model: write occurs on the falling edge of `/WE` while selected with `/OE` high.
