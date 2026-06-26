# RV8 Project — Changelog

## 2026-06-26 — v4.1: Programmer Dual-Mode RV8GR-V2 Compatibility

### Programmer
- **Programmer/firmware/firmware.ino**: RUN mode now releases both `/WR` and `/RD`; PROG mode reclaims `/WR` before ROM write cycles
- **Programmer/tools/rv8term.py**: Normal terminal mode now starts directly in RUN mode without sending the PROG-only `?` handshake; `-c` remains the explicit connection check
- **Programmer/tools/rv8flash.py**: Added RV8GR-V2 documented command aliases: `program FILE --base 0x0000` and `verify FILE --base 0x0000`; nonzero `--base` fails loudly
- **Programmer/tools/test_rv8flash.py** and **test_rv8term.py**: Added regression coverage for RV8GR-V2 CLI aliases and PROG/RUN handshake boundary
- **Programmer/README.md**, **schematic.md**, and requirement docs: Documented ZIF-direct vs RV8-Bus in-system use, never-both safety rule, and AT28C256 SDP limitation

### RV8GR-V2 Integration
- **RV8GR-V2/doc/02_wiring_guide.md**: Clarified that ROM `/WE` connects to RV8-Bus `/WR` pin 27 for Programmer support, and that current firmware does normal byte writes unless SDP unlock is added
- **RV8GR-V2/doc/labs/lab05_rom_buffer.md**: Separated early standalone ROM `/WE -> 5V` lab wiring from final Programmer/RV8-Bus `/WE -> /WR` wiring
- **RV8GR-V2/doc/labs/lab13_full_system.md**, **lab14_irq_bus.md**, and **doc/06_debug_plan.md**: Updated Programmer command examples to the actual `Programmer/tools/rv8flash.py` path and RV8GR-V2-compatible command form

### KiCad Exports
- Regenerated `Programmer/KICAD/RV8Programmer.pdf`
- Regenerated `Programmer/KICAD/RV8Programmer.svg` and `Programmer/KICAD/RV8Programmer/RV8Programmer.svg` with KiCad 10.0.4

### Verification
- `python3 -m unittest discover -s Programmer/tools -p 'test_*.py'` — 36 tests pass
- `python3 RV8GR-V2/sim/verify_wiring.py` — all wiring verified
- `python3 RV8GR-V2/tools/test_rv8gr_asm.py` — 11 tests pass
- Cleaned Python caches and Zone.Identifier artifacts after validation

## 2026-06-26 — v4.0: RV8GR-V2 Student Build Guardrails

### Documentation
- **RV8GR-V2/README.md**: Added Student Baseline Contract and recommended reading order for student, teacher, debug, wiring, and KiCad paths
- **RV8GR-V2/doc/build_plan/01_student_incremental_build_plan.md**: Added baseline contract, explicit temporary-wire removal checks, "do not add" warnings for vector/IRQ upgrade wiring, and stage checklist field for temporary wires
- **RV8GR-V2/doc/06_debug_plan.md**: Added Baseline Boundary and Probe Point Map for clock/reset, buses, control signals, PC, PG, DP, IRQ, and latch debug
- **RV8GR-V2/doc/labs/README.md**: Added Thai V2 baseline rules for students
- **RV8GR-V2/doc/04_bank_switch.md**: Marked ROM banking as future-only, not part of the student baseline
- **Top-level README.md**: Updated project routing to make RV8GR-V2 the active 33-chip student baseline

### Cleanup
- **RV8GR-V2/.gitignore**: Added rules for `*.pyc` and `*:Zone.Identifier*`
- Removed generated VCD/VVP traces, Python caches, and Windows Zone.Identifier metadata from RV8GR-V2

### Verification
- `python3 RV8GR-V2/tools/test_rv8gr_asm.py` — 11 tests pass
- `python3 RV8GR-V2/sim/chip_sim.py` — 8 CPU tests pass
- `python3 RV8GR-V2/sim/verify_wiring.py` — all wiring verified
- Icarus Verilog benches pass: full, IRQ polling, SETDP, tasks, assembler ROM, opcode sweep
- Opcode sweep: 512 cases pass

## 2026-06-21 — v3.9: KiCad Module Definitions

### Documentation
- **doc/10_kicad_modules.md**: Split 35-chip CPU into 6 hierarchical KiCad sheets
  - CLK_RST (U8), PC (U1-U4), ADDR_MEM (U15/U16/U29/U30+ROM+RAM), IR_BUF (U5-U7,U14), ALU_AC (U9-U13,U17-U22), CTRL (U23-U28,U31-U33)
  - Full sheet port tables, pin-level wiring, inter-module signal names
  - Aligned with debug plan (14 steps) and hardware labs (14 labs)
  - Build/test order matches existing bring-up sequence

### Verification
- All 35 chips accounted for (no duplicates, no gaps)
- Cross-referenced with 02_wiring_guide.md (source of truth) — all pin assignments match
- Module boundaries consistent with 05_understand_by_module.md groupings

## 2026-06-19 — v3.8: Opcode Sweep, Page-Safe Assembler, Skills

### Verification
- **tb_rv8gr_opcode_sweep.v**: New exhaustive testbench — tests all 256 opcodes × Z={0,1} = 512 cases against horizontal control equations
- All 5 testbenches pass: full (127 cycles), IRQ, SETDP (160 cycles), tasks, opcode sweep (512 cases)
- chip_sim.py 8/8, soft_debug.py 4/4 — no regressions

### Assembler (tools/rv8gr_asm.py)
- Cross-page validation: J/BEQ/BNE error if target is on different page than PC
- Overlap detection: error if two instructions write the same ROM address
- Duplicate label detection
- `memh` output format for Verilog `$readmemh`
- `AssemblerError` exception class for clean error handling

### Documentation
- **doc/11_future_upgrades.md**: Documents potential v1.1/v2.0 improvements extracted from Codex evaluation (clock qualification, hardware DI, I/O decode, reset supervisor)
- Clock targets clarified: 1 MHz breadboard, 4 MHz PCB (no hardware changes needed)

### Skills (new)
- **debug-mantra**: 4-step hardware debugging discipline adapted from 9arm-skills (reproduce → trace → falsify → breadcrumbs), with RV8-specific hazard checklist and sim layers
- **scrutinize**: Outsider design review adapted from 9arm-skills, with chip:pin signal tracing, ISA encoding safety, 33-chip budget awareness

### Cleanup
- Evaluated RV8GR-Codex (40-chip AI redesign): rejected as unauthorized/unnecessary at 1 MHz; extracted useful assembler safety and opcode sweep TB
- Evaluated 7 external GitHub repos: only 9arm-skills had applicable content

## 2026-06-16 — v3.7: Documentation Freeze & Consistency Pass

### Architecture Documentation (ALL FROZEN 🔒)
- **00_design_isa.md**: Added Architectural Invariants (7 rules), Hardware Freeze Policy (9 signals), Signal Naming Convention (suffix rules), Reset Contract, Forbidden Bus States, Instruction Trace Contract (13-field canonical format), Illegal Opcode Behavior (18/174/64 split with examples), Expansion Budget normalized (v1.0=35, v1.1=37, remaining=3)
- **02_wiring_guide.md**: Added Critical Timing Paths table (6 paths), Critical Nets Summary (12 key signals with source/dest pins), IRQ_FF clear wording fixed (v1.0 = /RST only)
- **03_instruction_trace.md**: Added Trace 10 (Forbidden Opcode $0C), Trace 11 (Boot Sequence 9-clock), Golden Trace (12-cycle regression reference), all signal clarifications
- **04_bank_switch.md**: Added v2.x Banking Contract (2-bit/128KB/74HC74), Banked Address Formula, Reserved I/O Table ($FF10), Compatibility Contract, Interrupt Safety Rule
- **06_debug_plan.md**: Added Step 0 (Boot Sanity Check), Bus Ownership Verification, Clock Integrity, Floating Input Audit, Memory Contention Test, Walking-1/RAM March, Ring Counter State Matrix, Clock Sweep, Power Integrity, Reset Recovery, Golden Bring-up Program (20-byte ROM image), Burn-in test, IRQ_FF sticky note
- **05_understand_by_module.md**: Added Block Diagram, Fetch→Fetch→Execute, ISA Table (18 instr), Clock-by-Clock Walkthrough, State Diagram, Two's Complement example, Registers in RAM, PG vs DP table, Memory Map with I/O, Chapter Book roadmap
- **07_risk_analysis.md**: Added Known Limitations (L1: $60 PG+DP conflict, L2: IRQ_FF sticky, L3: Hidden free instructions)
- **08_design_signoff.md**: Added Status Levels table (FROZEN/VERIFIED/PENDING), Remaining Proof checklist, IRQ v1.0 polling corrected
- **09_task_test_plan.md**: Verified consistent (no changes needed)

### Simulation
- **wiring.py**: Fixed missing U31 /RST connections (pin 1, pin 13) — IE and IRQ_FF now properly reset
- **sim_lab/lab14_irq_bus.py**: Labeled as v1.1 behavior (matching Verilog model)
- All sims pass: chip_sim ✅, verify_wiring ✅, soft_debug ✅, gate_sim ✅

### Hardware Labs (14 labs synced with debug plan)
- lab01: Added bypass cap warning, clock integrity, rail continuity, rising edge diagram, reset LED, troubleshooting
- lab02: Added state machine diagram, Q3-Q7 debug header, recovery wording fix, milestone summary
- lab04: Fixed 74HC157 description (Quad 2-to-1), Challenge A ADDR_MODE clarification
- lab05: Fixed ROM test data ($11→$30/$42), added Bus Ownership diagram, Hi-Z explanation, clock note
- lab06: Added Bus Ownership Verification table, Bus Float Test
- lab08: Fixed "AC=$00 (reset)" → "AC=unknown"
- lab09: Added async preset toggle test
- lab10: Added PC_LOAD Priority Test
- lab11: Added Long Jump Test ($FFFF, $AA55)
- lab12: Added ROM/RAM Boundary Test, Memory Contention Test
- lab14: Fixed IRQ from v1.1 auto-jump to v1.0 polling, added sticky latch test

### Status
- RV8-GR v1.0: **Architecture Complete, Implementation Validation Pending**
- All 9 documentation files frozen and internally consistent
- Ready for physical breadboard build

## 2026-06-14 — v3.6: Programmer Bus-Based Redesign

### Architecture Change
- **Bus-based**: Programmer connects via RV8-Bus (40-pin), not direct to ROM
- **No /CE /OE**: ROM chip-select handled by A15=0 on CPU board
- **/RD added**: GPIO 17 drives bus pin 28 (ROM /OE) for reads
- **Two scenarios**: A=bare ROM, B=full CPU board (hold /RST to free bus)

### Pin Mapping (final)
```
Data D[0:7]:  GPIO [13, 12, 14, 27, 26, 25, 33, 32] → Bus pin 17-24
SR_DATA:      GPIO 23 → 595 SER
SR_CLK:       GPIO 18 → 595 SRCLK
SR_LATCH:     GPIO 19 → 595 RCLK
/RST:         GPIO 4  → Bus pin 26
/WR:          GPIO 16 → Bus pin 27
/RD:          GPIO 17 → Bus pin 28 (output in PROG, input in RUN)
/SLOT1:       GPIO 34 ← Bus pin 30 (input, RUN mode)
/RD sense:    GPIO 35 ← Bus pin 28 (input, RUN mode)
/WR sense:    GPIO 36 ← Bus pin 27 (input, RUN mode)
MODE:         GPIO 39 ← Switch (LOW=PROG, HIGH=RUN)
```

### Firmware Protocol (final)
- `?` → `Connected\n` (new: connection check)
- `F` + len(2B) → `K\n` (ACK), receive data, → `D\n` (done)
- `V` → 32KB raw bytes (drives /RD for each read)
- `R` → pulse /RST, → `K\n`

### Python Tools
- rv8flash.py: fixed double-send bug, added boot delay, port+baud display
- rv8term.py: rewritten (follows rv8flash patterns), added `-c` check
- Both show `Port: /dev/ttyUSB0 @ 115200 baud` + `Programmer: Connected`

### Files Changed
- firmware/firmware.ino (rewritten, 276 lines)
- schematic.md (rewritten for bus-based design)
- README.md (scenarios, bus overview, updated pinout)
- tools/rv8flash.py, rv8term.py, rv8ram-boot.py (pin updates)
- All 4 requirement .md files updated

## 2026-06-14 — v3.5: Programmer Schematic Update

### Hardware Change
- **New schematic**: TXS0108E ×2 + 74HC595 ×2 (daisy-chain)
- **Board**: ESP32-WROOM-32 (verified against pinout image)
- **Address**: Full 15-bit via shift register (no direct ADDR_PINS)
- **Control**: /CE, /OE, /WE via TXS0108E #1

### Pin Mapping (all files synced)
```
Data D[0:7]:  GPIO [13, 12, 14, 27, 26, 25, 33, 32]
SR_DATA:      GPIO 23
SR_CLK:       GPIO 18
SR_LATCH:     GPIO 19
/CE:          GPIO 4
/OE:          GPIO 16
/WE:          GPIO 17
```

### Files Updated
- schematic.md (replaced with Thai pin-by-pin guide + code)
- rv8_programmer.ino, rv8flash.py, rv8ram-boot.py, rv8term.py
- All 3 requirement docs
- rv8_programmer-requirement.md

## 2026-06-09 — v3.4: Gate-Level Simulator + Build Plan

### Gate-Level Simulator (Task 6 Complete)
- **chip_sim.py**: Full CPU simulation through all 35 chips
- **sim_lab/**: 10 step-by-step labs (module-by-module testing)
- **chips/__init__.py**: 35 chip objects with pin layout + behavior
- **wiring.py**: 247 pin connections matching 03_wiring_guide.md
- **Timing analysis**: max safe clock 9.7 MHz, 97ns margin @ 5 MHz
- All 3 .bin programs pass through gate-level sim

### Build Plan
- Complete BOM with sources (LCSC/AliExpress)
- 5-board breadboard layout plan
- Wire color convention
- Propagation delay analysis for all chip types

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
