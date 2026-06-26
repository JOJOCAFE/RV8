# Lab 07: Adder/Subtractor — สร้างเครื่องบวกลบ 8 บิต

**เป้าหมาย**: ต่อ U10-U11 (74HC283 ×2 adder) + U12-U13 (74HC86 ×2 XOR) ให้คำนวณ ADD และ SUB

---

## ความรู้พื้นฐาน

### Block Diagram

```
        IBUS (operand)        ALU_SUB
             │                   │
             ▼                   ▼
        ┌─────────┐        ┌─────────┐
        │ XOR Bank│◄───────│ ALU_SUB │
        │ U12-U13 │        │ (switch)│
        └────┬────┘        └────┬────┘
             │ (B modified)      │
             ▼                   │
AC ────► ┌───────┐              │
         │ Adder │◄─────────────┘ Cin
         │U10-U11│
         └───┬───┘
             │
             ▼
         Result (LED)
         + Cout (Carry)
```

### หลักการทำงาน

ALU_SUB = 0 (ADD):
```
XOR gate: B XOR 0 = B (ผ่านตรง ไม่เปลี่ยน)
Cin = 0
Result = AC + B
```

ALU_SUB = 1 (SUB):
```
XOR gate: B XOR 1 = ~B (กลับทุกบิต)
Cin = 1
Result = AC + (~B) + 1 = AC - B
```

นี่คือ **Two's Complement Subtraction** — วิธีเดียวกับที่ CPU ทุกตัวใช้!

### Carry/Borrow

| Mode | Cout=1 | Cout=0 |
|:----:|--------|--------|
| ADD | Carry (ล้น) | ไม่ล้น |
| SUB | **ไม่มี borrow** (A ≥ B) | **มี borrow** (A < B) |

> 💡 **ทำไม SUB ถึงกลับด้าน?**
>
> เพราะเราใช้ A + (~B) + 1 แทน A - B
> ถ้า A ≥ B → ผลบวกล้น → Cout = 1 → ไม่มี borrow
> ถ้า A < B → ผลบวกไม่ล้น → Cout = 0 → มี borrow

### Carry Chain — ทำไมต้อง 2 ตัว?

74HC283 บวกได้ 4 บิตเท่านั้น (0-15) ต้องต่อ 2 ตัว cascade:
```
U10: bit0-3 (nibble ล่าง)
      │ Cout
      ▼ Cin
U11: bit4-7 (nibble บน)
```
Cout ของ U10 → Cin ของ U11 เพื่อส่ง carry ต่อไป

> ⚠️ **XOR gate ใน Lab นี้**
>
> XOR gate (U12-U13) ทำหน้าที่ **กลับบิต B** สำหรับ SUB เท่านั้น
> ยังไม่ใช่ XOR operation ของ ISA (AC XOR operand)
>
> XOR operation จริง (opcode $70) จะใช้ B-input mux (U19-U20)
> เพื่อเลือก AC เป็น XOR B-input + AC input mux (U17-U18)
> เพื่อส่ง XOR output ไป AC — จะทำใน **Lab 08**

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC283 (U10, U11) | 2 |
| 2 | 74HC86 (U12, U13) | 2 |
| 3 | DIP switch 8 ตัว (จำลอง IBUS = operand) | 1 |
| 4 | DIP switch 8 ตัว (จำลอง AC = accumulator) | 1 |
| 5 | Slide switch (ALU_SUB) | 1 |
| 6 | LED สีเหลือง 3mm | 8 |
| 7 | LED สีแดง 3mm | 1 |
| 8 | 330Ω resistor | 9 |
| 9 | 100nF capacitor | 4 |

---

## วงจร

### Pinout: 74HC283

```
        ┌───U───┐
  S1  1 │       │ 16 VCC
  B1  2 │       │ 15 B2
  A1  3 │ 283   │ 14 A2
  S0  4 │       │ 13 S2
  A0  5 │       │ 12 A3
  B0  6 │       │ 11 B3
 Cin  7 │       │ 10 S3
 GND  8 │       │  9 Cout
        └───────┘
```

### Pinout: 74HC86

```
        ┌───U───┐
  1A  1 │       │ 14 VCC
  1B  2 │       │ 13 4B
  1Y  3 │  86   │ 12 4A
  2A  4 │       │ 11 4Y
  2B  5 │       │ 10 3B
  2Y  6 │       │  9 3A
 GND  7 │       │  8 3Y
        └───────┘
```

### การต่อสาย

```
ทุกตัว ไฟเลี้ยง:
  U10: pin 16=VCC, pin 8=GND, 100nF
  U11: pin 16=VCC, pin 8=GND, 100nF
  U12: pin 14=VCC, pin 7=GND, 100nF
  U13: pin 14=VCC, pin 7=GND, 100nF

XOR B-input (กลับบิต B สำหรับ SUB):
  สำหรับ lab นี้: ต่อ XOR B-input = ALU_SUB switch ทุกขา
  (ในวงจรจริง B-input มาจาก U19-U20 mux — Lab 08)

  U12 pin 2 (1B) ← ALU_SUB switch
  U12 pin 5 (2B) ← ALU_SUB switch
  U12 pin 10(3B) ← ALU_SUB switch
  U12 pin 13(4B) ← ALU_SUB switch
  U13 pin 2 (1B) ← ALU_SUB switch
  U13 pin 5 (2B) ← ALU_SUB switch
  U13 pin 10(3B) ← ALU_SUB switch
  U13 pin 13(4B) ← ALU_SUB switch

XOR A-input ← IBUS (DIP switch #1 = operand):
  U12 pin 1 (1A) ← IBUS0 (DIP bit 0)
  U12 pin 4 (2A) ← IBUS1 (DIP bit 1)
  U12 pin 9 (3A) ← IBUS2 (DIP bit 2)
  U12 pin 12(4A) ← IBUS3 (DIP bit 3)
  U13 pin 1 (1A) ← IBUS4 (DIP bit 4)
  U13 pin 4 (2A) ← IBUS5 (DIP bit 5)
  U13 pin 9 (3A) ← IBUS6 (DIP bit 6)
  U13 pin 12(4A) ← IBUS7 (DIP bit 7)

XOR outputs → Adder B inputs:
  U12 pin 3 (1Y) → U10 pin 6 (B0)
  U12 pin 6 (2Y) → U10 pin 2 (B1)
  U12 pin 8 (3Y) → U10 pin 15(B2)
  U12 pin 11(4Y) → U10 pin 11(B3)
  U13 pin 3 (1Y) → U11 pin 6 (B0)
  U13 pin 6 (2Y) → U11 pin 2 (B1)
  U13 pin 8 (3Y) → U11 pin 15(B2)
  U13 pin 11(4Y) → U11 pin 11(B3)

Adder A inputs ← AC (DIP switch #2 = accumulator):
  U10 pin 5 (A0) ← AC0 (DIP bit 0)
  U10 pin 3 (A1) ← AC1 (DIP bit 1)
  U10 pin 14(A2) ← AC2 (DIP bit 2)
  U10 pin 12(A3) ← AC3 (DIP bit 3)
  U11 pin 5 (A0) ← AC4 (DIP bit 4)
  U11 pin 3 (A1) ← AC5 (DIP bit 5)
  U11 pin 14(A2) ← AC6 (DIP bit 6)
  U11 pin 12(A3) ← AC7 (DIP bit 7)

Adder Carry:
  U10 pin 7 (Cin) ← ALU_SUB switch (1 สำหรับ SUB, 0 สำหรับ ADD)
  U10 pin 9 (Cout) → U11 pin 7 (Cin)   [cascade]
  U11 pin 9 (Cout) → LED แดง (carry out) → 330Ω → GND

Adder SUM outputs → LED (ผลลัพธ์):
  U10 pin 4 (S0) → 330Ω → LED → GND (SUM0)
  U10 pin 1 (S1) → 330Ω → LED → GND (SUM1)
  U10 pin 13(S2) → 330Ω → LED → GND (SUM2)
  U10 pin 10(S3) → 330Ω → LED → GND (SUM3)
  U11 pin 4 (S0) → 330Ω → LED → GND (SUM4)
  U11 pin 1 (S1) → 330Ω → LED → GND (SUM5)
  U11 pin 13(S2) → 330Ω → LED → GND (SUM6)
  U11 pin 10(S3) → 330Ω → LED → GND (SUM7)
```

---

## ทดสอบ ✅

### Test 1: ADD (ALU_SUB = 0)

ตั้ง SUB switch = GND (OFF)

| AC | IBUS | SUM LED (bit7...bit0) | Cout | ค่า | ถูก? |
|:--:|:----:|:---------------------:|:----:|:---:|:----:|
| $03 | $05 | ○○○○●○○○ | ○ | $08 | ☐ |
| $10 | $20 | ○○●●○○○○ | ○ | $30 | ☐ |
| $FF | $01 | ○○○○○○○○ | ● | $00+C | ☐ |
| $7F | $01 | ●○○○○○○○ | ○ | $80 | ☐ |

> 💡 **Test สุดท้าย ($7F + $01 = $80)**
>
> Carry = 0 (ไม่มี unsigned overflow)
> แต่ในมุมมอง signed: +127 + 1 = −128 (signed overflow!)
> RV8-GR ไม่มี overflow flag — ใช้ bit7 ดูแทนได้

### Test 2: SUB (ALU_SUB = 1)

ตั้ง SUB switch = VCC (ON)

| AC | IBUS | SUM LED | Cout | ค่า | Borrow? | ถูก? |
|:--:|:----:|:-------:|:----:|:---:|:-------:|:----:|
| $05 | $03 | ○○○○○○●○ | ● | $02 | ไม่ (A≥B) | ☐ |
| $10 | $10 | ○○○○○○○○ | ● | $00 | ไม่ (A=B) | ☐ |
| $03 | $05 | ●●●●●●●○ | ○ | $FE (−2) | มี (A<B) | ☐ |

### Test 3: B Inversion (ทดสอบ XOR gate)

ตั้ง AC = $00, สลับ SUB switch เพื่อดู XOR output ผ่าน adder:

| IBUS | SUB | XOR output | Result (AC=0 + XOR) | ถูก? |
|:----:|:---:|:----------:|:-------------------:|:----:|
| $AA | 0 | $AA (ผ่านตรง) | $AA | ☐ |
| $AA | 1 | $55 (กลับบิต) | $55 + 1 = $56 | ☐ |
| $FF | 0 | $FF | $FF | ☐ |
| $FF | 1 | $00 (กลับหมด) | $01 | ☐ |

> ⚠️ **Test 3 ทดสอบ "Operand Inversion" ไม่ใช่ XOR operation!**
>
> สิ่งที่เห็น: IBUS ถูกกลับบิตเมื่อ ALU_SUB=1 (เพื่อทำ SUB)
> XOR operation จริง (AC XOR IBUS) จะทำได้ใน Lab 08 เมื่อต่อ mux

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| ผลบวกผิด 1 | Cin ไม่ได้ต่อ GND (ADD) | เช็ค U10 pin 7 |
| ผลลบผิด 1 | Cin ไม่ได้ต่อ ALU_SUB | SUB ต้อง Cin=1 |
| bit 4-7 ผิดหมด | Cout ไม่ cascade | เช็ค U10-9 → U11-7 |
| XOR ไม่กลับบิต | B-input ไม่ถึง SUB | เช็คสาย switch → U12/U13 pin B |
| SUM ค้าง 0 | A/B ต่อสลับ | เช็ค pinout: A0=5, A1=3, A2=14, A3=12 |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR-V2/sim/sim_lab
python3 lab07_alu.py
```

---

## มองไปข้างหน้า: จาก Adder สู่ ALU เต็มรูปแบบ

Lab นี้สร้าง Adder/Subtractor สำเร็จแล้ว แต่ RV8-GR ต้องการ 3 operation:

| Operation | Control | ต้องการ |
|:---------:|:-------:|---------|
| ADD | SUB=0, XOR_MODE=0 | Adder ✅ (Lab นี้) |
| SUB | SUB=1, XOR_MODE=0 | Adder + Cin ✅ (Lab นี้) |
| XOR | XOR_MODE=1, MUX_SEL=1 | **B-mux + AC-mux** (Lab 08) |

Lab 08 จะเพิ่ม:
- **U19-U20 (B-input mux)**: เลือก XOR B-input = SUB (สำหรับ ADD/SUB) หรือ AC (สำหรับ XOR)
- **U17-U18 (AC input mux)**: เลือก AC ← Adder (ADD/SUB) หรือ XOR output (XOR/LI/LB)
- **U9 (Accumulator)**: เก็บผลลัพธ์

เมื่อรวมกันจะได้ **Full ALU** ที่ครบ ADD/SUB/XOR ตาม ISA ของ RV8-GR!

---

## สิ่งที่ได้

- ✅ Adder 8 บิตบวกถูก (พร้อม carry chain)
- ✅ SUB = กลับบิต + Cin=1 (two's complement subtraction)
- ✅ XOR gate ทำหน้าที่เป็น conditional inverter สำหรับ SUB
- ✅ เข้าใจ Carry/Borrow ในระบบ two's complement
- ✅ พร้อมสำหรับ Lab 08 ที่จะเพิ่ม AC + mux → Full ALU!

**ผ่านทุกข้อ → ไป Lab 08!** 🎉
