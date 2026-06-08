# RV8-GR — Wiring Guide (Official)

**32 logic chips + ROM + RAM = 34 packages. Source of truth for physical build.**

---

## Memory Map

```
$0000-$7FFF  RAM 32KB (registers $00-$07, data, executable)
$8000-$FFFF  ROM 32KB (bankable to 128KB)
$FF00        IRQ vector
Reset → $8000
```

---

## RV8-Bus (40-pin System Bus)

CPU board ↔ Expansion/Programmer ผ่าน 40-pin IDC connector

```
┌──────────────────────────────────────────────────────────┐
│                   RV8-Bus (40 pins)                        │
├──────────────────────────────────────────────────────────┤
│ Pin  Signal    Dir   │ Pin  Signal    Dir                 │
│  1   A0        out   │  2   A1        out                 │
│  3   A2        out   │  4   A3        out                 │
│  5   A4        out   │  6   A5        out                 │
│  7   A6        out   │  8   A7        out                 │
│  9   A8        out   │ 10   A9        out                 │
│ 11   A10       out   │ 12   A11       out                 │
│ 13   A12       out   │ 14   A13       out                 │
│ 15   A14       out   │ 16   A15       out                 │
│ 17   D0        bidir │ 18   D1        bidir               │
│ 19   D2        bidir │ 20   D3        bidir               │
│ 21   D4        bidir │ 22   D5        bidir               │
│ 23   D6        bidir │ 24   D7        bidir               │
│ 25   CLK       out   │ 26   /RST      out                 │
│ 27   /WR       out   │ 28   /RD       out                 │
│ 29   /IRQ      in    │ 30   /SLOT1    out                 │
│ 31   /SLOT2    out   │ 32   T2        out                 │
│ 33   A15       out   │ 34   (reserved)                    │
│ 35   (reserved)      │ 36   (reserved)                    │
│ 37   (reserved)      │ 38   (reserved)                    │
│ 39   VCC (+5V)       │ 40   GND                           │
└──────────────────────────────────────────────────────────┘
```

### Signal Description

| Pin | Signal | Dir | Source | Description |
|:---:|--------|:---:|--------|-------------|
| 1-16 | A[15:0] | out | Addr Mux | 16-bit address bus |
| 17-24 | D[7:0] | bidir | U7/ROM/RAM | 8-bit data bus |
| 25 | CLK | out | Oscillator | System clock (10 MHz) |
| 26 | /RST | out | RC+button | Active-low reset |
| 27 | /WR | out | /AC_BUF (U26-8) | Write strobe (LOW during T2+STORE) |
| 28 | /RD | out | /T2 or fetch | Read strobe |
| 29 | /IRQ | in | Peripheral | Interrupt request (falling edge) |
| 30 | /SLOT1 | out | Address decode | I/O slot 1 select |
| 31 | /SLOT2 | out | Address decode | I/O slot 2 select |
| 32 | T2 | out | U8-5 | Execute phase (for expansion timing) |
| 33 | A15 | out | U30-12 | Duplicate for chip select |
| 39 | VCC | — | Power | +5V |
| 40 | GND | — | Power | Ground |

### Bus Timing

```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
CLK:  ──┘   └───┘   └───┘   └───┘   └──
        T0       T1       T2       T0
A[15:0]: ←── PC ──→←── PC ──→←─ IRL ─→←── PC ──→
D[7:0]:  ←─ ctrl ─→←─ oper ─→←─ data ─→←─ ctrl ─→
/WR:   ─────────────────────┐       ┌───────────
                             └───────┘ (T2+STORE only)
```

---

## Buses

### DBUS — External Data Bus (D0-D7)

```
D0 ←→ ROM D0, RAM D0, U7-2
D1 ←→ ROM D1, RAM D1, U7-3
D2 ←→ ROM D2, RAM D2, U7-4
D3 ←→ ROM D3, RAM D3, U7-5
D4 ←→ ROM D4, RAM D4, U7-6
D5 ←→ ROM D5, RAM D5, U7-7
D6 ←→ ROM D6, RAM D6, U7-8
D7 ←→ ROM D7, RAM D7, U7-9
```

### IBUS — Internal Bus (IB0-IB7)

Drivers (tristate, only ONE active at T2):
- U7: ROM/RAM data (fetch or register read)
- U6: IRL immediate (SRC=0, STR=0)
- U14: AC value (STR=1)

```
IB0 ←→ U7-18, U6-19*, U14-18*, U12-1, U23-2, U5-2
IB1 ←→ U7-17, U6-18*, U14-17*, U12-4, U23-3, U5-3
IB2 ←→ U7-16, U6-17*, U14-16*, U12-9, U23-4, U5-4
IB3 ←→ U7-15, U6-16*, U14-15*, U12-12, U23-5, U5-5
IB4 ←→ U7-14, U6-15*, U14-14*, U13-1, U23-6, U5-6
IB5 ←→ U7-13, U6-14*, U14-13*, U13-4, U23-7, U5-7
IB6 ←→ U7-12, U6-13*, U14-12*, U13-9, U23-8, U5-8
IB7 ←→ U7-11, U6-12*, U14-11*, U13-12, U23-9, U5-9
```

### ABUS — Address Bus (A0-A15)

```
A0  ← U15-4     A8  ← U29-4
A1  ← U15-7     A9  ← U29-7
A2  ← U15-9     A10 ← U29-9
A3  ← U15-12    A11 ← U29-12
A4  ← U16-4     A12 ← U30-4
A5  ← U16-7     A13 ← U30-7
A6  ← U16-9     A14 ← U30-9
A7  ← U16-12    A15 ← U30-12
```

---

## Chip Pin Wiring

### U1-U2 74HC161 — PC Low (bits 0-7)

```
U1: PC bits 0-3
U1-1  (/CLR) ← /RST          U1-2  (CLK)  ← CLK
U1-3  (D0)   ← IRL0 (U6-19)  U1-4  (D1)   ← IRL1 (U6-18)
U1-5  (D2)   ← IRL2 (U6-17)  U1-6  (D3)   ← IRL3 (U6-16)
U1-7  (ENP)  ← PC_INC (U25-6)
U1-8  (GND)  → GND
U1-9  (/LD)  ← /PC_LD (U26-11)
U1-10 (ENT)  ← PC_INC (U25-6)
U1-11 (QD)   → PC3 → U15-14
U1-12 (QC)   → PC2 → U15-11
U1-13 (QB)   → PC1 → U15-5
U1-14 (QA)   → PC0 → U15-2
U1-15 (RCO)  → U2-10
U1-16 (VCC)  → VCC

U2: PC bits 4-7
U2-1  (/CLR) ← /RST          U2-2  (CLK)  ← CLK
U2-3  (D0)   ← IRL4 (U6-15)  U2-4  (D1)   ← IRL5 (U6-14)
U2-5  (D2)   ← IRL6 (U6-13)  U2-6  (D3)   ← IRL7 (U6-12)
U2-7  (ENP)  ← PC_INC (U25-6)
U2-8  (GND)  → GND
U2-9  (/LD)  ← /PC_LD (U26-11)
U2-10 (ENT)  ← U1-15 (RCO)
U2-11 (QD)   → PC7 → U16-14
U2-12 (QC)   → PC6 → U16-11
U2-13 (QB)   → PC5 → U16-5
U2-14 (QA)   → PC4 → U16-2
U2-15 (RCO)  → U3-10
U2-16 (VCC)  → VCC
```

### U3-U4 74HC161 — PC High (bits 8-15)

```
U3: PC bits 8-11
U3-1  (/CLR) ← /RST          U3-2  (CLK)  ← CLK
U3-3  (D0)   ← PG0 (U23-19)  U3-4  (D1)   ← PG1 (U23-18)
U3-5  (D2)   ← PG2 (U23-17)  U3-6  (D3)   ← PG3 (U23-16)
U3-7  (ENP)  ← PC_INC (U25-6)
U3-8  (GND)  → GND
U3-9  (/LD)  ← /PC_LD (U26-11)
U3-10 (ENT)  ← U2-15 (RCO)
U3-11 (QD)   → PC11 → U29-14
U3-12 (QC)   → PC10 → U29-11
U3-13 (QB)   → PC9  → U29-5
U3-14 (QA)   → PC8  → U29-2
U3-15 (RCO)  → U4-10
U3-16 (VCC)  → VCC

U4: PC bits 12-15
U4-1  (/CLR) ← /RST          U4-2  (CLK)  ← CLK
U4-3  (D0)   ← PG4 (U23-15)  U4-4  (D1)   ← PG5 (U23-14)
U4-5  (D2)   ← PG6 (U23-13)  U4-6  (D3)   ← PG7 (U23-12)
U4-7  (ENP)  ← PC_INC (U25-6)
U4-8  (GND)  → GND
U4-9  (/LD)  ← /PC_LD (U26-11)
U4-10 (ENT)  ← U3-15 (RCO)
U4-11 (QD)   → PC15 → U30-14
U4-12 (QC)   → PC14 → U30-11
U4-13 (QB)   → PC13 → U30-5
U4-14 (QA)   → PC12 → U30-2
U4-15 (RCO)  → NC
U4-16 (VCC)  → VCC
```

### U5 74HC574 — IR_HIGH (Control Byte)

```
U5-1  (/OE) → GND
U5-2  (D1)  ← IB0             U5-3  (D2)  ← IB1
U5-4  (D3)  ← IB2             U5-5  (D4)  ← IB3
U5-6  (D5)  ← IB4             U5-7  (D6)  ← IB5
U5-8  (D7)  ← IB6             U5-9  (D8)  ← IB7
U5-10 (GND) → GND
U5-11 (CLK) ← T0 (U8-3)
U5-12 (Q8)  → ALU_SUB (bit7)
U5-13 (Q7)  → XOR_MODE (bit6)
U5-14 (Q6)  → MUX_SEL (bit5)
U5-15 (Q5)  → AC_WR (bit4)
U5-16 (Q4)  → SOURCE_TYPE (bit3)
U5-17 (Q3)  → STORE (bit2)
U5-18 (Q2)  → BRANCH (bit1)
U5-19 (Q1)  → JUMP (bit0)
U5-20 (VCC) → VCC
```

### U6 74HC574 — IR_LOW (Operand)

```
U6-1  (/OE) ← /IRL_OE (U26-3)
U6-2  (D1)  ← IB0             U6-3  (D2)  ← IB1
U6-4  (D3)  ← IB2             U6-5  (D4)  ← IB3
U6-6  (D5)  ← IB4             U6-7  (D6)  ← IB5
U6-8  (D7)  ← IB6             U6-9  (D8)  ← IB7
U6-10 (GND) → GND
U6-11 (CLK) ← T1 (U8-4)
U6-12 (Q8)  → IRL7 → U16-13, U2-6, IB7*
U6-13 (Q7)  → IRL6 → U16-10, U2-5, IB6*
U6-14 (Q6)  → IRL5 → U16-6, U2-4, IB5*
U6-15 (Q5)  → IRL4 → U16-3, U2-3, IB4*
U6-16 (Q4)  → IRL3 → U15-13, U1-6, IB3*
U6-17 (Q3)  → IRL2 → U15-10, U1-5, IB2*
U6-18 (Q2)  → IRL1 → U15-6, U1-4, IB1*
U6-19 (Q1)  → IRL0 → U15-3, U1-3, IB0*
U6-20 (VCC) → VCC
```

### U7 74HC245 — Bus Buffer (DBUS↔IBUS)

```
U7-1  (DIR) ← WR_DIR (U28-8)
U7-2  (A1)  ←→ D0             U7-18 (B1)  ←→ IB0
U7-3  (A2)  ←→ D1             U7-17 (B2)  ←→ IB1
U7-4  (A3)  ←→ D2             U7-16 (B3)  ←→ IB2
U7-5  (A4)  ←→ D3             U7-15 (B4)  ←→ IB3
U7-6  (A5)  ←→ D4             U7-14 (B5)  ←→ IB4
U7-7  (A6)  ←→ D5             U7-13 (B6)  ←→ IB5
U7-8  (A7)  ←→ D6             U7-12 (B7)  ←→ IB6
U7-9  (A8)  ←→ D7             U7-11 (B8)  ←→ IB7
U7-10 (GND) → GND
U7-19 (/OE) ← BUF_OE_SAFE (U25-8)
U7-20 (VCC) → VCC
```

### U8 74HC164 — Ring Counter (T0/T1/T2)

```
U8-1  (A)    ← NOT(Q0) (U24-2)
U8-2  (B)    ← NOT(Q1) (U24-4)
U8-3  (Q0)   → T0
U8-4  (Q1)   → T1
U8-5  (Q2)   → T2
U8-6  (Q3)   → NC
U8-7  (GND)  → GND
U8-8  (CLK)  ← CLK
U8-9  (/CLR) ← /RST
U8-10..13    → NC
U8-14 (VCC)  → VCC
```

### U9 74HC574 — Accumulator

```
U9-1  (/OE) → GND
U9-2  (D1)  ← U17-4 (Y0)     U9-3  (D2)  ← U17-7 (Y1)
U9-4  (D3)  ← U17-9 (Y2)     U9-5  (D4)  ← U17-12 (Y3)
U9-6  (D5)  ← U18-4 (Y4)     U9-7  (D6)  ← U18-7 (Y5)
U9-8  (D7)  ← U18-9 (Y6)     U9-9  (D8)  ← U18-12 (Y7)
U9-10 (GND) → GND
U9-11 (CLK) ← Acc_Load_N (U27-11)
U9-12 (Q8)  → AC7 → U11-12, U20-13, U14-9, U22-18
U9-13 (Q7)  → AC6 → U11-14, U20-10, U14-8, U22-16
U9-14 (Q6)  → AC5 → U11-3, U20-6, U14-7, U22-14
U9-15 (Q5)  → AC4 → U11-5, U20-3, U14-6, U22-12
U9-16 (Q4)  → AC3 → U10-12, U19-13, U14-5, U22-8
U9-17 (Q3)  → AC2 → U10-14, U19-10, U14-4, U22-6
U9-18 (Q2)  → AC1 → U10-3, U19-6, U14-3, U22-4
U9-19 (Q1)  → AC0 → U10-5, U19-3, U14-2, U22-2
U9-20 (VCC) → VCC
```

### U10-U11 74HC283 — ALU Adder

```
U10: bits 0-3
U10-5 (A0) ← AC0    U10-6 (B0) ← XOR_Y0 (U12-3)
U10-3 (A1) ← AC1    U10-2 (B1) ← XOR_Y1 (U12-6)
U10-14(A2) ← AC2    U10-15(B2) ← XOR_Y2 (U12-8)
U10-12(A3) ← AC3    U10-11(B3) ← XOR_Y3 (U12-11)
U10-7 (Cin) ← ALU_SUB (U5-12)
U10-4 (S0) → SUM0 → U17-2     U10-1 (S1) → SUM1 → U17-5
U10-13(S2) → SUM2 → U17-11    U10-10(S3) → SUM3 → U17-14
U10-9 (Cout) → U11-7
U10-8 (GND) → GND   U10-16(VCC) → VCC

U11: bits 4-7
U11-5 (A0) ← AC4    U11-6 (B0) ← XOR_Y4 (U13-3)
U11-3 (A1) ← AC5    U11-2 (B1) ← XOR_Y5 (U13-6)
U11-14(A2) ← AC6    U11-15(B2) ← XOR_Y6 (U13-8)
U11-12(A3) ← AC7    U11-11(B3) ← XOR_Y7 (U13-11)
U11-7 (Cin) ← U10-9 (Cout)
U11-4 (S0) → SUM4 → U18-2     U11-1 (S1) → SUM5 → U18-5
U11-13(S2) → SUM6 → U18-11    U11-10(S3) → SUM7 → U18-14
U11-9 (Cout) → NC
U11-8 (GND) → GND   U11-16(VCC) → VCC
```

### U12-U13 74HC86 — XOR Array

```
U12: bits 0-3 (A=IBUS, B=mux output)
U12-1 (A1) ← IB0    U12-2 (B1) ← U19-4    U12-3 (Y1) → XOR_Y0 → U10-6, U17-3
U12-4 (A2) ← IB1    U12-5 (B2) ← U19-7    U12-6 (Y2) → XOR_Y1 → U10-2, U17-6
U12-9 (A3) ← IB2    U12-10(B3) ← U19-9    U12-8 (Y3) → XOR_Y2 → U10-15, U17-10
U12-12(A4) ← IB3    U12-13(B4) ← U19-12   U12-11(Y4) → XOR_Y3 → U10-11, U17-13
U12-7 (GND) → GND   U12-14(VCC) → VCC

U13: bits 4-7
U13-1 (A1) ← IB4    U13-2 (B1) ← U20-4    U13-3 (Y1) → XOR_Y4 → U11-6, U18-3
U13-4 (A2) ← IB5    U13-5 (B2) ← U20-7    U13-6 (Y2) → XOR_Y5 → U11-2, U18-6
U13-9 (A3) ← IB6    U13-10(B3) ← U20-9    U13-8 (Y3) → XOR_Y6 → U11-15, U18-10
U13-12(A4) ← IB7    U13-13(B4) ← U20-12   U13-11(Y4) → XOR_Y7 → U11-11, U18-13
U13-7 (GND) → GND   U13-14(VCC) → VCC
```

### U14 74HC541 — AC Output Buffer

```
U14-1 (/OE1) ← /AC_BUF (U26-8)
U14-2  (A1) ← AC0    U14-18 (Y1) → IB0
U14-3  (A2) ← AC1    U14-17 (Y2) → IB1
U14-4  (A3) ← AC2    U14-16 (Y3) → IB2
U14-5  (A4) ← AC3    U14-15 (Y4) → IB3
U14-6  (A5) ← AC4    U14-14 (Y5) → IB4
U14-7  (A6) ← AC5    U14-13 (Y6) → IB5
U14-8  (A7) ← AC6    U14-12 (Y7) → IB6
U14-9  (A8) ← AC7    U14-11 (Y8) → IB7
U14-10 (GND) → GND
U14-19 (/OE2) ← /AC_BUF (U26-8)
U14-20 (VCC) → VCC
```

### U15-U16 74HC157 — Address Mux A[7:0] (PC vs IRL)

```
SEL=0: PC, SEL=1: IRL

U15-1 (SEL) ← ADDR_MODE (U25-3)    U15-15(/E) → GND
U15-2 (1A) ← PC0   U15-3 (1B) ← IRL0   U15-4 (1Y) → A0
U15-5 (2A) ← PC1   U15-6 (2B) ← IRL1   U15-7 (2Y) → A1
U15-11(3A) ← PC2   U15-10(3B) ← IRL2   U15-9 (3Y) → A2
U15-14(4A) ← PC3   U15-13(4B) ← IRL3   U15-12(4Y) → A3
U15-8 (GND) → GND  U15-16(VCC) → VCC

U16-1 (SEL) ← ADDR_MODE             U16-15(/E) → GND
U16-2 (1A) ← PC4   U16-3 (1B) ← IRL4   U16-4 (1Y) → A4
U16-5 (2A) ← PC5   U16-6 (2B) ← IRL5   U16-7 (2Y) → A5
U16-11(3A) ← PC6   U16-10(3B) ← IRL6   U16-9 (3Y) → A6
U16-14(4A) ← PC7   U16-13(4B) ← IRL7   U16-12(4Y) → A7
U16-8 (GND) → GND  U16-16(VCC) → VCC
```

### U17-U18 74HC157 — AC Input Mux (Adder vs XOR)

```
SEL=0: Adder SUM, SEL=1: XOR output

U17-1 (SEL) ← MUX_SEL (U5-14)      U17-15(/E) → GND
U17-2 (1A) ← SUM0   U17-3 (1B) ← XOR_Y0   U17-4 (1Y) → U9-2
U17-5 (2A) ← SUM1   U17-6 (2B) ← XOR_Y1   U17-7 (2Y) → U9-3
U17-11(3A) ← SUM2   U17-10(3B) ← XOR_Y2   U17-9 (3Y) → U9-4
U17-14(4A) ← SUM3   U17-13(4B) ← XOR_Y3   U17-12(4Y) → U9-5
U17-8 (GND) → GND   U17-16(VCC) → VCC

U18-1 (SEL) ← MUX_SEL (U5-14)      U18-15(/E) → GND
U18-2 (1A) ← SUM4   U18-3 (1B) ← XOR_Y4   U18-4 (1Y) → U9-6
U18-5 (2A) ← SUM5   U18-6 (2B) ← XOR_Y5   U18-7 (2Y) → U9-7
U18-11(3A) ← SUM6   U18-10(3B) ← XOR_Y6   U18-9 (3Y) → U9-8
U18-14(4A) ← SUM7   U18-13(4B) ← XOR_Y7   U18-12(4Y) → U9-9
U18-8 (GND) → GND   U18-16(VCC) → VCC
```

### U19-U20 74HC157 — XOR B-Input Mux (SUB vs AC)

```
SEL=0: ALU_SUB (for ADD/SUB), SEL=1: AC bits (for XOR instr)

U19-1 (SEL) ← XOR_MODE (U5-13)     U19-15(/E) → GND
U19-2 (1A) ← SUB   U19-3 (1B) ← AC0   U19-4 (1Y) → U12-2
U19-5 (2A) ← SUB   U19-6 (2B) ← AC1   U19-7 (2Y) → U12-5
U19-11(3A) ← SUB   U19-10(3B) ← AC2   U19-9 (3Y) → U12-10
U19-14(4A) ← SUB   U19-13(4B) ← AC3   U19-12(4Y) → U12-13
U19-8 (GND) → GND  U19-16(VCC) → VCC

U20-1 (SEL) ← XOR_MODE (U5-13)     U20-15(/E) → GND
U20-2 (1A) ← SUB   U20-3 (1B) ← AC4   U20-4 (1Y) → U13-2
U20-5 (2A) ← SUB   U20-6 (2B) ← AC5   U20-7 (2Y) → U13-5
U20-11(3A) ← SUB   U20-10(3B) ← AC6   U20-9 (3Y) → U13-10
U20-14(4A) ← SUB   U20-13(4B) ← AC7   U20-12(4Y) → U13-13
U20-8 (GND) → GND  U20-16(VCC) → VCC
```

### U21 74HC74 — Z Flag

```
U21-1 (/CLR1) → VCC
U21-2 (D1)    → GND
U21-3 (CLK1)  ← Acc_Load_N (U27-11)
U21-4 (/PR1)  ← U22-19 (/P=Q)
U21-5 (Q1)    → Z_flag → U28-1
U21-6 (/Q1)   → NC
U21-7 (GND)   → GND
U21-8..13     → FF2 unused (CLK2=GND, /PR2=VCC, /CLR2=VCC, D2=GND)
U21-14(VCC)   → VCC
```

### U22 74HC688 — Zero Detect

```
U22-1 (/OE) → GND
U22-2 (P0) ← AC0   U22-3 (Q0) → GND
U22-4 (P1) ← AC1   U22-5 (Q1) → GND
U22-6 (P2) ← AC2   U22-7 (Q2) → GND
U22-8 (P3) ← AC3   U22-9 (Q3) → GND
U22-10(GND) → GND
U22-11(Q4) → GND   U22-12(P4) ← AC4
U22-13(Q5) → GND   U22-14(P5) ← AC5
U22-15(Q6) → GND   U22-16(P6) ← AC6
U22-17(Q7) → GND   U22-18(P7) ← AC7
U22-19(/P=Q) → U21-4
U22-20(VCC) → VCC
```

### U23 74HC574 — Page Register

```
U23-1 (/OE) → GND
U23-2 (D1) ← IB0   U23-3 (D2) ← IB1
U23-4 (D3) ← IB2   U23-5 (D4) ← IB3
U23-6 (D5) ← IB4   U23-7 (D6) ← IB5
U23-8 (D7) ← IB6   U23-9 (D8) ← IB7
U23-10(GND) → GND
U23-11(CLK) ← PG_Load_N (U25-13)
U23-12(Q8) → PG7 → U4-6     U23-13(Q7) → PG6 → U4-5
U23-14(Q6) → PG5 → U4-4     U23-15(Q5) → PG4 → U4-3
U23-16(Q4) → PG3 → U3-6     U23-17(Q3) → PG2 → U3-5
U23-18(Q2) → PG1 → U3-4     U23-19(Q1) → PG0 → U3-3
U23-20(VCC) → VCC
```

### U24 74HC04 — Inverters

```
U24-1 (1A) ← T0 (U8-3)         U24-2 (1Y) → NOT(Q0) → U8-1
U24-3 (2A) ← T1 (U8-4)         U24-4 (2Y) → NOT(Q1) → U8-2
U24-5 (3A) ← A15 (U30-12)      U24-6 (3Y) → /A15 → ROM /CE
U24-7 (GND) → GND
U24-9 (4A) ← JUMP (U5-19)      U24-8 (4Y) → /JUMP → U27-4
U24-11(5A) ← AC_WR (U5-15)     U24-10(5Y) → /AC_WR → U27-10
U24-13(6A) ← /IRL_OE (U26-3)   U24-12(6Y) → BUF_OE_N → U25-9
U24-14(VCC) → VCC
```

### U25 74HC32 — OR Gates

```
U25-1 (1A) ← SRC (U5-16)   U25-2 (1B) ← STR (U5-17)   U25-3 (1Y) → ADDR_MODE
U25-4 (2A) ← T0 (U8-3)     U25-5 (2B) ← T1 (U8-4)     U25-6 (2Y) → PC_INC
U25-7 (GND) → GND
U25-9 (3A) ← BUF_OE_N (U24-12)  U25-10(3B) ← STR (U5-17)  U25-8 (3Y) → BUF_OE_SAFE → U7-19
U25-11(4A) ← /T2 (U28-6)   U25-12(4B) ← /PG_cond(U27-8) U25-13(4Y) → PG_Load_N → U23-11
U25-14(VCC) → VCC
```

### U26 74HC00 — NAND #1

```
Gate A: /IRL_OE = NAND(T2, /ADDR_MODE)
U26-1 ← T2 (U8-5)   U26-2 ← /ADDR_MODE (U26-6)   U26-3 → /IRL_OE → U6-1, U24-13

Gate B: /ADDR_MODE = NAND(ADDR_MODE, ADDR_MODE) = NOT
U26-4 ← ADDR_MODE   U26-5 ← ADDR_MODE   U26-6 → /ADDR_MODE → U26-2

Gate C: /AC_BUF = NAND(T2, STORE)
U26-9 ← T2 (U8-5)   U26-10 ← STR (U5-17)   U26-8 → /AC_BUF → U14-1/19, RAM /WE, U28-9

Gate D: /PC_LD = NAND(T2, PC_LOAD_COND)
U26-12 ← T2 (U8-5)   U26-13 ← PC_LOAD_COND (U27-6)   U26-11 → /PC_LD → U1-9..U4-9

U26-7 (GND) → GND   U26-14(VCC) → VCC
```

### U27 74HC00 — NAND #2

```
Gate A: /BR_TAKEN = NAND(BRANCH, Z_match)
U27-1 ← BR (U5-18)   U27-2 ← Z_match (U28-3)   U27-3 → /BR_TAKEN → U27-5

Gate B: PC_LOAD_COND = NAND(/JUMP, /BR_TAKEN) = JUMP OR BR_TAKEN
U27-4 ← /JUMP (U24-8)   U27-5 ← /BR_TAKEN (U27-3)   U27-6 → PC_LOAD_COND → U26-13

Gate C: /PG_cond = NAND(MUX_SEL, /AC_WR)
U27-9 ← MUX (U5-14)   U27-10 ← /AC_WR (U24-10)   U27-8 → /PG_cond → U25-12

Gate D: Acc_Load_N = NAND(T2, AC_WR)
U27-12 ← T2 (U8-5)   U27-13 ← AC_WR (U5-15)   U27-11 → Acc_Load_N → U9-11, U21-3

U27-7 (GND) → GND   U27-14(VCC) → VCC
```

### U28 74HC86 — XOR (Misc)

```
Gate A: Z_match = Z_flag XOR ALU_SUB
U28-1 ← Z_flag (U21-5)   U28-2 ← SUB (U5-12)   U28-3 → Z_match → U27-2

Gate B: /T2 = T2 XOR 1 = NOT(T2)
U28-4 ← T2 (U8-5)   U28-5 → VCC   U28-6 → /T2 → U25-11

Gate C: WR_DIR = /AC_BUF XOR 1 = NOT(/AC_BUF)
U28-9 ← /AC_BUF (U26-8)   U28-10 → VCC   U28-8 → WR_DIR → U7-1

Gate D: spare
U28-12 → NC   U28-13 → NC   U28-11 → NC

U28-7 (GND) → GND   U28-14(VCC) → VCC
```

### U29-U30 74HC157 — Address Mux A[15:8] (PC high vs Data Page)

```
SEL=0: PC high, SEL=1: Data Page Register (U32 Q outputs)

U29-1 (SEL) ← ADDR_MODE        U29-15(/E) → GND
U29-2 (1A) ← PC8    U29-3 (1B) ← DP0 (U32-19)   U29-4 (1Y) → A8
U29-5 (2A) ← PC9    U29-6 (2B) ← DP1 (U32-18)   U29-7 (2Y) → A9
U29-11(3A) ← PC10   U29-10(3B) ← DP2 (U32-17)   U29-9 (3Y) → A10
U29-14(4A) ← PC11   U29-13(4B) ← DP3 (U32-16)   U29-12(4Y) → A11
U29-8 (GND) → GND   U29-16(VCC) → VCC

U30-1 (SEL) ← ADDR_MODE        U30-15(/E) → GND
U30-2 (1A) ← PC12   U30-3 (1B) ← DP4 (U32-15)   U30-4 (1Y) → A12
U30-5 (2A) ← PC13   U30-6 (2B) ← DP5 (U32-14)   U30-7 (2Y) → A13
U30-11(3A) ← PC14   U30-10(3B) ← DP6 (U32-13)   U30-9 (3Y) → A14
U30-14(4A) ← PC15   U30-13(4B) ← DP7 (U32-12)    U30-12(4Y) → A15 → RAM /CE, U24-5
U30-8 (GND) → GND   U30-16(VCC) → VCC
```

### U31 74HC74 — IRQ (IE_FF + IRQ_FF)

```
FF-A: IE flag
U31-1 (/CLR1) ← DI_decode OR IRQ_ack
U31-2 (D1)    → VCC
U31-3 (CLK1)  ← EI_decode (T2 AND ir_high=$08)
U31-4 (/PR1)  → VCC
U31-5 (Q1)    → IE → IRQ-ack gate
U31-6 (/Q1)   → NC

FF-B: IRQ latch
U31-7 (GND)   → GND
U31-8 (/CLR2) ← IRQ_ack
U31-9 (D2)    → VCC
U31-10(CLK2)  ← /IRQ (external, falling edge)
U31-11(/PR2)  → VCC
U31-12(Q2)    → IRQ_FF → IRQ-ack gate
U31-13(/Q2)   → NC
U31-14(VCC)   → VCC

IRQ_ack = T2 AND IE AND IRQ_FF AND /PC_LOAD_COND
On ack: force PG=$FF, IRL=$00, assert /PC_LD, save PC to RAM[$0E:$0F]
```

---

### U32 74HC574 — Data Page Register

```
U32-1 (/OE) → GND
U32-2 (D1) ← IB0   U32-3 (D2) ← IB1
U32-4 (D3) ← IB2   U32-5 (D4) ← IB3
U32-6 (D5) ← IB4   U32-7 (D6) ← IB5
U32-8 (D7) ← IB6   U32-9 (D8) ← IB7
U32-10(GND) → GND
U32-11(CLK) ← DP_Load (decode: T2 AND SETDP)
U32-12(Q8) → DP7 → U30-13 (A15 B-input, enables ROM read)
U32-13(Q7) → DP6 → U30-10 (A14 B-input)
U32-14(Q6) → DP5 → U30-6 (A13 B-input)
U32-15(Q5) → DP4 → U30-3 (A12 B-input)
U32-16(Q4) → DP3 → U29-13 (A11 B-input)
U32-17(Q3) → DP2 → U29-10 (A10 B-input)
U32-18(Q2) → DP1 → U29-6 (A9 B-input)
U32-19(Q1) → DP0 → U29-3 (A8 B-input)
U32-20(VCC) → VCC

### U33 74HC21 — SETDP Decode (dual 4-input AND)

```
U33-1  (1A) ← T2 (U8-5)
U33-2  (1B) ← XOR_MODE (U5-13)
U33-3  (NC)
U33-4  (1C) ← /ADDR_MODE (U26-6)
U33-5  (1D) ← /AC_WR (U24-10)
U33-6  (1Y) → DP_Load → U32-11
U33-7  (GND) → GND
U33-8  (2Y) → NC
U33-9  (2A) → VCC (unused gate, tie inputs high)
U33-10 (2B) → VCC
U33-11 (NC)
U33-12 (2C) → VCC
U33-13 (2D) → VCC
U33-14 (VCC) → VCC
```
U33-8  (2Y) → NC
U33-14 (VCC) → VCC
```

Decode verification:
| Opcode | T2 | XOR | /ADDR | /AC_WR | DP_Load |
|:------:|:--:|:---:|:-----:|:------:|:-------:|
| SETDP $40 | 1 | 1 | 1 | 1 | **1** ✓ |
| DI $48 | 1 | 1 | 0 | 1 | 0 ✓ |
| XORI $70 | 1 | 1 | 1 | 0 | 0 ✓ |
| SETPG $20 | 1 | 0 | 1 | 1 | 0 ✓ |
| $C0 (SUB+XOR) | 1 | 1 | 1 | 1 | **1** (= SETDP alias, harmless) |

Note: $C0 triggers DP_Load but is equivalent to SETDP (SUB bit has no effect when AC_WR=0).

---

### IRQ Save-PC Logic (Pin-Level)

During IRQ-ack, CPU must:
1. Write PC[7:0] to RAM[$0E]
2. Write PC[15:8] to RAM[$0F]
3. Force PC = $FF00

**Implementation**: IRQ-ack reuses existing STORE path with forced address.

```
IRQ_ack = T2 AND IRQ_FF(U31-12) AND IE(U31-5) AND NOT(PC_LOAD_COND)

During IRQ-ack (extra 2 cycles inserted by hardware):

Cycle 1 — Save PC low:
  Force ADDR_MODE=1, address=$0E
  Force AC buffer to drive PC[7:0] onto IBUS (override U14 input)
  RAM /WE pulse → RAM[$0E] = PC[7:0]

Cycle 2 — Save PC high:
  Force address=$0F
  Drive PC[15:8] onto IBUS
  RAM /WE pulse → RAM[$0F] = PC[15:8]

Then:
  Force page_reg = $FF, ir_low = $00
  Assert /PC_LD → PC loads $FF00
  Clear IE (U31 /CLR1)
  Clear IRQ_FF (U31 /CLR2)
```

**Hardware complexity note**:
The IRQ save-PC requires additional multiplexing to:
- Drive PC bytes onto IBUS (normally only AC goes to IBUS via U14)
- Force address $0E/$0F (normally IRL provides address)

**Options for physical build**:

| Approach | Extra Chips | Complexity |
|----------|:-----------:|:----------:|
| A: Software save (ISR reads PC from known location) | 0 | Simple |
| B: Dedicated save circuit (mux PC onto bus) | 2-3 chips | Complex |
| C: Use return address register (like CALL) | 1 chip | Medium |

**Recommended for v1.0 build: Option A (software ISR)**

In practice, the Verilog model handles save-PC in behavioral code.
For physical build v1.0, the ISR at $FF00 can use a fixed return point
or the programmer can store return address before enabling interrupts.

Future v2.0: Add dedicated PC-save hardware if needed.

Note: A15 from U32 bit 7 → allows data access to both ROM and RAM (full 64KB).

---

## ROM & RAM

```
ROM (AT28C256 / SST39SF010A)
  A[0:7]  ← ABUS A[0:7]
  A[8:14] ← ABUS A[8:14]
  D[0:7]  → DBUS
  /CE     ← /A15 (U24-6)
  /OE     → GND
  /WE     → VCC

RAM (62256)
  A[0:7]  ← ABUS A[0:7]
  A[8:14] ← ABUS A[8:14]
  D[0:7]  ←→ DBUS
  /CE     ← A15 (U30-12)
  /OE     → GND
  /WE     ← /AC_BUF (U26-8)
```

---

## Control Signal Summary

| Signal | Source | Destinations |
|--------|--------|-------------|
| CLK | Oscillator | U1-2, U2-2, U3-2, U4-2, U8-8 |
| /RST | RC+button | U1-1, U2-1, U3-1, U4-1, U8-9 |
| T0 | U8-3 | U5-11, U25-4, U24-1 |
| T1 | U8-4 | U6-11, U25-5, U24-3 |
| T2 | U8-5 | U26-1, U26-9, U26-12, U27-12, U28-4 |
| ALU_SUB | U5-12 | U10-7, U19-2/5/11/14, U20-2/5/11/14, U28-2 |
| XOR_MODE | U5-13 | U19-1, U20-1 |
| MUX_SEL | U5-14 | U17-1, U18-1, U27-9 |
| AC_WR | U5-15 | U24-11, U27-13 |
| SRC | U5-16 | U25-1 |
| STR | U5-17 | U25-2, U26-10 |
| BR | U5-18 | U25-10, U27-1 |
| JMP | U5-19 | U24-9, U25-9 |
| ADDR_MODE | U25-3 | U15-1, U16-1, U29-1, U30-1, U26-4/5 |
| PC_INC | U25-6 | U1-7/10, U2-7, U3-7, U4-7 |
| /PC_LD | U26-11 | U1-9, U2-9, U3-9, U4-9 |
| /AC_BUF | U26-8 | U14-1/19, RAM /WE, U28-9 |
| Acc_Load_N | U27-11 | U9-11, U21-3 |
| BUF_OE_N | U24-12 | U25-9 |
| BUF_OE_SAFE | U25-8 | U7-19 |
| WR_DIR | U28-8 | U7-1 |
| A15 | U30-12 | RAM /CE, U24-5 |
| PG_Load_N | U25-13 | U23-11 |
| DP_Load | U33-6 | U32-11 |

---

## Power

| Package | VCC | GND | Bypass |
|---------|:---:|:---:|:------:|
| 74HC161 (U1-U4) | 16 | 8 | 100nF |
| 74HC574 (U5,U6,U9,U23,U32) | 20 | 10 | 100nF |
| 74HC21 (U33) | 14 | 7 | 100nF |
| 74HC245 (U7) | 20 | 10 | 100nF |
| 74HC164 (U8) | 14 | 7 | 100nF |
| 74HC283 (U10-U11) | 16 | 8 | 100nF |
| 74HC86 (U12,U13,U28) | 14 | 7 | 100nF |
| 74HC541 (U14) | 20 | 10 | 100nF |
| 74HC157 (U15-U20,U29-U30) | 16 | 8 | 100nF |
| 74HC74 (U21,U31) | 14 | 7 | 100nF |
| 74HC688 (U22) | 20 | 10 | 100nF |
| 74HC04 (U24) | 14 | 7 | 100nF |
| 74HC32 (U25) | 14 | 7 | 100nF |
| 74HC00 (U26-U27) | 14 | 7 | 100nF |
