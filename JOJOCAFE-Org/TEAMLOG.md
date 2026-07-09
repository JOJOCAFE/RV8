# Team Log

Maintained by: **Pim (พิม)**  
Updated: 2026-07-09

---

## Pim (พิม) — Coordinator
| Date | What | Result |
|------|------|--------|
| 2026-06-29 | Created BACKLOG.md, SPRINT.md, TEAMLOG.md | ✅ Team tracking online |
| 2026-07-09 | Closed Components simulator/library handoff and pushed skills update | ✅ Pushed |
| 2026-07-09 | Updated RV8GR canonical docs/labs, README status, and team memory after pushes through `1470963` | ✅ Pushed |

## Bank (แบงค์) — Architect
| Date | What | Result |
|------|------|--------|
| 2026-06-15 | Memory map swap decision (ROM $0000, RAM $8000) | ✅ Adopted |
| 2026-06-14 | Architecture frozen v1.0 | ✅ Signed off |
| 2026-07-09 | Approved Components as reusable library and kept simulator physical-pin/edge-aware | ✅ Adopted |

## Fern (เฟิร์น) — Verifier
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | 5 Verilog TBs pass + 512-opcode sweep verified | ✅ All pass |
| 2026-07-09 | Verified Components Python, 74HC Verilog, and Memory Verilog smoke checks | ✅ All pass |
| 2026-07-09 | Published B-007 non-physical verification report; physical B-007 remains blocked until hardware evidence exists | ⛔ Physical blocked |

## Mint (มิ้นท์) — RTL Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Verilog model finalized, gate-level sim 8/8 | ✅ All pass |
| 2026-07-09 | Aligned Components sequential chip edge behavior with Python simulator | ✅ Pushed |

## Ohm (โอม) — HW Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Programmer design finalized (ESP32 + TXS0108E + 74HC595) | ✅ 46 tests pass |
| 2026-07-09 | Captured component pinout/datasheet workflow and current blocked parts | ✅ Skill updated |

## Bam (แบม) — SW Coder
| Date | What | Result |
|------|------|--------|
| 2026-06-14 | Assembler complete (18 opcodes + macros, page-safe) | ✅ Working |
| 2026-07-09 | Captured Components Python backend contract: loader, 64 inputs, 8 clocks, future probes | ✅ Skill updated |
| 2026-07-09 | Implemented and assembler-verified B-010 example ASM programs for blink, counter, and echo workflows | ✅ Verified |

## Noon (นุ่น) — Docs Writer
| Date | What | Result |
|------|------|--------|
| 2026-06-15 | 14 hardware labs written (Thai, middle school) | ✅ Complete |
| 2026-07-09 | Captured simulator documentation requirements for future UI/backend docs | ✅ Skill updated |
| 2026-07-09 | Updated team docs for B-010 verification, B-007 verification split, and Components mapping push `a2ee62c` | ✅ Current |

---

## How to Use
- Pim adds entries when work is completed or significant progress made.
- One row = one deliverable or decision. Keep it short.
- Link to files if needed: `see rtl/rv8gr_cpu.v`
- Failed attempts count too — mark with ❌ and note why.
