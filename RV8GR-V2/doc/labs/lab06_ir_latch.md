# Lab 06: IR Latch — จำคำสั่งที่อ่านมา

**เป้าหมาย**: ต่อ U5 (IR High = control byte) + U6 (IR Low = operand byte) จับค่าจาก IBUS ตอน T0/T1

---

## ความรู้พื้นฐาน

คำสั่งของ RV8-GR มี 2 ไบต์:
- **ไบต์ 1 (IR High, U5)**: control byte — บอกว่า "ทำอะไร"
  - bit7=SUB, bit6=XOR_MODE, bit5=MUX_SEL, bit4=AC_WR
  - bit3=SRC, bit2=STR, bit1=BR, bit0=JMP
- **ไบต์ 2 (IR Low, U6)**: operand — บอกว่า "กับค่าอะไร / ที่ไหน"
  - IRL[7:0] = ค่า immediate หรือ address

U5 จับค่าตอน T0↑ (rising edge ของ T0)
U6 จับค่าตอน T1↑ (rising edge ของ T1)

> 💡 **สถาปัตยกรรม Direct-Control**
>
> CPU ทั่วไปจะมี **Decoder** แปลง opcode → control signals
> แต่ RV8-GR ใช้วิธีต่อ IR bit เป็น control signal **โดยตรง**
> (เรียกว่า horizontal encoding / direct-control)
>
> ดังนั้น bit4 ของ IR High = สาย AC_WR จริง ๆ ไม่ต้องผ่าน logic ใด ๆ
> นี่คือเหตุผลที่ RV8-GR ไม่มีชิป Decoder — ประหยัดชิปและเข้าใจง่าย!

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC574 (U5, IR High) | 1 |
| 2 | 74HC574 (U6, IR Low) | 1 |
| 3 | LED สีแดง 3mm | 8 |
| 4 | LED สีเขียว 3mm | 8 |
| 5 | 330Ω resistor | 16 |
| 6 | 100nF capacitor | 2 |

---

## วงจร

### Pinout: 74HC574

```
        ┌───U───┐
  /OE 1 │       │ 20 VCC
  D1  2 │       │ 19 Q1
  D2  3 │       │ 18 Q2
  D3  4 │ 574   │ 17 Q3
  D4  5 │       │ 16 Q4
  D5  6 │       │ 15 Q5
  D6  7 │       │ 14 Q6
  D7  8 │       │ 13 Q7
  D8  9 │       │ 12 Q8
 GND 10 │       │ 11 CLK
        └───────┘
```

### การต่อสาย

```
U5 (IR High — control byte):
  pin 20 (VCC) → 5V
  pin 10 (GND) → GND
  pin 1  (/OE) → GND (output ตลอด)
  pin 11 (CLK) ← T0 (U8 pin 3 จาก Lab 02)
  100nF คร่อม VCC-GND

  D inputs ← IBUS (จาก U7 B-side, Lab 05):
    pin 2 (D1) ← IBUS0
    pin 3 (D2) ← IBUS1
    pin 4 (D3) ← IBUS2
    pin 5 (D4) ← IBUS3
    pin 6 (D5) ← IBUS4
    pin 7 (D6) ← IBUS5
    pin 8 (D7) ← IBUS6
    pin 9 (D8) ← IBUS7

  Q outputs → LED (สีแดง) + control signals:
    pin 19 (Q1) → JMP (bit0) → 330Ω → LED → GND
    pin 18 (Q2) → BR (bit1) → 330Ω → LED → GND
    pin 17 (Q3) → STR (bit2) → 330Ω → LED → GND
    pin 16 (Q4) → SRC (bit3) → 330Ω → LED → GND
    pin 15 (Q5) → AC_WR (bit4) → 330Ω → LED → GND
    pin 14 (Q6) → MUX_SEL (bit5) → 330Ω → LED → GND
    pin 13 (Q7) → XOR_MODE (bit6) → 330Ω → LED → GND
    pin 12 (Q8) → ALU_SUB (bit7) → 330Ω → LED → GND

U6 (IR Low — operand byte):
  pin 20 (VCC) → 5V
  pin 10 (GND) → GND
  pin 1  (/OE) → GND (สำหรับ lab นี้ ให้ output ตลอด, จริงๆ ต่อ /IRL_OE)
  pin 11 (CLK) ← T1 (U8 pin 4 จาก Lab 02)
  100nF คร่อม VCC-GND
```

> ⚠️ **หมายเหตุ: /OE ใน Lab vs CPU จริง**
>
> Lab นี้ต่อ /OE = GND (เปิด output ตลอด) เพื่อให้เห็น LED ได้ง่าย
> แต่ใน CPU จริง (ดู 02_wiring_guide) U6 /OE จะถูกควบคุมด้วย control logic
> เพื่อป้องกัน **Bus Contention** — หลาย chip ขับ IBUS พร้อมกัน
> เรื่องนี้จะได้เรียนเมื่อต่อ datapath ครบใน Lab ถัด ๆ ไป

```
  D inputs ← IBUS:
    pin 2 (D1) ← IBUS0
    pin 3 (D2) ← IBUS1
    pin 4 (D3) ← IBUS2
    pin 5 (D4) ← IBUS3
    pin 6 (D5) ← IBUS4
    pin 7 (D6) ← IBUS5
    pin 8 (D7) ← IBUS6
    pin 9 (D8) ← IBUS7

  Q outputs → LED (สีเขียว):
    pin 19 (Q1) → IRL0 → 330Ω → LED → GND
    pin 18 (Q2) → IRL1 → 330Ω → LED → GND
    pin 17 (Q3) → IRL2 → 330Ω → LED → GND
    pin 16 (Q4) → IRL3 → 330Ω → LED → GND
    pin 15 (Q5) → IRL4 → 330Ω → LED → GND
    pin 14 (Q6) → IRL5 → 330Ω → LED → GND
    pin 13 (Q7) → IRL6 → 330Ω → LED → GND
    pin 12 (Q8) → IRL7 → 330Ω → LED → GND
```

---

## เตรียม ROM

Flash ค่าทดสอบเข้า ROM:
```
$0000: $10  ← control byte (ADDI: AC_WR=1, bit4 on)
$0001: $05  ← operand byte (ค่า 5)
$0002: $90  ← control byte (SUBI: SUB + AC_WR, bit7+bit4)
$0003: $02  ← operand byte (ค่า 2)
$0004: $08  ← control byte (SRC: bit3 = EI)
$0005: $00  ← operand byte (address 0)
```

---

## ทดสอบ ✅

### ขั้นตอน

1. Reset ทุกอย่าง (PC=$0000, ring counter)
2. เริ่มกด Clock ตามจังหวะ T0→T1→T2→T0→...
3. ดู LED ว่า U5/U6 จับค่าถูก:

### ตาราง LED

**คำสั่งแรก (ADDI $05 = control $10, operand $05):**

| จังหวะ | เหตุการณ์ | U5 (LED แดง) | U6 (LED เขียว) | ถูก? |
|:------:|-----------|:------------:|:--------------:|:----:|
| T0↑ | U5 จับ $10 | ○○○●○○○○ ($10) | ไม่เปลี่ยน | ☐ |
| T1↑ | U6 จับ $05 | ○○○●○○○○ ($10) | ○○○○○●○● ($05) | ☐ |
| T2 | execute | ไม่เปลี่ยน | ไม่เปลี่ยน | ☐ |

**คำสั่งที่สอง (SUB $02 = control $90, operand $02):**

| จังหวะ | เหตุการณ์ | U5 (LED แดง) | U6 (LED เขียว) | ถูก? |
|:------:|-----------|:------------:|:--------------:|:----:|
| T0↑ | U5 จับ $90 | ●○○●○○○○ ($90) | ไม่เปลี่ยน | ☐ |
| T1↑ | U6 จับ $02 | ●○○●○○○○ ($90) | ○○○○○○●○ ($02) | ☐ |

**อ่าน LED: bit7(ซ้ายสุด)...bit0(ขวาสุด)**

### เช็ค control bits ทีละบิต:

| คำสั่ง | SUB | XOR | MUX | AC_WR | SRC | STR | BR | JMP | ถูก? |
|:------:|:---:|:---:|:---:|:-----:|:---:|:---:|:--:|:---:|:----:|
| $10 (ADDI) | ○ | ○ | ○ | ● | ○ | ○ | ○ | ○ | ☐ |
| $90 (SUBI) | ● | ○ | ○ | ● | ○ | ○ | ○ | ○ | ☐ |
| $08 (EI) | ○ | ○ | ○ | ○ | ● | ○ | ○ | ○ | ☐ |

### Bus Ownership Verification

Single-step ตรวจว่า IBUS driver active ทีละตัวเท่านั้น:

| Phase | IBUS driver | ตรวจ |
|:-----:|:-----------:|------|
| T0 | U7 (DBUS→IBUS) | U7-19=LOW, U6-1=HIGH, U14-1=HIGH |
| T1 | U7 (DBUS→IBUS) | (เหมือน T0) |
| T2 immediate | U6 (IRL→IBUS) | U6-1=LOW, U7-19=HIGH |
| T2 store | U14 (AC→IBUS), U7 writes IBUS→DBUS | U14-1=LOW, U7-19=LOW, U7-1=HIGH |

### Bus Float Test
- [ ] ปิด U7, U6, U14 ทั้งหมด (/OE=HIGH) → วัด IBUS ต้องไม่สุ่มค่า

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| U5 จับค่าตอน T1 (ไม่ใช่ T0) | CLK ต่อผิดเฟส | สลับ: U5-CLK ← T0, U6-CLK ← T1 |
| LED ค้างค่าเดิมตลอด | CLK ไม่ pulse | เช็คสาย T0/T1 จาก ring counter |
| ค่าผิดจากที่ flash | IBUS สายสลับ | เช็คลำดับ D1-D8 ↔ IBUS0-IBUS7 |
| U6 output ลอย | /OE ค้าง HIGH | เช็ค U6 pin 1 = GND |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR-V2/sim/sim_lab
python3 lab06_ir_latch.py
```

---

## มองไปข้างหน้า: T2 = Execute

ตอนนี้ T2 ยังไม่มีผลอะไร — LED ไม่เปลี่ยน เพราะยังไม่มี ALU / AC / Memory

แต่ลองจินตนาการ:

```
T0: Fetch opcode    → U5 จับ "ทำอะไร"
T1: Fetch operand   → U6 จับ "กับค่าอะไร"
T2: Execute         → ALU คำนวณ, AC เก็บผล, หรือ Jump ไปที่ใหม่
```

Lab 07 จะเพิ่ม **Accumulator (AC)** — ทำให้ CPU "ทำอะไร" กับคำสั่งได้เป็นครั้งแรก!

---

## Challenge 🏆

### Challenge 1: ทายก่อนกด

ถ้า ROM มี:
```
$0000: $90
$0001: $02
```

หลัง T0↑ แล้ว T1↑ — LED U5 และ U6 ควรเป็นอะไร?
เขียนคำตอบก่อน แล้วกดดู!

### Challenge 2: วาด Data Flow

วาดแผนภาพ data flow ด้วยตนเอง:
```
PC → Address Bus → ROM → IBUS → U5/U6
```
ระบุว่าแต่ละช่วง (T0, T1) ข้อมูลวิ่งไปไหน

### Challenge 3: สลับ T0/T1

ลองถอดสาย CLK ของ U5 กับ U6 สลับกัน:
- U5 CLK ← T1 (แทนที่จะเป็น T0)
- U6 CLK ← T0 (แทนที่จะเป็น T1)

สังเกตว่า opcode กับ operand **สลับตำแหน่ง** — LED แดงจะแสดง operand แทน!
นี่แสดงว่า timing ของ Fetch Cycle สำคัญมาก

---

## สิ่งที่ได้

- ✅ U5 จับ control byte ตอน T0 (บอก CPU ว่าทำอะไร)
- ✅ U6 จับ operand byte ตอน T1 (บอก CPU ว่าค่า/ที่อยู่อะไร)
- ✅ IR bits ไปควบคุมส่วนอื่นของ CPU โดยตรง!
- ✅ ตอนนี้ CPU อ่านคำสั่งจาก ROM ได้แล้ว (fetch complete!)

**ผ่านทุกข้อ → ไป Lab 07!** 🎉
