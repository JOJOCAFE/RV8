# RV8 Project — Memory

**Last updated**: 2026-06-21

## Focus: RV8-GR (33 chips) — preparing for physical breadboard build

### Active folders:
- `RV8GR/` — CPU design (33 logic + ROM + RAM = 35 packages, Verilog 5/5, gate-level sim passing)
- `Programmer/` — ESP32 board (bus-based, firmware+tools verified, 46 tests)
- `RV8/` — microcode variant (28 chips, Verilog 8/8, reference)
- `RV8R/` — RAM register variant (19 chips, next project)
- `RV8G/` — full ISA no-microcode variant (38 chips, concept)

### Current version: v3.9

### What was done today (2026-06-21):
1. Created `RV8GR/doc/10_kicad_modules.md` — splits 35-chip design into 6 KiCad hierarchical sheets:
   - CLK_RST (U8), PC (U1-U4), ADDR_MEM (U15/U16/U29/U30+ROM+RAM), IR_BUF (U5-U7,U14), ALU_AC (U9-U13,U17-U22), CTRL (U23-U28,U31-U33)
2. Verified alignment with debug plan (14 steps), hardware labs (14 labs), and wiring guide
3. Fixed typo in `06_debug_plan.md`: U33 pin 2 source was `U5-16` (SRC) → corrected to `U5-13` (XOR_MODE)
4. Updated README, CHANGELOG, HISTORY — pushed as v3.9

### Key design facts:
- 33 logic chips + ROM + RAM = 35 packages
- 18 instructions, 3-cycle (T0/T1/T2), no microcode
- Clock: 1 MHz breadboard (official), 4 MHz PCB
- Horizontal control: opcode = control word directly
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
- Create KiCad schematics from 10_kicad_modules.md (6 sheets)
- Hardware Labs 04-14 (continue from lab03)
- Order parts for physical build
- RV8-R architecture design (when ready)
