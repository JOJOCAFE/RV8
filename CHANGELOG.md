# RV8 Project — Changelog

## 2026-05-27 — RV8-GR v2.0 + RV8-G Construct

### RV8-GR Complete
- **Architecture**: 29 logic chips, full 64K, A15 chip select, execute from RAM
- **ISA**: 15 instructions (XORI=$70, XOR=$78, SETPG=$20, SETPG_R=$28)
- **Verilog**: ALL TESTS PASSED (127 cycles)
- **Assembler**: rv8gr_asm.py — labels, macros, .bin output
- **Test ROM**: testrom.bin — 10 test groups, 187 cycles, ALL PASS
- **Docs**: Construct (pin-level), ISA, traces, wiring, modules (Thai), bank switch

### RV8-G Construct
- **Architecture**: 38 logic chips, full 35-instruction ISA, no microcode
- **4-cycle**: T0=fetch, T1=operand, T2=load B, T3=execute
- **Full ALU**: ADD/SUB/AND/OR/XOR/SLL/SRL/SLT
- **Branches**: BEQ/BNE/BLT/BGE comparing two registers
- **JAL/JALR**: hardware subroutine call/return
- **PUSH/POP**: hardware stack pointer
- **Status**: Construct done, Verilog next

## 2026-05-16 — RV8-GR Initial Design (v1.0)

- 21 logic chips, ROM at $8000, 256-byte jump range
- Verilog 11/11 tests pass
- Assembler (rv8gr_asm.py)
- Full doc set (design, ISA, trace, wiring, modules, bank switch)

## 2026-05-15 — RV8 Family Architecture

- RV8: 27 chips, microcode, Verilog 8/8 pass
- RV8-R: 18 chips concept
- RV8-G: 28 chips concept
- RV8-GR: 21 chips concept

## 2026-05-10 to 2026-05-14 — Project Start

- Original designs explored and archived
- Programmer board (ESP32 + TXB0108) complete
- Reference study: Gigatron, SAP-1, Nand2Tetris
