# RV8-GR — KiCad Module Definitions

**Split the 36-chip CPU into 6 sub-schematics for easier wiring and debugging.**

This file is **not** the pin-level source of truth. Use
`01_wiring_guide.md` for exact chip pins and electrical wiring. Use this file
to understand how the same CPU is split into smaller KiCad sheets and smaller
student build/debug chunks.

Each module = 1 KiCad hierarchical sheet. The module order follows
`05_debug_plan.md` and the hardware labs. Wire one module or partial module at a
time on breadboard, test it, then connect the next module.

Why keep this doc:
- It shows the real KiCad sheet boundary for each group of chips.
- It helps students see the CPU as six smaller systems instead of one large
  schematic.
- It identifies cross-module signals so sheet pins and labels stay consistent.
- It points back to the wiring guide whenever exact pin truth matters.

---

## Module Overview

| # | Module | Chips | Count | Debug Steps |
|:-:|--------|-------|:-----:|:-----------:|
| 1 | **CLK_RST** | U8, U24 (gates 1-2) | 1.5* | Steps 1-2 |
| 2 | **PC** | U1-U4 | 4 | Step 3 |
| 3 | **ADDR_MEM** | U15-U16, U29-U30, ROM, RAM | 6 | Steps 4-5, 11 |
| 4 | **IR_BUF** | U5, U6, U7, U14, U34 | 5 | Step 6 |
| 5 | **ALU_AC** | U9, U10-U13, U17-U20, U21, U22 | 11 | Steps 7-8-9 (AC+Z) |
| 6 | **CTRL** | U23, U24 (gates 3-6), U25-U28, U31, U32, U33 | 9.5* | Steps 9-14 |
| | **Total** | | **36** | |

\* U24 is shared: gates 1-2 in CLK_RST (ring counter feedback), gates 3-6 in CTRL.
In KiCad, place U24 on the CTRL sheet with hierarchical pins for NOT_T0/NOT_T1 back to CLK_RST.

---

## Alignment with Debug Plan, Labs, and Build Plan

| Debug Step | Lab | What's tested | KiCad Module |
|:----------:|:---:|---------------|:------------:|
| 1 | Lab 01 | Power + Clock | CLK_RST |
| 2 | Lab 02 | Ring Counter (U8 + U24 inv) | CLK_RST |
| 3 | Lab 03 | PC Counter (U1-U4) | PC |
| 4 | Lab 04 | Address Mux (U15-U16, U29-U30) | ADDR_MEM |
| 5 | Lab 05 | ROM + Bus Buffer (ROM, U7) | ADDR_MEM + IR_BUF |
| 6 | Lab 06 | IR Latch (U5, U6) | IR_BUF |
| 7 | Lab 07 | ALU Adder (U10-U13) | ALU_AC |
| 8 | Lab 08 | AC + Mux (U9, U14, U17-U20) | ALU_AC + IR_BUF(U14) |
| 9 | Lab 09 | Z Flag (U21, U22) | ALU_AC |
| 10 | Lab 10 | Branch/Jump (U25-U28) | CTRL |
| 11 | Lab 11 | Page Register (U23) | CTRL |
| 12 | Lab 12 | RAM + Data Page (RAM, U32, U33) | ADDR_MEM + CTRL |
| 13 | Lab 13 | Full System | All |
| 14 | Lab 14 | IRQ + Bus (U31, 40-pin) | CTRL |

> 📌 **Lab 05 spans two modules** (ROM in ADDR_MEM, U7 in IR_BUF).
> **Lab 08 spans two modules** (U14 in IR_BUF, muxes in ALU_AC).
> This is unavoidable — some chips interact across boundaries.
> The KiCad sheets define **signal ownership**, not physical placement.

`build_plan/01_student_incremental_build_plan.md` is more granular than the six
KiCad sheets. It intentionally builds partial modules first:

| Build-plan stages | Main chips | KiCad module boundary |
|---|---|---|
| 0-1 | Power, reset, U8, U24 gates 1-2 | CLK_RST |
| 2-3 | U1-U4 | PC |
| 4-6 | U15, U16, U29, U30, ROM | ADDR_MEM partial |
| 7-9 | U5, U6, U7, U34, early U24/U25/U26 control | IR_BUF + CTRL partial |
| 10-13 | U9-U14, U17-U22 | ALU_AC + IR_BUF(U14) |
| 14-17 | U23-U28, U31-U33, RAM | CTRL + ADDR_MEM(RAM) |
| 18-20 | RV8-Bus, boot ROM, full smoke test | All modules |
| Physical signoff | Voltage, clock, bus-race, edge, delay evidence | All modules + `07_real_build_timing_log.md` |

---

## Inter-Module Signal Names (for KiCad net labels)

### Global Buses
```
DBUS[7:0]     DBUS0..DBUS7    Memory/RV8 data bus (ROM/RAM ↔ U7)
IBUS[7:0]     IBUS0..IBUS7    CPU internal data bus
ABUS[15:0]    ABUS0..ABUS15   Address mux output bus
```

### Global Timing (from CLK_RST)
```
CLK           System clock
/RST          Active-low reset
T0            U8-3 (fetch control phase)
T1            U8-4 (fetch operand phase)
T2            U8-5 (execute phase)
NOT_T0        U24-2 (ring counter feedback)
NOT_T1        U24-4 (ring counter feedback)
```

### IR Outputs (from IR_BUF, directly named per bit)
```
ALU_SUB       U5-12 (bit7)
XOR_MODE      U5-13 (bit6)
MUX_SEL       U5-14 (bit5)
AC_WR         U5-15 (bit4)
SRC           U5-16 (bit3)
STR           U5-17 (bit2)
BR            U5-18 (bit1)
JMP           U5-19 (bit0)
IRL[7:0]      U6 Q1-Q8 outputs
```

### Control Signals (from CTRL → other modules)
```
PC_INC        U25-6    → PC
/PC_LD        U26-11   → PC
ADDR_REQ      U25-3    → CTRL internal (U26)
/ADDR_MODE    U26-6    → ADDR_MEM
ACC_CLK       U27-11   → ALU_AC (U9, U21)
/IRL_OE       U26-3    → IR_BUF (U34 /OE)
/AC_BUF       U26-8    → IR_BUF (U14 /OE), ADDR_MEM (RAM /WE)
BUF_OE_N      U24-12   → IR_BUF (U7 /OE)
WR_DIR        U28-8    → IR_BUF (U7 DIR)
PG_CLK        U25-11   → CTRL internal (U23)
DP_Load       U33-6    → CTRL internal (U32)
```

### Data Paths (between modules)
```
PC[15:0]      U1-U4 Q outputs → ADDR_MEM
AC[7:0]       U9 Q outputs → ALU_AC internal, IR_BUF (U14)
PG[7:0]       U23 Q outputs → PC (jump D-inputs)
DP[7:0]       U32 Q outputs → ADDR_MEM (mux high A-inputs)
Z_flag        U21-5 → CTRL (U28-1)
```

---

## Module 1: CLK_RST (Clock + Reset + Ring Counter)

**Chips**: U8 (74HC164)
**Shared**: U24 gates 1-2 (inverters for ring feedback — physically on CTRL sheet)

**Debug Steps**: 1 (power/clock), 2 (ring counter)

### Components on this sheet
```
- Crystal oscillator module (1 MHz)
- Reset circuit: 10kΩ + 10µF + 74HC14 Schmitt + pushbutton
- U8 (74HC164 ring counter)
- 3× LED + 330Ω on T0, T1, T2
- 1× LED + 330Ω on CLK
```

### Sheet Ports (hierarchical pins)
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| CLK | out | CLK | PC (U1-U4 pin 2) |
| /RST | out | /RST | PC, CTRL (U31) |
| T0 | out | T0 | IR_BUF (U5-11), CTRL (U25-4, U24-1) |
| T1 | out | T1 | IR_BUF (U6-11), CTRL (U25-5, U24-3) |
| T2 | out | T2 | CTRL (U26, U27, U28, U33) |
| NOT_T0 | in | NOT_T0 | From CTRL (U24-2) → U8-1 |
| NOT_T1 | in | NOT_T1 | From CTRL (U24-4) → U8-2 |

### Wiring
```
U8 (74HC164):
  Pin 1 (A)    ← NOT_T0 (from CTRL module, U24-2)
  Pin 2 (B)    ← NOT_T1 (from CTRL module, U24-4)
  Pin 3 (Q0)   → T0
  Pin 4 (Q1)   → T1
  Pin 5 (Q2)   → T2
  Pin 6 (Q3)   → NC
  Pin 7 (GND)  → GND
  Pin 8 (CLK)  ← CLK
  Pin 9 (/CLR) ← /RST
  Pin 10-13    → NC
  Pin 14 (VCC) → VCC

Reset Circuit:
  VCC → 10kΩ → NODE → 10µF → GND
  NODE → 74HC14 (Schmitt) → /RST
  Pushbutton: NODE → GND (momentary)
```

---

## Module 2: PC (Program Counter)

**Chips**: U1, U2, U3, U4 (74HC161 × 4)

**Debug Step**: 3

### Sheet Ports
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| CLK | in | CLK | From CLK_RST |
| /RST | in | /RST | From CLK_RST |
| PC_INC | in | PC_INC | From CTRL (U25-6) |
| /PC_LD | in | /PC_LD | From CTRL (U26-11) |
| IRL[7:0] | in | IRL0..IRL7 | From IR_BUF (U6 Q outputs) |
| PG[7:0] | in | PG0..PG7 | From CTRL (U23 Q outputs) |
| PC[15:0] | out | PC0..PC15 | To ADDR_MEM (mux B-inputs) |

### Wiring
```
U1 (PC bits 0-3):
  Pin 1 (/CLR) ← /RST
  Pin 2 (CLK)  ← CLK
  Pin 3 (D0)   ← IRL0     Pin 4 (D1) ← IRL1
  Pin 5 (D2)   ← IRL2     Pin 6 (D3) ← IRL3
  Pin 7 (ENP)  ← PC_INC
  Pin 9 (/LD)  ← /PC_LD
  Pin 10 (ENT) ← PC_INC
  Pin 14 (QA)  → PC0      Pin 13 (QB) → PC1
  Pin 12 (QC)  → PC2      Pin 11 (QD) → PC3
  Pin 15 (RCO) → U2-10

U2 (PC bits 4-7):
  Pin 1 (/CLR) ← /RST
  Pin 2 (CLK)  ← CLK
  Pin 3 (D0)   ← IRL4     Pin 4 (D1) ← IRL5
  Pin 5 (D2)   ← IRL6     Pin 6 (D3) ← IRL7
  Pin 7 (ENP)  ← PC_INC
  Pin 9 (/LD)  ← /PC_LD
  Pin 10 (ENT) ← U1-15 (RCO)
  Pin 14 (QA)  → PC4      Pin 13 (QB) → PC5
  Pin 12 (QC)  → PC6      Pin 11 (QD) → PC7
  Pin 15 (RCO) → U3-10

U3 (PC bits 8-11):
  Pin 1 (/CLR) ← /RST
  Pin 2 (CLK)  ← CLK
  Pin 3 (D0)   ← PG0      Pin 4 (D1) ← PG1
  Pin 5 (D2)   ← PG2      Pin 6 (D3) ← PG3
  Pin 7 (ENP)  ← PC_INC
  Pin 9 (/LD)  ← /PC_LD
  Pin 10 (ENT) ← U2-15 (RCO)
  Pin 14 (QA)  → PC8      Pin 13 (QB) → PC9
  Pin 12 (QC)  → PC10     Pin 11 (QD) → PC11
  Pin 15 (RCO) → U4-10

U4 (PC bits 12-15):
  Pin 1 (/CLR) ← /RST
  Pin 2 (CLK)  ← CLK
  Pin 3 (D0)   ← PG4      Pin 4 (D1) ← PG5
  Pin 5 (D2)   ← PG6      Pin 6 (D3) ← PG7
  Pin 7 (ENP)  ← PC_INC
  Pin 9 (/LD)  ← /PC_LD
  Pin 10 (ENT) ← U3-15 (RCO)
  Pin 14 (QA)  → PC12     Pin 13 (QB) → PC13
  Pin 12 (QC)  → PC14     Pin 11 (QD) → PC15
  Pin 15 (RCO) → NC
```

### Placement
> U1-U4 in a row. Carry chain (RCO→ENT) timing-critical at high speed.

---

## Module 3: ADDR_MEM (Address Mux + ROM + RAM)

**Chips**: U15, U16 (74HC157 × 2), U29, U30 (74HC157 × 2), AT28C256 (ROM), 62256 (RAM)

**Debug Steps**: 4 (address mux), 5 (ROM), 11 (RAM)

### Sheet Ports
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| PC[15:0] | in | PC0..PC15 | From PC module |
| IRL[7:0] | in | IRL0..IRL7 | From IR_BUF (U6) |
| DP[7:0] | in | DP0..DP7 | From CTRL (U32 Q outputs) |
| /ADDR_MODE | in | /ADDR_MODE | From CTRL (U26-6) |
| /A15 | in | /A15 | From CTRL (U24-6) — RAM /CE |
| /AC_BUF | in | /AC_BUF | From CTRL (U26-8) — RAM /WE |
| DBUS[7:0] | bidir | DBUS0..DBUS7 | ↔ IR_BUF (U7 B-side), RV8_D0..RV8_D7 |
| ABUS[15:0] | out | ABUS0..ABUS15 | To RV8-Bus, ROM/RAM address |
| ABUS15 | out | ABUS15 | To CTRL (U24-5 for chip select), RV8 pin 33 duplicate |

### Wiring
```
=== Address Mux Low: U15-U16 (ABUS0-ABUS7) ===
SEL=0: IRL (for data access), SEL=1: PC

U15 (A0-A3):
  Pin 1 (SEL) ← /ADDR_MODE    Pin 15 (/E) → GND
  Pin 2 (1A) ← IRL0   Pin 3 (1B) ← PC0    Pin 4 (1Y) → ABUS0
  Pin 5 (2A) ← IRL1   Pin 6 (2B) ← PC1    Pin 7 (2Y) → ABUS1
  Pin 11(3A) ← IRL2   Pin 10(3B) ← PC2    Pin 9 (3Y) → ABUS2
  Pin 14(4A) ← IRL3   Pin 13(4B) ← PC3    Pin 12(4Y) → ABUS3

U16 (A4-A7):
  Pin 1 (SEL) ← /ADDR_MODE    Pin 15 (/E) → GND
  Pin 2 (1A) ← IRL4   Pin 3 (1B) ← PC4    Pin 4 (1Y) → ABUS4
  Pin 5 (2A) ← IRL5   Pin 6 (2B) ← PC5    Pin 7 (2Y) → ABUS5
  Pin 11(3A) ← IRL6   Pin 10(3B) ← PC6    Pin 9 (3Y) → ABUS6
  Pin 14(4A) ← IRL7   Pin 13(4B) ← PC7    Pin 12(4Y) → ABUS7

=== Address Mux High: U29-U30 (ABUS8-ABUS15) ===
SEL=0: Data Page, SEL=1: PC high

U29 (A8-A11):
  Pin 1 (SEL) ← /ADDR_MODE    Pin 15 (/E) → GND
  Pin 2 (1A) ← DP0    Pin 3 (1B) ← PC8    Pin 4 (1Y) → ABUS8
  Pin 5 (2A) ← DP1    Pin 6 (2B) ← PC9    Pin 7 (2Y) → ABUS9
  Pin 11(3A) ← DP2    Pin 10(3B) ← PC10   Pin 9 (3Y) → ABUS10
  Pin 14(4A) ← DP3    Pin 13(4B) ← PC11   Pin 12(4Y) → ABUS11

U30 (A12-A15):
  Pin 1 (SEL) ← /ADDR_MODE    Pin 15 (/E) → GND
  Pin 2 (1A) ← DP4    Pin 3 (1B) ← PC12   Pin 4 (1Y) → ABUS12
  Pin 5 (2A) ← DP5    Pin 6 (2B) ← PC13   Pin 7 (2Y) → ABUS13
  Pin 11(3A) ← DP6    Pin 10(3B) ← PC14   Pin 9 (3Y) → ABUS14
  Pin 14(4A) ← DP7    Pin 13(4B) ← PC15   Pin 12(4Y) → ABUS15

=== ROM (AT28C256) ===
  A0-A14 ← ABUS0-ABUS14
  D0-D7  ↔ DBUS0-DBUS7
  /CE    ← ABUS15 (direct from U30-12; active when ABUS15=0)
  /OE    ← WR_DIR (U28-8; disables ROM output during CPU store)
  /WE    ← HIGH during CPU runtime; programmer path may drive only in PROG/reset isolation

=== RAM (62256) ===
  A0-A14 ← ABUS0-ABUS14
  D0-D7  ↔ DBUS0-DBUS7
  /CE    ← /A15 (from CTRL, U24-6; active when ABUS15=1)
  /OE    → GND
  /WE    ← /AC_BUF (from CTRL, U26-8)
```

### Chip Select Logic
```
ABUS15=0 → ROM /CE=LOW (ROM active), RAM /CE=HIGH (off)
ABUS15=1 → ROM /CE=HIGH (off), RAM /CE=LOW (RAM active)
Never both active — complementary by design.
```

### Placement
> U15/U16 near U6 (short IRL wires). U29/U30 near U32 in CTRL (short DP wires).
> ROM/RAM near U7 (short DBUS traces). This is the widest module physically.

---

## Module 4: IR_BUF (Instruction Register + Bus Buffers)

**Chips**: U5 (74HC574), U6 (74HC574), U7 (74HC245), U14 (74HC541), U34 (74HC541)

**Debug Steps**: 5 (U7 buffer with ROM), 6 (IR latch), 8 (U14 AC buffer)

### Sheet Ports
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| T0 | in | T0 | From CLK_RST → U5-11 (CLK) |
| T1 | in | T1 | From CLK_RST → U6-11 (CLK) |
| DBUS[7:0] | bidir | DBUS0..DBUS7 | ↔ ADDR_MEM (ROM/RAM) |
| AC[7:0] | in | AC0..AC7 | From ALU_AC (U9) → U14 inputs |
| /IRL_OE | in | /IRL_OE | From CTRL (U26-3) |
| /AC_BUF | in | /AC_BUF | From CTRL (U26-8) |
| BUF_OE_N | in | BUF_OE_N | From CTRL (U24-12) |
| WR_DIR | in | WR_DIR | From CTRL (U28-8) |
| IBUS[7:0] | bidir | IBUS0..IBUS7 | ↔ ALU_AC, CTRL (U23, U32) |
| ALU_SUB | out | ALU_SUB | U5-12 → ALU_AC, CTRL |
| XOR_MODE | out | XOR_MODE | U5-13 → ALU_AC, CTRL |
| MUX_SEL | out | MUX_SEL | U5-14 → ALU_AC, CTRL |
| AC_WR | out | AC_WR | U5-15 → CTRL |
| SRC | out | SRC | U5-16 → CTRL |
| STR | out | STR | U5-17 → CTRL |
| BR | out | BR | U5-18 → CTRL |
| JMP | out | JMP | U5-19 → CTRL |
| IRL[7:0] | out | IRL0..IRL7 | U6 Q → PC, ADDR_MEM |

### Wiring
```
U5 (IR_HIGH — control byte, 74HC574):
  Pin 1 (/OE) → GND (always enabled)
  Pin 2-9 (D1-D8) ← IBUS0-IBUS7 (IBUS)
  Pin 11 (CLK) ← T0
  Pin 19 (Q1) → JMP (bit0)
  Pin 18 (Q2) → BR (bit1)
  Pin 17 (Q3) → STR (bit2)
  Pin 16 (Q4) → SRC (bit3)
  Pin 15 (Q5) → AC_WR (bit4)
  Pin 14 (Q6) → MUX_SEL (bit5)
  Pin 13 (Q7) → XOR_MODE (bit6)
  Pin 12 (Q8) → ALU_SUB (bit7)

U6 (IR_LOW — operand, 74HC574):
  Pin 1 (/OE) → GND
  Pin 2-9 (D1-D8) ← IBUS0-IBUS7 (IBUS)
  Pin 11 (CLK) ← T1
  Pin 19 (Q1) → IRL0    Pin 18 (Q2) → IRL1
  Pin 17 (Q3) → IRL2    Pin 16 (Q4) → IRL3
  Pin 15 (Q5) → IRL4    Pin 14 (Q6) → IRL5
  Pin 13 (Q7) → IRL6    Pin 12 (Q8) → IRL7

U34 (IRL Immediate Buffer, 74HC541):
  Pin 1 (/OE1) ← /IRL_OE
  Pin 19 (/OE2) ← /IRL_OE
  Pin 2-9 (A1-A8) ← IRL0-IRL7
  Pin 18-11 (Y1-Y8) → IBUS0-IBUS7

U7 (Bus Buffer, 74HC245):
  Pin 1 (DIR) ← WR_DIR (0=DBUS→IBUS read, 1=IBUS→DBUS write)
  Pin 19 (/OE) ← BUF_OE_N
  Pin 2-9 (A1-A8) ↔ IBUS0-IBUS7 (IBUS side)
  Pin 18-11 (B1-B8) ↔ D0-D7 (DBUS side)

U14 (AC Output Buffer, 74HC541):
  Pin 1 (/OE1) ← /AC_BUF
  Pin 19 (/OE2) ← /AC_BUF
  Pin 2-9 (A1-A8) ← AC0-AC7
  Pin 18-11 (Y1-Y8) → IBUS0-IBUS7 (IBUS, active only during STORE)
```

### Bus Contention Rules (from wiring guide)
```
Only ONE IBUS driver active at T2:
  SRC=0, STR=0 → U34 drives IBUS (immediate from IRL)
  SRC=1, STR=0 → U7 drives IBUS (RAM/ROM data)
  SRC=0, STR=1 → U14 drives IBUS (AC value for store)
  SRC=1, STR=1 → reserved horizontal encoding; store-dominant bus ownership

Store safety:
  U7 /OE = BUF_OE_N
  ROM /OE = WR_DIR
  During STORE, U7 writes IBUS→DBUS and ROM output is disabled
```

For valid student programs, use only the frozen ISA in `00_design_isa.md`.
Reserved horizontal encodings are not teaching instructions; they are only
checked to avoid unsafe bus ownership.

---

## Module 5: ALU_AC (ALU + Accumulator + Z Flag)

**Chips**: U9 (74HC574), U10-U11 (74HC283 × 2), U12-U13 (74HC86 × 2), U17-U18 (74HC157 × 2), U19-U20 (74HC157 × 2), U21 (74HC74), U22 (74HC688)

**Total**: 11 chips

**Debug Steps**: 7 (adder), 8 (AC + mux), 9 (Z flag)

### Sheet Ports
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| IBUS[7:0] | in | IBUS0..IBUS7 | From bus (U12/U13 A-inputs) |
| ALU_SUB | in | ALU_SUB | From IR_BUF (U5-12) → U10-7, U19/U20 |
| XOR_MODE | in | XOR_MODE | From IR_BUF (U5-13) → U19-1, U20-1 |
| MUX_SEL | in | MUX_SEL | From IR_BUF (U5-14) → U17-1, U18-1 |
| ACC_CLK | in | ACC_CLK | From CTRL (U27-11) → U9-11, U21-3 |
| AC[7:0] | out | AC0..AC7 | To IR_BUF (U14), internal (adder, XOR mux, zero det) |
| Z_flag | out | Z_flag | To CTRL (U28-1) |

### Wiring
```
=== XOR B-Input Mux: U19-U20 (74HC157) ===
SEL = XOR_MODE
  SEL=0: output = ALU_SUB (all bits same, for ADD/SUB)
  SEL=1: output = AC bits (for XOR instruction)

U19 (bits 0-3):
  Pin 1 (SEL) ← XOR_MODE    Pin 15 (/E) → GND
  1A,2A,3A,4A (pins 2,5,11,14) ← ALU_SUB (all same wire)
  1B←AC0(pin3), 2B←AC1(pin6), 3B←AC2(pin10), 4B←AC3(pin13)
  1Y→U12-2, 2Y→U12-5, 3Y→U12-10, 4Y→U12-13

U20 (bits 4-7):
  Pin 1 (SEL) ← XOR_MODE    Pin 15 (/E) → GND
  1A,2A,3A,4A (pins 2,5,11,14) ← ALU_SUB
  1B←AC4(pin3), 2B←AC5(pin6), 3B←AC6(pin10), 4B←AC7(pin13)
  1Y→U13-2, 2Y→U13-5, 3Y→U13-10, 4Y→U13-13

=== XOR Array: U12-U13 (74HC86) ===
A = IBUS, B = mux output → Y = XOR result

U12 (bits 0-3):
  Pin 1←IBUS0,  Pin 2←U19-4,  Pin 3→XOR_Y0
  Pin 4←IBUS1,  Pin 5←U19-7,  Pin 6→XOR_Y1
  Pin 9←IBUS2,  Pin 10←U19-9, Pin 8→XOR_Y2
  Pin 12←IBUS3, Pin 13←U19-12, Pin 11→XOR_Y3

U13 (bits 4-7):
  Pin 1←IBUS4,  Pin 2←U20-4,  Pin 3→XOR_Y4
  Pin 4←IBUS5,  Pin 5←U20-7,  Pin 6→XOR_Y5
  Pin 9←IBUS6,  Pin 10←U20-9, Pin 8→XOR_Y6
  Pin 12←IBUS7, Pin 13←U20-12, Pin 11→XOR_Y7

=== Adder: U10-U11 (74HC283) ===
A = AC, B = XOR output, Cin = ALU_SUB

U10 (bits 0-3):
  A0(pin5)←AC0, A1(pin3)←AC1, A2(pin14)←AC2, A3(pin12)←AC3
  B0(pin6)←XOR_Y0, B1(pin2)←XOR_Y1, B2(pin15)←XOR_Y2, B3(pin11)←XOR_Y3
  Cin(pin7)←ALU_SUB
  S0(pin4)→SUM0, S1(pin1)→SUM1, S2(pin13)→SUM2, S3(pin10)→SUM3
  Cout(pin9)→U11-7

U11 (bits 4-7):
  A0(pin5)←AC4, A1(pin3)←AC5, A2(pin14)←AC6, A3(pin12)←AC7
  B0(pin6)←XOR_Y4, B1(pin2)←XOR_Y5, B2(pin15)←XOR_Y6, B3(pin11)←XOR_Y7
  Cin(pin7)←U10-9 (Cout)
  S0(pin4)→SUM4, S1(pin1)→SUM5, S2(pin13)→SUM6, S3(pin10)→SUM7

=== AC Input Mux: U17-U18 (74HC157) ===
SEL = MUX_SEL
  SEL=0: Adder SUM (for ADD/SUB)
  SEL=1: XOR output (for LI/LB/XOR)

U17 (bits 0-3):
  Pin 1 (SEL) ← MUX_SEL    Pin 15 (/E) → GND
  1A←SUM0(pin2), 1B←XOR_Y0(pin3), 1Y→U9-2
  2A←SUM1(pin5), 2B←XOR_Y1(pin6), 2Y→U9-3
  3A←SUM2(pin11), 3B←XOR_Y2(pin10), 3Y→U9-4
  4A←SUM3(pin14), 4B←XOR_Y3(pin13), 4Y→U9-5

U18 (bits 4-7):
  Pin 1 (SEL) ← MUX_SEL    Pin 15 (/E) → GND
  1A←SUM4(pin2), 1B←XOR_Y4(pin3), 1Y→U9-6
  2A←SUM5(pin5), 2B←XOR_Y5(pin6), 2Y→U9-7
  3A←SUM6(pin11), 3B←XOR_Y6(pin10), 3Y→U9-8
  4A←SUM7(pin14), 4B←XOR_Y7(pin13), 4Y→U9-9

=== Accumulator: U9 (74HC574) ===
  Pin 1 (/OE) → GND (always output)
  Pin 2-9 (D1-D8) ← U17/U18 Y outputs (AC_MUX0-7)
  Pin 11 (CLK) ← ACC_CLK
  Pin 19→AC0, Pin 18→AC1, Pin 17→AC2, Pin 16→AC3
  Pin 15→AC4, Pin 14→AC5, Pin 13→AC6, Pin 12→AC7

=== Zero Detect: U22 (74HC688) ===
  Pin 1 (/OE) → GND
  A0(pin2)←AC0, A1(pin4)←AC1, A2(pin6)←AC2, A3(pin8)←AC3
  A4(pin11)←AC4, A5(pin13)←AC5, A6(pin15)←AC6, A7(pin17)←AC7
  B0-B7 (pins 3,5,7,9,12,14,16,18) → all GND
  Pin 19 (Y, active-low equal) → U21-4 (/PR1)

=== Z Flag: U21 (74HC74, FF1 only) ===
  Pin 1 (/CLR1) → VCC
  Pin 2 (D1)    → GND
  Pin 3 (CLK1)  ← ACC_CLK
  Pin 4 (/PR1)  ← U22-19 (/P=Q)
  Pin 5 (Q1)    → Z_flag
  Pin 6 (/Q1)   → NC
  FF2 unused: Pin 8(/Q2)→NC, Pin 9(Q2)→NC, Pin 10(/PR2)→VCC,
              Pin 11(CLK2)→GND, Pin 12(D2)→GND, Pin 13(/CLR2)→VCC
```

### Placement
> Place in signal flow: U19/U20 → U12/U13 → U10/U11 → U17/U18 → U9.
> U10-U11 carry chain is timing-critical — keep adjacent.
> U22 physically adjacent to U21 (async /PR wire must be short).

---

## Module 6: CTRL (Control Logic + Page Registers + IRQ)

**Chips**: U23 (74HC574), U24 (74HC04), U25 (74HC32), U26 (74HC00), U27 (74HC00), U28 (74HC86), U31 (74HC74), U32 (74HC574), U33 (74HC21)

**Total**: 9 chips

**Debug Steps**: 10 (branch/jump), 11 (page register), 12 (data page + SETDP), 13 (IRQ), 14 (bus)

### Sheet Ports
| Port | Dir | Net | Connects to |
|------|:---:|-----|-------------|
| T0 | in | T0 | From CLK_RST |
| T1 | in | T1 | From CLK_RST |
| T2 | in | T2 | From CLK_RST |
| /RST | in | /RST | From CLK_RST |
| ALU_SUB | in | ALU_SUB | From IR_BUF (U5-12) |
| XOR_MODE | in | XOR_MODE | From IR_BUF (U5-13) |
| MUX_SEL | in | MUX_SEL | From IR_BUF (U5-14) |
| AC_WR | in | AC_WR | From IR_BUF (U5-15) |
| SRC | in | SRC | From IR_BUF (U5-16) |
| STR | in | STR | From IR_BUF (U5-17) |
| BR | in | BR | From IR_BUF (U5-18) |
| JMP | in | JMP | From IR_BUF (U5-19) |
| Z_flag | in | Z_flag | From ALU_AC (U21-5) |
| A15 | in | A15 | From ADDR_MEM (U30-12) |
| IBUS[7:0] | in | IBUS0..IBUS7 | From bus → U23, U32 D-inputs |
| /IRQ | in | /IRQ | From RV8-Bus pin 29 |
| NOT_T0 | out | NOT_T0 | To CLK_RST (U8-1) |
| NOT_T1 | out | NOT_T1 | To CLK_RST (U8-2) |
| /A15 | out | /A15 | To ADDR_MEM (RAM /CE) |
| /ADDR_MODE | out | /ADDR_MODE | To ADDR_MEM |
| PC_INC | out | PC_INC | To PC |
| /PC_LD | out | /PC_LD | To PC |
| ACC_CLK | out | ACC_CLK | To ALU_AC (U9, U21) |
| /IRL_OE | out | /IRL_OE | To IR_BUF (U34) |
| /AC_BUF | out | /AC_BUF | To IR_BUF (U14), ADDR_MEM (RAM /WE) |
| BUF_OE_N | out | BUF_OE_N | To IR_BUF (U7 /OE) |
| WR_DIR | out | WR_DIR | To IR_BUF (U7 DIR) |
| PG[7:0] | out | PG0..PG7 | To PC (U3/U4 D-inputs) |
| DP[7:0] | out | DP0..DP7 | To ADDR_MEM (U29/U30 A-inputs) |

### Wiring
```
=== U24 (74HC04 — 6 Inverters) ===
Gate 1: Pin 1←T0,       Pin 2→NOT_T0 (→CLK_RST U8-1)
Gate 2: Pin 3←T1,       Pin 4→NOT_T1 (→CLK_RST U8-2)
Gate 3: Pin 5←A15,      Pin 6→/A15 (→RAM /CE)
Gate 4: Pin 9←JMP,      Pin 8→/JUMP (internal)
Gate 5: Pin 11←AC_WR,   Pin 10→/AC_WR (internal)
Gate 6: Pin 13←/IRL_OE, Pin 12→BUF_OE_N (internal)

=== U25 (74HC32 — 4 OR Gates) ===
Gate 1: Pin 1←SRC,       Pin 2←STR,       Pin 3→ADDR_REQ
Gate 2: Pin 4←T0,        Pin 5←T1,        Pin 6→PC_INC
Gate 3: Pin 9←GND,       Pin 10←GND,      Pin 8→NC (spare)
Gate 4: Pin 12←/T2,      Pin 13←/PG_cond, Pin 11→PG_CLK (→U23-11)

=== U26 (74HC00 — 4 NAND Gates) ===
Gate A: Pin 1←T2,        Pin 2←/ADDR_MODE, Pin 3→/IRL_OE
Gate B: Pin 4←ADDR_REQ,  Pin 5←T2,         Pin 6→/ADDR_MODE
Gate C: Pin 9←T2,        Pin 10←STR,       Pin 8→/AC_BUF
Gate D: Pin 12←T2,       Pin 13←PC_LOAD_COND, Pin 11→/PC_LD

=== U27 (74HC00 — 4 NAND Gates) ===
Gate A: Pin 1←BR,       Pin 2←Z_match,    Pin 3→/BR_TAKEN (internal)
Gate B: Pin 4←/JUMP,    Pin 5←/BR_TAKEN,  Pin 6→PC_LOAD_COND (internal)
Gate C: Pin 9←MUX_SEL,  Pin 10←/AC_WR,    Pin 8→/PG_cond (internal)
Gate D: Pin 12←T2,      Pin 13←AC_WR,     Pin 11→ACC_CLK

=== U28 (74HC86 — 4 XOR Gates) ===
Gate A: Pin 1←Z_flag,    Pin 2←ALU_SUB,   Pin 3→Z_match (internal)
Gate B: Pin 4←T2,        Pin 5←VCC,       Pin 6→/T2 (internal)
Gate C: Pin 9←/AC_BUF,   Pin 10←VCC,      Pin 8→WR_DIR
Gate D: Pin 12←XOR_MODE, Pin 13←VCC,      Pin 11→/XOR_MODE (internal)

=== U33 (74HC21 — Dual 4-input AND) ===
Gate 1 (DP_Load):
  Pin 1←T2, Pin 2←XOR_MODE, Pin 4←/ADDR_MODE, Pin 5←/AC_WR
  Pin 6→DP_Load (→U32-11)

Gate 2 (EI_decode):
  Pin 9←T2, Pin 10←SRC, Pin 12←/XOR_MODE, Pin 13←/AC_WR
  Pin 8→EI_decode (→U31-3)

Pin 3, Pin 11 → NC (74HC21 no-connect pins)

=== U23 (Page Register, 74HC574) ===
  Pin 1 (/OE) → GND
  Pin 2-9 (D1-D8) ← IBUS0-IBUS7
  Pin 11 (CLK) ← PG_CLK (U25-11)
  Pin 19→PG0, Pin 18→PG1, Pin 17→PG2, Pin 16→PG3
  Pin 15→PG4, Pin 14→PG5, Pin 13→PG6, Pin 12→PG7

=== U32 (Data Page Register, 74HC574) ===
  Pin 1 (/OE) → GND
  Pin 2-9 (D1-D8) ← IBUS0-IBUS7
  Pin 11 (CLK) ← DP_Load (U33-6)
  Pin 19→DP0, Pin 18→DP1, Pin 17→DP2, Pin 16→DP3
  Pin 15→DP4, Pin 14→DP5, Pin 13→DP6, Pin 12→DP7

=== U31 (IRQ + IE, 74HC74) ===
FF1 (IE flag):
  Pin 1 (/CLR1) ← /RST
  Pin 2 (D1)    ← VCC
  Pin 3 (CLK1)  ← EI_decode (U33-8)
  Pin 4 (/PR1)  ← VCC
  Pin 5 (Q1)    → IE (LED)
  Pin 6 (/Q1)   → NC

FF2 (IRQ latch):
  Pin 8 (/Q2)   → NC
  Pin 9 (Q2)    → IRQ_FF (LED)
  Pin 10 (/PR2) ← VCC
  Pin 11 (CLK2) ← /IRQ (from RV8-Bus)
  Pin 12 (D2)   ← VCC
  Pin 13 (/CLR2)← /RST
```

### Internal Signals (not exported)
```
/JUMP         U24-8
/AC_WR        U24-10
BUF_OE_N      U24-12
/ADDR_MODE    U26-6
Z_match       U28-3
/T2           U28-6
/XOR_MODE     U28-11
/BR_TAKEN     U27-3
PC_LOAD_COND  U27-6
/PG_cond      U27-8
```

---

## Module Interconnection Summary

```
┌──────────────┐
│  CLK_RST     │ CLK, /RST, T0, T1, T2
│  (U8)        │────────────────────────────────────┐
└──────┬───────┘                                    │
  NOT_T0/T1↑   CLK,/RST                            │
       │        │                                   │
┌──────┴───────┐│    ┌────────────┐                 │
│  CTRL        ││    │  PC        │                 │
│  U23-U28     │├───►│  U1-U4     │◄──PG[7:0]──────┤
│  U31-U33     ││    └─────┬──────┘                 │
└──┬───┬───┬───┘│          │PC[15:0]                │
   │   │   │    │          ▼                        │
   │   │   │    │    ┌────────────┐   DBUS   ┌─────┴──────┐
   │   │   │    │    │ ADDR_MEM   │◄════════►│  IR_BUF    │
   │   │   │    │    │ U15/16/29/30│          │  U5,U6,U7  │
   │   │   │    │    │ ROM + RAM  │          │  U14       │
   │   │   │    │    └────────────┘          └─────┬──────┘
   │   │   │    │                                   │IR bits
   │   │   │    │         IBUS                      │IRL[7:0]
   │   │   │    │    ┌════════════════════════┐     │
   │   │   │    │    │                        │     │
   │   │   └────│────│─── control signals ────│─────┘
   │   │         │   │                        │
   │   │         │   │   ┌────────────┐       │
   │   │         │   └──►│  ALU_AC    │◄──────┘
   │   │         │       │  U9-U13    │  IBUS
   │   └─────────│──────►│  U17-U22   │
   │  ACC_CLK    │       └─────┬──────┘
   │              │             │AC[7:0], Z_flag
   └──────────────│─────────────┘
    to CTRL       │
                  └── to all (CLK, T0-T2)
```

---

## Chip → Module Lookup

| Chip | Part | Module | Debug Step |
|:----:|------|:------:|:----------:|
| U1 | 74HC161 | PC | 3 |
| U2 | 74HC161 | PC | 3 |
| U3 | 74HC161 | PC | 3 |
| U4 | 74HC161 | PC | 3 |
| U5 | 74HC574 | IR_BUF | 6 |
| U6 | 74HC574 | IR_BUF | 6 |
| U7 | 74HC245 | IR_BUF | 5 |
| U8 | 74HC164 | CLK_RST | 2 |
| U9 | 74HC574 | ALU_AC | 8 |
| U10 | 74HC283 | ALU_AC | 7 |
| U11 | 74HC283 | ALU_AC | 7 |
| U12 | 74HC86 | ALU_AC | 7 |
| U13 | 74HC86 | ALU_AC | 7 |
| U14 | 74HC541 | IR_BUF | 8 |
| U15 | 74HC157 | ADDR_MEM | 4 |
| U16 | 74HC157 | ADDR_MEM | 4 |
| U17 | 74HC157 | ALU_AC | 8 |
| U18 | 74HC157 | ALU_AC | 8 |
| U19 | 74HC157 | ALU_AC | 8 |
| U20 | 74HC157 | ALU_AC | 8 |
| U21 | 74HC74 | ALU_AC | 9 |
| U22 | 74HC688 | ALU_AC | 9 |
| U23 | 74HC574 | CTRL | 11 |
| U24 | 74HC04 | CTRL* | 2, 10 |
| U25 | 74HC32 | CTRL | 10 |
| U26 | 74HC00 | CTRL | 10 |
| U27 | 74HC00 | CTRL | 10 |
| U28 | 74HC86 | CTRL | 10 |
| U29 | 74HC157 | ADDR_MEM | 4 |
| U30 | 74HC157 | ADDR_MEM | 4 |
| U31 | 74HC74 | CTRL | 13 |
| U32 | 74HC574 | CTRL | 12 |
| U33 | 74HC21 | CTRL | 12 |
| U34 | 74HC541 | IR_BUF | 6, 8 |
| ROM | AT28C256 | ADDR_MEM | 5 |
| RAM | 62256 | ADDR_MEM | 11 |

\* U24 gates 1-2 serve CLK_RST (ring counter feedback). Gates 3-6 serve CTRL.
Place U24 physically between U8 and control logic on breadboard.

---

## KiCad Implementation Notes

### Hierarchical Sheet Setup
1. Top-level sheet with 6 hierarchical sheet symbols
2. Each symbol has hierarchical pins matching the Sheet Ports tables
3. Use **global labels** for buses: `IBUS0`..`IBUS7`, `DBUS0`..`DBUS7`, `ABUS0`..`ABUS15`
4. Use **hierarchical pins** for control signals (point-to-point)

### Power
- Every chip: `VCC` + `GND` power symbols (auto-connect in KiCad)
- 100nF bypass cap per chip (place next to VCC/GND pins)
- 100µF bulk electrolytic per power rail

### Net Naming Convention
```
Buses:       IBUS0..IBUS7, DBUS0..DBUS7, ABUS0..ABUS15
Active-low:  use / prefix: /RST, /PC_LD, /AC_BUF, /IRL_OE
Phases:      T0, T1, T2
IR bits:     ALU_SUB, XOR_MODE, MUX_SEL, AC_WR, SRC, STR, BR, JMP
Registers:   PC0..PC15, AC0..AC7, PG0..PG7, DP0..DP7, IRL0..IRL7
Internal:    Z_match, /BR_TAKEN, PC_LOAD_COND, /PG_cond, /T2, BUF_OE_N
```

### RV8-Bus Connector (on CTRL sheet or separate top-level)
```
40-pin IDC header with nets:
  Pins 1-16:  A0-A15 (from ADDR_MEM)
  Pins 17-24: D0-D7 (from DBUS)
  Pin 25: CLK, Pin 26: /RST, Pin 27: /AC_BUF (/WR)
  Pin 28: /T2 (/RD), Pin 29: /IRQ (input)
  Pin 30: /SLOT1, Pin 31: /SLOT2, Pin 32: T2
  Pin 33: ABUS15 duplicate, Pins 34-38: reserved/NC
  Pin 39: VCC, Pin 40: GND
```

### Build/Test Order (same as debug plan)
```
1. Power + Clock (no chips yet)
2. CLK_RST module (U8 + U24 gates 1-2) → verify T0/T1/T2
3. PC module (U1-U4) → verify counting
4. ADDR_MEM partial (U15/U16/U29/U30) → verify address follows PC
5. ADDR_MEM + IR_BUF partial (ROM + U7) → verify ROM data on DBUS
6. IR_BUF (U5 + U6) → verify IR latches
7. ALU_AC partial (U10-U13) → verify adder
8. ALU_AC + IR_BUF (U9, U14, U17-U20) → verify full ALU path
9. ALU_AC (U21, U22) → verify Z flag
10. CTRL partial (U25-U28) → verify branch/jump
11. CTRL (U23) → verify page register + 16-bit jump
12. ADDR_MEM (RAM) + CTRL (U32, U33) → verify SB/LB + data page
13. Full system integration test
14. CTRL (U31) + RV8-Bus connector → verify IRQ + bus
```
