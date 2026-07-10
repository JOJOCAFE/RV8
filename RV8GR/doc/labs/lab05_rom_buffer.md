# Lab 05: ROM + Bus Buffer — อ่านข้อมูลจาก ROM

**เป้าหมาย**: ต่อ AT28C256 ROM + U7 (74HC245) อ่านค่าจาก ROM ผ่าน data bus

---

## ความรู้พื้นฐาน

ROM เก็บโปรแกรม (คำสั่ง CPU) ที่แต่ละตำแหน่ง เมื่อ CPU ส่ง address ไป ROM ก็ส่งข้อมูลกลับมาทาง data bus (DBUS)

U7 (74HC245) = สะพาน 2 ทิศทาง:
- **อ่าน** (DIR=0): DBUS → IBUS (ROM/RAM ส่งข้อมูลเข้า CPU)
- **เขียน** (DIR=1): IBUS → DBUS (CPU ส่งข้อมูลไป RAM)
- **/OE=HIGH**: ตัดการเชื่อมต่อ (ปิดสะพาน)

> ⚠️ **หมายเหตุสำหรับสร้างจริง: ทิศทาง 74HC245**
>
> Datasheet มาตรฐาน 74HC245: DIR=0 → B→A, DIR=1 → A→B
>
> ใน RV8-GR ต้องการ DIR=0 = DBUS→IBUS
> ดังนั้น**ต้องต่อ**: B-side (pins 18-11) = DBUS, A-side (pins 2-9) = IBUS
>
> ```
> pin 2-9   (A) ←→ IBUS (ฝั่ง CPU)
> pin 18-11 (B) ←→ DBUS (ฝั่ง Memory)
> ```
>
> แล้ว DIR=0 → B→A → DBUS→IBUS (อ่าน) ✅
> WR_DIR=1 → A→B → IBUS→DBUS (เขียน) ✅

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | AT28C256-70 (ROM, DIP-28) | 1 |
| 2 | 74HC245 (U7) | 1 |
| 3 | LED สีเหลือง 3mm | 8 |
| 4 | 330Ω resistor | 8 |
| 5 | 100nF capacitor | 2 |

---

## เตรียม ROM

โปรแกรม ROM ก่อนเสียบ (ใช้ Programmer):
```
ที่อยู่ $0000: $30    (LI opcode)
ที่อยู่ $0001: $42    (operand = $42)
ที่อยู่ $0002: $22    
ที่อยู่ $0003: $33    
ที่อยู่ $0004: $44    
ที่อยู่ $0005: $55    
ที่อยู่ $0006: $AA    
ที่อยู่ $0007: $FF    
```

Flash ROM ด้วย:
```bash
python3 ../Programmer/tools/rv8flash.py program test_bytes.bin --base 0x0000
```

---

## วงจร

### Pinout: AT28C256 (DIP-28)

```
        ┌───U───┐
  A14 1 │       │ 28 VCC
  A12 2 │       │ 27 /WE
   A7 3 │       │ 26 A13
   A6 4 │       │ 25 A8
   A5 5 │ 28C   │ 24 A9
   A4 6 │ 256   │ 23 A11
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

### Pinout: 74HC245 (U7)

```
        ┌───U───┐
  DIR 1 │       │ 20 VCC
  A1  2 │       │ 19 /OE
  A2  3 │       │ 18 B1
  A3  4 │ 245   │ 17 B2
  A4  5 │       │ 16 B3
  A5  6 │       │ 15 B4
  A6  7 │       │ 14 B5
  A7  8 │       │ 13 B6
  A8  9 │       │ 12 B7
 GND 10 │       │ 11 B8
        └───────┘
```

### การต่อสาย

```
ROM ไฟเลี้ยง:
  pin 28 (VCC) → 5V
  pin 14 (GND) → GND
  pin 27 (/WE) → 5V (ไม่เขียน ระหว่าง Lab 05 แบบ standalone)
  pin 22 (/OE) → GND (อ่านตลอด)
  pin 20 (/CE) ← A15 (ถ้ายังไม่มี ให้ต่อ GND = enable ตลอด)
  100nF คร่อม VCC-GND

หมายเหตุสำหรับบอร์ดจริง: ระหว่าง CPU runtime ให้ ROM pin 27 (`/WE`) inactive
(HIGH). Programmer เขียน ROM ได้เฉพาะตอน PROG/reset isolation ที่ CPU ถูก hold
reset และ Programmer เป็นเจ้าของ `/WE`.

ROM Address ← จาก ABUS (Lab 04):
  pin 10 (A0) ← A0 (U15 pin 4)
  pin 9  (A1) ← A1 (U15 pin 7)
  pin 8  (A2) ← A2 (U15 pin 9)
  pin 7  (A3) ← A3 (U15 pin 12)
  pin 6  (A4) ← A4 (U16 pin 4)
  pin 5  (A5) ← A5 (U16 pin 7)
  pin 4  (A6) ← A6 (U16 pin 9)
  pin 3  (A7) ← A7 (U16 pin 12)
  pin 25 (A8) ← A8 (U29 pin 4)
  pin 24 (A9) ← A9 (U29 pin 7)
  pin 21 (A10) ← A10 (U29 pin 9)
  pin 23 (A11) ← A11 (U29 pin 12)
  pin 2  (A12) ← A12 (U30 pin 4)
  pin 26 (A13) ← A13 (U30 pin 7)
  pin 1  (A14) ← A14 (U30 pin 9)
  (A15 ใช้เป็น chip select: /CE = A15)

ROM Data → DBUS:
  pin 11 (D0) → D0
  pin 12 (D1) → D1
  pin 13 (D2) → D2
  pin 15 (D3) → D3
  pin 16 (D4) → D4
  pin 17 (D5) → D5
  pin 18 (D6) → D6
  pin 19 (D7) → D7

U7 (74HC245) ไฟเลี้ยง:
  pin 20 (VCC) → 5V
  pin 10 (GND) → GND
  pin 1  (DIR) → GND (DIR=0 → B→A → DBUS→IBUS = อ่าน)
  pin 19 (/OE) → GND (enable ตลอดสำหรับ lab นี้)
  100nF คร่อม VCC-GND

U7 ด้าน A (ต่อ IBUS — ฝั่ง CPU):
  pin 2 (A1) → IBUS0
  pin 3 (A2) → IBUS1
  pin 4 (A3) → IBUS2
  pin 5 (A4) → IBUS3
  pin 6 (A5) → IBUS4
  pin 7 (A6) → IBUS5
  pin 8 (A7) → IBUS6
  pin 9 (A8) → IBUS7

U7 ด้าน B (ต่อ DBUS — ฝั่ง Memory):
  pin 18 (B1) ← D0
  pin 17 (B2) ← D1
  pin 16 (B3) ← D2
  pin 15 (B4) ← D3
  pin 14 (B5) ← D4
  pin 13 (B6) ← D5
  pin 12 (B7) ← D6
  pin 11 (B8) ← D7

LED (ดู IBUS จากฝั่ง A):
  pin 2 (A1=IBUS0) → 330Ω → LED → GND
  pin 3 (A2=IBUS1) → 330Ω → LED → GND
  pin 4 (A3=IBUS2) → 330Ω → LED → GND
  pin 5 (A4=IBUS3) → 330Ω → LED → GND
  pin 6 (A5=IBUS4) → 330Ω → LED → GND
  pin 7 (A6=IBUS5) → 330Ω → LED → GND
  pin 8 (A7=IBUS6) → 330Ω → LED → GND
  pin 9 (A8=IBUS7) → 330Ω → LED → GND
```

**สำคัญ**: PC reset = $0000 (bit15=0) ดังนั้น A15=0 → ROM /CE=0 (enabled) ✅

ถ้ายังไม่มี inverter (U24): ต่อ ROM /CE → GND แทน แล้ว **อย่าต่อ RAM** (ไม่งั้น bus fight)

---

## ทดสอบ ✅

### ขั้นตอน

1. Reset PC → $0000 (counter จาก Lab 03 reset เป็น $0000)
2. ตั้ง /ADDR_MODE = 1 (ให้ PC ขับ address)
3. กด Clock ดู LED:

### ตาราง LED (IBUS7...IBUS0 = data จาก ROM)

| กด Clock | Address | ROM data | IBUS7 | IBUS6 | IBUS5 | IBUS4 | IBUS3 | IBUS2 | IBUS1 | IBUS0 | ค่า | ถูก? |
|:--------:|:-------:|:--------:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:----:|
| Reset | $0000 | $30 | ○ | ○ | ● | ● | ○ | ○ | ○ | ○ | $30 | ☐ |
| 1 | $0001 | $42 | ○ | ● | ○ | ○ | ○ | ○ | ● | ○ | $42 | ☐ |
| 2 | $0002 | $22 | ○ | ○ | ● | ○ | ○ | ○ | ● | ○ | $22 | ☐ |
| 3 | $0003 | $33 | ○ | ○ | ● | ● | ○ | ○ | ● | ● | $33 | ☐ |
| 4 | $0004 | $44 | ○ | ● | ○ | ○ | ○ | ● | ○ | ○ | $44 | ☐ |
| 5 | $0005 | $55 | ○ | ● | ○ | ● | ○ | ● | ○ | ● | $55 | ☐ |
| 6 | $0006 | $AA | ● | ○ | ● | ○ | ● | ○ | ● | ○ | $AA | ☐ |
| 7 | $0007 | $FF | ● | ● | ● | ● | ● | ● | ● | ● | $FF | ☐ |
| extra | — | Force A15=1 (VCC) → ROM /CE=HIGH → DBUS ไม่ถูกขับ | — | — | — | — | — | — | — | — | ROM hi-Z | ☐ |

> 📌 **Chip Select Contract** (from Design ISA):
> ROM /CE = A15 (active when A15=0, address $0000-$7FFF)
> RAM /CE = /A15 (active when A15=1, address $8000-$FFFF)
>
> นี่คือ 1-bit address decoding — ใช้ A15 เส้นเดียวแบ่ง ROM 32KB / RAM 32KB

> 📌 **Bus Ownership**:
> ```
> ROM ───┐
>        ├── DBUS ──── U7 ──── IBUS ──── CPU
> RAM ───┘
> ```
> เวลาใดเวลาหนึ่ง มีเพียง ROM หรือ RAM เท่านั้นที่ขับ DBUS (ห้ามพร้อมกัน!)
> A15 ทำหน้าที่เป็น "ตำรวจจราจร" — เปิดทีละฝั่งเท่านั้น

> 📌 **Hi-Z คืออะไร?**
> เมื่อ ROM ถูกปิด (/CE=HIGH) → ขา data ของ ROM "ลอย" (Hi-Z = High Impedance)
> LED อาจดับ หมด หรือสุ่มค่า — เป็นเรื่องปกติ แสดงว่าไม่มีใครขับ DBUS

> 📌 **Lab นี้ PC นับทุก clock** (ยังไม่ใช้ Ring Counter ควบคุม)
> CPU จริง: PC+1 เฉพาะ T0,T1 (fetch) ไม่เพิ่มใน T2 (execute)

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| LED ดับหมด | ROM ไม่ output | เช็ค /CE=LOW, /OE=LOW |
| LED ค้างค่าเดิม | PC ไม่นับ | เช็ค PC (Lab 03) |
| ค่าผิดจาก ROM | address สายสลับ | เช็ค A0-A14 ต่อถูกขา |
| LED ไม่ตรงกับ ROM | U7 ต่อผิดทิศ | DIR=0 (B→A), B=DBUS, A=IBUS |
| ค่า $FF ตลอด | ROM ยังไม่ได้ flash | flash ROM ใหม่ |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab05_rom_fetch.py
```

---

## สิ่งที่ได้

- ✅ ROM ส่งข้อมูลออกมาตาม address ที่ PC ชี้
- ✅ U7 (245) ส่งข้อมูลจาก DBUS → IBUS
- ✅ PC นับขึ้น → อ่านค่าถัดไปจาก ROM ได้
- ✅ นี่คือ "instruction fetch path" — เส้นทางที่ CPU ใช้อ่านคำสั่ง!

> 📝 **หมายเหตุ: ยังไม่ใช่ Fetch สมบูรณ์**
>
> Lab นี้เห็น data จาก ROM ปรากฏบน IBUS ผ่าน LED
> แต่ยังไม่มี Instruction Register (U5/U6) มาจับค่าไว้
> ดังนั้นตอนนี้คือ "memory read path" — Lab 06 จะเพิ่ม IR ให้ fetch สมบูรณ์:
> ```
> T0: IR_H ← ROM[PC], PC++
> T1: IR_L ← ROM[PC], PC++
> T2: execute
> ```

> 📝 **เรื่อง Chip Select (A15)**
>
> Lab นี้ต่อ ROM /CE=GND (เปิดตลอด) เพื่อความง่าย
> ใน CPU จริง ใช้ A15 เป็น chip select:
> ```
> A15=0 ($0000-$7FFF): ROM เปิด, RAM ปิด
> A15=1 ($8000-$FFFF): RAM เปิด, ROM ปิด
> ```
> จะได้เรียนใน Lab 12 เมื่อต่อ RAM เข้ามา

**ผ่านทุกข้อ → ไป Lab 06!** 🎉
