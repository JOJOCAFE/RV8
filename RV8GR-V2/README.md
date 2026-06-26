# RV8-GR — No Microcode, Full 64K, IRQ (Stable)

**33 logic chips + ROM + RAM = 35 packages. Verilog verified.**

---

## Student Baseline Contract

This is the build target for RV8GR-V2. Do not add future features while
building the baseline CPU.

- **33 logic chips + ROM + RAM = 35 packages**
- **No microcode ROM**
- **No hardware IRQ vector**: IRQ is a polling latch only
- **Every instruction is 3 phases**: T0 fetch opcode, T1 fetch operand, T2 execute
- **Only one IBUS driver may be active at a time**
- **Only one DBUS driver may be active at a time**
- **Build one module, test it, then continue**

Recommended reading order:

| Role | Start here | Use for |
|------|------------|---------|
| Student | `doc/labs/README.md` | Lab-by-lab physical build |
| Teacher | `doc/build_plan/01_student_incremental_build_plan.md` | Supervised stage plan |
| Debug | `doc/06_debug_plan.md` | Probe points and fault tracing |
| Wiring | `doc/02_wiring_guide.md` | Official pin-level source of truth |
| KiCad | `doc/10_kicad_modules.md` | Schematic sheet/module split |

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 33 (74HC series, DIP) |
| Total packages | 35 (+ ROM + RAM) |
| ISA | 18 instructions |
| Clock | 1 MHz (breadboard), 5 MHz (PCB) |
| Speed | 333K instr/sec @ 1 MHz |
| Gate count | ~1,260 (logic only, excl. ROM/RAM) |
| Address | 64KB (ROM $0000-$7FFF, RAM $8000-$FFFF) |
| Bus | RV8-Bus 40-pin (A16+D8+control) |
| Registers | 8 in RAM ($8000-$8007 via DP=$80) |
| ALU | ADD, SUB, XOR |
| Jump | 16-bit (Page Register) |
| Execute RAM | Yes (PC ≥ $8000) |
| IRQ | v1.0: polling latch; hardware vector is future/unfrozen |

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

## BOM — Complete Order List

### Logic (33 chips)

| Part | Qty | Package | Notes |    |count|
|------|:---:|:-------:|-------|-----|-----|
| 74HC161 | 4 | 16DIP | PC counter |✅ |   |
| 74HC574 | 5 | 20DIP | IR, AC, PG, DP | ✅ | มี 6 ตัว|
| 74HC245 | 1 | 20DIP | Bus buffer |✅ | มี 3 ตัว|
| 74HC164 | 1 | 14DIP | Ring counter |✅ |   |
| 74HC283 | 2 | 16DIP | Adder |✅ |มี 10 ตัว   |
| 74HC86 | 3 | 14DIP | XOR |✅ |✅ |  |
| 74HC541 | 1 | 20DIP | AC buffer |✅ |  |
| 74HC157 | 8 | 16DIP | Muxes | ✅ |  มี 10 ตัว |
| 74HC74 | 2 | 14DIP | Z flag, IRQ |✅ |  |
| 74HC688 | 1 | 20DIP | Zero detect |✅ |  |
| 74HC04 | 1 | 14DIP | Inverters |✅ |  |
| 74HC32 | 1 | 14DIP | OR gates |✅ |  |
| 74HC00 | 2 | 14DIP | NAND gates |✅ |  |
| 74HC21 | 1 | 14DIP | SETDP decode | ✅ |มี 2 ตัว|

### Memory

| Part | Qty | Notes |
|------|:---:|-------|
| AT28C256-70 or SST39SF010A-70 | 1 | ROM 32KB, 70ns |waiting|  |
| 62256-70 (or AS6C62256) | 1 | RAM 32KB, 70ns |waiting|  |

### Clock & Reset

| Part | Qty | Notes |
|------|:---:|-------|
| 5 MHz crystal (HC49S) | 1 | Start clock |waiting|  |
| 22pF capacitor | 2 | Crystal load caps |waiting|  |
| 10kΩ resistor | 1 | Reset pull-up |waiting|  |
| 100nF capacitor | 1 | Reset RC |waiting|  |
| Push button (NO) | 1 | Reset button |waiting|  |

### Passives & Debug

| Part | Qty | Notes |
|------|:---:|-------|
| 100nF capacitor (ceramic) | 35 | Bypass (1 per chip) |waiting|  |
| 10µF capacitor | 2 | Power filter |waiting|  |
| 330Ω resistor | 8 | LED current limit |waiting|  |
| LED 3mm green | 8 | Bus probe |waiting|  |
| LED 3mm red | 1 | Power |waiting|  |
| DIP switch 8-bit | 1 | Debug input |waiting|  |

### Breadboard & Wiring

| Part | Qty | Notes |
|------|:---:|-------|
| Full-size breadboard (830pt) | 5 | Layout below |
| Jumper wire kit (M-M) | 1 | 65pc assorted |
| 22AWG solid wire (6 colors) | 1 set | Bus wiring |
| 40-pin IDC socket + ribbon | 1 | RV8-Bus |
| USB 5V breadboard PSU | 1 | Power supply |

---

## Breadboard Layout (5 boards)

```
Board 1: TIMING          Board 2: MEMORY         Board 3: ALU
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ U8  U24          │    │ U15 U16 U29 U30 │    │ U5  U6  U14     │
│ U1  U2  U3  U4  │    │ ROM         RAM  │    │ U19 U20         │
│ Crystal  Reset   │    │ U7               │    │ U12 U13         │
└──────────────────┘    └──────────────────┘    │ U10 U11         │
  6 chips                 7 chips               └──────────────────┘
                                                  9 chips

Board 4: CONTROL         Board 5: BUS + DEBUG
┌──────────────────┐    ┌──────────────────┐
│ U17 U18 U9      │    │ 40-pin IDC       │
│ U21 U22 U23     │    │ 8× LED probe     │
│ U25 U26 U27 U28│    │ DIP switch       │
│ U31 U32 U33     │    │ Power rails      │
└──────────────────┘    └──────────────────┘
  12 chips                Debug tools
```

### Wiring Color Convention

| Color | Signal |
|-------|--------|
| Red | VCC (+5V) |
| Black | GND |
| Yellow | DBUS D[7:0] |
| Blue | IBUS IB[7:0] |
| Green | ABUS A[15:0] |
| White | Control |
| Orange | Clock/Timing |

---

## Simulation

```bash
cd RV8GR-V2
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_full.v && vvp /tmp/tb.vvp
# === ALL TESTS PASSED === (127 cycles)

iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_irq.v && vvp /tmp/tb.vvp
# ALL IRQ POLLING TESTS PASSED

python3 sim/chip_sim.py
# ALL 8 CPU TESTS PASSED ✅

python3 sim/verify_wiring.py
# ALL WIRING VERIFIED ✅
```

---

## Files

```
RV8GR-V2/
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
    ├── 02_wiring_guide.md      SOURCE OF TRUTH (wiring)
    ├── 03_instruction_trace.md Pin-level traces
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
| 6 | Gate-level simulator | ✅ |
| 7 | Breadboard layout plan | ✅ |
| 8 | Order parts | ⬜ |
| 9 | Physical build (1 MHz) | ⬜ |
| 10 | Verify at 1-2 MHz | ⬜ |
| 11 | BASIC interpreter | ⬜ |
| 12 | Simple game | ⬜ |

### Task 6: Gate-Level Simulator ✅

All 35 chips simulated pin-by-pin. 8 CPU tests + 11K wiring checks pass.

```
sim/
├── chips/__init__.py       — 35 chip models
├── chips/test_chips.py     — 141 test vectors (14 chip types)
├── chip_sim.py             — Full CPU simulation + timing analysis
├── soft_debug.py           — High-level trace (4 tests)
├── gate_sim.py             — Simplified educational sim
├── verify_wiring.py        — Pin-level wiring checker (11K+ checks)
├── wiring.py               — 247 pin connections (02_wiring_guide)
└── sim_lab/lab01-14.py     — 14 step-by-step labs
```
