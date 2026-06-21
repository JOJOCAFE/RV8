# Programmer Board — ESP32-WROOM-32

**One board, two modes**: program ROM via RV8-Bus (in-system) OR via ZIF socket (standalone).

---

## Overview

```
                                           ┌─────────────────────┐
                                      ┌──→ │ RV8-Bus (40-pin)    │ → CPU Board
                                      │    └─────────────────────┘
PC ←USB→ [ESP32] ←→ [TXS ×2] ←→ [595 ×2]┤
                                      │    ┌─────────────────────┐
                                      └──→ │ AT28C256 (ZIF 28)   │ → ถอดไปเสียบบอร์ด
                                           └─────────────────────┘

Use ONE at a time: Bus cable OR ROM in ZIF (never both!)
```

---

## Two Modes

### Mode A: ZIF Direct (program bare ROM chip)

1. ❌ Disconnect Bus cable
2. Insert ROM into ZIF socket → lock
3. `python3 tools/rv8flash.py -w program.bin`
4. `python3 tools/rv8flash.py -v program.bin`
5. Remove ROM → plug into CPU board

### Mode B: RV8-Bus (program in-system)

1. ❌ ZIF empty (no ROM inserted)
2. Connect Bus cable to CPU board
3. Switch → PROG: `python3 tools/rv8flash.py -w program.bin`
4. Switch → RUN: `python3 tools/rv8term.py` (terminal)

---

## Hardware

| Part | Qty | Function |
|------|:---:|----------|
| ESP32-WROOM-32 | 1 | Controller (USB-serial, GPIO) |
| TXS0108E module | 2 | Level shift 3.3V ↔ 5V |
| 74HC595 | 2 | Shift register → address A[14:0] |
| ZIF socket 28-pin | 1 | Insert/remove ROM |
| 40-pin IDC header | 1 | RV8-Bus connector |
| SPDT switch | 1 | PROG/RUN mode |
| 10K resistors | 3 | Pull-ups (/CE, /OE, TXS OE) |
| 100nF caps | 7 | Bypass |

---

## Bus Pinout (matches RV8GR)

```
pin 1-16:  A[0:15]
pin 17-24: D[0:7]
pin 25:    CLK
pin 26:    /RST
pin 27:    /WR
pin 28:    /RD
pin 29:    /IRQ
pin 30:    /SLOT1
pin 39:    VCC
pin 40:    GND
```

---

## Files

```
Programmer/
├── KICAD/              ← KiCad project (schematic + PCB)
├── RV8Programmer.pdf   ← schematic PDF export
├── RV8Programmer.svg   ← schematic SVG export
├── schematic.md        ← pin-level wiring (Thai, matches KiCad)
├── firmware/
│   ├── firmware.ino    ← ESP32 Arduino firmware
│   └── bootloader.asm  ← ROM bootloader (for RAM-boot mode)
└── tools/
    ├── rv8flash.py     ← flash/verify ROM
    ├── rv8term.py      ← UART terminal (RUN mode)
    └── rv8ram-boot.py  ← upload to RAM via bootloader
```

---

## Software Commands

```bash
# Flash ROM
python3 tools/rv8flash.py -w program.bin

# Verify ROM
python3 tools/rv8flash.py -v program.bin

# Terminal (RUN mode)
python3 tools/rv8term.py

# Upload to RAM (requires bootloader in ROM)
python3 tools/rv8ram-boot.py program.bin
```

---

## Safety

| ⚠️ Never connect BOTH Bus cable AND ROM in ZIF at the same time! |
|:---:|
| Data bus fight → chip damage |

---

## Status

- ✅ KiCad schematic (verified, GPIO 16↔17 swap applied)
- ✅ Firmware (matches schematic pin assignments)
- ✅ Tools (protocol matches firmware)
- ✅ Schematic doc (Thai, Bus + ZIF, matches KiCad)
- ⬜ Physical build
- ⬜ PCB fabrication
