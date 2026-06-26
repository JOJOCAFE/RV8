# RV8-R — ISA Encoding (2-byte format)

**Same 2-byte RV8-style encoding shape. RV8-R defines hardware, macro, and system subcode levels explicitly.**

---

## Instruction Format (16-bit = 2 bytes)

```
Byte 0 (opcode):  [7:6] class  [5:3] op  [2:0] rd/rs1
Byte 1 (operand): [7:5] rs2    [4:0] imm5
                  — OR —
                  [7:0] imm8 (for immediate/branch classes)
```

### Microcode ROM uses:
- **opcode byte** → microcode address A[7:0]
- **operand byte** → OPR register (available for step sequencing)
- **rd** = opcode[2:0] → register address for read/write destination
- **rs** = operand[7:5] → register address for source

---

## Class 00: ALU Register-Register

```
Byte 0: [00][op:3][rd:3]
Byte 1: [rs:3][00000]
```

| Opcode | op | Mnemonic | Operation |
|:------:|:--:|----------|-----------|
| $00+rd | 000 | ADD rd, rs | rd ← rd + rs |
| $08+rd | 001 | SUB rd, rs | rd ← rd - rs |
| $10+rd | 010 | AND rd, rs | rd ← rd & rs |
| $18+rd | 011 | OR rd, rs | rd ← rd \| rs |
| $20+rd | 100 | XOR rd, rs | rd ← rd ^ rs |
| $28+rd | 101 | SLT rd, rs | rd ← (rd < rs) ? 1 : 0 |
| $30+rd | 110 | SLL rd | rd ← rd << 1 |
| $38+rd | 111 | SRL rd | rd ← rd >> 1 |

**Notes:**
- SLL: microcode does ADD rd, rd (shift left = add to self)
- SRL: microcode multi-step through carry (slow, ~10 cycles)
- rs field in operand byte ignored for SLL/SRL

---

## Class 01: ALU Immediate

```
Byte 0: [01][op:3][rd:3]
Byte 1: [imm8:8]
```

| Opcode | op | Mnemonic | Operation |
|:------:|:--:|----------|-----------|
| $40+rd | 000 | LI rd, imm | rd ← imm |
| $48+rd | 001 | ADDI rd, imm | rd ← rd + imm |
| $50+rd | 010 | SUBI rd, imm | rd ← rd - imm |
| $58+rd | 011 | ANDI rd, imm | rd ← rd & imm |
| $60+rd | 100 | ORI rd, imm | rd ← rd \| imm |
| $68+rd | 101 | XORI rd, imm | rd ← rd ^ imm |
| $70+rd | 110 | SLTI rd, imm | rd ← (rd < imm) ? 1 : 0 |
| $78+rd | 111 | LUI rd, imm | rd ← imm << 4 |

---

## Class 10: Load/Store

```
Byte 0: [10][op:3][rd:3]
Byte 1: [rs:3][off5:5]    (signed offset, -16..+15)
    OR: [imm8:8]           (fast-page / stack variants)
```

| Opcode | op | Mnemonic | Operation |
|:------:|:--:|----------|-----------|
| $80+rd | 000 | LB rd, off(rs) | rd ← mem[rs + sext(off5)] |
| $88+rd | 001 | SB rd, off(rs) | mem[rs + sext(off5)] ← rd |
| $90+rd | 010 | LB rd, addr | rd ← mem[{$FF, imm8}] |
| $98+rd | 011 | SB rd, addr | mem[{$FF, imm8}] ← rd |
| $A0+rd | 100 | PUSH rd | sp--, mem[sp] ← rd |
| $A8+rd | 101 | POP rd | rd ← mem[sp], sp++ |
| $B0+rd | 110 | LB rd, off(sp) | rd ← mem[sp + off5] |
| $B8+rd | 111 | SB rd, off(sp) | mem[sp + off5] ← rd |

**Notes:**
- Fast page (`$FF00-$FFFF`) for quick RAM variables. `$FFF6-$FFFF` is reserved for IRQ save slots and registers.
- Stack-relative for local variables (function frames)
- PUSH/POP: sp = r7, auto decrement/increment

---

## Class 11: Branch/Jump

```
Branch: Byte 0: [11][op:3][rs1:3]
        Byte 1: [rs2:3][off5:5]    (signed, -16..+15)

Jump:   Byte 0: [11][op:3][rd:3]
        Byte 1: [off8:8]           (signed, -128..+127)
```

| Opcode | op | Mnemonic | Operation |
|:------:|:--:|----------|-----------|
| $C0+rs1 | 000 | BEQ rs1, rs2, off | if rs1==rs2: PC += sext(off5) |
| $C8+rs1 | 001 | BNE rs1, rs2, off | if rs1≠rs2: PC += sext(off5) |
| $D0+rs1 | 010 | BLT rs1, rs2, off | if rs1<rs2 (unsigned): PC += sext(off5) |
| $D8+rs1 | 011 | BGE rs1, rs2, off | if rs1≥rs2 (unsigned): PC += sext(off5) |
| $E0+rd | 100 | JAL rd, off8 | rd ← PC, PC += sext(off8) |
| $E8+rd | 101 | JALR rd, rs | rd ← PC, PC ← rs |
| $F0+xx | 110 | J off8 | PC += sext(off8) |
| $F8+xx | 111 | SYS imm | NOP/HLT/EI/DI/IRET (sub-decoded) |

**Notes:**
- Branch compares two registers directly (RISC-V style, no flags visible to programmer)
- JAL: saves PC_LO to rd (same-page return), jumps relative ±128
- JALR: saves PC_LO to rd, jumps to absolute address in rs (full 16-bit via page reg)
- J: unconditional relative jump (= JAL r0, off8)
- SYS: operand byte selects sub-function (`0=NOP`, `1=HLT`, `2=EI`, `3=DI`, `4=IRET`)

---

## Opcode Map (hex, first byte)

```
       rd=0  rd=1  rd=2  rd=3  rd=4  rd=5  rd=6  rd=7
      ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
00-07 │ ADD │ ADD │ ADD │ ADD │ ADD │ ADD │ ADD │ ADD │ Class 00
08-0F │ SUB │ SUB │ SUB │ SUB │ SUB │ SUB │ SUB │ SUB │
10-17 │ AND │ AND │ AND │ AND │ AND │ AND │ AND │ AND │
18-1F │ OR  │ OR  │ OR  │ OR  │ OR  │ OR  │ OR  │ OR  │
20-27 │ XOR │ XOR │ XOR │ XOR │ XOR │ XOR │ XOR │ XOR │
28-2F │ SLT │ SLT │ SLT │ SLT │ SLT │ SLT │ SLT │ SLT │
30-37 │ SLL │ SLL │ SLL │ SLL │ SLL │ SLL │ SLL │ SLL │
38-3F │ SRL │ SRL │ SRL │ SRL │ SRL │ SRL │ SRL │ SRL │
      ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
40-47 │ LI  │ LI  │ LI  │ LI  │ LI  │ LI  │ LI  │ LI  │ Class 01
48-4F │ADDI │ADDI │ADDI │ADDI │ADDI │ADDI │ADDI │ADDI │
50-57 │SUBI │SUBI │SUBI │SUBI │SUBI │SUBI │SUBI │SUBI │
58-5F │ANDI │ANDI │ANDI │ANDI │ANDI │ANDI │ANDI │ANDI │
60-67 │ ORI │ ORI │ ORI │ ORI │ ORI │ ORI │ ORI │ ORI │
68-6F │XORI │XORI │XORI │XORI │XORI │XORI │XORI │XORI │
70-77 │SLTI │SLTI │SLTI │SLTI │SLTI │SLTI │SLTI │SLTI │
78-7F │ LUI │ LUI │ LUI │ LUI │ LUI │ LUI │ LUI │ LUI │
      ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
80-87 │ LB  │ LB  │ LB  │ LB  │ LB  │ LB  │ LB  │ LB  │ Class 10
88-8F │ SB  │ SB  │ SB  │ SB  │ SB  │ SB  │ SB  │ SB  │
90-97 │LBfp │LBfp │LBfp │LBfp │LBfp │LBfp │LBfp │LBfp │
98-9F │SBfp │SBfp │SBfp │SBfp │SBfp │SBfp │SBfp │SBfp │
A0-A7 │PUSH │PUSH │PUSH │PUSH │PUSH │PUSH │PUSH │PUSH │
A8-AF │ POP │ POP │ POP │ POP │ POP │ POP │ POP │ POP │
B0-B7 │LBsp │LBsp │LBsp │LBsp │LBsp │LBsp │LBsp │LBsp │
B8-BF │SBsp │SBsp │SBsp │SBsp │SBsp │SBsp │SBsp │SBsp │
      ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
C0-C7 │ BEQ │ BEQ │ BEQ │ BEQ │ BEQ │ BEQ │ BEQ │ BEQ │ Class 11
C8-CF │ BNE │ BNE │ BNE │ BNE │ BNE │ BNE │ BNE │ BNE │
D0-D7 │ BLT │ BLT │ BLT │ BLT │ BLT │ BLT │ BLT │ BLT │
D8-DF │ BGE │ BGE │ BGE │ BGE │ BGE │ BGE │ BGE │ BGE │
E0-E7 │ JAL │ JAL │ JAL │ JAL │ JAL │ JAL │ JAL │ JAL │
E8-EF │JALR │JALR │JALR │JALR │JALR │JALR │JALR │JALR │
F0-F7 │  J  │  J  │  J  │  J  │  J  │  J  │  J  │  J  │
F8-FF │ SYS │ SYS │ SYS │ SYS │ SYS │ SYS │ SYS │ SYS │
      └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

---

## Encoding Examples

```
ADD r2, r3      → $02 $60    (class=00, op=000, rd=010, rs=011, imm5=00000)
ADDI r4, 42     → $4C $2A    (class=01, op=001, rd=100, imm8=$2A)
LI r1, $FF      → $41 $FF    (class=01, op=000, rd=001, imm8=$FF)
LB r2, 3(r5)   → $82 $A3    (class=10, op=000, rd=010, rs=101, off5=00011)
SB r3, -1(r7)  → $8B $FF    (class=10, op=001, rd=011, rs=111, off5=11111)
BEQ r2, r3, 4  → $C2 $64    (class=11, op=000, rs1=010, rs2=011, off5=00100)
JAL r1, 10     → $E1 $0A    (class=11, op=100, rd=001, off8=$0A)
J -5           → $F0 $FB    (class=11, op=110, rd=000, off8=$FB = -5)
PUSH r2        → $A2 $00    (class=10, op=100, rd=010, operand unused)
POP r4         → $AC $00    (class=10, op=101, rd=100, operand unused)
SYS 1 (HLT)   → $F8 $01    (class=11, op=111, rd=000, imm8=01)
SYS 2 (EI)    → $F8 $02    (enable interrupts)
SYS 3 (DI)    → $F8 $03    (disable interrupts)
SYS 4 (IRET)  → $F8 $04    (return from interrupt)
```

---

## Microcode Implications

The encoding maps directly to microcode ROM addressing:

1. **opcode[7:6] (class)** tells microcode the general step pattern
2. **opcode[5:3] (op)** selects ALU operation or memory mode
3. **opcode[2:0] (rd)** feeds register-address mode: `A[15:3]=1`, `A[2:0]=rd`, so `rd` maps to `$FFF8-$FFFF`
4. **operand[7:5] (rs)** feeds the same register-address path for source register access
5. **operand[4:0] or [7:0]** stays in OPR register for immediate/offset use

The microcode ROM sees the **full 8-bit opcode** so each of the 256 possible opcodes gets its own step sequence. This means:
- No instruction decoder chip needed
- Each opcode variant (e.g., ADD r0 vs ADD r7) shares the same microcode (rd routing is automatic from opcode[2:0])
- Unused opcodes can be filled with NOP microcode or future extensions

---

## Pseudo-instructions (assembler macros)

| Pseudo | Expansion | Encoding |
|--------|-----------|----------|
| NOP | SYS 0 | $F8 $00 |
| HLT | SYS 1 | $F8 $01 |
| MOV rd, rs | ADD rd, rs (with rd=0 first? No — ADD rd,rs adds) | OR rd, rs (if rd=0 first) |
| CLR rd | LI rd, 0 | $40+rd $00 |
| INC rd | ADDI rd, 1 | $48+rd $01 |
| DEC rd | SUBI rd, 1 | $50+rd $01 |
| NOT rd | XORI rd, $FF | $68+rd $FF |
| NEG rd | SUBI rd, 0... | (SUB r0, rd → needs temp) |
| CALL off8 | JAL r1, off8 | $E1 off8 |
| RET | JALR r1, r1 | $E9 $20 (rd=r1, rs=r1) |
| EI | SYS 2 | $F8 $02 |
| DI | SYS 3 | $F8 $03 |
| IRET | SYS 4 | $F8 $04 |

**MOV rd, rs** needs care: there's no dedicated MOV. Options:
- `ADD rd, rs` only works if rd=0 first → 2 instructions: `LI rd,0` + `ADD rd,rs`
- Better: `OR rd, rs` with rd=0 first → same issue
- Best: add MOV as alias for a specific microcode (e.g., op=110 in class 00 could be MOV instead of SLL for non-shift case)

Actually looking at the encoding: **SLL and SRL ignore the rs field**. So for class 00, ops 110 and 111, the rs field is free. We could repurpose them:
- SLL rd: opcode=$30+rd, operand=$00 (rs=000, unused)
- SRL rd: opcode=$38+rd, operand=$00

But `$30+rd` with rs≠0 is technically a different opcode in microcode... we could make `$30+rd` with rs=000 mean SLL, and with rs≠0 mean something else. But that's fragile.

**Keep it simple**: MOV = `LI rd, 0` + `ADD rd, rs` (2 instructions, 9 cycles). Or the assembler emits `XOR rd, rd` + `OR rd, rs`. Good enough.

---

*Document version: 2026-06-14*
*RV8-style binary format with RV8-R-specific hardware and system behavior*
