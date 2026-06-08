# RV8-GR — Bank Switch & Memory Expansion (Stable)

**CPU stays 30 chips. All expansion on the bus via 74HC574 latches.**

---

## Base Memory Map

```
$0000-$7FFF  RAM 32KB (/CE = A15)
$8000-$FEFF  ROM 32KB (/CE = /A15)
$FF00-$FF0F  I/O Slot 1 (/SLOT1 on RV8-Bus)
$FF10-$FF1F  I/O Slot 2 (/SLOT2 on RV8-Bus)
Data access: $00xx (A8-A15 = GND during T2)
```

---

## ROM Bank (32KB → 128KB)

Extra chip: 1× 74HC574 on expansion board.

```
ROM A16 ← latch Q0 (selects bank 0 or 1)
Latch CLK ← address decode ($FF + STORE)
Latch D0 ← DBUS D0
```

**Software:**
```asm
LI $01          ; bank 1
SB $FF          ; latch captures D0 → ROM A16=1
```

---

## RAM Pages (256B → 32KB data)

Extra chip: 1× 74HC574 on expansion board.

Replace U29/U30 B-inputs (GND) with latch outputs for A8-A14.

```
Latch Q[6:0] → A8-A14 (override GND on U29/U30 B-inputs)
Latch CLK ← address decode ($FE + STORE)
Latch D[6:0] ← DBUS D[6:0]
```

**Software:**
```asm
LI $05          ; page 5
SB $FE          ; latch captures → data at $0500-$05FF
```

Note: Page 0 = registers ($00-$07). Return to page 0 before register access.

---

## Execute from RAM (Built-in)

No expansion needed. PC < $8000 → fetches from RAM.

```asm
; Load program to RAM, then:
SETPG $00
J $00           ; PC=$0000, fetches from RAM
```

---

## Summary

| Feature | Extra Chips | Result |
|---------|:-----------:|--------|
| ROM bank | 1× 74HC574 | 128KB (2 banks) |
| RAM pages | 1× 74HC574 | 32KB data (128 pages) |
| Execute RAM | 0 | Built-in |
