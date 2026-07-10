# Lab 10: Branch/Jump Logic — กระโดดตามเงื่อนไข

**เป้าหมาย**: ต่อ U24-U28 (gate logic) ให้ CPU กระโดด (J) และแยกทาง (BEQ/BNE) ได้

---

## ความรู้พื้นฐาน

Branch/Jump ต้องตอบคำถาม: "โหลด PC ใหม่ หรือ นับต่อ?"

| สัญญาณ | สูตร | หน้าที่ |
|--------|------|---------|
| Z_match | Z_flag XOR ALU_SUB | BEQ: match เมื่อ Z=1. BNE: match เมื่อ Z=0 |
| /BR_TAKEN | NAND(BR, Z_match) | LOW เมื่อ branch taken |
| PC_LOAD_COND | NAND(/JMP, /BR_TAKEN) | HIGH เมื่อ JMP หรือ branch taken |
| /PC_LD | NAND(T2, PC_LOAD_COND) | LOW → PC loads new value |
| PC_INC | T0 OR T1 | HIGH → PC counts up during fetch only |

**กฎ**: /PC_LD = LOW → U1-U4 โหลดค่าใหม่ (jump!)
         PC_INC = HIGH → U1-U4 นับขึ้น (fetch ปกติ)

### Z_match Truth Table (BEQ vs BNE)

| Z flag | ALU_SUB | Z_match | ความหมาย |
|:------:|:-------:|:-------:|----------|
| 0 | 0 | 0 | BEQ: AC≠0 → ไม่กระโดด |
| 1 | 0 | 1 | BEQ: AC=0 → **กระโดด!** |
| 0 | 1 | 1 | BNE: AC≠0 → **กระโดด!** |
| 1 | 1 | 0 | BNE: AC=0 → ไม่กระโดด |

> 💡 **เคล็ดลับ: XOR 1 gate แทน 2 opcodes!**
>
> BEQ ($02): SUB=0 → Z_match = Z (jump เมื่อ Z=1)
> BNE ($82): SUB=1 → Z_match = NOT(Z) (jump เมื่อ Z=0)
> ใช้ XOR gate ตัวเดียวแทน logic แยก 2 ชุด — ประหยัดชิปมาก!

### Jump Address = {PG, IRL}

เมื่อ /PC_LD = LOW จะโหลด:
```
PC[7:0]  ← IRL[7:0]  (U6 → U1-U2 D inputs)
PC[15:8] ← PG[7:0]   (U23 → U3-U4 D inputs)
```

ดังนั้น jump target = **{Page Register, Operand byte}** = 16-bit address เต็ม

ตัวอย่าง:
```
PG = $00 (for this lab, tie PC high-load inputs low until U23 exists)
J $06  → PC = $0006
BEQ $20 → PC = $0020 (ถ้า Z=1)
```

> ⚠️ **Lab นี้ยังไม่มี U23 Page Register**
>
> U23 จะมาต่อใน Lab 11. ก่อนถึง Lab 11 ให้ tie U3/U4 D inputs เป็น GND
> เพื่อให้ PC high byte = $00 ตอน jump/branch. อย่าปล่อยขา D ลอย.

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC04 (U24, inverters) — มีจาก Lab 02 | 0 (มีแล้ว) |
| 2 | 74HC32 (U25, OR gates) | 1 |
| 3 | 74HC00 (U26, NAND #1) | 1 |
| 4 | 74HC00 (U27, NAND #2) | 1 |
| 5 | 74HC86 (U28, XOR misc) | 1 |
| 6 | LED สีแดง 3mm | 1 |
| 7 | 330Ω resistor | 1 |
| 8 | 100nF capacitor | 4 |

---

## วงจร

### Pinout: 74HC00 (NAND), 74HC32 (OR), 74HC86 (XOR)

```
ทั้ง 3 ชิป มี pinout เหมือนกัน (quad 2-input gate):
        ┌───U───┐
  1A  1 │       │ 14 VCC
  1B  2 │       │ 13 4B
  1Y  3 │00/32/ │ 12 4A
  2A  4 │ 86    │ 11 4Y
  2B  5 │       │ 10 3B
  2Y  6 │       │  9 3A
 GND  7 │       │  8 3Y
        └───────┘
```

### การต่อสาย

```
U28 (XOR misc):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  Gate A: Z_match = Z_flag XOR ALU_SUB
    pin 1 ← Z_flag (U21-5)
    pin 2 ← ALU_SUB (U5-12)
    pin 3 → Z_match → U27-2

  Gate B: /T2 = T2 XOR VCC (= NOT T2)
    pin 4 ← T2 (U8-5)
    pin 5 ← VCC
    pin 6 → /T2 → U25-11

  Gate C: WR_DIR = NOT(/AC_BUF)
    pin 9 ← /AC_BUF (U26-8)
    pin 10← VCC
    pin 8 → WR_DIR → U7-1 และ ROM /OE

  Gate D: /XOR_MODE = NOT(XOR_MODE) — used by SETDP/EI decode (Lab 12+)
    pin 12← XOR_MODE (U5-13), pin 13← VCC, pin 11→ /XOR_MODE → U33-12

U24 (Inverters — เพิ่มจาก Lab 02):
  Gate 4: pin 9 ← JMP (U5-19)     pin 8 → /JMP → U27-4
  Gate 5: pin 11← AC_WR (U5-15)   pin 10→ /AC_WR → U27-10, U33-5
  Gate 6: pin 13← /IRL_OE (U26-3) pin 12→ BUF_OE_N → U7-19

U27 (NAND #2):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  Gate A: /BR_TAKEN = NAND(BR, Z_match)
    pin 1 ← BR (U5-18)
    pin 2 ← Z_match (U28-3)
    pin 3 → /BR_TAKEN → U27-5

  Gate B: PC_LOAD_COND = NAND(/JMP, /BR_TAKEN)
    pin 4 ← /JMP (U24-8)
    pin 5 ← /BR_TAKEN (U27-3)
    pin 6 → PC_LOAD_COND → U26-13

  Gate C: /PG_cond = NAND(MUX_SEL, /AC_WR)
    pin 9 ← MUX_SEL (U5-14)
    pin 10← /AC_WR (U24-10)
    pin 8 → /PG_cond → U25-12

  Gate D: ACC_CLK = NAND(T2, AC_WR)
    pin 12← T2 (U8-5)
    pin 13← AC_WR (U5-15)
    pin 11→ ACC_CLK → U9-11, U21-3

U26 (NAND #1):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  Gate A: /IRL_OE = NAND(T2, /ADDR_MODE)
    pin 1 ← T2 (U8-5)
    pin 2 ← /ADDR_MODE (U26-6)
    pin 3 → /IRL_OE → U34-1/19, U24-13

  Gate B: /ADDR_MODE = NAND(ADDR_REQ, T2)
    pin 4 ← ADDR_REQ (U25-3)
    pin 5 ← T2 (U8-5)
    pin 6 → /ADDR_MODE → U15/U16/U29/U30 pin 1, U26-2, U33-4

  Gate C: /AC_BUF = NAND(T2, STR)
    pin 9 ← T2 (U8-5)
    pin 10← STR (U5-17)
    pin 8 → /AC_BUF → U14-1/19, RAM /WE, U28-9

  Gate D: /PC_LD = NAND(T2, PC_LOAD_COND)
    pin 12← T2 (U8-5)
    pin 13← PC_LOAD_COND (U27-6)
    pin 11→ /PC_LD → U1-9, U2-9, U3-9, U4-9

U25 (OR gates):
  pin 14 (VCC) → 5V,  pin 7 (GND) → GND,  100nF คร่อม VCC-GND

  Gate 1: ADDR_REQ = SRC OR STR
    pin 1 ← SRC (U5-16)
    pin 2 ← STR (U5-17)
    pin 3 → ADDR_REQ → U26-4; U26-6 /ADDR_MODE → U15/U16/U29/U30 pin 1

  Gate 2: PC_INC = T0 OR T1
    pin 4 ← T0 (U8-3)
    pin 5 ← T1 (U8-4)
    pin 6 → PC_INC → U1-7/10, U2-7, U3-7, U4-7
```

> 💡 **PC_INC = T0 OR T1 → increment 2 ครั้งต่อคำสั่ง**
>
> T0: PC++ (ชี้ operand byte)
> T1: PC++ (ชี้คำสั่งถัดไป)
> T2: hold (ตัดสินใจ jump หรือไม่)
>
> นี่คือเหตุผลที่ **ทุกคำสั่ง RV8-GR = 2 bytes เสมอ**
> (fixed-width instruction — ไม่มีคำสั่ง 1-byte หรือ 3-byte)

> ⚠️ **XOR เป็น Inverter (Gate B, C)**
>
> U28 gate B: T2 XOR 1 = NOT(T2)
> U28 gate C: /AC_BUF XOR 1 = NOT(/AC_BUF)
> ใช้เป็น `WR_DIR`: HIGH ระหว่าง store เพื่อให้ U7 เขียน IBUS→DBUS
> และปิด ROM output ผ่าน ROM `/OE`
>
> ใช้ XOR gate เหลือจาก U28 แทน inverter ได้
> เพราะ U24 (74HC04) ใช้ครบ 6 gate แล้ว
> (เทคนิค: A XOR 1 = NOT A, A XOR 0 = A)

  Gate 3: spare
    pin 9 ← GND
    pin 10← GND
    pin 8 → NC

  Gate 4: PG_CLK = /T2 OR /PG_cond
    pin 11← /T2 (U28-6)
    pin 12← /PG_cond (U27-8)
    pin 13→ PG_CLK → U23-11

ต่อ PC:
  U1-U4 pin 9 (/LD) ← /PC_LD (U26-11)
  U1 pin 7 (ENP) ← PC_INC (U25-6)
  U1 pin 10 (ENT) ← PC_INC (U25-6)
  ก่อน Lab 11: U3/U4 D inputs → GND เพื่อให้ jump high byte = $00

LED (ดู /PC_LD):
  U26-11 → 330Ω → LED → VCC  [LED ติดเมื่อ /PC_LD=LOW = jump!]
```

---

## ทดสอบ ✅

### Test 1: J (unconditional jump) — JMP=1

Flash ROM test pattern:
```
$0000: $01  ; J (JMP=1)
$0001: $06  ; target: low byte = $06
```
เมื่อ execute: /PC_LD ต้อง LOW → PC โหลด $0006

| ขั้น | Phase | สัญญาณ | LED /PC_LD | PC | ถูก? |
|:----:|:-----:|--------|:----------:|:--:|:----:|
| 1 | T0 | fetch $01 → IR_H | ดับ (HIGH) | $0000 | ☐ |
| 2 | T1 | fetch $06 → IR_L | ดับ (HIGH) | $0001 | ☐ |
| 3 | T2 | JMP=1 → /PC_LD=LOW | ติด (LOW!) | loads | ☐ |
| 4 | T0 | PC=$0006 fetch | ดับ (HIGH) | $0006 | ☐ |

### Test 2: BEQ taken (Z=1, BR=1, SUB=0)

ก่อนทดสอบ: ทำให้ AC=0 (Z=1) ด้วย LI $00

Flash ROM:
```
$0000: $30  ; LI
$0001: $00  ; imm=0 → AC=0, Z=1
$0002: $02  ; BEQ (BR=1, ALU_SUB=0)
$0003: $08  ; target: $08
```

| ขั้น | Phase | Z | Z_match | /BR_TAKEN | /PC_LD | ถูก? |
|:----:|:-----:|:-:|:-------:|:---------:|:------:|:----:|
| 7 | T0 | 1 | — | — | HIGH | ☐ |
| 8 | T1 | 1 | — | — | HIGH | ☐ |
| 9 | T2 | 1 | 1 (Z XOR 0) | LOW | LOW (jump!) | ☐ |

### Test 3: BEQ not taken (Z=0, BR=1, SUB=0)

ก่อนทดสอบ: ทำให้ AC≠0 (Z=0) ด้วย LI $42

```
$0000: $30  ; LI
$0001: $42  ; imm=$42 → AC=$42, Z=0
$0002: $02  ; BEQ
$0003: $08  ; target (should NOT jump)
```

| ขั้น | Phase | Z | Z_match | /BR_TAKEN | /PC_LD | ถูก? |
|:----:|:-----:|:-:|:-------:|:---------:|:------:|:----:|
| 9 | T2 | 0 | 0 (Z XOR 0) | HIGH | HIGH (no jump) | ☐ |

### Test 4: BNE taken (Z=0, BR=1, SUB=1)

```
$0004: $82  ; BNE (SUB=1, BR=1) — AC≠0 → should jump
$0005: $0A  ; target: $0A
```

| Z | ALU_SUB | Z_match | /BR_TAKEN | /PC_LD | ถูก? |
|:-:|:-------:|:-------:|:---------:|:------:|:----:|
| 0 | 1 | 1 (0 XOR 1) | LOW | LOW (jump!) | ☐ |

### PC_LOAD vs PC_INC Priority Test
- [ ] Execute J $10 → PC ต้องเป็น $0010 (ไม่ใช่ $0011)
- [ ] ถ้า PC=$0011 → /PC_LD ชนะ PC_INC ไม่ได้ → ตรวจ 74HC161 /LD wiring

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| J ไม่ jump (PC นับต่อ) | /PC_LD ค้าง HIGH | เช็ค U26-11: T2 ต้อง HIGH + PC_LOAD_COND ต้อง HIGH |
| BEQ jump ทั้งๆ ที่ Z=0 | Z_match ผิด | เช็ค U28-1(Z), U28-2(SUB) → pin3 |
| BNE ไม่ jump เมื่อ Z=0 | ALU_SUB ไม่ HIGH | เช็ค U5-12 → U28-2 |
| PC โหลดค่าผิด | IRL ไม่ต่อ PC D-inputs | เช็ค U6 → U1/U2 D inputs |
| PC jump ทุก cycle | /PC_LD ค้าง LOW | เช็ค T2 gating (U26-12 ← T2) |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab10_branch_jump.py
```

---

## สิ่งที่ได้

- ✅ J (unconditional jump) โหลด PC = {PG, IRL}
- ✅ BEQ กระโดดเมื่อ Z=1 (AC=0)
- ✅ BNE กระโดดเมื่อ Z=0 (AC≠0)
- ✅ Branch not taken → PC นับปกติ (+2 per instruction)
- ✅ Control logic ครบ: PC_INC, /PC_LD, /ADDR_MODE, ACC_CLK, /IRL_OE, /AC_BUF

### CPU Milestone: สิ่งที่ทำได้แล้ว!

```
✓ Fetch (PC → ROM → IR)
✓ ALU (ADD, SUB, XOR)
✓ Accumulator (state)
✓ Z Flag (condition)
✓ Branch/Jump (control flow)
```

ตอนนี้สามารถเขียนโปรแกรมแบบ loop ได้แล้ว:
```
$0000: LI $05     ; AC = 5
$0002: SUBI $01   ; AC = AC - 1
$0004: BNE $02    ; ถ้า AC≠0 กลับไป $0002
$0006: J $06      ; หยุด (วน)
```

เหลือเพียง: **Page Register** (jump 64KB) + **RAM** (load/store) → CPU สมบูรณ์!

**ผ่านทุกข้อ → ไป Lab 11!** 🎉
