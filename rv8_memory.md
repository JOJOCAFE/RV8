# RV8 Project — Session Memory

**Last updated**: 2026-05-27 04:50

---

## Active: RV8-GR (ready for physical build)

### Architecture (29 chips):
- 3-cycle, ring counter, no microcode
- Full 64K: ROM $8000-$FFFF, RAM $0000-$7FFF, A15 chip select
- Execute from RAM, Page Register for 16-bit jump
- 15 instructions, XOR only (no AND/OR — use RV8-G for that)

### Done:
- ✅ Construct.md (pin-level, bus-centric, verified)
- ✅ Verilog (127 cycles pass)
- ✅ Assembler (rv8gr_asm.py, labels, macros)
- ✅ Test ROM (testrom.bin, 187 cycles, 10 test groups)
- ✅ All docs (ISA, traces, wiring, modules Thai, bank switch)

### Next:
- ⬜ Parts list → order chips
- ⬜ Programmer board test (ESP32 flash SST39SF010A)
- ⬜ Physical breadboard build

---

## Active: RV8-G (Construct done, needs Verilog)

### Architecture (38 chips):
- 4-cycle, B-register, no microcode
- Full 35-instruction ISA (ADD/SUB/AND/OR/XOR/SLL/SRL/SLT + branches + JAL/JALR + PUSH/POP)
- Same bus, same memory map

### Done:
- ✅ Construct.md (pin-level)

### Next:
- ⬜ Verilog model
- ⬜ Testbench
- ⬜ Assembler

---

## Stable: RV8 (27 chips, microcode)
- ✅ Full design, Verilog, docs, labs
- ⬜ Physical build

---

## Key files:
    RV8GR/doc/Construct.md       ← RV8-GR source of truth
    RV8GR/rv8gr_cpu.v            ← Verilog (pass)
    RV8GR/tools/rv8gr_asm.py     ← assembler
    RV8GR/programs/testrom.bin   ← flash this to test hardware
    RV8G/doc/Construct.md        ← RV8-G source of truth
