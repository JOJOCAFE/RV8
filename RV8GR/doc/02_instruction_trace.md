# RV8-GR — Instruction Trace (Golden Debug Trace)

**Pin-level traces for key instructions. Based on 01_wiring_guide.md (36 packages).**

Use this file when single-stepping the real CPU or comparing simulator logs.
It is not the ISA source of truth; `00_design_isa.md` owns the architecture and
`01_wiring_guide.md` owns physical pin wiring. This file shows what students
should expect to see on buses, control lines, and LEDs during important
instructions.

---

## Trace 1: ADDI $05 ($10, $05) — AC=$10 → AC=$15

### T0: Fetch control byte
```
ABUS = PC = $0000, ROM /CE=0, DBUS=$10
U7 enabled (DIR=0, D→IB), IBUS=$10
U5 latches $10 on T0 edge → AC_WR=1, rest=0
PC → $0001
```

### T1: Fetch operand
```
ABUS = $0001, ROM outputs $05, IBUS=$05
U6 latches $05 on T1 edge
PC → $0002
```

### T2: Execute
```
/IRL_OE = NAND(1,1)=0 → U34 drives IBUS=$05
XOR_MODE=0 → XOR B-mux=SUB=0 → XOR out = $05 XOR $00 = $05
Adder: AC($10) + XOR($05) + Cin(0) = $15
MUX_SEL=0 → AC mux = adder = $15
ACC_CLK = NAND(T2=1, AC_WR=1) = 0 during T2
At T2→T0 edge: ACC_CLK rises → U9 latches $15 and U21 updates Z
```
**Result: AC = $15 ✓**

---

## Trace 2: SB $03 ($04, $03) — RAM[$03] = AC

### T2: Execute (AC=$AA)
```
IR=$04: STR=1, /ADDR_MODE=0
Addr mux = IRL=$03, A[15:8]=DP=$80 → addr=$8003
A15=1 → /A15=0 → RAM selected
/AC_BUF = NAND(T2=1, STR=1) = 0 → U14 drives IBUS=AC=$AA
WR_DIR = NOT(0) = 1 → U7 DIR=1 (IB→D)
DBUS=$AA, RAM /WE=0 → RAM[$8003]=$AA
```
**Result: RAM[$8003] = $AA ✓**

---

## Trace 3: XORI $55 ($70, $55) — AC=$FF → AC=$AA

### T2: Execute
```
IR=$70: XOR_MODE=1, MUX_SEL=1, AC_WR=1
/IRL_OE=0 → IBUS=$55
XOR_MODE=1 → XOR B-mux=AC=$FF
XOR: $55 ^ $FF = $AA
MUX_SEL=1 → AC mux = XOR output = $AA
At T2→T0 edge: ACC_CLK rises → AC latches $AA
```
**Result: AC = $AA ✓**

---

## Trace 4: BEQ $20 ($02, $20) — Z=1, branch taken

### T2: Execute
```
IR=$02: BR=1, JMP=0
Z_match = Z_flag(1) XOR SUB(0) = 1
/BR_TAKEN = NAND(BR=1, Z_match=1) = 0
PC_LOAD_COND = NAND(/JUMP=1, /BR_TAKEN=0) = 1
/PC_LD = NAND(T2=1, 1) = 0 → PC loads
PC D[7:0]=IRL=$20, D[15:8]=PG=$00 → PC=$0020
```
**Result: PC = $0020 ✓**

---

## Trace 5: SETPG $90 ($20, $90) — PG=$90

### T2: Execute
```
IR=$20: MUX_SEL=1, AC_WR=0
/IRL_OE=0 → IBUS=$90
/PG_cond = NAND(MUX_SEL=1, /AC_WR=1) = 0
PG_CLK = OR(/T2=0, /PG_cond=0) = 0
At T2→T0 edge: PG_CLK rises → U23 latches $90
```
**Result: PG = $90 ✓**

---

## Trace 6: J $00 ($01, $00) — PC=$9000

### T2: Execute (PG=$90)
```
IR=$01: JMP=1
/JUMP = NOT(1) = 0
PC_LOAD_COND = NAND(0, x) = 1
/PC_LD = NAND(1, 1) = 0 → PC loads
PC = {PG=$90, IRL=$00} = $9000
```
**Result: PC = $9000 ✓**

---

## Trace 7: LB $03 ($38, $03) — AC=RAM[$8003]

### T2: Execute (RAM[$8003]=$AA)
```
IR=$38: MUX_SEL=1, AC_WR=1, SRC=1
/ADDR_MODE=0 → addr mux=IRL=$03, A[15:8]=DP=$80
A15=1 → /A15=0 → RAM selected
BUF_OE_N=0 → U7 enabled (DBUS→IBUS)
U7 reads RAM → IBUS=$AA
XOR_MODE=0 → XOR out = IBUS = $AA
MUX_SEL=1 → AC mux = XOR out = $AA
At T2→T0 edge: ACC_CLK rises → AC latches $AA
```
**Result: AC = $AA ✓**

---

## Trace 8: SETDP $80 ($40, $80) — DP=$80

### T2: Execute
```
IR=$40: XOR_MODE=1, MUX_SEL=0, AC_WR=0, SRC=0, STR=0
ADDR_REQ = SRC|STR = 0
/IRL_OE = NAND(T2=1, /ADDR_MODE=1) = 0 → U34 drives IBUS=$80
DP_Load = T2(1) AND XOR_MODE(1) AND /ADDR_MODE(1) AND /AC_WR(1) = 1
At T2 start: DP_Load rises after U33 delay → U32 latches $80 on rising edge

Bus: ABUS=PC, IBUS=U34($80), DBUS=ROM(stale)
Check: ✓ PG_CLK stays HIGH (MUX=0) ✓ AC unchanged (AC_WR=0)
```
**Result: DP = $80 ✓**

---

## Trace 9: BNE $20 ($82, $20) — Z=0, branch taken

### T2: Execute
```
IR=$82: SUB=1, BR=1, JMP=0, AC_WR=0, SRC=0, STR=0
Z_match = Z_flag(0) XOR SUB(1) = 1
/BR_TAKEN = NAND(BR=1, Z_match=1) = 0
PC_LOAD_COND = NAND(/JUMP=1, /BR_TAKEN=0) = 1
/PC_LD = NAND(T2=1, 1) = 0 → PC loads
PC = {PG=$00, IRL=$20} = $0020

Bus: ABUS=PC, IBUS=U34($20), DBUS=ROM(stale)
Check: ✓ Same hardware as BEQ — SUB bit flips Z_match polarity
```
**Result: PC = $0020 ✓ (BNE reuses BEQ hardware via Z XOR SUB)**

---

## Trace 10: Mixed Opcode $0C — Store-Dominant Bus Direction

### T2: Execute (hypothetical — opcode $0C has SRC=1, STR=1)
```
IR=$0C: SRC=1, STR=1, /ADDR_MODE=0
Addr mux = {DP,IRL} → ABUS = data address
/AC_BUF = NAND(T2=1, STR=1) = 0 → U14 drives IBUS = AC

U7 /OE = BUF_OE_N = 0 → U7 enabled
WR_DIR=1 → U7 direction is IBUS→DBUS
ROM /OE=WR_DIR=1 → ROM output tri-stated during write direction

Result: U14 drives IBUS, U7 writes that value to DBUS, RAM write proceeds if A15=1
No bus contention. Store executes. RAM gets AC value.
```
**Result: Store path is electrically safe ✓**

> 📌 64 opcodes where (opcode & $0C) == $0C are reserved — none are in the ISA.
> Store direction is deterministic even if executed accidentally.

---

## Trace 11: Boot Sequence (SETDP $80 → SETPG $00 → LI $00)

Power-on state: PC=$0000, PG=??, DP=??, AC=??, Z=??

### Instruction 1: SETDP $80 ($40, $80) at $0000
```
T0: PC=$0000, ABUS=$0000, A15=0 → ROM selected
    DBUS=$40, U7→IBUS=$40, U5 latches $40. PC→$0001
T1: PC=$0001, DBUS=$80, U6 latches $80. PC→$0002
T2: IR=$40: XOR_MODE=1, /ADDR_MODE=1, AC_WR=0
    /IRL_OE=0 → U34 drives IBUS=$80
    DP_Load rises after U33 delay near T2 start → U32 latches $80
    ✓ ABUS=PC (no data access) — DP=?? is harmless
```
**Result: DP = $80 ✓ (RAM page selected for registers)**

### Instruction 2: SETPG $00 ($20, $00) at $0002
```
T0: PC=$0002, DBUS=$20, U5 latches $20. PC→$0003
T1: PC=$0003, DBUS=$00, U6 latches $00. PC→$0004
T2: IR=$20: MUX_SEL=1, AC_WR=0, /ADDR_MODE=1
    /IRL_OE=0 → IBUS=$00
    PG_CLK: 0→1 at T2→T0 edge → U23 latches $00
    ✓ ABUS=PC — PG=?? is harmless (no jump yet)
```
**Result: PG = $00 ✓ (page 0 for safe jumps)**

### Instruction 3: LI $00 ($30, $00) at $0004
```
T0: PC=$0004, DBUS=$30, U5 latches $30. PC→$0005
T1: PC=$0005, DBUS=$00, U6 latches $00. PC→$0006
T2: IR=$30: MUX_SEL=1, AC_WR=1, XOR_MODE=0
    /IRL_OE=0 → IBUS=$00
    XOR out = $00 XOR $00 = $00
    MUX_SEL=1 → AC mux = XOR out = $00
    ACC_CLK rises at T2→T0 edge → AC=$00, Z=1
```
**Result: AC=$00, Z=1 ✓ (all architectural state now defined)**

> 📌 After 3 instructions (9 clocks): PC=$0006, DP=$80, PG=$00, AC=$00, Z=1.
> Safe to use SRC/STR/J/BEQ from this point onward.

---

## Summary

| # | Instruction | Opcode | Key Signal | Result |
|:-:|-------------|:------:|------------|--------|
| 1 | ADDI | $10 | AC_WR, adder | AC = AC + imm |
| 2 | SB | $04 | STR, /AC_BUF, WR_DIR | RAM ← AC |
| 3 | XORI | $70 | XOR_MODE, MUX_SEL | AC = AC ^ imm |
| 4 | BEQ | $02 | BR, Z_match, /PC_LD | PC loads if Z=1 |
| 5 | SETPG | $20 | MUX_SEL, PG_CLK | PG ← IBUS |
| 6 | J | $01 | JMP, /PC_LD | PC = {PG, addr} |
| 7 | LB | $38 | SRC, /ADDR_MODE, BUF_OE_N | AC = RAM[{DP,rs}] |
| 8 | SETDP | $40 | XOR_MODE, DP_Load | DP ← operand |
| 9 | BNE | $82 | SUB, BR, Z_match | PC loads if Z=0 |
| 10 | Mixed SRC+STR | $0C | WR_DIR=1, ROM /OE=1 | Store wins, no conflict |
| 11 | Boot Seq | $40→$20→$30 | DP_Load, PG_CLK, AC_WR | All state defined |

All 11 traces verified pin-by-pin against 01_wiring_guide.md. ✓

---

## Bus Ownership Quick Reference

| Trace | ABUS | IBUS driver | DBUS driver |
|:-----:|:----:|:-----------:|:-----------:|
| ADDI (T2) | PC | U34 (immediate) | ROM (stale) |
| SB (T2) | {DP,IRL} | U14 (AC) | U7 (write) |
| XORI (T2) | PC | U34 (immediate) | ROM (stale) |
| BEQ (T2) | PC | U34 (immediate) | ROM (stale) |
| SETPG (T2) | PC | U34 (immediate) | ROM (stale) |
| J (T2) | PC | U34 (immediate) | ROM (stale) |
| LB (T2) | {DP,IRL} | U7 (RAM read) | RAM |
| SETDP (T2) | PC | U34 (immediate) | ROM (stale) |
| BNE (T2) | PC | U34 (immediate) | ROM (stale) |
| Mixed SRC+STR (T2) | {DP,IRL} | U14 (AC) | U7 (write), ROM disabled |
| Boot: SETDP (T2) | PC | U34 (immediate) | ROM (stale) |
| Boot: SETPG (T2) | PC | U34 (immediate) | ROM (stale) |
| Boot: LI (T2) | PC | U34 (immediate) | ROM (stale) |

---

## Golden Trace (Regression Reference)

Program: `LI $42 → ADDI $01 → SUBI $43 → BEQ target`

ROM contents: `$30 $42 $10 $01 $90 $43 $02 $08`

All simulators must produce this exact output (after boot: DP=$80, PG=$00, AC=$00, Z=1):

```
Cycle  Phase  PC    ABUS  IRH  IRL  Mnemonic  AC  Z  PG  DP  Notes
-----  -----  ----  ----  ---  ---  --------  --  -  --  --  -----
1      T0     0000  0000  30   --   --        00  1  00  80  fetch ctrl
2      T1     0001  0001  30   42   --        00  1  00  80  fetch operand
3      T2     0002  0002  30   42   LI        42  0  00  80  AC=$42
4      T0     0002  0002  10   --   --        42  0  00  80  fetch ctrl
5      T1     0003  0003  10   01   --        42  0  00  80  fetch operand
6      T2     0004  0004  10   01   ADDI      43  0  00  80  AC=$42+$01=$43
7      T0     0004  0004  90   --   --        43  0  00  80  fetch ctrl
8      T1     0005  0005  90   43   --        43  0  00  80  fetch operand
9      T2     0006  0006  90   43   SUBI      00  1  00  80  AC=$43-$43=$00
10     T0     0006  0006  02   --   --        00  1  00  80  fetch ctrl
11     T1     0007  0007  02   08   --        00  1  00  80  fetch operand
12     T2     0008  0008  02   08   BEQ       00  1  00  80  Z=1→branch taken, PC=$0008
```

**Expected final state**: PC=$0008, AC=$00, Z=1, PG=$00, DP=$80

> 📌 Any simulator or testbench that does NOT produce this exact sequence has a bug.
> Use this as the first regression check after any code change.
