# RV8-GR — Wiring Guide

**Quick reference. Source of truth: `Construct.md`**

---

## IBUS Connections (IB0-IB7)

| IB# | U7 (245 B) | U6 (IRL Q)* | U14 (AC buf Y)* | U12/13 (XOR A) | U23 (PG D) | U5 (IRH D) |
|:---:|:----------:|:-----------:|:---------------:|:--------------:|:----------:|:----------:|
| 0 | pin18 | pin19 | pin18 | U12-1 | pin2 | pin2 |
| 1 | pin17 | pin18 | pin17 | U12-4 | pin3 | pin3 |
| 2 | pin16 | pin17 | pin16 | U12-9 | pin4 | pin4 |
| 3 | pin15 | pin16 | pin15 | U12-12 | pin5 | pin5 |
| 4 | pin14 | pin15 | pin14 | U13-1 | pin6 | pin6 |
| 5 | pin13 | pin14 | pin13 | U13-4 | pin7 | pin7 |
| 6 | pin12 | pin13 | pin12 | U13-9 | pin8 | pin8 |
| 7 | pin11 | pin12 | pin11 | U13-12 | pin9 | pin9 |

*Tristate — only one active at a time

---

## DBUS Connections (D0-D7)

| D# | U7 (245 A) | ROM | RAM |
|:--:|:----------:|:---:|:---:|
| 0 | pin2 | D0 | D0 |
| 1 | pin3 | D1 | D1 |
| 2 | pin4 | D2 | D2 |
| 3 | pin5 | D3 | D3 |
| 4 | pin6 | D4 | D4 |
| 5 | pin7 | D5 | D5 |
| 6 | pin8 | D6 | D6 |
| 7 | pin9 | D7 | D7 |

---

## ABUS Connections (A0-A15)

| A# | Mux chip | Mux pin | → ROM | → RAM |
|:--:|:--------:|:-------:|:-----:|:-----:|
| 0 | U15 | pin4 (1Y) | A0 | A0 |
| 1 | U15 | pin7 (2Y) | A1 | A1 |
| 2 | U15 | pin9 (3Y) | A2 | A2 |
| 3 | U15 | pin12 (4Y) | A3 | A3 |
| 4 | U16 | pin4 (1Y) | A4 | A4 |
| 5 | U16 | pin7 (2Y) | A5 | A5 |
| 6 | U16 | pin9 (3Y) | A6 | A6 |
| 7 | U16 | pin12 (4Y) | A7 | A7 |
| 8 | U29 | pin4 (1Y) | A8 | A8 |
| 9 | U29 | pin7 (2Y) | A9 | A9 |
| 10 | U29 | pin9 (3Y) | A10 | A10 |
| 11 | U29 | pin12 (4Y) | A11 | A11 |
| 12 | U30 | pin4 (1Y) | A12 | A12 |
| 13 | U30 | pin7 (2Y) | A13 | A13 |
| 14 | U30 | pin9 (3Y) | A14 | A14 |
| 15 | U30 | pin12 (4Y) | — | /CE |

---

## Control Signal Routing

| Signal | Source chip-pin | Destination chip-pins |
|--------|:--------------:|----------------------|
| CLK | oscillator | U1-2, U2-2, U3-2, U4-2, U8-8 |
| /RST | RC + button | U1-1, U2-1, U3-1, U4-1, U8-9 |
| T0 | U8-3 | U5-11, U25-4, U24-1 |
| T1 | U8-4 | U6-11, U25-5, U24-3 |
| T2 | U8-5 | U26-1, U26-9, U26-12, U27-12, U28-4 |
| ALU_SUB | U5-12 | U10-7, U19-2/5/11/14, U20-2/5/11/14, U28-2 |
| XOR_MODE | U5-13 | U19-1, U20-1 |
| MUX_SEL | U5-14 | U17-1, U18-1, U27-9 |
| AC_WR | U5-15 | U24-11, U27-13 |
| SOURCE_TYPE | U5-16 | U25-1 |
| STORE | U5-17 | U25-2, U26-10 |
| BRANCH | U5-18 | U25-10, U27-1 |
| JUMP | U5-19 | U24-9, U25-9 |
| ADDR_MODE | U25-3 | U15-1, U16-1, U29-1, U30-1, U26-4, U26-5 |
| PC_INC | U25-6 | U1-7/10, U2-7, U3-7, U4-7 |
| /IRL_OE | U26-3 | U6-1, U24-13 |
| /ADDR_MODE | U26-6 | U26-2 |
| /AC_BUF | U26-8 | U14-1, U14-19, RAM /WE, U28-9 |
| /PC_LD | U26-11 | U1-9, U2-9, U3-9, U4-9 |
| /BR_TAKEN | U27-3 | U27-5 |
| PC_LOAD_COND | U27-6 | U26-13 |
| /PG_cond | U27-8 | U25-12 |
| Acc_Load_N | U27-11 | U9-11, U21-3 |
| Z_match | U28-3 | U27-2 |
| /T2 | U28-6 | U25-11 |
| WR_DIR | U28-8 | U7-1 |
| /A15 | U24-6 | ROM /CE |
| /JUMP | U24-8 | U27-4 |
| /AC_WR | U24-10 | U27-10 |
| BUF_OE_N | U24-12 | U7-19 |
| PG_Load_N | U25-13 | U23-11 |
| A15 | U30-12 | RAM /CE, U24-5 |

---

## Memory Chip Select

| Chip | /CE | /OE | /WE |
|------|-----|-----|-----|
| ROM (SST39SF010A) | /A15 (U24-6) | GND | VCC |
| RAM (62256) | A15 (U30-12) | GND | /AC_BUF (U26-8) |

    ROM enabled when A15=1 ($8000-$FFFF)
    RAM enabled when A15=0 ($0000-$7FFF)
    RAM write when /AC_BUF=0 (T2 + STORE)

---

## Power (VCC/GND per chip)

| Chip | VCC pin | GND pin |
|------|:-------:|:-------:|
| U1-U4 (161) | 16 | 8 |
| U5,U6,U9,U23 (574) | 20 | 10 |
| U7 (245) | 20 | 10 |
| U8 (164) | 14 | 7 |
| U10-U11 (283) | 16 | 8 |
| U12-U13 (86) | 14 | 7 |
| U14 (541) | 20 | 10 |
| U15-U20,U29-U30 (157) | 16 | 8 |
| U21 (74) | 14 | 7 |
| U22 (688) | 20 | 10 |
| U24 (04) | 14 | 7 |
| U25 (32) | 14 | 7 |
| U26-U27 (00) | 14 | 7 |
| U28 (86) | 14 | 7 |

100nF decoupling capacitor on each VCC-GND pair.
