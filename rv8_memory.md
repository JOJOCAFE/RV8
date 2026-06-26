# RV8 Project — Memory

**Last updated**: 2026-06-26

## Focus: RV8GR-V2 student build + RV8-R FullHW investigation

### Active folders:
- `RV8GR-V2/` — active CPU design (33 logic + ROM + RAM = 35 packages, student baseline contract, labs, Verilog benches, gate-level sim passing)
- `RV8GR-V1/` — previous RV8-GR reference snapshot
- `Programmer/` — ESP32 board (dual ZIF/RV8-Bus mode, firmware+tools verified, 36 current tests)
- `RV8/` — microcode variant (28 chips, Verilog 8/8, reference)
- `RV8R/` — FullHW RAM-register variant (49 logic + 4 ROM/RAM = 53 packages, full RV8-style TTL hardware path, RTL/KiCad/generator migration pending)
- `RV8G/` — full ISA no-microcode variant (38 chips, concept)

### Current version: v4.2

### What was done today (2026-06-26):
1. Added RV8GR-V2 student build guardrails:
   - Student Baseline Contract in README and build plan
   - clear reading order for students, teachers, debug, wiring, and KiCad work
   - temporary-wire removal checkpoints in the incremental build plan
   - probe-point map in the physical debug plan
   - future-only warnings for hardware IRQ vectoring and ROM banking
2. Cleaned RV8GR-V2 generated artifacts:
   - removed VCD/VVP traces, Python caches, and Zone.Identifier metadata
   - updated `.gitignore` for `*.pyc` and `*:Zone.Identifier*`
3. Verified RV8GR-V2:
   - assembler tests: 11 pass
   - Python chip sim: 8 CPU tests pass
   - wiring verifier: all wiring verified
   - RTL benches: full, IRQ, SETDP, tasks, assembler ROM, opcode sweep all pass
   - opcode sweep: 512 cases pass

4. Hardened Programmer/RV8GR-V2 integration:
   - confirmed dual ZIF-direct and RV8-Bus in-system programming paths
   - fixed RUN-mode bus release and terminal handshake boundary
   - added RV8GR-V2 `program/verify --base 0x0000` CLI aliases
   - regenerated Programmer KiCad PDF/SVG exports with KiCad 10.0.4
   - documented ROM `/WE -> /WR` final wiring and AT28C256 SDP limitation
5. Verified integration:
   - Programmer tests: 36 pass
   - RV8GR-V2 wiring verifier: all wiring verified
   - RV8GR-V2 assembler tests: 11 pass
6. Promoted RV8-R to FullHW:
   - old 19-chip reduced sketch is now legacy design history
   - FullHW target is 49 logic chips + 2 microcode ROM + 1 program ROM + 1 RAM = 53 packages
   - full-ISA hardware paths are real in docs for PC load/save, ALU logic, register addressing, fast page, stack, IRQ entry, and IRET
   - control is now 16-bit direct-control microcode with 15-bit address `{IRQ_ACTIVE,C,Z,step[3:0],opcode[7:0]}`
   - existing `RV8R/tools/microcode_gen.py` is legacy 14-bit prototype; FullHW generator, RTL, and KiCad proof are pending

### Key design facts:
#### RV8GR-V2 student baseline
- 33 logic chips + ROM + RAM = 35 packages
- 18 instructions, 3-cycle (T0/T1/T2), no microcode
- Clock: 1 MHz breadboard (official), 4 MHz PCB
- Horizontal control: opcode = control word directly
- IRQ is polling-only in V2; no hardware vector
- ISA frozen, design signed off, ready for physical build

#### RV8-R FullHW investigation
- 49 logic chips + 4 ROM/RAM packages = 53 total
- ROM-low boot: Program ROM `$0000-$7FFF`, RAM `$8000-$FFFF`
- registers live in high RAM at `$FFF8-$FFFF`
- fast page is `$FF00+imm8`, with `$FFF6-$FFFF` reserved for IRQ save slots and registers
- FullHW uses 2 microcode ROMs, 16-bit direct-control word, 15-bit microcode address
- `SRL` remains software macro; `LUI` is assembler pre-shift
- not ready for physical build until FullHW microcode generator, RTL/testbench, KiCad/ERC, and Programmer/RV8-Bus pin audit are done

### RV8-Bus pinout (40-pin):
```
pin 1-16: A[0:15], pin 17-24: D[0:7]
pin 25: CLK, pin 26: /RST, pin 27: /WR, pin 28: /RD
pin 29: /IRQ, pin 30: /SLOT1, pin 31: /SLOT2, pin 32: T2
pin 39: VCC, pin 40: GND
```

### Programmer board:
- ESP32-WROOM-32 + 2× TXS0108E + 2× 74HC595
- Dual mode, use exactly one at a time:
  - ZIF direct: insert bare AT28C256 in Programmer ZIF, disconnect RV8-Bus
  - RV8-Bus in-system: leave ZIF empty, connect Programmer to RV8GR-V2 bus, hold CPU reset during flash
- GPIO: 23(SR_DATA), 18(SR_CLK), 19(SR_LATCH), 4(/RST), 16(/WR), 17(/RD)
- Data: GPIO {13,12,14,27,26,25,33,32} = D[7:0]
- RUN mode releases `/WR` and `/RD`; `rv8term.py` terminal mode does not use the PROG-only `?` handshake
- `rv8flash.py` accepts both legacy flags and RV8GR-V2 aliases: `program FILE --base 0x0000`, `verify FILE --base 0x0000`
- AT28C256 caveat: current firmware performs normal byte write cycles; use SDP-disabled chips or add SDP unlock support before protected parts

### Next steps:
- Build RV8GR-V2 physically from `RV8GR-V2/doc/labs/README.md`
- Use `RV8GR-V2/doc/06_debug_plan.md` probe map during bring-up
- Create KiCad schematics from `RV8GR-V2/doc/10_kicad_modules.md` (6 sheets)
- Order parts for physical build
- RV8-R FullHW: write 15-bit direct-control microcode generator, migrate RTL/testbench, then convert `doc/02_wiring_guide.md` into KiCad sheets
