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

## BOM — Complete Order List

### Logic (33 chips)

| Part | Qty | Package | Notes |
|------|:---:|:-------:|-------|
| 74HC161 | 4 | 16DIP | PC counter |
| 74HC574 | 5 | 20DIP | IR, AC, PG, DP |
| 74HC245 | 1 | 20DIP | Bus buffer |
| 74HC164 | 1 | 14DIP | Ring counter |
| 74HC283 | 2 | 16DIP | Adder |
| 74HC86 | 3 | 14DIP | XOR |
| 74HC541 | 1 | 20DIP | AC buffer |
| 74HC157 | 8 | 16DIP | Muxes |
| 74HC74 | 2 | 14DIP | Z flag, IRQ |
| 74HC688 | 1 | 20DIP | Zero detect |
| 74HC04 | 1 | 14DIP | Inverters |
| 74HC32 | 1 | 14DIP | OR gates |
| 74HC00 | 2 | 14DIP | NAND gates |
| 74HC21 | 1 | 14DIP | SETDP decode |

### Memory

| Part | Qty | Notes |
|------|:---:|-------|
| AT28C256-70 or SST39SF010A-70 | 1 | ROM 32KB, 70ns |
| 62256-70 (or AS6C62256) | 1 | RAM 32KB, 70ns |

### Clock & Reset

| Part | Qty | Notes |
|------|:---:|-------|
| 5 MHz crystal (HC49S) | 1 | Start clock |
| 22pF capacitor | 2 | Crystal load caps |
| 10kΩ resistor | 1 | Reset pull-up |
| 100nF capacitor | 1 | Reset RC |
| Push button (NO) | 1 | Reset button |

### Passives & Debug

| Part | Qty | Notes |
|------|:---:|-------|
| 100nF capacitor (ceramic) | 35 | Bypass (1 per chip) |
| 10µF capacitor | 2 | Power filter |
| 330Ω resistor | 8 | LED current limit |
| LED 3mm green | 8 | Bus probe |
| LED 3mm red | 1 | Power |
| DIP switch 8-bit | 1 | Debug input |

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

### Task 6: Gate-Level Simulator (In Progress)

Pin-accurate Python simulation of all 35 chips. Design: `sim/chip_sim_design.md`

**Done:**
- [x] All 35 chip objects with correct pin layout
- [x] All 14 chip type behaviors (combinational + sequential + memory)
- [x] Probe + DipSwitch test tools
- [x] 141 test vectors, all pass
- [x] Wiring definition (145 wires, 444 pin endpoints)

**Next:**
- [ ] Propagation engine (chip_sim.py) — steps clock, resolves shared wires
- [ ] Full CPU test: LI $42 executes correctly
- [ ] Integration: run test_setdp.asm through gate-level sim

```
sim/
├── chips/__init__.py       — 35 chips with behavior (done)
├── chips/test_chips.py     — 141 test vectors (done)
├── wiring.py               — all connections (done)
├── chip_sim_design.md      — design doc (done)
├── chip_sim.py             — propagation engine (next)
└── soft_debug.py           — high-level sim (done)
```
