# Team Log

Maintained by: **Pim (พิม)**  
Updated: 2026-07-10

---

## Pim (พิม) — Coordinator
| Date | What | Result |
|------|------|--------|
| 2026-06-29 | Created BACKLOG.md, SPRINT.md, TEAMLOG.md | ✅ Team tracking online |
| 2026-07-09 | Closed Components simulator/library handoff and pushed skills update | ✅ Pushed |
| 2026-07-09 | Updated RV8GR canonical docs/labs, README status, and team memory after pushes through `1470963` | ✅ Pushed |
| 2026-07-10 | Merged latest Components student guide, CLI/API, and virtual physical checker skills into RV8 team docs | ✅ Documented |
| 2026-07-10 | Routed all-ISA dual Verilog scoreboard work and pushed status through `622e41a` | ✅ Pushed |

## Bank (แบงค์) — Architect
| Date | What | Result |
|------|------|--------|
| 2026-06-15 | Memory map swap decision (ROM $0000, RAM $8000) | ✅ Adopted |
| 2026-06-14 | Architecture frozen v1.0 | ✅ Signed off |
| 2026-07-09 | Approved Components as reusable library and kept simulator physical-pin/edge-aware | ✅ Adopted |
| 2026-07-10 | Adopted Components virtual checker boundaries for RV8GR chip/circuit/system workflows | ✅ Documented |

## Fern (เฟิร์น) — Verifier
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | 5 Verilog TBs pass + 512-opcode sweep verified | ✅ All pass |
| 2026-07-09 | Verified Components Python, 74HC Verilog, and Memory Verilog smoke checks | ✅ All pass |
| 2026-07-09 | Published B-007 non-physical verification report; physical B-007 remains blocked until hardware evidence exists | ⛔ Physical blocked |
| 2026-07-10 | Added RV8 team responsibility for Components pin, bus, edge, timing, R/C, and delay-noise verification gates | ✅ Documented |
| 2026-07-10 | Verified all-ISA dual Verilog scoreboard: 55 chip-level checkpoints matched behavioral checkpoints | ✅ All pass |

## Mint (มิ้นท์) — RTL Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Verilog model finalized, gate-level sim 8/8 | ✅ All pass |
| 2026-07-09 | Aligned Components sequential chip edge behavior with Python simulator | ✅ Pushed |
| 2026-07-10 | Linked Components edge-behavior compatibility to RV8 team skill docs | ✅ Documented |
| 2026-07-10 | Added dual Verilog scoreboard covering every frozen ISA command, page/data-page control, and IRQ polling | ✅ Pushed |

## Ohm (โอม) — HW Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Programmer design finalized (ESP32 + TXS0108E + 74HC595) | ✅ 46 tests pass |
| 2026-07-09 | Captured component pinout/datasheet workflow and current blocked parts | ✅ Skill updated |
| 2026-07-10 | Added breadboard timing/current-risk and virtual R/C/noise responsibilities to shared Components ownership | ✅ Documented |

## Bam (แบม) — SW Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Assembler complete (18 opcodes + macros, page-safe) | ✅ Working |
| 2026-07-09 | Captured Components Python backend contract: loader, 64 inputs, 8 clocks, future probes | ✅ Skill updated |
| 2026-07-09 | Implemented and assembler-verified B-010 example ASM programs for blink, counter, and echo workflows | ✅ Verified |
| 2026-07-10 | Added Components `circuit-faults` CLI/API test instrument ownership to RV8 team docs | ✅ Documented |
| 2026-07-10 | Confirmed Python CPU, Components-backed CPU, assembler, wiring, and Components package checks still pass after Verilog timing fixes | ✅ All pass |

## Noon (นุ่น) — Docs Writer
| Date | What | Result |
|------|------|--------|
| 2026-06-15 | 14 hardware labs written (Thai, middle school) | ✅ Complete |
| 2026-07-09 | Captured simulator documentation requirements for future UI/backend docs | ✅ Skill updated |
| 2026-07-09 | Updated team docs for B-010 verification, B-007 verification split, and Components mapping push `a2ee62c` | ✅ Current |
| 2026-07-10 | Added student guide and future chip JSON / wiring-command clarity lane to RV8 team docs | ✅ Documented |
| 2026-07-10 | Updated README and CPU logical protocol with the all-ISA dual Verilog standard-test matrix | ✅ Current |

---

## How to Use
- Pim adds entries when work is completed or significant progress made.
- One row = one deliverable or decision. Keep it short.
- Link to files if needed: `see rtl/rv8gr_cpu.v`
- Failed attempts count too — mark with ❌ and note why.
