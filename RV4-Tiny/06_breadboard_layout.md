# RV4-Tiny v1.3 Breadboard Layout

Use three full-size boards. Check whether their power rails are split.

## Board A — control

```text
front/test edge
U14 U15   U2 U12
U1  U3    U7 U13
back/inter-board edge
```

Keep clock, reset, phase, and PC_LOAD_N wires short. Put test points beside
U14/U15.

## Board B — datapath

```text
U8 U9
U4 U6
U5
```

Keep AC, mux, and adder close. Route every four-bit group in the same bit order.

## Board C — memory and I/O

```text
U10 ROM   U11 RAM   U16 write driver
buttons   selectors
LEDs      IN switches
headers
```

Place U16 and its four resistors beside SRAM.

## Wiring rules

- Use several ground links between boards.
- Put each 100 nF capacitor beside its IC.
- Keep clock wires away from LED and RAM data bundles.
- Use consistent wire colors for clock, control, address, and data.
- Mark header pin 1.
- Do not place permanent LEDs on internal signals without checking fan-out.
- Put student probe headers along the front/test edge where possible.
- Use `13_student_probe_header_plan.md` for header grouping.

RAM data path:

```text
AC -> U16 -> resistor -> RAM_D <-> SRAM
RAM_D -> mux and adder
```

OUT LED:

```text
OUT -> 1k -> LED -> GND
```

## Assembly order

Follow `07_build_plan.md`, not board order:

```text
power -> clock/control -> phase -> PC -> ROM/IR -> decoder
-> AC/OUT -> RAM -> adder -> branch -> headers
```

Photograph and label each passing stage before adding more wires.
