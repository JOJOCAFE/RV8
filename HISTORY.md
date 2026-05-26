# RV8 Project — Development History

## Day 1-5 (2026-05-10 to 2026-05-14)
- Original designs explored and archived
- Programmer board complete

## Day 6 (2026-05-15)
- RV8 redesigned (RISC-V, microcode, 27 chips)
- RV8-G and RV8-GR concepts

## Day 7 (2026-05-16-17) — Final Architecture + Implementation

### Designs verified (all traced):
- RV8: 27 chips, microcode, Verilog 8/8 pass
- RV8-R: 18 chips, microcode, RAM registers, traced
- RV8-G: 28 chips, no microcode, full ISA, traced
- RV8-GR: 21 chips, no microcode, reduced ISA, **Verilog 11/11 + assembler + assembly test pass**

### RV8-GR fully implemented:
- Verilog model (11/11 unit tests pass)
- Assembler (rv8gr_asm.py, working)
- Assembly integration test (full pipeline: asm→bin→CPU→pass)
- VCD waveform support (gtkwave)
- Full doc set (design, ISA, trace, wiring, modules, bank switch)

### Bank switch design:
- Run code from RAM via XOR on A15 (fetch path only)
- Registers ($0000-$0007) always safe (data path unchanged)
- Decision: bank switch lives on TRAINER BOARD (not CPU board)
- CPU board stays pure at 21 chips

### Key lessons:
1. Every trace finds 1-2 more chips than claimed
2. Full ISA always costs ~27 chips regardless of approach
3. RAM registers save ~10 chips (proven)
4. "No microcode" doesn't save chips for full ISA (saves for reduced)
5. Bank switch belongs on expansion board, not CPU

---

## Key Milestones

| Date | Milestone |
|------|-----------|
| 2026-05-10 | Project started |
| 2026-05-14 | Programmer board complete |
| 2026-05-15 | RV8 microcode working (8/8) |
| 2026-05-16 | All 4 variants traced and verified |
| 2026-05-17 | **RV8-GR: full toolchain (Verilog + assembler + test) ready for build** |

## Day 8 (2026-05-27) — RV8-GR Complete Redesign + Assembler

### Assembler (rv8gr_asm.py):
- Labels, forward/backward references
- hi()/lo() address functions
- .ORG directive
- HLT, JMP, CALL macros
- MV auto-detect (a0,rs vs rd,a0)
- Output: .bin (32KB ROM image) or hex listing
- Full pipeline: .asm → assembler → .bin → Verilog sim → PASS

### Test ROM (testrom.bin):
- 10 test groups covering all 15 instructions
- Cross-page jump ($8000→$9000→$8070)
- Software subroutine call/return
- 187 cycles, ALL PASS
- Ready to flash to real hardware

### Architecture redesign (same session):
- No XOR chips for ALU (SUB/XOR broken)
- Bus conflict when SOURCE_TYPE=1 (IRL + RAM both drive IBUS)
- Only 256-byte jump range (no page register)
- ROM/RAM not in shared 64K space (operation-based chip select)

### Solution: Full redesign from scratch
- 29 logic chips (was 21)
- Full 64K address space: ROM $8000-$FFFF, RAM $0000-$7FFF
- A15-based chip select (ROM /CE = NOT(A15), RAM /CE = A15)
- 16-bit address mux (4× 74HC157 for A0-A15)
- Page Register (74HC574) for 16-bit jump
- XOR B-input mux (2× 74HC157) for SUB inversion + XOR instruction
- AC input mux (2× 74HC157) selects adder vs XOR output
- Ring counter (74HC164) for T0/T1/T2
- U7 DIR gated with T2+STORE (prevents bus conflict)
- U7 /OE = NOT(/IRL_OE) (prevents IBUS conflict)
- Can execute code from RAM (PC < $8000)
- Expandable: ROM bank (A16), RAM pages (A8-A14) via bus

### ISA changes
- XORI=$70, XOR=$78 (was $50/$58 — needed MUX_SEL=1 for data path)
- Added SETPG $20, SETPG_R $28
- Removed hardware JAL (software subroutine only)
- 15 instructions total

### Verification
- New Verilog model: rv8gr_cpu.v (behavioral)
- New testbench: tb_rv8gr_full.v (all ISA + 64K jump + subroutine)
- ALL TESTS PASSED (127 cycles)

### Documentation (all rewritten)
- Construct.md: pin-by-pin, bus-centric (source of truth)
- 00_design.md, 01_isa_reference.md, 02_instruction_trace.md
- 03_wiring_guide.md, 04_understand_by_module.md (Thai)
- 05_bank_switch.md (expansion via bus)
