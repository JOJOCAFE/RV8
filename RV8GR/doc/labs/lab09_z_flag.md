# Lab 09: Z Flag — ตรวจจับค่าศูนย์

**เป้าหมาย**: ต่อ U22 (74HC688, comparator) + U21 (74HC74, flip-flop) ให้ CPU รู้ว่า "ผลลัพธ์เป็น 0 หรือไม่"

---

## ความรู้พื้นฐาน

- **U22 (74HC688)**: เปรียบเทียบ 8 บิต — ถ้า P=Q → output LOW
  - เราต่อ P ← AC, Q ← GND (0) → ถ้า AC=0 → /P=Q = LOW
- **U21 (74HC74)**: D flip-flop สำหรับ Z flag
  - Z=1 เมื่อ AC=0, Z=0 เมื่อ AC≠0
  - ใช้ /PR (async preset) เพื่อ set Z=1 ทันทีเมื่อ AC=0

### Truth Table

| AC | /P=Q (U22-19) | Z flag (U21-5) | ความหมาย |
|:--:|:-------------:|:--------------:|----------|
| $00 | LOW | 1 (ติด) | ผลลัพธ์เป็นศูนย์ |
| $01 | HIGH | 0 (ดับ) | ผลลัพธ์ไม่เป็นศูนย์ |
| $42 | HIGH | 0 (ดับ) | ผลลัพธ์ไม่เป็นศูนย์ |
| $FF | HIGH | 0 (ดับ) | ผลลัพธ์ไม่เป็นศูนย์ |

### วิธีทำงาน (Timing)

```
ACC_CLK ──────────┐
                     ▼ (rising edge)
          ┌─────────────────────┐
          │ U21 (74HC74)        │
          │ CLK↑ → D=0 → Q=0   │ ← clear Z ก่อน
          │                     │
          │ แล้วถ้า AC=0:       │
          │ /PR=LOW → Q=1       │ ← preset Z=1 ทันที
          └─────────────────────┘

Timeline:
  CLK↑ ────────── Z cleared to 0
  +20ns ───────── AC ค่าใหม่ stable
  +50ns ───────── U22 เปรียบเทียบเสร็จ
  +50ns ───────── /PR → Z=1 (ถ้า AC=0)
  ─────────────── Z stable ก่อน BEQ/BNE ใช้งานใน T2 ถัดไป (~200ns)
```

> 💡 **ทำไมใช้ Async Preset แทน Synchronous D-input?**
>
> วิธีปกติใน CPU: ใช้ D=comparator_output + CLK=Acc_Load
> RV8-GR เลือกใช้ /PR (async) เพราะ:
> 1. **ไม่ต้อง inverter เพิ่ม** — 74HC688 output = active-low = /PR input ตรงๆ
> 2. **ประหยัด 1 gate**
> 3. **Z path มี margin ที่ 5 MHz** — Z flag settle ภายใน ~100ns, แต่ถูก sample ที่ T2
>    ของคำสั่งถัดไป (200ns+ ทีหลัง)
>
> ⚠️ ถ้าจะทดลองความเร็วสูงกว่าขอบเขต RV8GR v1.0 ให้กลับไปดู timing ใน
> `../01_wiring_guide.md` และบันทึกผลจริงใน `../07_real_build_timing_log.md`.
>
> สำหรับ CPU ทั้งเครื่อง: breadboard target คือ 1 MHz; 5 MHz เป็น PCB-only experiment.

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC688 (U22, zero comparator) | 1 |
| 2 | 74HC74 (U21, Z flag flip-flop) | 1 |
| 3 | LED สีแดง 3mm | 1 |
| 4 | 330Ω resistor | 1 |
| 5 | 100nF capacitor | 2 |

---

## วงจร

### Pinout: 74HC688

```
        ┌───U───┐
 /OE  1 │       │ 20 VCC
  A0  2 │       │ 19 Y  ← OUTPUT!
  B0  3 │ 688   │ 18 B7
  A1  4 │       │ 17 A7
  B1  5 │       │ 16 B6
  A2  6 │       │ 15 A6
  B2  7 │       │ 14 B5
  A3  8 │       │ 13 A5
  B3  9 │       │ 12 B4
 GND 10 │       │ 11 A4
        └───────┘
```

### Pinout: 74HC74

```
        ┌───U───┐
/CLR1 1 │       │ 14 VCC
   D1 2 │       │ 13 /CLR2
 CLK1 3 │  74   │ 12 D2
/PR1  4 │       │ 11 CLK2
  Q1  5 │       │ 10 /PR2
 /Q1  6 │       │  9 Q2
 GND  7 │       │  8 /Q2
        └───────┘
```

### การต่อสาย

```
U22 (Zero Comparator):
  pin 20 (VCC) → 5V,  pin 10 (GND) → GND,  100nF คร่อม VCC-GND
  pin 1 (/OE) → GND (enable ตลอด)

  A inputs ← AC (U9 Q outputs):
    pin 2 (A0) ← U9-19 (AC0)
    pin 4 (A1) ← U9-18 (AC1)
    pin 6 (A2) ← U9-17 (AC2)
    pin 8 (A3) ← U9-16 (AC3)
    pin 11(A4) ← U9-15 (AC4)
    pin 13(A5) ← U9-14 (AC5)
    pin 15(A6) ← U9-13 (AC6)
    pin 17(A7) ← U9-12 (AC7)

  B inputs ← GND (เปรียบเทียบกับ 0):
    pin 3 (B0) → GND
    pin 5 (B1) → GND
    pin 7 (B2) → GND
    pin 9 (B3) → GND
    pin 12(B4) → GND
    pin 14(B5) → GND
    pin 16(B6) → GND
    pin 18(B7) → GND

  pin 19 (Y, active-low equal) → U21 pin 4 (/PR1)
    [เมื่อ AC=0: Y goes LOW → preset Z=1]

U21 (Z flag flip-flop):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  FF1 (Z flag):
    pin 1 (/CLR1) → VCC (ไม่ clear)
    pin 2 (D1) → GND (D=0 เสมอ)
    pin 3 (CLK1) ← ACC_CLK (U27-11)
    pin 4 (/PR1) ← U22-19 (/P=Q)
    pin 5 (Q1) → Z_flag → LED + U28-1
```

> 💡 **ACC_CLK คืออะไร?**
>
> ACC_CLK = สัญญาณ clock ตัวเดียวกับที่ load AC (U9 pin 11)
> 74HC74 trigger ที่ **rising edge** → CLK↑ จะ clear Z=0 ก่อน
> แล้ว /PR จาก U22 จึง preset Z=1 ถ้า AC=0
>
> Lab นี้ใช้ปุ่มเดียวกับที่ clock AC (จาก Lab 08)
> ใน CPU จริง มาจาก logic: T2 AND AC_WR (U27-11)

  FF2 (ไม่ใช้ใน lab นี้):
    pin 8 (/Q2) → NC
    pin 9 (Q2) → NC
    pin 10(/PR2) → VCC
    pin 11(CLK2) → GND
    pin 12(D2) → GND
    pin 13(/CLR2) → VCC

  LED (ดู Z flag):
    U21-5 (Q1) → 330Ω → LED → GND

วิธีทำงาน:
  1. เมื่อ ACC_CLK pulse (CLK↑): D=0 → Z ถูก clear เป็น 0
  2. ทันทีหลังจากนั้น: ถ้า AC=0 → /P=Q=LOW → /PR=LOW → preset Z=1
  3. ผลลัพธ์สุทธิ: Z=1 เมื่อ AC=0, Z=0 เมื่อ AC≠0
```

---

## ทดสอบ ✅

ใช้วงจรจาก Lab 08 (AC ทำงานอยู่แล้ว)

### Test 1: AC ≠ 0 → Z=0

| ขั้น | ทำอะไร | AC | Z LED | ถูก? |
|:----:|--------|:--:|:-----:|:----:|
| 1 | LI $42 (ใส่ค่า $42 ใน AC) | $42 | ดับ (Z=0) | ☐ |
| 2 | LI $FF | $FF | ดับ (Z=0) | ☐ |
| 3 | LI $01 | $01 | ดับ (Z=0) | ☐ |

### Test 2: AC = 0 → Z=1

| ขั้น | ทำอะไร | AC | Z LED | ถูก? |
|:----:|--------|:--:|:-----:|:----:|
| 1 | LI $42 → SUBI $42 | $00 | ติด (Z=1) | ☐ |
| 2 | LI $00 | $00 | ติด (Z=1) | ☐ |

### Test 3: Z กลับเป็น 0 เมื่อ AC≠0 อีกครั้ง

| ขั้น | ทำอะไร | AC | Z LED | ถูก? |
|:----:|--------|:--:|:-----:|:----:|
| 1 | เริ่มจาก AC=$00, Z=1 | $00 | ติด | ☐ |
| 2 | ADDI $01 | $01 | ดับ (Z=0) | ☐ |
| 3 | SUBI $01 | $00 | ติด (Z=1) | ☐ |

### ทดสอบ async preset toggle
- [ ] LI $00 → Z LED ON
- [ ] LI $01 → Z LED OFF
- [ ] LI $00 → Z LED ON อีกครั้ง (toggle กลับได้ = async preset ทำงาน)

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| Z ติดตลอดไม่ว่า AC เป็นเท่าไร | /PR ค้าง LOW | เช็ค U22-19: ต้อง HIGH เมื่อ AC≠0 |
| Z ไม่ติดเลยแม้ AC=0 | /PR ไม่ต่อ U22-19 | เช็คสาย U22-19 → U21-4 |
| Z ค้าง 0 หลัง AC กลับเป็น 0 | CLK ไม่ pulse | เช็ค ACC_CLK → U21-3 |
| Z กระพริบ/unstable | noise บน AC | เพิ่ม 100nF ที่ U22 VCC-GND |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab09_z_flag.py
```

---

## สิ่งที่ได้

- ✅ U22 ตรวจจับ AC=0 ได้ถูกต้อง (comparator with Q=0)
- ✅ U21 เก็บ Z flag: Z=1 เมื่อ AC=0, Z=0 เมื่อ AC≠0
- ✅ Async preset = Z update ทันทีเมื่อ AC เปลี่ยน (ไม่ต้องรอ clock ตัวที่สอง)
- ✅ Z path มี margin ที่ 5 MHz, แต่ CPU breadboard target ยังเป็น 1 MHz
- ✅ พร้อมใช้ Z flag สำหรับ BEQ/BNE ใน Lab 10!

**ผ่านทุกข้อ → ไป Lab 10!** 🎉
