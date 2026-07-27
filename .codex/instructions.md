# RV8 — Codex Instructions

## Project

8-bit CPU (RV8-GR) built from 74HC logic on breadboards. Audience: Thai middle school students.
Repo: CPU architecture, Verilog RTL, gate-level simulation, assembler, test programs, hardware labs.

## Architecture (frozen v1.0)

- 36 packages: 34 logic + ROM + RAM
- 3-cycle: T0 fetch control, T1 fetch operand, T2 execute
- Horizontal control: opcode bits ARE the control word (no decoder)
- Encoding: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
- 18 instructions + SETDP + IRQ (polling v1.0)
- Memory: ROM $0000–$7FFF, RAM $8000–$FFFF, A15 chip-select
- Clock: 5 MHz target (70ns ROM/RAM)
- 64 forbidden opcodes: (opcode & $0C) == $0C (bus fight)

## Team

| Name | Role | Scope |
|------|------|-------|
| Pim | Coordinator | Route tasks, never code |
| Bank | Architect | ISA, chip selection, design decisions |
| Fern | Verifier | Test all coder output, defect reports |
| Mint | RTL Coder | Verilog, testbenches, gate-level sim |
| Ohm | HW Coder | Circuits, wiring, breadboard, KiCad |
| Bam | SW Coder | Assembler, tools, ROM images, firmware |
| Noon | Docs Writer | Thai labs, guides, student materials |

## Rules

- No code ships without non-author verification.
- Every RTL change → verifier runs testbenches.
- Every wiring change → verifier + architect review.
- Source of truth for wiring: `RV8GR/doc/02_wiring_guide.md`.
- Source of truth for ISA: `RV8GR/doc/00_design_isa.md`.
- Chip budget frozen at 34 logic. No additions without architect approval.
- All 256 opcodes produce deterministic behavior.
- Four-model equivalence: behavioral Verilog = chip-level Verilog = gate-sim Python = physical hardware.

## Debugging

1. Reproduce in BOTH Verilog AND chip_sim.py
2. Trace the fail path (PC/AC/IBUS/address/control at T0/T1/T2)
3. Falsify — disproof first (bus contention? timing race? wrong wiring? logic error?)
4. Record in breadcrumb ledger

## Wiring Discipline

- Single bus driver per cycle (A15 chip select enforces ROM/RAM)
- Active-low signals: `/` prefix (e.g., `/OE`, `/WE`, `/CE`)
- Chips referenced by U-number (U1–U33)
- Pin numbers required in all wiring references
- Unused inputs tied high or low per datasheet
- Decoupling cap per IC

## File Layout

```
RV8GR/
├── rtl/rv8gr_cpu.v       Behavioral Verilog (all tests pass)
├── tb/                   Testbenches
├── tools/rv8gr_asm.py    Assembler
├── programs/             .asm/.bin test programs
├── sim/chip_sim.py       Gate-level Python simulation (35 chips)
├── sim/wiring.py         247 pin connections
└── doc/                  Design docs + Thai labs
```

## Test Commands

```bash
# Verilog regression
cd RV8GR && bash run_all_verilog_tb.sh

# Gate-level sim
cd RV8GR/sim && python3 chip_sim.py ../programs/test_all.bin --trace

# Assembler
cd RV8GR && python3 tools/rv8gr_asm.py programs/test_all.asm -o programs/test_all.bin
```

## Thai Labs Style

- Structure: เป้าหมาย → ความรู้พื้นฐาน → อุปกรณ์ → ผังวงจร → ขั้นตอน → ทดสอบ → เช็คลิสต์
- One concept per lab, pin numbers always, short sentences
- Thai for explanation, English for technical terms
- Full chip name on first mention: "U7 (74HC86, Quad XOR)"

## Shared Components

Reusable chip models live at `/home/jo/kiro/Components` (separate repo).
Pinouts must cite manufacturer DIP evidence. Python and Verilog behavior must agree.
