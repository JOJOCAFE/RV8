# RV8-GR — Risk Analysis (Final)

**10 hazards analyzed. 1 fixed in hardware. All others safe or deterministic.**

---

## Summary

| # | Hazard | Severity | Status |
|:-:|--------|:--------:|:------:|
| 1 | Memory Map /CE polarity | 🟢 | Correct (active-low) |
| 2 | Z Flag async preset | 🟡 | Safe (200ns settle) |
| 3 | PG_Load_N timing | 🟢 | Sync with CLK |
| 4 | RAM /WE margin | 🟢 | 70ns margin @ 10MHz |
| 5 | SRC+STR bus conflict | 🟢 | **Fixed** (U25 gate 3) |
| 6 | STR+AC_WR feedback | 🟢 | Deterministic (AC*2) |
| 7 | Illegal ALU modes | 🟢 | All 8 modes deterministic |
| 8 | BR+JMP overlap | 🟢 | = unconditional jump |
| 9 | T2→T0 bus switch | 🟢 | U14 off before U7 on |
| 10 | Bus signal integrity | 🟡 | Safe with cable <30cm |

---

## #2: Z Flag Async Preset

U22 (/P=Q) → U21 (/PR) — async preset when AC=0.

**Risk**: Glitch during AC transition.
**Why safe**: Z sampled 2 clocks later (200ns settle time). BEQ/BNE only checks Z at T2 of next instruction.
**For >20 MHz**: Change to synchronous D-input.

---

## #5: SRC+STR Bus Conflict (FIXED)

**Problem**: SRC=1 + STR=1 → U7 + U14 both drive IBUS → electrical fight.
**Pattern**: `(opcode & $0C) == $0C` → 64 forbidden opcodes.

**Fix applied**:
```
BUF_OE_SAFE = BUF_OE_N OR STR
U25-9 ← U24-12 (BUF_OE_N)
U25-10 ← U5-17 (STR)
U25-8 → U7-19
```
Result: STR=1 → U7 always disabled → STORE wins → no bus fight.

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

## #10: Bus Signal Integrity

| Cable Length | Max Clock | Status |
|:------------:|:---------:|:------:|
| <30cm | 10 MHz | 🟢 Safe |
| 30-60cm | 5 MHz | 🟡 Add termination |
| >60cm | 1 MHz | ⛔ Not recommended |

**Tips**: 100nF at peripheral VCC, series 33Ω on CLK if ringing.

---

## Opcode Policy

| Class | Pattern | Count | Behavior |
|-------|---------|:-----:|----------|
| Valid ISA | 17 defined | 17 | Specified |
| Illegal safe | NOT (opcode & $0C)==$0C | 175 | Deterministic |
| Forbidden | (opcode & $0C)==$0C | 64 | Blocked by guard |

---

## Conclusion

- **1 critical hazard** (SRC+STR): Fixed with spare gate, 0 chips added
- **0 remaining electrical risks**: All other hazards are functional-only
- **All 256 opcodes**: deterministic behavior (no undefined states)
- **Bus**: safe at 10 MHz with <30cm cable

Design is electrically safe for physical build.
