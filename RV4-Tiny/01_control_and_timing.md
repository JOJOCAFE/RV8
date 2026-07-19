# RV4-Tiny v1.3 Control and Timing

This is the control-logic source of truth.

## Phase and decode window

```text
FETCH=/T
EXEC=T
```

U7 is enabled only when:

```text
EXEC=1 and CPU_CLK=0
```

That gives every EXECUTE control signal time to settle before the rising edge.

## Control table

| Job | Signal |
|---|---|
| IR load | `U3 /E = T` |
| PC count | `ENP=ENT=FETCH` |
| AC mux select | `S0=OP0`, `S1=OP1` |
| AC load | `AC_LOAD_N` |
| RAM write | `RAM_WE_N=SW_N` |
| RAM driver | `U16 /OE=SW_N` |
| OUT load | `OUT_LOAD_N=OUT_N` |
| PC load | `PC_LOAD_N` |
| HALT data | `HLT_D=NOT(HLT_N)` |

Canonical active-low RAM control:

```text
RAM_WE_N = SW_N
```

## AC load

Opcodes 4-7 have `OP3=0` and `OP2=1`:

```text
OP3_N=NOT(OP3)
AC_LOAD_N=NOT(EXEC AND CPU_CLK_N AND OP2 AND OP3_N)
```

U15A makes `AC_LOAD_N`.

## Branch

Required behavior:

```text
J            -> load PC
JZ and Z=1   -> load PC
otherwise    -> hold PC
```

Equation:

```text
PC_LOAD_N = J_N AND (JZ_N OR NOT(Z))
```

U12 NAND gates:

```text
JZ=NAND(JZ_N,JZ_N)
JZ_TAKEN_N=NAND(JZ,Z)
MIX_N=NAND(J_N,JZ_TAKEN_N)
PC_LOAD_N=NAND(MIX_N,MIX_N)
```

## Zero

```text
Z = NOR(AC0, AC1, AC2, AC3)
```

U13 makes `Z`. It is not stored.

## Clock and HALT

```text
HLT_D=NOT(HLT_N)
CLK_GATE_N = NOT(CLK_COND AND RUN)
CPU_CLK    = NOT(CLK_GATE_N)
CPU_CLK_N  = NOT(CPU_CLK)
```

U2B sets HALT on the HLT EXECUTE edge. `RUN` then becomes 0 and blocks later
clock pulses. `RESET_N` clears HALT without needing a clock.

## Reset

```text
RESET_N=0 -> PC=0 AC=0 OUT=0 T=FETCH HALT=0
```

IR is replaced on the first FETCH.

## Timing rule

Clock-low time must be longer than:

```text
decoder delay + control delay + register setup time + safety margin
```

Use worst-case datasheet values.

## Never do this

- Do not create `AC_CLK` or `OUT_CLK` with logic gates.
- Do not connect AC directly to SRAM data pins.
- Do not enable U7 during FETCH or while CPU_CLK is high.
- Do not use `CLK_GATE_N` as `CPU_CLK_N`.
- Do not leave spare CMOS inputs floating.

## Gate allocation

```text
U12: four branch NAND gates
U13: one zero NOR gate; second gate unused
U14: STEP, RESET_N, CPU_CLK, CPU_CLK_N, OP3_N, HLT_D
U15A: AC_LOAD_N
U15B: CLK_GATE_N
U16: RAM write-data driver
```
