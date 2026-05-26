# RV8 Project — Changelog

## 2026-05-27 — RV8-GR Complete Redesign (v2.0)

- **Architecture**: 29 logic chips, full 64K, A15 chip select, execute from RAM
- **ISA**: 15 instructions (XORI=$70, XOR=$78, SETPG=$20, SETPG_R=$28)
- **Removed**: hardware JAL (software subroutine only)
- **Added**: Page Register (16-bit jump), ring counter (74HC164)
- **Fixed**: XOR data path, bus conflicts, U7 DIR gating, address mux 16-bit
- **Verilog**: rv8gr_cpu.v — ALL TESTS PASSED (127 cycles)
- **Assembler**: rv8gr_asm.py — labels, macros, .bin output
- **Test ROM**: testrom.bin — 10 test groups, 187 cycles, ALL PASS
- **Docs**: Construct.md (pin-level), ISA ref, traces, wiring, modules (Thai), bank switch

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
