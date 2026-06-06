# RV8-GR — เข้าใจ CPU ทีละโมดูล

**อธิบายการทำงานของ CPU ทั้ง 30 ชิป แยกเป็น 9 โมดูล**

---

## ภาพรวม: CPU ทำงานอย่างไร

CPU นี้ทำงาน 3 จังหวะต่อ 1 คำสั่ง:

    T0: อ่าน control byte จาก ROM → เก็บใน IR_HIGH
    T1: อ่าน operand จาก ROM → เก็บใน IR_LOW
    T2: ทำงานตาม control byte (คำนวณ, เก็บค่า, กระโดด)

ทุกอย่างขับเคลื่อนด้วย control byte 8 บิต — ไม่มี microcode, ไม่มี lookup table.
แต่ละบิตของ control byte ต่อตรงไปควบคุม hardware.

---

## โมดูล 1: นาฬิกาและจังหวะ (U8, U24 บางส่วน)

**หน้าที่**: สร้างสัญญาณ T0, T1, T2 สลับกันไปเรื่อยๆ

**ชิป**: U8 (74HC164 shift register) + U24 inverter 2 ตัว

**วิธีทำงาน**:
- U8 เป็น shift register 8 บิต ใช้เป็น ring counter
- มีบิตเดียวที่เป็น 1 วิ่งไปทีละตำแหน่ง: Q0→Q1→Q2→Q0...
- Q0=T0 (fetch control), Q1=T1 (fetch operand), Q2=T2 (execute)
- Feedback: serial input = NOT(Q0) AND NOT(Q1)
  - ใช้ U24 inverter 2 ตัว กลับ Q0, Q1
  - 74HC164 มี internal AND gate ที่ pin A,B → serial = NOT(Q0) AND NOT(Q1)
  - เมื่อ Q0=0 AND Q1=0 (คือตอน T2) → serial=1 → clock ถัดไป Q0=1 = T0 ใหม่

**ผลลัพธ์**: ทุก 3 clock ได้ 1 คำสั่ง → 3.3 MIPS ที่ 10 MHz

---

## โมดูล 2: Program Counter (U1-U4)

**หน้าที่**: นับที่อยู่ของคำสั่งถัดไปใน ROM/RAM

**ชิป**: U1-U4 (74HC161 × 4 ตัว = 16 บิต)

**วิธีทำงาน**:
- 74HC161 เป็น counter 4 บิต ต่อ cascade 4 ตัว = 16 บิต
- **นับขึ้น** (PC_INC=1): ตอน T0 และ T1 → อ่านคำสั่งทีละ byte
- **หยุดนับ** (PC_INC=0): ตอน T2 → ไม่เปลี่ยน address ระหว่าง execute
- **โหลดค่าใหม่** (/PC_LD=0): ตอน jump/branch → PC = {PageReg, IRL}
  - U1-U2 รับ IRL (low byte จาก operand)
  - U3-U4 รับ Page Register (high byte)
- **Reset** (/CLR=0): PC = $0000 → แต่ Page Register = $80 → jump ไป $8000

**ทำไมต้อง 16 บิต**: เพื่อ address ได้ทั้ง 64KB (ROM $8000+ และ RAM $0000+)

---

## โมดูล 3: Instruction Register (U5, U6)

**หน้าที่**: จำคำสั่งที่อ่านมาจาก ROM

**ชิป**: U5 (IR_HIGH = control byte), U6 (IR_LOW = operand)

**วิธีทำงาน**:
- U5 latch ค่าจาก IBUS ตอน T0 → ได้ control byte
- U6 latch ค่าจาก IBUS ตอน T1 → ได้ operand
- U5 Q outputs ต่อตรงไปเป็น control signals:
  - pin12 = ALU_SUB (บวกหรือลบ)
  - pin13 = XOR_MODE (ใช้ XOR instruction)
  - pin14 = MUX_SEL (เลือก adder หรือ XOR เข้า AC)
  - pin15 = AC_WR (เขียน AC หรือไม่)
  - pin16 = SOURCE_TYPE (ค่ามาจาก immediate หรือ RAM)
  - pin17 = STORE (เขียน AC ลง RAM)
  - pin18 = BRANCH (กระโดดแบบมีเงื่อนไข)
  - pin19 = JUMP (กระโดดไม่มีเงื่อนไข)

**จุดสำคัญ**: ไม่มี decoder! control byte บิตไหนเป็น 1 ก็สั่ง hardware ตรงๆ

---

## โมดูล 4: Bus Bridge และ IBUS (U7, U14)

**หน้าที่**: เชื่อม DBUS (ภายนอก) กับ IBUS (ภายใน) + ส่ง AC ออก IBUS

**ชิป**: U7 (74HC245 bidirectional buffer), U14 (74HC541 AC buffer)

**IBUS คืออะไร**:
- เส้นทางข้อมูลภายใน CPU 8 เส้น (IB0-IB7)
- มี 3 ตัวที่ขับ IBUS ได้ (ทีละตัวเท่านั้น!):
  1. **U7**: ส่งข้อมูลจาก ROM/RAM เข้ามา (ตอน fetch หรืออ่าน register)
  2. **U6**: ส่ง operand ตรงๆ (immediate mode)
  3. **U14**: ส่งค่า AC ออกไป (ตอน STORE เขียน RAM)

**U7 ทำงานอย่างไร**:
- DIR=0: อ่าน (DBUS → IBUS) — ใช้ตอน fetch และอ่าน RAM
- DIR=1: เขียน (IBUS → DBUS) — ใช้ตอน STORE
- /OE: ปิด U7 ตอนที่ U6 ขับ IBUS (ป้องกัน bus conflict)

**U14 ทำงานอย่างไร**:
- เปิดเฉพาะตอน T2+STORE → ส่งค่า AC ไป IBUS → U7 → DBUS → RAM

---

## โมดูล 5: ALU — เครื่องคำนวณ (U10-U13, U19-U20)

**หน้าที่**: บวก, ลบ, XOR

**ชิป**:
- U10-U11 (74HC283 × 2): adder 8 บิต
- U12-U13 (74HC86 × 2): XOR gates
- U19-U20 (74HC157 × 2): mux เลือก XOR B-input

**วิธีทำงาน**:

XOR chips (U12-U13) มี 2 input:
- **A-input** = IBUS (ค่าที่จะคำนวณ)
- **B-input** = จาก mux U19-U20:
  - XOR_MODE=0: B = ALU_SUB (0 หรือ 1 ทุกบิต)
  - XOR_MODE=1: B = AC (สำหรับ XOR instruction)

**3 โหมดการทำงาน**:

| โหมด | XOR B-input | XOR output | ผลลัพธ์ |
|------|-------------|------------|---------|
| ADD (SUB=0) | 0 ทุกบิต | = IBUS (ผ่านตรง) | AC + IBUS |
| SUB (SUB=1) | 1 ทุกบิต | = NOT(IBUS) | AC + NOT(IBUS) + 1 = AC - IBUS |
| XOR (XOR_MODE=1) | AC | = IBUS XOR AC | ใช้ตรง (bypass adder) |

**Adder** (U10-U11):
- A = AC (เสมอ)
- B = XOR output
- Cin = ALU_SUB (เพิ่ม 1 สำหรับ two's complement)
- ผลลัพธ์ SUM → AC input mux

---

## โมดูล 6: AC Input Mux — เลือกค่าเข้า AC (U17-U18)

**หน้าที่**: เลือกว่า AC จะรับค่าจากไหน

**ชิป**: U17-U18 (74HC157 × 2)

**วิธีทำงาน**:
- SEL = MUX_SEL (จาก control byte bit 5)
- **MUX_SEL=0** (A-input): Adder SUM → AC (สำหรับ ADD, SUB)
- **MUX_SEL=1** (B-input): XOR output → AC
  - ถ้า XOR_MODE=0: XOR output = IBUS (ผ่านตรง) → ใช้สำหรับ LI, MV a0,rs
  - ถ้า XOR_MODE=1: XOR output = AC XOR IBUS → ใช้สำหรับ XORI, XOR

**เคล็ดลับ**: XOR output ทำหน้าที่ 2 อย่าง:
1. ส่งค่า IBUS ตรงๆ เข้า AC (เมื่อ XOR_MODE=0, SUB=0)
2. คำนวณ XOR แล้วส่งเข้า AC (เมื่อ XOR_MODE=1)

ไม่ต้องมี buffer แยก — ประหยัดชิป!

---

## โมดูล 7: Address Mux — เลือกที่อยู่ (U15-U16, U29-U30)

**หน้าที่**: เลือกว่า address bus จะชี้ไปไหน

**ชิป**: U15-U16 (A0-A7), U29-U30 (A8-A15) — ทั้งหมด 74HC157

**วิธีทำงาน**:
- SEL = ADDR_MODE = SOURCE_TYPE OR STORE
- **ADDR_MODE=0** (fetch): address = PC → อ่าน ROM/RAM ตาม PC
- **ADDR_MODE=1** (data access): address = {$00, IRL} → อ่าน/เขียน RAM ที่ $00xx

**Chip select จาก A15**:
- A15=1 ($8000+): ROM /CE=0 → ROM ทำงาน
- A15=0 ($0000+): RAM /CE=0 → RAM ทำงาน

**ทำไม A8-A15 = GND ตอน data access**:
- Operand (IRL) มีแค่ 8 บิต → address ได้แค่ $00-$FF
- A8-A15 ต้องเป็น 0 เพื่อให้ชี้ RAM ที่ $0000-$00FF
- ถ้าต้องการ RAM มากกว่า 256 bytes → ใช้ bank switch (expansion board)

---

## โมดูล 8: Control Logic — สมองสั่งการ (U21-U28)

**หน้าที่**: สร้าง control signals ที่ซับซ้อนจาก IR_HIGH + state

**ชิป**:
- U21 (74HC74): เก็บ Z flag
- U22 (74HC688): ตรวจว่า AC = 0 หรือไม่
- U23 (74HC574): Page Register (high byte สำหรับ jump)
- U24 (74HC04): inverters 6 ตัว
- U25 (74HC32): OR gates 4 ตัว
- U26-U27 (74HC00 × 2): NAND gates 8 ตัว
- U28 (74HC86): XOR gates

### Z Flag (U21 + U22)

- U22 เปรียบเทียบ AC กับ 0 → ถ้าเท่ากัน /P=Q = LOW
- U21 เก็บผลลัพธ์: /P=Q=LOW → preset Z=1 (AC เป็นศูนย์)
- ใช้สำหรับ BEQ (jump ถ้า Z=1) และ BNE (jump ถ้า Z=0)

### Page Register (U23)

- เก็บ high byte ของ jump target (8 บิต)
- SETPG $xx: โหลดค่า immediate เข้า Page Register
- J $yy: PC = {PageReg, $yy} = 16-bit address
- ทำให้ jump ได้ทั้ง 64KB!

### Branch/Jump Logic (U26-U28)

ลำดับการตัดสินใจ:
```
1. Z_match = Z_flag XOR ALU_SUB        (U28)
   - BEQ: SUB=0 → Z_match = Z_flag (jump ถ้า Z=1)
   - BNE: SUB=1 → Z_match = NOT(Z_flag) (jump ถ้า Z=0)

2. /BR_TAKEN = NAND(BRANCH, Z_match)   (U27)
   - LOW เมื่อ branch taken

3. PC_LOAD_COND = NAND(/JUMP, /BR_TAKEN) (U27)
   - = JUMP OR BRANCH_TAKEN (De Morgan)
   - HIGH เมื่อต้อง jump

4. /PC_LD = NAND(T2, PC_LOAD_COND)     (U26)
   - LOW เมื่อ T2 + ต้อง jump → PC โหลดค่าใหม่
```

### IBUS Driver Control (U26, U24)

ป้องกัน bus conflict — มีตัวเดียวขับ IBUS ได้:
```
/IRL_OE = NAND(T2, /ADDR_MODE)         (U26)
  - LOW (U6 ขับ IBUS) เมื่อ: T2 + immediate mode

BUF_OE_N = NOT(/IRL_OE)                (U24)
  - U7 /OE: ปิด U7 เมื่อ U6 ขับ IBUS

/AC_BUF = NAND(T2, STORE)              (U26)
  - LOW (U14 ขับ IBUS) เมื่อ: T2 + STORE

WR_DIR = NOT(/AC_BUF)                  (U28)
  - U7 DIR: เปลี่ยนทิศเป็น write เฉพาะตอน STORE+T2
```

---

## สรุป: ข้อมูลไหลอย่างไร

### คำสั่ง ADDI $05 (AC = AC + 5):

```
T0: PC→mux→ABUS→ROM→DBUS→U7→IBUS→U5 latch (control=$10)
T1: PC→mux→ABUS→ROM→DBUS→U7→IBUS→U6 latch (operand=$05)
T2: U6→IBUS($05)→U12 XOR(pass)→U10 adder(AC+$05)→U17 mux(A)→U9 AC latch
```

### คำสั่ง MV $03,a0 (RAM[3] = AC):

```
T2: U6→mux→ABUS($0003), U14→IBUS(AC)→U7(DIR=1)→DBUS→RAM write
```

### คำสั่ง J $20 (jump to {PG,$20}):

```
T2: /PC_LD=0 → U1-U4 load: D[7:0]=IRL=$20, D[15:8]=PG=$80 → PC=$8020
```

---

## ตารางชิปทั้งหมด

| โมดูล | ชิป | จำนวน | หน้าที่ |
|-------|------|:-----:|---------|
| จังหวะ | U8, U24(2) | 1+ส่วน | ring counter T0/T1/T2 |
| PC | U1-U4 | 4 | นับ address 16 บิต |
| IR | U5, U6 | 2 | เก็บ control + operand |
| Bus | U7, U14 | 2 | เชื่อม DBUS↔IBUS, AC→IBUS |
| ALU | U10-U13, U19-U20 | 6 | บวก/ลบ/XOR |
| AC Mux | U17-U18 | 2 | เลือกค่าเข้า AC |
| Addr Mux | U15-U16, U29-U30 | 4 | เลือก address (PC/IRL) |
| Control | U21-U28 | 8 | Z flag, PG reg, logic gates |
| IRQ | U31 | 1 | IE + IRQ latch (74HC74) |
| **รวม** | | **30** | |
