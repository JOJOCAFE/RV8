# Programmer Board — Schematic (ผังวงจร)

**แนวคิด**: Programmer ต่อเข้ากับ CPU board ผ่าน **RV8-Bus (40-pin)** ไม่ได้ต่อตรงกับ ROM
ข้อดี: ใช้กับ CPU board ทุกรุ่น (RV8, RV8-R, RV8-G, RV8-GR) และยังใช้เป็น Terminal bridge ได้ด้วย

---

## ภาพรวมระบบ

```
PC ←─USB─→ [ESP32-WROOM-32] ←─3.3V─→ [TXS0108E ×2] ←─5V─→ [74HC595 ×2] ──┐
                                                                              │
                                                              ┌───────────────┘
                                                              │
                                                              ▼
                                                 ┌─────────────────────┐
                                                 │  RV8-Bus (40-pin)   │
                                                 │  A[14:0], D[7:0]    │
                                                 │  /WR, /RD, /RST     │
                                                 │  /SLOT1, VCC, GND   │
                                                 └──────────┬──────────┘
                                                            │
                                                   CPU Board (RV8-GR etc.)
                                                   ROM + RAM อยู่บน CPU board
```

**PROG mode**: ESP32 ยึด /RST=LOW (CPU หยุด), ขับ Address + Data + /WR ผ่าน bus → เขียน ROM บน CPU board
**RUN mode**: ESP32 ปล่อย bus ทั้งหมด, ฟังที่ /SLOT1 สำหรับ UART bridge

---

## 1. ผังการต่อระบบไฟเลี้ยง (Power & Ground)

ต่อสายไฟเลี้ยงหลักให้ครบทุกจุดก่อนเริ่มเดินสายสัญญาณ

```
[ ESP32 บอร์ด ] ─── (3V3) ───────→ [ TXS0108E ตัวที่ 1 และ 2: พิน 1 (V_A) ]
                                    [ TXS0108E ตัวที่ 1 และ 2: พิน 10 (OE) ] (Pull-up 10kΩ เข้า 3.3V)

                ─── (VN / 5V) ────→ [ 74HC595 ตัวที่ 1 และ 2: พิน 16 (VCC) ]
                                    [ TXS0108E ตัวที่ 1 และ 2: พิน 20 (V_B) ]

                ─── (GND) ────────→ ต่อพ่วง GND ของ IC ทุกตัว
                                    - TXS0108E ตัวที่ 1 และ 2: พิน 11 (GND)
                                    - 74HC595 ตัวที่ 1 และ 2: พิน 8 (GND)
```

หมายเหตุ: VCC (+5V) และ GND รับจาก RV8-Bus pin 39 (VCC) และ pin 40 (GND) ก็ได้

---

## 2. ผังวงจรฝั่งสัญญาณควบคุมและ Address Bus

ใช้ TXS0108E ตัวที่ 1 แปลง 3.3V → 5V ส่งเข้า 74HC595 และขา Control

```
[ ESP32 ฝั่ง 3.3V ]       [ TXS0108E ตัวที่ 1 ]              [ ปลายทาง 5V ]

📌 กลุ่มขับ Shift Register (กำหนด Address)
GPIO 23 ──────→ พิน 2 (A1) ←══→ พิน 19 (B1) ──→ [ 74HC595 #1: พิน 14 (SER) ]
GPIO 18 ──────→ พิน 3 (A2) ←══→ พิน 18 (B2) ──→ [ 74HC595 ทั้ง 2: พิน 11 (SRCLK) ]
GPIO 19 ──────→ พิน 4 (A3) ←══→ พิน 17 (B3) ──→ [ 74HC595 ทั้ง 2: พิน 12 (RCLK) ]

📌 กลุ่มสัญญาณควบคุม → ออก RV8-Bus
GPIO 4  ──────→ พิน 5 (A4) ←══→ พิน 16 (B4) ──→ RV8-Bus pin 26 (/RST)
GPIO 16 ──────→ พิน 6 (A5) ←══→ พิน 15 (B5) ──→ RV8-Bus pin 27 (/WR)
GPIO 17 ──────→ พิน 7 (A6) ←══→ พิน 14 (B6) ──→ RV8-Bus pin 28 (/RD)

(ขา A7/B7 และ A8/B8 ของ TXS ตัวที่ 1 ไม่ได้ใช้ — ปล่อยลอย)
```

### การเชื่อมต่อ 74HC595 → RV8-Bus Address

```
📌 ขาพิเศษของ 74HC595 ทั้ง 2 ตัว:
- พิน 10 (/SRCLR) → ต่อ VCC (5V) — ไม่เคลียร์
- พิน 13 (/G)     → ต่อ GND     — เปิด output ตลอด

📌 Daisy Chain:
- 74HC595 #1: พิน 9 (Q7S) → 74HC595 #2: พิน 14 (SER)

📌 74HC595 #1 → RV8-Bus Address ต่ำ (A0-A7):
  พิน 15 (Q0) → Bus pin 1 (A0)
  พิน 1  (Q1) → Bus pin 2 (A1)
  พิน 2  (Q2) → Bus pin 3 (A2)
  พิน 3  (Q3) → Bus pin 4 (A3)
  พิน 4  (Q4) → Bus pin 5 (A4)
  พิน 5  (Q5) → Bus pin 6 (A5)
  พิน 6  (Q6) → Bus pin 7 (A6)
  พิน 7  (Q7) → Bus pin 8 (A7)

📌 74HC595 #2 → RV8-Bus Address สูง (A8-A14):
  พิน 15 (Q0) → Bus pin 9  (A8)
  พิน 1  (Q1) → Bus pin 10 (A9)
  พิน 2  (Q2) → Bus pin 11 (A10)
  พิน 3  (Q3) → Bus pin 12 (A11)
  พิน 4  (Q4) → Bus pin 13 (A12)
  พิน 5  (Q5) → Bus pin 14 (A13)
  พิน 6  (Q6) → Bus pin 15 (A14)
  พิน 7  (Q7) → (ปล่อยลอย ไม่ใช้)
```

---

## 3. ผังวงจรฝั่ง Data Bus (สื่อสารแบบ 2 ทาง)

ใช้ TXS0108E ตัวที่ 2 รับ-ส่ง 8 บิต ระหว่าง ESP32 (3.3V) และ RV8-Bus D[7:0] (5V)

```
[ ESP32 ฝั่ง 3.3V ]       [ TXS0108E ตัวที่ 2 ]          [ RV8-Bus Data ]

GPIO 13 ──────→ พิน 2 (A1) ←══→ พิน 19 (B1) ──→ Bus pin 17 (D0)
GPIO 12 ──────→ พิน 3 (A2) ←══→ พิน 18 (B2) ──→ Bus pin 18 (D1)
GPIO 14 ──────→ พิน 4 (A3) ←══→ พิน 17 (B3) ──→ Bus pin 19 (D2)
GPIO 27 ──────→ พิน 5 (A4) ←══→ พิน 16 (B4) ──→ Bus pin 20 (D3)
GPIO 26 ──────→ พิน 6 (A5) ←══→ พิน 15 (B5) ──→ Bus pin 21 (D4)
GPIO 25 ──────→ พิน 7 (A6) ←══→ พิน 14 (B6) ──→ Bus pin 22 (D5)
GPIO 33 ──────→ พิน 8 (A7) ←══→ พิน 13 (B7) ──→ Bus pin 23 (D6)
GPIO 32 ──────→ พิน 9 (A8) ←══→ พิน 12 (B8) ──→ Bus pin 24 (D7)
```

---

## 4. สัญญาณฟังจาก RV8-Bus (Input-only)

สัญญาณเหล่านี้ ESP32 ฟังอย่างเดียว (INPUT) สำหรับ RUN mode:

```
RV8-Bus pin 30 (/SLOT1) ──→ ESP32 GPIO 34  (ตรวจจับ CPU เข้าถึง I/O slot)
RV8-Bus pin 28 (/RD)    ──→ ESP32 GPIO 35  (CPU อ่านข้อมูล)
RV8-Bus pin 27 (/WR)    ──→ ESP32 GPIO 36  (CPU เขียนข้อมูล)
```

หมายเหตุ: GPIO 34-39 เป็น input-only บน ESP32 (ไม่มี pull-up ภายใน)
ใช้ตัวต้านทาน pull-up 10kΩ ภายนอกเข้า 5V ถ้าจำเป็น

---

## 5. PROG/RUN Switch

```
GPIO 39 (MODE) ──→ สวิตช์:
  - ต่อ GND = PROG mode (ESP32 ยึด bus, เขียน ROM)
  - ปล่อยลอย/ต่อ VCC = RUN mode (ESP32 ปล่อย bus, เป็น UART bridge)
```

---

## 6. RV8-Bus Pinout (อ้างอิง)

| Pin | Signal | Dir (CPU) | ใช้โดย Programmer |
|:---:|--------|:---------:|:-----------------:|
| 1-8 | A[7:0] | out | ✅ ขับผ่าน 595 #1 (PROG) |
| 9-15 | A[14:8] | out | ✅ ขับผ่าน 595 #2 (PROG) |
| 16 | A15 | out | ✅ ขับผ่าน 595 #2 (=0 for ROM) |
| 17-24 | D[7:0] | bidir | ✅ อ่าน/เขียนผ่าน TXS #2 |
| 25 | CLK | out | ❌ ไม่ใช้ |
| 26 | /RST | out | ✅ ESP32 ยึด LOW ตอน PROG |
| 27 | /WR | out | ✅ ESP32 pulse LOW ตอนเขียน |
| 28 | /RD | out | ✅ ESP32 pulse LOW ตอนอ่าน (→ ROM /OE) |
| 29 | /IRQ | in | ❌ ไม่ใช้ |
| 30 | /SLOT1 | out | ✅ ฟัง (RUN mode, UART bridge) |
| 31 | /SLOT2 | out | ❌ ไม่ใช้ |
| 32 | T2 | out | ❌ ไม่ใช้ |
| 39 | VCC | — | ✅ จ่ายไฟ 5V |
| 40 | GND | — | ✅ Ground |

---

## 7. การทำงานในแต่ละ Mode

### PROG Mode (เขียน/อ่าน ROM ผ่าน bus)

```
เขียน (Write):
1. ESP32 ยึด /RST = LOW (CPU หยุดทำงาน, ปล่อย bus)
2. ESP32 ขับ A[14:0] ผ่าน 74HC595 (A15=0 → ROM /CE active)
3. ESP32 ขับ D[7:0] ผ่าน TXS #2
4. ESP32 pulse /WR = LOW (1µs) → ROM รับข้อมูล
5. ทำซ้ำจนครบ

อ่าน (Read/Verify):
1. ESP32 ยึด /RST = LOW
2. ESP32 ขับ A[14:0] (A15=0 → ROM /CE active)
3. ESP32 ปล่อย D[7:0] เป็น input
4. ESP32 pulse /RD = LOW → ROM ปล่อยข้อมูลออกมา (/OE active)
5. ESP32 อ่าน D[7:0]
```

หมายเหตุ: ROM /CE ต่อกับ /A15 บน CPU board → Programmer ตั้ง A15=0 → ROM ถูกเลือกอัตโนมัติ
ถ้าไม่มี CPU (ROM อย่างเดียว) ก็ทำงานได้เหมือนกัน เพราะ Programmer ขับ /WR + /RD เอง

### RUN Mode (UART bridge ผ่าน /SLOT1)

```
1. ESP32 ปล่อย /RST = HIGH (CPU ทำงาน)
2. ESP32 ปล่อย address bus (595 output ไม่ conflict เพราะ CPU ขับแรงกว่า)
3. ESP32 ฟัง /SLOT1 + /WR → CPU เขียนข้อมูลมาที่ I/O → ส่งไป PC
4. ESP32 ฟัง /SLOT1 + /RD → CPU อ่านข้อมูล → ESP32 ขับ D[7:0] ตอบ
```

---

## 8. Bypass Capacitors

C 104 (0.1µF) เซรามิก คร่อม VCC-GND ของทุก IC:
- TXS0108E ตัวที่ 1: 1 ตัว
- TXS0108E ตัวที่ 2: 1 ตัว
- 74HC595 ตัวที่ 1: 1 ตัว
- 74HC595 ตัวที่ 2: 1 ตัว

**รวม 4 ตัว**

---

## 9. รายการอุปกรณ์ (BOM)

| Part | Qty | หน้าที่ |
|------|:---:|---------|
| ESP32-WROOM-32 | 1 | สมองหลัก |
| TXS0108E module (8-ch) | 2 | แปลงระดับไฟ 3.3V↔5V |
| 74HC595 | 2 | Shift register ขับ Address |
| 40-pin IDC connector | 1 | ต่อ RV8-Bus |
| 40-pin ribbon cable | 1 | เชื่อมไป CPU board |
| 100nF capacitor | 4 | Bypass |
| สวิตช์ SPDT | 1 | PROG/RUN |
| USB cable (micro-B) | 1 | PC → ESP32 |

---

## 10. ESP32 GPIO Summary

| GPIO | Function | Direction | Via |
|:----:|----------|:---------:|-----|
| 23 | SR_DATA | OUT | TXS #1 → 595 SER |
| 18 | SR_CLK | OUT | TXS #1 → 595 SRCLK |
| 19 | SR_LATCH | OUT | TXS #1 → 595 RCLK |
| 4 | /RST | OUT | TXS #1 → Bus pin 26 |
| 16 | /WR | OUT | TXS #1 → Bus pin 27 |
| 17 | /RD | OUT/IN | TXS #1 → Bus pin 28 (OUT in PROG, IN in RUN) |
| 13 | D0 | BIDIR | TXS #2 → Bus pin 17 |
| 12 | D1 | BIDIR | TXS #2 → Bus pin 18 |
| 14 | D2 | BIDIR | TXS #2 → Bus pin 19 |
| 27 | D3 | BIDIR | TXS #2 → Bus pin 20 |
| 26 | D4 | BIDIR | TXS #2 → Bus pin 21 |
| 25 | D5 | BIDIR | TXS #2 → Bus pin 22 |
| 33 | D6 | BIDIR | TXS #2 → Bus pin 23 |
| 32 | D7 | BIDIR | TXS #2 → Bus pin 24 |
| 34 | /SLOT1 | IN | Bus pin 30 |
| 35 | /RD (sense) | IN | Bus pin 28 |
| 36 | /WR (sense) | IN | Bus pin 27 |
| 39 | MODE | IN | PROG/RUN switch |

**Total: 18 GPIO used**

---

*เขียนสำหรับน้อง ๆ ม.ต้น — ถ้าติดตรงไหนถามพี่ได้เลย!*
