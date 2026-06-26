# RV8 Project — Memory

**Last updated**: 2026-06-26

## Focus: RV8GR-V2 (33 chips) — student-friendly physical breadboard build

### Active folders:
- `RV8GR-V2/` — active CPU design (33 logic + ROM + RAM = 35 packages, student baseline contract, labs, Verilog benches, gate-level sim passing)
- `RV8GR-V1/` — previous RV8-GR reference snapshot
- `Programmer/` — ESP32 board (bus-based, firmware+tools verified, 46 tests)
- `RV8/` — microcode variant (28 chips, Verilog 8/8, reference)
- `RV8R/` — RAM register variant (19 chips, next project)
- `RV8G/` — full ISA no-microcode variant (38 chips, concept)

### Current version: v4.0

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

### Key design facts:
- 33 logic chips + ROM + RAM = 35 packages
- 18 instructions, 3-cycle (T0/T1/T2), no microcode
- Clock: 1 MHz breadboard (official), 4 MHz PCB
- Horizontal control: opcode = control word directly
- IRQ is polling-only in V2; no hardware vector
- ISA frozen, design signed off, ready for physical build

### RV8-Bus pinout (40-pin):
```
pin 1-16: A[0:15], pin 17-24: D[0:7]
pin 25: CLK, pin 26: /RST, pin 27: /WR, pin 28: /RD
pin 29: /IRQ, pin 30: /SLOT1, pin 31: /SLOT2, pin 32: T2
pin 39: VCC, pin 40: GND
```

### Programmer board:
- ESP32-WROOM-32 + 2× TXS0108E + 2× 74HC595
- Connects via RV8-Bus (40-pin), holds /RST during flash
- GPIO: 23(SR_DATA), 18(SR_CLK), 19(SR_LATCH), 4(/RST), 16(/WR), 17(/RD)
- Data: GPIO {13,12,14,27,26,25,33,32} = D[7:0]

### Next steps:
- Build RV8GR-V2 physically from `RV8GR-V2/doc/labs/README.md`
- Use `RV8GR-V2/doc/06_debug_plan.md` probe map during bring-up
- Create KiCad schematics from `RV8GR-V2/doc/10_kicad_modules.md` (6 sheets)
- Order parts for physical build
- RV8-R architecture design (when ready)
