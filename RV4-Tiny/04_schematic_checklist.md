# RV4-Tiny v1.3 Schematic Checklist

Draw the graphical schematic in these six sheets.

## 1. Power and clock

- +5 V and GND on every IC.
- 100 nF beside every IC.
- STEP debounce and EXT selector.
- U14/U15 clock/control module.
- RESET_N to U1, U2, U4, U5.

```text
CLK_COND -> U15B -> CLK_GATE_N -> U14 -> CPU_CLK -> U14 -> CPU_CLK_N
```

## 2. Program path

```text
U1 PC -> U10 ROM -> U3 IR -> U7 decoder
```

Show:

- PC count/load controls;
- ROM high address pins tied low;
- U3 `/E=T`;
- U7 enables `FETCH` and `CPU_CLK`.

## 3. Datapath

```text
ARG/RAM/ALU/IN -> U8/U9 -> U4 AC
AC + RAM -> U6 adder
AC -> U5 OUT
```

Ground U4/U5 count enables so they only load or hold.

## 4. RAM module

```text
ARG -> U11 address
U11 D0..D3 <-> RAM_D
AC -> U16 -> resistors -> RAM_D
SW_N -> U11 /WE and all U16 /OE
```

U16 must be high impedance outside `SW`.

## 5. Zero and branch

```text
AC0..AC3 -> U13 four-input NOR -> Z
J_N, JZ_N, Z -> U12 -> PC_LOAD_N
```

Ground all inputs of unused U13 gate 2.

## 6. Headers and LEDs

- OUT LEDs use 1k resistors.
- IN switches have pull resistors.
- Mark pin 1 on both headers.
- Add student probe headers from `13_student_probe_header_plan.md`.
- Probe headers must not drive CPU signals.
- External ALU needs a jumper so it cannot fight U6.

## Edge behavior

| Edge | Result |
|---|---|
| FETCH | IR loads and PC increments |
| EXEC LI/LW/ADD/IN | AC loads |
| EXEC OUT | OUT loads |
| EXEC J/JZ taken | PC loads ARG |
| EXEC HLT | HALT sets |

`SW` writes during the low half before its EXECUTE edge.

## ERC must catch

- floating CMOS inputs;
- output-to-output connections;
- missing power pins;
- U16 enabled outside SW;
- ROM `/WE` not tied high;
- RAM D4..D7 tied to a rail;
- U2 preset pins left open.

The schematic is not approved until ERC passes and it matches
`02_signal_assignment.md`.
