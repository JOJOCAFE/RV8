# RV4-Tiny v1.3 Architecture

This document explains what the CPU does. It does not list physical pin
numbers.

## The big idea

A CPU repeats two jobs:

```text
FETCH:   read the next instruction
EXECUTE: do that instruction
```

RV4-Tiny changes phase on each rising edge of `CPU_CLK`.

```text
RESET -> FETCH -> EXECUTE -> FETCH -> EXECUTE ...
```

All state-holding devices use the same rising-edge `CPU_CLK`. Derived register
clocks are not allowed.

Useful words:

- **bit**: one binary digit, 0 or 1;
- **4-bit number**: four bits, from 0 to 15;
- **ROM**: memory that stores the program;
- **RAM**: memory that stores changing data;
- **register**: a small storage place inside the CPU;
- **clock edge**: the moment when CPU state changes.

## Main blocks

```text
PC -> ROM -> IR -> decoder/control
              |
              +-> operand -> RAM address / immediate / jump target

RAM + AC -> adder -> AC
IN -------------> AC
AC -------------> OUT LEDs
AC -> write buffer -> RAM
```

Student modules:

1. clock/control support: U14 and U15;
2. phase and HALT: U2;
3. program flow: U1 and U10;
4. instruction and decode: U3 and U7;
5. accumulator and output: U4, U5, U8, U9;
6. adder: U6;
7. RAM: U11 and U16;
8. zero and branch: U13 and U12.

## Numbers and memory

| Item | Size |
|---|---:|
| Data number | 4 bits: `0..15` |
| Address | 4 bits: `0..15` |
| Instruction | 8 bits |
| Program ROM | 16 instructions |
| Data RAM | 16 four-bit values |

Four-bit addition wraps around:

```text
14 + 3 = 17 -> 1
```

The CPU has no carry or overflow flag.

## Registers

| Name | Job |
|---|---|
| PC | points to the next ROM instruction |
| IR | holds the current instruction |
| AC | holds the working number |
| OUT | remembers the number shown on LEDs |
| T | selects FETCH or EXECUTE |
| HALT | blocks future clock pulses |

Reset gives:

```text
PC=0  AC=0  OUT=0  T=FETCH  HALT=0
```

IR does not need reset because the first FETCH replaces it.

## Instruction format

```text
bits 7..4 = opcode
bits 3..0 = operand
```

| Code | Instruction | Meaning |
|---:|---|---|
| `0` | `NOP` | do nothing |
| `4n` | `LI n` | `AC = n` |
| `5a` | `LW a` | `AC = RAM[a]` |
| `6a` | `ADD a` | `AC = AC + RAM[a]` |
| `70` | `IN` | `AC = input switches` |
| `8a` | `SW a` | `RAM[a] = AC` |
| `90` | `OUT` | `OUT = AC` |
| `Aa` | `JZ a` | jump if AC is zero |
| `Ba` | `J a` | always jump |
| `F0` | `HLT` | stop the CPU |

Codes `1`, `2`, `3`, `C`, `D`, and `E` are reserved.

## What happens on clock edges

FETCH edge:

```text
IR <- ROM[PC]
PC <- PC + 1
T  <- EXECUTE
```

EXECUTE edge:

```text
LI/LW/ADD/IN -> load AC
OUT          -> load OUT
J/JZ         -> load PC when the jump is taken
HLT          -> set HALT
T            -> FETCH
```

`SW` writes asynchronous SRAM during the low half of EXECUTE. The write ends at
the EXECUTE rising edge.

## AC input choices

Opcodes 4 to 7 use their two low opcode bits to select AC data:

| Instruction | Select | AC input |
|---|---:|---|
| LI | `00` | instruction operand |
| LW | `01` | RAM |
| ADD | `10` | adder |
| IN | `11` | input switches |

## Zero and branch

U13 detects zero directly:

```text
Z = NOR(AC0, AC1, AC2, AC3)
```

`Z=1` only when AC is `0000`. `JZ` uses this live signal; there is no zero
register.

## RAM bus ownership

RAM uses the same four wires for reading and writing:

```text
read:  SRAM -> RAM_D
write: AC -> U16 -> RAM_D -> SRAM
```

U16 is enabled only for `SW`. At all other times it is high impedance, so SRAM
can drive reads safely.

SRAM power-on data is unknown. A standalone program must initialize every RAM
location it uses.

## Physical limits

The practical build uses:

```text
14 logic packages
2 memory packages
16 IC packages total
```

Every CMOS input must have a defined level. Every IC needs a nearby 100 nF
bypass capacitor. Exact pins must be checked against the purchased part's
datasheet.
