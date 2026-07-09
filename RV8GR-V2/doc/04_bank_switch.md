# RV8-GR — Bank Switch & Memory Expansion (Stable)

**CPU has 36 packages with SETDP (full 64KB data access). Expansion only needed for ROM banking.**

> FUTURE ONLY: ROM banking is not part of the RV8GR-V2 student baseline.
> Build and verify the 34-logic-chip CPU first. Do not add bank-switch wiring
> until the baseline passes the full instruction smoke test.

---

## Base Memory Map

```
$0000-$7EFF  ROM 32KB (/CE = A15) — read via SETDP $00-$7E
$7F00-$7FFF  ROM (available)
$8000-$FEFF  RAM 32KB (/CE = /A15) — read/write via SETDP $80-$FE
$FF00-$FF0F  RAM (available; future vector area)
$FF10-$FF1F  I/O Slot 1 (/SLOT1 on RV8-Bus)
$FF20-$FF2F  I/O Slot 2 (/SLOT2 on RV8-Bus)
$FF30-$FFFF  RAM (available)
```

### Data Access (built-in, no expansion needed)

SETDP = 2-byte instruction: opcode `$40` + operand (page value)

```asm
; SETDP encoding: $40 = XOR_MODE=1, SRC=0, STR=0, AC_WR=0
; U33 decodes: DP_Load = T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR
; Alias $C0 also works (SUB bit ignored by U33 decode)

SETDP $80       ; page $80: registers ($8000-$80FF)
SETDP $90       ; page $90: data at $9000-$90FF
SETDP $FF       ; page $FF: RAM at $FF00-$FFFF (last RAM page)
SETDP $00       ; page $00: ROM read at $0000-$00FF
SETDP $7F       ; page $7F: ROM + I/O at $7F00-$7FFF
```

Full 64KB accessible. No expansion chip needed.

> ⚠️ **SB to ROM address = ไม่มีผล!**
>
> SETDP < $80 → A15=0 → RAM /CE=HIGH (disabled), ROM selected
> ROM `/WE` is on `/WR` for programmer support, but normal CPU stores do not
> perform the EEPROM/flash unlock sequence, so ROM contents do not change.
> ใช้ LB อ่านจาก ROM ได้ (lookup table, string table) แต่เขียนไม่ได้

---

## ROM Bank Expansion (32KB → 128KB)

### v2.x Contract (Reserved — not implemented in v1.0)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| BANK width | 2 bits [1:0] | 4 banks × 32KB = 128KB. 1× 74HC74 = 1 chip |
| Affected range | ROM only ($0000-$7FFF) | RAM unchanged — no impact on DP, SB, LB |
| Reset value | BANK = 0 | Boot ROM must be deterministic |
| Future IRQ vector | Always bank 0 | $FF00 is in RAM — unaffected by ROM banking if a vector design is built |
| Chip budget | +1 (74HC74) | Within 3-package remaining budget |
| Instruction | SETBANK imm (via I/O write) | No new opcode — uses SB to /SLOT address |

```
ROM physical address = {BANK[1:0], A14..A0} = 17 bits = 128KB
ROM chip: SST39SF010A (128KB) or W27C010 (128KB)
Bank register: 74HC74 (2 flip-flops, bits 0-1)
Latch CLK: /SLOT1 decode (write to $FF10)
Latch D: DBUS D[1:0]
```

**Constraints (must preserve v1.0 behavior):**
- Bank 0 must contain boot code (reset → PC=$0000 → bank 0)
- Bank switching is software-only (no auto-bank on jump)
- RAM ($8000-$FFFF) is never banked
- All v1.0 programs run unmodified on bank 0

**Software:**
```asm
SETDP $FF       ; I/O page
LI $02          ; bank 2
SB $10          ; write to $FF10 → /SLOT1 → latch captures D[1:0]
SETDP $80       ; back to RAM
; ROM now shows bank 2 content at $0000-$7FFF
```

---

## Banked Address Formula

```
Logical CPU address: $0000-$7FFF (ROM space, 15 bits)
Physical ROM address: {BANK[1:0], A14..A0} = 17 bits

Examples:
  BANK=0, CPU=$1234 → ROM physical $01234 (bank 0, offset $1234)
  BANK=1, CPU=$1234 → ROM physical $11234 (bank 1, offset $1234)
  BANK=2, CPU=$1234 → ROM physical $21234 (bank 2, offset $1234)
  BANK=3, CPU=$1234 → ROM physical $31234 (bank 3, offset $1234)

RAM ($8000-$FFFF) is NOT affected — always maps to physical RAM directly.
```

---

## Reserved Expansion I/O ($FF10-$FF1F)

| Address | Function | Status |
|:-------:|----------|:------:|
| $FF10 | BANK register D[1:0] | v2.x |
| $FF11 | (reserved) | — |
| $FF12 | (reserved) | — |
| $FF13-$FF1F | (reserved for future /SLOT1 devices) | — |

> 📌 Do not assign $FF10 to other peripherals. Bank register owns this address.

---

## Interrupt Safety Rule

Software must not switch ROM bank while an external polling handler could run
from a bank-specific address. v1.0 DI does not disable hardware; use a software
guard flag or arrange handlers identically in every bank.

```asm
; Safe pattern:
    ; set software guard flag before bank switch
    SETDP $FF
    LI $02
    SB $10          ; switch to bank 2
    SETDP $80
    ; clear software guard flag after switch complete
```

---

## Execute from RAM (Built-in)

No expansion needed. PC >= $8000 → fetches from RAM.

```asm
SETPG $80
J $00           ; PC=$8000, fetches from RAM
```

---

## Summary

| Feature | Chips | Status | How |
|---------|:-----:|:------:|-----|
| Full 64KB data access | 0 (built-in) | v1.0 ✅ | SETDP instruction (U32+U33) |
| Execute from RAM | 0 (built-in) | v1.0 ✅ | PC >= $8000 fetches from RAM |
| ROM bank 128KB | +1 (74HC74) | v2.x reserved | I/O latch on expansion board |

---

## Bank Register Power-On State

| Register | Reset Value | How |
|----------|:-----------:|-----|
| BANK[1:0] | 00 | 74HC74 /CLR ← /RST |

Boot is always from bank 0. Software must not assume any other bank is active after reset.

---

## Compatibility Contract

```
┌─────────────────────────────────────────────────────┐
│  All RV8-GR v1.0 software MUST run unchanged        │
│  when BANK = 0.                                     │
│                                                     │
│  Bank switching must NOT alter:                     │
│    • Opcode behavior                                │
│    • Logical memory map ($0000-$FFFF)               │
│    • DP semantics                                   │
│    • PG semantics                                   │
│    • IRQ vector behavior                            │
│    • RAM content or addressing                      │
│                                                     │
│  Banking is transparent to the CPU —                │
│  only the ROM chip sees different physical address. │
└─────────────────────────────────────────────────────┘
```

> 📌 Banking does NOT require any change to frozen v1.0 logic.
> It is implemented entirely on the expansion board via /SLOT1 I/O write.
