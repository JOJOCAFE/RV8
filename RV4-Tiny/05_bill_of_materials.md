# RV4-Tiny v1.3 Bill of Materials

## ICs

| Ref | Part | Job |
|---|---|---|
| U1 | 74HC161 | PC |
| U2 | 74HC74 | phase/HALT |
| U3 | 74HC377 | IR |
| U4 | 74HC161 | AC |
| U5 | 74HC161 | OUT |
| U6 | 74HC283 | adder |
| U7 | 74HC154 | decoder |
| U8-U9 | 74HC153 x2 | AC mux |
| U10 | 5 V EEPROM | program ROM |
| U11 | 5 V SRAM | data RAM |
| U12 | 74HC00 | branch logic |
| U13 | 74HC4002 | zero detector |
| U14 | 74HC14 | clock/reset/inverters |
| U15 | 74HC20 | control |
| U16 | 74HC125 | RAM write driver |

```text
14 logic packages
2 memory packages
16 IC packages
```

Possible memory parts:

```text
ROM: 28C16, 28C64, AT28C256
RAM: 6116, 62256
```

Choose the exact part before wiring. Confirm 5 V operation, package, pinout,
read/write timing, and SRAM output behavior during write.

## Small parts

| Part | Quantity |
|---|---:|
| 100 nF ceramic capacitor | 16 plus spares |
| 47-100 uF capacitor | 2-3 |
| LED | 4 |
| 1k LED resistor | 4 |
| 100-330 ohm RAM series resistor | 4 |
| 10k pull resistor | at least 8 |
| push button | 2 |
| debounce RC parts | for the tested circuit |

## Build materials

- three full-size breadboards;
- sockets matching each package;
- short solid-core wires;
- 2x10 and 2x8 headers;
- STEP/EXT selector;
- labelled test points;
- regulated current-limited 5 V supply;
- multimeter and logic analyzer/oscilloscope;
- EEPROM programmer.

## Substitution rules

- HC and HCT have different input thresholds.
- A 3.3 V module may need level shifting.
- Do not replace a register with one missing load or reset behavior.
- U13 must be a true four-input NOR.
- Do not remove U16 unless RAM is changed to a part with separate input/output
  data paths.
