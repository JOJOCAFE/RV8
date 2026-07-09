# Lab 12: RAM + Data Page — อ่าน/เขียนหน่วยความจำ

**เป้าหมาย**: ต่อ 62256-70 (RAM) + U32 (Data Page Register) + U33 (SETDP decode) ให้ CPU อ่าน/เขียน RAM ได้ทั้ง 64KB

---

## ความรู้พื้นฐาน

- **62256-70**: RAM 32KB (A[14:0], D[7:0])
- **Chip select**: A15=0 → ROM (/CE=LOW), A15=1 → RAM (/CE=LOW)
- **U32 (74HC574)**: Data Page Register — กำหนด A[15:8] ตอน LB/SB
- **U33 (74HC21)**: 4-input AND gate สำหรับ SETDP decode:
  ```
  DP_Load = T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR
  ```
- **SB (store)**: AC → DBUS → RAM (เขียน) เมื่อ /WE pulse LOW
- **LB (load)**: RAM → DBUS → IBUS → AC (อ่าน) เมื่อ address ชี้ RAM

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 62256-70 (RAM, DIP-28) | 1 |
| 2 | 74HC574 (U32, Data Page Register) | 1 |
| 3 | 74HC21 (U33, 4-input AND) | 1 |
| 4 | LED สีเขียว 3mm | 8 |
| 5 | 330Ω resistor | 8 |
| 6 | 100nF capacitor | 3 |

---

## วงจร

### Pinout: 62256 (RAM, DIP-28)

```
        ┌───U───┐
  A14 1 │       │ 28 VCC
  A12 2 │       │ 27 /WE
   A7 3 │       │ 26 A13
   A6 4 │ 6225  │ 25 A8
   A5 5 │  6    │ 24 A9
   A4 6 │       │ 23 A11
   A3 7 │       │ 22 /OE
   A2 8 │       │ 21 A10
   A1 9 │       │ 20 /CE
   A0 10│       │ 19 D7
   D0 11│       │ 18 D6
   D1 12│       │ 17 D5
   D2 13│       │ 16 D4
  GND 14│       │ 15 D3
        └───────┘
```

### Pinout: 74HC21

```
        ┌───U───┐
  1A  1 │       │ 14 VCC
  1B  2 │       │ 13 2D
  NC  3 │  21   │ 12 2C
  1C  4 │       │ 11 NC
  1D  5 │       │ 10 2B
  1Y  6 │       │  9 2A
 GND  7 │       │  8 2Y
        └───────┘
```

### การต่อสาย

```
RAM (62256-70):
  pin 28 (VCC) → 5V,  pin 14 (GND) → GND,  100nF คร่อม VCC-GND

  Address ← ABUS (จาก address mux outputs):
    pin 10(A0) ← A0 (U15-4)     pin 9(A1)  ← A1 (U15-7)
    pin 8(A2)  ← A2 (U15-9)     pin 7(A3)  ← A3 (U15-12)
    pin 6(A4)  ← A4 (U16-4)     pin 5(A5)  ← A5 (U16-7)
    pin 4(A6)  ← A6 (U16-9)     pin 3(A7)  ← A7 (U16-12)
    pin 25(A8) ← A8 (U29-4)     pin 24(A9) ← A9 (U29-7)
    pin 21(A10)← A10 (U29-9)    pin 23(A11)← A11 (U29-12)
    pin 2(A12) ← A12 (U30-4)    pin 26(A13)← A13 (U30-7)
    pin 1(A14) ← A14 (U30-9)

  Data ↔ DBUS:
    pin 11(D0) ↔ D0    pin 12(D1) ↔ D1    pin 13(D2) ↔ D2
    pin 15(D3) ↔ D3    pin 16(D4) ↔ D4    pin 17(D5) ↔ D5
    pin 18(D6) ↔ D6    pin 19(D7) ↔ D7

  Control:
    pin 20(/CE) ← /A15 (U24-6)   [A15=1 → /A15=0 → RAM enabled]
    pin 22(/OE) → GND             [อ่านตลอดเมื่อ enabled]
    pin 27(/WE) ← /AC_BUF (U26-8) [เขียนเมื่อ T2+STORE]
```

> 💡 **RAM /OE = GND ตลอด — ปลอดภัยหรือ?**
>
> ปลอดภัย ✅ เพราะ 62256 (และ SRAM ส่วนใหญ่) มีกฎ:
> เมื่อ /WE = LOW → RAM **output ถูก disable อัตโนมัติ** ไม่ว่า /OE จะเป็นอะไร
> ดังนั้น: อ่าน = /CE=0, /WE=1, data out. เขียน = /CE=0, /WE=0, data in.
> ไม่มี bus fight ระหว่าง STORE.

```
Chip Select (สำคัญมาก!):
  A15=0 (addr $0000-$7FFF): ROM /CE = LOW (ROM on), RAM /CE = HIGH (RAM off)
  A15=1 (addr $8000-$FFFF): ROM /CE = HIGH (ROM off), RAM /CE = LOW (RAM on)
  
  ROM pin 20 ← A15 (U30-12) ตรงๆ
  RAM pin 20 ← /A15 (U24-6)

U32 (Data Page Register):
  pin 20 (VCC) → 5V,  pin 10 (GND) → GND,  100nF คร่อม VCC-GND
  pin 1 (/OE) → GND (output ตลอด)
  pin 11 (CLK) ← DP_Load (U33-6)

    74HC574 loads on RISING edge.
    DP_Load = AND(T2, XOR_MODE, /ADDR_MODE, /AC_WR)
    เมื่อ T2 เริ่ม → DP_Load goes HIGH → rising edge → U32 latches!
    (ต่างจาก U23 Page Reg ที่ latch ตอน edge ปลาย T2)

  D inputs ← IBUS:
    pin 2 ← IBUS0    pin 3 ← IBUS1    pin 4 ← IBUS2    pin 5 ← IBUS3
    pin 6 ← IBUS4    pin 7 ← IBUS5    pin 8 ← IBUS6    pin 9 ← IBUS7

  Q outputs → Address Mux A-inputs (high byte for LB/SB):
    pin 19 (Q1) → DP0 → U29-2     pin 18 (Q2) → DP1 → U29-5
    pin 17 (Q3) → DP2 → U29-11    pin 16 (Q4) → DP3 → U29-14
    pin 15 (Q5) → DP4 → U30-2     pin 14 (Q6) → DP5 → U30-5
    pin 13 (Q7) → DP6 → U30-11    pin 12 (Q8) → DP7 → U30-14

  LED (ดู Data Page value):
    DP0-DP7 → 330Ω → LED → GND (8 ดวง)

U33 (SETDP decode):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  Gate 1: DP_Load = T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR
    pin 1 (1A) ← T2 (U8-5)
    pin 2 (1B) ← XOR_MODE (U5-13)
    pin 4 (1C) ← /ADDR_MODE (U26-6)
    pin 5 (1D) ← /AC_WR (U24-10)
    pin 6 (1Y) → DP_Load → U32-11

  Gate 2 (unused):
    pin 9, 10, 12, 13 → VCC
    pin 8 → NC
```

---

## ทดสอบ ✅

### Test 1: SETDP $80 (page $80 = RAM)

Flash ROM:
```
$0000: $40  ; SETDP (XOR_MODE=1, SRC=0, STR=0, AC_WR=0)
$0001: $80  ; page = $80
```

| ขั้น | Phase | DP LED | ถูก? |
|:----:|:-----:|:------:|:----:|
| 3 | T2 | $80 ●○○○○○○○ | ☐ |

### Test 2: SB — เขียน RAM

Flash ROM:
```
$0000: $30  ; LI
$0001: $AA  ; AC = $AA
$0002: $40  ; SETDP
$0003: $80  ; page = $80
$0004: $04  ; SB (STR=1)
$0005: $03  ; addr low = $03 → write to $8003
$0006: $01  ; J
$0007: $06  ; loop at $0006
```

| ขั้น | Instruction | AC | เหตุการณ์ | ถูก? |
|:----:|:-----------:|:--:|-----------|:----:|
| 1 | LI $AA | $AA | AC loaded | ☐ |
| 2 | SETDP $80 | $AA | DP = $80 | ☐ |
| 3 | SB $03 | $AA | RAM[$8003] ← $AA | ☐ |

**ยืนยัน**: หยุด clock, ใช้ programmer อ่าน RAM address $8003 → ต้องได้ $AA

### Test 3: LB — อ่าน RAM กลับ

Flash ROM (ต่อจาก test 2 — RAM[$8003] = $AA):
```
$0000: $30  ; LI
$0001: $00  ; AC = $00 (clear)
$0002: $40  ; SETDP
$0003: $80  ; page = $80
$0004: $38  ; LB (MUX+AC_WR+SRC)
$0005: $03  ; addr = $03 → read RAM[$8003]
$0006: $01  ; J
$0007: $06  ; loop
```

| ขั้น | Instruction | AC | ถูก? |
|:----:|:-----------:|:--:|:----:|
| 1 | LI $00 | $00 | ☐ |
| 2 | SETDP $80 | $00 | ☐ |
| 3 | LB $03 | **$AA** (from RAM!) | ☐ |

### Test 4: SETDP $90 — page $90

```
$0000: $30  ; LI
$0001: $55  ; AC = $55
$0002: $40  ; SETDP
$0003: $90  ; page = $90
$0004: $04  ; SB
$0005: $00  ; addr = $00 → RAM[$9000] ← $55
$0006: $30  ; LI
$0007: $00  ; AC = $00 (clear)
$0008: $38  ; LB
$0009: $00  ; addr = $00 → AC ← RAM[$9000]
```

| ขั้น | AC | DP | Address | ถูก? |
|:----:|:--:|:--:|:-------:|:----:|
| SB execute | $55 | $90 | $9000 | ☐ |
| LB execute | **$55** | $90 | $9000 | ☐ |

### ROM/RAM Boundary Test
- [ ] SETDP $7F, LB $FF → reads ROM[$7FFF] (A15=0 → ROM)
- [ ] SETDP $80, LB $00 → reads RAM[$8000] (A15=1 → RAM)
- [ ] ถ้าอ่านค่าเดียวกัน → A15 wiring ผิด!

### Memory Contention Test
- [ ] SETDP $7F, LB $00 → probe ROM /CE=LOW, RAM /CE=HIGH
- [ ] SETDP $80, SB $00 → probe RAM /CE=LOW, ROM /CE=HIGH

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| RAM ไม่เขียน (LB ได้ $FF) | /WE ไม่ pulse LOW | เช็ค U26-8 → RAM pin 27 |
| เขียนผิด address | DP ไม่ต่อ mux A-input | เช็ค U32-Q → U29/U30 pin A |
| ROM+RAM ชนกัน (IC ร้อน!) | chip select ผิด | ROM /CE ← A15, RAM /CE ← /A15 |
| DP ไม่เปลี่ยน | U33 output ไม่ pulse | เช็ค U33 inputs: T2, XOR_MODE, /ADDR_MODE, /AC_WR |
| LB ได้ $00 แทน $AA | IBUS/DBUS path fault | เช็ค BUF_OE_N: U7 ต้อง enabled ตอน LB |
| SB เขียน ROM (ไม่มีผล) | A15=0 → RAM off | SETDP ต้องตั้ง page ≥ $80 |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab12_ram_datapage.py
```

---

## สิ่งที่ได้

- ✅ RAM เขียนข้อมูลด้วย SB ได้
- ✅ RAM อ่านข้อมูลด้วย LB ได้
- ✅ Chip select แยก ROM/RAM ถูกต้อง (A15)
- ✅ Data Page Register ตั้ง address high byte ได้
- ✅ SETDP decode (U33) ทำงานสำหรับ SETDP ($40) และ alias ($C0)

### STORE Path (สิ่งที่เกิดตอน SB):

```
AC → U14 (buffer, /OE=LOW) → IBUS → U7 (DIR=out) → DBUS → RAM (D pins)
                                                              ↑
Address: U15-U16 (low=IRL), U29-U30 (high=DP) ──────────────→ RAM A pins
                                                              ↑
/WE = /AC_BUF (U26-8) = LOW during T2+STR ──────────────────→ RAM write!
```

### ROM Access via DP (Feature!)

```
SETDP $00   ; DP = $00 → address = $00xx = ROM!
LB $00      ; AC ← ROM[$0000] (read program byte as data)
```

ใช้ทำ lookup table, constant table, string table ได้โดยไม่ต้องคำสั่งพิเศษ

> ⚠️ **SB ไปที่ ROM address = ไม่มีผล** — ROM `/WE` is on `/WR` for programmer
> support, but CPU stores do not perform the EEPROM/flash unlock sequence.
> ไม่ error แต่ข้อมูลหายไป — ระวังอย่า SETDP < $80 แล้ว SB

**ผ่านทุกข้อ → ไป Lab 13!** 🎉
