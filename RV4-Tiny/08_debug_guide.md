# RV4-Tiny v1.3 Debug Guide

Debug in this order:

```text
power -> reset -> clock -> phase -> PC -> ROM -> IR -> decoder
-> AC -> OUT -> RAM -> adder -> zero/branch
```

Use a multimeter and an oscilloscope or logic analyzer. An LED cannot prove
that a clock pulse is clean.

## Probe point map

Use these points before guessing:

| Signal | Probe at | Expected |
|---|---|---|
| `+5 V`, `GND` | every IC socket | correct rail before inserting ICs |
| `RESET_N` | U1/U2/U4/U5 clear pins | low during reset, high while running |
| `CLK_COND` | U14/U15 clock input path | one clean pulse per STEP |
| `CPU_CLK` | every register clock pin | shared rising-edge clock |
| `CPU_CLK_N` | inverse clock net | inverse of `CPU_CLK` |
| `FETCH`, `EXEC` | U2 phase outputs | alternate every clock edge |
| `PC0..PC3` | U1 outputs | count/load behavior |
| `ROM_D0..ROM_D7` | ROM/U3 input bus | instruction byte during FETCH |
| `OP0..OP3`, `ARG0..ARG3` | U3 outputs | stable decoded instruction fields |
| `LI_N..HLT_N` | U7 outputs | active only during EXECUTE clock-low |
| `AC_D0..AC_D3` | U8/U9 outputs | selected AC input |
| `AC0..AC3` | U4 outputs | accumulator state |
| `OUT0..OUT3` | U5 outputs | display state |
| `RAM_D0..RAM_D3` | U11/U16 shared bus | SRAM owner except during SW |
| `ALU_OUT0..ALU_OUT3` | U6 outputs | AC + RAM_D result |
| `Z` | U13 output | high only when AC is 0 |
| `PC_LOAD_N` | U12 output | low only for taken J/JZ |
| `HLT_D`, `HALT`, `RUN` | U2/U14/U15 support | halt gates the clock until reset |

## Temporary wire audit

Before moving to the next stage, write down:

```text
Stage:
Temporary wires used:
Temporary wires removed:
Probe points checked:
Pass/fail:
```

Do not continue if a temporary forced signal is still connected.

## Quick checks

| Stage | Expected |
|---|---|
| Power | +5 V at every IC; no hot chip |
| Reset | `PC=AC=OUT=0`, `T=FETCH`, `HALT=0` |
| Clock | one rising edge per STEP press |
| Phase | T changes every edge |
| PC | counts on FETCH only |
| IR | loads ROM on FETCH only |
| Decoder | active only during EXECUTE clock-low |
| AC | loads only for LI/LW/ADD/IN |
| OUT | changes only for OUT |
| RAM | writes only for SW |
| Z | high only when AC=0 |

## Clock/control faults

Probe:

```text
CLK_COND CLK_GATE_N CPU_CLK CPU_CLK_N RESET_N AC_LOAD_N HLT_D
```

- Two edges per press: fix debounce.
- No clock after reset: inspect RUN and HALT.
- AC changes twice: U4 must use CPU_CLK and `/LOAD`, not a gated clock.
- Wrong HALT: test U14/U15 before reconnecting U2.

## Program path faults

At FETCH:

```text
IR after edge = ROM[old PC]
PC after edge = old PC + 1
```

- PC changes on EXECUTE: check ENP/ENT.
- IR changes on EXECUTE: check U3 `/E=T`.
- Wrong instruction: check ROM address/data bit order.
- Decoder active during FETCH: check U7 enables.

## Datapath faults

For `LI 5`:

```text
AC mux=0101
AC_LOAD_N=0 before EXECUTE edge
AC=0101 after edge
```

For OUT, U5 count enables must be grounded. If LEDs follow AC all the time,
OUT has been bypassed.

## RAM faults

During SW:

```text
SW_N=0
U16 enabled
SRAM /WE=0
ARG and AC stable
```

Outside SW:

```text
U16 high impedance
SRAM drives RAM_D
```

If RAM changes during another instruction, stop power and inspect U7, SW_N, and
U16. Do not continue with a bus fight.

## Adder and branch faults

- Set AC=14 and RAM=3; ALU output must be 1.
- Check U6 CIN=0 and bit order.
- Probe U13 inputs and Z for all 16 AC values.
- For J, `PC_LOAD_N=0`.
- For JZ, `PC_LOAD_N=0` only when Z=1.

## Symptom map

| Symptom | First place to look |
|---|---|
| Nothing works | power, RESET_N, CPU_CLK |
| Random steps | debounce |
| PC works but IR wrong | ROM, U3 `/E` |
| Wrong AC | mux, AC_LOAD_N |
| RAM corrupts | SW_N, U16, data bus |
| J works but JZ fails | U13 Z, U12 |
| HLT will not reset | U2 `/CLR`, RESET_N |

## Record evidence

Write down:

- ROM/RAM images;
- exact IC part numbers;
- state before and after the edge;
- relevant control signals;
- scope probe point and time scale.

A repeatable passing test closes the fault, not “it seems to work.”
