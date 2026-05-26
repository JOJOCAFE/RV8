# RV8 Project — Task Tracker

**Last updated**: 2026-05-27
**Focus**: RV8-GR — REDESIGNED, VERIFIED, READY FOR BUILD

---

## ✅ Completed (RV8-GR)

- [x] Architecture redesign (29 chips, full 64K, A15 chip select)
- [x] ISA (15 instructions, verified encodings, no conflicts)
- [x] Construct.md (pin-level wiring, bus-centric, source of truth)
- [x] Verilog model (rv8gr_cpu.v, all tests pass, 127 cycles)
- [x] Testbench (tb_rv8gr_full.v, all ISA + 64K jump + subroutine)
- [x] Instruction trace (7 pin-level traces + 27-step test program)
- [x] Wiring guide (signal routing quick reference)
- [x] Module guide (Thai, 8 modules)
- [x] ISA reference (encoding + derived signals + IBUS rules)
- [x] Design document (architecture + data path + key decisions)
- [x] Bank switch doc (ROM/RAM expansion via bus)

---

## ⬜ TODO — Next Steps

| # | Task | Priority |
|:-:|------|:--------:|
| 1 | Assembler (Python, .asm → .bin) | HIGH |
| 2 | Order parts (29 chips + ROM + RAM) | HIGH |
| 3 | Build Programmer board (ESP32) | HIGH |
| 4 | Build RV8-GR on breadboard | HIGH |
| 5 | First program on real hardware | HIGH |
| 6 | BASIC interpreter (ROM) | MEDIUM |
| 7 | Simple game (ROM) | MEDIUM |
| 8 | PCB layout (KiCad) | LOW |

---

## Other Variants

| Variant | Status |
|---------|--------|
| RV8 (27 chips) | ✅ Designed, Verilog pass, docs done |
| RV8-R (18 chips) | ⬜ Concept only |
| RV8-G (28 chips) | ⬜ Concept only |
