# RV8-GR — เข้าใจ CPU ทีละโมดูล (สำหรับน้อง ม.ต้น)

**สอน CPU 31 ชิปตัวนี้ทีละขั้น ใช้ภาษาง่ายๆ ไม่รีบ อ่านจบแล้วต่อวงจรได้เลย**

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

**ภาคผนวก:**
- ตารางสรุปชิปทั้ง 32 ตัว
- ก่อนอื่น... ต้องรู้อะไรบ้าง? (ศัพท์พื้นฐาน)
- ภาคพิเศษ: ทำไมเลือกชิปตัวนี้? (design rationale)

---

## 1. CPU คืออะไร — ภาพรวม

CPU เหมือนสมองของคอมพิวเตอร์ มันทำ 3 สิ่ง ซ้ำไปเรื่อยๆ:

```
1. อ่านคำสั่ง (จาก ROM)
2. เข้าใจคำสั่ง (แปลเป็นสัญญาณ)
3. ทำตามคำสั่ง (คำนวณ, เก็บค่า, กระโดด)
```

CPU ตัวนี้ใช้ 3 จังหวะนาฬิกาต่อ 1 คำสั่ง:
- **T0**: อ่านคำสั่ง (control byte)
- **T1**: อ่านข้อมูลเพิ่มเติม (operand)
- **T2**: ทำงาน!

ทั้งหมดนี้ทำได้ด้วยชิป 31 ตัว ไม่มี microcode ไม่มี lookup table.

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

**ที่ 10 MHz**: 3 clock = 1 คำสั่ง → **3.3 ล้านคำสั่ง/วินาที!**

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
PC = $8000 → อ่าน ROM ที่ $8000 (คำสั่ง LI $10)
PC = $8001 → อ่าน ROM ที่ $8001 (operand $10)
PC = $8002 → อ่าน ROM ที่ $8002 (คำสั่งถัดไป)
...
PC = $8020 ← J $20 สั่ง jump → PC กระโดดไปตรงนี้!
```

**ทำไม 16 บิต?**
- 16 บิต = address ได้ 65,536 ตำแหน่ง (64KB)
- ROM อยู่ที่ $8000-$FFFF (32KB)
- RAM อยู่ที่ $0000-$7FFF (32KB)

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
                                        ││└────── MUX=0
                                        │└─────── XOR=0
                                        └──────── SUB=0
```

**U6 (IR_LOW)** — จำ operand:
```
ตัวอย่าง: ADDI $05 → operand = $05 = ค่าที่จะบวก
```

**จุดสำคัญ**: แต่ละบิตของ control byte ต่อสายตรงไปสั่ง hardware!
- ไม่ต้องแปลง ไม่ต้อง decode
- บิต AC_WR=1 → สายไปสั่ง AC ให้ latch ค่าใหม่
- เรียบง่ายมาก!

---

## 5. DBUS, IBUS — ถนนข้อมูล (U7, U14)

**2 ถนนข้อมูล:**

```
┌─────────────────────────────────────────────────┐
│  โลกภายนอก (ROM, RAM)                            │
│          ↕ DBUS (D0-D7)                          │
│      ┌───────┐                                   │
│      │  U7   │  ← Bus Buffer (สะพาน)             │
│      └───────┘                                   │
│          ↕ IBUS (IB0-IB7)                        │
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
| U6 (IRL) | T2 + immediate mode | ค่า operand ตรงๆ |
| U14 (AC buf) | T2 + STORE | ค่า AC → เขียนลง RAM |

ถ้า 2 คนส่งพร้อมกัน = **bus conflict** = ชิปพัง!
Control logic ดูแลไม่ให้เกิด + มี **hardware guard** (U25 gate 3):

```
BUF_OE_SAFE = BUF_OE_N OR STR
→ ถ้า STR=1 (STORE active) → U7 ถูกปิดเสมอ
→ ป้องกันไม่ให้ U7 กับ U14 ขับ IBUS พร้อมกัน
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
- XOR B = 0 (XOR_MODE=0, SUB=0)
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
ADDR_MODE=0 (T0, T1): A[15:0] = PC          → อ่าน ROM/RAM ตาม PC
ADDR_MODE=1 (T2):     A[7:0]  = IRL         → low byte จาก operand
                       A[15:8] = Data Page   → high byte จาก U32
```

**Data Page Register (U32):**
```
SETDP $10     → Data Page = $10
LB $05        → อ่าน RAM[$1005] (ไม่ใช่ $0005!)
SB $20        → เขียน RAM[$1020]

SETDP $80     → Data Page = $80
LB $00        → อ่าน ROM[$8000] (lookup table!)

SETDP $00     → กลับมาที่ registers ($0000-$00FF)
```

**ทำไมต้องมี Data Page?**
- Operand มีแค่ 8 บิต → เข้าถึงได้แค่ 256 ตำแหน่ง
- Data Page เพิ่ม high byte → เข้าถึงได้ทั้ง **64KB!**
- ไม่มี Data Page → ทำ BASIC หรือ game ไม่ได้ (256 bytes ไม่พอ!)

**Chip Select จาก A15:**
```
A15=1 → ROM ทำงาน (address $8000+) — อ่านได้อย่างเดียว
A15=0 → RAM ทำงาน (address $0000+) — อ่านและเขียนได้
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
  → U22 LOW → preset Z = 1 (ใช่! AC เป็นศูนย์)
  → U22 HIGH → Z = 0 (ไม่ใช่)
```

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

---

## 11. Control Logic — สมองสั่งการ (U24-U28)

**ชิปเหล่านี้ทำอะไร?**

สร้าง control signals ที่ซับซ้อนจากสัญญาณง่ายๆ:

```
U24 (Inverters): กลับสัญญาณ
  - NOT(T0), NOT(T1) → feedback ให้ ring counter
  - NOT(A15) → ROM /CE
  - NOT(JUMP), NOT(AC_WR) → ใช้ในเงื่อนไข

U25 (OR gates): รวมสัญญาณ
  - ADDR_MODE = SRC OR STR (ถ้ามีอย่างใดอย่างหนึ่ง = data access)
  - PC_INC = T0 OR T1 (นับ PC ตอน fetch)

U26 (NAND gates): ป้องกัน + สั่ง
  - /IRL_OE: เปิด U6 ขับ IBUS (immediate mode)
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
1. ทำงานปัจจุบันให้จบ (จบคำสั่ง)
2. จำว่าทำถึงไหน (save PC)
3. ไปดูว่าใครเคาะ (jump ไป $FF00)
4. จัดการเสร็จ กลับมาทำต่อ (restore PC)

**ชิป U31 (74HC74)** — 2 flip-flops:
- **IE flag**: เปิด/ปิดการรับ interrupt (EI/DI)
- **IRQ latch**: จำว่ามี interrupt เข้ามา

**ลำดับการทำงาน:**
```
1. ขา /IRQ มีสัญญาณ (LOW) → IRQ_FF = 1
2. จบคำสั่งปัจจุบัน (T2 end)
3. ถ้า IRQ_FF=1 AND IE=1:
   - PC = $FF00 (IRQ vector)
   - IE = 0 (ปิดรับ interrupt ชั่วคราว)
```

**PC save (v1.0 = software)**:
```asm
; ก่อนเปิด interrupt:
LI lo(return_here)    ; save return address ด้วยตัวเอง
SB $0E
LI hi(return_here)
SB $0F
EI                    ; เปิด interrupt

; ... CPU ทำงาน ...
; ถ้ามี IRQ → กระโดดไป $FF00 ทันที
; ISR อ่าน RAM[$0E:$0F] เพื่อกลับมา
```

**คำสั่ง:**
```
EI ($08): เปิดรับ interrupt
DI ($48): ปิดรับ interrupt
```

---

## 13. ROM กับ RAM — หน่วยความจำ

**ROM** (AT28C256) — เก็บโปรแกรม:
- ใส่คำสั่งเข้าไปด้วย Programmer board
- CPU อ่านอย่างเดียว (ตอน run)
- อยู่ที่ $8000-$FFFF

**RAM** (62256) — เก็บข้อมูลชั่วคราว:
- Registers ($00-$07): เหมือนกระเป๋ากางเกง 8 ใบ
- Data ($08-$FF): เก็บข้อมูลทั่วไป
- อ่านและเขียนได้
- อยู่ที่ $0000-$7FFF

**Chip Select:**
```
A15 = 1 → ROM active  (address $8000+)
A15 = 0 → RAM active  (address $0000+)
```

สายเส้นเดียว A15 ตัดสินทุกอย่าง!

---

## 14. RV8-Bus — ถนนสู่โลกภายนอก (40-pin)

**ทำไมต้องมี Bus?**

CPU 31 ชิปอยู่บน breadboard — แต่ต้องต่อกับ:
- Programmer board (flash ROM)
- Terminal (UART)
- จอ LCD, keyboard, timer (อนาคต)

RV8-Bus คือ **สายเชื่อม 40 เส้น** ที่ส่งทุกสัญญาณที่จำเป็นออกมา:

```
┌────────────────────────────────────────────┐
│          CPU Board (32 chips)              │
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
- **สัญญาณเหมือนกัน! แค่ CPU ข้างในเป็น 31 ชิปแทน 1 ชิป**

**I/O Slot Address:**
```
$FF10-$FF1F → /SLOT1 active (เช่น UART)
$FF20-$FF2F → /SLOT2 active (เช่น LCD)
```

CPU เขียน SB $00 ที่ page $FF → ข้อมูลไปถึง peripheral ผ่าน bus!

---

## 15. สรุป: ข้อมูลไหลอย่างไร

### ตัวอย่าง: ADDI $05 (AC = AC + 5)

```
┌─ T0: อ่านคำสั่ง ──────────────────────────────────────────┐
│  PC($8000) → Addr Mux → ABUS → ROM → DBUS → U7 → IBUS    │
│  → U5 latch control byte ($10)                             │
│  PC นับขึ้น → $8001                                         │
└─────────────────────────────────────────────────────────────┘

┌─ T1: อ่าน operand ─────────────────────────────────────────┐
│  PC($8001) → Addr Mux → ABUS → ROM → DBUS → U7 → IBUS    │
│  → U6 latch operand ($05)                                  │
│  PC นับขึ้น → $8002                                         │
└─────────────────────────────────────────────────────────────┘

┌─ T2: ทำงาน! ───────────────────────────────────────────────┐
│  U6 → IBUS ($05)                                           │
│  → U12 XOR (ผ่านตรง เพราะ SUB=0)                           │
│  → U10 Adder: AC($10) + $05 = $15                         │
│  → U17 Mux (เลือก Adder)                                   │
│  → U9 AC latch = $15 ✓                                     │
└─────────────────────────────────────────────────────────────┘
```

### ตัวอย่าง: SB $03 (RAM[3] = AC)

```
┌─ T2: เขียน RAM ────────────────────────────────────────────┐
│  Address: U6($03) → Addr Mux → ABUS = $0003                │
│  Data: U9(AC) → U14 buf → IBUS → U7(DIR=write) → DBUS     │
│  RAM /CE=0 (A15=0), RAM /WE=0 → เขียนค่า!                   │
└─────────────────────────────────────────────────────────────┘
```

### ตัวอย่าง: J $20 (กระโดดไป $8020)

```
┌─ T2: กระโดด ───────────────────────────────────────────────┐
│  JMP=1 → PC_LOAD_COND=1 → /PC_LD=0                        │
│  PC load: D[7:0] = IRL = $20                               │
│           D[15:8] = Page Reg = $80                          │
│  → PC = $8020 ✓                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## ตารางสรุปชิปทั้ง 32 ตัว

| โมดูล | ชิป | จำนวน | หน้าที่หลัก |
|-------|------|:-----:|-------------|
| จังหวะ | U8 (74HC164) | 1 | สร้าง T0/T1/T2 |
| PC | U1-U4 (74HC161) | 4 | นับ/โหลด address 16 บิต |
| IR | U5-U6 (74HC574) | 2 | จำ control + operand |
| Bus | U7 (74HC245) | 1 | สะพาน DBUS↔IBUS |
| AC buf | U14 (74HC541) | 1 | ส่ง AC → IBUS |
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
| **รวม** | | **32** | |

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
- มี /OE (ปิด output ได้) — ใช้กับ U6 (IRL tristate)
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
- MUX_SEL=1 → AC ← XOR output = IBUS (เมื่อ XOR_MODE=0, SUB=0)
- ไม่ต้องมี path ตรงจาก IBUS เข้า AC → ประหยัด mux 1 ชุด

### ทำไม A15 ใช้เป็น chip select?

**ปัญหา**: ต้องแยก ROM กับ RAM → ปกติใช้ address decoder (74HC138)
**เคล็ดลับ**: ถ้าแบ่ง memory เป็น 2 ส่วนเท่าๆ กัน:
- Upper half ($8000+) = ROM → ใช้ A15 ตรงๆ
- Lower half ($0000+) = RAM → ใช้ NOT(A15)
- ไม่ต้องมี decoder! ใช้แค่ inverter 1 gate (U24)

### ทำไม Data Access ใช้ Data Page Register?

**ปัญหา**: Operand มีแค่ 8 บิต → address ได้แค่ 256 ตำแหน่ง
**วิธีแก้**: เพิ่ม U32 (Data Page Register) เป็น high byte ของ data address

```
Data address = {Data Page (8 bit), Operand (8 bit)} = 16 bit = 64KB!
```

- SETDP $00 → data at $0000-$00FF (registers)
- SETDP $10 → data at $1000-$10FF (array page 1)
- SETDP $80 → data at $8000-$80FF (read ROM!)

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
- Z settle ทันใน 200ns (2 clock cycles ก่อนถูก sample)

### ทำไม BNE ใช้ SUB bit?

**ปัญหา**: BEQ ($02) jump เมื่อ Z=1, BNE ($82) jump เมื่อ Z=0
**เคล็ดลับ**: ใช้ XOR gate!
```
Z_match = Z_flag XOR SUB_bit
BEQ: SUB=0 → Z_match = Z (jump เมื่อ Z=1)
BNE: SUB=1 → Z_match = NOT(Z) (jump เมื่อ Z=0)
```
ไม่ต้องมี BR_TYPE bit แยก — reuse SUB bit ที่มีอยู่แล้ว!
ประหยัดบิตใน control byte (ใช้แค่ 8 บิต ครอบคลุม 17 คำสั่ง)

### ทำไมต้องมี hardware guard?

**ปัญหา**: Opcode = Control Word → ทุก combination ของ 8 บิตทำงานได้
**อันตราย**: ถ้า SRC=1 AND STR=1 → U7 + U14 ขับ IBUS พร้อมกัน → bus fight!
**วิธีแก้**: `BUF_OE_SAFE = BUF_OE_N OR STR` (ใช้ spare gate U25)
- ถ้า STR=1 → U7 ปิดเสมอ → STORE ชนะ → ไม่มี bus fight
- 0 ชิปเพิ่ม (ใช้ gate ที่ว่างอยู่)

### ทำไมใช้ 2 bus (DBUS + IBUS)?

**ปัญหา**: ROM/RAM อยู่นอก CPU, ALU อยู่ใน CPU
**ถ้าใช้ bus เดียว**: ต้อง tristate ทุกชิปที่ต่อ bus → ซับซ้อน, มี contention risk สูง
**2 bus + bridge (U7)**:
- DBUS: เชื่อม ROM, RAM เท่านั้น (3 ตัว)
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
| **Spare gates** | U25 gate 3, U28 gate D → ใช้ทำ guard |

ทุกการตัดสินใจมุ่งไปที่: **ใช้ชิปน้อยที่สุด แต่ยังทำงานถูกต้อง**
