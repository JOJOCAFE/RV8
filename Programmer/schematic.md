# RV8 Programmer — Combined Schematic (Bus + Direct ROM)

**แนวคิด**: บอร์ดเดียว ใช้ได้ 2 แบบ — เสียบสาย Bus ไปยัง CPU board หรือเสียบ ROM ลง ZIF
**กฎ**: ใช้ทีละอย่าง — เสียบ Bus cable หรือ เสียบ ROM ใน ZIF (ไม่ใช้พร้อมกัน)

**KiCad project**: `KICAD/RV8Programmer.kicad_sch`
**PDF export**: `RV8Programmer.pdf`

---

## ภาพรวมระบบ

```
                                              ┌─────────────────────┐
                                         ┌──→ │  RV8-Bus (40-pin)   │ → CPU Board
                                         │    └─────────────────────┘
                                         │
PC ←USB→ [ESP32] ←→ [TXS ×2] ←→ [595 ×2]┤
                                         │
                                         │    ┌─────────────────────┐
                                         └──→ │  AT28C256 (ZIF 28)  │ → ถอดไปเสียบบอร์ด
                                              └─────────────────────┘

          เลือกใช้ทีละอย่าง: เสียบสาย Bus  หรือ  เสียบ ROM ใน ZIF
```

---

## 1. Power & Ground

```
ESP32 (3V3) ───→ TXS0108E ×2: V_A (พิน 1)
                 TXS0108E ×2: OE (พิน 10) — pull-up R1=10K เข้า 3.3V

ESP32 (5V)  ───→ TXS0108E ×2: V_B (พิน 20)
                 74HC595 ×2: VCC (พิน 16)
                 AT28C256: VCC (พิน 28)
                 Bus header: pin 39 (VCC)

ESP32 (GND) ───→ ทุก IC GND
                 AT28C256: GND (พิน 14)
                 Bus header: pin 40 (GND)
```

---

## 2. Control Signals (TXS0108E #2 = U4)

```
[ ESP32 ]         [ TXS #2 (U4) ]              [ ปลายทาง ×2 ]

GPIO 23 ──→ A1 ←═══→ B1 ──→ 595 #1 SER (พิน 14)
GPIO 18 ──→ A2 ←═══→ B2 ──→ 595 ×2 SRCLK (พิน 11)
GPIO 19 ──→ A3 ←═══→ B3 ──→ 595 ×2 RCLK (พิน 12)

GPIO 4  ──→ A4 ←═══→ B4 ──┬→ Bus pin 26 (/RST)
                           └→ ZIF ROM พิน 20 (/CE)

GPIO 16 ──→ A5 ←═══→ B5 ──┬→ Bus pin 27 (/WR)      ← ⚡ SWAP จาก KiCad เดิม
                           └→ ZIF ROM พิน 27 (/WE)

GPIO 17 ──→ A6 ←═══→ B6 ──┬→ Bus pin 28 (/RD)      ← ⚡ SWAP จาก KiCad เดิม
                           └→ ZIF ROM พิน 22 (/OE)

(A7/B7, A8/B8 ไม่ใช้)
```

### Pull-ups ที่ ZIF ROM (ป้องกัน glitch ตอน ESP32 boot)

```
R2 (10K): ZIF /OE (พิน 22) pull-up → +5V
R3 (10K): ZIF /CE (พิน 20) pull-up → +5V
```

---

## 3. Address Bus (74HC595 ×2 → Bus + ZIF)

```
📌 74HC595 ขาพิเศษ:
- พิน 10 (/SRCLR) → VCC
- พิน 13 (/OE)    → GND

📌 Daisy Chain:
- 595 #1 (U2) พิน 9 (QH') → 595 #2 (U3) พิน 14 (SER)

📌 595 #1 (U2) → A[7:0]:
  พิน 15 (QA) ──┬→ Bus pin 1  (A0)  └→ ZIF ROM พิน 10 (A0)
  พิน 1  (QB) ──┬→ Bus pin 2  (A1)  └→ ZIF ROM พิน 9  (A1)
  พิน 2  (QC) ──┬→ Bus pin 3  (A2)  └→ ZIF ROM พิน 8  (A2)
  พิน 3  (QD) ──┬→ Bus pin 4  (A3)  └→ ZIF ROM พิน 7  (A3)
  พิน 4  (QE) ──┬→ Bus pin 5  (A4)  └→ ZIF ROM พิน 6  (A4)
  พิน 5  (QF) ──┬→ Bus pin 6  (A5)  └→ ZIF ROM พิน 5  (A5)
  พิน 6  (QG) ──┬→ Bus pin 7  (A6)  └→ ZIF ROM พิน 4  (A6)
  พิน 7  (QH) ──┬→ Bus pin 8  (A7)  └→ ZIF ROM พิน 3  (A7)

📌 595 #2 (U3) → A[14:8]:
  พิน 15 (QA) ──┬→ Bus pin 9  (A8)  └→ ZIF ROM พิน 25 (A8)
  พิน 1  (QB) ──┬→ Bus pin 10 (A9)  └→ ZIF ROM พิน 24 (A9)
  พิน 2  (QC) ──┬→ Bus pin 11 (A10) └→ ZIF ROM พิน 21 (A10)
  พิน 3  (QD) ──┬→ Bus pin 12 (A11) └→ ZIF ROM พิน 23 (A11)
  พิน 4  (QE) ──┬→ Bus pin 13 (A12) └→ ZIF ROM พิน 2  (A12)
  พิน 5  (QF) ──┬→ Bus pin 14 (A13) └→ ZIF ROM พิน 26 (A13)
  พิน 6  (QG) ──┬→ Bus pin 15 (A14) └→ ZIF ROM พิน 1  (A14)
  พิน 7  (QH) ──  (ไม่ใช้)
```

---

## 4. Data Bus (TXS0108E #1 = U5 → Bus + ZIF)

```
[ ESP32 ]        [ TXS #1 (U5) ]         [ Bus + ZIF ]

GPIO 13 ──→ A1 ←═══→ B1 ──┬→ Bus pin 17 (D0)  └→ ZIF ROM พิน 11 (D0)
GPIO 12 ──→ A2 ←═══→ B2 ──┬→ Bus pin 18 (D1)  └→ ZIF ROM พิน 12 (D1)
GPIO 14 ──→ A3 ←═══→ B3 ──┬→ Bus pin 19 (D2)  └→ ZIF ROM พิน 13 (D2)
GPIO 27 ──→ A4 ←═══→ B4 ──┬→ Bus pin 20 (D3)  └→ ZIF ROM พิน 15 (D3)
GPIO 26 ──→ A5 ←═══→ B5 ──┬→ Bus pin 21 (D4)  └→ ZIF ROM พิน 16 (D4)
GPIO 25 ──→ A6 ←═══→ B6 ──┬→ Bus pin 22 (D5)  └→ ZIF ROM พิน 17 (D5)
GPIO 33 ──→ A7 ←═══→ B7 ──┬→ Bus pin 23 (D6)  └→ ZIF ROM พิน 18 (D6)
GPIO 32 ──→ A8 ←═══→ B8 ──┬→ Bus pin 24 (D7)  └→ ZIF ROM พิน 19 (D7)
```

---

## 5. Bus-only Signals (Input for RUN mode)

```
Bus pin 30 (/SLOT1) ──→ ESP32 GPIO 34
Bus pin 28 (/RD)    ──→ ESP32 GPIO 35  (sense)
Bus pin 27 (/WR)    ──→ ESP32 GPIO 36  (sense)
MODE switch         ──→ ESP32 GPIO 39  (LOW=PROG, HIGH=RUN)
```

เมื่อใช้ ZIF (ไม่ได้เสียบ Bus): GPIO 34/35/36 ลอย (input-only, ไม่มีผล)
GPIO 39: ต่อ pull-down 10K → GND (ค้าง PROG mode) หรือ ใช้สวิตช์เหมือนเดิม

---

## 6. Bypass Capacitors (C 104 = 0.1µF)

| Ref | IC |
|-----|-----|
| C1 | 74HC595 #1 (U2) |
| C2 | 74HC595 #2 (U3) |
| C3 | TXS0108E #1 (U5) — V_B side |
| C4 | TXS0108E #2 (U4) — V_A side |
| C5 | TXS0108E #2 (U4) — V_B side |
| C6 | TXS0108E #1 (U5) — V_A side |
| C7 | AT28C256 (U1) |

**รวม 7 ตัว**

---

## 7. BOM

| Part | Qty | หน้าที่ |
|------|:---:|---------|
| ESP32-WROOM-32 | 1 | สมองหลัก |
| TXS0108E module | 2 | Level shift 3.3V↔5V |
| 74HC595 | 2 | Shift register → address |
| AT28C256 | (ใส่ใน ZIF เวลาใช้) | ROM |
| ZIF socket 28-pin wide | 1 | ใส่/ถอด ROM |
| 40-pin IDC header | 1 | Bus connector |
| 40-pin ribbon cable | 1 | ไป CPU board |
| R1 (10K) | 1 | TXS OE pull-up |
| R2 (10K) | 1 | ZIF /OE pull-up |
| R3 (10K) | 1 | ZIF /CE pull-up |
| C1-C7 (100nF) | 7 | Bypass |
| SPDT switch | 1 | PROG/RUN (Bus mode) |
| USB cable | 1 | PC → ESP32 |

---

## 8. ESP32 GPIO Summary

| GPIO | Function | Dir | ปลายทาง |
|:----:|----------|:---:|---------|
| 23 | SR_DATA | OUT | 595 SER |
| 18 | SR_CLK | OUT | 595 SRCLK |
| 19 | SR_LATCH | OUT | 595 RCLK |
| 4 | /RST + /CE | OUT | Bus /RST & ZIF /CE |
| 16 | /WR + /WE | OUT in PROG, released in RUN | Bus /WR & ZIF /WE |
| 17 | /RD + /OE | OUT in PROG, released in RUN | Bus /RD & ZIF /OE |
| 13 | D0 | BIDIR | Bus D0 & ZIF D0 |
| 12 | D1 | BIDIR | Bus D1 & ZIF D1 |
| 14 | D2 | BIDIR | Bus D2 & ZIF D2 |
| 27 | D3 | BIDIR | Bus D3 & ZIF D3 |
| 26 | D4 | BIDIR | Bus D4 & ZIF D4 |
| 25 | D5 | BIDIR | Bus D5 & ZIF D5 |
| 33 | D6 | BIDIR | Bus D6 & ZIF D6 |
| 32 | D7 | BIDIR | Bus D7 & ZIF D7 |
| 34 | /SLOT1 | IN | Bus pin 30 (RUN mode) |
| 35 | /RD sense | IN | Bus pin 28 (RUN mode) |
| 36 | /WR sense | IN | Bus pin 27 (RUN mode) |
| 39 | MODE | IN | Switch (PROG/RUN) |

**Total: 18 GPIO**

---

## 9. วิธีใช้

### ใช้กับ ZIF (โปรแกรม ROM เปล่า)

1. ❌ ถอดสาย Bus ออก (ถ้ามี)
2. เสียบ ROM ลง ZIF → ล็อค
3. สวิตช์ → PROG (หรือ ground GPIO 39)
4. `python3 rv8flash.py -w program.bin`
5. `python3 rv8flash.py -v program.bin`
6. ปลดล็อค ZIF → ถอด ROM ไปเสียบ CPU board

### ใช้กับ Bus (โปรแกรม in-system)

1. ❌ ZIF ว่าง (ไม่เสียบ ROM)
2. เสียบสาย Bus ไป CPU board
3. สวิตช์ → PROG → flash
4. สวิตช์ → RUN → terminal (`rv8term.py`)

---

## 10. ทำไมปลอดภัย (ไม่ conflict)

| สถานการณ์ | เกิดอะไร |
|-----------|----------|
| ZIF มี ROM + Bus ไม่ได้เสียบ | Bus header ลอย, ไม่มีอะไรขับสาย ✅ |
| Bus เสียบ + ZIF ว่าง | ZIF ไม่มี chip, /CE pull-up HIGH, ไม่ตอบ ✅ |
| ⚠️ ทั้ง 2 เสียบพร้อมกัน | **ห้าม!** data bus fight → ชิปพัง |

---

*ตรงกับ KiCad schematic หลัง swap GPIO 16↔17*
*Firmware ไม่ต้องแก้*
*เขียนสำหรับน้อง ๆ ม.ต้น — ถ้าติดตรงไหนถามพี่ได้เลย!*
