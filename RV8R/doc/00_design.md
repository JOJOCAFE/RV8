# RV8-R Architecture Design Document

## Overview

RV8-R is a minimal 8-bit RISC-V style CPU built from 18 logic chips plus 2 ROM and 1 RAM package (21 total). It features a single-bus architecture with hardware registers backed by RAM, a microcode ROM for instruction sequencing, and execute-from-RAM capability.

**Target**: Middle school students (Thai language documentation available)  
**Clock**: 5 MHz  
**Performance**: ~0.91 MIPS (5.5 avg cycles/instruction)  
**ISA**: Full 35-instruction RISC-V style (SRL via software macro)

---

## Specs

| Feature | Value |
|:--------|:------|
| Logic chips | 19 (74HC series) |
| ROM packages | 2 (AT28C256-70 each) |
| RAM packages | 1 (CY7C199 or 62256) |
| Total packages | 22 |
| Register file | 8 × 8-bit (RAM-backed) |
| Address space | 64 KB |
| Microcode | 8-bit group-encoded, 13-bit address |
| Flags | Z (zero), C (carry/borrow) |
| Execute from | RAM ($0000-$7FFF) and ROM ($8000-$FFFF) |

---

## Control Word Encoding (8 bits)

```
[7:6] GROUP
[5:0] ACTION within group
```

### GROUP 00: BUS/MEMORY

| Bits [5:3] | Source | Bits [2:0] | Flags |
|:----------|:-------|:----------|:------|
| 000 | MEM[PC] → IR | [2] PC_INC |
| 001 | MEM[PC] → OPR | [1] end |
| 010 | MEM[rd] → REG_A | [0] save_flags |
| 011 | MEM[rs] → REG_B | |
| 100 | MEM[addr] → REG_A | |
| 101 | OPR → REG_B | |
| 110 | OPR → REG_A | |
| 111 | ZERO → REG_B | |

### GROUP 01: ALU + WRITEBACK

| Bits [5:3] | ALU Op | Bits [2:0] | Destination |
|:----------|:-------|:----------|:------------|
| 000 | A + B | 000 → rd |
| 001 | A - B | 001 → rs |
| 010 | A ^ B | 010 → ADDR_LO |
| 011 | A & B | 011 → ADDR_HI |
| 100 | A \| B | 100 → rd + end |
| 101 | pass A | 101 → rd + flags |
| 110 | pass B | 110 → rd + flags + end |
| 111 | NOT A | 111 → MEM[addr] |

### GROUP 10: BRANCH/JUMP

| Bits [5:4] | Condition | Bits [3:0] | Type |
|:----------|:----------|:----------|:-----|
| 00 | always | 0000 PC += sext(OPR) |
| 01 | Z | 0001 PC = ADDR |
| 10 | NZ | 0010 PC_HI → REG_A |
| 11 | C | 0011 PC_LO → REG_A |
| | | 0100 end |
| | | 0101-1111 reserved |

### GROUP 11: SPECIAL

| Action | Description |
|:-------|:------------|
| 000000 | NOP |
| 000001 | HLT |
| 000010 | END (step reset) |

---

## Microcode ROM Address (13 bits)

```
A[12]   = flag_C
A[11]   = flag_Z
A[10:8] = step counter (0-7)
A[7:0]  = opcode (from IR)
```

- **Total entries**: 8192 (2^13)
- **ROM**: AT28C256 (32 KB) — fits with address space to spare
- **Conditional branching**: Flags in address enable free conditional paths

---

## Memory Map

| Range | Description |
|:------|:------------|
| $0000-$0007 | Registers r0-r7 (in RAM) |
| $0008-$00FF | Stack (sp=r7 starts at $FF) |
| $0100-$3FFF | Data / arrays / video buffer |
| $4000-$7FFF | RAM program (execute from RAM) |
| $8000-$FFFF | ROM program (BASIC, boot) |

**Address routing**:
- Steps 0-1 (fetch): PC drives address bus (hardwired from step counter)
- Steps 2+: Register address (A[15:3]=0, A[2:0] from IR[2:0] or OPR[7:5]) or memory address (from ADDR_HI/ADDR_LO latches)

**Address mux**: 2 × 74HC157  
**ADDR_SEL** (bit 7 of control word): 0=rd from IR[2:0], 1=rs from OPR[7:5]

---

## Chip List

| Part | Qty | Function |
|:-----|:---:|:---------|
| 74HC161 | 5 | U1-U4: PC (16-bit), U5: step counter (3-bit) |
| 74HC574 | 5 | U6: IR, U7: OPR, U8: REG_A, U9: REG_B, U10: ADDR_LO |
| 74HC283 | 2 | U11-U12: ALU adder (8-bit) |
| 74HC86 | 1 | U13: XOR for SUB/XOR mode |
| 74HC157 | 2 | U14-U15: Address mux (PC vs reg vs mem) |
| 74HC245 | 1 | U16: Bus buffer (external data) |
| 74HC139 | 1 | U17: Control word group decoder |
| 74HC74 | 2 | U18: Flags (Z, C), U22: IRQ (IE + IRQ_FF) |
| **Logic** | **19** | |
| AT28C256 | 2 | U19: Microcode ROM, U20: Program ROM |
| CY7C199 | 1 | U21: RAM (32 KB) |
| **Total** | **22** | |

---

## Datapath Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    RV8-R (18 logic chips)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────┐    ┌────────┐    ┌────────────┐            │
│  │Microcode│    │Program │    │    RAM      │            │
│  │  ROM   │    │  ROM   │    │ (regs+data) │            │
│  │AT28C256│    │AT28C256│    │  CY7C199    │            │
│  └───┬────┘    └───┬────┘    └──────┬──────┘            │
│      │ctrl[7:0]    │data           │data                │
│      ▼             ▼               ▼                    │
│  ┌──────┐     ┌─────────────────────────┐              │
│  │DECODE│     │        IBUS (8-bit)      │              │
│  │HC139 │     └──┬──────┬──────┬────┬───┘              │
│  └──────┘        │      │      │    │                   │
│           ┌──────┴┐ ┌───┴──┐ ┌─┴──┐ ┌┴────┐           │
│           │ REG_A │ │REG_B │ │ IR │ │ OPR │           │
│           │ (574) │ │(574) │ │574 │ │ 574 │           │
│           └───┬───┘ └──┬──┘ └────┘ └─────┘           │
│               │         │                               │
│               ▼         ▼                               │
│           ┌─────────────────┐                           │
│           │   ALU (283×2+86)│                           │
│           │   A op B → R    │                           │
│           └────────┬────────┘                           │
│                    │result → IBUS                        │
│                    ▼                                     │
│  ┌────────────────────────────────┐                     │
│  │  PC (161×4) ←→ ADDR MUX (157×2)│                    │
│  │  Step(161)  → MCU ROM addr      │                    │
│  │  Flags(74)  → MCU ROM addr      │                    │
│  └─────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

---

## Cycle Counts

| Instruction | Cycles |
|:------------|-------:|
| J off8 | 3 |
| LI rd, imm | 4 |
| RET | 4 |
| ADDI/SUBI/XORI/ANDI/ORI rd, imm | 5 |
| ADD/SUB/XOR/AND/OR rd, rs | 5 |
| SLL rd | 5 |
| JAL rd, off8 | 5 |
| LB rd, addr (zero-page) | 6 |
| SB rd, addr (zero-page) | 6 |
| BEQ/BNE/BLT/BGE rs1,rs2,off | 6 |
| SLT rd, rs | 7 |
| LB rd, off(rs) | 8 |
| SB rd, off(rs) | 8 |
| PUSH rd | 9 |
| POP rd | 9 |
| SRL rd | Dropped (software macro) |

**Average**: 5.5 cycles → **0.91 MIPS @ 5 MHz**

---

## Key Design Decisions

1. **8-bit group-encoded control word** — Single ROM, needs 1 decoder chip (HC139). Tradeoff: fewer chips, more decode logic per instruction.

2. **2× register cache (REG_A, REG_B)** — Makes reg-reg operations same speed as immediate (5 cycles). Avoids extra memory cycle.

3. **Flags in microcode address** — Free conditional branching. No SKIP logic needed. Z and C flags directly select microcode path.

4. **SRL dropped** — Software macro. Saves complexity (no barrel shifter). SRL implemented via software loop.

5. **JAL same-page only (±128 bytes)** — Cross-page via CALL/RET macros pushing 16-bit PC. Reduces microcode complexity.

6. **r0 protection** — AND gate masks WR when addr[2:0]=000 (from spare gate). Prevents accidental writes to r0.

7. **Execute from RAM** — Free capability. PC can point anywhere in 64KB. A15 selects ROM vs RAM (A15=0 → RAM, A15=1 → ROM).

---

## ISA

Same as RV8 (35 instructions, RISC-V style encoding). Only change: **SRL dropped from hardware** (34 instructions in hardware, SRL via software macro).

**Instruction classes**:
- **ALU immediate** (8): LI, ADDI, SUBI, ANDI, ORI, XORI, CMPI, LUI
- **ALU register** (8): ADD, SUB, AND, OR, XOR, CMP, SLL, SLT
- **Memory** (8): LB, SB (x2 variants), PUSH, POP, LW, SW
- **Control** (8): BEQ, BNE, BCS, BCC, BRA, JAL, JMP, SYS
- **Special** (3): NOP, HLT, EI/DI (reserved)

**Encoding format**:
- Opcode byte: [7:6]=iclass, [5:3]=op, [2:0]=rd
- Operand byte: [7:5]=rs, [4:0]=off5/imm

See RV8/doc/01_isa_reference.md for full instruction set.

---

## Performance Comparison

| System | CPU | Clock | MIPS | BASIC lines/sec |
|:-------|:----|:------|:-----|:----------------|
| Apple II | 6502 | 1 MHz | ~0.3 | ~300 |
| MSX2 | Z80 | 3.58 MHz | ~0.5 | ~500 |
| RV8-R | 8-bit | 5 MHz | 0.91 | ~260 |

RV8-R trades throughput for simplicity. BASIC slower than MSX2 due to interpreted interpreter overhead.

---

## Microcode Step Sequences

### ADDI rd, imm (5 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | OPR → REG_B |
| 3 | MEM[rd] → REG_A |
| 4 | ALU(A+B) → MEM[rd], END |

### ADD rd, rs (5 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[rs] → REG_B |
| 3 | MEM[rd] → REG_A |
| 4 | ALU(A+B) → MEM[rd], END |

### BEQ rs1, rs2, off (6 cycles)

| Step | Action | Flag condition |
|:-----|:-------|:---------------|
| 0 | MEM[PC] → IR, PC++ | — |
| 1 | MEM[PC] → OPR, PC++ | — |
| 2 | MEM[rs1] → REG_A (rd from IR[2:0]) | — |
| 3 | MEM[rs2] → REG_B (rs from OPR[7:5]) | — |
| 4 | ALU(A-B), save flags | — |
| 5 | [Z=1] PC += sext(OPR[4:0]), END | Z=1 |
| 5 | END (no branch) | Z=0 |

### LB rd, off(rs) (8 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[rs] → REG_A |
| 3 | OPR → REG_B (offset, sign-extended) |
| 4 | ALU(A+B) → ADDR_LO |
| 5 | ZERO → ADDR_HI |
| 6 | MEM[addr] → REG_A |
| 7 | ALU(passA) → MEM[rd], END |

### PUSH rd (9 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[sp] → REG_A (read SP) |
| 3 | load const 1 → REG_B |
| 4 | ALU(A-B) → MEM[sp] (SP--) |
| 5 | ALU(A-B) → ADDR_LO (new SP = address) |
| 6 | ZERO → ADDR_HI |
| 7 | MEM[rd] → REG_A (value to push) |
| 8 | ALU(passA) → MEM[addr], END |

---

## IRQ Design

### Hardware: U22 (74HC74) — 2 flip-flops

```
U22-A: IE_FF (Interrupt Enable)
  CLK ← EI microcode decode
  /CLR ← DI decode OR IRQ-ack OR /RST
  Q → IE

U22-B: IRQ_FF (Interrupt Pending)  
  CLK ← /IRQ pin (falling edge)
  /CLR ← IRQ-ack OR /RST
  Q → IRQ_PENDING
```

### Microcode ROM address (14 bits)

```
A[13]   = /IRQ_ACTIVE (NOT(IE AND IRQ_PENDING))
A[12]   = flag_C
A[11]   = flag_Z
A[10:8] = step counter (0-7)
A[7:0]  = opcode (from IR)
```

Total: 14 bits = 16384 entries. Fits AT28C256 (32KB).

### IRQ entry sequence (in microcode, when A[13]=0 at step 0):

```
Step 0: Save PC_LO → RAM[$0E]
Step 1: Save PC_HI → RAM[$0F]
Step 2: Load PC ← $FF00 (vector address)
Step 3: Clear IE, Clear IRQ_FF, END
```

### Instructions (sub-codes of SYS $F8):

| Operand | Mnemonic | Action |
|:-------:|----------|--------|
| $02 | EI | IE ← 1 (enable interrupts) |
| $03 | DI | IE ← 0 (disable interrupts) |

### ISR pattern:

```asm
; ISR at $FF00:
    DI                  ; prevent nesting (already cleared by HW)
    PUSH r2             ; save registers as needed
    ; ... handle interrupt ...
    POP r2
    ; return: PC was saved to RAM[$0E/$0F]
    LB r4, [$0F]        ; load saved PC_HI
    LB r5, [$0E]        ; load saved PC_LO
    ; jump back (via JALR or page+jump)
    EI
    JALR r0, r5         ; return to saved PC (same-page)
```

---

## Status

- **Architecture**: Finalized (with IRQ)
- **Chip count**: 19 logic + 2 ROM + 1 RAM = **22 packages**
- **Control**: 8-bit group-encoded, 13-bit microcode address
- **Verification**: Pending Verilog RTL and gate-level simulation

---

*Document version: 2026-06-14*  
*Source of truth for RV8-R architecture*  
*Next: RTL implementation in Verilog*
