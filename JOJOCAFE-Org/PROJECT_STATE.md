# Project State

## Owner: Team JOJOCAFE-Org

The team owns the entire RV8 project. All variants, all deliverables.

## Active Target: RV8-GR (Student Baseline)

- **Status**: Architecture frozen v1.0 — ready for physical build
- **Chips**: 34 logic + ROM + RAM = 36 packages
- **ISA**: 18 instructions (17 + SETDP), all verified
- **Verification**: behavioral + chip-level Verilog TBs pass, all-ISA dual Verilog scoreboard pass, 512-opcode sweep, gate-level sim 8/8
- **ROM tests**: `NOT` pseudo-instruction ROM test and B-011 `basic_min.asm`
  BASIC-style smoke ROM pass in current regression
- **Labs**: 14 hardware labs written (Thai, middle school level)
- **Clock**: 1 MHz breadboard target

## Current Sprint & Backlog

- **Backlog**: see `BACKLOG.md` (19 items, prioritized P0-P3)
- **Sprint 1**: see `SPRINT.md` (Physical Build Kickoff, individual task lists)

### Sprint 1 Summary
- [ ] Order parts for physical build
- [ ] Build Labs 01-14 on breadboard (sequential, verify each)
- [ ] Flash test ROM via Programmer
- [x] Write example .asm programs (B-010 implemented and assembler-verified)
- [x] B-011 phase 1 BASIC-style ROM smoke test implemented
- [ ] Full ISA test on physical hardware (B-007 blocked until hardware evidence exists; non-physical report available)

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
| 2026-07-09 | B-010 example ASM programs implemented and assembler-verified; B-007 non-physical verification report available while physical B-007 remains blocked for hardware evidence; Components netlist mappings verified and pushed through `a2ee62c` | Pim |
| 2026-07-10 | Components latest student guide, CLI/API contract, `circuit-faults` virtual physical checker, and future student-friendly chip JSON/wiring-command lane merged into RV8 team operating docs; Components pushed through `87bcfdc` | Pim |
| 2026-07-10 | RV8GR all-ISA dual Verilog scoreboard added; behavioral `rv8gr_cpu.v` and chip-level `rv8gr_chip_level.v` now compare `PC`, `AC`, `Z`, `PG`, `DP`, `IE`, `IRQ_FF`, and key RAM writes; pushed through `622e41a` | Pim |
| 2026-07-10 | RV8GR source-of-truth doc pass completed for design ISA, instruction trace, bank switch, and module-understanding docs; team skills refreshed to prevent stale IRQ/DI/bus/ROM assumptions; packaged doc zip removed for now | Pim |
| 2026-07-11 | RV8GR baseline sync and test-ROM checkpoint: U34/BOM/clock docs aligned, `NOT` pseudo-instruction covered by Python/Verilog ROM tests, B-011 phase 1 BASIC-style ROM smoke added, and Verilog timescale warnings removed | Pim |
| 2026-06-15 | Memory map swapped: ROM $0000-$7FFF, RAM $8000-$FFFF | architect |
| 2026-06-14 | Architecture frozen v1.0 — no more changes until physical build | architect |
| 2026-06-14 | Programmer design finalized (ESP32 + TXS0108E + 74HC595) | hw-coder |

## Known Issues

No RV8-GR design blockers. Physical B-007 verification is blocked until
hardware evidence exists; a non-physical B-007 verification report is available.
Non-physical Verilog confidence now includes the all-ISA dual scoreboard, but
that still does not replace measured physical build evidence.
B-011 is currently a non-interactive test ROM only; a real BASIC interpreter
still needs an RV8-Bus I/O device and runtime model decision.
Shared Components removed `74hc150` and `74hc260`
from the active catalog because manufacturer-verified HC-family DIP evidence
was not available.

Shared Components known follow-ups:

- Keep Components Python schematic backend compatible with future UI/block/JSON editing and RV8GR chip-level netlist/Verilog export.
- Components student guide and virtual physical checker handoff is verified and pushed through `87bcfdc`.
- Use `circuit-faults` before treating Components-derived RV8GR chip/circuit/system behavior as ready for physical build steps.
- Later Components cleanup: review chip JSON/component definition output for student readability and document system wiring commands.
- SST39SF010A Python/Verilog write-trigger semantics are now aligned for the simplified flash model: write occurs on the falling edge of `/WE` while selected with `/OE` high.

Documentation follow-ups:

- Treat `RV8GR/doc/00_design_isa.md` and `RV8GR/doc/01_wiring_guide.md` as source of truth. `04_understand_by_module.md` is a student explanation only.
- Do not use `RV8GR/doc/RV8GR-Doc.zip` for now; keep Markdown docs as the live source of truth.
