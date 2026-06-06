# RV8-GR — Bank Switch (Memory Expansion via Bus)

**CPU board: 30 chips, unchanged. Expansion plugs into address bus.**

---

## Current Memory Map (no expansion)

    $0000-$7FFF  RAM 62256 (32KB), /CE = A15
    $8000-$FFFF  ROM SST39SF010A (32KB visible), /CE = /A15

    Data access during T2: address = $00xx (A8-A15 muxed to GND)
    → only 256 bytes of RAM accessible for data ($0000-$00FF)

---

## ROM Expansion (32KB → 128KB)

SST39SF010A has 17 address lines (A0-A16 = 128KB).
CPU uses A0-A14 (32KB). A15 is used for /CE. A16 is NC.

**Expansion board** (1 chip: 74HC574 latch):

    CPU writes bank number to RAM[$FF] → expansion board latches D0 → ROM A16

    ROM A16 = 0: lower 32KB of flash (bank 0)
    ROM A16 = 1: upper 32KB of flash (bank 1)

Software:
```
LI $01          ; select bank 1
MV $FF, a0      ; write to $00FF → expansion latch captures D0
; now ROM $8000-$FFFF shows upper 32KB of 128KB flash
```

Hardware on expansion board:
```
Address decode: A0-A7 = $FF AND ADDR_MODE=1 AND /AC_BUF=0 → latch CLK
74HC574 pin11(CLK) ← decode output
74HC574 pin2(D1) ← D0 (DBUS)
74HC574 pin19(Q1) → ROM A16
```

---

## RAM Expansion (256B data → 32KB data)

During T2 data access, A8-A14 = GND (from U29-U30 B-inputs).
Replace GND with a latch to select RAM pages.

**Expansion board** (1 chip: 74HC574 latch):

    CPU writes page number to RAM[$FE] → expansion board latches D[6:0] → RAM A8-A14

    Page 0: RAM $0000-$00FF (registers + stack)
    Page 1: RAM $0100-$01FF
    ...
    Page 127: RAM $7F00-$7FFF

Software:
```
LI $05          ; select page 5
MV $FE, a0      ; write to $00FE → expansion latch captures D[6:0]
; now data access reads/writes RAM page 5 ($0500-$05FF)
```

Hardware on expansion board:
```
Address decode: A0-A7 = $FE AND ADDR_MODE=1 AND /AC_BUF=0 → latch CLK
74HC574 pin11(CLK) ← decode output
74HC574 pin2-8(D1-D7) ← D0-D6 (DBUS)
74HC574 pin19-13(Q1-Q7) → override U29/U30 B-inputs (cut GND, insert latch)
```

**Note**: Changing page loses access to registers ($00-$07) unless page 0 is active.
Convention: always return to page 0 before accessing registers.

---

## Safe Register Scheme (optional)

Split RAM address space so registers are always accessible:

    $00-$07: always page 0 (registers) — hardwire A8-A14=0 for these addresses
    $08-$FF: banked (page selectable)

Requires 1 extra gate on expansion board:
```
If A0-A7 < $08: force A8-A14 = 0 (bypass page latch)
If A0-A7 >= $08: use page latch for A8-A14
```

---

## Execute from RAM

PC in $0000-$7FFF fetches from RAM (A15=0 → RAM /CE=0).
No expansion needed — works with base CPU board.

To load and run a program from RAM:
```
; In ROM ($8000+): loader copies program to RAM
LI $42          ; example: write instruction bytes to RAM
MV $00, a0      ; RAM[$0000] = $42 (first byte of program)
...
; Jump to RAM:
SETPG $00       ; page = $00
J $00           ; PC = $0000 → fetches from RAM
```

---

## Summary

| Expansion | Chips on expansion board | Result |
|-----------|:------------------------:|--------|
| ROM bank (A16) | 1× 74HC574 + decode | 128KB ROM (2 × 32KB) |
| RAM pages (A8-A14) | 1× 74HC574 + decode | 32KB data (128 × 256B) |
| Execute from RAM | 0 (built-in) | PC < $8000 → RAM |

**CPU board stays at 30 chips. All expansion on the bus.**
