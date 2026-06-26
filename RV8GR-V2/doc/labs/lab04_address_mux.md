# Lab 04: Address Mux — เลือกที่อยู่ระหว่าง PC กับ IRL

**เป้าหมาย**: ต่อ U15-U16 + U29-U30 (74HC157 ×4) เพื่อเลือกว่า address bus จะมาจาก PC หรือ IRL

---

## ความรู้พื้นฐาน

CPU ต้องเข้าถึง 2 ที่อยู่:
- **ตอน fetch** (T0/T1): address = PC → อ่านคำสั่งจาก ROM
- **ตอน execute** (T2): address = IRL → อ่าน/เขียนข้อมูลจาก RAM

**ทำไมต้องมี Mux?**

```
ถ้าไม่มี Mux:
  PC ────→ ABUS (ตรง)

  ปัญหา: คำสั่ง LB $20 ต้องอ่าน RAM ที่ address $20
  แต่ ABUS ยังชี้ไปที่ PC อยู่ → อ่าน ROM แทน!

มี Mux:
  PC ────\
          >──→ ABUS    ← เลือกได้!
  IRL ───/

  T0,T1: ABUS = PC     → อ่านโปรแกรมจาก ROM
  T2:    ABUS = IRL+DP  → อ่าน/เขียนข้อมูลจาก RAM
```

74HC157 = Quad 2-to-1 Multiplexer (มี 4 ช่อง แต่ละช่องเลือก A หรือ B)
- S=0 → เอา input "A" (จาก PC)
- S=1 → เอา input "B" (จาก IRL)

ต้องใช้ 4 ตัว = 16 บิต = A[15:0] ครบ!

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC157 (U15, U16, U29, U30) | 4 |
| 2 | LED สีเขียว 3mm | 8 |
| 3 | 330Ω resistor | 8 |
| 4 | 100nF capacitor | 4 |
| 5 | Slide switch (หรือ jumper wire) | 1 |
| 6 | DIP switch 8 ตัว (จำลอง IRL) | 1 |

---

## วงจร

### Pinout: 74HC157

```
        ┌───U───┐
  SEL 1 │       │ 16 VCC
  1A  2 │       │ 15 /E
  1B  3 │ 157   │ 14 4A
  1Y  4 │       │ 13 4B
  2A  5 │       │ 12 4Y
  2B  6 │       │ 11 3A
  2Y  7 │       │ 10 3B
 GND  8 │       │  9 3Y
        └───────┘
```

### การต่อสาย

```
ทุกตัว (U15, U16, U29, U30):
  pin 16 (VCC) → 5V
  pin 8 (GND) → GND
  pin 15 (/E) → GND (enable ตลอด)
  pin 1 (SEL) → ADDR_MODE (switch: GND=PC, 5V=IRL)
  100nF คร่อม VCC-GND ทุกตัว

U15 — Address bits 0-3:
  pin 2 (1A) ← PC0 (U1-14 จาก Lab 03)
  pin 3 (1B) ← IRL0 (DIP switch bit 0 หรือ U6-19)
  pin 4 (1Y) → A0 (ออก address bus)

  pin 5 (2A) ← PC1 (U1-13)
  pin 6 (2B) ← IRL1 (DIP switch bit 1 หรือ U6-18)
  pin 7 (2Y) → A1

  pin 11 (3A) ← PC2 (U1-12)
  pin 10 (3B) ← IRL2 (DIP switch bit 2 หรือ U6-17)
  pin 9  (3Y) → A2

  pin 14 (4A) ← PC3 (U1-11)
  pin 13 (4B) ← IRL3 (DIP switch bit 3 หรือ U6-16)
  pin 12 (4Y) → A3

U16 — Address bits 4-7:
  pin 2 (1A) ← PC4 (U2-14)
  pin 3 (1B) ← IRL4 (DIP switch bit 4 หรือ U6-15)
  pin 4 (1Y) → A4

  pin 5 (2A) ← PC5 (U2-13)
  pin 6 (2B) ← IRL5 (DIP switch bit 5 หรือ U6-14)
  pin 7 (2Y) → A5

  pin 11 (3A) ← PC6 (U2-12)
  pin 10 (3B) ← IRL6 (DIP switch bit 6 หรือ U6-13)
  pin 9  (3Y) → A6

  pin 14 (4A) ← PC7 (U2-11)
  pin 13 (4B) ← IRL7 (DIP switch bit 7 หรือ U6-12)
  pin 12 (4Y) → A7

U29 — Address bits 8-11 (high):
  pin 2 (1A) ← PC8 (U3-14)
  pin 3 (1B) ← DP0 (GND สำหรับ lab นี้, ภายหลังต่อ U32-19)
  pin 4 (1Y) → A8

  pin 5 (2A) ← PC9 (U3-13)
  pin 6 (2B) ← DP1 (GND)
  pin 7 (2Y) → A9

  pin 11 (3A) ← PC10 (U3-12)
  pin 10 (3B) ← DP2 (GND)
  pin 9  (3Y) → A10

  pin 14 (4A) ← PC11 (U3-11)
  pin 13 (4B) ← DP3 (GND)
  pin 12 (4Y) → A11

U30 — Address bits 12-15:
  pin 2 (1A) ← PC12 (U4-14)
  pin 3 (1B) ← DP4 (GND)
  pin 4 (1Y) → A12

  pin 5 (2A) ← PC13 (U4-13)
  pin 6 (2B) ← DP5 (GND)
  pin 7 (2Y) → A13

  pin 11 (3A) ← PC14 (U4-12)
  pin 10 (3B) ← DP6 (GND)
  pin 9  (3Y) → A14

  pin 14 (4A) ← PC15 (U4-11)
  pin 13 (4B) ← DP7 (GND)
  pin 12 (4Y) → A15

LED (ดู A0-A7 output):
  U15 pin 4 (A0) → 330Ω → LED → GND
  U15 pin 7 (A1) → 330Ω → LED → GND
  U15 pin 9 (A2) → 330Ω → LED → GND
  U15 pin 12(A3) → 330Ω → LED → GND
  U16 pin 4 (A4) → 330Ω → LED → GND
  U16 pin 7 (A5) → 330Ω → LED → GND
  U16 pin 9 (A6) → 330Ω → LED → GND
  U16 pin 12(A7) → 330Ω → LED → GND
```

---

## ทดสอบ ✅

### ขั้นตอน

1. Reset PC → $00 (Lab 03)
2. ตั้ง DIP switch = $A5 (10100101)
3. สลับ ADDR_MODE switch ดูผลลัพธ์

### ตาราง LED (A7...A0)

| ADDR_MODE | แหล่ง | A7 | A6 | A5 | A4 | A3 | A2 | A1 | A0 | ค่า | ถูก? |
|:---------:|:-----:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:----:|
| 0 (GND) | PC=$00 | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | $00 | ☐ |
| 1 (5V) | IRL=$A5 | ● | ○ | ● | ○ | ○ | ● | ○ | ● | $A5 | ☐ |

4. กด Clock 3 ครั้ง (PC=$03) แล้วสลับ:

| ADDR_MODE | แหล่ง | A7 | A6 | A5 | A4 | A3 | A2 | A1 | A0 | ค่า | ถูก? |
|:---------:|:-----:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:----:|
| 0 (GND) | PC=$03 | ○ | ○ | ○ | ○ | ○ | ○ | ● | ● | $03 | ☐ |
| 1 (5V) | IRL=$A5 | ● | ○ | ● | ○ | ○ | ● | ○ | ● | $A5 | ☐ |

5. เปลี่ยน DIP switch = $FF (11111111):

| ADDR_MODE | A7 | A6 | A5 | A4 | A3 | A2 | A1 | A0 | ค่า | ถูก? |
|:---------:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:----:|
| 1 (5V) | ● | ● | ● | ● | ● | ● | ● | ● | $FF | ☐ |

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| LED ไม่เปลี่ยนเมื่อสลับ SEL | pin 1 (SEL) ไม่ได้ต่อ | เช็คสาย SEL ทุกตัว |
| บิตบางตัวค้าง | สาย A/B ต่อผิดขา | เช็ค pinout: 1A=2, 1B=3, 2A=5, 2B=6, 3A=11, 3B=10, 4A=14, 4B=13 |
| output ค้าง LOW ทั้งหมด | /E ไม่ได้ต่อ GND | เช็ค pin 15 ต่อ GND |
| A0-A3 ถูกแต่ A4-A7 ผิด | U16 ต่อผิด | เช็ค U16 แยกจาก U15 |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR-V2/sim/sim_lab
python3 lab04_address_mux.py
```

---

## สิ่งที่ได้

- ✅ Address mux เลือกระหว่าง PC กับ IRL ได้
- ✅ SEL=0 → A[15:0] มาจาก PC (สำหรับ fetch)
- ✅ SEL=1 → A[7:0] มาจาก IRL, A[15:8] มาจาก Data Page (สำหรับ data access)
- ✅ ในวงจรจริง ADDR_MODE = SRC OR STR (จาก IR bits)

> 📝 **หมายเหตุ: Data Page**
>
> Lab นี้ต่อ DP0-DP7 = GND ทำให้ address high byte = $00 เสมอ
> ใน CPU จริง มี Data Page Register (U32) ที่กำหนด A[15:8] ตอน access RAM:
> ```
> SETDP $90    → DP = $90
> LB $03       → address = $9003 (DP:IRL = $90:$03)
> ```
> จะได้เรียนใน Lab 12

---

## Challenge (ไม่บังคับ)

### Challenge A: ให้ Ring Counter ควบคุม Mux (สาธิต)

ลองต่อ:
```
SEL (pin 1 ทุกตัว) ← T2 (U8 pin 5 จาก Lab 02)
```

สังเกต:
- T0, T1: ABUS = PC (fetch)
- T2: ABUS = IRL (execute)

→ **Control Unit ควบคุม Address Mux โดยอัตโนมัติ!**

> ⚠️ **หมายเหตุ: CPU จริงใช้ ADDR_MODE ไม่ใช่ T2 ตรงๆ**
>
> RV8-GR จริง: `ADDR_MODE = SRC OR STR` (จาก U25)
> ไม่ใช่ทุก T2 จะเปลี่ยน address — เฉพาะคำสั่ง LB/SB/ADD/SUB/XOR เท่านั้น
> คำสั่ง LI, ADDI, SETPG ไม่มี SRC/STR → ABUS ยังเป็น PC แม้ใน T2
>
> Challenge นี้ใช้ T2 เพื่อสาธิตแนวคิดเท่านั้น

**ผ่านทุกข้อ → ไป Lab 05!** 🎉
