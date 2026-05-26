# RV8-GR — No Microcode, Full 64K, 16-bit Jump

**29 logic chips + ROM + RAM = 31 packages. Verilog verified.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 29 (74HC series) |
| Total packages | 31 (29 + ROM + RAM) |
| ISA | 15 instructions |
| Speed | 3.3 MIPS @ 10 MHz |
| Address space | 64KB (ROM $8000-$FFFF, RAM $0000-$7FFF) |
| Registers | 8 in RAM ($00-$07) |
| Control | Direct-encoded control byte, no microcode |
| ALU | ADD, SUB, XOR (8-bit) |
| Jump | 16-bit via Page Register (SETPG + J) |
| Execute from RAM | Yes (PC in $0000-$7FFF fetches from RAM) |

---

## ISA

    $00  NOP           $10  ADDI imm      $18  ADD rs
    $90  SUBI imm      $98  SUB rs        $70  XORI imm
    $78  XOR rs        $30  LI imm        $38  MV a0,rs
    $04  MV rd,a0      $02  BEQ addr      $82  BNE addr
    $01  J addr        $20  SETPG imm     $28  SETPG_R rs

---

## Chip List

| U# | Chip | Function |
|:--:|------|----------|
| U1-U4 | 74HC161 ×4 | PC (16-bit counter) |
| U5 | 74HC574 | IR_HIGH (control byte) |
| U6 | 74HC574 | IR_LOW (operand) |
| U7 | 74HC245 | Bus buffer (DBUS ↔ IBUS) |
| U8 | 74HC164 | Ring counter (T0,T1,T2) |
| U9 | 74HC574 | Accumulator |
| U10-U11 | 74HC283 ×2 | ALU adder |
| U12-U13 | 74HC86 ×2 | ALU XOR |
| U14 | 74HC541 | AC → IBUS buffer |
| U15-U16 | 74HC157 ×2 | Address mux A0-A7 |
| U17-U18 | 74HC157 ×2 | AC input mux |
| U19-U20 | 74HC157 ×2 | XOR B-input mux |
| U21 | 74HC74 | Z flag |
| U22 | 74HC688 | Zero detect |
| U23 | 74HC574 | Page Register |
| U24 | 74HC04 | Inverters |
| U25 | 74HC32 | OR gates |
| U26-U27 | 74HC00 ×2 | NAND gates |
| U28 | 74HC86 | Z_match + /T2 + WR_DIR |
| U29-U30 | 74HC157 ×2 | Address mux A8-A15 |

---

## Simulation

```bash
cd RV8GR
iverilog -o tb/sim_full.vvp rv8gr_cpu.v tb/tb_rv8gr_full.v
vvp tb/sim_full.vvp
# === ALL TESTS PASSED === (127 cycles)
gtkwave rv8gr_test.vcd
```

---

## Files

    RV8GR/
    ├── README.md
    ├── rv8gr_cpu.v              Verilog model (all tests pass)
    ├── tb/tb_rv8gr_full.v       Full ISA + 64K jump testbench
    └── doc/
        ├── Construct.md         SOURCE OF TRUTH (pin-level wiring)
        ├── 00_design.md         Architecture overview
        ├── 01_isa_reference.md  ISA encoding
        ├── 02_instruction_trace.md  Chip-level traces + test program
        └── 05_bank_switch.md    ROM/RAM expansion via bus

---

## Status

- ✅ Construct (pin-level, bus-centric, verified)
- ✅ Verilog (127 cycles, all 15 instructions pass)
- ✅ Full 64K address space (ROM + RAM)
- ✅ 16-bit jump (Page Register)
- ✅ Execute from RAM
- ✅ Expandable (ROM bank, RAM pages via bus)
- ⬜ Assembler
- ⬜ Physical build
