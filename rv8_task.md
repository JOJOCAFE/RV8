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

## ⬜ TODO — Roadmap to Physical Build

| # | Task | Priority | Notes |
|:-:|------|:--------:|-------|
| 1 | ~~Assembler~~ | ✅ DONE | rv8gr_asm.py, labels, macros, .bin |
| 2 | ~~Test ROM image~~ | ✅ DONE | testrom.bin, 10 tests, 187 cycles |
| 3 | Parts list (exact part numbers) | **NOW** | DIP packages, speed grades |
| 4 | Programmer board test | **NOW** | Verify ESP32 flashes SST39SF010A |
| 5 | Breadboard layout plan | HIGH | 4-5 boards, bus routing |
| 6 | Physical build | HIGH | Module by module, test each stage |
| 7 | First program on hardware | HIGH | LED blink or counter |
| 8 | BASIC interpreter | MEDIUM | Threaded interpreter in ROM |
| 9 | Simple game | MEDIUM | Pong-style, ROM only |
| 10 | PCB layout (KiCad) | LOW | After breadboard verified |

---

## Other Variants

### RV8-G (38 chips, full ISA, no microcode)

| # | Task | Status |
|:-:|------|:------:|
| 1 | Construct.md (pin-level) | ✅ |
| 2 | Verilog model | ⬜ |
| 3 | Testbench (all 35 instructions) | ⬜ |
| 4 | Assembler | ⬜ |
| 5 | ISA reference doc | ⬜ |
| 6 | Instruction trace | ⬜ |

### RV8 (27 chips, microcode)

- ✅ Designed, Verilog pass, docs done
- ⬜ Physical build

### RV8-R (18 chips)

- ⬜ Concept only
