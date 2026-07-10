# RV8-GR — เข้าใจ CPU ทีละโมดูล (สำหรับน้อง ม.ต้น)

**สอน CPU 34 logic chips + ROM + RAM ตัวนี้ทีละขั้น ใช้ภาษาง่ายๆ ไม่รีบ อ่านแล้วเข้าใจว่าแต่ละโมดูลทำงานอย่างไร**

> 📌 เอกสารนี้คือ "แผนที่ความเข้าใจ" ไม่ใช่ wiring guide เต็ม.
> ใช้อ่านก่อนหรือระหว่างทำ lab เพื่อรู้ว่าแต่ละโมดูลทำอะไร.
> ตอนต่อวงจรจริงให้ใช้ `doc/labs/README.md`,
> `doc/build_plan/01_student_incremental_build_plan.md`, และ
> `doc/01_wiring_guide.md` เป็นแหล่งอ้างอิงขาและสายจริง.

---

## สารบัญ

1. CPU คืออะไร — ภาพรวม
2. จังหวะนาฬิกา T0/T1/T2 (U8)
3. Program Counter — ตัวชี้คำสั่ง (U1-U4)
4. Instruction Register — ตัวจำคำสั่ง (U5, U6)
5. DBUS, IBUS — ถนนข้อมูล (U7, U14)
6. ALU — เครื่องคำนวณ (U10-U13, U19-U20)
7. AC Mux — เลือกผลลัพธ์ (U17-U18)
8. Address Mux — เลือกที่อยู่ (U15-U16, U29-U30)
9. Z Flag — ธงศูนย์ (U21, U22)
10. Page Register — กระโดดไกล (U23)
11. Control Logic — สมองสั่งการ (U24-U28)
12. IRQ — ขัดจังหวะ (U31)
13. ROM กับ RAM — หน่วยความจำ
14. RV8-Bus — ถนนสู่โลกภายนอก (40-pin)
15. สรุป: ข้อมูลไหลอย่างไร
16. คำสั่งทั้งหมดของ RV8-GR (ISA)
17. CPU ทำงานจริง — ไล่ทีละ Clock
18. อ่านจบแล้ว ทำอะไรต่อ?

**ภาคผนวก:**
- ตารางสรุปชิปทั้ง 34 logic chips
- ก่อนอื่น... ต้องรู้อะไรบ้าง? (ศัพท์พื้นฐาน)
- ภาคพิเศษ: ทำไมเลือกชิปตัวนี้? (design rationale)

---

## 1. CPU คืออะไร — ภาพรวม

CPU เหมือนสมองของคอมพิวเตอร์ มันทำ 3 สิ่ง ซ้ำไปเรื่อยๆ:

### ภาพรวมทั้ง CPU (จำภาพนี้ไว้ตลอดทั้งเล่ม!)

```
                    ┌─────────┐
        ┌──────────│   ROM   │ ← เก็บโปรแกรม
        │          └─────────┘
        │               ↕ DBUS (ถนนภายนอก)
        │          ┌─────────┐
        │          │   U7    │ ← สะพานเชื่อม
        │          └─────────┘
        │               ↕ IBUS (ถนนภายใน)
        │    ┌──────────┼──────────┐
        │    │          │          │
   ┌────┴──┐│    ┌─────┴────┐   ┌─┴───┐
   │  PC   ││    │   ALU    │   │ AC  │ ← ผลลัพธ์
   │(U1-U4)││    │(U10-U13) │   │(U9) │
   └───────┘│    └──────────┘   └─────┘
        ↑   │          ↑              │
        │   │    ┌─────┴────┐         │
   กระโดด  │    │  IR (U5) │ ← คำสั่ง │
        │   │    └──────────┘         ↓
        │   │                    ┌─────────┐
        │   └───────────────────→│   RAM   │ ← เก็บข้อมูล
        │                        └─────────┘
   Page Reg (U23)
```

### Fetch → Fetch → Execute (หัวใจของ CPU!)

CPU ตัวนี้ไม่มี "Decode" แยก เพราะ opcode = สัญญาณควบคุมโดยตรง!

ทุกคำสั่งใช้ 3 จังหวะ ลองดูตัวอย่าง `ADDI $05` (บวก 5):

| จังหวะ | ทำอะไร | เปรียบเทียบ |
|:------:|--------|-------------|
| **T0** (Fetch Control) | อ่านคำสั่งจาก ROM | หยิบสูตรอาหาร |
| **T1** (Fetch Operand) | อ่านตัวเลขเพิ่มเติม | อ่านส่วนผสม |
| **T2** (Execute) | ทำงาน! (บวก 5) | ลงมือทำ |

```
T0: PC ชี้ ROM → ได้ "$10" → IR จำไว้ (="บวก")
T1: PC ชี้ ROM → ได้ "$05" → IR จำไว้ (="5")
T2: ALU ทำ AC + 5 → AC = ผลลัพธ์ใหม่!
```

> 📌 **จำไว้**: CPU ทำ 3 ขั้นนี้ซ้ำไปเรื่อยๆ ไม่มีหยุด!
> ทุกโมดูลที่จะเรียนต่อไป ทำงานภายใน 3 จังหวะนี้ทั้งหมด

```
1. อ่านคำสั่ง (จาก ROM)
2. เข้าใจคำสั่ง (แปลเป็นสัญญาณ)
3. ทำตามคำสั่ง (คำนวณ, เก็บค่า, กระโดด)
```

CPU ตัวนี้ใช้ 3 จังหวะนาฬิกาต่อ 1 คำสั่ง:
- **T0**: อ่านคำสั่ง (control byte)
- **T1**: อ่านข้อมูลเพิ่มเติม (operand)
- **T2**: ทำงาน!

ทั้งหมดนี้ทำได้ด้วย 34 logic chips ไม่มี microcode ไม่มี lookup table.

---

## 2. จังหวะนาฬิกา T0/T1/T2 (U8)

**ทำไมต้องมีจังหวะ?**

ลองนึกภาพการทำขนมปัง:
1. หยิบแป้ง (T0)
2. ใส่ไส้ (T1)
3. ปิ้ง (T2)

CPU ก็เหมือนกัน — ทำทีละขั้น ขั้นละ 1 จังหวะนาฬิกา.

**ชิป U8 (74HC164)** สร้างจังหวะ:

```
CLK:  ⎽⎽⎽⎽╱‾‾‾‾╲⎽⎽⎽⎽╱‾‾‾‾╲⎽⎽⎽⎽╱‾‾‾‾╲⎽⎽⎽⎽╱‾‾‾‾╲⎽⎽⎽

T0:   ‾‾‾‾‾‾‾‾‾‾╲⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽╱‾‾‾‾‾‾‾‾‾‾
T1:   ⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽╱‾‾‾‾‾‾‾‾‾‾╲⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽
T2:   ⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽╱‾‾‾‾‾‾‾‾‾‾╲⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽⎽
        T0          T1          T2          T0 ...
```

มีบิตเดียวที่เป็น 1 วิ่งไป: Q0→Q1→Q2→Q0...

```
State Diagram (หัวใจ CPU):

    RESET → [T0] → [T1] → [T2] ─┐
              ↑                    │
              └────────────────────┘

ภายใน Shift Register:

    [1][0][0]  ← T0 active
         ↓ clock
    [0][1][0]  ← T1 active
         ↓ clock
    [0][0][1]  ← T2 active
         ↓ clock (feedback วนกลับ)
    [1][0][0]  ← T0 อีกรอบ!
```

> 📌 มีบิต "1" เพียงตัวเดียววิ่งวนในวงแหวน — เรียกว่า **one-hot encoding**
> ใน lab เราเรียกสถานะพร้อมเริ่มหลัง reset ว่า **T0**.
> รายละเอียดทางไฟฟ้าของ 74HC164 คือ `/CLR` เคลียร์ Q ทั้งหมดเป็น 0 ก่อน,
> แล้ววงจร feedback ทำให้ clock แรกเข้าสู่ T0 ที่ใช้งานได้.
> ดังนั้นเวลา build/debug ให้ดูตาราง lab เป็นหลัก: reset แล้ว single-step
> ต้องเห็น T0→T1→T2 วนสะอาด ไม่มีสอง phase ติดพร้อมกัน.

**ที่ 1 MHz (breadboard, official target)**: 3 clock = 1 คำสั่ง → **333K คำสั่ง/วินาที**
**ที่ 5 MHz (PCB only, experimental)**: → **1.67 ล้านคำสั่ง/วินาที!**

---

## 3. Program Counter — ตัวชี้คำสั่ง (U1-U4)

**ทำไมต้องมี PC?**

ROM เก็บคำสั่งไว้เป็นลำดับ เหมือนหนังสือ.
PC คือ "นิ้วชี้" ที่บอกว่าตอนนี้อ่านถึงหน้าไหน.

**ชิป**: U1-U4 (74HC161 × 4 ตัว = 16 บิต)

```
ทำงาน 3 แบบ:
1. นับขึ้น +1  (ตอน T0, T1 → อ่านคำสั่งถัดไป)
2. หยุดนับ     (ตอน T2 → ทำงาน ไม่ต้องอ่านเพิ่ม)
3. กระโดด     (ตอน jump → ใส่ค่าใหม่เข้า PC)
```

**ตัวอย่าง**:
```
PC = $0000 → อ่าน ROM ที่ $0000 (คำสั่ง LI $10)
PC = $0001 → อ่าน ROM ที่ $0001 (operand $10)
PC = $0002 → อ่าน ROM ที่ $0002 (คำสั่งถัดไป)
...
PC = $0020 ← J $20 สั่ง jump → PC กระโดดไปตรงนี้!
```

**ทำไม 16 บิต?**
- 16 บิต = address ได้ 65,536 ตำแหน่ง (64KB)
- ROM อยู่ที่ $0000-$7FFF (32KB)
- RAM อยู่ที่ $8000-$FFFF (32KB)

---

## 4. Instruction Register — ตัวจำคำสั่ง (U5, U6)

**ทำไมต้องจำคำสั่ง?**

CPU อ่านคำสั่งจาก ROM มา 2 byte:
- Byte 1 = "ทำอะไร" (control byte)
- Byte 2 = "ทำกับอะไร" (operand)

ต้องจำไว้เพื่อใช้ตอน T2 (execute).

**U5 (IR_HIGH)** — จำ control byte:
```
ตัวอย่าง: ADDI → control byte = $10 = 00010000
                                        │││││││└─ JMP=0
                                        ││││││└── BR=0
                                        │││││└─── STR=0
                                        ││││└──── SRC=0
                                        │││└───── AC_WR=1 ← เขียน AC!
                                        ││└────── MUX_SEL=0
                                        │└─────── XOR_MODE=0
                                        └──────── ALU_SUB=0
```

**U6 (IR_LOW)** — จำ operand:
```
ตัวอย่าง: ADDI $05 → operand = $05 = ค่าที่จะบวก
```

**จุดสำคัญ**: แต่ละบิตของ control byte ต่อสายตรงไปสั่ง hardware!
- ไม่มี Instruction Decoder ROM, ไม่มี Microcode
- บิต AC_WR=1 → สายไปสั่ง AC ให้ latch ค่าใหม่
- (ยังมี gate logic U24-U28 ช่วยสร้างสัญญาณซับซ้อน แต่ไม่ใช่ decoder table)

---

## 5. DBUS, IBUS — ถนนข้อมูล (U7, U14)

> 💡 **ยังไม่เข้าใจ Bus?** ไม่ต้องกังวล — ลองอ่านบท 6 (ALU) และ 7 (AC) ก่อนแล้วกลับมาอ่านบทนี้อีกครั้งก็ได้!
> Bus เป็นแค่ "ถนน" ที่เชื่อมทุกอย่างเข้าด้วยกัน

**2 ถนนข้อมูล:**

```
┌─────────────────────────────────────────────────┐
│  โลกภายนอก (ROM, RAM)                            │
│          ↕ DBUS (D0-D7)                          │
│      ┌───────┐                                   │
│      │  U7   │  ← Bus Buffer (สะพาน)             │
│      └───────┘                                   │
│          ↕ IBUS (IBUS0-IBUS7)                        │
│  โลกภายใน (ALU, registers)                       │
└─────────────────────────────────────────────────┘
```

**DBUS** = ถนนภายนอก (ต่อกับ ROM, RAM)
**IBUS** = ถนนภายใน (ต่อกับ ALU, IR, Page Reg)
**U7** = สะพานเชื่อม 2 ถนน (เปลี่ยนทิศได้)

**กฎสำคัญ: ทางเดินเดียว!**

IBUS มี 3 คนที่ส่งข้อมูลได้ แต่ **ทีละคนเท่านั้น**:

| ใคร | เมื่อไหร่ | ส่งอะไร |
|-----|----------|---------|
| U7 (buffer) | Fetch, หรือ อ่าน RAM | ข้อมูลจาก ROM/RAM |
| U34 (IRL buffer) | T2 + immediate mode | ค่า operand ตรงๆ |
| U14 (AC buf) | T2 + STORE | ค่า AC → เขียนลง RAM |

ถ้า 2 คนส่งพร้อมกัน = **bus conflict** = ชิปพัง!
Control logic ดูแลไม่ให้เกิดด้วยทิศทางของ U7 และ ROM /OE:

```
U7 /OE = BUF_OE_N
WR_DIR = NOT(/AC_BUF)
ROM /OE = WR_DIR
→ ถ้า STR=1 (STORE active): U14 ขับ IBUS, U7 ส่ง IBUS→DBUS, ROM ปิด output
```

---

## 6. ALU — เครื่องคำนวณ (U10-U13, U19-U20)

**ALU ทำอะไรได้?**
- **บวก** (ADD): AC + ค่า
- **ลบ** (SUB): AC - ค่า
- **XOR**: AC XOR ค่า

**เคล็ดลับ: ใช้ XOR gate ทำทั้ง 3 อย่าง!**

```
                    IBUS (ค่าที่จะคำนวณ)
                      │
              ┌───────┴───────┐
              │   U12-U13     │  ← XOR gates
              │   A=IBUS      │
              │   B=??? ←─────┼── U19-U20 (mux เลือก)
              └───────┬───────┘
                      │
              XOR output
                ╱          ╲
    ┌──────────┘            └──────────┐
    │ U10-U11 (Adder)                  │ U17-U18 (AC mux B)
    │ A = AC                           │ → ส่งตรงเข้า AC
    │ B = XOR output                   │   (สำหรับ LI, XOR)
    │ Cin = SUB bit                    │
    │ SUM = ผลบวก                      │
    └──────────────────────────────────┘
```

**3 โหมด:**

| คำสั่ง | XOR B-input | XOR ทำอะไร | ผลลัพธ์ |
|--------|-------------|-----------|---------|
| ADD | 0 ทุกบิต | ส่ง IBUS ผ่านตรง | AC + IBUS |
| SUB | 1 ทุกบิต | กลับบิต IBUS | AC + NOT(IBUS) + 1 = AC - IBUS |
| XOR | AC | คำนวณ XOR | AC XOR IBUS |

**ทำไมลบได้?**
```
ลบ = บวกกับจำนวนลบ
จำนวนลบ = กลับบิต + 1 (two's complement)
กลับบิต = XOR กับ 1111 1111
+1 = Cin=1 (ใส่ carry เข้า adder)
```

**ตัวอย่าง: 5 - 3 ทีละขั้น:**
```
5 = 00000101

ขั้น 1: เอา 3 มากลับบิต
  3 = 00000011
  กลับ = 11111100

ขั้น 2: +1
  11111100 + 1 = 11111101  ← นี่คือ "-3"!

ขั้น 3: บวก 5 + (-3)
  00000101
+ 11111101
-----------
  00000010  = 2 ✓ (5-3=2!)
```

> 📌 CPU ไม่มีวงจรลบจริงๆ! มันแค่กลับบิต+1 แล้วบวก — ได้คำตอบเหมือนกัน

---

## 7. AC Mux — เลือกผลลัพธ์ (U17-U18)

**ทำไมต้องเลือก?**

ALU ให้ผลลัพธ์ 2 แบบ:
- **Adder SUM**: สำหรับ ADD, SUB
- **XOR output**: สำหรับ LI, LB, XOR

Mux เลือกว่าจะส่งอันไหนเข้า AC:

```
MUX_SEL=0: Adder SUM → AC     (ADD, SUB, ADDI, SUBI)
MUX_SEL=1: XOR output → AC    (LI, LB, XORI, XOR)
```

**เคล็ดลับ LI (Load Immediate):**
```
LI $42: ต้องการ AC = $42
- IBUS = $42 (จาก IRL)
- XOR B = 0 (XOR_MODE=0, ALU_SUB=0)
- XOR output = $42 XOR 0 = $42 (ผ่านตรง!)
- MUX_SEL=1 → AC = XOR output = $42
```

ไม่ต้องมีสายตรงจาก IBUS เข้า AC — ประหยัดชิป!

---

## 8. Address Mux — เลือกที่อยู่ (U15-U16, U29-U30)

**ปัญหา**: CPU ต้องใช้ address bus 2 แบบ:
1. **Fetch**: ชี้ไป ROM ตาม PC (อ่านคำสั่ง)
2. **Data access**: ชี้ไป RAM/ROM ตาม operand (อ่าน/เขียนข้อมูล)

**Mux เลือก:**

```
/ADDR_MODE=1 (T0, T1): A[15:0] = PC          → อ่าน ROM/RAM ตาม PC
/ADDR_MODE=0 (data T2): A[7:0]  = IRL         → low byte จาก operand
                       A[15:8] = Data Page   → high byte จาก U32
```

**Data Page Register (U32):**
```
SETDP $90     → Data Page = $90
LB $05        → อ่าน RAM[$9005] (ไม่ใช่ $0005!)
SB $20        → เขียน RAM[$9020]

SETDP $00     → Data Page = $00
LB $00        → อ่าน ROM[$0000] (lookup table!)

SETDP $80     → กลับมาที่ registers ($8000-$80FF)
```

**ทำไมต้องมี Data Page?**
- Operand มีแค่ 8 บิต → เข้าถึงได้แค่ 256 ตำแหน่ง
- Data Page เพิ่ม high byte → เข้าถึงได้ทั้ง **64KB!**
- ไม่มี Data Page → ทำ BASIC หรือ game ไม่ได้ (256 bytes ไม่พอ!)

**Chip Select จาก A15:**
```
A15=0 → ROM ทำงาน (address $0000-$7FFF) — อ่านได้อย่างเดียวตอน CPU run
A15=1 → RAM ทำงาน (address $8000-$FFFF) — อ่านและเขียนได้
```

---

## 9. Z Flag — ธงศูนย์ (U21, U22)

**ทำไมต้องมี Z flag?**

เพื่อให้ CPU ตัดสินใจได้:
- BEQ: "ถ้าผลลัพธ์ = 0 → กระโดด"
- BNE: "ถ้าผลลัพธ์ ≠ 0 → กระโดด"

**วิธีทำงาน:**

```
U22 (74HC688): เปรียบเทียบ AC กับ $00
  → ถ้า AC = $00: ส่งสัญญาณ LOW

U21 (74HC74): เก็บผลลัพธ์
  → U22 LOW → /PR preset ทำให้ Z = 1 (ใช่! AC เป็นศูนย์)
  → U22 HIGH → preset ปล่อย และ ACC_CLK จะ clock ค่า 0 เข้า Z (ไม่ใช่ศูนย์)
```

> 📌 Z เปลี่ยนรอบเดียวกับ AC write: `ACC_CLK` clock ทั้ง AC และ Z.
> ถ้า AC ใหม่เป็น 0, U22 จะ preset Z เป็น 1 แบบ async หลัง comparator settle.
> ถ้า AC ใหม่ไม่เป็น 0, U21 จะเก็บ 0 จาก D input.
> BEQ/BNE จะดูค่า Z ตอน T2 ของคำสั่งถัดไป หลังค่า Z stable แล้ว.

**ตัวอย่าง:**
```
LI $05    → AC=$05 → Z=0 (ไม่ใช่ศูนย์)
SUBI $05  → AC=$00 → Z=1 (เป็นศูนย์!)
BEQ $20   → Z=1 → กระโดดไป $20!
```

---

## 10. Page Register — กระโดดไกล (U23)

**ปัญหา**: Operand มีแค่ 8 บิต → jump ได้แค่ 256 ตำแหน่ง!

**วิธีแก้**: ใช้ Page Register เป็น high byte:

```
SETPG $90     → Page Register = $90
J $00         → PC = {$90, $00} = $9000
```

ตอน jump: PC ใหม่ = {Page Register, Operand} = 16 บิต → jump ได้ทั้ง 64KB!

**ชิป U23 (74HC574)** — latch 8 บิต:
- SETPG: โหลด high byte จาก IBUS
- J/BEQ/BNE: ส่ง high byte ไป PC (U3-U4)

> 📌 **อย่าสับสน! มี Register 2 ตัวที่คล้ายกัน:**
>
> | Register | ชิป | ใช้กับ | ตั้งค่าด้วย |
> |----------|-----|--------|-------------|
> | Page Register (PG) | U23 | **Jump** — กำหนด PC[15:8] | SETPG |
> | Data Page (DP) | U32 | **Load/Store** — กำหนด address[15:8] | SETDP |
>
> ```
> Jump:   PC = {PG, operand}      ← SETPG กำหนด
> Data:   addr = {DP, operand}    ← SETDP กำหนด
> ```

---

## 11. Control Logic — สมองสั่งการ (U24-U28)

**ชิปเหล่านี้ทำอะไร?**

สร้าง control signals ที่ซับซ้อนจากสัญญาณง่ายๆ:

```
U24 (Inverters): กลับสัญญาณ
  - NOT(T0), NOT(T1) → feedback ให้ ring counter
  - NOT(A15) → RAM /CE (RAM active when A15=1)
  - NOT(JUMP), NOT(AC_WR) → ใช้ในเงื่อนไข

U25 (OR gates): รวมสัญญาณ
  - ADDR_REQ = SRC OR STR (ถ้ามีอย่างใดอย่างหนึ่ง = data access)
  - PC_INC = T0 OR T1 (นับ PC ตอน fetch)

U26 (NAND gates): ป้องกัน + สั่ง
  - /IRL_OE: เปิด U34 ขับ IBUS (immediate mode)
  - /AC_BUF: เปิด U14 + สั่ง RAM write
  - /PC_LD: สั่ง PC load (jump!)

U27 (NAND gates): ตัดสินใจ jump
  - Branch taken? → ดู Z flag
  - PC load? → jump OR branch taken

U28 (XOR gates): สัญญาณพิเศษ
  - Z_match: ใช้ SUB bit กลับเงื่อนไข (BEQ vs BNE)
  - /T2: ใช้กับ Page Register timing
  - WR_DIR: ทิศของ U7 bus buffer
```

---

## 12. IRQ — ขัดจังหวะ (U31)

**IRQ คืออะไร?**

เหมือนมีคนมาเคาะประตูตอนเราทำงานอยู่:
1. คนมาเคาะ → กริ่งดัง (IRQ latch จับสัญญาณ)
2. เราทำงานอยู่ → ลองหันไปดูเป็นระยะ (software poll)
3. เห็นกริ่งดัง → หยุดทำงานเดิม ไปเปิดประตู (branch to handler)
4. จัดการเสร็จ → กลับมาทำต่อ

**ชิป U31 (74HC74)** — 2 flip-flops:
- **IE flag**: เปิดการรับ interrupt ด้วย EI; reset ปิด (DI ไม่มีผลใน v1.0)
- **IRQ latch**: จำว่ามี interrupt เข้ามา

**v1.0: Polling Model (ไม่มี hardware vector)**
```
1. ขา /IRQ ถูกดึง LOW แล้วปล่อยกลับ HIGH → rising edge ทำให้ IRQ_FF = 1
2. Main loop ตรวจ IRQ_FF ถ้ามีอุปกรณ์ /SLOT ภายนอก expose latch นี้ให้ software อ่าน
3. ถ้า IRQ_FF=1 AND IE=1:
   - Software branch ไป handler
   - จัดการ event ตาม software policy
   - อย่าเรียก EI ซ้ำ เว้นแต่ software ต้องการให้ IE=1
```

> ⚠️ **v1.0: IRQ_FF เคลียร์ได้โดย /RST เท่านั้น!**
> DI ไม่มีผลใน v1.0 — IE และ IRQ_FF ยังค้างจนกว่าจะ reset
> สำหรับ game/BASIC: poll input โดยตรงผ่าน I/O slot แทนการพึ่ง IRQ_FF re-arm
> v1.1 fix: Route /SLOT2 write → U31 /CLR2 (software clear via `SB $20`, +0 chips)

**อนาคต**: Hardware vector → PC กระโดดไป $FF00 อัตโนมัติ ยังไม่ frozen และไม่ใช่ +2 ชิปง่ายๆ

**คำสั่ง:**
```
EI ($08): เปิดรับ interrupt
DI ($48): ไม่มีผลกับ hardware v1.0
```

---

## 13. ROM กับ RAM — หน่วยความจำ

**ROM** (AT28C256) — เก็บโปรแกรม:
- ใส่คำสั่งเข้าไปด้วย Programmer board
- CPU อ่านอย่างเดียว (ตอน run)
- อยู่ที่ $0000-$7FFF

**RAM** (62256) — เก็บข้อมูลชั่วคราว:
- Registers ($8000-$8007): เหมือนกระเป๋ากางเกง 8 ใบ
- Data ($8008-$FEFF): เก็บข้อมูลทั่วไป
- อ่านและเขียนได้
- อยู่ที่ $8000-$FFFF

### ทำไม Register อยู่ใน RAM?

CPU ปกติ (เช่น Z80) มี register อยู่ในชิป CPU เลย:
```
A, B, C, D, E, H, L ← อยู่ข้างใน CPU
```

แต่ RV8-GR ประหยัดชิป → เก็บ register ไว้ใน RAM แทน:
```
$8000 = R0 (general purpose)
$8001 = R1
$8002 = R2
...
$8007 = R7
```

**ตัวอย่าง: R2 = R0 + R1**
```asm
LB $00      ; AC = R0 (อ่าน RAM[$8000])
ADD $01     ; AC = AC + R1 (บวกกับ RAM[$8001])
SB $02      ; R2 = AC (เขียนลง RAM[$8002])
```

> 📌 ข้อดี: ประหยัดชิป 8 ตัว (ไม่ต้องมี register file)
> ข้อเสีย: ช้ากว่า hardware register 1 clock (ต้อง LB/SB)

**Memory Map ทั้งหมด:**
```
$0000-$7FFF  ROM (โปรแกรม, อ่านอย่างเดียว)
$8000-$FEFF  RAM (ข้อมูล, อ่าน+เขียน)
$FF00-$FF0F  RAM (available; future vector)
$FF10-$FF1F  I/O Slot 1 address ← reserved for external device
$FF20-$FF2F  I/O Slot 2 address ← reserved for external device
$FF30-$FFFF  RAM (เหลือใช้)
```

> 📌 $FF10-$FF2F เป็น address ที่ RV8-Bus ใช้เลือกอุปกรณ์ภายนอก.
> ถ้ายังไม่ได้ต่อ peripheral พื้นที่นี้ยังอ่าน/เขียน RAM บน CPU board ได้ตาม A15.
> ถ้าต่อ peripheral แล้ว ต้องออกแบบ /SLOT device ไม่ให้ขับ DBUS ชนกับ RAM.

**Chip Select:**
```
A15 = 0 → ROM active  (address $0000-$7FFF)
A15 = 1 → RAM active  (address $8000-$FFFF)
```

สำหรับ ROM/RAM บน CPU board สาย A15 เส้นเดียวตัดสินว่าเลือกชิปไหน.
ส่วน /SLOT1 และ /SLOT2 เป็นสัญญาณเลือกอุปกรณ์ภายนอกบน RV8-Bus.

---

## 14. RV8-Bus — ถนนสู่โลกภายนอก (40-pin)

**ทำไมต้องมี Bus?**

CPU 34 logic chips + ROM + RAM อยู่บน breadboard — แต่ต้องต่อกับ:
- Programmer board (flash ROM)
- Terminal (UART)
- จอ LCD, keyboard, timer (อนาคต)

RV8-Bus คือ **สายเชื่อม 40 เส้น** ที่ส่งทุกสัญญาณที่จำเป็นออกมา:

```
┌────────────────────────────────────────────┐
│          CPU Board (36 packages)              │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │     RV8-Bus (40-pin IDC socket)      │  │
│  └──┬───┬───┬───┬───┬───┬───┬───┬───┬──┘  │
└─────┼───┼───┼───┼───┼───┼───┼───┼───┼─────┘
      │   │   │   │   │   │   │   │   │
   A[15:0] D[7:0] CLK /WR /RD /IRQ /SLOT VCC GND
      │   │   │   │   │   │   │   │   │
┌─────┼───┼───┼───┼───┼───┼───┼───┼───┼─────┐
│  ┌──┴───┴───┴───┴───┴───┴───┴───┴───┴──┐  │
│  │     RV8-Bus (40-pin IDC plug)        │  │
│  └──────────────────────────────────────┘  │
│          Peripheral Board                  │
│  (Programmer, UART, LCD, Keyboard...)      │
└────────────────────────────────────────────┘
```

**สัญญาณสำคัญ:**

| กลุ่ม | สัญญาณ | ทำอะไร |
|-------|---------|--------|
| Address | A[15:0] | บอกตำแหน่ง (อ่าน/เขียนที่ไหน) |
| Data | D[7:0] | ข้อมูลที่ส่งไป-กลับ |
| Clock | CLK | จังหวะนาฬิกา |
| Control | /WR, /RD | อ่านหรือเขียน |
| Reset | /RST | รีเซ็ตระบบ |
| Interrupt | /IRQ | อุปกรณ์ขอความสนใจ |
| I/O Select | /SLOT1, /SLOT2 | เลือกอุปกรณ์ I/O |

**เปรียบเทียบกับ CPU จริง:**
- Z80 มี 40 ขา → A16 + D8 + control
- RV8-GR มี 40 pin bus → A16 + D8 + control
- **สัญญาณเหมือนกัน! แค่ CPU ข้างในเป็น 34 logic chips แทน 1 ชิป**

**I/O Slot Address:**
```
$FF10-$FF1F → /SLOT1 active (เช่น UART)
$FF20-$FF2F → /SLOT2 active (เช่น LCD)
```

ตัวอย่างเขียนไป /SLOT1:
```asm
SETDP $FF
LI $41
SB $10      ; address $FF10 → /SLOT1 active
```

ข้อมูลจะออกไปที่ RV8-Bus ระหว่าง STORE. Peripheral ต้องรับเฉพาะตอน /SLOT
ของตัวเอง active และต้องไม่ขับ DBUS พร้อมกับ RAM.

---

## 15. สรุป: ข้อมูลไหลอย่างไร

### ตัวอย่าง: ADDI $05 (AC = AC + 5)

```
┌─ T0: อ่านคำสั่ง ──────────────────────────────────────────┐
│  PC($0000) → Addr Mux → ABUS → ROM → DBUS → U7 → IBUS    │
│  → U5 latch control byte ($10)                             │
│  PC นับขึ้น → $0001                                         │
└─────────────────────────────────────────────────────────────┘

┌─ T1: อ่าน operand ─────────────────────────────────────────┐
│  PC($0001) → Addr Mux → ABUS → ROM → DBUS → U7 → IBUS    │
│  → U6 latch operand ($05)                                  │
│  PC นับขึ้น → $0002                                         │
└─────────────────────────────────────────────────────────────┘

┌─ T2: ทำงาน! ───────────────────────────────────────────────┐
│  U34 → IBUS ($05)                                           │
│  → U12 XOR (ผ่านตรง เพราะ ALU_SUB=0)                           │
│  → U10 Adder: AC($10) + $05 = $15                         │
│  → U17 Mux (เลือก Adder)                                   │
│  → U9 AC latch = $15 ✓                                     │
└─────────────────────────────────────────────────────────────┘
```

### ตัวอย่าง: SB $03 (RAM[$8003] = AC)

```
┌─ T2: เขียน RAM ────────────────────────────────────────────┐
│  Address: U6($03) → Addr Mux → ABUS = $8003                │
│  Data: U9(AC) → U14 buf → IBUS → U7(DIR=write) → DBUS     │
│  RAM /CE=0 (A15=1), RAM /WE=0 → เขียนค่า!                   │
└─────────────────────────────────────────────────────────────┘
```

### ตัวอย่าง: J $20 (กระโดดไป $0020)

```
┌─ T2: กระโดด ───────────────────────────────────────────────┐
│  JMP=1 → PC_LOAD_COND=1 → /PC_LD=0                        │
│  PC load: D[7:0] = IRL = $20                               │
│           D[15:8] = Page Reg = $00                          │
│  → PC = $0020 ✓                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 16. คำสั่งทั้งหมดของ RV8-GR (ISA)

CPU ตัวนี้มี 18 คำสั่ง:

| Opcode | คำสั่ง | ทำอะไร |
|:------:|--------|--------|
| $00 | NOP | ไม่ทำอะไร |
| $01 | J addr | กระโดดไป address |
| $02 | BEQ addr | ถ้า Z=1 → กระโดด |
| $82 | BNE addr | ถ้า Z=0 → กระโดด |
| $04 | SB addr | เขียน AC ลง RAM |
| $08 | EI | เปิดรับ interrupt |
| $48 | DI | ไม่มีผลกับ hardware v1.0 |
| $10 | ADDI imm | AC = AC + ค่า |
| $18 | ADD rs | AC = AC + RAM[rs] |
| $90 | SUBI imm | AC = AC - ค่า |
| $98 | SUB rs | AC = AC - RAM[rs] |
| $70 | XORI imm | AC = AC XOR ค่า |
| $78 | XOR rs | AC = AC XOR RAM[rs] |
| $30 | LI imm | AC = ค่า |
| $38 | LB rs | AC = RAM[rs] |
| $20 | SETPG imm | Page Register = ค่า (สำหรับ jump) |
| $28 | SETPG_R rs | Page Register = RAM[rs] |
| $40 | SETDP imm | Data Page = ค่า (สำหรับ load/store) |

---

## 17. CPU ทำงานจริง — ไล่ทีละ Clock

โปรแกรมตัวอย่าง: `LI $05 → ADDI $03 → SUBI $08`

```
ROM:
$0000: $30  (LI)
$0001: $05  (ค่า 5)
$0002: $10  (ADDI)
$0003: $03  (ค่า 3)
$0004: $90  (SUBI)
$0005: $08  (ค่า 8)
```

ไล่ทีละ clock:

```
Clock  Phase  PC    AC   Z   เกิดอะไร
-----  -----  ----  ---  --  ---------
1      T0     0000  ??   ?   อ่าน $30 → IR จำว่า "LI"
2      T1     0001  ??   ?   อ่าน $05 → IR จำว่า "5"
3      T2     0002  05   0   ทำ! AC = 5

4      T0     0002  05   0   อ่าน $10 → IR จำว่า "ADDI"
5      T1     0003  05   0   อ่าน $03 → IR จำว่า "3"
6      T2     0004  08   0   ทำ! AC = 5 + 3 = 8

7      T0     0004  08   0   อ่าน $90 → IR จำว่า "SUBI"
8      T1     0005  08   0   อ่าน $08 → IR จำว่า "8"
9      T2     0006  00   1   ทำ! AC = 8 - 8 = 0, Z=1!
```

> 📌 **สังเกต**: ทุกคำสั่งใช้ 3 clocks เสมอ. AC เปลี่ยนเฉพาะตอน T2.
> ถ้าต่อวงจรแล้วกดปุ่ม clock ทีละครั้ง จะเห็น LED เปลี่ยนตามตารางนี้เป๊ะ!

---

## 18. อ่านจบแล้ว ทำอะไรต่อ?

| ขั้นถัดไป | เอกสาร |
|-----------|--------|
| เริ่มต่อวงจรจริงแบบนักเรียน | `doc/labs/README.md` |
| แผนครู/พี่เลี้ยงสำหรับต่อทีละ stage | `doc/build_plan/01_student_incremental_build_plan.md` |
| ดูสายต่อทุกขา | `doc/01_wiring_guide.md` |
| ไล่ fault ตอนวงจรไม่ผ่าน | `doc/05_debug_plan.md` |
| เขียนโปรแกรมให้ CPU | `tools/rv8gr_asm.py` |
| ดูตัวอย่างโปรแกรม .asm | `programs/` |
| เทียบ trace กับ simulator | `doc/02_instruction_trace.md` |

### วิธีใช้เอกสารนี้ตอนเรียน

สำหรับแต่ละโมดูล ให้ตอบ 5 ข้อนี้ก่อนต่อวงจรถัดไป:

| คำถาม | ตัวอย่างคำตอบ |
|---|---|
| โมดูลนี้ทำหน้าที่อะไร? | PC ชี้ address ของคำสั่งถัดไป |
| ใช้ชิปอะไร? | U1-U4 = 74HC161 |
| รับ input สำคัญอะไร? | CLK, `/RST`, `PC_INC`, `/PC_LD` |
| ส่ง output อะไรต่อให้โมดูลอื่น? | `PC0..PC15` ไป address mux |
| ทดสอบผ่านต้องเห็นอะไร? | single-step แล้ว PC นับตอน T0/T1 และ load ตอน jump |

ถ้าตอบไม่ได้ ให้กลับไปอ่านโมดูลนั้นอีกครั้ง แล้วใช้ lab ที่ตรงกันทดสอบด้วย
manual clock ก่อนเพิ่มโมดูลใหม่.

> 💡 **Chapter Book (อนาคต)** — ถ้าจะทำเป็นหนังสือเต็ม:
>
> 0. รู้จักชิป TTL ทั้ง 34 ตัว (74HC161, 574, 245, 283, 86, 157...)
> 1. CPU Tour 60 วินาที — เดินชมโรงงานก่อน
> 2. CPU ทีละโมดูล (เอกสารนี้)
> 3. Clock-by-Clock Walkthrough — ไล่โปรแกรม 30+ clocks
> 4. Opcode-by-Opcode — ทุกคำสั่งทำงานอย่างไร
> 5. Wiring & Bring-up Lab — ต่อจริงทีละขั้น
> 6. Debugging Lab — พังแล้วหาเจอ
> 7. เขียน Assembler และโปรแกรมจริง
> 8. สร้างเกมบน RV8-GR

---

## ตารางสรุปชิปทั้ง 34 ตัว

| โมดูล | ชิป | จำนวน | หน้าที่หลัก |
|-------|------|:-----:|-------------|
| จังหวะ | U8 (74HC164) | 1 | สร้าง T0/T1/T2 |
| PC | U1-U4 (74HC161) | 4 | นับ/โหลด address 16 บิต |
| IR | U5-U6 (74HC574) | 2 | จำ control + operand |
| Bus | U7 (74HC245) | 1 | สะพาน DBUS↔IBUS |
| AC buf | U14 (74HC541) | 1 | ส่ง AC → IBUS |
| IRL buf | U34 (74HC541) | 1 | ส่ง operand → IBUS |
| Adder | U10-U11 (74HC283) | 2 | บวก 8 บิต |
| XOR | U12-U13 (74HC86) | 2 | XOR / กลับบิต |
| XOR mux | U19-U20 (74HC157) | 2 | เลือก XOR B-input |
| AC mux | U17-U18 (74HC157) | 2 | เลือก Adder/XOR → AC |
| Addr mux | U15-U16 (74HC157) | 2 | เลือก A[7:0] |
| Addr mux hi | U29-U30 (74HC157) | 2 | เลือก A[15:8] |
| AC | U9 (74HC574) | 1 | เก็บผลลัพธ์ |
| Z flag | U21 (74HC74) | 1 | จำว่า AC=0? |
| Zero det | U22 (74HC688) | 1 | ตรวจ AC=0 |
| Page Reg | U23 (74HC574) | 1 | High byte jump |
| Inverters | U24 (74HC04) | 1 | กลับสัญญาณ |
| OR gates | U25 (74HC32) | 1 | รวมเงื่อนไข |
| NAND | U26-U27 (74HC00) | 2 | สร้าง control |
| XOR misc | U28 (74HC86) | 1 | Z_match, WR_DIR |
| IRQ | U31 (74HC74) | 1 | IE + IRQ latch |
| Data Page | U32 (74HC574) | 1 | Data address high byte |
| SETDP decode | U33 (74HC21) | 1 | 4-input AND for DP_Load |
| **รวม** | | **34** | |

---

## ก่อนอื่น... ต้องรู้อะไรบ้าง?

ก่อนต่อวงจร ควรเข้าใจ:
- **HIGH = 1 = 5V**, **LOW = 0 = 0V**
- **Clock** = สัญญาณที่สลับ HIGH/LOW เป็นจังหวะ
- **Latch** = จำค่าไว้เมื่อได้สัญญาณ clock
- **Bus** = สายหลายเส้นที่ส่งข้อมูลพร้อมกัน (8 เส้น = 8 บิต)
- **Mux** = สวิตช์เลือกสัญญาณ

ถ้ายังไม่เข้าใจตรงไหน ถามพี่ได้เลย! 🙂

---

## ภาคพิเศษ: ทำไมเลือกชิปตัวนี้? ทำไมต่อแบบนี้?

### ทำไมใช้ 74HC164 เป็น ring counter?

**ทางเลือกอื่น**: ใช้ counter 74HC74 (2 flip-flop) + decode
**ที่เลือก**: 74HC164 เพราะ:
- มี serial input A,B (ใช้เป็น AND gate ฟรี!)
- ไม่ต้อง decode — Q0/Q1/Q2 เป็น one-hot output พร้อมใช้
- ใช้ชิปเดียว แทนที่จะใช้ 2-3 ชิป

### ทำไม PC ใช้ 74HC161 × 4?

**ทางเลือกอื่น**: ใช้ 74HC193 (up/down counter)
**ที่เลือก**: 74HC161 เพราะ:
- มี synchronous load (/LD) — โหลดค่า jump target ได้ทันที
- มี RCO (ripple carry out) — cascade ง่าย ต่อ ENT ตัวถัดไป
- มี ENP/ENT — หยุดนับได้ (ตอน T2)
- 4 บิต × 4 ตัว = 16 บิต พอดี

### ทำไมใช้ 74HC574 เป็น IR และ AC?

**ทางเลือกอื่น**: 74HC374, 74HC273
**ที่เลือก**: 74HC574 เพราะ:
- Edge-triggered (latch ที่ rising edge ของ CLK)
- มี /OE (ปิด output ได้) — ใน RV8-GR ส่วนใหญ่ผูก enabled ตลอด; การขับ IBUS ใช้ U14/U34 ซึ่งเป็น 74HC541 แยกต่างหาก
- Pinout เหมาะ: D1-D8 อยู่ด้านหนึ่ง, Q1-Q8 อยู่อีกด้าน → ต่อง่าย

### ทำไม XOR ทำหน้าที่ 3 อย่าง?

**ปัญหา**: ต้องการ ADD, SUB, XOR ใน ALU — ปกติต้องใช้ 3 วงจรแยก
**เคล็ดลับ**:
```
XOR(A, 0) = A        → ส่งค่าผ่านตรง (ใช้กับ ADD)
XOR(A, 1) = NOT(A)   → กลับบิต (ใช้กับ SUB)
XOR(A, B) = A^B      → คำนวณ XOR (ใช้กับ XOR instruction)
```
ใช้ mux (U19-U20) เลือก B-input → ชิป XOR ทำได้ทั้ง 3 หน้าที่!
ประหยัดชิปไป 4-6 ตัว เทียบกับ design ที่แยก logic unit ออก.

### ทำไม AC mux เลือกระหว่าง Adder กับ XOR output?

**ปัญหา**: LI $42 ต้องใส่ค่า $42 เข้า AC ตรงๆ ไม่ผ่าน adder
**วิธีแก้**: XOR(IBUS, 0) = IBUS → ส่ง IBUS ผ่านตรงเข้า AC ผ่านทาง XOR output!
- MUX_SEL=1 → AC ← XOR output = IBUS (เมื่อ XOR_MODE=0, ALU_SUB=0)
- ไม่ต้องมี path ตรงจาก IBUS เข้า AC → ประหยัด mux 1 ชุด

### ทำไม A15 ใช้เป็น chip select?

**ปัญหา**: ต้องแยก ROM กับ RAM → ปกติใช้ address decoder (74HC138)
**เคล็ดลับ**: ถ้าแบ่ง memory เป็น 2 ส่วนเท่าๆ กัน:
- Lower half ($0000-$7FFF) = ROM → ใช้ A15 ตรงๆ เป็น /CE
- Upper half ($8000-$FFFF) = RAM → ใช้ NOT(A15)
- ไม่ต้องมี decoder! ใช้แค่ inverter 1 gate (U24)

### ทำไม Data Access ใช้ Data Page Register?

**ปัญหา**: Operand มีแค่ 8 บิต → address ได้แค่ 256 ตำแหน่ง
**วิธีแก้**: เพิ่ม U32 (Data Page Register) เป็น high byte ของ data address

```
Data address = {Data Page (8 bit), Operand (8 bit)} = 16 bit = 64KB!
```

- SETDP $80 → data at $8000-$80FF (registers)
- SETDP $90 → data at $9000-$90FF (array page 1)
- SETDP $00 → data at $0000-$00FF (read ROM!)

**ทำไมไม่ใช้ GND?**
- ถ้าใส่ GND → เข้าถึงได้แค่ 256 bytes → ทำ BASIC/game ไม่ได้!
- Data Page Register ให้ full 64KB → เขียนโปรแกรมจริงได้

### ทำไม Z flag ใช้ async preset?

**ปัญหา**: ต้องรู้ว่า AC=0 หรือไม่ ก่อน BEQ/BNE ตัดสินใจ
**ทางเลือก**: synchronous (ใช้ D input + clock)
**ที่เลือก**: async preset เพราะ:
- U22 (688) ให้ /P=Q ที่ต่อ /PR ของ U21 ได้ตรงๆ
- ไม่ต้องมี inverter เพิ่ม (688 output = active-low = /PR input)
- ลด gate count 1 ตัว
- ค่า Z มีเวลา settle ตลอด T0/T1 ของคำสั่งถัดไป ก่อน BEQ/BNE ใช้ตอน T2

### ทำไม BNE ใช้ SUB bit?

**ปัญหา**: BEQ ($02) jump เมื่อ Z=1, BNE ($82) jump เมื่อ Z=0
**เคล็ดลับ**: ใช้ XOR gate!
```
Z_match = Z_flag XOR SUB_bit
BEQ: SUB=0 → Z_match = Z (jump เมื่อ Z=1)
BNE: SUB=1 → Z_match = NOT(Z) (jump เมื่อ Z=0)
```
ไม่ต้องมี BR_TYPE bit แยก — reuse SUB bit ที่มีอยู่แล้ว!
ประหยัดบิตใน control byte (ใช้แค่ 8 บิต ครอบคลุม 18 คำสั่ง)

### ทำไมต้องปิด ROM ตอน STORE?

**ปัญหา**: Opcode = Control Word → ทุก combination ของ 8 บิตทำงานได้
**อันตราย**: ถ้า STORE ไป page ROM, U7 อาจขับ DBUS พร้อมกับ ROM
**วิธีแก้**: `ROM /OE = WR_DIR`
- ถ้า STR=1 → U7 เขียน IBUS→DBUS และ ROM output ถูกปิด
- 0 ชิปเพิ่ม (ใช้ U28 gate หนึ่งตัวสร้าง `WR_DIR`)

### ทำไมใช้ 2 bus (DBUS + IBUS)?

**ปัญหา**: ROM/RAM อยู่นอก CPU, ALU อยู่ใน CPU
**ถ้าใช้ bus เดียว**: ต้อง tristate ทุกชิปที่ต่อ bus → ซับซ้อน, มี contention risk สูง
**2 bus + bridge (U7)**:
- DBUS: เชื่อม ROM, RAM, U7 และ RV8-Bus/peripheral อย่างมีเงื่อนไข
- IBUS: เชื่อม IR, ALU, AC, PG (ภายใน)
- U7 เป็นตัวกลาง — ควบคุมทิศ + enable/disable ได้

### สรุป: ปรัชญาการออกแบบ

| หลักการ | ตัวอย่าง |
|---------|---------|
| **Reuse** | XOR ทำ 3 หน้าที่ |
| **Direct control** | Opcode bit → hardware (no decoder) |
| **Minimal decode** | A15 = chip select (no 74HC138) |
| **Gate sharing** | SUB bit ใช้กับ BNE condition |
| **Bus isolation** | 2 buses + bridge ป้องกัน conflict |
| **Spare/gate budget** | ใช้ gate ที่มีอยู่ให้คุ้ม เช่น U28 ทำ `WR_DIR`, `Z_match`, `/T2`, `/XOR_MODE`; U25 gate 3 เท่านั้นที่ spare |

ทุกการตัดสินใจมุ่งไปที่: **ใช้ชิปน้อยที่สุด แต่ยังทำงานถูกต้อง**
