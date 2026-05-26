# RV8-GR Construction Guide

**29 logic chips + ROM + RAM = 31 packages**
**No microcode. Full 64K address. 16-bit jump. Verilog verified (127 cycles).**

---

## Memory Map

    $0000-$7FFF  RAM (32KB) — registers, data, can execute code
    $8000-$FFFF  ROM (32KB visible, bankable to 128KB)
    PC starts at $8000 after reset

## ISA (15 instructions)

    Byte 0 Control: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
    Byte 1 Operand: immediate value, RAM address, or jump target (8-bit)

    $00  NOP          00000000   —
    $10  ADDI imm     00010000   AC = AC + imm
    $18  ADD rs       00011000   AC = AC + RAM[rs]
    $90  SUBI imm     10010000   AC = AC - imm
    $98  SUB rs       10011000   AC = AC - RAM[rs]
    $70  XORI imm     01110000   AC = AC ^ imm
    $78  XOR rs       01111000   AC = AC ^ RAM[rs]
    $30  LI imm       00110000   AC = imm
    $38  MV a0,rs     00111000   AC = RAM[rs]
    $04  MV rd,a0     00000100   RAM[rd] = AC
    $02  BEQ addr     00000010   if Z=1: PC = {PG, addr}
    $82  BNE addr     10000010   if Z=0: PC = {PG, addr}
    $01  J addr       00000001   PC = {PG, addr}
    $20  SETPG imm    00100000   PageReg = imm
    $28  SETPG_R rs   00101000   PageReg = RAM[rs]

    Aliases: LB=$38, SB=$04, HLT=J self, SLL=ADD a0,a0

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
//   U7  = ROM/RAM data (fetch or T2+register)
//   U6  = IRL immediate (T2, SRC=0, STR=0)
//   U14 = AC value (T2, STR=1)
// Consumers (always connected):
//   U12-U13 XOR A-inputs, U23 Page Reg D, U5 IR_HIGH D

IB0 <-> U7-18(B1), U6-19(Q1)*, U14-18(Y1)*, U12-1(A1), U23-2(D1), U5-2(D1)
IB1 <-> U7-17(B2), U6-18(Q2)*, U14-17(Y2)*, U12-4(A2), U23-3(D2), U5-3(D2)
IB2 <-> U7-16(B3), U6-17(Q3)*, U14-16(Y3)*, U12-9(A3), U23-4(D3), U5-4(D3)
IB3 <-> U7-15(B4), U6-16(Q4)*, U14-15(Y4)*, U12-12(A4), U23-5(D4), U5-5(D4)
IB4 <-> U7-14(B5), U6-15(Q5)*, U14-14(Y5)*, U13-1(A1), U23-6(D5), U5-6(D5)
IB5 <-> U7-13(B6), U6-14(Q6)*, U14-13(Y6)*, U13-4(A2), U23-7(D6), U5-7(D6)
IB6 <-> U7-12(B7), U6-13(Q7)*, U14-12(Y7)*, U13-9(A3), U23-8(D7), U5-8(D7)
IB7 <-> U7-11(B8), U6-12(Q8)*, U14-11(Y8)*, U13-12(A4), U23-9(D8), U5-9(D8)

*******************************************
ABUS — Address Bus (A0-A15)
*******************************************
// A0-A7:  from mux U15-U16 (PC low or IRL)
// A8-A15: from mux U29-U30 (PC high or GND)
// Chip select: ROM /CE = NOT(A15), RAM /CE = A15

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

CLK     --> U1-2, U2-2, U3-2, U4-2, U8-8
/RST    --> U1-1, U2-1, U3-1, U4-1, U8-9
ROM /CE <-- /A15 (U24-6)         // enabled when A15=1
RAM /CE <-- A15 (U30-12)         // enabled when A15=0
RAM /WE <-- /AC_BUF (U26-8)     // write pulse during T2+STORE

---

## Chip Wiring

*******************************************
U1-U4 74HC161 ×4 — Program Counter (16-bit)
// Counts during fetch (T0,T1). Loads jump target during T2.
// D[7:0] from IRL (low byte), D[15:8] from Page Register (high byte).
*******************************************

U1-1 (/CLR) --> /RST
U1-2 (CLK)  --> CLK
U1-3 (A)    <-- IRL0 (U6-19)
U1-4 (B)    <-- IRL1 (U6-18)
U1-5 (C)    <-- IRL2 (U6-17)
U1-6 (D)    <-- IRL3 (U6-16)
U1-7 (ENP)  <-- PC_INC (U25-6)
U1-8 (GND)  --> GND
U1-9 (/LD)  <-- /PC_LD (U26-11)
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
U3-3 (A)    <-- PG0 (U23-19)
U3-4 (B)    <-- PG1 (U23-18)
U3-5 (C)    <-- PG2 (U23-17)
U3-6 (D)    <-- PG3 (U23-16)
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
U4-3 (A)    <-- PG4 (U23-15)
U4-4 (B)    <-- PG5 (U23-14)
U4-5 (C)    <-- PG6 (U23-13)
U4-6 (D)    <-- PG7 (U23-12)
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
U5 74HC574 — IR_HIGH (Control Byte Register)
// Latches control byte from IBUS at end of T0.
// Q outputs ARE the control signals (no decode needed).
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
U5-12 (Q8)  --> ALU_SUB (bit7)
U5-13 (Q7)  --> XOR_MODE (bit6)
U5-14 (Q6)  --> MUX_SEL (bit5)
U5-15 (Q5)  --> AC_WR (bit4)
U5-16 (Q4)  --> SOURCE_TYPE (bit3)
U5-17 (Q3)  --> STORE (bit2)
U5-18 (Q2)  --> BRANCH (bit1)
U5-19 (Q1)  --> JUMP (bit0)
U5-20 (VCC) --> VCC

*******************************************
U6 74HC574 — IR_LOW (Operand Register)
// Latches operand from IBUS at end of T1.
// Q outputs go to address mux (always) and IBUS (when /OE=0).
// Also provides jump target to PC D-inputs (U1-U2).
*******************************************

U6-1 (/OE)  <-- /IRL_OE (U26-3)
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
U6-12 (Q8)  --> IRL7 → U16-13, U2-6, IB7*
U6-13 (Q7)  --> IRL6 → U16-10, U2-5, IB6*
U6-14 (Q6)  --> IRL5 → U16-6, U2-4, IB5*
U6-15 (Q5)  --> IRL4 → U16-3, U2-3, IB4*
U6-16 (Q4)  --> IRL3 → U15-13, U1-6, IB3*
U6-17 (Q3)  --> IRL2 → U15-10, U1-5, IB2*
U6-18 (Q2)  --> IRL1 → U15-6, U1-4, IB1*
U6-19 (Q1)  --> IRL0 → U15-3, U1-3, IB0*
U6-20 (VCC) --> VCC
// *IBUS connection active only when /OE=0

*******************************************
U7 74HC245 — Bus Buffer (DBUS ↔ IBUS bridge)
// Bridges external DBUS to internal IBUS.
// DIR: 0=read(D→IB), 1=write(IB→D). Gated by T2+STORE.
// /OE: disabled when IRL drives IBUS (immediate mode).
*******************************************

U7-1 (DIR)  <-- WR_DIR (U28-8)
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
U7-19 (/OE) <-- BUF_OE_N (U24-12)
U7-20 (VCC) --> VCC

*******************************************
U8 74HC164 — Ring Counter (T0, T1, T2 one-hot)
// Generates 3-phase clock: T0→T1→T2→T0...
// Feedback: serial = NOT(Q0) AND NOT(Q1) via internal AND gate.
*******************************************

U8-1 (A)   <-- NOT(Q0) (U24-2)
U8-2 (B)   <-- NOT(Q1) (U24-4)
U8-3 (Q0)  --> T0
U8-4 (Q1)  --> T1
U8-5 (Q2)  --> T2
U8-6 (Q3)  --> NC
U8-7 (GND) --> GND
U8-8 (CLK) --> CLK
U8-9 (/CLR)--> /RST
U8-10..13  --> NC
U8-14(VCC) --> VCC

*******************************************
U9 74HC574 — Accumulator (AC)
// The only real register. Always drives ALU A-input.
// Latches new value from AC input mux at end of T2 (when AC_WR=1).
*******************************************

U9-1 (/OE)  --> GND
U9-2 (D1)   <-- U17-4 (AC mux Y0)
U9-3 (D2)   <-- U17-7 (Y1)
U9-4 (D3)   <-- U17-9 (Y2)
U9-5 (D4)   <-- U17-12 (Y3)
U9-6 (D5)   <-- U18-4 (Y4)
U9-7 (D6)   <-- U18-7 (Y5)
U9-8 (D7)   <-- U18-9 (Y6)
U9-9 (D8)   <-- U18-12 (Y7)
U9-10 (GND) --> GND
U9-11 (CLK) <-- Acc_Load_N (U27-11)
U9-12 (Q8)  --> AC7 → U11-12, U20-13, U14-9, U22-18
U9-13 (Q7)  --> AC6 → U11-14, U20-10, U14-8, U22-16
U9-14 (Q6)  --> AC5 → U11-3, U20-6, U14-7, U22-14
U9-15 (Q5)  --> AC4 → U11-5, U20-3, U14-6, U22-12
U9-16 (Q4)  --> AC3 → U10-12, U19-13, U14-5, U22-8
U9-17 (Q3)  --> AC2 → U10-14, U19-10, U14-4, U22-6
U9-18 (Q2)  --> AC1 → U10-3, U19-6, U14-3, U22-4
U9-19 (Q1)  --> AC0 → U10-5, U19-3, U14-2, U22-2
U9-20 (VCC) --> VCC

*******************************************
U10 74HC283 — ALU Adder Low Nibble (bit 0-3)
// Computes AC[3:0] + XOR_output[3:0] + Cin.
// Cin = ALU_SUB (adds 1 for two's complement subtraction).
*******************************************

U10-5 (A0)  <-- AC0 (U9-19)
U10-3 (A1)  <-- AC1 (U9-18)
U10-14(A2)  <-- AC2 (U9-17)
U10-12(A3)  <-- AC3 (U9-16)
U10-6 (B0)  <-- XOR_Y0 (U12-3)
U10-2 (B1)  <-- XOR_Y1 (U12-6)
U10-15(B2)  <-- XOR_Y2 (U12-8)
U10-11(B3)  <-- XOR_Y3 (U12-11)
U10-7 (Cin) <-- ALU_SUB (U5-12)
U10-4 (S0)  --> SUM0 → U17-2
U10-1 (S1)  --> SUM1 → U17-5
U10-13(S2)  --> SUM2 → U17-11
U10-10(S3)  --> SUM3 → U17-14
U10-9 (Cout)--> U11-7
U10-8 (GND) --> GND
U10-16(VCC) --> VCC

*******************************************
U11 74HC283 — ALU Adder High Nibble (bit 4-7)
// Computes AC[7:4] + XOR_output[7:4] + carry from U10.
*******************************************

U11-5 (A0)  <-- AC4 (U9-15)
U11-3 (A1)  <-- AC5 (U9-14)
U11-14(A2)  <-- AC6 (U9-13)
U11-12(A3)  <-- AC7 (U9-12)
U11-6 (B0)  <-- XOR_Y4 (U13-3)
U11-2 (B1)  <-- XOR_Y5 (U13-6)
U11-15(B2)  <-- XOR_Y6 (U13-8)
U11-11(B3)  <-- XOR_Y7 (U13-11)
U11-7 (Cin) <-- U10-9
U11-4 (S0)  --> SUM4 → U18-2
U11-1 (S1)  --> SUM5 → U18-5
U11-13(S2)  --> SUM6 → U18-11
U11-10(S3)  --> SUM7 → U18-14
U11-9 (Cout)--> NC
U11-8 (GND) --> GND
U11-16(VCC) --> VCC

*******************************************
U12 74HC86 — XOR Low Nibble (bit 0-3)
// A = IBUS (source value). B = mux output (ALU_SUB or AC).
// Output → adder B-input AND AC mux B-input.
// ADD/SUB: B=ALU_SUB → inverts IBUS for subtract.
// XOR instr: B=AC → computes AC XOR IBUS.
*******************************************

U12-1 (A1)  <-- IB0
U12-2 (B1)  <-- U19-4 (XOR_B_mux Y0)
U12-3 (Y1)  --> XOR_Y0 → U10-6, U17-3
U12-4 (A2)  <-- IB1
U12-5 (B2)  <-- U19-7 (Y1)
U12-6 (Y2)  --> XOR_Y1 → U10-2, U17-6
U12-7 (GND) --> GND
U12-8 (Y3)  --> XOR_Y2 → U10-15, U17-10
U12-9 (A3)  <-- IB2
U12-10(B3)  <-- U19-9 (Y2)
U12-11(Y4)  --> XOR_Y3 → U10-11, U17-13
U12-12(A4)  <-- IB3
U12-13(B4)  <-- U19-12 (Y3)
U12-14(VCC) --> VCC

*******************************************
U13 74HC86 — XOR High Nibble (bit 4-7)
// Same as U12 but for bits 4-7.
*******************************************

U13-1 (A1)  <-- IB4
U13-2 (B1)  <-- U20-4 (XOR_B_mux Y4)
U13-3 (Y1)  --> XOR_Y4 → U11-6, U18-3
U13-4 (A2)  <-- IB5
U13-5 (B2)  <-- U20-7 (Y5)
U13-6 (Y2)  --> XOR_Y5 → U11-2, U18-6
U13-7 (GND) --> GND
U13-8 (Y3)  --> XOR_Y6 → U11-15, U18-10
U13-9 (A3)  <-- IB6
U13-10(B3)  <-- U20-9 (Y6)
U13-11(Y4)  --> XOR_Y7 → U11-11, U18-13
U13-12(A4)  <-- IB7
U13-13(B4)  <-- U20-12 (Y7)
U13-14(VCC) --> VCC

*******************************************
U14 74HC541 — AC Output Buffer (AC → IBUS for STORE)
// Puts AC value on IBUS when writing to RAM.
// Enabled only during T2+STORE (/AC_BUF=0).
*******************************************

U14-1 (/OE1)<-- /AC_BUF (U26-8)
U14-2 (A1)  <-- AC0 (U9-19)
U14-3 (A2)  <-- AC1 (U9-18)
U14-4 (A3)  <-- AC2 (U9-17)
U14-5 (A4)  <-- AC3 (U9-16)
U14-6 (A5)  <-- AC4 (U9-15)
U14-7 (A6)  <-- AC5 (U9-14)
U14-8 (A7)  <-- AC6 (U9-13)
U14-9 (A8)  <-- AC7 (U9-12)
U14-10(GND) --> GND
U14-11(Y8)  --> IB7
U14-12(Y7)  --> IB6
U14-13(Y6)  --> IB5
U14-14(Y5)  --> IB4
U14-15(Y4)  --> IB3
U14-16(Y3)  --> IB2
U14-17(Y2)  --> IB1
U14-18(Y1)  --> IB0
U14-19(/OE2)<-- /AC_BUF (U26-8)
U14-20(VCC) --> VCC

*******************************************
U15-U16 74HC157 ×2 — Address Mux A0-A7 (PC vs IRL)
// SEL=0 (fetch): PC[7:0] → ABUS A0-A7
// SEL=1 (T2 data): IRL[7:0] → ABUS A0-A7
*******************************************

U15-1 (SEL) <-- ADDR_MODE (U25-3)
U15-2 (1A)  <-- PC0 (U1-14)    U15-3 (1B) <-- IRL0 (U6-19)    U15-4 (1Y) --> A0
U15-5 (2A)  <-- PC1 (U1-13)    U15-6 (2B) <-- IRL1 (U6-18)    U15-7 (2Y) --> A1
U15-11(3A)  <-- PC2 (U1-12)    U15-10(3B) <-- IRL2 (U6-17)    U15-9 (3Y) --> A2
U15-14(4A)  <-- PC3 (U1-11)    U15-13(4B) <-- IRL3 (U6-16)    U15-12(4Y) --> A3
U15-8 (GND) --> GND    U15-15(/E) --> GND    U15-16(VCC) --> VCC

U16-1 (SEL) <-- ADDR_MODE
U16-2 (1A)  <-- PC4 (U2-14)    U16-3 (1B) <-- IRL4 (U6-15)    U16-4 (1Y) --> A4
U16-5 (2A)  <-- PC5 (U2-13)    U16-6 (2B) <-- IRL5 (U6-14)    U16-7 (2Y) --> A5
U16-11(3A)  <-- PC6 (U2-12)    U16-10(3B) <-- IRL6 (U6-13)    U16-9 (3Y) --> A6
U16-14(4A)  <-- PC7 (U2-11)    U16-13(4B) <-- IRL7 (U6-12)    U16-12(4Y) --> A7
U16-8 (GND) --> GND    U16-15(/E) --> GND    U16-16(VCC) --> VCC

*******************************************
U17-U18 74HC157 ×2 — AC Input Mux (Adder vs XOR output)
// SEL=0 (MUX_SEL=0): Adder SUM → AC (ADD/SUB)
// SEL=1 (MUX_SEL=1): XOR output → AC (LI/MV/XOR)
// XOR output = IBUS when XOR_MODE=0 (passthrough for LI/MV)
// XOR output = AC^IBUS when XOR_MODE=1 (XOR instruction)
*******************************************

U17-1 (SEL) <-- MUX_SEL (U5-14)
U17-2 (1A)  <-- SUM0 (U10-4)   U17-3 (1B) <-- XOR_Y0 (U12-3)  U17-4 (1Y) --> AC D0 (U9-2)
U17-5 (2A)  <-- SUM1 (U10-1)   U17-6 (2B) <-- XOR_Y1 (U12-6)  U17-7 (2Y) --> AC D1 (U9-3)
U17-11(3A)  <-- SUM2 (U10-13)  U17-10(3B) <-- XOR_Y2 (U12-8)  U17-9 (3Y) --> AC D2 (U9-4)
U17-14(4A)  <-- SUM3 (U10-10)  U17-13(4B) <-- XOR_Y3 (U12-11) U17-12(4Y) --> AC D3 (U9-5)
U17-8 (GND) --> GND    U17-15(/E) --> GND    U17-16(VCC) --> VCC

U18-1 (SEL) <-- MUX_SEL (U5-14)
U18-2 (1A)  <-- SUM4 (U11-4)   U18-3 (1B) <-- XOR_Y4 (U13-3)  U18-4 (1Y) --> AC D4 (U9-6)
U18-5 (2A)  <-- SUM5 (U11-1)   U18-6 (2B) <-- XOR_Y5 (U13-6)  U18-7 (2Y) --> AC D5 (U9-7)
U18-11(3A)  <-- SUM6 (U11-13)  U18-10(3B) <-- XOR_Y6 (U13-8)  U18-9 (3Y) --> AC D6 (U9-8)
U18-14(4A)  <-- SUM7 (U11-10)  U18-13(4B) <-- XOR_Y7 (U13-11) U18-12(4Y) --> AC D7 (U9-9)
U18-8 (GND) --> GND    U18-15(/E) --> GND    U18-16(VCC) --> VCC

*******************************************
U19-U20 74HC157 ×2 — XOR B-input Mux (ALU_SUB vs AC)
// SEL=0 (XOR_MODE=0): ALU_SUB → XOR B (for ADD: pass, SUB: invert)
// SEL=1 (XOR_MODE=1): AC bits → XOR B (for XOR instruction)
*******************************************

U19-1 (SEL) <-- XOR_MODE (U5-13)
U19-2 (1A)  <-- ALU_SUB(U5-12) U19-3 (1B) <-- AC0(U9-19) U19-4 (1Y) --> U12-2
U19-5 (2A)  <-- ALU_SUB        U19-6 (2B) <-- AC1(U9-18) U19-7 (2Y) --> U12-5
U19-11(3A)  <-- ALU_SUB        U19-10(3B) <-- AC2(U9-17) U19-9 (3Y) --> U12-10
U19-14(4A)  <-- ALU_SUB        U19-13(4B) <-- AC3(U9-16) U19-12(4Y) --> U12-13
U19-8 (GND) --> GND    U19-15(/E) --> GND    U19-16(VCC) --> VCC

U20-1 (SEL) <-- XOR_MODE (U5-13)
U20-2 (1A)  <-- ALU_SUB(U5-12) U20-3 (1B) <-- AC4(U9-15) U20-4 (1Y) --> U13-2
U20-5 (2A)  <-- ALU_SUB        U20-6 (2B) <-- AC5(U9-14) U20-7 (2Y) --> U13-5
U20-11(3A)  <-- ALU_SUB        U20-10(3B) <-- AC6(U9-13) U20-9 (3Y) --> U13-10
U20-14(4A)  <-- ALU_SUB        U20-13(4B) <-- AC7(U9-12) U20-12(4Y) --> U13-13
U20-8 (GND) --> GND    U20-15(/E) --> GND    U20-16(VCC) --> VCC

*******************************************
U21 74HC74 — Z Flag Register
// Stores zero flag. Z=1 when AC=0.
// Uses /PR trick: U22 forces Z=1 when AC=0 (async preset).
// When AC≠0: rising edge of Acc_Load_N latches D=GND → Z=0.
*******************************************

U21-1 (/CLR1)--> VCC
U21-2 (D1)   --> GND
U21-3 (CLK1) <-- Acc_Load_N (U27-11)
U21-4 (/PR1) <-- U22-19 (/P=Q)
U21-5 (Q1)   --> Z_flag → U28-1
U21-6 (/Q1)  --> NC
U21-7 (GND)  --> GND
U21-8..14    --> FF2 unused (CLK2=GND, /PR2=VCC, /CLR2=VCC, D2=GND)
U21-14(VCC)  --> VCC

*******************************************
U22 74HC688 — Zero Detect (AC == 0?)
// Compares AC with $00. /P=Q output LOW when all bits match.
*******************************************

U22-1 (/OE) --> GND
U22-2 (P0)  <-- AC0(U9-19)   U22-3 (Q0) --> GND
U22-4 (P1)  <-- AC1(U9-18)   U22-5 (Q1) --> GND
U22-6 (P2)  <-- AC2(U9-17)   U22-7 (Q2) --> GND
U22-8 (P3)  <-- AC3(U9-16)   U22-9 (Q3) --> GND
U22-10(GND) --> GND
U22-11(Q4)  --> GND           U22-12(P4) <-- AC4(U9-15)
U22-13(Q5)  --> GND           U22-14(P5) <-- AC5(U9-14)
U22-15(Q6)  --> GND           U22-16(P6) <-- AC6(U9-13)
U22-17(Q7)  --> GND           U22-18(P7) <-- AC7(U9-12)
U22-19(/P=Q)--> U21-4 (/PR1)
U22-20(VCC) --> VCC

*******************************************
U23 74HC574 — Page Register (Jump High Byte)
// Stores high byte for 16-bit jump target.
// Latches from IBUS when SETPG executes (MUX_SEL=1, AC_WR=0).
// Q outputs provide PC D[15:8] for jump/branch.
*******************************************

U23-1 (/OE) --> GND
U23-2 (D1)  <-- IB0
U23-3 (D2)  <-- IB1
U23-4 (D3)  <-- IB2
U23-5 (D4)  <-- IB3
U23-6 (D5)  <-- IB4
U23-7 (D6)  <-- IB5
U23-8 (D7)  <-- IB6
U23-9 (D8)  <-- IB7
U23-10(GND) --> GND
U23-11(CLK) <-- PG_Load_N (U25-13)
U23-12(Q8)  --> PG7 → U4-6
U23-13(Q7)  --> PG6 → U4-5
U23-14(Q6)  --> PG5 → U4-4
U23-15(Q5)  --> PG4 → U4-3
U23-16(Q4)  --> PG3 → U3-6
U23-17(Q3)  --> PG2 → U3-5
U23-18(Q2)  --> PG1 → U3-4
U23-19(Q1)  --> PG0 → U3-3
U23-20(VCC) --> VCC

*******************************************
U24 74HC04 — Inverters (6 gates)
// Ring counter feedback + control signal inversions.
*******************************************

U24-1 (1A)  <-- T0 (U8-3)          U24-2 (1Y) --> NOT(Q0) → U8-1
U24-3 (2A)  <-- T1 (U8-4)          U24-4 (2Y) --> NOT(Q1) → U8-2
U24-5 (3A)  <-- A15 (U30-12)       U24-6 (3Y) --> /A15 → ROM /CE
U24-7 (GND) --> GND
U24-9 (4A)  <-- JUMP (U5-19)       U24-8 (4Y) --> /JUMP → U27-4
U24-11(5A)  <-- AC_WR (U5-15)      U24-10(5Y) --> /AC_WR → U27-10
U24-13(6A)  <-- /IRL_OE (U26-3)    U24-12(6Y) --> BUF_OE_N → U7-19
U24-14(VCC) --> VCC

*******************************************
U25 74HC32 — OR Gates (4 gates)
// Derived control signals.
*******************************************

U25-1 (1A)  <-- SOURCE_TYPE(U5-16)  U25-2(1B) <-- STORE(U5-17)   U25-3(1Y) --> ADDR_MODE
U25-4 (2A)  <-- T0 (U8-3)           U25-5(2B) <-- T1 (U8-4)      U25-6(2Y) --> PC_INC
U25-7 (GND) --> GND
U25-9 (3A)  <-- JUMP (U5-19)        U25-10(3B)<-- BRANCH(U5-18)  U25-8(3Y) --> J_OR_B (spare)
U25-11(4A)  <-- /T2 (U28-6)         U25-12(4B)<-- /PG_cond(U27-8) U25-13(4Y)--> PG_Load_N → U23-11
U25-14(VCC) --> VCC

// ADDR_MODE → U15-1, U16-1, U29-1, U30-1, U26-4, U26-5
// PC_INC → U1-7, U1-10, U2-7, U3-7, U4-7

*******************************************
U26 74HC00 — NAND Gates #1 (4 gates)
// IBUS driver control + PC load.
*******************************************

// Gate A: /IRL_OE — enables IRL on IBUS during T2 immediate mode
U26-1 (1A) <-- T2 (U8-5)
U26-2 (1B) <-- /ADDR_MODE (U26-6)
U26-3 (1Y) --> /IRL_OE → U6-1, U24-13

// Gate B: /ADDR_MODE = NOT(ADDR_MODE) — used by gate A
U26-4 (2A) <-- ADDR_MODE (U25-3)
U26-5 (2B) <-- ADDR_MODE (U25-3)
U26-6 (2Y) --> /ADDR_MODE → U26-2

// Gate C: /AC_BUF — enables AC buffer + RAM write during T2+STORE
U26-9 (3A) <-- T2 (U8-5)
U26-10(3B) <-- STORE (U5-17)
U26-8 (3Y) --> /AC_BUF → U14-1, U14-19, RAM /WE, U28-9

// Gate D: /PC_LD — loads PC during T2 when jump/branch taken
U26-12(4A) <-- T2 (U8-5)
U26-13(4B) <-- PC_LOAD_COND (U27-6)
U26-11(4Y) --> /PC_LD → U1-9, U2-9, U3-9, U4-9

U26-7 (GND)--> GND    U26-14(VCC)--> VCC

*******************************************
U27 74HC00 — NAND Gates #2 (4 gates)
// Branch logic + page register + accumulator clock.
*******************************************

// Gate A: /BR_TAKEN = NAND(BRANCH, Z_match)
U27-1 (1A) <-- BRANCH (U5-18)
U27-2 (1B) <-- Z_match (U28-3)
U27-3 (1Y) --> /BR_TAKEN → U27-5

// Gate B: PC_LOAD_COND = NAND(/JUMP, /BR_TAKEN) = JUMP OR BR_TAKEN
U27-4 (2A) <-- /JUMP (U24-8)
U27-5 (2B) <-- /BR_TAKEN (U27-3)
U27-6 (2Y) --> PC_LOAD_COND → U26-13

// Gate C: /PG_cond = NAND(MUX_SEL, /AC_WR) — LOW when SETPG
U27-9 (3A) <-- MUX_SEL (U5-14)
U27-10(3B) <-- /AC_WR (U24-10)
U27-8 (3Y) --> /PG_cond → U25-12

// Gate D: Acc_Load_N = NAND(T2, AC_WR) — AC+Z latch clock
U27-12(4A) <-- T2 (U8-5)
U27-13(4B) <-- AC_WR (U5-15)
U27-11(4Y) --> Acc_Load_N → U9-11, U21-3

U27-7 (GND)--> GND    U27-14(VCC)--> VCC

*******************************************
U28 74HC86 — XOR Gates (4 gates, 2 used)
// Branch condition + timing + bus direction.
*******************************************

// Gate A: Z_match = Z_flag XOR ALU_SUB (BEQ: Z=1, BNE: Z=0)
U28-1 (1A) <-- Z_flag (U21-5)
U28-2 (1B) <-- ALU_SUB (U5-12)
U28-3 (1Y) --> Z_match → U27-2

// Gate B: /T2 = NOT(T2) — for PG_Load timing
U28-4 (2A) <-- T2 (U8-5)
U28-5 (2B) --> VCC
U28-6 (2Y) --> /T2 → U25-11

// Gate C: WR_DIR = NOT(/AC_BUF) = T2 AND STORE — U7 write direction
U28-9 (3A) <-- /AC_BUF (U26-8)
U28-10(3B) --> VCC
U28-8 (3Y) --> WR_DIR → U7-1

// Gate D: spare
U28-12(4A) --> NC    U28-13(4B) --> NC    U28-11(4Y) --> NC

U28-7 (GND)--> GND    U28-14(VCC)--> VCC

*******************************************
U29-U30 74HC157 ×2 — Address Mux A8-A15 (PC high vs GND)
// SEL=0 (fetch): PC[15:8] → ABUS A8-A15 (full 64K)
// SEL=1 (T2 data): GND → ABUS A8-A15 (data at $00xx)
// Expansion: replace GND with bank register for >256B RAM
*******************************************

U29-1 (SEL) <-- ADDR_MODE (U25-3)
U29-2 (1A)  <-- PC8 (U3-14)    U29-3 (1B) --> GND    U29-4 (1Y) --> A8
U29-5 (2A)  <-- PC9 (U3-13)    U29-6 (2B) --> GND    U29-7 (2Y) --> A9
U29-11(3A)  <-- PC10(U3-12)    U29-10(3B) --> GND    U29-9 (3Y) --> A10
U29-14(4A)  <-- PC11(U3-11)    U29-13(4B) --> GND    U29-12(4Y) --> A11
U29-8 (GND) --> GND    U29-15(/E) --> GND    U29-16(VCC) --> VCC

U30-1 (SEL) <-- ADDR_MODE (U25-3)
U30-2 (1A)  <-- PC12(U4-14)    U30-3 (1B) --> GND    U30-4 (1Y) --> A12
U30-5 (2A)  <-- PC13(U4-13)    U30-6 (2B) --> GND    U30-7 (2Y) --> A13
U30-11(3A)  <-- PC14(U4-12)    U30-10(3B) --> GND    U30-9 (3Y) --> A14
U30-14(4A)  <-- PC15(U4-11)    U30-13(4B) --> GND    U30-12(4Y) --> A15 → RAM /CE, U24-5
U30-8 (GND) --> GND    U30-15(/E) --> GND    U30-16(VCC) --> VCC

*******************************************
ROM — SST39SF010A (128KB Flash)
// Program storage. Visible at $8000-$FFFF.
// A16 optional: bank switch via expansion board for 128KB.
*******************************************

ROM A0-A7  <-- ABUS A0-A7
ROM A8-A14 <-- ABUS A8-A14
ROM A15    --> NC (or expansion A16)
ROM A16    --> GND (or expansion bank latch)
ROM D0-D7  --> DBUS
ROM /CE    <-- /A15 (U24-6)
ROM /OE    --> GND
ROM /WE    --> VCC

*******************************************
RAM — 62256 (32KB SRAM)
// Data + registers at $0000-$7FFF. Can execute code.
// During T2 data access: address = $00xx (A8-A15 = GND from mux).
// During fetch: full A0-A14 from PC (if PC < $8000).
*******************************************

RAM A0-A7  <-- ABUS A0-A7
RAM A8-A14 <-- ABUS A8-A14
RAM D0-D7  <-> DBUS
RAM /CE    <-- A15 (U30-12)
RAM /OE    --> GND
RAM /WE    <-- /AC_BUF (U26-8)

---

## ISA Decode Verification (all 15 instructions)

| Instr | IBUS | XOR B-mux | AC mux | Result | Bus |
|-------|------|-----------|--------|--------|:---:|
| NOP $00 | IRL* | SUB=0→pass | — | no write | ✓ |
| ADDI $10 | IRL | SUB=0→pass | A(adder) | AC+imm | ✓ |
| ADD $18 | RAM | SUB=0→pass | A(adder) | AC+RAM | ✓ |
| SUBI $90 | IRL | SUB=1→inv | A(adder) | AC-imm | ✓ |
| SUB $98 | RAM | SUB=1→inv | A(adder) | AC-RAM | ✓ |
| XORI $70 | IRL | AC bits | B(XOR) | AC^imm | ✓ |
| XOR $78 | RAM | AC bits | B(XOR) | AC^RAM | ✓ |
| LI $30 | IRL | SUB=0→pass | B(=IBUS) | imm | ✓ |
| MV a0 $38 | RAM | SUB=0→pass | B(=IBUS) | RAM[rs] | ✓ |
| MV rd $04 | AC buf | — | — | RAM←AC | ✓ |
| BEQ $02 | IRL* | — | — | PC load if Z | ✓ |
| BNE $82 | IRL* | — | — | PC load if !Z | ✓ |
| J $01 | IRL* | — | — | PC load | ✓ |
| SETPG $20 | IRL | — | — | PG←IBUS | ✓ |
| SETPG_R $28| RAM | — | — | PG←IBUS | ✓ |

*IRL drives IBUS but AC_WR=0, harmless. No bus conflicts. ✓

---

## Simulation

```bash
cd RV8GR
iverilog -o tb/sim_full.vvp rv8gr_cpu.v tb/tb_rv8gr_full.v
vvp tb/sim_full.vvp
# === ALL TESTS PASSED === (127 cycles)
gtkwave rv8gr_test.vcd
```
