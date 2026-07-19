# RV4-Tiny v1.3 Signal Assignment

This is the wiring source of truth. A name ending in `_N` is active low.

## U1 74HC161 — PC

```text
CLK=CPU_CLK  /CLR=RESET_N  /LOAD=PC_LOAD_N
ENP=FETCH    ENT=FETCH
A..D=ARG0..ARG3
QA..QD=PC0..PC3
RCO=NC
```

## U2 74HC74 — phase and HALT

Section A:

```text
D=/Q  CLK=CPU_CLK  /CLR=RESET_N  /PRE=VCC
Q=EXEC/T  /Q=FETCH
```

Section B:

```text
D=HLT_D  CLK=CPU_CLK  /CLR=RESET_N  /PRE=VCC
Q=HALT  /Q=RUN
```

## U3 74HC377 — IR

```text
D0..D7=ROM_D0..ROM_D7
CLK=CPU_CLK  /E=T
Q0..Q3=ARG0..ARG3
Q4..Q7=OP0..OP3
```

## U4/U5 74HC161 — AC and OUT

Both:

```text
CLK=CPU_CLK  /CLR=RESET_N  ENP=GND  ENT=GND  RCO=NC
```

U4:

```text
A..D=AC_D0..AC_D3  /LOAD=AC_LOAD_N  QA..QD=AC0..AC3
```

U5:

```text
A..D=AC0..AC3  /LOAD=OUT_N  QA..QD=OUT0..OUT3
```

## U6 74HC283 — adder

```text
A0..A3=AC0..AC3
B0..B3=RAM_D0..RAM_D3
CIN=GND
S0..S3=ALU_OUT0..ALU_OUT3
COUT=NC
```

## U7 74HC154 — decoder

```text
A=OP0  B=OP1  C=OP2  D=OP3
/G1=FETCH  /G2=CPU_CLK
Y4=LI_N   Y5=LW_N   Y6=ADD_N  Y7=IN_N
Y8=SW_N   Y9=OUT_N  Y10=JZ_N  Y11=J_N  Y15=HLT_N
other Y outputs=NC
```

## U8/U9 74HC153 — AC mux

Both:

```text
S0=OP0  S1=OP1  /1E=GND  /2E=GND
C0=ARG  C1=RAM_D  C2=ALU_OUT  C3=IN
```

U8 outputs AC_D0/AC_D1. U9 outputs AC_D2/AC_D3.

## U10 — program ROM

```text
A0..A3=PC0..PC3
higher A pins=GND
D0..D7=ROM_D0..ROM_D7
/CE=GND  /OE=GND  /WE=VCC
```

## U11 — data SRAM

```text
A0..A3=ARG0..ARG3
higher A pins=GND
D0..D3=RAM_D0..RAM_D3
D4..D7=NC
/CE=GND  /OE=GND  /WE=SW_N
```

## U12 74HC00 — branch

```text
gate A: JZ_N,JZ_N -> JZ
gate B: JZ,Z -> JZ_TAKEN_N
gate C: J_N,JZ_TAKEN_N -> MIX_N
gate D: MIX_N,MIX_N -> PC_LOAD_N
```

## U13 74HC4002 — zero

```text
1A=AC0  1B=AC1  1C=AC2  1D=AC3  1Y=Z
2A..2D=GND  2Y=NC
```

## Clock/control support — U14/U15

U14 74HC14:

```text
A STEP conditioner
B RESET_N conditioner
C CLK_GATE_N -> CPU_CLK
D CPU_CLK -> CPU_CLK_N
E OP3 -> OP3_N
F HLT_N -> HLT_D
```

U15 74HC20:

```text
gate A: EXEC,CPU_CLK_N,OP2,OP3_N -> AC_LOAD_N
gate B: CLK_COND,RUN,VCC,VCC -> CLK_GATE_N
output CLK_GATE_N
```

## U16 74HC125 — RAM write driver

```text
1A..4A=AC0..AC3
1Y..4Y -> 100-330 ohm -> RAM_D0..RAM_D3
/1OE../4OE=SW_N
```

## Reset state

```text
PC=0  AC=0  OUT=0  T=FETCH  HALT=0  RUN=1
```

## Unused-pin rule

- Tie every unused input to VCC or GND.
- Leave unused outputs open.
- Never tie SRAM data outputs to a rail.
- Never connect two push-pull outputs together.
