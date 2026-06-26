# RV8-GR — Risk Analysis (Final)

**11 hazards analyzed. 1 fixed in hardware. All others safe or deterministic.**

---

## Summary

| # | Hazard | Severity | Status |
|:-:|--------|:--------:|:------:|
| 1 | Memory Map /CE polarity | 🟢 | Correct (active-low) |
| 2 | Z Flag async preset | 🟡 | Safe (200ns settle) |
| 3 | PG_CLK timing | 🟢 | Sync with CLK |
| 4 | RAM /WE margin | 🟢 | >700ns margin @ 1MHz |
| 5 | Store bus contention | 🟢 | **Fixed** (ROM /OE follows WR_DIR) |
| 6 | STR+AC_WR feedback | 🟢 | Deterministic (AC*2) |
| 7 | Illegal ALU modes | 🟢 | All 8 modes deterministic |
| 8 | BR+JMP overlap | 🟢 | = unconditional jump |
| 9 | T2→T0 bus switch | 🟢 | U14 off before U7 on |
| 10 | Bus signal integrity | 🟡 | Safe with cable <30cm |
| 11 | SETDP vs SETPG conflict | 🟢 | XOR_MODE distinguishes |

---

## #2: Z Flag Async Preset

U22 (/P=Q) → U21 (/PR) — async preset when AC=0.

**Risk**: Glitch during AC transition.
**Why safe**: Z sampled 2 clocks later (200ns settle time). BEQ/BNE only checks Z at T2 of next instruction.
**For >20 MHz**: Change to synchronous D-input.

---

## #5: Store Bus Contention (FIXED)

**Problem**: During STORE, U7 must drive DBUS from IBUS. If the data page
selects ROM (A15=0), ROM could also drive DBUS.

**Fix applied**:
```
U7-19  ← BUF_OE_N (U24-12)
ROM /OE ← WR_DIR (U28-8)
```
Result: STORE keeps U7 enabled for the write path and tri-states ROM output.
SB to a ROM page drives DBUS but writes no memory, so it is electrically safe.

---

## #7: Illegal ALU Modes (All Deterministic)

| SUB | XOR | MUX | Used? | Output |
|:---:|:---:|:---:|:-----:|--------|
| 0 | 0 | 0 | ✅ ADD | AC + IBUS |
| 0 | 0 | 1 | ✅ LI/LB | IBUS passthrough |
| 0 | 1 | 0 | ❌ | AC + (IBUS^AC) |
| 0 | 1 | 1 | ✅ XOR | AC ^ IBUS |
| 1 | 0 | 0 | ✅ SUB | AC - IBUS |
| 1 | 0 | 1 | ❌ **NOT** | NOT(IBUS) ← free! |
| 1 | 1 | 0 | ❌ | AC + NOT(IBUS^AC) + 1 |
| 1 | 1 | 1 | ❌ | AC ^ IBUS (= mode 011) |

**No undefined behavior.** Mode 101 = free NOT instruction ($B0/$B8).

---

## #11: SETDP vs SETPG Conflict

**SETDP** ($40) = XOR_MODE=1, MUX=0, SRC=0
**SETPG** ($20) = XOR_MODE=0, MUX=1, SRC=0

Hardware decode (from wiring guide):
- **PG_CLK** = /T2 OR NAND(MUX, /AC_WR) → fires when MUX=1, AC_WR=0
- **DP_Load** = T2 AND XOR AND /ADDR AND /AC_WR (U33 gate 1)

| Opcode | MUX | XOR | PG fires? | DP fires? | Conflict? |
|:------:|:---:|:---:|:---------:|:---------:|:---------:|
| SETPG $20 | 1 | 0 | ✅ | ❌ | ✗ |
| SETDP $40 | 0 | 1 | ❌ | ✅ | ✗ |
| $60 (unused) | 1 | 1 | ✅ | ✅ | ⚠️ both! |

**$60 triggers both PG and DP simultaneously** — but $60 is not in the ISA (harmless).
For valid opcodes: no conflict. MUX and XOR bits naturally separate SETPG/SETDP.

---

## #10: Bus Signal Integrity

| Cable Length | @ 1 MHz | @ 5 MHz | Notes |
|:------------:|:-------:|:-------:|-------|
| <30cm | 🟢 | 🟢 | No issues |
| 30-60cm | 🟢 | 🟡 | Add termination for 5 MHz |
| >60cm | 🟢 | ⛔ | 1 MHz OK, avoid 5 MHz |

**Tips**: 100nF at peripheral VCC, series 33Ω on CLK if ringing at high speed.

---

## Opcode Policy

| Class | Pattern | Count | Behavior |
|-------|---------|:-----:|----------|
| Valid ISA | 18 defined | 18 | Specified |
| Illegal safe | NOT (opcode & $0C)==$0C | 174 | Deterministic |
| Forbidden | (opcode & $0C)==$0C | 64 | Blocked by guard |

---

## IRQ Save-PC Status

| Approach | v1.0 Build (33 chips) | Future vector | v2.0 Future |
|----------|:---------------------:|:----------------:|:-----------:|
| Detect /IRQ edge | ✅ Hardware (U31) | ✅ Hardware | ✅ Hardware |
| Jump to $FF00 | ❌ Software poll+branch | TBD hardware | ✅ Hardware |
| Clear IE on IRQ | ❌ Reset only | TBD hardware | ✅ Hardware |
| Save PC to RAM | ❌ Software (pre-save before EI) | ❌ Software | ✅ Hardware |
| Return from ISR | Software (known addr) | Software | Hardware |

**v1.0 (building now)**: IRQ_FF latch only. Software polls, branches to handler.
IRQ_FF cleared only by /RST — sticky until reset (a future I/O clear may route /SLOT2 to /CLR2).
**Future vector**: not frozen. Two 74HC157 muxes are not sufficient by themselves; the design also needs /PC_LD control, safe IRQ_ack generation, and active-low clear logic.
**v2.0**: +additional logic → hardware save-PC to RAM[$800E:$800F].

---

## SETDP ROM Lookup (Design Strength)

```asm
SETDP $10       ; point to ROM page $10
LB $10          ; AC = ROM[$1010] — lookup table!
```

Enables memory-mapped constant tables (fonts, sin, tiles) with zero extra hardware.
Same LB instruction reads RAM or ROM depending on DP value.

---

## Conclusion

- **1 critical hazard** (STORE to ROM page): Fixed by ROM /OE=WR_DIR, 0 chips added
- **0 remaining electrical risks**: All other hazards are functional-only
- **All 256 opcodes**: deterministic behavior (no undefined states)
- **Clock target**: 1 MHz breadboard (700ns+ margin), 5 MHz PCB only
- **Bus**: safe with <30cm cable

Design is electrically safe for physical build.

---

## Known Limitations (v1.0)

### L1: Opcode $60-$6F triggers both PG and DP

```
$60: MUX=1, XOR=1 → PG_CLK fires AND DP_Load fires simultaneously
Both U23 and U32 latch IBUS value on same cycle.
```

**Impact**: Not harmful (both registers get same value). Not in ISA.
**Policy**: Reserved range. Assembler must not emit $60-$6F.
**v2.0 fix option**: `DP_Load = XOR_MODE AND NOT(MUX_SEL) AND ...` — adds 1 gate.

### L2: IRQ_FF is sticky (one-shot only)

```
┌─────────────────────────────────────────────────────┐
│  IRQ_FF cleared ONLY by /RST in v1.0.               │
│                                                     │
│  After first /IRQ event: IRQ_FF = 1 forever.        │
│  Software cannot re-arm without reset.              │
│                                                     │
│  Intended use: wake-up / event latch (poll once).   │
│  For repeated interrupts: poll I/O directly.        │
│                                                     │
│  v1.1 fix: Route /SLOT2 → U31 /CLR2 (+0 chips)     │
└─────────────────────────────────────────────────────┘
```

### L3: "Hidden" free instructions (not in ISA but functional)

| Opcode | Bits | Effect | Notes |
|:------:|------|--------|-------|
| $B0 imm | SUB+XOR+MUX+AC_WR | AC = NOT(imm) | Free NOT immediate |
| $B8 rs | SUB+XOR+MUX+AC_WR+SRC | AC = NOT(RAM[rs]) | Free NOT register |
| $60 imm | XOR+MUX | PG=imm, DP=imm | Both page regs loaded |
| $11 addr | AC_WR+JMP | AC=ALU result + jump | Compute-and-jump |

These are electrically safe and deterministic but **reserved** — not part of the frozen ISA.
Assembler must not emit them. Future ISA revision may formally adopt $B0/$B8 as NOT.
