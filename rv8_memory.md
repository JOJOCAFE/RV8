# RV8 Project — Memory

**Last updated**: 2026-06-21

## Focus: RV8-GR (21 chips) + Programmer board

### Active folders:
- `RV8GR/` — CPU design (21 chips, no microcode, Verilog 11/11, assembler working)
- `Programmer/` — ESP32 board (KiCad done, firmware+tools verified, ZIF+Bus dual-mode)
- `RV8/` — microcode variant (27 chips, Verilog 8/8, reference)
- `RV8R/` — RAM register variant (18 chips, traced)
- `RV8G/` — full ISA no-microcode variant (28 chips, traced)

### RV8-Bus pinout (standard for all):
```
pin 25: CLK, pin 26: /RST, pin 27: /WR, pin 28: /RD
pin 29: /IRQ, pin 30: /SLOT1
```

### Programmer board:
- ESP32 + 2× TXS0108E + 2× 74HC595
- Dual mode: ZIF socket (direct ROM) or RV8-Bus (in-system)
- GPIO: 23(SR_DATA), 18(SR_CLK), 19(SR_LATCH), 4(/RST), 16(/WR), 17(/RD)
- Data: GPIO {13,12,14,27,26,25,33,32} = D[7:0]
- KiCad schematic verified, firmware+tools match

### Key design decisions:
- Bank switch (run from RAM) lives on Trainer board, not CPU board
- CPU board stays pure at 21 chips
- Registers in RAM $0000-$0007
- 3-cycle execution, ~3.3 MIPS @ 10 MHz
