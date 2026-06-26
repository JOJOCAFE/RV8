# RV8 Project — Development History

## 2026-06-26 — v4.2: RV8-R FullHW Real Hardware Path

- Reframed RV8-R as **FullHW**, a larger but real full-ISA TTL hardware path instead of the old 19-chip reduced concept
- Updated package target to **49 logic chips + 4 memory/ROM packages = 53 total**
- Defined real hardware paths for PC load/save, ALU logic operations, high-RAM register addressing, fast-page RAM, stack, `JAL/JALR`, IRQ entry, and `IRET`
- Changed RV8-R control model to **16-bit direct-control microcode** with a **15-bit microcode address**: `{IRQ_ACTIVE, C, Z, step[3:0], opcode[7:0]}`
- Marked the old 19-chip instruction trace as legacy design history
- Marked the existing Python microcode generator as a legacy 14-bit prototype; FullHW needs a new generator, RTL migration, and KiCad/ERC proof
- Updated the top-level README so RV8GR-V2 remains the physical student baseline and RV8-R FullHW becomes the full RV8-style TTL investigation path

## 2026-06-26 — v4.1: Programmer Dual-Mode RV8GR-V2 Compatibility

- Rechecked `Programmer/` against the current `RV8GR-V2` RV8-Bus pinout and ROM wiring contract
- Confirmed the board supports two mutually exclusive programming paths: ZIF direct ROM programming, or in-system RV8-Bus programming with the ZIF empty
- Fixed RUN-mode bus release in firmware: `/WR` and `/RD` are both released when switching to RUN, then reclaimed in PROG
- Fixed `rv8term.py` so normal RUN terminal mode no longer requires the PROG-only `? -> Connected` handshake; `-c` remains the explicit PROG-mode health check
- Added RV8GR-V2-compatible `rv8flash.py program FILE --base 0x0000` and `verify FILE --base 0x0000` aliases; nonzero base is rejected explicitly
- Documented the AT28C256 software data protection boundary: current firmware performs normal byte write cycles, so use SDP-disabled ROM chips or add an unlock sequence before protected parts
- Updated RV8GR-V2 docs and labs so Programmer command examples use the actual `Programmer/tools/rv8flash.py` path and final ROM `/WE -> RV8-Bus /WR` wiring is clear
- Regenerated `Programmer/KICAD/RV8Programmer.pdf` and SVG exports with KiCad 10.0.4
- Verification passed: Programmer Python tests (36), RV8GR-V2 wiring verifier, and RV8GR-V2 assembler tests

## 2026-06-26 — v4.0: RV8GR-V2 Student Build Guardrails

- Made `RV8GR-V2/` the active 33-chip student baseline in the top-level project docs
- Added Student Baseline Contract: 33 logic chips + ROM + RAM, no microcode, no hardware IRQ vector, fixed T0/T1/T2 execution, one active IBUS/DBUS driver
- Added recommended reading order: labs for students, build plan for teachers, debug plan for probing, wiring guide as source of truth, KiCad module split for schematic work
- Added temporary-wire removal checkpoints to the incremental build plan to prevent test jumpers from becoming hidden wiring bugs
- Added probe-point map to the physical debug plan for clock/reset, buses, enables, PC, PG, DP, AC, Z, and IRQ latch signals
- Marked ROM banking and hardware IRQ vectoring as future-only, not part of the V2 baseline
- Cleaned generated VCD/VVP traces, Python caches, and Zone.Identifier metadata from RV8GR-V2
- Verification passed: assembler tests, Python chip sim, wiring verifier, all RTL benches, and 512-case opcode sweep

## 2026-06-21 — v3.9: KiCad Module Definitions

- Created doc/10_kicad_modules.md: 6 hierarchical sheets for KiCad (CLK_RST, PC, ADDR_MEM, IR_BUF, ALU_AC, CTRL)
- Each module has sheet ports, pin-level wiring, placement notes
- Aligned with 06_debug_plan.md (14 steps) and hardware labs
- Cross-verified against 02_wiring_guide.md — all connections match

## 2026-06-19 — v3.8: Opcode Sweep, Page-Safe Assembler, Agent Skills

- Added exhaustive opcode sweep testbench (256 opcodes × Z=0/1 = 512 cases)
- Assembler upgraded: cross-page validation, overlap detection, duplicate labels, memh format
- Created debug-mantra skill (4-step hardware debugging discipline, adapted from 9arm-skills)
- Created scrutinize skill (outsider design review, adapted from 9arm-skills)
- Evaluated RV8GR-Codex (40-chip AI redesign): timing concerns real but irrelevant at 1 MHz, extracted useful bits, rejected the redesign
- Documented future upgrades (doc/11_future_upgrades.md): clock qualification, hardware DI, I/O decode for v2.0
- Clock targets: 1 MHz breadboard (808ns margin), 4 MHz PCB (88ns margin), no hardware changes
- Evaluated 7 external GitHub repos for applicable content (only 9arm-skills was useful)
- Status: 5 testbenches passing, assembler hardened, ready for physical build

## 2026-06-16 — v3.7: Documentation Freeze & Consistency Pass

- All 9 RV8-GR docs reviewed, corrected, and frozen (design_isa, wiring_guide, instruction_trace, bank_switch, understand_by_module, debug_plan, risk_analysis, design_signoff, task_test_plan)
- Added: Architectural Invariants, Hardware Freeze Policy, Instruction Trace Contract (13-field format), Golden Trace, Reset Contract, Forbidden Bus States, Illegal Opcode Behavior table
- Fixed: IRQ_FF clear mechanism consistent across all docs (v1.0 = /RST only)
- Fixed: Package count normalized (v1.0=35, v1.1=37)
- Fixed: Memory map consistent (ROM $0000-$7FFF, RAM $8000-$FFFF) everywhere
- Fixed: wiring.py missing U31 /RST connections
- Enhanced: debug_plan with 15+ new tests (bus ownership, walking-1, RAM march, burn-in, clock sweep)
- Enhanced: understand_by_module with block diagram, ISA table, clock-by-clock walkthrough
- Enhanced: 14 hardware labs synced with debug_plan
- Status: Architecture frozen, ready for physical build

## 2026-06-14 — v3.6: Programmer Bus-Based Redesign

- Programmer connects via RV8-Bus (40-pin) instead of direct ROM
- Firmware rewritten: removed /CE /OE, now drives /RST + /WR + /RD on bus
- Added `?` command for connection check (rv8flash + rv8term use it)
- Added 2s boot delay + buffer drain (ESP32 resets on serial open)
- Two usage scenarios documented: bare ROM (A) and full CPU board (B)
- rv8term.py rewritten following rv8flash.py patterns (check before connect)
- Added `-c` option to rv8term.py
- Port + baud displayed on connect (`Port: /dev/ttyUSB0 @ 115200 baud`)
- Fixed cmd_flash double-send bug in rv8flash.py
- All docs updated: schematic, README, requirements (6 .md files)
- Firmware compiled and flashed to ESP32 via arduino-cli
- 31 tests passing (16 flash + 15 term)

## 2026-06-14 — v3.5: Programmer Schematic Update

- Replaced schematic with new design (TXS0108E + 74HC595 ×2)
- Board renamed to ESP32-WROOM-32 (pin-verified)
- All software pin mappings updated and verified consistent
- RV8-R design plan created (18 chips, RISC-V, microcode)
- RV8F concept saved (38 chips, fast SRAM microcode)

## 2026-06-09 — v3.4: Gate-Level Simulator + Build Plan

- Gate-level chip simulator: 35 chips, 14 types, 141 test vectors
- 10 sim labs (ring counter → full execute LI $42)
- 3 .bin programs verified through gate-level sim
- Propagation delay model (70ns ROM/RAM, max 9.7 MHz)
- Complete BOM (order-ready) + 5-board breadboard layout
- Wiring verified: 23 critical connections checked against 03_wiring_guide

## 2026-06-09 — v3.3: SETDP + Full 64KB Data Access

- Added SETDP instruction ($40) — Data Page Register (U32 74HC574)
- Added U33 (74HC21) for SETDP decode — pin-level finalized
- Full 64KB data access: DP=$00-$7F → RAM, DP=$80-$FF → ROM read
- 32 logic chips, 18 instructions, 34 packages total
- IRQ save-PC documented (software approach for v1.0)
- SETDP test: 5KB RAM write/read + ROM read (160 cycles, all pass)
- All docs updated and verified consistent

## 2026-06-09 — v3.2: RV8-GR Design Sign-off

- Complete design review and risk analysis (10 hazards)
- SRC+STR hardware guard applied (spare gate, 0 chips added)
- RV8-Bus v2 defined (40-pin: A16+D8+CLK+/WR+/RD+/IRQ+/SLOT)
- Documentation rewrite: merged and compacted all docs
- Created debug plan (14 steps for physical build)
- Discovered free NOT instruction ($B0/$B8)
- Design signed off for physical build

## 2026-06-08 — v3.1: Programmer Tools

- Created rv8flash.py (540 lines, 16 tests) — Flash ROM via ESP32
- Created rv8ram-boot.py (430 lines, 15 tests) — Upload to RAM via bootloader
- Created rv8term.py (289 lines, 15 tests) — Terminal bridge PC↔CPU
- Created test suites: 46 tests total, all passing
- Created requirement documents for all tools
- Updated README.md and schematic.md with software documentation

## 2026-05-10 to 2026-05-14 — Project Start
- Original designs explored and archived
- Programmer board complete (ESP32 + TXB0108)

## 2026-05-15 — RV8 Family Architecture
- RV8: 27 chips, microcode, Verilog 8/8 pass
- RV8-R: 18 chips concept
- RV8-G: 28 chips concept
- RV8-GR: 21 chips concept

## 2026-05-16 to 2026-05-17 — RV8-GR Initial Design (v1.0)
- 21 logic chips, ROM at $8000, 256-byte jump range
- All 4 variants traced and verified
- Verilog 11/11 unit tests pass
- Assembler (rv8gr_asm.py)
- Assembly integration test passes
- Full doc set complete

## 2026-05-27 — RV8-GR v2.0 Complete Redesign + RV8-G Construct

### RV8-GR Complete (v2.0)
- Architecture: 29 logic chips, full 64K, A15 chip select
- Execute from RAM (PC < $8000)
- 16-bit jump via Page Register
- ISA: 15 instructions (XORI=$70, XOR=$78, SETPG=$20, SETPG_R=$28)
- Verilog: ALL TESTS PASSED (127 cycles)
- Assembler: rv8gr_asm.py — labels, macros, .bin output
- Test ROM: testrom.bin — 10 test groups, 187 cycles
- Docs: Construct (pin-level), ISA, traces, wiring, modules, bank switch

### RV8-G Construct
- 38 logic chips, full 35-instruction ISA, no microcode
- 4-cycle execution with B-register
- Full ALU: ADD/SUB/AND/OR/XOR/SLL/SRL/SLT
- Branches: BEQ/BNE/BLT/BGE rs1,rs2
- JAL/JALR, PUSH/POP
- Construct.md written

## 2026-06-06 — RV8-GR v3.0: IRQ + Python Simulation + Codeberg

### IRQ Support
- Added EI ($08) and DI ($48) instructions
- IRQ latch (74HC74 U31-B) for edge detection
- IE flag (74HC74 U31-A) for enable/disable
- Fixed vector $FF00, auto-save PC to RAM[$0E:$0F]
- No nesting (IE cleared on entry)
- 30 logic chips total (+1 from v2.0)
- 17 instructions total (+2 from v2.0)
- tb_rv8gr_irq.v — 6 tests: EI/DI, IRQ fire, PC save, defer past jumps

### Python Gate-Level Simulation
- sim/gate_sim.py — simplified chip models
- Ring counter, registers, ALU components
- Trace timing: T0→T1→T2
- Educational tool for understanding CPU behavior

### Test Infrastructure
- tb_rv8gr_tasks.v — milestone tests (1-9)
- tools/test_rv8gr_asm.py — assembler unit tests
- doc/task_test_plan.md — test milestones

### Repository
- Moved from GitHub to Codeberg
- https://codeberg.org/JOJOCAFE/RV8

## Key Milestones

| Date | Milestone |
|------|-----------|
| 2026-05-10 | Project started |
| 2026-05-14 | Programmer board complete |
| 2026-05-16 | All 4 variants traced and verified |
| 2026-05-17 | RV8-GR v1.0: toolchain ready |
| 2026-05-27 | RV8-GR v2.0: complete redesign, full 64K |
| 2026-06-06 | RV8-GR v3.0: IRQ + sim + Codeberg |

## Lessons Learned

1. Every trace finds 1-2 more chips than initially claimed
2. Full ISA always costs ~27-30 chips regardless of approach
3. RAM registers save ~10 chips (proven)
4. "No microcode" doesn't save chips for full ISA
5. Bank switch belongs on expansion board, not CPU
