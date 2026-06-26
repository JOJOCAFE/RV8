# Lab 08: Accumulator + Mux — เก็บผลลัพธ์ + เลือก input

**เป้าหมาย**: ต่อ U9 (AC), U14 (AC buffer), U17-U18 (AC input mux), U19-U20 (XOR B-input mux) ให้ ALU เก็บผลลัพธ์และเลือก mode ได้

---

## ความรู้พื้นฐาน

- **U9 (74HC574, Accumulator)**: จำผลลัพธ์ของ ALU — "คำตอบล่าสุด"
- **U14 (74HC541, AC buffer)**: ส่งค่า AC ออก IBUS ตอน STORE
- **U17-U18 (74HC157, AC input mux)**: เลือกว่า AC จะรับจาก Adder หรือ XOR output
  - MUX_SEL=0 → AC ← Adder SUM (สำหรับ ADD/SUB)
  - MUX_SEL=1 → AC ← XOR output (สำหรับ XOR instruction)
- **U19-U20 (74HC157, XOR B-input mux)**: เลือก XOR B-input
  - XOR_MODE=0 → B = ALU_SUB ทุกบิต (สำหรับ ADD/SUB)
  - XOR_MODE=1 → B = AC bits (สำหรับ XOR instruction: IBUS XOR AC)

### Full ALU Datapath (ภาพรวม)

```
                XOR_MODE          MUX_SEL
                   │                 │
                   ▼                 ▼
AC(old) ──┬──► U19/U20 ──► U12/U13 ──┬──► U17/U18 ──► AC(new)
           │   (B mux)     (XOR)      │   (result mux)    ▲
           │                │          │      ▲            │
           │                ▼          │      │            │
           └──────────► U10/U11 ──────►┘      │         CLK edge
                        (Adder)            Adder output
                           ▲
                           │
                       IBUS (operand)
```

> 💡 **ไม่มี Combinational Loop!**
>
> แม้ AC output ต่อกลับไปที่ ALU input ผ่าน U19/U20
> แต่ **AC เป็น register** — ค่าเปลี่ยนเฉพาะตอน CLK rising edge
>
> ดังนั้น: AC(old) → ALU คำนวณ → ผลรอที่ D input → CLK↑ → AC(new)
>
> ไม่มีการวิ่งวนเอง — register ตัด loop ทุกรอบ clock!

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC574 (U9, Accumulator) | 1 |
| 2 | 74HC541 (U14, AC buffer) | 1 |
| 3 | 74HC157 (U17, U18, AC input mux) | 2 |
| 4 | 74HC157 (U19, U20, XOR B-input mux) | 2 |
| 5 | LED สีเหลือง 3mm | 8 |
| 6 | 330Ω resistor | 8 |
| 7 | 100nF capacitor | 5 |
| 8 | Push button (clock AC) | 1 |

---

## วงจร

### Pinout: 74HC541

```
        ┌───U───┐
 /OE1 1 │       │ 20 VCC
  A1  2 │       │ 19 /OE2
  A2  3 │ 541   │ 18 Y1
  A3  4 │       │ 17 Y2
  A4  5 │       │ 16 Y3
  A5  6 │       │ 15 Y4
  A6  7 │       │ 14 Y5
  A7  8 │       │ 13 Y6
  A8  9 │       │ 12 Y7
 GND 10 │       │ 11 Y8
        └───────┘
```

### การต่อสาย

```
U19 (XOR B-input mux, bits 0-3):
  pin 16 (VCC) → 5V,  pin 8 (GND) → GND,  pin 15 (/E) → GND
  pin 1 (SEL) ← XOR_MODE (U5 pin 13)
  
  pin 2 (1A) ← ALU_SUB (U5 pin 12)    pin 3 (1B) ← AC0 (U9 pin 19)
  pin 4 (1Y) → U12 pin 2 (XOR gate 1 B-input)
  
  pin 5 (2A) ← ALU_SUB                 pin 6 (2B) ← AC1 (U9 pin 18)
  pin 7 (2Y) → U12 pin 5
  
  pin 11(3A) ← ALU_SUB                 pin 10(3B) ← AC2 (U9 pin 17)
  pin 9 (3Y) → U12 pin 10
  
  pin 14(4A) ← ALU_SUB                 pin 13(4B) ← AC3 (U9 pin 16)
  pin 12(4Y) → U12 pin 13
  100nF คร่อม VCC-GND

U20 (XOR B-input mux, bits 4-7):
  pin 16 (VCC) → 5V,  pin 8 (GND) → GND,  pin 15 (/E) → GND
  pin 1 (SEL) ← XOR_MODE (U5 pin 13)
  
  pin 2 (1A) ← ALU_SUB                 pin 3 (1B) ← AC4 (U9 pin 15)
  pin 4 (1Y) → U13 pin 2
  
  pin 5 (2A) ← ALU_SUB                 pin 6 (2B) ← AC5 (U9 pin 14)
  pin 7 (2Y) → U13 pin 5
  
  pin 11(3A) ← ALU_SUB                 pin 10(3B) ← AC6 (U9 pin 13)
  pin 9 (3Y) → U13 pin 10
  
  pin 14(4A) ← ALU_SUB                 pin 13(4B) ← AC7 (U9 pin 12)
  pin 12(4Y) → U13 pin 13
  100nF คร่อม VCC-GND

U17 (AC input mux, bits 0-3):
  pin 16 (VCC) → 5V,  pin 8 (GND) → GND,  pin 15 (/E) → GND
  pin 1 (SEL) ← MUX_SEL (U5 pin 14)
  
  pin 2 (1A) ← SUM0 (U10 pin 4)       pin 3 (1B) ← XOR_Y0 (U12 pin 3)
  pin 4 (1Y) → U9 pin 2 (D1)
  
  pin 5 (2A) ← SUM1 (U10 pin 1)       pin 6 (2B) ← XOR_Y1 (U12 pin 6)
  pin 7 (2Y) → U9 pin 3 (D2)
  
  pin 11(3A) ← SUM2 (U10 pin 13)      pin 10(3B) ← XOR_Y2 (U12 pin 8)
  pin 9 (3Y) → U9 pin 4 (D3)
  
  pin 14(4A) ← SUM3 (U10 pin 10)      pin 13(4B) ← XOR_Y3 (U12 pin 11)
  pin 12(4Y) → U9 pin 5 (D4)
  100nF คร่อม VCC-GND

U18 (AC input mux, bits 4-7):
  pin 16 (VCC) → 5V,  pin 8 (GND) → GND,  pin 15 (/E) → GND
  pin 1 (SEL) ← MUX_SEL (U5 pin 14)
  
  pin 2 (1A) ← SUM4 (U11 pin 4)       pin 3 (1B) ← XOR_Y4 (U13 pin 3)
  pin 4 (1Y) → U9 pin 6 (D5)
  
  pin 5 (2A) ← SUM5 (U11 pin 1)       pin 6 (2B) ← XOR_Y5 (U13 pin 6)
  pin 7 (2Y) → U9 pin 7 (D6)
  
  pin 11(3A) ← SUM6 (U11 pin 13)      pin 10(3B) ← XOR_Y6 (U13 pin 8)
  pin 9 (3Y) → U9 pin 8 (D7)
  
  pin 14(4A) ← SUM7 (U11 pin 10)      pin 13(4B) ← XOR_Y7 (U13 pin 11)
  pin 12(4Y) → U9 pin 9 (D8)
  100nF คร่อม VCC-GND

U9 (Accumulator):
  pin 20 (VCC) → 5V,  pin 10 (GND) → GND
  pin 1 (/OE) → GND (output ตลอด)
  pin 11 (CLK) ← ปุ่ม clock (สำหรับ lab นี้; จริงๆ ต่อ ACC_CLK จาก U27-11)
  D inputs: จาก U17-U18 outputs (ด้านบน)
  Q outputs → LED + ALU + mux feedback:
    pin 19 (Q1) → AC0 → LED0, U10-5, U19-3, U14-2, U22-2
    pin 18 (Q2) → AC1 → LED1, U10-3, U19-6, U14-3, U22-4
    pin 17 (Q3) → AC2 → LED2, U10-14, U19-10, U14-4, U22-6
    pin 16 (Q4) → AC3 → LED3, U10-12, U19-13, U14-5, U22-8
    pin 15 (Q5) → AC4 → LED4, U11-5, U20-3, U14-6, U22-12
    pin 14 (Q6) → AC5 → LED5, U11-3, U20-6, U14-7, U22-14
    pin 13 (Q7) → AC6 → LED6, U11-14, U20-10, U14-8, U22-16
    pin 12 (Q8) → AC7 → LED7, U11-12, U20-13, U14-9, U22-18
  100nF คร่อม VCC-GND

  LED (ดู AC):
    AC0 → 330Ω → LED → GND ... (ทุกบิต)
```

> ⚠️ **U9 /OE ใน Lab vs CPU จริง**
>
> Lab นี้ต่อ U9 /OE = GND (output ตลอด) เพื่อให้เห็น LED
> แต่ **AC ไม่ขับ IBUS โดยตรง** — ต้องผ่าน U14 (buffer) เสมอ
> U14 มี /OE ที่ถูกควบคุม → เปิดเฉพาะตอน STORE เท่านั้น
> ป้องกันไม่ให้ AC ชนกับ ROM/RAM/IRL บน IBUS

> 💡 **MUX_SEL / XOR_MODE / ALU_SUB — มาจากไหน?**
>
> Lab นี้ใช้ switch กำหนดเอง (สะดวกสำหรับทดสอบ)
> แต่ใน CPU จริง สัญญาณเหล่านี้มาจาก **IR High (U5)** โดยตรง:
> - MUX_SEL = bit5 (U5 pin 14)
> - XOR_MODE = bit6 (U5 pin 13)
> - ALU_SUB = bit7 (U5 pin 12)
>
> Lab 09 เป็นต้นไปจะเชื่อม IR → control signals จริง!

U14 (AC output buffer):
  pin 20 (VCC) → 5V,  pin 10 (GND) → GND
  pin 1 (/OE1) ← /AC_BUF (จริงๆ จาก U26-8; สำหรับ lab ใช้ switch)
  pin 19(/OE2) ← /AC_BUF (ต่อเหมือน /OE1)
  A inputs ← AC:
    pin 2 ← AC0, pin 3 ← AC1, pin 4 ← AC2, pin 5 ← AC3
    pin 6 ← AC4, pin 7 ← AC5, pin 8 ← AC6, pin 9 ← AC7
  Y outputs → IBUS:
    pin 18 → IBUS0, pin 17 → IBUS1, pin 16 → IBUS2, pin 15 → IBUS3
    pin 14 → IBUS4, pin 13 → IBUS5, pin 12 → IBUS6, pin 11 → IBUS7
  100nF คร่อม VCC-GND
```

---

## ทดสอบ ✅

### Test 1: ADDI — ใส่ค่า IBUS แล้ว clock AC

เริ่ม: AC = unknown (74HC574 has no /CLR), MUX_SEL=0 (เลือก adder), XOR_MODE=0, ALU_SUB=0

| ขั้น | IBUS (DIP) | ALU_SUB | MUX_SEL | กด AC CLK | AC LED (ผลลัพธ์) | ถูก? |
|:----:|:----------:|:-------:|:-------:|:---------:|:----------------:|:----:|
| 1 | $05 | 0 | 0 | กด | $05 (0+5=5) | ☐ |
| 2 | $03 | 0 | 0 | กด | $08 (5+3=8) | ☐ |
| 3 | $02 | 1 | 0 | กด | $06 (8-2=6) | ☐ |
| 4 | $06 | 1 | 0 | กด | $00 (6-6=0) | ☐ |

### Test 2: XOR mode

ตั้ง XOR_MODE=1, MUX_SEL=1

| ขั้น | AC ก่อน | IBUS | กด AC CLK | AC ใหม่ (= IBUS XOR AC) | ถูก? |
|:----:|:-------:|:----:|:---------:|:------------------------:|:----:|
| 1 | $00 | $FF | กด | $FF (00 XOR FF) | ☐ |
| 2 | $FF | $AA | กด | $55 (FF XOR AA) | ☐ |
| 3 | $55 | $55 | กด | $00 (55 XOR 55) | ☐ |

### Test 3: AC buffer (U14)

ตั้ง AC = $42 (จาก test ก่อนหน้า หรือกด CLK ให้ได้ $42)
สลับ /AC_BUF = LOW → ดู IBUS LED ต้องเป็น $42

| /AC_BUF | IBUS LED | ถูก? |
|:-------:|:--------:|:----:|
| HIGH | ลอย/ไม่ขับ | ☐ |
| LOW | = AC ($42) | ☐ |

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| AC ไม่เปลี่ยนเมื่อกด | CLK ไม่ pulse | เช็คปุ่ม → U9 pin 11 |
| ผลบวกถูกแต่ XOR ผิด | MUX_SEL ไม่ถึง U17/U18 | เช็ค pin 1 ทุกตัว |
| XOR กลับบิตตอน ADD | XOR_MODE ค้าง HIGH | เช็ค U19/U20 pin 1 |
| AC buffer ไม่ออก IBUS | /OE ค้าง HIGH | เช็ค U14 pin 1, 19 |
| ค่า feedback loop ผิด | AC output ไม่ต่อกลับ mux | เช็ค U9-Q → U19/U20 pin B |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR-V2/sim/sim_lab
python3 lab08_ac_mux.py
```

---

## Test 4: Carry Flag (เตรียมสำหรับ Lab 09)

ตั้ง MUX_SEL=0, XOR_MODE=0, ALU_SUB=0

| ขั้น | AC ก่อน | IBUS | กด CLK | AC ใหม่ | Cout (LED แดง) | หมายเหตุ | ถูก? |
|:----:|:-------:|:----:|:------:|:-------:|:--------------:|----------|:----:|
| 1 | $00 | $FF | กด | $FF | ○ | ไม่ล้น | ☐ |
| 2 | $FF | $01 | กด | $00 | ● | ล้น! AC กลับเป็น 0 | ☐ |
| 3 | $00 | $01 | กด | $01 | ○ | ปกติ | ☐ |

> 💡 **Carry = สัญญาณบอกว่า "ผลเกิน 8 บิต"**
>
> $FF + $01 = $100 → เก็บได้แค่ 8 บิต = $00, Carry=1
> Lab 09 จะเพิ่ม **Z Flag register** เพื่อจำว่า AC=0 หรือไม่
> (RV8-GR ใช้ Z flag สำหรับ BEQ/BNE)

---

## ISA Mapping — ทำอะไรได้แล้ว?

| Instruction | XOR_MODE | ALU_SUB | MUX_SEL | ผล |
|:-----------:|:--------:|:-------:|:-------:|:---|
| ADDI imm | 0 | 0 | 0 | AC = AC + imm |
| SUBI imm | 0 | 1 | 0 | AC = AC − imm |
| XORI imm | 1 | — | 1 | AC = AC XOR imm |
| LI imm | 0 | 0 | 1 | AC = imm (XOR output = imm XOR 0) |

> LI ทำงานได้เพราะ: XOR_MODE=0 → B=0, XOR output = IBUS XOR 0 = IBUS
> MUX_SEL=1 → AC ← XOR output = IBUS = immediate value!

---

## สิ่งที่ได้

- ✅ AC เก็บผลลัพธ์ ALU ได้ (state!)
- ✅ MUX_SEL เลือกระหว่าง Adder กับ XOR output
- ✅ XOR_MODE เลือก B-input ของ XOR gate (SUB constant vs AC feedback)
- ✅ AC buffer ส่งค่า AC ออก IBUS ได้ (สำหรับ STORE)
- ✅ Full ALU: ADD, SUB, XOR ครบตาม ISA!
- ✅ ตอนนี้ CPU คำนวณ + เก็บผลลัพธ์ได้แล้ว!

**ผ่านทุกข้อ → ไป Lab 09!** 🎉
