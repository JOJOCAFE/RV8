# RV4-Tiny v1.3 Assembler Specification

The assembler changes readable instructions into 16 ROM bytes.

## Instructions

| Assembly | Byte |
|---|---|
| `NOP` | `00` |
| `LI n` | `4n` |
| `LW a` | `5a` |
| `ADD a` | `6a` |
| `IN` | `70` |
| `SW a` | `8a` |
| `OUT` | `90` |
| `JZ a` | `Aa` |
| `J a` | `Ba` |
| `HLT` | `F0` |

`NOP`, `IN`, `OUT`, and `HLT` take no operand. Other instructions require one.

## Source format

```asm
VALUE = expression
LABEL:
MNEMONIC operand
.RAM address, value
; comment
```

Names use letters, numbers, and `_`, but cannot start with a number.

## Numbers

```text
10       decimal ten
$A       hexadecimal ten
0xA      hexadecimal ten
0b1010   binary ten
```

Values must fit `0..15`. Silent truncation is forbidden.

## Labels

Labels name ROM addresses. The assembler must:

1. find labels and expanded instruction sizes;
2. resolve names and create bytes.

The final program must fit addresses `0..15`.

## RAM image

```asm
.RAM $E, 0
.RAM $F, 1
```

`.RAM address, value` changes the simulator or external-loader RAM image. It
does not use ROM space. Real SRAM starts with unknown data, so standalone
programs must use `LI` and `SW` to initialize values.

## Optional short forms

```asm
CLR        -> LI 0
JMP label  -> J label
```

If `INC address` is supported, it expands to:

```asm
LW address
ADD ONE
SW address
```

`ONE` must name a RAM location containing 1.

## Output files

- ROM image: 16 lines, two hex digits each; unused bytes are `F0`.
- RAM image: 16 lines, one hex digit each; unused values are `0`.
- Listing: address, byte, source line, and expanded instruction.

## Errors

Stop with a nonzero exit status for:

- unknown instruction;
- missing or extra operand;
- invalid number;
- value outside `0..15`;
- duplicate or missing name;
- duplicate RAM address;
- program longer than 16 bytes.

## Example

```asm
COUNT = $E
ONE = $F

  LI 0
  SW COUNT
  LI 1
  SW ONE

LOOP:
  LW COUNT
  ADD ONE
  SW COUNT
  OUT
  J LOOP
```

ROM:

```text
40 8E 41 8F 5E 6F 8E 90 B4 F0 F0 F0 F0 F0 F0 F0
```
