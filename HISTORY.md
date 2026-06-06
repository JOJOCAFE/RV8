# RV8 Project — Development History

## 2026-05-10 to 2026-05-14 — Project Start
- Original designs explored and archived
- Programmer board complete (ESP32 + TXB0108)

## 2026-05-15 — RV8 Family Architecture
- RV8: 27 chips, microcode, Verilog 8/8 pass
- RV8-R: 18 chips concept
- RV8-G: 28 chips concept
- RV8-GR: 21 chips concept

## 2026-05-16 to 2026-05-17 — RV8-GR Initial Design (v1.0)
- 21 logic chips, ROM at $8000, 256-byte jump range
- All 4 variants traced and verified
- Verilog 11/11 unit tests pass
- Assembler (rv8gr_asm.py)
- Assembly integration test passes
- Full doc set complete

## 2026-05-27 — RV8-GR v2.0 Complete Redesign + RV8-G Construct

### RV8-GR Complete (v2.0)
- Architecture: 29 logic chips, full 64K, A15 chip select
- Execute from RAM (PC < $8000)
- 16-bit jump via Page Register
- ISA: 15 instructions (XORI=$70, XOR=$78, SETPG=$20, SETPG_R=$28)
- Verilog: ALL TESTS PASSED (127 cycles)
- Assembler: rv8gr_asm.py — labels, macros, .bin output
- Test ROM: testrom.bin — 10 test groups, 187 cycles
- Docs: Construct (pin-level), ISA, traces, wiring, modules, bank switch

### RV8-G Construct
- 38 logic chips, full 35-instruction ISA, no microcode
- 4-cycle execution with B-register
- Full ALU: ADD/SUB/AND/OR/XOR/SLL/SRL/SLT
- Branches: BEQ/BNE/BLT/BGE rs1,rs2
- JAL/JALR, PUSH/POP
- Construct.md written

## 2026-06-06 — RV8-GR v3.0: IRQ + Python Simulation + Codeberg

### IRQ Support
- Added EI ($08) and DI ($48) instructions
- IRQ latch (74HC74 U31-B) for edge detection
- IE flag (74HC74 U31-A) for enable/disable
- Fixed vector $FF00, auto-save PC to RAM[$0E:$0F]
- No nesting (IE cleared on entry)
- 30 logic chips total (+1 from v2.0)
- 17 instructions total (+2 from v2.0)
- tb_rv8gr_irq.v — 6 tests: EI/DI, IRQ fire, PC save, defer past jumps

### Python Gate-Level Simulation
- sim/gate_sim.py — simplified chip models
- Ring counter, registers, ALU components
- Trace timing: T0→T1→T2
- Educational tool for understanding CPU behavior

### Test Infrastructure
- tb_rv8gr_tasks.v — milestone tests (1-9)
- tools/test_rv8gr_asm.py — assembler unit tests
- doc/task_test_plan.md — test milestones

### Repository
- Moved from GitHub to Codeberg
- https://codeberg.org/JOJOCAFE/RV8

## Key Milestones

| Date | Milestone |
|------|-----------|
| 2026-05-10 | Project started |
| 2026-05-14 | Programmer board complete |
| 2026-05-16 | All 4 variants traced and verified |
| 2026-05-17 | RV8-GR v1.0: toolchain ready |
| 2026-05-27 | RV8-GR v2.0: complete redesign, full 64K |
| 2026-06-06 | RV8-GR v3.0: IRQ + sim + Codeberg |

## Lessons Learned

1. Every trace finds 1-2 more chips than initially claimed
2. Full ISA always costs ~27-30 chips regardless of approach
3. RAM registers save ~10 chips (proven)
4. "No microcode" doesn't save chips for full ISA
5. Bank switch belongs on expansion board, not CPU