---
name: cpu-design
description: RV8 CPU architecture patterns. 64K address, RAM-backed registers, no microcode, direct-encoded control. Use when designing, implementing, or reviewing any RV8 variant.
---

# RV8 CPU Design

## Core Architecture

- 8-bit data, 16-bit address (64KB)
- Accumulator-based, RISC-V style mnemonics
- RAM-backed registers at $8000-$8007 (DP=$80)
- RV8-Bus: 40-pin (A[15:0] + D[7:0] + CLK + /WR + /RD + /IRQ + /SLOT)

## RV8-GR (Active Build Target)

- 34 logic + ROM + RAM = 36 packages
- No microcode — opcode byte IS the control word
- 3-cycle: T0=fetch ctrl, T1=fetch operand, T2=execute
- ROM $0000-$7FFF, RAM $8000-$FFFF (A15 chip select)
- 18 instructions, architecture frozen v1.0

## Control Encoding

```
[7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
```

| Hex | Mnemonic | Bits | Operation |
|-----|----------|------|-----------|
| $00 | NOP | 00000000 | — |
| $10 | ADDI | 00010000 | AC += imm |
| $18 | ADD | 00011000 | AC += RAM[rs] |
| $90 | SUBI | 10010000 | AC -= imm |
| $98 | SUB | 10011000 | AC -= RAM[rs] |
| $70 | XORI | 01110000 | AC ^= imm |
| $78 | XOR | 01111000 | AC ^= RAM[rs] |
| $30 | LI | 00110000 | AC = imm |
| $38 | MV a0,rs | 00111000 | AC = RAM[rs] |
| $04 | MV rd,a0 | 00000100 | RAM[rd] = AC |
| $02 | BEQ | 00000010 | if Z: PC={PG,addr} |
| $82 | BNE | 10000010 | if !Z: PC={PG,addr} |
| $01 | J | 00000001 | PC={PG,addr} |
| $20 | SETPG | 00100000 | PG = imm |
| $28 | SETPG_R | 00101000 | PG = RAM[rs] |
| $40 | SETDP | 01000000 | DP = imm |
| $08 | EI | 00001000 | IE=1 |
| $48 | DI | 01001000 | inert marker in v1.0; IE clears only on reset |

## ALU Pattern (XOR sharing)

```verilog
wire [7:0] xor_b   = xor_mode ? ac : {8{alu_sub}};
wire [7:0] xor_out = ibus ^ xor_b;
wire [8:0] adder   = {1'b0, ac} + {1'b0, xor_out} + {8'b0, alu_sub};
wire [7:0] ac_mux  = mux_sel ? xor_out : adder[7:0];
```

- SUB: xor_b=$FF → two's complement
- XOR: xor_b=AC → XOR result
- LI/MV: xor_b=$00 → pass-through, adder gives AC+imm with no carry

## Critical Hazards

1. **Bus ownership**: IBUS drivers are U34 immediate, U7 memory bridge, and U14 AC buffer; only one may drive at a time.
2. **SRC+STR mixed opcodes**: reserved but electrically safe in the current 36-package design. STR dominates; U14 drives IBUS, U7 writes IBUS→DBUS, ROM `/OE=WR_DIR` disables ROM output.
3. **ROM write boundary**: CPU runtime keeps ROM `/WE` inactive. Programmer may drive ROM `/WE` only in PROG/reset isolation.
4. **Z-flag async preset**: U22→U21 `/PR` sets Z=1 when AC becomes zero; Z has T0/T1 of the next instruction to settle before BEQ/BNE uses it at T2.
5. **IRQ v1.0**: polling latch only. `/IRQ` release/rising edge sets `IRQ_FF`; no hardware vector, no PC save, DI inert.

## Key Chip Roles

| Function | Chips |
|----------|-------|
| PC (16-bit) | U1-U4 (74HC161 ×4) |
| IR (ctrl+operand) | U5, U6 (74HC574) |
| Bus buffer | U7 (74HC245) |
| T-state ring | U8 (74HC164) |
| Accumulator | U9 (74HC574) |
| ALU adder | U10-U11 (74HC283 ×2) |
| ALU XOR | U12-U13 (74HC86 ×2) |
| AC output buf | U14 (74HC541) |
| Addr mux low | U15-U16 (74HC157 ×2) |
| AC input mux | U17-U18 (74HC157 ×2) |
| XOR B mux | U19-U20 (74HC157 ×2) |
| Z-flag | U21 (74HC74) + U22 (74HC688) |
| Page register | U23 (74HC574) |
| Inverters | U24 (74HC04) |
| OR/NAND glue | U25 (74HC32), U26-U27 (74HC00) |
| Misc XOR | U28 (74HC86) |
| Addr mux high | U29-U30 (74HC157 ×2) |
| IRQ + IE | U31 (74HC74) |
| Data page reg | U32 (74HC574) |
| Decode AND | U33 (74HC21) |

## IRQ

- U31-A=IE_FF, U31-B=IRQ_FF
- Trigger: `/IRQ` release/rising edge → IRQ_FF=1
- v1.0: polling only. No automatic PC vector, no PC save, no bus override.
- EI sets IE. DI is an inert software marker in the 36-package build.
- IE and IRQ_FF clear by `/RST`; an external `/SLOT` status device may expose IRQ_FF to software.

## Design Rules

- Chip budget: 34 logic (frozen). Adding a chip needs strong justification.
- All 256 opcodes produce deterministic behavior (horizontal control).
- Gate budget: U28 gates are used for `Z_match`, `/T2`, `WR_DIR`, and `/XOR_MODE`; U25 gate 3 is spare in the current wiring.
- Memory: ROM (AT28C256-70), RAM (62256-70 or CY7C199-15PC).
- Clock: 1 MHz breadboard, 4-5 MHz PCB.
- Four-model equivalence signoff uses `RV8GR/tools/check_python_verilog_equivalence.py`, which compares CPUSim, ComponentsCPUSim, behavioral Verilog, and TTL-chip Verilog over 55 checkpoints.
