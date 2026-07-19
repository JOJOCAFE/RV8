# RV4-Tiny v1.3 Simulator Specification

The simulator is the reference for CPU state changes. It does not model switch
bounce, voltage, or chip delay.

## State

```text
PC, AC, OUT, IN: 4 bits
IR: 8 bits
T, HALT: 1 bit
ROM: 16 bytes
RAM: 16 nibbles
```

Reset:

```text
PC=0 IR=0 AC=0 OUT=0 IN=0 T=FETCH HALT=0
```

ROM and RAM keep their loaded images.

## One step

One simulator step equals one rising CPU clock edge.

FETCH:

```python
ir = rom[pc]
pc = (pc + 1) & 0xF
t = EXECUTE
```

EXECUTE:

| Opcode | State change |
|---:|---|
| `0` | no change |
| `4` | `AC=operand` |
| `5` | `AC=RAM[operand]` |
| `6` | `AC=(AC+RAM[operand]) & 0xF` |
| `7` | `AC=IN` |
| `8` | `RAM[operand]=AC` |
| `9` | `OUT=AC` |
| `A` | if AC is zero, `PC=operand` |
| `B` | `PC=operand` |
| `F` | `HALT=1` |

After a successful EXECUTE, set `T=FETCH`.

Opcodes `1`, `2`, `3`, `C`, `D`, and `E` raise `IllegalInstruction`. When that
happens, state must remain at the start of that EXECUTE step.

Hardware ignores the low nibble for NOP, IN, OUT, and HLT. The simulator does
the same; the assembler still emits only canonical bytes.

## Input checks

Loaders reject values outside their width. They must not silently mask bad
input.

After each successful step:

```text
PC,AC,OUT,IN,RAM[x] are 0..15
IR is 0..255
T and HALT are 0 or 1
ROM and RAM each contain 16 values
```

## Running

Every run needs a positive edge limit. Reaching the limit is not a successful
halt. Report these outcomes separately:

```text
halted
edge limit reached
illegal instruction
bad image/input
```

## Image files

- ROM: one hex byte per line; fill missing lines with `F0`.
- RAM: one hex nibble per line; fill missing lines with `0`.
- More than 16 entries is an error.
- Blank lines and `;` comments may be accepted.

## Trace

Use one clearly labelled format:

```text
edge transition PC IR AC OUT IN Z HALT
```

Example after an edge:

```text
000 FETCH->EXEC PC=1 IR=45 AC=0 OUT=0 IN=0 Z=1 HALT=0
```

## Required tests

- reset and FETCH/PC wrap;
- every LI value;
- every RAM address for LW and SW;
- all 256 ADD input pairs;
- IN and persistent OUT;
- J to all 16 targets;
- JZ taken and not taken;
- HLT blocks later changes;
- all reserved opcodes;
- canonical and noncanonical no-operand bytes;
- image errors and edge-limit result.

Hardware must match simulator state transitions. The simulator cannot prove
that the breadboard timing is safe.
