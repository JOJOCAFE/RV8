# RV8-GR — No Microcode, Full 64K, 16-bit Jump

**30 logic chips + ROM + RAM = 32 packages. Verilog verified.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 30 (74HC series) |
| Total packages | 32 (30 + ROM + RAM) |
| ISA | 17 instructions (15 + EI/DI) |
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
    $08  EI            $48  DI

---

## Chip List (30 logic chips)

| U# | Chip | Function | DIP Pins |
|:--:|------|----------|:--------:|
| U1-U4 | 74HC161 ×4 | PC (16-bit counter) | 16 ×4 |
| U5 | 74HC574 | IR_HIGH (control byte) | 20 |
| U6 | 74HC574 | IR_LOW (operand) | 20 |
| U7 | 74HC245 | Bus buffer (DBUS ↔ IBUS) | 20 |
| U8 | 74HC164 | Ring counter (T0,T1,T2) | 14 |
| U9 | 74HC574 | Accumulator | 20 |
| U10-U11 | 74HC283 ×2 | ALU adder | 16 ×2 |
| U12-U13 | 74HC86 ×2 | ALU XOR | 14 ×2 |
| U14 | 74HC541 | AC → IBUS buffer | 20 |
| U15-U16 | 74HC157 ×2 | Address mux A0-A7 | 16 ×2 |
| U17-U18 | 74HC157 ×2 | AC input mux | 16 ×2 |
| U19-U20 | 74HC157 ×2 | XOR B-input mux | 16 ×2 |
| U21 | 74HC74 | Z flag | 14 |
| U22 | 74HC688 | Zero detect | 20 |
| U23 | 74HC574 | Page Register | 20 |
| U24 | 74HC04 | Inverters | 14 |
| U25 | 74HC32 | OR gates | 14 |
| U26-U27 | 74HC00 ×2 | NAND gates | 14 ×2 |
| U28 | 74HC86 | Z_match + /T2 + WR_DIR | 14 |
| U29-U30 | 74HC157 ×2 | Address mux A8-A15 | 16 ×2 |
| U31 | 74HC74 | IRQ_FF + IE_FF | 14 |

---

## BOM — Full Parts List

### Logic Chips (30)

| Part | Qty | Package | Notes |
|------|:---:|:-------:|-------|
| 74HC161 | 4 | 16DIP | PC counter |
| 74HC574 | 6 | 20DIP | IR, AC, Page Reg |
| 74HC245 | 1 | 20DIP | Bus buffer |
| 74HC164 | 1 | 14DIP | Ring counter |
| 74HC283 | 2 | 16DIP | ALU adder |
| 74HC86 | 3 | 14DIP | ALU XOR, misc |
| 74HC541 | 1 | 20DIP | Buffer |
| 74HC157 | 8 | 16DIP | Muxes |
| 74HC74 | 2 | 14DIP | Z flag, IRQ |
| 74HC688 | 1 | 20DIP | Zero detect |
| 74HC04 | 1 | 14DIP | Inverters |
| 74HC32 | 1 | 14DIP | OR gates |
| 74HC00 | 2 | 14DIP | NAND gates |

### Memory

| Part | Qty | Package | Notes |
|------|:---:|:-------:|-------|
| AT28C256-15PU | 1 | 28DIP | ROM 32KB, 150ns, 5V |
| 62256-70PC | 1 | 28DIP | RAM 32KB, 70ns, 5V |

### Passives

| Part | Qty | Notes |
|------|:---:|-------|
| 100nF capacitor | ~20 | Bypass caps near each IC |
| 10µF capacitor | 2 | Power filtering |

### Crystal / Clock

| Part | Qty | Notes |
|------|:---:|-------|
| 10 MHz crystal | 1 | HC49S package |
| 20pF capacitor | 2 | Crystal load caps |

### LEDs

| Part | Qty | Notes |
|------|:---:|-------|
| Red LED 3mm | 1 | Power indicator |
| Green LED 3mm | 1 | Activity/clock indicator |

### Power

| Part | Qty | Notes |
|------|:---:|-------|
| 5V regulator (7805) | 1 | TO-220 |
| 100µF capacitor | 1 | Input filter |
| 10µF capacitor | 1 | Output filter |

### Connectors

| Part | Qty | Notes |
|------|:---:|-------|
| 40-pin IDC socket | 1 | For RV8-Bus |
| 2.54mm pin header | ~40 | General I/O |

### Total

| Category | Qty |
|----------|:---:|
| Logic chips | 30 |
| ROM | 1 |
| RAM | 1 |
| Capacitors | ~25 |
| LEDs | 2 |
| Crystal | 1 |
| Regulators | 1 |
| Connectors | ~40 pins |

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
- ✅ Verilog (127 cycles + IRQ tests, all 17 instructions pass)
- ✅ Full 64K address space (ROM + RAM)
- ✅ 16-bit jump (Page Register)
- ✅ Execute from RAM
- ✅ Expandable (ROM bank, RAM pages via bus)
- ⬜ Assembler
- ⬜ Physical build

---

## Roadmap to Physical Build

| # | Task | Status | Notes |
|:-:|------|:------:|-------|
| 1 | Assembler (Python) | ✅ | labels, macros, .bin output |
| 2 | Test ROM image (.bin) | ✅ | 10 test groups, 187 cycles pass |
| 3 | Parts list | ⬜ | Exact part numbers, DIP packages |
| 4 | Programmer board test | ⬜ | Verify ESP32 can flash SST39SF010A |
| 5 | Breadboard layout plan | ⬜ | 4-5 boards, minimize wire length |
| 6 | Physical build | ⬜ | Module by module, test each stage |
| 7 | First program running | ⬜ | LED blink or counter on real hardware |
