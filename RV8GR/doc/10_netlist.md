# RV8-GR Netlist

**Source of truth**: `01_wiring_guide.md`  
**Generated**: 2026-06-30  
**Reviewed**: 2026-07-10 against `01_wiring_guide.md` and wiring verifier
**Chips**: 34 logic (U1-U34) + ROM + RAM = 36 packages

This document lists every net (named signal) in the RV8-GR CPU with all
connected chip pins. Use for schematic capture, KiCad import, or breadboard
cross-checking.

---

## Naming Conventions

| Convention | Meaning | Example |
|------------|---------|---------|
| `/NAME` | Active-low signal | `/RST`, `/PC_LD` |
| `NAME_N` | Active-low (alternate) | `BUF_OE_N` |
| `NAMEn` | Bit n of a bus | `ABUS0`, `IBUS7` |
| `*` after pin | Tri-state driver (only active when enabled) | `U34-18*` |
| `←` | Input | |
| `→` | Output | |
| `←→` | Bidirectional | |

---

## Power Nets

### VCC (+5V)

| Chip | Pin |
|------|:---:|
| U1 (74HC161) | 16 |
| U2 (74HC161) | 16 |
| U3 (74HC161) | 16 |
| U4 (74HC161) | 16 |
| U5 (74HC574) | 20 |
| U6 (74HC574) | 20 |
| U7 (74HC245) | 20 |
| U8 (74HC164) | 14 |
| U9 (74HC574) | 20 |
| U10 (74HC283) | 16 |
| U11 (74HC283) | 16 |
| U12 (74HC86) | 14 |
| U13 (74HC86) | 14 |
| U14 (74HC541) | 20 |
| U15 (74HC157) | 16 |
| U16 (74HC157) | 16 |
| U17 (74HC157) | 16 |
| U18 (74HC157) | 16 |
| U19 (74HC157) | 16 |
| U20 (74HC157) | 16 |
| U21 (74HC74) | 14 |
| U22 (74HC688) | 20 |
| U23 (74HC574) | 20 |
| U24 (74HC04) | 14 |
| U25 (74HC32) | 14 |
| U26 (74HC00) | 14 |
| U27 (74HC00) | 14 |
| U28 (74HC86) | 14 |
| U29 (74HC157) | 16 |
| U30 (74HC157) | 16 |
| U31 (74HC74) | 14 |
| U32 (74HC574) | 20 |
| U33 (74HC21) | 14 |
| U34 (74HC541) | 20 |
| ROM (AT28C256) | 28 |
| RAM (62256) | 28 |

Also tied to VCC:
- U21-1 (/CLR1), U21-10 (/PR2), U21-13 (/CLR2) — VCC
- U28-5, U28-10, U28-13 — VCC (XOR with VCC = invert)
- U31-2 (D1), U31-4 (/PR1), U31-10 (/PR2), U31-12 (D2) — VCC

### GND

| Chip | Pin |
|------|:---:|
| U1 (74HC161) | 8 |
| U2 (74HC161) | 8 |
| U3 (74HC161) | 8 |
| U4 (74HC161) | 8 |
| U5 (74HC574) | 10 |
| U6 (74HC574) | 10 |
| U7 (74HC245) | 10 |
| U8 (74HC164) | 7 |
| U9 (74HC574) | 10 |
| U10 (74HC283) | 8 |
| U11 (74HC283) | 8 |
| U12 (74HC86) | 7 |
| U13 (74HC86) | 7 |
| U14 (74HC541) | 10 |
| U15 (74HC157) | 8 |
| U16 (74HC157) | 8 |
| U17 (74HC157) | 8 |
| U18 (74HC157) | 8 |
| U19 (74HC157) | 8 |
| U20 (74HC157) | 8 |
| U21 (74HC74) | 7 |
| U22 (74HC688) | 10 |
| U23 (74HC574) | 10 |
| U24 (74HC04) | 7 |
| U25 (74HC32) | 7 |
| U26 (74HC00) | 7 |
| U27 (74HC00) | 7 |
| U28 (74HC86) | 7 |
| U29 (74HC157) | 8 |
| U30 (74HC157) | 8 |
| U31 (74HC74) | 7 |
| U32 (74HC574) | 10 |
| U33 (74HC21) | 7 |
| U34 (74HC541) | 10 |
| ROM (AT28C256) | 14 |
| RAM (62256) | 14 |

Also tied to GND:
- U5-1 (/OE), U9-1 (/OE), U23-1 (/OE), U32-1 (/OE) — always enabled
- U15-15, U16-15, U17-15, U18-15, U19-15, U20-15, U29-15, U30-15 (/E) — mux always enabled
- U21-2 (D1), U21-11 (CLK2), U21-12 (D2) — GND
- U22-1 (/OE), U22-3, U22-5, U22-7, U22-9, U22-12, U22-14, U22-16, U22-18 (B0-B7) — GND
- U25-9, U25-10 (spare gate inputs) — GND
- RAM /OE — GND (always output enabled)

---

## Clock & Reset Nets

### CLK (System Clock — 1 MHz)

Source: Oscillator

| Destination | Pin |
|-------------|:---:|
| U1 (PC 0-3) | 2 |
| U2 (PC 4-7) | 2 |
| U3 (PC 8-11) | 2 |
| U4 (PC 12-15) | 2 |
| U8 (Ring Counter) | 8 |
| RV8-Bus | pin 25 |

### /RST (Active-Low Reset)

Source: RC circuit (10kΩ + 10µF → 74HC14 Schmitt)

| Destination | Pin |
|-------------|:---:|
| U1 (PC 0-3) /CLR | 1 |
| U2 (PC 4-7) /CLR | 1 |
| U3 (PC 8-11) /CLR | 1 |
| U4 (PC 12-15) /CLR | 1 |
| U8 (Ring Counter) /CLR | 9 |
| U31 (IRQ) /CLR1 | 1 |
| U31 (IRQ) /CLR2 | 13 |
| RV8-Bus | pin 26 |

---

## Ring Counter Nets (T0, T1, T2)

### T0

Source: U8-3 (Q0)

| Destination | Pin | Purpose |
|-------------|:---:|---------|
| U5 (IR_HIGH) CLK | 11 | Latch opcode on T0↑ |
| U25 (OR) gate 2 input A | 4 | PC_INC = T0 OR T1 |
| U24 (INV) input 1A | 1 | NOT(Q0) → U8-1 feedback |

### T1

Source: U8-4 (Q1)

| Destination | Pin | Purpose |
|-------------|:---:|---------|
| U6 (IR_LOW) CLK | 11 | Latch operand on T1↑ |
| U25 (OR) gate 2 input B | 5 | PC_INC = T0 OR T1 |
| U24 (INV) input 2A | 3 | NOT(Q1) → U8-2 feedback |

### T2

Source: U8-5 (Q2)

| Destination | Pin | Purpose |
|-------------|:---:|---------|
| U26 (NAND) gate A input | 1 | /IRL_OE decode |
| U26 (NAND) gate C input | 9 | /AC_BUF decode |
| U26 (NAND) gate D input | 12 | /PC_LD decode |
| U27 (NAND) gate D input | 12 | ACC_CLK |
| U28 (XOR) gate B input | 4 | /T2 = NOT(T2) |
| U33 (AND) gate 1 input A | 1 | DP_Load decode |
| U33 (AND) gate 2 input A | 9 | EI_decode |
| RV8-Bus | pin 32 | Expansion timing |

### /T2

Source: U28-6 (T2 XOR VCC = NOT T2)

| Destination | Pin | Purpose |
|-------------|:---:|---------|
| U25 (OR) gate 4 input A | 11 | PG_CLK generation |

### Ring Counter Feedback

| Net | Source | Destination |
|-----|--------|-------------|
| NOT(Q0) | U24-2 | U8-1 (A input) |
| NOT(Q1) | U24-4 | U8-2 (B input) |

---

## Bus Nets

### ABUS (Address Bus — 16-bit)

Source: Address mux outputs (U15, U16, U29, U30)

| Net | Source | Destinations |
|-----|--------|-------------|
| ABUS0 | U15-4 | ROM A0, RAM A0, RV8-Bus pin 1 |
| ABUS1 | U15-7 | ROM A1, RAM A1, RV8-Bus pin 2 |
| ABUS2 | U15-9 | ROM A2, RAM A2, RV8-Bus pin 3 |
| ABUS3 | U15-12 | ROM A3, RAM A3, RV8-Bus pin 4 |
| ABUS4 | U16-4 | ROM A4, RAM A4, RV8-Bus pin 5 |
| ABUS5 | U16-7 | ROM A5, RAM A5, RV8-Bus pin 6 |
| ABUS6 | U16-9 | ROM A6, RAM A6, RV8-Bus pin 7 |
| ABUS7 | U16-12 | ROM A7, RAM A7, RV8-Bus pin 8 |
| ABUS8 | U29-4 | ROM A8, RAM A8, RV8-Bus pin 9 |
| ABUS9 | U29-7 | ROM A9, RAM A9, RV8-Bus pin 10 |
| ABUS10 | U29-9 | ROM A10, RAM A10, RV8-Bus pin 11 |
| ABUS11 | U29-12 | ROM A11, RAM A11, RV8-Bus pin 12 |
| ABUS12 | U30-4 | ROM A12, RAM A12, RV8-Bus pin 13 |
| ABUS13 | U30-7 | ROM A13, RAM A13, RV8-Bus pin 14 |
| ABUS14 | U30-9 | ROM A14, RAM A14, RV8-Bus pin 15 |
| ABUS15 | U30-12 | ROM /CE, U24-5 (→/A15), RV8-Bus pin 16, RV8-Bus pin 33 |

### DBUS (Data Bus — 8-bit, bidirectional)

Shared by: ROM data out, RAM data I/O, U7 B-side, RV8-Bus D[7:0]

| Net | U7 pin | ROM pin | RAM pin | RV8-Bus pin |
|-----|:------:|:-------:|:-------:|:-----------:|
| DBUS0 | 18 (B1) | D0 | D0 | 17 |
| DBUS1 | 17 (B2) | D1 | D1 | 18 |
| DBUS2 | 16 (B3) | D2 | D2 | 19 |
| DBUS3 | 15 (B4) | D3 | D3 | 20 |
| DBUS4 | 14 (B5) | D4 | D4 | 21 |
| DBUS5 | 13 (B6) | D5 | D5 | 22 |
| DBUS6 | 12 (B7) | D6 | D6 | 23 |
| DBUS7 | 11 (B8) | D7 | D7 | 24 |

### IBUS (Internal Data Bus — 8-bit)

Drivers (tri-state — only one active at a time):
- U7 A-side (fetch/load — DIR=0: B→A)
- U34 Y outputs (immediate — U6 IR_LOW feeds U34 A inputs; U34 drives only when `/IRL_OE=LOW`)
- U14 Y outputs (store — /OE=LOW)

| Net | U7 | U34* | U14* | U12/U13 | U5 D | U6 D | U23 D | U32 D |
|-----|:--:|:----:|:----:|:-------:|:----:|:----:|:-----:|:-----:|
| IBUS0 | 2 | 18 | 18 | U12-1 | 2 | 2 | 2 | 2 |
| IBUS1 | 3 | 17 | 17 | U12-4 | 3 | 3 | 3 | 3 |
| IBUS2 | 4 | 16 | 16 | U12-9 | 4 | 4 | 4 | 4 |
| IBUS3 | 5 | 15 | 15 | U12-12 | 5 | 5 | 5 | 5 |
| IBUS4 | 6 | 14 | 14 | U13-1 | 6 | 6 | 6 | 6 |
| IBUS5 | 7 | 13 | 13 | U13-4 | 7 | 7 | 7 | 7 |
| IBUS6 | 8 | 12 | 12 | U13-9 | 8 | 8 | 8 | 8 |
| IBUS7 | 9 | 11 | 11 | U13-12 | 9 | 9 | 9 | 9 |

---

## Register Output Nets

### PC (Program Counter — 16-bit)

| Net | Source | Destinations |
|-----|--------|-------------|
| PC0 | U1-14 (QA) | U15-3 (mux B low 1B) |
| PC1 | U1-13 (QB) | U15-6 (mux B low 2B) |
| PC2 | U1-12 (QC) | U15-10 (mux B low 3B) |
| PC3 | U1-11 (QD) | U15-13 (mux B low 4B) |
| PC4 | U2-14 (QA) | U16-3 (mux B low 1B) |
| PC5 | U2-13 (QB) | U16-6 (mux B low 2B) |
| PC6 | U2-12 (QC) | U16-10 (mux B low 3B) |
| PC7 | U2-11 (QD) | U16-13 (mux B low 4B) |
| PC8 | U3-14 (QA) | U29-3 (mux B high 1B) |
| PC9 | U3-13 (QB) | U29-6 (mux B high 2B) |
| PC10 | U3-12 (QC) | U29-10 (mux B high 3B) |
| PC11 | U3-11 (QD) | U29-13 (mux B high 4B) |
| PC12 | U4-14 (QA) | U30-3 (mux B high 1B) |
| PC13 | U4-13 (QB) | U30-6 (mux B high 2B) |
| PC14 | U4-12 (QC) | U30-10 (mux B high 3B) |
| PC15 | U4-11 (QD) | U30-13 (mux B high 4B) |

Carry chain:
| Net | Source | Destination |
|-----|--------|-------------|
| RCO_0 | U1-15 | U2-10 (ENT) |
| RCO_1 | U2-15 | U3-10 (ENT) |
| RCO_2 | U3-15 | U4-10 (ENT) |

### IRL (Operand Register — 8-bit)

Source: U6 Q outputs. IRL feeds PC load D-inputs (U1-U2), address mux A-inputs (U15-U16), and the U34 immediate buffer.

| Net | Source | Destinations |
|-----|--------|-------------|
| IRL0 | U6-19 | U15-2 (mux 1A), U1-3 (PC D0), U34-2 |
| IRL1 | U6-18 | U15-5 (mux 2A), U1-4 (PC D1), U34-3 |
| IRL2 | U6-17 | U15-11 (mux 3A), U1-5 (PC D2), U34-4 |
| IRL3 | U6-16 | U15-14 (mux 4A), U1-6 (PC D3), U34-5 |
| IRL4 | U6-15 | U16-2 (mux 1A), U2-3 (PC D0), U34-6 |
| IRL5 | U6-14 | U16-5 (mux 2A), U2-4 (PC D1), U34-7 |
| IRL6 | U6-13 | U16-11 (mux 3A), U2-5 (PC D2), U34-8 |
| IRL7 | U6-12 | U16-14 (mux 4A), U2-6 (PC D3), U34-9 |

### PG (Page Register — 8-bit)

Source: U23 Q outputs. Feeds PC high load D-inputs (U3-U4).

| Net | Source | Destination |
|-----|--------|-------------|
| PG0 | U23-19 | U3-3 (D0) |
| PG1 | U23-18 | U3-4 (D1) |
| PG2 | U23-17 | U3-5 (D2) |
| PG3 | U23-16 | U3-6 (D3) |
| PG4 | U23-15 | U4-3 (D0) |
| PG5 | U23-14 | U4-4 (D1) |
| PG6 | U23-13 | U4-5 (D2) |
| PG7 | U23-12 | U4-6 (D3) |

### DP (Data Page Register — 8-bit)

Source: U32 Q outputs. Feeds address mux high A-inputs (U29-U30).

| Net | Source | Destination |
|-----|--------|-------------|
| DP0 | U32-19 | U29-2 (1A) |
| DP1 | U32-18 | U29-5 (2A) |
| DP2 | U32-17 | U29-11 (3A) |
| DP3 | U32-16 | U29-14 (4A) |
| DP4 | U32-15 | U30-2 (1A) |
| DP5 | U32-14 | U30-5 (2A) |
| DP6 | U32-13 | U30-11 (3A) |
| DP7 | U32-12 | U30-14 (4A) |

### AC (Accumulator — 8-bit)

Source: U9 Q outputs. Feeds: adder A-inputs, XOR B-mux B-inputs, store buffer (U14), zero detect (U22).

| Net | Source | U10/U11 (Adder A) | U19/U20 (XOR mux B) | U14 (Buffer A) | U22 (Zero P) |
|-----|--------|:------------------:|:--------------------:|:--------------:|:------------:|
| AC0 | U9-19 | U10-5 | U19-3 | U14-2 | U22-2 |
| AC1 | U9-18 | U10-3 | U19-6 | U14-3 | U22-4 |
| AC2 | U9-17 | U10-14 | U19-10 | U14-4 | U22-6 |
| AC3 | U9-16 | U10-12 | U19-13 | U14-5 | U22-8 |
| AC4 | U9-15 | U11-5 | U20-3 | U14-6 | U22-11 |
| AC5 | U9-14 | U11-3 | U20-6 | U14-7 | U22-13 |
| AC6 | U9-13 | U11-14 | U20-10 | U14-8 | U22-15 |
| AC7 | U9-12 | U11-12 | U20-13 | U14-9 | U22-17 |

### SUM (Adder Outputs — 8-bit)

Source: 74HC283 sum outputs. Feeds AC input mux A-inputs (U17-U18).

| Net | Source | Destination |
|-----|--------|-------------|
| SUM0 | U10-4 | U17-2 (1A) |
| SUM1 | U10-1 | U17-5 (2A) |
| SUM2 | U10-13 | U17-11 (3A) |
| SUM3 | U10-10 | U17-14 (4A) |
| SUM4 | U11-4 | U18-2 (1A) |
| SUM5 | U11-1 | U18-5 (2A) |
| SUM6 | U11-13 | U18-11 (3A) |
| SUM7 | U11-10 | U18-14 (4A) |

Carry: U10-9 (Cout) → U11-7 (Cin)

### XOR_Y (XOR Array Outputs — 8-bit)

Source: 74HC86 XOR outputs. Feeds: adder B-inputs (U10-U11), AC input mux B-inputs (U17-U18).

| Net | Source | U10/U11 (Adder B) | U17/U18 (Mux B) |
|-----|--------|:------------------:|:----------------:|
| XOR_Y0 | U12-3 | U10-6 | U17-3 |
| XOR_Y1 | U12-6 | U10-2 | U17-6 |
| XOR_Y2 | U12-8 | U10-15 | U17-10 |
| XOR_Y3 | U12-11 | U10-11 | U17-13 |
| XOR_Y4 | U13-3 | U11-6 | U18-3 |
| XOR_Y5 | U13-6 | U11-2 | U18-6 |
| XOR_Y6 | U13-8 | U11-15 | U18-10 |
| XOR_Y7 | U13-11 | U11-11 | U18-13 |

### XOR B-Input Mux Outputs (U19-U20 → U12-U13)

| Net | Source | Destination |
|-----|--------|-------------|
| XOR_B0 | U19-4 | U12-2 |
| XOR_B1 | U19-7 | U12-5 |
| XOR_B2 | U19-9 | U12-10 |
| XOR_B3 | U19-12 | U12-13 |
| XOR_B4 | U20-4 | U13-2 |
| XOR_B5 | U20-7 | U13-5 |
| XOR_B6 | U20-9 | U13-10 |
| XOR_B7 | U20-12 | U13-13 |

### AC Input Mux Outputs (U17-U18 → U9)

| Net | Source | Destination |
|-----|--------|-------------|
| AC_IN0 | U17-4 | U9-2 (D1) |
| AC_IN1 | U17-7 | U9-3 (D2) |
| AC_IN2 | U17-9 | U9-4 (D3) |
| AC_IN3 | U17-12 | U9-5 (D4) |
| AC_IN4 | U18-4 | U9-6 (D5) |
| AC_IN5 | U18-7 | U9-7 (D6) |
| AC_IN6 | U18-9 | U9-8 (D7) |
| AC_IN7 | U18-12 | U9-9 (D8) |

---

## Control Signal Nets

### Opcode Decode Outputs (U5 Q pins)

| Net | Source | Destinations | Bit |
|-----|--------|-------------|:---:|
| ALU_SUB | U5-12 (Q8) | U10-7 (Cin), U19-2/5/11/14 (mux A×4), U20-2/5/11/14 (mux A×4), U28-2 | 7 |
| XOR_MODE | U5-13 (Q7) | U19-1 (SEL), U20-1 (SEL), U33-2 (1B), U28-12 | 6 |
| MUX_SEL | U5-14 (Q6) | U17-1 (SEL), U18-1 (SEL), U27-9 | 5 |
| AC_WR | U5-15 (Q5) | U24-11 (→/AC_WR), U27-13 | 4 |
| SRC | U5-16 (Q4) | U25-1 (→ADDR_REQ), U33-10 (2B) | 3 |
| STR | U5-17 (Q3) | U25-2 (→ADDR_REQ), U26-10 | 2 |
| BR | U5-18 (Q2) | U27-1 | 1 |
| JMP | U5-19 (Q1) | U24-9 (→/JUMP) | 0 |

### Derived Control Signals

| Net | Source | Destinations | Function |
|-----|--------|-------------|----------|
| ADDR_REQ | U25-3 | U26-4 | SRC OR STR |
| /ADDR_MODE | U26-6 | U15-1, U16-1, U29-1, U30-1, U26-2, U33-4 | NAND(ADDR_REQ, T2) |
| PC_INC | U25-6 | U1-7, U1-10, U2-7, U3-7, U4-7 | T0 OR T1 |
| /PC_LD | U26-11 | U1-9, U2-9, U3-9, U4-9 | NAND(T2, PC_LOAD_COND) |
| /IRL_OE | U26-3 | U34-1, U34-19, U24-13 | NAND(T2, /ADDR_MODE) |
| /AC_BUF | U26-8 | U14-1, U14-19, RAM /WE, U28-9 | NAND(T2, STR) |
| BUF_OE_N | U24-12 | U7-19 | NOT(/IRL_OE) |
| WR_DIR | U28-8 | U7-1, ROM /OE | NOT(/AC_BUF) |
| ACC_CLK | U27-11 | U9-11, U21-3 | NAND(T2, AC_WR) — active LOW edge |
| PG_CLK | U25-11 | U23-11 | /T2 OR /PG_cond |
| DP_Load | U33-6 | U32-11 | T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR |
| EI_decode | U33-8 | U31-3 | T2 AND SRC AND /XOR_MODE AND /AC_WR |
| /AC_WR | U24-10 | U27-10, U33-5, U33-13 | NOT(AC_WR) |
| /JUMP | U24-8 | U27-4 | NOT(JMP) |
| /XOR_MODE | U28-11 | U33-12 | XOR_MODE XOR VCC |
| /A15 | U24-6 | RAM /CE | NOT(ABUS15) |

### Branch/Jump Logic

| Net | Source | Destinations | Function |
|-----|--------|-------------|----------|
| Z_flag | U21-5 (Q1) | U28-1 | Z register output |
| Z_match | U28-3 | U27-2 | Z_flag XOR ALU_SUB (BEQ: Z=1, BNE: Z=0) |
| /BR_TAKEN | U27-3 | U27-5 | NAND(BR, Z_match) |
| PC_LOAD_COND | U27-6 | U26-13 | NAND(/JUMP, /BR_TAKEN) = JMP OR BR_TAKEN |
| /PG_cond | U27-8 | U25-12 | NAND(MUX_SEL, /AC_WR) |

### Z Flag Circuit

| Net | Source | Destination | Function |
|-----|--------|-------------|----------|
| /P=Q | U22-19 | U21-4 (/PR1) | Zero detect: LOW when AC=0 (async preset) |

### IRQ Nets

| Net | Source | Destination | Function |
|-----|--------|-------------|----------|
| IE | U31-5 (Q1) | LED/test point | Interrupt enable flag |
| IRQ_FF | U31-9 (Q2) | LED/test point | IRQ latch (cleared by /RST only) |
| /IRQ | RV8-Bus pin 29 | U31-11 (CLK2) | External IRQ input |

---

## ROM & RAM Connections

### ROM (AT28C256)

| Pin | Function | Net |
|:---:|----------|-----|
| A0–A7 | Address low | ABUS0–ABUS7 |
| A8–A14 | Address high | ABUS8–ABUS14 |
| D0–D7 | Data out | DBUS0–DBUS7 |
| /CE | Chip enable | ABUS15 (A15=0 selects ROM) |
| /OE | Output enable | WR_DIR (U28-8) — disabled during store |
| /WE | Write enable | VCC during CPU runtime; programmer write path only when CPU is stopped/reset-isolated |
| VCC | Power | pin 28 |
| GND | Ground | pin 14 |

### RAM (62256)

| Pin | Function | Net |
|:---:|----------|-----|
| A0–A7 | Address low | ABUS0–ABUS7 |
| A8–A14 | Address high | ABUS8–ABUS14 |
| D0–D7 | Data I/O | DBUS0–DBUS7 |
| /CE | Chip enable | /A15 (U24-6) — A15=1 selects RAM |
| /OE | Output enable | GND (always enabled) |
| /WE | Write enable | /AC_BUF (U26-8) |
| VCC | Power | pin 28 |
| GND | Ground | pin 14 |

---

## RV8-Bus Connector Summary

| Pin | Net | Direction |
|:---:|-----|:---------:|
| 1–16 | ABUS0–ABUS15 | out |
| 17–24 | DBUS0–DBUS7 | bidir |
| 25 | CLK | out |
| 26 | /RST | out |
| 27 | /WR (/AC_BUF, U26-8) | out |
| 28 | /RD | out |
| 29 | /IRQ | in |
| 30 | /SLOT1 | out |
| 31 | /SLOT2 | out |
| 32 | T2 (U8-5) | out |
| 33 | ABUS15 (duplicate) | out |
| 34–38 | (reserved) | — |
| 39 | VCC | — |
| 40 | GND | — |

---

## Net Count Summary

| Category | Count |
|----------|:-----:|
| Power (VCC, GND) | 2 |
| Clock & Reset (CLK, /RST) | 2 |
| Ring Counter (T0, T1, T2, /T2, feedback ×2) | 6 |
| Address Bus (ABUS0–15) | 16 |
| Data Bus (DBUS0–7) | 8 |
| Internal Bus (IBUS0–7) | 8 |
| PC outputs (PC0–15 + RCO ×3) | 19 |
| IRL outputs (IRL0–7) | 8 |
| PG outputs (PG0–7) | 8 |
| DP outputs (DP0–7) | 8 |
| AC outputs (AC0–7) | 8 |
| SUM outputs (SUM0–7 + carry) | 9 |
| XOR_Y outputs (XOR_Y0–7) | 8 |
| XOR_B mux outputs (XOR_B0–7) | 8 |
| AC_IN mux outputs (AC_IN0–7) | 8 |
| Opcode decode (8 bits from U5) | 8 |
| Derived control signals | 16 |
| Branch/Jump logic | 5 |
| Z flag circuit | 2 |
| IRQ nets | 3 |
| **Total unique nets** | **~152** |

---

## Cross-Reference: Chip → Nets Connected

| Chip | Type | Nets Used |
|------|------|-----------|
| U1 | 74HC161 | CLK, /RST, IRL0-3, PC_INC, /PC_LD, PC0-3, RCO_0 |
| U2 | 74HC161 | CLK, /RST, IRL4-7, PC_INC, /PC_LD, RCO_0, PC4-7, RCO_1 |
| U3 | 74HC161 | CLK, /RST, PG0-3, PC_INC, /PC_LD, RCO_1, PC8-11, RCO_2 |
| U4 | 74HC161 | CLK, /RST, PG4-7, PC_INC, /PC_LD, RCO_2, PC12-15 |
| U5 | 74HC574 | T0, IBUS0-7, ALU_SUB, XOR_MODE, MUX_SEL, AC_WR, SRC, STR, BR, JMP |
| U6 | 74HC574 | T1, IBUS0-7, IRL0-7 |
| U7 | 74HC245 | WR_DIR, BUF_OE_N, IBUS0-7, DBUS0-7 |
| U8 | 74HC164 | CLK, /RST, NOT(Q0), NOT(Q1), T0, T1, T2 |
| U9 | 74HC574 | ACC_CLK, AC_IN0-7, AC0-7 |
| U10 | 74HC283 | AC0-3, XOR_Y0-3, ALU_SUB(Cin), SUM0-3, Cout→U11 |
| U11 | 74HC283 | AC4-7, XOR_Y4-7, U10-Cout(Cin), SUM4-7 |
| U12 | 74HC86 | IBUS0-3, XOR_B0-3, XOR_Y0-3 |
| U13 | 74HC86 | IBUS4-7, XOR_B4-7, XOR_Y4-7 |
| U14 | 74HC541 | /AC_BUF, AC0-7, IBUS0-7 |
| U15 | 74HC157 | /ADDR_MODE, IRL0-3, PC0-3, ABUS0-3 |
| U16 | 74HC157 | /ADDR_MODE, IRL4-7, PC4-7, ABUS4-7 |
| U17 | 74HC157 | MUX_SEL, SUM0-3, XOR_Y0-3, AC_IN0-3 |
| U18 | 74HC157 | MUX_SEL, SUM4-7, XOR_Y4-7, AC_IN4-7 |
| U19 | 74HC157 | XOR_MODE, ALU_SUB(×4), AC0-3, XOR_B0-3 |
| U20 | 74HC157 | XOR_MODE, ALU_SUB(×4), AC4-7, XOR_B4-7 |
| U21 | 74HC74 | ACC_CLK, /P=Q, Z_flag |
| U22 | 74HC688 | AC0-7, /P=Q |
| U23 | 74HC574 | PG_CLK, IBUS0-7, PG0-7 |
| U24 | 74HC04 | T0, T1, ABUS15, JMP, AC_WR, /IRL_OE → NOT(Q0), NOT(Q1), /A15, /JUMP, /AC_WR, BUF_OE_N |
| U25 | 74HC32 | SRC, STR, T0, T1, /T2, /PG_cond → ADDR_REQ, PC_INC, (spare), PG_CLK |
| U26 | 74HC00 | T2, /ADDR_MODE, ADDR_REQ, STR, PC_LOAD_COND → /IRL_OE, /ADDR_MODE, /AC_BUF, /PC_LD |
| U27 | 74HC00 | BR, Z_match, /JUMP, /BR_TAKEN, MUX_SEL, /AC_WR, T2, AC_WR → /BR_TAKEN, PC_LOAD_COND, /PG_cond, ACC_CLK |
| U28 | 74HC86 | Z_flag, ALU_SUB, T2, /AC_BUF, XOR_MODE → Z_match, /T2, WR_DIR, /XOR_MODE |
| U29 | 74HC157 | /ADDR_MODE, DP0-3, PC8-11, ABUS8-11 |
| U30 | 74HC157 | /ADDR_MODE, DP4-7, PC12-15, ABUS12-15 |
| U31 | 74HC74 | /RST, EI_decode, /IRQ, IE, IRQ_FF |
| U32 | 74HC574 | DP_Load, IBUS0-7, DP0-7 |
| U33 | 74HC21 | T2, XOR_MODE, /ADDR_MODE, /AC_WR, SRC, /XOR_MODE → DP_Load, EI_decode |
| U34 | 74HC541 | /IRL_OE, IRL0-7, IBUS0-7 |
| ROM | AT28C256 | ABUS0-14, ABUS15(/CE), WR_DIR(/OE), DBUS0-7 |
| RAM | 62256 | ABUS0-14, /A15(/CE), /AC_BUF(/WE), DBUS0-7 |

---

*End of netlist.*
