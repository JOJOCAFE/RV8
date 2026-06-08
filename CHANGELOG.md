# RV8 Project — Changelog

## 2026-06-09 — v3.3: SETDP + Full 64KB Data Access

### New Feature
- **SETDP $40**: Data Page Register (U32 74HC574) — full 64KB data access
- **U33 74HC21**: SETDP decode (4-input AND gate) — pin-level finalized
- Data address = {DP, operand} = 16-bit (ROM read + RAM read/write)
- 32 logic chips, 18 instructions
- IRQ save-PC: documented as software-based for v1.0 build

### Tests
- `tb_rv8gr_setdp.v`: 5KB RAM write/read + ROM read (160 cycles, PASS)
- All existing tests still pass (127 + IRQ + tasks)

### Documentation
- All docs updated for 32 chips / 18 instructions / 64KB data
- DP_Load decode finalized (U33 74HC21 pin-level wiring)
- IRQ save-PC path documented (software approach for v1.0)
- Opcode map updated with SETDP at $40

## 2026-06-09 — v3.2: RV8-GR Design Sign-off

### Design Review
- **Risk analysis**: 10 hazards analyzed, all resolved
- **SRC+STR guard**: Hardware fix applied (U25 gate 3 → U7-19)
- **Bus definition**: RV8-Bus v2 (40-pin, CLK, /IRQ, /SLOT1-2)
- **Design sign-off**: Approved for physical build

### Documentation Rewrite (Stable)
- Merged 00_design + 01_isa_reference → `00_design_isa.md`
- Merged Construct.md → `03_wiring_guide.md` (official source of truth)
- Rewrote `02_instruction_trace.md` (compact, 7 traces)
- Rewrote `05_understand_by_module.md` (Thai tutorial, 15 sections + design rationale)
- Created `06_debug_plan.md` (14-step physical build guide)
- Created `07_risk_analysis.md` (10 hazards)
- Created `08_design_signoff.md` (final sign-off)
- Moved rv8gr_cpu.v → `rtl/` folder
- Removed obsolete files (Construct.md, tb_rv8gr_cpu.v, TASKS.md)

### Key Discoveries
- **Free NOT instruction** ($B0/$B8): ALU mode 101 = NOT(operand), 0 hardware cost
- **Opcode space**: 17 used (6.6%), 175 deterministic (68.4%), 64 forbidden (25%)
- **All 256 opcodes** produce deterministic behavior (horizontal control)

## 2026-06-08 — v3.1: Programmer Tools Complete

### Features
- **rv8flash.py**: Flash ROM via ESP32 (540 lines, 16 tests)
- **rv8ram-boot.py**: Upload to RAM via bootloader (430 lines, 15 tests)
- **rv8term.py**: Terminal bridge PC↔CPU (289 lines, 15 tests)
- **Test suites**: 46 tests, all passing

### Requirements Documents
- rv8flash-requirement.md — Full specification
- rv8ram-boot-requirement.md — Bootloader protocol
- rv8term-requirement.md — Terminal mode
- rv8_programmer-requirement.md — ESP32 firmware spec

### Documentation Updates
- README.md — Updated PC Software section with tool reference
- schematic.md — Added Section 6: Software (protocol, tools, tests)

### Files Added
```
Programmer/tools/
├── rv8flash.py           # ROM flash tool
├── rv8ram-boot.py        # RAM upload tool
├── rv8term.py            # Terminal tool
├── test_rv8flash.py      # 16 unit tests
├── test_rv8ram-boot.py   # 15 unit tests
├── test_rv8term.py       # 15 unit tests
├── rv8flash-requirement.md
├── rv8ram-boot-requirement.md
└── rv8term-requirement.md

Programmer/firmware/
└── rv8_programmer-requirement.md
```

### Serial Protocol
| Command | Action |
|---------|--------|
| `?` | Check connection → `Connected` |
| `F` + len + data | Flash ROM |
| `V` | Read ROM (32KB) |
| `R` | Reset CPU |

### VirtualESP32 Class
All tools use VirtualESP32 class at top for pin definitions (NodeMCU-32S defaults).

## 2026-06-06 — v3.0: IRQ + Python Simulation + Codeberg

### Features
- **IRQ Support**: Added EI ($08) and DI ($48) instructions
- **Interrupt Controller**: 74HC74 (U31) for IRQ latch and IE flag
- **Vectored Interrupt**: Fixed vector $FF00, auto-save PC to RAM[$0E:$0F]
- **Python Simulation**: sim/gate_sim.py — gate-level educational model

### Changes
- Logic chips: 29 → 30 (+1 for IRQ flip-flop)
- Instructions: 15 → 17 (+EI, +DI)

### New Files
- `RV8GR/tb/tb_rv8gr_irq.v` — IRQ testbench (6 tests)
- `RV8GR/tb/tb_rv8gr_tasks.v` — milestone tests
- `RV8GR/sim/gate_sim.py` — Python chip simulation
- `RV8GR/tools/test_rv8gr_asm.py` — assembler unit tests
- `RV8GR/doc/task_test_plan.md` — test milestones

### Documentation Updates
- All docs updated: 30 chips, 17 instructions, IRQ section
- Construct.md: U31 wiring, EI/DI in ISA table

### Repository
- Moved to Codeberg: https://codeberg.org/JOJOCAFE/RV8

## 2026-05-27 — v2.0: RV8-GR Complete Redesign

### Features
- **Full 64K**: A15 chip select (ROM $8000-$FFFF, RAM $0000-$7FFF)
- **16-bit Jump**: Page Register for full address space
- **Execute from RAM**: PC in $0000-$7FFF fetches from RAM
- **Expandable**: ROM bank (A16), RAM pages via bus

### Architecture (29 chips)
- PC: 4× 74HC161
- IR: 2× 74HC574 (control + operand)
- Page Reg: 74HC574
- Accumulator: 74HC574
- ALU: 2× 74HC283 (adder) + 2× 74HC86 (XOR)
- Muxes: 8× 74HC157 (address, AC, XOR B-input)
- Control: 74HC245, 74HC164, 74HC541, 74HC74, 74HC688, 74HC04, 74HC32, 4× 74HC00, 74HC86

### ISA (15 instructions)
- ALU: ADDI, ADD, SUBI, SUB, XORI, XOR
- Move: LI, LB (MV a0,rs), SB (MV rd,a0)
- Control: BEQ, BNE, J, SETPG, SETPG_R

### Verification
- Verilog: 127 cycles, ALL TESTS PASSED
- Assembler: rv8gr_asm.py with labels, macros, .bin output
- Test ROM: testrom.bin — 10 test groups, 187 cycles

### Documentation
- Construct.md: pin-by-pin, bus-centric (source of truth)
- 00_design.md, 01_isa_reference.md, 02_instruction_trace.md
- 03_wiring_guide.md, 04_understand_by_module.md, 05_bank_switch.md

## 2026-05-16 to 2026-05-17 — v1.0: Initial RV8-GR

- 21 logic chips, ROM at $8000, 256-byte jump range
- Verilog 11/11 unit tests pass
- Assembler with basic features
- Full documentation set

## 2026-05-15 — RV8 Family

- **RV8**: 27 chips, microcode, Verilog 8/8 pass
- **RV8-R**: 18 chips concept (RAM registers)
- **RV8-G**: 28 chips concept (full ISA, no microcode)
- **RV8-GR**: 21 chips concept (reduced ISA, no microcode)

## 2026-05-10 to 2026-05-14 — Project Start

- Original designs explored and archived
- Programmer board (ESP32 + TXB0108) complete
- Reference study: Gigatron, SAP-1, Nand2Tetris