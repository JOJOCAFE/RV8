# RV8-GR — Instruction Trace (Stable)

**Pin-level traces for key instructions. Based on 03_wiring_guide.md (30 chips).**

---

## Trace 1: ADDI $05 ($10, $05) — AC=$10 → AC=$15

### T0: Fetch control byte
```
ABUS = PC = $8000, ROM /CE=0, DBUS=$10
U7 enabled (DIR=0, D→IB), IBUS=$10
U5 latches $10 on T0 edge → AC_WR=1, rest=0
PC → $8001
```

### T1: Fetch operand
```
ABUS = $8001, ROM outputs $05, IBUS=$05
U6 latches $05 on T1 edge
PC → $8002
```

### T2: Execute
```
/IRL_OE = NAND(1,1)=0 → U6 drives IBUS=$05
XOR_MODE=0 → XOR B-mux=SUB=0 → XOR out = $05 XOR $00 = $05
Adder: AC($10) + XOR($05) + Cin(0) = $15
MUX_SEL=0 → AC mux = adder = $15
Acc_Load_N = NAND(T2=1, AC_WR=1) = 0 → AC latches $15
```
**Result: AC = $15 ✓**

---

## Trace 2: SB $03 ($04, $03) — RAM[$03] = AC

### T2: Execute (AC=$AA)
```
IR=$04: STR=1, ADDR_MODE=1
Addr mux = IRL=$03, A[15:8]=GND → addr=$0003
A15=0 → RAM /CE=0
/AC_BUF = NAND(T2=1, STR=1) = 0 → U14 drives IBUS=AC=$AA
WR_DIR = NOT(0) = 1 → U7 DIR=1 (IB→D)
DBUS=$AA, RAM /WE=0 → RAM[$0003]=$AA
```
**Result: RAM[$03] = $AA ✓**

---

## Trace 3: XORI $55 ($70, $55) — AC=$FF → AC=$AA

### T2: Execute
```
IR=$70: XOR_MODE=1, MUX_SEL=1, AC_WR=1
/IRL_OE=0 → IBUS=$55
XOR_MODE=1 → XOR B-mux=AC=$FF
XOR: $55 ^ $FF = $AA
MUX_SEL=1 → AC mux = XOR output = $AA
AC latches $AA
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
PC D[7:0]=IRL=$20, D[15:8]=PG=$80 → PC=$8020
```
**Result: PC = $8020 ✓**

---

## Trace 5: SETPG $90 ($20, $90) — PG=$90

### T2: Execute
```
IR=$20: MUX_SEL=1, AC_WR=0
/IRL_OE=0 → IBUS=$90
/PG_cond = NAND(MUX=1, /AC_WR=1) = 0
PG_Load_N = OR(/T2=0, /PG_cond=0) = 0
At T2→T0 edge: PG_Load_N rises → U23 latches $90
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

## Trace 7: LB $03 ($38, $03) — AC=RAM[$03]

### T2: Execute (RAM[$03]=$AA)
```
IR=$38: MUX_SEL=1, AC_WR=1, SRC=1
ADDR_MODE=1 → addr mux=IRL=$03, A[15:8]=GND
A15=0 → RAM /CE=0, U7 reads RAM → IBUS=$AA
XOR_MODE=0 → XOR out = IBUS = $AA
MUX_SEL=1 → AC mux = XOR out = $AA
AC latches $AA
```
**Result: AC = $AA ✓**

---

## Summary

| # | Instruction | Opcode | Key Signal | Result |
|:-:|-------------|:------:|------------|--------|
| 1 | ADDI | $10 | AC_WR, adder | AC = AC + imm |
| 2 | SB | $04 | STR, /AC_BUF, WR_DIR | RAM ← AC |
| 3 | XORI | $70 | XOR_MODE, MUX_SEL | AC = AC ^ imm |
| 4 | BEQ | $02 | BR, Z_match, /PC_LD | PC loads if Z |
| 5 | SETPG | $20 | MUX_SEL, !AC_WR | PG ← IBUS |
| 6 | J | $01 | JMP, /PC_LD | PC = {PG, addr} |
| 7 | LB | $38 | SRC, MUX_SEL, AC_WR | AC = RAM[rs] |

All 7 traces verified pin-by-pin against 03_wiring_guide.md. ✓
