# RV8-GR — Design Document

**21 logic chips. No microcode. Reduced ISA. Cheapest that plays games.**

---

## Architecture

- Accumulator (AC) hardwired to ALU A
- Registers in RAM ($00-$07)
- 3-cycle execution (fetch control, fetch operand, execute)
- Control byte bits directly drive hardware (no lookup table)
- 8-bit parallel ALU (adder + XOR)
- SST39SF010A program ROM (8-bit, 70ns)

## Chip List (21 logic) จาก Design เดิม

| U# | Chip | Function |
|:--:|------|----------|
| U1 | 74HC574 | AC (accumulator) |
| U2 | 74HC574 | IR_HIGH (control byte) |
| U3-U4 | 74HC283 ×2 | ALU adder (8-bit) |
| U5-U6 | 74HC86 ×2 | XOR (SUB + XOR instruction) |
| U7 | 74HC157 | Address mux A[7:4] |
| U8 | 74HC574 | IR_LOW (operand) |
| U9 | 74HC541 | AC → IBUS buffer |
| U10 | 74HC245 | Bus buffer (IBUS ↔ RAM) |
| U11-U12 | 74HC157 ×2 | AC D-input mux |
| U13 | 74HC157 | Address mux A[3:0] |
| U14 | 74HC161 | State counter (3 states) |
| U15-U18 | 74HC161 ×4 | PC (16-bit) |
| U19 | 74HC541 | PC → IBUS buffer (JAL) |
| U20 | 74HC74 | Flags (Z) |
| U21 | 74HC32 | OR gates (derived signals) |
| — | SST39SF010A | Program ROM |
| — | 62256 | RAM (registers + data) |


## Encoding (2 bytes per instruction)

### Byte 0 — Control (8 bits, drives hardware):
```
Bit 7: ALU_SUB      0=ADD, 1=SUB
Bit 6: XOR_MODE     1=XOR result → AC
Bit 5: MUX_SEL      0=ALU→AC, 1=IBUS→AC
Bit 4: AC_WR        1=write to AC
Bit 3: SOURCE_TYPE  0=immediate, 1=register(RAM)
Bit 2: STORE        1=write AC to RAM
Bit 1: BRANCH       1=conditional jump
Bit 0: JUMP         1=unconditional jump
```
### Byte 1 — Operand (8 bits):
- Immediate value (0-255) when SOURCE_TYPE=0
- Register/memory address when SOURCE_TYPE=1 or STORE=1
- Branch/jump target address when BRANCH=1 or JUMP=1

## Instructions

### ALU (AC = AC op source)

| Control byte | Mnemonic | Operation |
|:------------:|----------|-----------|
| $18 | `ADD a0, a0, rs` | AC = AC + RAM[rs] |
| $98 | `SUB a0, a0, rs` | AC = AC - RAM[rs] |
| $48 | `XOR a0, a0, rs` | AC = AC ^ RAM[rs] |
| $10 | `ADDI a0, a0, imm` | AC = AC + imm |
| $90 | `SUBI a0, a0, imm` | AC = AC - imm |
| $50 | `XORI a0, a0, imm` | AC = AC ^ imm |
| $10 | `SLL a0, a0, 1` | AC = AC + AC (shift left, use ADDI with self... actually ADD a0,a0) |

### Load/Move

| Control byte | Mnemonic | Operation |
|:------------:|----------|-----------|
| $30 | `LI a0, imm` | AC = imm (MUX_SEL=1, AC_WR=1) |
| $38 | `MV a0, rs` | AC = RAM[rs] (MUX_SEL=1, SOURCE=1, AC_WR=1) |
| $04 | `MV rd, a0` | RAM[rd] = AC (STORE=1) |
| $3C | `LB a0, addr` | AC = RAM[addr] (MUX_SEL=1, SOURCE=1, AC_WR=1) |
| $04 | `SB a0, addr` | RAM[addr] = AC (STORE=1) |

### Branch/Jump

| Control byte | Mnemonic | Operation |
|:------------:|----------|-----------|
| $02 | `BEQ a0, zero, addr` | if Z=1, PC = addr |
| $82 | `BNE a0, zero, addr` | if Z=0, PC = addr (SUB bit as invert) |
| $01 | `J addr` | PC = addr |
| $11 | `JAL ra, addr` | RAM[$07]=PC, PC = addr (AC_WR saves PC... needs work) |

### System

| Control byte | Mnemonic | Operation |
|:------------:|----------|-----------|
| $00 | `NOP` | nothing |
| $01 | `HLT` | PC = same address (loop) |

---

## What's missing vs RV8:

| RV8 instruction | RV8-GR | Workaround |
|-----------------|:------:|-----------|
| AND/ANDI | ❌ | Subroutine (~20 instr) |
| OR/ORI | ❌ | Subroutine (~25 instr) |
| SRL (shift right) | ❌ | Subroutine (~15 instr) |
| SLT/SLTI | ❌ | SUB + check Z |
| BLT/BGE | ❌ | SUB + BEQ/BNE |
| Relative branch | ❌ | Absolute address (assembler resolves) |
| BEQ rs1,rs2 | ❌ | SUB rs1,rs2 then BEQ |


RV8_Bus:{
    "A[15:0]": "From PC (fetch) or operand (register/memory access)",
    "D[7:0]":  "ROM data out / RAM data ↔ U10 (245 bridge) ↔ IBUS",
    "/RD":     "From IR_HIGH control bit → ROM./OE + RAM./OE",
    "/WR":     "From IR_HIGH control bit → RAM./WE",
    CLK:       "Crystal oscillator",
    "/RST":    "10K pull-up + 100nF + pushbutton",
    "/IRQ":    "10K pull-up (active low, directly to state logic)",
    SYNC:      "State=0 (new instruction starting)",

    pinout: {
        "1-8":   "A[7:0]",
        "9-16":  "A[15:8]",
        "17-24": "D[7:0]",
        25:"/RD", 26:"/WR", 27:"CLK", 28:"/RST",
        29:"/NMI", 30:"/IRQ", 31:"HALT", 32:"SYNC",
        "33-38":"reserved", 39:"VCC", 40:"GND"}
},

// ═══════════════════════════════════════════════════════════════
// IBUS (INTERNAL) — 8-bit, connects AC buffer + bus bridge + ALU B
// ═══════════════════════════════════════════════════════════════

IBUS:{
    width: 8,
    drivers: [
        "U10 (245 bus bridge, when reading RAM → IBUS)",
        "U9 (541 AC buffer, when AC_TO_BUS=1)"
    ],
    consumers: [
        "U5-U6 (XOR chips, ALU B input via XOR)",
        "U10 (245 bus bridge, when writing IBUS → RAM)",
        "U1 (AC D-input, via mux: ALU result or IBUS)"
    ],
    rule: "Only one driver at a time. Controlled by IR_HIGH bits."
},


## 4 Modules

```
┌──────────────────────────────────────────────────┐
│  Module 1: AC + ALU (U1, U3-U6, U11-U12)        │
│  Module 2: PC + Address (U7, U13-U18, U21)       │
│  Module 3: Memory Interface (U9, U10, U19)        │
│  Module 4: Instruction + State (U2, U8, U14, U20)│
└──────────────────────────────────────────────────┘
```

## Module 1: AC + ALU (the calculator)

**Chips**: U1 (574 AC) + U3-U4 (283 adder) + U5-U6 (86 XOR) + U11-U12 (157 mux)

AC is the ONLY real register. Its Q outputs are hardwired to adder A inputs (always computing). The mux (U11-U12) selects what goes into AC: adder result, XOR result, or IBUS data.

## Module 2: PC + Address (the navigator)

**Chips**: U7+U13 (157 addr mux) + U14 (161 state counter) + U15-U18 (161 PC) + U21 (32 OR gates)

PC auto-increments during fetch. Address mux selects PC (fetch) or operand (data access). State counter cycles 0→1→2→0 (3 states per instruction).

## Module 3: Memory Interface (the bridge)

**Chips**: U9 (541 AC buffer) + U10 (245 bus bridge) + U19 (541 PC buffer)

U10 bridges IBUS to RAM data bus. U9 puts AC value on IBUS (for store). U19 puts PC value on IBUS (for JAL).

## Module 4: Instruction + State (the controller)

**Chips**: U2 (574 IR_HIGH) + U8 (574 IR_LOW) + U14 (161 state) + U20 (74 flags)

IR_HIGH holds the control byte — its Q outputs ARE the control signals. No decode needed! U8 holds the operand. U14 counts states. U20 remembers if last result was zero (for branches).

---

## How `ADDI a0, a0, 5` executes:

```
State 0: PC→ROM→$10 (control byte)→U2 latches. PC++.
State 1: PC→ROM→$05 (operand)→U8 latches. PC++.
State 2: U2 says: AC_WR=1, SOURCE=imm, SUB=0
          IBUS = $05 (from U8, immediate)
          ALU: AC($10) + IBUS($05) = $15
          Mux selects adder result → AC latches $15. Done!
```

**3 clocks. No microcode. No lookup. Just wires.**

จาก RV8_Bus ประกอบด้วย 
Address (A0-A15)
Data (D0-D7)
Control 
    RD (read), WR (write), CLK (clock), RST (Reset)
    NMI (non-maskable interrupt)
    IRQ (interrupt request)
    HALT (halt)
    SYNC (instruction sync)

IBUS (internal bus)ประกอบด้วย
    IA0 - IA15
    /I_LD (Load address to PC )
    /I_PCINC (Enable PC)
    I_RH_Load register H Load
    I_RL_Load register L Load
    
    Drivers และ Consumers
    IB0-IB7
    
    
Rom SST39SF010A ต่อ A01A14, D0-D7
    ROM (/CE) -->A15
    ROM (/OE) -->/RD
    ROM (/WE) -->Vcc
    Vcc --> ROM /WE //เก็บไว้สำหรับ ต่อกับ programmer)หรือไปเพิ่ม Rom Write enable บน bus

Ram 64256 ต่อ A0-A14, D0-D7
    Ram.20 (/CS) --> 74hc04 --> A15
    Ram.22 (/OE) --> /RD
    Ram.27 (/WE) --> /WR

*******************************************
PC (Program Counter) 16 bit
*******************************************

74hc161 4 ตัว U1-U4 (เดิม U15-U18 )

U1-1 (/CLR) --> /RST
U1-2 (CLK)  --> CLK
U1-3 (A)    --> IA0  //pc address
U1-4 (B)    --> IA1
U1-5 (C)    --> IA2
U1-6 (D)    --> IA3
U1-7 (ENP)  --> I_PCINC
U1-8 (GND)  --> GND
U1-9 (/LD)  --> /I_LD //Load pc address
U1-10 (ENT) --> I_PCINC
U1-11 (QD)  --> A3
U1-12 (QC)  --> A2
U1-13 (QB)  --> A1
U1-14 (QA)  --> A0
U1-15 (RC0) --> U2-10(ENT)
U1-16 (VCC) --> VCC

U2-1 (/CLR) --> /RST
U2-2 (CLK)  --> CLK
U2-3 (A)    --> IA4
U2-4 (B)    --> IA5
U2-5 (C)    --> IA6
U2-6 (D)    --> IA7
U2-7 (ENP)  --> I_PCINC
U2-8 (GND)  --> GND
U2-9 (/LD)  --> /I_LD
U2-10 (ENT) --> From U1-15 (RC0)
U2-11 (QD)  --> A7
U2-12 (QC)  --> A6
U2-13 (QB)  --> A5
U2-14 (QA)  --> A4
U2-15 (RC0) --> U3-10 (ENT)
U2-16 (VCC) --> VCC
    
U3-1 (/CLR) --> /RST
U3-2 (CLK)  --> CLK
U3-3 (A)    --> IA8
U3-4 (B)    --> IA9
U3-5 (C)    --> IA10
U3-6 (D)    --> IA11
U3-7 (ENP)  --> I_PCINC
U3-8 (GND)  --> GND
U3-9 (/LD)  --> /I_LD
U3-10 (ENT) --> From U2-15 (RC0)
U3-11 (QD)  --> A11
U3-12 (QC)  --> A10
U3-13 (QB)  --> A9
U3-14 (QA)  --> A8
U3-15 (RC0) --> U4-10 (ENT)
U3-16 (VCC) --> VCC

U4-1 (/CLR) --> /RST
U4-2 (CLK)  --> CLK
U4-3 (A)    --> IA12
U4-4 (B)    --> IA13
U4-5 (C)    --> IA14
U4-6 (D)    --> IA15
U4-7 (ENP)  --> I_PCINC
U4-8 (GND)  --> GND
U4-9 (/LD)  --> /I_LD
U4-10 (ENT) --> From U3-15 (RC0)
U4-11 (QD)  --> A15
U4-12 (QC)  --> A14
U4-13 (QB)  --> A13
U4-14 (QA)  --> A12
U4-15 (RC0) --> NC // Not Connected
U4-16 (VCC) --> VCC

****************** จากจุดนี้สามารถทดลอง PC ได้โดยป้อน clock หรือ switch ทดสอบอ่านค่าจาก rom ได้


intruction register
T0 fetch opcode 
 pc ชี้ไปคำสั่ง 
 rom ส่ง byte แรกไป data bus
 โหลดเข้า u5 (I_RH)
 pc_inc = 1

 T1 fetch operand
 pc ชี้ไป byte 2
 rom ส่ง byte 2 (operand) ไป data bus
 โหลดเข้า u6 (I_RL)
 pc_inc = 1

 t2 execute 
 ใช้ข้อมูลจาก i_rh และ i_rl ไปทำงาน

 

U5, U6 74hc574  (U2, U8 เดิม)
***********************************
U5 74HC574 I_RH Control Byte (U2 เดิม)
**********************************
U5-1 (/OE)   --> GND //หรือ output enable
U5-2 (D1)    --> ID0
U5-3 (D2)    --> ID1
U5-4 (D3)    --> ID2
U5-5 (D4)    --> ID3
U5-6 (D5)    --> ID4
U5-7 (D6)    --> ID5
U5-8 (D7)    --> ID6
U5-9 (D8)    --> ID7
U5-10 (GND)  --> GND
U5-11 (CLK)  --> I_RH_Load
U5-12 (Q8)   --> IRH7
U5-13 (Q7)   --> IRH6
U5-14 (Q6)   --> IRH5
U5-15 (Q5)   --> IRH4
U5-16 (Q4)   --> IRH3
U5-17 (Q3)   --> IRH2
U5-18 (Q2)   --> IRH1
U5-19 (Q1)   --> IRH0
U5-20 (VCC)  --> Vcc

***************************************
U6 74HC547 I_RL Operand (U8 เดิม)
**************************************
U6-1 (/OE)   --> GND  //หรือต่อ output enable
U6-2 (D1)    --> ID0
U6-3 (D2)    --> ID1
U6-4 (D3)    --> ID2
U6-5 (D4)    --> ID3
U6-6 (D5)    --> ID4
U6-7 (D6)    --> ID5
U6-8 (D7)    --> ID6
U6-9 (D8)    --> ID7
U6-10 (GND)  --> GND
U6-11 (CLK)  --> I_RL_Load
U6-12 (Q8)   --> IRL7
U6-13 (Q7)   --> IRL6
U6-14 (Q6)   --> IRL5
U6-15 (Q5)   --> IRL4
U6-16 (Q4)   --> IRL3
U6-17 (Q3)   --> IRL2
U6-18 (Q2)   --> IRL1
U6-19 (Q1)   --> IRL0
U6-20 (VCC)  --> Vcc

U7-1 (DIR)   --> Vcc for test (D-->ID)
U7-2 (A1)    --> D0 RV8-bus
U7-3 (A2)    --> D1
U7-4 (A3)    --> D2
U7-5 (A4)    --> D3
U7-6 (A5)    --> D4
U7-7 (A6)    --> D5
U7-8 (A7)    --> D6
U7-9 (A8)    --> D7
U7-10 (GND)  --> GND
U7-11 (B8)   --> ID7
U7-12 (B7)   --> ID6
U7-13 (B6)   --> ID5
U7-14 (B5)   --> ID4
U7-15 (B4)   --> ID3
U7-16 (B3)   --> ID2
U7-17 (B2)   --> ID1
U7-18 (B1)   --> ID0
U7-19 (/EN)  --> GND // Always enable
U7-20 (Vcc)  --> Vcc

ทดสอบโดย 
เซ็ตอัพ
1 rom เก็บค่า 12--> adr 0000h, 34 --> adr 0001h
2 ต่อ led output ที่ U5 (IRH) q1-q8 (pin19-12)
3 ต่อ led output ที่ u6 (IRL) q1-q8 (pin19-12)
4 reset pc 0000h
5 u7-1(dir)->vcc (d-->id)
6 u7-19(/en) -> gnd (enable)
7 u5-1(/oe) ->gnd
8 u6-1(/oe)-->gnd
9 rom /rd -->gnd อ่าน
ทดสอบ
1 reset pc 0000h
2 rom จะแสดง 12h ที่ d0-d7
3 irh_load U5-12 --> pulse
4 irh จะได้ 12h (00010010)

5 PC_INC --> Vcc แล้ว CLK 1 pulse
6 PC จะเปลี่ยนเป็น 0001h
7 rom จะแสดง 34h ที่ d0-d7

8 irl_load U6-12 --> pulse
9 irl จะได้ 34

10 IRH 12h, IRL 34h

U8 74HC161
U8-1 (/CLR)   --> U9-3 (reset state T0-T2 กลับเป็น T0)
U8-2 (CLK)    --> CLK (system)
U8-3 (A)      ---> GND
U8-4 (B)      ---> GND
U8-5 (C)      ---> GND
U8-6 (D)      ---> GND
U8-7 (ENP)    --> Vcc (Enable)
U8-8 (GND)    --> GND
U8-9 (/LD)    --> Vcc (Not Load)
U8-10 (ENT)   --> Vcc (Enable)
U8-11 (QD)    -->   State bit3  NC
U8-12 (QC)    -->   State bit 2 NC
U8-13 (QB)    -->   State bit 1 --> U11-9/
U8-14 (QA)    -->   State bit 0 --> U11-5 
U8-15 (RC0)   --> NC
U8-16 (Vcc)   --> Vcc

State (QB,QA) ใช้ QB, QA 2 bit สำหรับ 3 state
   00   T0
   01   T1
   10   T2
   11   Reset --> ต่อ QB, QA กับ nand U-9 74hc00 --> U8-1 (/CLR)

U9 74HC00 nand (ABCD)

// สร้าง loop state T0-T2 then reset to T0 again
   U9-1 (nand A i/p)  --> U8-14 (QA)
   U9-2 (nand A i/p)  --> U8-13 (QB)
   U9-3 (nand A o/p)  --> U8-1 (/CLR)

U10 74HC04 inverter ใช้กลับสัญญาณ QA, QB 

U10-1 (N A i/p) <-- U8-14 (QA)
U10-2 (N A o/p) ----> ได้สัญญาณ !QA --> U11-2 / U11-10
U10-3 (N B i/p) <-- U8-13 (QB)
U10-4 (N B o/p) -----> ได้สัญญาณ !QB --> U11-1 / U11-4
U10-7     --> Gnd
U10-14    --> Vcc

U11 74HC08 and gate  ตรงนี้ลด gate ได้ 2 ตัว โดยใช้ QA-QD แทน 4 state โดยไม่ต้องใช้ U10(74hc04) และ U11 (74hc08) มาถอดรหัส

U11-1 (and A i/p)  <-- U10-4 (!QB)
U11-2 (and A i/p)  <-- U10-2 (!QA)
U11-3 (and A o/p)  --> T0 state (!QA + !QB -> T0)
U11-4 (and B i/p) <-- U10-4 (!QB)
U11-5 (and B i/p) <-- U8-14 (QA)
U11-6 (and B o/p) --> T1 State (QA + !QB -> T1)
U11-7   --> GND
U11-8 (and C o/p)
U11-9 (and C i/p)   <-- U8-13 (QB)
U11-10 (and C i/p)  <-- U10-2 (!QA)
U11-11 (and D o/p)  --> T2 state (!QA + QB -> T2)
U11-12 (and D i/p)
U11-13 (and D i/p)
U11-14  --> Vcc

**************** ต่อไปเป็น accumulator

U12 74HC574 (Accumulator)

U12-1 (/OE)   --> GND 
U12-2 (D1)    --> ID0
U12-3 (D2)    --> ID1
U12-4 (D3)    --> ID2
U12-5 (D4)    --> ID3
U12-6 (D5)    --> ID4
U12-7 (D6)    --> ID5
U12-8 (D7)    --> ID6
U12-9 (D8)    --> ID7
U12-10 (GND)  --> GND
U12-11 (CLK)  --> Acc_Load (T2 + LDI_Opcode (LDI,Add,Load)) หรือ ต่อกับ T2 เพื่อทดสอบ
U12-12 (Q8)   --> Acc7
U12-13 (Q7)   --> Acc6
U12-14 (Q6)   --> acc5
U12-15 (Q5)   --> Acc4
U12-16 (Q4)   --> Acc3
U12-17 (Q3)   --> Acc2
U12-18 (Q2)   --> Acc1
U12-19 (Q1)   --> Acc0
U12-20 (VCC)  --> Vcc

ถึงจุดนี้ เราได้คำสั่ง LDI imm8 ---> Acc <-IRL

ขั้นตอนต่อไป ALU 8 bit
Acc --> ALU A
IRL --> ALU B 
ALU_A & ALU_B -->IBUS-->Acc

U13, U14 74hc283

U13 74HC283 ALU Low nibble (bit0-3)
U13-1 (S1)    -->ALU1
U13-2 (B1)    <--IRL1
U13-3 (A1)    <--Acc1
U13-4 (S0)    -->ALU0
U13-5 (A0)    <--Acc0 (Input A)
U13-6 (B0)    <--IRL0 (input B)
U13-7 (Cin)     --> GND (carry in)
U13-8 (GND)     ---> GND
U13-9 (Cout)    --> U14-7 (U14 Carry in)
U13-10 (S3)   -->ALU3
U13-11 (B3)   <--IRL3
U13-12 (A3)   <-- Acc3
U13-13 (S2)   --> ALU2
U13-14 (A2)   <--Acc2
U13-15 (B2)   <--IRL2
U13-16 (Vcc)    ---> Vcc

U14 74Hc283 ALU High nibble (bit 4-7)
U14-1 (S1)   -->ALU5
U14-2 (B1)  <--IRL5
U14-3 (A1)  <--Acc5
U14-4 (S0)   -->ALU4
U14-5 (A0)   <--Acc4
U14-6 (B0)  <--IRL4
U14-7 (Cin) <--U13-9 (U13 carry out)
U14-8 (GND)     ---> GND
U14-9 (Cout) ---> Cout Flag
U14-10 (S3)   -->ALU7
U14-11 (B3)  <--IRL7
U14-12 (A3)  <--Acc7
U14-13 (S2)   -->ALU6
U14-14 (A2)   <--Acc6
U14-15 (B2)   <--IRL6
U14-16 (Vcc)    ---> Vcc

ได้ ALU = Acc+IRL หรือ ADDI xx
ขั้นต่อไปคือ ALU --> IBUS -->Acc
Acc+IRL --> ALU-->IBUS-->Acc

U15 74HC541 tristate ALU output Buffer

U15-1 (/OE)  <--ALU_Out_N0
U15-2 (A1)    <-- ALU0
U15-3 (A2)    <-- ALU1
U15-4 (A3)    <-- ALU2
U15-5 (A4)    <-- ALU3
U15-6 (A5)    <-- ALU4
U15-7 (A6)    <-- ALU5
U15-8 (A7)    <-- ALU6
U15-9 (A8)    <-- ALU7
U15-10 (GND)  --> GND
U15-11 (Y8)   -->IB7
U15-12 (Y7)   -->IB6
U15-13 (Y6)   -->IB5
U15-14 (Y5)   -->IB4
U15-15 (Y4)   -->IB3
U15-16 (Y3)   -->IB2
U15-17 (Y2)   -->IB1
U15-18 (Y1)   -->IB0
U15-19 (/OE2) <-- ALU_Out_N1
U15-20 Vcc    --> Vcc

ชื่อ Block ตอนนี้
Acc, IRH, IRL, ALU, ALU_output_Buffer, IBUS, PC, State_Counter

ทดสอบ alu
ADDI #03h
Acc <--Acc+IRL โดยทำงานใน T2
ทดสอบโดย 
ALU_out_N   T2 (0)
Acc_Load    T2 (1)

U15-1 (Alu_output_buffer /OE1)  -> GND
U15-19 (Alu_output_buffer /OE2) -> GND
U12_11 (Acc_load)               <--T2

เมื่อ T2 ทำงาน Acc <--Acc+IRL

ได้ LDI และ ADDI แล้ว จาก Acc+IRL -> ALU ->ALU_output_buffer -> IBuss -> Acc
