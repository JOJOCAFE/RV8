# RV4-Tiny v1.3 Chip Pinouts

Always check the datasheet for the exact part you bought. This page is a quick
cross-check, not permission to wire from memory.

## Common DIP pinouts

### 74HC161

```text
1 /CLR   2 CLK    3 A      4 B
5 C      6 D      7 ENP    8 GND
9 /LOAD 10 ENT   11 QD    12 QC
13 QB   14 QA    15 RCO   16 VCC
```

### 74HC74

```text
1 /CLR1  2 D1    3 CLK1   4 /PRE1
5 Q1     6 /Q1   7 GND    8 /Q2
9 Q2    10 /PRE2 11 CLK2 12 D2
13 /CLR2 14 VCC
```

Tie both unused preset inputs high.

### 74HC377

```text
1 /E     2 Q0     3 D0     4 D1     5 Q1
6 Q2     7 D2     8 D3     9 Q3    10 GND
11 CLK  12 Q4    13 D4    14 D5    15 Q5
16 Q6   17 D6    18 D7    19 Q7    20 VCC
```

### 74HC4002

```text
1 1Y    2 1A    3 1B    4 1C    5 1D    6 NC    7 GND
8 NC    9 2A   10 2B   11 2C   12 2D   13 2Y   14 VCC
```

### 74HC125

```text
1 /1OE   2 1A   3 1Y   4 /2OE   5 2A   6 2Y   7 GND
8 3Y     9 3A  10 /3OE 11 4Y    12 4A  13 /4OE 14 VCC
```

High `/OE` means high impedance.

## Verify from the selected datasheet

Copy the actual pin table into the build notes for:

```text
74HC283
74HC154
74HC153
EEPROM
SRAM
74HC00
74HC14
74HC20
```

## Memory checklist

ROM:

- find A0..A3, D0..D7, `/CE`, `/OE`, `/WE`;
- tie all unused address inputs low;
- keep `/WE` high while installed in the CPU.

SRAM:

- find A0..A3, D0..D7, `/CE`, `/OE`, `/WE`;
- confirm outputs turn off during write;
- leave unused data outputs open;
- check write pulse and setup/hold timing.

## Before inserting an IC

1. Find pin 1 and the notch.
2. Check VCC and GND.
3. Check every unused input.
4. Check preset and clear defaults.
5. Check that no two outputs share a wire.
6. Check continuity against `02_signal_assignment.md`.

## Logic-family reminder

- 74HC uses CMOS input thresholds.
- 74HCT uses TTL-compatible input thresholds.
- Do not assume 3.3 V is a valid high for every 5 V HC input.
- Do not mix families without checking the interface.

## Datasheets

- [74HC/HCT377](https://assets.nexperia.com/documents/data-sheet/74HC_HCT377.pdf)
- [74HC/HCT4002](https://assets.nexperia.com/documents/data-sheet/74HC_HCT4002.pdf)
- [74HC/HCT125](https://assets.nexperia.com/documents/data-sheet/74HC_HCT125.pdf)
- [74HC/HCT154](https://assets.nexperia.com/documents/data-sheet/74HC_HCT154.pdf)
- [SN74HC161](https://www.ti.com/lit/ds/symlink/sn74hc161.pdf)
