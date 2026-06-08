# RV8-GR — No Microcode, Full 64K, IRQ (Stable)

**33 logic chips + ROM + RAM = 35 packages. Verilog verified.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 33 (74HC series, DIP) |
| Total packages | 35 (+ ROM + RAM) |
| ISA | 18 instructions |
| Clock | 5 MHz (start), 10 MHz (target) |
| Speed | 1.67 MIPS @ 5 MHz, 3.3 MIPS @ 10 MHz |
| Gate count | ~1,260 (logic only, excl. ROM/RAM) |
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

### Logic (33 chips)

| Part | Qty | Function |
|------|:---:|----------|
| 74HC161 | 4 | PC counter |
| 74HC574 | 5 | IR, AC, Page Reg, Data Page |
| 74HC21 | 1 | SETDP decode (4-input AND) |
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
| AT28C256-70 or SST39SF010A-70 | 1 | ROM 32KB, 70ns |
| 62256-70PC | 1 | RAM 32KB |
| 5 MHz crystal (start), 10 MHz (target) | 1 | + 2× 20pF caps |
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
    └── 09_task_test_plan.md    Test milestones
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
| 4 | Design sign-off | ✅ |
| 5 | Programmer tools | ✅ |
| 6 | Gate-level simulator (chip_sim.py) | ⬜ |
| 7 | Breadboard layout plan | ⬜ |
| 8 | Physical build (5 MHz) | ⬜ |
| 9 | Verify at 10 MHz | ⬜ |
| 10 | BASIC interpreter | ⬜ |
| 11 | Simple game | ⬜ |

### Task 6: Gate-Level Simulator (Next)

Pin-accurate Python simulation of all 35 chips. Design: `sim/chip_sim_design.md`

```
sim/
├── chips/base.py           — Chip + TristateBus + Simulator engine
├── chips/sequential.py     — HC574, HC161, HC164, HC74
├── chips/combinational.py  — HC04, HC00, HC32, HC86, HC157, HC283, HC245, HC541, HC688, HC21
├── chips/memory.py         — ROM, RAM
├── wiring.py               — All connections from 03_wiring_guide.md
└── chip_sim.py             — Main entry + probe + LED-style testing
```
