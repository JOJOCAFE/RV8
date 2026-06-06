# RV8-GR — ISA Reference

**17 instructions. Direct-encoded. 16-bit jump via Page Register. IRQ.**

---

## Encoding (2 bytes per instruction)

    Byte 0 — Control: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
    Byte 1 — Operand: immediate value, RAM address, or jump target (8-bit)

---

## Instructions

| Hex | Mnemonic | Binary | Operation |
|:---:|----------|:------:|-----------|
| $00 | NOP | 00000000 | no operation |
| $10 | ADDI imm | 00010000 | AC = AC + imm |
| $18 | ADD rs | 00011000 | AC = AC + RAM[rs] |
| $90 | SUBI imm | 10010000 | AC = AC - imm |
| $98 | SUB rs | 10011000 | AC = AC - RAM[rs] |
| $70 | XORI imm | 01110000 | AC = AC ^ imm |
| $78 | XOR rs | 01111000 | AC = AC ^ RAM[rs] |
| $30 | LI imm | 00110000 | AC = imm |
| $38 | MV a0,rs | 00111000 | AC = RAM[rs] |
| $04 | MV rd,a0 | 00000100 | RAM[rd] = AC |
| $02 | BEQ addr | 00000010 | if Z=1: PC = {PG, addr} |
| $82 | BNE addr | 10000010 | if Z=0: PC = {PG, addr} |
| $01 | J addr | 00000001 | PC = {PG, addr} |
| $20 | SETPG imm | 00100000 | PageReg = imm |
| $28 | SETPG_R rs | 00101000 | PageReg = RAM[rs] |
| $08 | EI | 00001000 | IE = 1 (enable interrupts) |
| $48 | DI | 01001000 | IE = 0 (disable interrupts) |

---

## Aliases

    LB addr   = MV a0,rs ($38)    — load byte from RAM
    SB addr   = MV rd,a0 ($04)    — store byte to RAM
    SLL a0,1  = ADD a0,a0 ($18)   — shift left (add self)
    HLT       = J self ($01)      — halt (jump to own address)

---

## Control Byte Decode

| Bit | Name | =0 | =1 |
|:---:|------|----|----|
| 7 | ALU_SUB | ADD mode | SUB mode (invert + Cin=1) |
| 6 | XOR_MODE | XOR B = ALU_SUB | XOR B = AC (for XOR instr) |
| 5 | MUX_SEL | AC ← Adder result | AC ← XOR output |
| 4 | AC_WR | AC unchanged | AC latches new value |
| 3 | SOURCE_TYPE | IBUS = IRL (immediate) | IBUS = RAM[IRL] |
| 2 | STORE | — | RAM[IRL] = AC |
| 1 | BRANCH | — | Conditional PC load (check Z) |
| 0 | JUMP | — | Unconditional PC load |

---

## Derived Signals

    ADDR_MODE = SRC OR STR          → address mux selects IRL
    PC_INC = T0 OR T1               → PC counts during fetch
    /IRL_OE = NAND(T2, /ADDR_MODE)  → IRL drives IBUS
    /AC_BUF = NAND(T2, STORE)       → AC drives IBUS + RAM write
    /PC_LD = NAND(T2, PC_LOAD_COND) → PC loads jump target
    PC_LOAD_COND = JUMP OR (BRANCH AND Z_match)
    Z_match = Z_flag XOR ALU_SUB    → BEQ: Z=1, BNE: Z=0
    PG_Load = T2 AND MUX_SEL AND NOT(AC_WR)

---

## IBUS Driver Rules

Only ONE driver active during T2:

| Condition | Driver | Signal |
|-----------|--------|--------|
| SRC=0, STR=0 | U6 (IRL immediate) | /IRL_OE=0 |
| SRC=1, STR=0 | U7 (RAM read) | BUF_OE_N=0 |
| STR=1 | U14 (AC buffer) | /AC_BUF=0 |

During T0/T1 (fetch): U7 always enabled (BUF_OE_N=0), reads ROM/RAM.

---

## Subroutine Pattern (Software)

    ; CALL sub at page P, address A:
    LI lo(return)       ; $30, ret_lo
    MV $07, a0          ; $04, $07
    SETPG P             ; $20, P
    J A                 ; $01, A

    ; RET (at end of sub, return address known at compile time):
    SETPG ret_page      ; $20, ret_pg
    J ret_lo            ; $01, ret_lo

---

## What's Missing vs RV8

| Feature | Status | Workaround |
|---------|:------:|-----------|
| AND/OR | ❌ | Software subroutine |
| SRL | ❌ | Software loop |
| JAL/JALR | ❌ | Software CALL/RET |
| Relative branch | ❌ | Absolute (assembler) |
| Interrupts | ✅ | EI/DI + fixed vector $FF00 |
