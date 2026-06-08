# RV8-GR — Bank Switch & Memory Expansion (Stable)

**CPU has 33 chips with SETDP (full 64KB data access). Expansion only needed for ROM banking.**

---

## Base Memory Map

```
$0000-$7FFF  RAM 32KB (/CE = A15) — read/write via SETDP $00-$7F
$8000-$FEFF  ROM 32KB (/CE = /A15) — read via SETDP $80-$FE
$FF10-$FF1F  I/O Slot 1 (/SLOT1 on RV8-Bus)
$FF20-$FF2F  I/O Slot 2 (/SLOT2 on RV8-Bus)
```

### Data Access (built-in, no expansion needed)

```asm
SETDP $00       ; page 0: registers ($0000-$00FF)
SETDP $10       ; page $10: data at $1000-$10FF
SETDP $7F       ; page $7F: RAM at $7F00-$7FFF
SETDP $80       ; page $80: ROM read at $8000-$80FF
SETDP $FF       ; page $FF: ROM/IO at $FF00-$FFFF
```

Full 64KB accessible. No expansion chip needed.

---

## ROM Bank Expansion (32KB → 128KB)

AT28C256 = 32KB. To get more ROM: use SST39SF010A (128KB) + bank latch.

Extra chip: 1× 74HC574 on expansion board.

```
ROM A16 ← latch Q0 (selects bank 0 or 1)
Latch CLK ← address decode (write to specific I/O address)
Latch D0 ← DBUS D0
```

**Software:**
```asm
SETDP $FF       ; I/O page
LI $01          ; bank 1
SB $10          ; write to $FF10 → /SLOT1 active → latch captures D0 → ROM A16=1
```

---

## Execute from RAM (Built-in)

No expansion needed. PC < $8000 → fetches from RAM.

```asm
SETPG $00
J $00           ; PC=$0000, fetches from RAM
```

---

## Summary

| Feature | Chips | How |
|---------|:-----:|-----|
| Full 64KB data access | 0 (built-in) | SETDP instruction (U32) |
| ROM bank (128KB) | +1 (74HC574) | Expansion board latch |
| Execute from RAM | 0 (built-in) | PC < $8000 |
