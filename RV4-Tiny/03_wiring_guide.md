# RV4-Tiny v1.3 Wiring Guide

Use this guide to connect functional signals. Use
`11_chip_pinouts.md` and the manufacturer datasheet for physical pin
numbers.

## Power first

- Regulated supply: `+5 V`.
- Join all grounds.
- Put 100 nF beside every IC.
- Add 47-100 uF at the power input.
- Never leave a CMOS input floating.

## Clock/control support: U14 and U15

Important signals:

```text
CLK_COND   cleaned STEP or EXT clock
CLK_GATE_N clock after HALT gate, inverted
CPU_CLK    shared rising-edge clock
CPU_CLK_N  inverse of CPU_CLK
RESET_N    active-low reset
```

Equations:

```text
CLK_GATE_N = NAND4(CLK_COND, RUN, 1, 1)
CPU_CLK    = NOT(CLK_GATE_N)
CPU_CLK_N  = NOT(CPU_CLK)
```

`CPU_CLK_N` must come from `CPU_CLK`, not directly from `CLK_GATE_N`.

Use a proven RC/74HC14 debounce circuit for STEP. EXT clock must already be a
clean 5 V-compatible signal. A selector must never connect STEP and EXT outputs
together.

## U2 phase and HALT

Phase flip-flop:

```text
D=/Q  CLK=CPU_CLK  /CLR=RESET_N  /PRE=1
Q=EXEC  /Q=FETCH
```

HALT flip-flop:

```text
D=HLT_D  CLK=CPU_CLK  /CLR=RESET_N  /PRE=1
Q=HALT  /Q=RUN
```

## U1 program counter

```text
CLK=CPU_CLK
/CLR=RESET_N
/LOAD=PC_LOAD_N
ENP=FETCH
ENT=FETCH
A..D=ARG0..ARG3
QA..QD=PC0..PC3
```

It counts on FETCH and loads a jump address on a taken EXECUTE.

## U10 ROM and U3 IR

ROM:

```text
A0..A3=PC0..PC3
higher address pins=GND
/CE=0  /OE=0  /WE=1
D0..D7=ROM_D0..ROM_D7
```

IR:

```text
D0..D7=ROM_D0..ROM_D7
CLK=CPU_CLK
/E=T
Q0..Q3=ARG0..ARG3
Q4..Q7=OP0..OP3
```

Because `/E` is active low, IR loads only when `T=FETCH=0`.

## U7 opcode decoder

```text
A..D=OP0..OP3
/G1=FETCH
/G2=CPU_CLK
```

U7 is enabled only during EXECUTE while the clock is low.

```text
Y4=LI_N   Y5=LW_N   Y6=ADD_N  Y7=IN_N
Y8=SW_N   Y9=OUT_N  Y10=JZ_N  Y11=J_N  Y15=HLT_N
```

## U8/U9 AC source mux

Both chips use:

```text
S0=OP0  S1=OP1  both enables=0
```

Each AC bit receives:

```text
C0=ARG  C1=RAM_D  C2=ALU_OUT  C3=IN
```

U8 handles bits 0-1. U9 handles bits 2-3.

## U4 AC and U5 OUT

Both are 74HC161 counters used only as load/hold registers:

```text
ENP=0  ENT=0  CLK=CPU_CLK  /CLR=RESET_N
```

AC:

```text
A..D=AC_D0..AC_D3
/LOAD=AC_LOAD_N
QA..QD=AC0..AC3
```

OUT:

```text
A..D=AC0..AC3
/LOAD=OUT_N
QA..QD=OUT0..OUT3
```

Connect each OUT bit to an LED through 1k ohm.

## U6 adder

```text
A0..A3=AC0..AC3
B0..B3=RAM_D0..RAM_D3
CIN=0
S0..S3=ALU_OUT0..ALU_OUT3
COUT=NC
```

## RAM module: U11 and U16

SRAM:

```text
A0..A3=ARG0..ARG3
higher address pins=GND
D0..D3=RAM_D0..RAM_D3
D4..D7=NC
/CE=0  /OE=0  /WE=SW_N
```

Write driver:

```text
U16 inputs=AC0..AC3
U16 outputs -> 100-330 ohm -> RAM_D0..RAM_D3
all U16 /OE pins=SW_N
```

During `SW`, U16 drives AC onto RAM_D. Otherwise U16 is high impedance and SRAM
drives RAM_D.

### RAM_D bus ownership

`RAM_D0..RAM_D3` are shared physical wires:

| CPU state | SRAM data pins | U16 AC write driver | RAM_D owner |
|---|---|---|---|
| `SW_N=0` | input/write target | enabled | U16 drives AC to RAM |
| `SW_N=1` | output/read source | high-Z | SRAM drives RAM_D |
| reset or idle | output/read source | high-Z | SRAM drives RAM_D |

If U16 and SRAM both drive `RAM_D`, stop and fix control wiring.

## U13 zero and U12 branch

Zero:

```text
U13 gate 1 inputs=AC0..AC3
U13 gate 1 output=Z
U13 gate 2 inputs=GND
U13 gate 2 output=NC
```

Branch:

```text
N1=NAND(JZ_N,JZ_N)
N2=NAND(N1,Z)
N3=NAND(J_N,N2)
PC_LOAD_N=NAND(N3,N3)
```

## Inputs

IN0..IN3 need pull-up or pull-down resistors. Never leave switch inputs open.

## Before first power

Check:

- VCC and GND on every socket;
- no output connected to another output;
- all unused inputs tied;
- ROM `/WE` high;
- U16 disabled outside SW;
- correct IC orientation.
- all temporary test jumpers removed.
