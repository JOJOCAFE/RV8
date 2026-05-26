# RV8-G Construction Guide

**38 logic chips + ROM + RAM = 40 packages**
**No microcode. Full 64K address. 35 instructions. 4-cycle execution.**

---

## Memory Map

    $0000-$0007  RAM registers R0-R7 (R0=AC mirror, R7=SP)
    $0008-$7FFF  RAM (32KB) — data, stack, can execute code
    $8000-$FFFF  ROM (32KB) — program storage
    PC starts at $8000 after reset

## ISA (35 instructions)

    Format: [opcode byte] [rs2/imm byte]
    
    Bit layout: [7:5]=ALU_OP, [4:3]=TYPE, [2:0]=rd/rs1
    
    ALU_OP: 000=NOP, 001=ADD, 010=SUB, 011=XOR, 100=AND, 101=OR, 110=SLL, 111=SRL/SLT
    TYPE:   00=R-type, 01=I-type, 10=LOAD, 11=STORE/BRANCH/SPECIAL

### R-Type (AC op RAM[rs2])
    $08  ADD  rd,rs2   001 00 rs2   AC = AC + RAM[rs2]; RAM[rd] = AC
    $10  SUB  rd,rs2   010 00 rs2   AC = AC - RAM[rs2]; RAM[rd] = AC
    $18  XOR  rd,rs2   011 00 rs2   AC = AC ^ RAM[rs2]; RAM[rd] = AC
    $20  AND  rd,rs2   100 00 rs2   AC = AC & RAM[rs2]; RAM[rd] = AC
    $28  OR   rd,rs2   101 00 rs2   AC = AC | RAM[rs2]; RAM[rd] = AC
    $30  SLL  rd,rs2   110 00 rs2   AC = AC << RAM[rs2]; RAM[rd] = AC
    $38  SRL  rd,rs2   111 00 rs2   AC = AC >> RAM[rs2]; RAM[rd] = AC
    $3C  SLT  rd,rs2   111 01 rs2   AC = (AC < RAM[rs2]) ? 1 : 0; RAM[rd] = AC

### I-Type (AC op imm)
    $48  ADDI rd,imm  001 01 iii   AC = AC + imm; RAM[rd] = AC
    $50  SUBI rd,imm  010 01 iii   AC = AC - imm; RAM[rd] = AC
    $58  XORI rd,imm  011 01 iii   AC = AC ^ imm; RAM[rd] = AC
    $60  ANDI rd,imm  100 01 iii   AC = AC & imm; RAM[rd] = AC
    $68  ORI  rd,imm  101 01 iii   AC = AC | imm; RAM[rd] = AC
    $70  SLLI rd,imm  110 01 iii   AC = AC << imm; RAM[rd] = AC
    $78  SRLI rd,imm  111 01 iii   AC = AC >> imm; RAM[rd] = AC
    $7C  SLTI rd,imm  111 01 iii   AC = (AC < imm) ? 1 : 0; RAM[rd] = AC

### Load/Store
    $88  LB   rd,off   001 10 ooo   AC = RAM[off]; RAM[rd] = AC
    $8C  SB   rd,off   001 11 ooo   RAM[off] = AC; RAM[rd] = AC

### Branch (rs1,rs2 in byte1)
    $A0  BEQ  rs1,rs2  101 00 ---   if RAM[rs1] == RAM[rs2]: PC += offset
    $A4  BNE  rs1,rs2  101 01 ---   if RAM[rs1] != RAM[rs2]: PC += offset
    $A8  BLT  rs1,rs2  101 10 ---   if RAM[rs1] < RAM[rs2]: PC += offset
    $AC  BGE  rs1,rs2  101 11 ---   if RAM[rs1] >= RAM[rs2]: PC += offset

### Jump
    $B0  JAL  rd,off   011 10 ooo   RAM[rd] = PC; PC += off; AC = RAM[rd]
    $B8  JALR rd,rs2   011 11 rrr   RAM[rd] = PC; PC = RAM[rs2]; AC = RAM[rd]

### Stack
    $C0  PUSH rs2      110 00 rrr   RAM[SP] = RAM[rs2]; SP--
    $C4  POP  rd       110 01 rrr   SP++; RAM[rd] = RAM[SP]; AC = RAM[rd]

### Special
    $00  NOP           000 00 000   no operation
    $04  MV   rd,rs2   000 01 rrr   RAM[rd] = RAM[rs2]; AC = RAM[rd]
    $0C  LI   rd,imm   000 11 iii   AC = imm; RAM[rd] = AC

---

## Architecture Overview

### 4-Cycle Timing
    T0: Fetch opcode byte from ROM[PC], latch to IR, PC++
    T1: Fetch operand byte from ROM[PC], latch to IRL, PC++
    T2: Load B-register from RAM[rs2] (R-type) or use IRL (I-type)
    T3: Execute ALU operation, write result to AC and RAM[rd]

### Key Components
    - PC (16-bit): 4× 74HC161 (U1-U4)
    - IR (16-bit): 2× 74HC574 (U5-U6) — opcode + operand
    - AC (8-bit): 1× 74HC574 (U9)
    - B-register (8-bit): 1× 74HC574 (U30) — second operand
    - SP (8-bit): 2× 74HC161 (U31-U32) — stack pointer
    - ALU: Adder(2× 283, U10-U11) + XOR(2× 86, U12-U13) + AND(2× 08, U14-U15) + OR(2× 32, U16-U17)
    - Result Mux: 6× 74HC157 (U18-U24) — ALU result selection + shift
    - Addr Mux: 4× 74HC157 (U25-U28) — PC vs register address

### Control Word (from IR byte 0)
    IR[7:5] = ALU_OP (selects ADD/SUB/XOR/AND/OR/SLL/SRL)
    IR[4:3] = TYPE (R/I/LOAD/STORE/BRANCH)
    IR[2:0] = rd (destination register)


---

## Buses (Pin-Level)

*******************************************
DBUS — External Data Bus (D0-D7)
*******************************************

D0  <-> ROM D0, RAM D0, U7-2(A1)
D1  <-> ROM D1, RAM D1, U7-3(A2)
D2  <-> ROM D2, RAM D2, U7-4(A3)
D3  <-> ROM D3, RAM D3, U7-5(A4)
D4  <-> ROM D4, RAM D4, U7-6(A5)
D5  <-> ROM D5, RAM D5, U7-7(A6)
D6  <-> ROM D6, RAM D6, U7-8(A7)
D7  <-> ROM D7, RAM D7, U7-9(A8)

*******************************************
IBUS — Internal Bus (IB0-IB7)
*******************************************
// Drivers (tristate, only ONE active):
//   U7  = ROM/RAM data (fetch or T2 register read)
//   U6  = IRL immediate (I-type, T2)
//   U14 = AC value (STORE, T3)
//   U34 = PC low byte (JAL/JALR return address)
// Consumers:
//   ALU A-input, B-register, SP, IR

IB0 <-> U7-18(B1), U6-19(Q1)*, U14-18(Y1)*, U34-18(Y1)*, U10-5(A0), U31-2(D1)
IB1 <-> U7-17(B2), U6-18(Q2)*, U14-17(Y2)*, U34-17(Y2)*, U10-3(A1), U31-3(D2)
IB2 <-> U7-16(B3), U6-17(Q3)*, U14-16(Y3)*, U34-16(Y3)*, U10-14(A2), U31-4(D3)
IB3 <-> U7-15(B4), U6-16(Q4)*, U14-15(Y4)*, U34-15(Y4)*, U10-12(A3), U31-5(D4)
IB4 <-> U7-14(B5), U6-15(Q5)*, U14-14(Y5)*, U34-14(Y5)*, U11-5(A0), U31-6(D5)
IB5 <-> U7-13(B6), U6-14(Q6)*, U14-13(Y6)*, U34-13(Y6)*, U11-3(A1), U31-7(D6)
IB6 <-> U7-12(B7), U6-13(Q7)*, U14-12(Y7)*, U34-12(Y7)*, U11-14(A2), U31-8(D7)
IB7 <-> U7-11(B8), U6-12(Q8)*, U14-11(Y8)*, U34-11(Y8)*, U11-12(A3), U31-9(D8)

*******************************************
ABUS — Address Bus (A0-A15)
*******************************************
// A0-A7:  from mux U15-U16 (PC low or rs2 or IRL)
// A8-A15: from mux U29-U30 (PC high or GND)

A0  <-- U15-4(1Y)      A8  <-- U29-4(1Y)
A1  <-- U15-7(2Y)      A9  <-- U29-7(2Y)
A2  <-- U15-9(3Y)      A10 <-- U29-9(3Y)
A3  <-- U15-12(4Y)     A11 <-- U29-12(4Y)
A4  <-- U16-4(1Y)      A12 <-- U30-4(1Y)
A5  <-- U16-7(2Y)      A13 <-- U30-7(2Y)
A6  <-- U16-9(3Y)      A14 <-- U30-9(3Y)
A7  <-- U16-12(4Y)     A15 <-- U30-12(4Y)


*******************************************
Control Signals
*******************************************

CLK     --> U1-2, U2-2, U3-2, U4-2, U8-8, U32-2
/RST    --> U1-1, U2-1, U3-1, U4-1, U8-9, U32-1
ROM /CE <-- /A15 (U33-6)
RAM /CE <-- A15 (U30-12)
RAM /WE <-- /RAM_WE (U28-8)

---

## Chip Wiring

*******************************************
U1-U4 74HC161 ×4 — Program Counter (16-bit)
*******************************************

U1-1 (/CLR) --> /RST
U1-2 (CLK)  --> CLK
U1-3 (A)    <-- IRL0 (U6-19)
U1-4 (B)    <-- IRL1 (U6-18)
U1-5 (C)    <-- IRL2 (U6-17)
U1-6 (D)    <-- IRL3 (U6-16)
U1-7 (ENP)  <-- PC_INC (U25-6)
U1-8 (GND)  --> GND
U1-9 (/LD)  <-- /PC_LD (U28-11)
U1-10 (ENT) <-- PC_INC (U25-6)
U1-11 (QD)  --> U15-14 (PC3)
U1-12 (QC)  --> U15-11 (PC2)
U1-13 (QB)  --> U15-5 (PC1)
U1-14 (QA)  --> U15-2 (PC0)
U1-15 (RCO) --> U2-10
U1-16 (VCC) --> VCC

U2-1 (/CLR) --> /RST
U2-2 (CLK)  --> CLK
U2-3 (A)    <-- IRL4 (U6-15)
U2-4 (B)    <-- IRL5 (U6-14)
U2-5 (C)    <-- IRL6 (U6-13)
U2-6 (D)    <-- IRL7 (U6-12)
U2-7 (ENP)  <-- PC_INC
U2-8 (GND)  --> GND
U2-9 (/LD)  <-- /PC_LD
U2-10 (ENT) <-- U1-15
U2-11 (QD)  --> U16-14 (PC7)
U2-12 (QC)  --> U16-11 (PC6)
U2-13 (QB)  --> U16-5 (PC5)
U2-14 (QA)  --> U16-2 (PC4)
U2-15 (RCO) --> U3-10
U2-16 (VCC) --> VCC

U3-1 (/CLR) --> /RST
U3-2 (CLK)  --> CLK
U3-3 (A)    <-- OFF0 (branch offset bit 0)
U3-4 (B)    <-- OFF1
U3-5 (C)    <-- OFF2
U3-6 (D)    <-- OFF3
U3-7 (ENP)  <-- PC_INC
U3-8 (GND)  --> GND
U3-9 (/LD)  <-- /PC_LD
U3-10 (ENT) <-- U2-15
U3-11 (QD)  --> U29-14 (PC11)
U3-12 (QC)  --> U29-11 (PC10)
U3-13 (QB)  --> U29-5 (PC9)
U3-14 (QA)  --> U29-2 (PC8)
U3-15 (RCO) --> U4-10
U3-16 (VCC) --> VCC

U4-1 (/CLR) --> /RST
U4-2 (CLK)  --> CLK
U4-3 (A)    <-- OFF4
U4-4 (B)    <-- OFF5
U4-5 (C)    <-- OFF6
U4-6 (D)    <-- OFF7
U4-7 (ENP)  <-- PC_INC
U4-8 (GND)  --> GND
U4-9 (/LD)  <-- /PC_LD
U4-10 (ENT) <-- U3-15
U4-11 (QD)  --> U30-14 (PC15)
U4-12 (QC)  --> U30-11 (PC14)
U4-13 (QB)  --> U30-5 (PC13)
U4-14 (QA)  --> U30-2 (PC12)
U4-15 (RCO) --> NC
U4-16 (VCC) --> VCC

*******************************************
U5 74HC574 — IR_HIGH (Opcode Register)
*******************************************

U5-1 (/OE)  --> GND
U5-2 (D1)   <-- IB0
U5-3 (D2)   <-- IB1
U5-4 (D3)   <-- IB2
U5-5 (D4)   <-- IB3
U5-6 (D5)   <-- IB4
U5-7 (D6)   <-- IB5
U5-8 (D7)   <-- IB6
U5-9 (D8)   <-- IB7
U5-10 (GND) --> GND
U5-11 (CLK) <-- T0 (U8-3)
U5-12 (Q8)  --> OP2 (bit 7)
U5-13 (Q7)  --> OP1 (bit 6)
U5-14 (Q6)  --> OP0 (bit 5)
U5-15 (Q5)  --> TYPE1 (bit 4)
U5-16 (Q4)  --> TYPE0 (bit 3)
U5-17 (Q3)  --> RD2 (bit 2)
U5-18 (Q2)  --> RD1 (bit 1)
U5-19 (Q1)  --> RD0 (bit 0)
U5-20 (VCC) --> VCC

*******************************************
U6 74HC574 — IR_LOW (Operand Register)
*******************************************

U6-1 (/OE)  <-- /IRL_OE (U28-3)
U6-2 (D1)   <-- IB0
U6-3 (D2)   <-- IB1
U6-4 (D3)   <-- IB2
U6-5 (D4)   <-- IB3
U6-6 (D5)   <-- IB4
U6-7 (D6)   <-- IB5
U6-8 (D7)   <-- IB6
U6-9 (D8)   <-- IB7
U6-10 (GND) --> GND
U6-11 (CLK) <-- T1 (U8-4)
U6-12 (Q8)  --> IRL7 → U16-13, IB7*
U6-13 (Q7)  --> IRL6 → U16-10, IB6*
U6-14 (Q6)  --> IRL5 → U16-6, IB5*
U6-15 (Q5)  --> IRL4 → U16-3, IB4*
U6-16 (Q4)  --> IRL3 → U15-13, IB3*
U6-17 (Q3)  --> IRL2 → U15-10, IB2*
U6-18 (Q2)  --> IRL1 → U15-6, IB1*
U6-19 (Q1)  --> IRL0 → U15-3, IB0*
U6-20 (VCC) --> VCC


*******************************************
U7 74HC245 — Bus Buffer (DBUS ↔ IBUS)
*******************************************

U7-1 (DIR)  <-- WR_DIR (U35-8)
U7-2 (A1)   <-> D0
U7-3 (A2)   <-> D1
U7-4 (A3)   <-> D2
U7-5 (A4)   <-> D3
U7-6 (A5)   <-> D4
U7-7 (A6)   <-> D5
U7-8 (A7)   <-> D6
U7-9 (A8)   <-> D7
U7-10 (GND) --> GND
U7-11 (B8)  <-> IB7
U7-12 (B7)  <-> IB6
U7-13 (B6)  <-> IB5
U7-14 (B5)  <-> IB4
U7-15 (B4)  <-> IB3
U7-16 (B3)  <-> IB2
U7-17 (B2)  <-> IB1
U7-18 (B1)  <-> IB0
U7-19 (/OE) <-- BUF_OE_N (U33-12)
U7-20 (VCC) --> VCC

*******************************************
U8 74HC164 — Ring Counter (T0, T1, T2, T3)
*******************************************

U8-1 (A)   <-- NOT(Q0) (U33-2)
U8-2 (B)   <-- NOT(Q1) (U33-4)
U8-3 (Q0)  --> T0
U8-4 (Q1)  --> T1
U8-5 (Q2)  --> T2
U8-6 (Q3)  --> T3
U8-7 (GND) --> GND
U8-8 (CLK) --> CLK
U8-9 (/CLR)--> /RST
U8-10..13  --> NC
U8-14(VCC) --> VCC


*******************************************
U9 74HC574 — Accumulator (AC)
*******************************************

U9-1 (/OE)  --> GND
U9-2 (D1)   <-- U21-4 (Result mux Y0)
U9-3 (D2)   <-- U21-7 (Y1)
U9-4 (D3)   <-- U21-9 (Y2)
U9-5 (D4)   <-- U21-12 (Y3)
U9-6 (D5)   <-- U22-4 (Y4)
U9-7 (D6)   <-- U22-7 (Y5)
U9-8 (D7)   <-- U22-9 (Y6)
U9-9 (D8)   <-- U22-12 (Y7)
U9-10 (GND) --> GND
U9-11 (CLK) <-- AC_CLK (U27-11)
U9-12 (Q8)  --> AC7 → U11-12, U12-13, U13-13, U14-9, U23-18
U9-13 (Q7)  --> AC6 → U11-14, U12-10, U13-10, U14-8, U23-16
U9-14 (Q6)  --> AC5 → U11-3, U12-6, U13-6, U14-7, U23-14
U9-15 (Q5)  --> AC4 → U11-5, U12-3, U13-3, U14-6, U23-12
U9-16 (Q4)  --> AC3 → U10-12, U14-5, U23-8
U9-17 (Q3)  --> AC2 → U10-14, U14-4, U23-6
U9-18 (Q2)  --> AC1 → U10-3, U14-3, U23-4
U9-19 (Q1)  --> AC0 → U10-5, U14-2, U23-2
U9-20 (VCC) --> VCC

*******************************************
U10 74HC283 — ALU Adder Low Nibble
*******************************************

U10-5 (A0)  <-- AC0 (U9-19)
U10-3 (A1)  <-- AC1 (U9-18)
U10-14(A2)  <-- AC2 (U9-17)
U10-12(A3)  <-- AC3 (U9-16)
U10-6 (B0)  <-- B0 (U31-19)
U10-2 (B1)  <-- B1 (U31-18)
U10-15(B2)  <-- B2 (U31-17)
U10-11(B3)  <-- B3 (U31-16)
U10-7 (Cin) <-- SUB_INV (U36-3)
U10-4 (S0)  --> SUM0 → U21-2
U10-1 (S1)  --> SUM1 → U21-5
U10-13(S2)  --> SUM2 → U21-11
U10-10(S3)  --> SUM3 → U21-14
U10-9 (Cout)--> U11-7
U10-8 (GND) --> GND
U10-16(VCC) --> VCC

*******************************************
U11 74HC283 — ALU Adder High Nibble
*******************************************

U11-5 (A0)  <-- AC4 (U9-15)
U11-3 (A1)  <-- AC5 (U9-14)
U11-14(A2)  <-- AC6 (U9-13)
U11-12(A3)  <-- AC7 (U9-12)
U11-6 (B0)  <-- B4 (U31-15)
U11-2 (B1)  <-- B5 (U31-14)
U11-15(B2)  <-- B6 (U31-13)
U11-11(B3)  <-- B7 (U31-12)
U11-7 (Cin) <-- U10-9
U11-4 (S0)  --> SUM4 → U22-2
U11-1 (S1)  --> SUM5 → U22-5
U11-13(S2)  --> SUM6 → U22-11
U11-10(S3)  --> SUM7 → U22-14
U11-9 (Cout)--> CARRY → U36-6
U11-8 (GND) --> GND
U11-16(VCC) --> VCC


*******************************************
U12 74HC86 — XOR Gates Low Nibble (ALU XOR)
*******************************************

U12-1 (A1)  <-- AC0 (U9-19)
U12-2 (B1)  <-- B0 (U31-19)
U12-3 (Y1)  --> XOR0 → U21-3
U12-4 (A2)  <-- AC1 (U9-18)
U12-5 (B2)  <-- B1 (U31-18)
U12-6 (Y2)  --> XOR1 → U21-6
U12-7 (GND) --> GND
U12-8 (Y3)  --> XOR2 → U21-10
U12-9 (A3)  <-- AC2 (U9-17)
U12-10(B3)  <-- B2 (U31-17)
U12-11(Y4)  --> XOR3 → U21-13
U12-12(A4)  <-- AC3 (U9-16)
U12-13(B4)  <-- B3 (U31-16)
U12-14(VCC) --> VCC

*******************************************
U13 74HC86 — XOR Gates High Nibble (ALU XOR)
*******************************************

U13-1 (A1)  <-- AC4 (U9-15)
U13-2 (B1)  <-- B4 (U31-15)
U13-3 (Y1)  --> XOR4 → U22-3
U13-4 (A2)  <-- AC5 (U9-14)
U13-5 (B2)  <-- B5 (U31-14)
U13-6 (Y2)  --> XOR5 → U22-6
U13-7 (GND) --> GND
U13-8 (Y3)  --> XOR6 → U22-10
U13-9 (A3)  <-- AC6 (U9-13)
U13-10(B3)  <-- B6 (U31-13)
U13-11(Y4)  --> XOR7 → U22-13
U13-12(A4)  <-- AC7 (U9-12)
U13-13(B4)  <-- B7 (U31-12)
U13-14(VCC) --> VCC

*******************************************
U14 74HC08 — AND Gates Low Nibble (ALU AND)
*******************************************

U14-1 (A1)  <-- AC0 (U9-19)
U14-2 (B1)  <-- B0 (U31-19)
U14-3 (Y1)  --> AND0 → U21-1 (mux A input)
U14-4 (A2)  <-- AC1 (U9-18)
U14-5 (B2)  <-- B1 (U31-18)
U14-6 (Y2)  --> AND1 → U21-8
U14-7 (GND) --> GND
U14-8 (Y3)  --> AND2 → U21-15
U14-9 (A3)  <-- AC2 (U9-17)
U14-10(B3)  <-- B2 (U31-17)
U14-11(Y4)  --> AND3 → U21-16
U14-12(A4)  <-- AC3 (U9-16)
U14-13(B4)  <-- B3 (U31-16)
U14-14(VCC) --> VCC

*******************************************
U15 74HC08 — AND Gates High Nibble (ALU AND)
*******************************************

U15-1 (A1)  <-- AC4 (U9-15)
U15-2 (B1)  <-- B4 (U31-15)
U15-3 (Y1)  --> AND4 → U22-1
U15-4 (A2)  <-- AC5 (U9-14)
U15-5 (B2)  <-- B5 (U31-14)
U15-6 (Y2)  --> AND5 → U22-8
U15-7 (GND) --> GND
U15-8 (Y3)  --> AND6 → U22-15
U15-9 (A3)  <-- AC6 (U9-13)
U15-10(B3)  <-- B6 (U31-13)
U15-11(Y4)  --> AND7 → U22-16
U15-12(A4)  <-- AC7 (U9-12)
U15-13(B4)  <-- B7 (U31-12)
U15-14(VCC) --> VCC

*******************************************
U16 74HC32 — OR Gates Low Nibble (ALU OR)
*******************************************

U16-1 (A1)  <-- AC0 (U9-19)
U16-2 (B1)  <-- B0 (U31-19)
U16-3 (Y1)  --> OR0 → U17-2
U16-4 (A2)  <-- AC1 (U9-18)
U16-5 (B2)  <-- B1 (U31-18)
U16-6 (Y2)  --> OR1 → U17-5
U16-7 (GND) --> GND
U16-8 (Y3)  --> OR2 → U17-11
U16-9 (A3)  <-- AC2 (U9-17)
U16-10(B3)  <-- B2 (U31-17)
U16-11(Y4)  --> OR3 → U17-14
U16-12(A4)  <-- AC3 (U9-16)
U16-13(B4)  <-- B3 (U31-16)
U16-14(VCC) --> VCC

*******************************************
U17 74HC32 — OR Gates High Nibble (ALU OR)
*******************************************

U17-1 (A1)  <-- AC4 (U9-15)
U17-2 (B1)  <-- B4 (U31-15)
U17-3 (Y1)  --> OR4 → U18-2
U17-4 (A2)  <-- AC5 (U9-14)
U17-5 (B2)  <-- B5 (U31-14)
U17-6 (Y2)  --> OR5 → U18-5
U17-7 (GND) --> GND
U17-8 (Y3)  --> OR6 → U18-11
U17-9 (A3)  <-- AC6 (U9-13)
U17-10(B3)  <-- B6 (U31-13)
U17-11(Y4)  --> OR7 → U18-14
U17-12(A4)  <-- AC7 (U9-12)
U17-13(B4)  <-- B7 (U31-12)
U17-14(VCC) --> VCC


*******************************************
U18 74HC157 — Result Mux Low Nibble (ALU select)
// SEL[0]=0: SUM (adder) | SEL[0]=1: XOR
// SEL[1]=0: use SEL[0] | SEL[1]=1: AND/OR bypass
*******************************************

U18-1 (SEL0) <-- ALU_SEL0 (U37-3)
U18-2 (1A)   <-- SUM0 (U10-4)   U18-3 (1B) <-- XOR0 (U12-3)   U18-4 (1Y) --> RES0
U18-5 (2A)   <-- SUM1 (U10-1)   U18-6 (2B) <-- XOR1 (U12-6)   U18-7 (2Y) --> RES1
U18-11(3A)   <-- SUM2 (U10-13)  U18-10(3B) <-- XOR2 (U12-8)   U18-9 (3Y) --> RES2
U18-14(4A)   <-- SUM3 (U10-10)  U18-13(4B) <-- XOR3 (U12-11)  U18-12(4Y) --> RES3
U18-8 (GND)  --> GND    U18-15(/E) --> GND    U18-16(VCC) --> VCC

*******************************************
U19 74HC157 — Result Mux High Nibble
*******************************************

U19-1 (SEL0) <-- ALU_SEL0 (U37-3)
U19-2 (1A)   <-- SUM4 (U11-4)   U19-3 (1B) <-- XOR4 (U13-3)   U19-4 (1Y) --> RES4
U19-5 (2A)   <-- SUM5 (U11-1)   U19-6 (2B) <-- XOR5 (U13-6)   U19-7 (2Y) --> RES5
U19-11(3A)   <-- SUM6 (U11-13)  U19-10(3B) <-- XOR6 (U13-8)   U19-9 (3Y) --> RES6
U19-14(4A)   <-- SUM7 (U11-10)  U19-13(4B) <-- XOR7 (U13-11)  U19-12(4Y) --> RES7
U19-8 (GND)  --> GND    U19-15(/E) --> GND    U19-16(VCC) --> VCC

*******************************************
U20 74HC157 — Result Mux Stage 2 (AND/OR select)
*******************************************

U20-1 (SEL)  <-- ALU_SEL1 (U37-6)
U20-2 (1A)   <-- RES0 (U18-4)    U20-3 (1B) <-- AND0 (U14-3)   U20-4 (1Y) --> MUX0 → U21-2
U20-5 (2A)   <-- RES1 (U18-7)    U20-6 (2B) <-- AND1 (U14-6)   U20-7 (2Y) --> MUX1 → U21-5
U20-11(3A)   <-- RES2 (U18-9)    U20-10(3B) <-- AND2 (U14-8)   U20-9 (3Y) --> MUX2 → U21-11
U20-14(4A)   <-- RES3 (U18-12)   U20-13(4B) <-- AND3 (U14-11)  U20-12(4Y) --> MUX3 → U21-14
U20-8 (GND)  --> GND    U20-15(/E) --> GND    U20-16(VCC) --> VCC

*******************************************
U21 74HC157 — Result Mux Stage 3 (OR/Shift)
*******************************************

U21-1 (SEL)  <-- ALU_SEL2 (U37-11)
U21-2 (1A)   <-- MUX0 (U20-4)    U21-3 (1B) <-- OR0 (U16-3)    U21-4 (1Y) --> AC D0 (U9-2)
U21-5 (2A)   <-- MUX1 (U20-7)    U21-6 (2B) <-- OR1 (U16-6)    U21-7 (2Y) --> AC D1 (U9-3)
U21-11(3A)   <-- MUX2 (U20-9)    U21-10(3B) <-- OR2 (U16-8)    U21-9 (3Y) --> AC D2 (U9-4)
U21-14(4A)   <-- MUX3 (U20-12)   U21-13(4B) <-- OR3 (U16-11)   U21-12(4Y) --> AC D3 (U9-5)
U21-8 (GND)  --> GND    U21-15(/E) --> GND    U21-16(VCC) --> VCC

*******************************************
U22 74HC157 — Result Mux Stage 3 High + Shift
*******************************************

U22-1 (SEL)  <-- ALU_SEL2 (U37-11)
U22-2 (1A)   <-- MUX4 (U23-4)    U22-3 (1B) <-- OR4 (U17-3)    U22-4 (1Y) --> AC D4 (U9-6)
U22-5 (2A)   <-- MUX5 (U23-7)    U22-6 (2B) <-- OR5 (U17-6)    U22-7 (2Y) --> AC D5 (U9-7)
U22-11(3A)   <-- MUX6 (U23-9)    U22-10(3B) <-- OR6 (U17-8)    U22-9 (3Y) --> AC D6 (U9-8)
U22-14(4A)   <-- MUX7 (U23-12)   U22-13(4B) <-- OR7 (U17-11)   U22-12(4Y) --> AC D7 (U9-9)
U22-8 (GND)  --> GND    U22-15(/E) --> GND    U22-16(VCC) --> VCC

*******************************************
U23 74HC157 — Shift Right Mux (SRL)
*******************************************

U23-1 (SEL)  <-- ALU_SEL3 (U37-8)
U23-2 (1A)   <-- MUX4 (U24-4)    U23-3 (1B) <-- AC5 (U9-14)     U23-4 (1Y) --> MUX4 → U22-2
U23-5 (2A)   <-- MUX5 (U24-7)    U23-6 (2B) <-- AC6 (U9-13)     U23-7 (2Y) --> MUX5 → U22-5
U23-11(3A)   <-- MUX6 (U24-9)    U23-10(3B) <-- AC7 (U9-12)     U23-9 (3Y) --> MUX6 → U22-11
U23-14(4A)   <-- MUX7 (U24-12)   U23-13(4B) <-- GND             U23-12(4Y) --> MUX7 → U22-14
U23-8 (GND)  --> GND    U23-15(/E) --> GND    U23-16(VCC) --> VCC

*******************************************
U24 74HC157 — Result Stage 2 High + Shift Logic
*******************************************

U24-1 (SEL)  <-- ALU_SEL1 (U37-6)
U24-2 (1A)   <-- RES4 (U19-4)    U24-3 (1B) <-- AND4 (U15-3)    U24-4 (1Y) --> MUX4 → U23-2
U24-5 (2A)   <-- RES5 (U19-7)    U24-6 (2B) <-- AND5 (U15-6)    U24-7 (2Y) --> MUX5 → U23-5
U24-11(3A)   <-- RES6 (U19-9)    U24-10(3B) <-- AND6 (U15-8)    U24-9 (3Y) --> MUX6 → U23-11
U24-14(4A)   <-- RES7 (U19-12)   U24-13(4B) <-- AND7 (U15-11)   U24-12(4Y) --> MUX7 → U23-14
U24-8 (GND)  --> GND    U24-15(/E) --> GND    U24-16(VCC) --> VCC


*******************************************
U25 74HC157 — Address Mux A0-A3 (PC vs rs2)
*******************************************

U25-1 (SEL) <-- ADDR_MODE (U38-3)
U25-2 (1A)  <-- PC0 (U1-14)    U25-3 (1B) <-- RS20 (U6-19)    U25-4 (1Y) --> A0
U25-5 (2A)  <-- PC1 (U1-13)    U25-6 (2B) <-- RS21 (U6-18)    U25-7 (2Y) --> A1
U25-11(3A)  <-- PC2 (U1-12)    U25-10(3B) <-- RS22 (U6-17)    U25-9 (3Y) --> A2
U25-14(4A)  <-- PC3 (U1-11)    U25-13(4B) <-- RS23 (U6-16)    U25-12(4Y) --> A3
U25-8 (GND) --> GND    U25-15(/E) --> GND    U25-16(VCC) --> VCC

*******************************************
U26 74HC157 — Address Mux A4-A7
*******************************************

U26-1 (SEL) <-- ADDR_MODE
U26-2 (1A)  <-- PC4 (U2-14)    U26-3 (1B) <-- RS24 (U6-15)    U26-4 (1Y) --> A4
U26-5 (2A)  <-- PC5 (U2-13)    U26-6 (2B) <-- RS25 (U6-14)    U26-7 (2Y) --> A5
U26-11(3A)  <-- PC6 (U2-12)    U26-10(3B) <-- RS26 (U6-13)    U26-9 (3Y) --> A6
U26-14(4A)  <-- PC7 (U2-11)    U26-13(4B) <-- RS27 (U6-12)    U26-12(4Y) --> A7
U26-8 (GND) --> GND    U26-15(/E) --> GND    U26-16(VCC) --> VCC

*******************************************
U27 74HC157 — Address Mux A8-A11
*******************************************

U27-1 (SEL) <-- ADDR_MODE
U27-2 (1A)  <-- PC8 (U3-14)    U27-3 (1B) <-- GND               U27-4 (1Y) --> A8
U27-5 (2A)  <-- PC9 (U3-13)    U27-6 (2B) <-- GND               U27-7 (2Y) --> A9
U27-11(3A)  <-- PC10(U3-12)    U27-10(3B) <-- GND               U27-9 (3Y) --> A10
U27-14(4A)  <-- PC11(U3-11)    U27-13(4B) <-- GND               U27-12(4Y) --> A11
U27-8 (GND) --> GND    U27-15(/E) --> GND    U27-16(VCC) --> VCC

*******************************************
U28 74HC157 — Address Mux A12-A15
*******************************************

U28-1 (SEL) <-- ADDR_MODE
U28-2 (1A)  <-- PC12(U4-14)    U28-3 (1B) <-- GND               U28-4 (1Y) --> A12
U28-5 (2A)  <-- PC13(U4-13)    U28-6 (2B) <-- GND               U28-7 (2Y) --> A13
U28-11(3A)  <-- PC14(U4-12)    U28-10(3B) <-- GND               U28-9 (3Y) --> A14
U28-14(4A)  <-- PC15(U4-11)    U28-13(4B) <-- GND               U28-12(4Y) --> A15
U28-8 (GND) --> GND    U28-15(/E) --> GND    U28-16(VCC) --> VCC

*******************************************
U29 74HC541 — AC Output Buffer (AC → IBUS)
*******************************************

U29-1 (/OE1) <-- /AC_BUF (U39-8)
U29-2 (A1)   <-- AC0 (U9-19)
U29-3 (A2)   <-- AC1 (U9-18)
U29-4 (A3)   <-- AC2 (U9-17)
U29-5 (A4)   <-- AC3 (U9-16)
U29-6 (A5)   <-- AC4 (U9-15)
U29-7 (A6)   <-- AC5 (U9-14)
U29-8 (A7)   <-- AC6 (U9-13)
U29-9 (A8)   <-- AC7 (U9-12)
U29-10(GND)  --> GND
U29-11(Y8)   --> IB7
U29-12(Y7)   --> IB6
U29-13(Y6)   --> IB5
U29-14(Y5)   --> IB4
U29-15(Y4)   --> IB3
U29-16(Y3)   --> IB2
U29-17(Y2)   --> IB1
U29-18(Y1)   --> IB0
U29-19(/OE2) <-- /AC_BUF (U39-8)
U29-20(VCC)  --> VCC

*******************************************
U30 74HC574 — B-Register (Second Operand)
*******************************************

U30-1 (/OE)  --> GND
U30-2 (D1)   <-- IB0
U30-3 (D2)   <-- IB1
U30-4 (D3)   <-- IB2
U30-5 (D4)   <-- IB3
U30-6 (D5)   <-- IB4
U30-7 (D6)   <-- IB5
U30-8 (D7)   <-- IB6
U30-9 (D8)   <-- IB7
U30-10(GND)  --> GND
U30-11(CLK)  <-- B_CLK (U39-11)
U30-12(Q8)   --> B7 → U11-11, U13-13, U15-13, U17-13
U30-13(Q7)   --> B6 → U11-15, U13-10, U15-10, U17-10
U30-14(Q6)   --> B5 → U11-2, U13-5, U15-5, U17-5
U30-15(Q5)   --> B4 → U11-6, U13-2, U15-2, U17-2
U30-16(Q4)   --> B3 → U10-11, U12-13, U14-13, U16-13
U30-17(Q3)   --> B2 → U10-15, U12-10, U14-10, U16-10
U30-18(Q2)   --> B1 → U10-2, U12-5, U14-5, U16-5
U30-19(Q1)   --> B0 → U10-6, U12-2, U14-2, U16-2
U30-20(VCC)  --> VCC


*******************************************
U31 74HC161 — Stack Pointer (SP)
*******************************************

U31-1 (/CLR) --> /RST
U31-2 (CLK)  --> CLK
U31-3 (A)    <-- SP_D0
U31-4 (B)    <-- SP_D1
U31-5 (C)    <-- SP_D2
U31-6 (D)    <-- SP_D3
U31-7 (ENP)  <-- SP_EN (U38-11)
U31-8 (GND)  --> GND
U31-9 (/LD)  <-- /SP_LD (U39-3)
U31-10(ENT)  <-- SP_EN
U31-11(QD)   --> SP3 → U32-3
U31-12(QC)   --> SP2 → U32-6
U31-13(QB)   --> SP1 → U32-11
U31-14(QA)   --> SP0 → U32-14
U31-15(RCO)  --> NC
U31-16(VCC)  --> VCC

*******************************************
U32 74HC161 — Stack Pointer High Nibble
*******************************************

U32-1 (/CLR) --> /RST
U32-2 (CLK)  --> CLK
U32-3 (A)    <-- SP3 (U31-11)
U32-4 (B)    <-- SP_D4
U32-5 (C)    <-- SP_D5
U32-6 (D)    <-- SP2 (U31-12)
U32-7 (ENP)  <-- SP_EN
U32-8 (GND)  --> GND
U32-9 (/LD)  <-- /SP_LD
U32-10(ENT)  <-- U31-15
U32-11(QD)   --> SP7 → U33-2
U32-12(QC)   --> SP6 → U33-5
U32-13(QB)   --> SP5 → U33-9
U32-14(QA)   --> SP4 → U33-12
U32-15(RCO)  --> NC
U32-16(VCC)  --> VCC

*******************************************
U33 74HC541 — SP Buffer (SP → ABUS A0-A7 for stack)
*******************************************

U33-1 (/OE1) <-- /SP_OE (U38-8)
U33-2 (A1)   <-- SP7 (U32-11)
U33-3 (A2)   <-- SP6 (U32-12)
U33-4 (A3)   <-- SP5 (U32-13)
U33-5 (A4)   <-- SP4 (U32-14)
U33-6 (A5)   <-- SP3 (U31-11)
U33-7 (A6)   <-- SP2 (U31-12)
U33-8 (A7)   <-- SP1 (U31-13)
U33-9 (A8)   <-- SP0 (U31-14)
U33-10(GND)  --> GND
U33-11(Y8)   --> NC (SP goes through different path)
U33-12(Y7)   --> NC
U33-13(Y6)   --> NC
U33-14(Y5)   --> NC
U33-15(Y4)   --> NC
U33-16(Y3)   --> NC
U33-17(Y2)   --> NC
U33-18(Y1)   --> NC
U33-19(/OE2) <-- /SP_OE
U33-20(VCC)  --> VCC

*******************************************
U34 74HC74 — Z Flag + N Flag Registers
*******************************************

U34-1 (/CLR1)--> VCC
U34-2 (D1)   --> GND
U34-3 (CLK1) <-- AC_CLK (U39-11)
U34-4 (/PR1) <-- Z_SET (U35-19)
U34-5 (Q1)   --> Z_FLAG → U36-1
U34-6 (/Q1)  --> NC
U34-7 (GND)  --> GND
U34-8 (/PR2) <-- N_SET (U35-17)
U34-9 (CLK2) <-- AC_CLK
U34-10(D2)   --> GND
U34-11(/CLR2)--> VCC
U34-12(Q2)   --> N_FLAG → U36-4
U34-13(/Q2)  --> NC
U34-14(VCC)  --> VCC

*******************************************
U35 74HC688 — Zero Detect (AC == 0?)
*******************************************

U35-1 (/OE)  --> GND
U35-2 (P0)   <-- AC0 (U9-19)   U35-3 (Q0) --> GND
U35-4 (P1)   <-- AC1 (U9-18)   U35-5 (Q1) --> GND
U35-6 (P2)   <-- AC2 (U9-17)   U35-7 (Q2) --> GND
U35-8 (P3)   <-- AC3 (U9-16)   U35-9 (Q3) --> GND
U35-10(GND)  --> GND
U35-11(Q4)   --> GND           U35-12(P4) <-- AC4 (U9-15)
U35-13(Q5)   --> GND           U35-14(P5) <-- AC5 (U9-14)
U35-15(Q6)   --> GND           U35-16(P6) <-- AC6 (U9-13)
U35-17(Q7)   --> GND           U35-18(P7) <-- AC7 (U9-12)
U35-19(/P=Q) --> Z_SET → U34-4
U35-20(VCC)  --> VCC


*******************************************
U36 74HC86 — Control XOR Gates
*******************************************

// Gate A: Z_MATCH = Z_FLAG XOR COND_INV (BEQ vs BNE)
U36-1 (1A)  <-- Z_FLAG (U34-5)
U36-2 (1B)  <-- COND_INV (U37-8)
U36-3 (1Y)  --> Z_MATCH → U38-1

// Gate B: N_MATCH = N_FLAG XOR COND_INV (BLT vs BGE)
U36-4 (2A)  <-- N_FLAG (U34-12)
U36-5 (2B)  <-- COND_INV
U36-6 (2Y)  --> N_MATCH → U38-2

// Gate C: SUB_INV = 1 for SUB (inverts B for subtraction)
U36-9 (3A)  <-- OP_SUB (U37-11)
U36-10(3B)  --> VCC
U36-8 (3Y)  --> SUB_INV → U10-7

// Gate D: /T3 = NOT(T3)
U36-12(4A) <-- T3 (U8-6)
U36-13(4B) --> VCC
U36-11(4Y) --> /T3 → U39-2

U36-7 (GND) --> GND    U36-14(VCC) --> VCC

*******************************************
U37 74HC138 — 3-to-8 Decoder (ALU_OP decode)
*******************************************

U37-1 (A)   <-- OP0 (U5-14)
U37-2 (B)   <-- OP1 (U5-13)
U37-3 (C)   <-- OP2 (U5-12)
U37-4 (/E1) --> GND
U37-5 (/E2) --> GND
U37-6 (E3)  --> VCC
U37-7 (Y7)  --> OP_SRL → U23-1
U37-8 (GND) --> GND
U37-9 (Y6)  --> OP_SLL
U37-10(Y5)  --> OP_OR
U37-11(Y4)  --> OP_AND
U37-12(Y3)  --> OP_XOR
U37-13(Y2)  --> OP_SUB
U37-14(Y0)  --> OP_ADD
U37-15(Y1)  --> NC (NOP, no ALU op)
U37-16(VCC) --> VCC

*******************************************
U38 74HC00 — NAND Gates #1 (Control logic)
*******************************************

// Gate A: BR_TAKEN = NAND(Z_MATCH, N_MATCH, BRANCH)
U38-1 (1A) <-- Z_MATCH (U36-3)
U38-2 (1B) <-- N_MATCH (U36-6)
U38-3 (1Y) --> BR_COND → U38-4

// Gate B: PC_BRANCH = NAND(BR_COND, BRANCH)
U38-4 (2A) <-- BR_COND (U38-3)
U38-5 (2B) <-- BRANCH (U39-6)
U38-6 (2Y) --> PC_BRANCH → U39-12

// Gate C: ADDR_MODE = NAND(/T0, /T1) = T2 OR T3
U38-9 (3A) <-- /T0 (U40-2)
U38-10(3B) <-- /T1 (U40-4)
U38-8 (3Y) --> ADDR_MODE → U25-1, U26-1, U27-1, U28-1

// Gate D: SP_EN = NAND(T3, PUSH_OR_POP)
U38-12(4A) <-- T3 (U8-6)
U38-13(4B) <-- STACK_OP (U39-13)
U38-11(4Y) --> SP_EN → U31-7, U31-10, U32-7

U38-7 (GND)--> GND    U38-14(VCC)--> VCC

*******************************************
U39 74HC00 — NAND Gates #2 (More control)
*******************************************

// Gate A: /SP_LD = NAND(T3, STACK_OP)
U39-1 (1A) <-- T3 (U8-6)
U39-2 (1B) <-- STACK_OP
U39-3 (1Y) --> /SP_LD → U31-9, U32-9

// Gate B: AC_CLK = NAND(T3, AC_WR)
U39-4 (2A) <-- T3 (U8-6)
U39-5 (2B) <-- AC_WR (from opcode decode)
U39-6 (2Y) --> AC_CLK → U9-11, U34-3, U34-9

// Gate C: /AC_BUF = NAND(T3, STORE_OP)
U39-9 (3A) <-- T3
U39-10(3B) <-- STORE_OP
U39-8 (3Y) --> /AC_BUF → U29-1, U29-19, RAM /WE

// Gate D: B_CLK = NAND(T2, LOAD_B)
U39-12(4A) <-- T2 (U8-5)
U39-13(4B) <-- LOAD_B (from TYPE decode)
U39-11(4Y) --> B_CLK → U30-11

U39-7 (GND)--> GND    U39-14(VCC)--> VCC

*******************************************
U40 74HC04 — Inverters
*******************************************

U40-1 (1A)  <-- T0 (U8-3)          U40-2 (1Y) --> /T0 → U38-9
U40-3 (2A)  <-- T1 (U8-4)          U40-4 (2Y) --> /T1 → U38-10
U40-5 (3A)  <-- T2 (U8-5)          U40-6 (3Y) --> /T2 → U41-1
U40-7 (GND) --> GND
U40-9 (4A)  <-- A15 (U28-12)       U40-8 (4Y) --> /A15 → ROM /CE
U40-11(5A)  <-- IRL_OE_COND        U40-10(5Y) --> /IRL_OE → U6-1
U40-13(6A)  <-- BUF_EN             U40-12(6Y) --> BUF_OE_N → U7-19
U40-14(VCC) --> VCC

*******************************************
U41 74HC32 — OR Gates (Timing)
*******************************************

// Gate A: PC_INC = T0 OR T1
U41-1 (1A) <-- T0 (U8-3)
U41-2 (1B) <-- T1 (U8-4)
U41-3 (1Y) --> PC_INC → U1-7, U1-10, U2-7, U3-7, U4-7

// Gate B: /PC_LD for jump/branch
U41-4 (2A) <-- PC_BRANCH (U38-6)
U41-5 (2B) <-- JUMP (from opcode)
U41-6 (2Y) --> /PC_LD → U1-9, U2-9, U3-9, U4-9

// Gate C: WR_DIR for bus direction
U41-9 (3A) <-- T3
U41-10(3B) <-- STORE_OP
U41-8 (3Y) --> WR_DIR → U7-1

// Gate D: spare
U41-12(4A) --> NC    U41-13(4B) --> NC    U41-11(4Y) --> NC

U41-7 (GND) --> GND    U41-14(VCC) --> VCC


*******************************************
ROM — SST39SF010A (128KB Flash)
*******************************************

ROM A0-A7  <-- ABUS A0-A7
ROM A8-A14 <-- ABUS A8-A14
ROM A15    --> NC
ROM A16    --> GND
ROM D0-D7  --> DBUS
ROM /CE    <-- /A15 (U40-8)
ROM /OE    --> GND
ROM /WE    --> VCC

*******************************************
RAM — 62256 (32KB SRAM)
*******************************************

RAM A0-A7  <-- ABUS A0-A7
RAM A8-A14 <-- ABUS A8-A14
RAM D0-D7  <-> DBUS
RAM /CE    <-- A15 (U28-12)
RAM /OE    --> GND
RAM /WE    <-- /AC_BUF (U39-8)

---

## Control Signal Generation

### ALU Select Signals (from U37 74HC138)

| ALU_OP | OP2 | OP1 | OP0 | Y output | Operation |
|--------|-----|-----|-----|----------|-----------|
| NOP    | 0   | 0   | 0   | Y0=0     | None      |
| ADD    | 0   | 0   | 1   | Y1=0     | SUM → AC  |
| SUB    | 0   | 1   | 0   | Y2=0     | SUM → AC  |
| XOR    | 0   | 1   | 1   | Y3=0     | XOR → AC  |
| AND    | 1   | 0   | 0   | Y4=0     | AND → AC  |
| OR     | 1   | 0   | 1   | Y5=0     | OR → AC   |
| SLL    | 1   | 1   | 0   | Y6=0     | A+A → AC  |
| SRL    | 1   | 1   | 1   | Y7=0     | Shift → AC|

### Result Mux Select

    ALU_SEL0 = NOT(Y1) OR NOT(Y2)  // ADD or SUB selects SUM
    ALU_SEL1 = NOT(Y4) OR NOT(Y5)  // AND or OR selects those gates
    ALU_SEL2 = NOT(Y5) OR NOT(Y6) OR NOT(Y7)  // OR/SLL/SRL bypass
    ALU_SEL3 = NOT(Y7)             // SRL enables shift mux

### Address Mode

    ADDR_MODE = T2 OR T3 (high during data phase)
    SEL=0: PC → ABUS (fetch)
    SEL=1: rs2 → ABUS (register access)

### B-Register Load

    B_CLK = T2 AND (TYPE=00 OR TYPE=01)  // R-type or I-type
    I-type: IRL already on IBUS (immediate)
    R-type: RAM[rs2] on IBUS after read

### AC Write

    AC_CLK = T3 AND (ALU_OP ≠ 0)  // Write result for non-NOP

### RAM Write

    RAM /WE = NOT(T3 AND STORE_OP)

---

## ISA Decode Verification

| Instr | Opcode | T2 Action | T3 Action | Result |
|-------|--------|-----------|-----------|--------|
| NOP   | $00    | —         | —         | no op |
| ADD   | $08    | B←RAM[rs2]| AC←A+B    | AC+RAM |
| SUB   | $10    | B←RAM[rs2]| AC←A-B    | AC-RAM |
| XOR   | $18    | B←RAM[rs2]| AC←A^B    | AC^RAM |
| AND   | $20    | B←RAM[rs2]| AC←A&B    | AC&RAM |
| OR    | $28    | B←RAM[rs2]| AC←A\|B   | AC\|RAM |
| SLL   | $30    | B←RAM[rs2]| AC←A<<B   | shift L |
| SRL   | $38    | B←RAM[rs2]| AC←A>>B   | shift R |
| SLT   | $3C    | B←RAM[rs2]| AC←(A<B)  | compare |
| ADDI  | $48    | B←imm     | AC←A+B    | AC+imm |
| SUBI  | $50    | B←imm     | AC←A-B    | AC-imm |
| XORI  | $58    | B←imm     | AC←A^B    | AC^imm |
| ANDI  | $60    | B←imm     | AC←A&B    | AC&imm |
| ORI   | $68    | B←imm     | AC←A\|B   | AC\|imm |
| SLLI  | $70    | B←imm     | AC←A<<B   | shift L |
| SRLI  | $78    | B←imm     | AC←A>>B   | shift R |
| SLTI  | $7C    | B←imm     | AC←(A<B)  | compare |
| LB    | $88    | B←RAM[off]| AC←B      | load |
| SB    | $8C    | —         | RAM←AC    | store |
| BEQ   | $A0    | SUB rs1,rs2| if Z: PC+=off | branch |
| BNE   | $A4    | SUB rs1,rs2| if !Z: PC+=off| branch |
| BLT   | $A8    | SUB rs1,rs2| if N: PC+=off | branch |
| BGE   | $AC    | SUB rs1,rs2| if !N: PC+=off| branch |
| JAL   | $B0    | —         | RAM[rd]=PC, PC+=off | jump |
| JALR  | $B8    | B←RAM[rs2]| RAM[rd]=PC, PC=B | jump reg |
| PUSH  | $C0    | —         | RAM[SP]=AC, SP-- | push |
| POP   | $C4    | SP++      | AC←RAM[SP] | pop |
| MV    | $04    | B←RAM[rs2]| AC←B, RAM[rd]=B | move |
| LI    | $0C    | B←imm     | AC←B      | load imm |

---

## Chip Summary (38 logic chips)

| U#  | Chip    | Function |
|-----|---------|----------|
| U1-4| 74HC161 | PC (16-bit) |
| U5  | 74HC574 | IR_HIGH (opcode) |
| U6  | 74HC574 | IR_LOW (operand) |
| U7  | 74HC245 | Bus buffer |
| U8  | 74HC164 | Ring counter |
| U9  | 74HC574 | Accumulator |
| U10 | 74HC283 | Adder low |
| U11 | 74HC283 | Adder high |
| U12 | 74HC86  | XOR low |
| U13 | 74HC86  | XOR high |
| U14 | 74HC08  | AND low |
| U15 | 74HC08  | AND high |
| U16 | 74HC32  | OR low |
| U17 | 74HC32  | OR high |
| U18 | 74HC157 | Result mux 1 |
| U19 | 74HC157 | Result mux 2 |
| U20 | 74HC157 | Result mux 3 |
| U21 | 74HC157 | Result mux 4 |
| U22 | 74HC157 | Result mux 5 |
| U23 | 74HC157 | Shift mux |
| U24 | 74HC157 | Result stage 2 |
| U25 | 74HC157 | Addr mux A0-A3 |
| U26 | 74HC157 | Addr mux A4-A7 |
| U27 | 74HC157 | Addr mux A8-A11 |
| U28 | 74HC157 | Addr mux A12-A15 |
| U29 | 74HC541 | AC buffer |
| U30 | 74HC574 | B-register |
| U31 | 74HC161 | SP low |
| U32 | 74HC161 | SP high |
| U33 | 74HC541 | SP buffer |
| U34 | 74HC74  | Z/N flags |
| U35 | 74HC688 | Zero detect |
| U36 | 74HC86  | Control XOR |
| U37 | 74HC138 | ALU decode |
| U38 | 74HC00  | NAND #1 |
| U39 | 74HC00  | NAND #2 |
| U40 | 74HC04  | Inverters |
| U41 | 74HC32  | OR gates |

---

## RV8-Bus Pinout (40-pin)

    Pin 1-8:   D0-D7 (DBUS)
    Pin 9-16:  A0-A7 (ABUS low)
    Pin 17-24: A8-A15 (ABUS high)
    Pin 25:    CLK
    Pin 26:    /RST
    Pin 27:    /HALT (output)
    Pin 28:    /IRQ (input)
    Pin 29:    GND
    Pin 30:    VCC
    Pin 31-40: GPIO (expansion)

