# Lab 03: Program Counter — นับตำแหน่งคำสั่ง

**เป้าหมาย**: ต่อ U1-U4 (74HC161 ×4) เป็น counter 16 บิต นับขึ้นทีละ 1

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC161 (U1-U4) | 4 |
| 2 | LED สีเขียว 3mm | 8 |
| 3 | 330Ω resistor | 8 |
| 4 | 100nF capacitor | 4 |

---

## วงจร

### Pinout: 74HC161

```
          ┌───U───┐
  /CLR  1 │       │ 16 VCC
   CLK  2 │       │ 15 RCO
    D0  3 │ 161   │ 14 QA (bit 0)
    D1  4 │       │ 13 QB (bit 1)
    D2  5 │       │ 12 QC (bit 2)
    D3  6 │       │ 11 QD (bit 3)
   ENP  7 │       │ 10 ENT
   GND  8 │       │  9 /LD
          └───────┘
```

### การต่อสาย

```
ทุกตัว (U1-U4):
  pin 16 (VCC) → 5V
  pin 8 (GND) → GND
  pin 1 (/CLR) → ปุ่ม Reset (ปกติ HIGH)
  pin 2 (CLK) → สาย CLK จาก Lab 01
  pin 7 (ENP) → 5V (enable นับตลอด)
  pin 9 (/LD) → 5V (ไม่ load, นับอย่างเดียว)
  100nF คร่อม VCC-GND ทุกตัว

Cascade (ต่อพ่วง):
  U1 pin 10 (ENT) → 5V (ตัวแรก enable ตลอด)
  U1 pin 15 (RCO) → U2 pin 10 (ENT)
  U2 pin 15 (RCO) → U3 pin 10 (ENT)
  U3 pin 15 (RCO) → U4 pin 10 (ENT)

LED (ดู 8 บิตล่าง = U1 + U2):
  U1 pin 14 (QA=bit0) → 330Ω → LED → GND
  U1 pin 13 (QB=bit1) → 330Ω → LED → GND
  U1 pin 12 (QC=bit2) → 330Ω → LED → GND
  U1 pin 11 (QD=bit3) → 330Ω → LED → GND
  U2 pin 14 (QA=bit4) → 330Ω → LED → GND
  U2 pin 13 (QB=bit5) → 330Ω → LED → GND
  U2 pin 12 (QC=bit6) → 330Ω → LED → GND
  U2 pin 11 (QD=bit7) → 330Ω → LED → GND
```

---

## ทดสอบ ✅

### ขั้นตอน

1. กด Reset → LED ทั้ง 8 ดับ (PC = 0000 0000)
2. กด Clock ทีละครั้ง → LED นับขึ้น:

### ตาราง LED (อ่านจากขวาไปซ้าย = bit7...bit0)

| กด | bit7 | bit6 | bit5 | bit4 | bit3 | bit2 | bit1 | bit0 | ค่า | ถูก? |
|:--:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:---:|:----:|
| Reset | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | $00 | ☐ |
| 1 | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● | $01 | ☐ |
| 2 | ○ | ○ | ○ | ○ | ○ | ○ | ● | ○ | $02 | ☐ |
| 3 | ○ | ○ | ○ | ○ | ○ | ○ | ● | ● | $03 | ☐ |
| 4 | ○ | ○ | ○ | ○ | ○ | ● | ○ | ○ | $04 | ☐ |
| 15 | ○ | ○ | ○ | ○ | ● | ● | ● | ● | $0F | ☐ |
| 16 | ○ | ○ | ○ | ● | ○ | ○ | ○ | ○ | $10 | ☐ |

● = LED ติด (1), ○ = LED ดับ (0)

**สำคัญ**: ถ้ากด 16 ครั้งแล้ว bit4 ติด = cascade ทำงาน!

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| ไม่นับเลย | ENP หรือ ENT ไม่ HIGH | เช็คสาย pin 7, 10 |
| นับแค่ 0-15 วน | U2 ENT ไม่ต่อ U1 RCO | ต่อ U1-15 → U2-10 |
| นับ 2 ทีละครั้ง | Clock bounce | เพิ่ม 100nF ที่ปุ่ม |
| Reset ไม่ทำงาน | /CLR ค้าง HIGH | เช็คปุ่ม Reset |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab02_pc_counter.py
```

---

## สิ่งที่ได้

- ✅ Counter 16 บิต นับ $0000 → $FFFF
- ✅ Reset กลับ $0000 ได้
- ✅ Cascade: U1 เต็ม → U2 นับต่อ → U3 → U4
- ✅ นี่คือ Program Counter ของ CPU!

**ผ่านทุกข้อ → ไป Lab 04!** 🎉
