# RV8-GR — No Microcode, Full 64K, IRQ (Stable)

**31 logic chips + ROM + RAM = 33 packages. Verilog verified.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 31 (74HC series, DIP) |
| Total packages | 33 (+ ROM + RAM) |
| ISA | 18 instructions |
| Clock | 10 MHz |
| Speed | 3.3 MIPS |
| Gate count | ~1,250 (logic only, excl. ROM/RAM) |
| Address | 64KB (ROM $8000+, RAM $0000+) |
| Bus | RV8-Bus 40-pin (A16+D8+control) |
| Registers | 8 in RAM ($00-$07) |
| ALU | ADD, SUB, XOR |
| Jump | 16-bit (Page Register) |
| Execute RAM | Yes |
| IRQ | Fixed vector $FF00 |

---

## ISA (18 instructions)

```
$00  NOP         $01  J addr       $02  BEQ addr
$04  SB addr     $08  EI           $10  ADDI imm
$18  ADD rs      $20  SETPG imm    $28  SETPG_R rs
$30  LI imm      $38  LB rs        $40  SETDP imm
$48  DI           $70  XORI imm    $78  XOR rs
$82  BNE addr    $90  SUBI imm     $98  SUB rs
```

Encoding: `[7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP`

---

## BOM

### Logic (31 chips)

| Part | Qty | Function |
|------|:---:|----------|
| 74HC161 | 4 | PC counter |
| 74HC574 | 7 | IR, AC, Page Reg, Data Page |
| 74HC245 | 1 | Bus buffer |
| 74HC164 | 1 | Ring counter |
| 74HC283 | 2 | Adder |
| 74HC86 | 3 | XOR |
| 74HC541 | 1 | AC buffer |
| 74HC157 | 8 | Muxes |
| 74HC74 | 2 | Z flag, IRQ |
| 74HC688 | 1 | Zero detect |
| 74HC04 | 1 | Inverters |
| 74HC32 | 1 | OR gates |
| 74HC00 | 2 | NAND gates |

### Memory & Support

| Part | Qty | Notes |
|------|:---:|-------|
| AT28C256-15PU | 1 | ROM 32KB |
| 62256-70PC | 1 | RAM 32KB |
| 10 MHz crystal | 1 | + 2× 20pF caps |
| 100nF capacitors | ~20 | Bypass |
| LEDs (red, green) | 2 | Power + activity |
| 40-pin IDC socket | 1 | RV8-Bus |

---

## Simulation

```bash
cd RV8GR
iverilog -o tb/sim_full.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_full.v
vvp tb/sim_full.vvp
# === ALL TESTS PASSED === (127 cycles)

iverilog -o tb/sim_irq.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_irq.v
vvp tb/sim_irq.vvp
# === ALL IRQ TESTS PASSED ===
```

---

## Files

```
RV8GR/
├── rtl/
│   └── rv8gr_cpu.v             Verilog (all tests pass)
├── tb/
│   ├── tb_rv8gr_full.v         Full ISA testbench (127 cycles)
│   ├── tb_rv8gr_irq.v          IRQ testbench (6 tests)
│   ├── tb_rv8gr_tasks.v        Milestone tests
│   └── tb_rv8gr_asm.v          Assembled binary loader
├── tools/
│   ├── rv8gr_asm.py            Assembler
│   └── test_rv8gr_asm.py       Assembler tests
├── programs/
│   ├── test_all.asm            Full ISA test
│   ├── test_isa.asm            ISA subset test
│   ├── testrom.asm             Test ROM image
│   └── countdown.asm           Demo program
├── sim/
│   └── gate_sim.py             Python gate-level simulation
└── doc/
    ├── 00_design_isa.md        Design + ISA reference
    ├── 02_instruction_trace.md Pin-level traces
    ├── 03_wiring_guide.md      SOURCE OF TRUTH (wiring)
    ├── 04_bank_switch.md       Memory expansion
    ├── 05_understand_by_module.md  Thai tutorial
    ├── 06_debug_plan.md        Physical build debug steps
    ├── 07_risk_analysis.md     Hazard analysis
    ├── 08_design_signoff.md    Sign-off v1.0
    └── task_test_plan.md       Test milestones
```

---

## Status

| Item | Status |
|------|:------:|
| Wiring guide (pin-level) | ✅ |
| Verilog (full ISA + IRQ) | ✅ |
| Assembler (Python) | ✅ |
| Test ROM (.bin) | ✅ |
| BOM (parts list) | ✅ |
| Programmer tools | ✅ |
| Physical build | ⬜ |

---

## Roadmap

| # | Task | Status |
|:-:|------|:------:|
| 1 | Assembler | ✅ |
| 2 | Test ROM | ✅ |
| 3 | Parts list | ✅ |
| 4 | Programmer test | ⬜ |
| 5 | Breadboard layout | ⬜ |
| 6 | Physical build | ⬜ |
| 7 | First program | ⬜ |
