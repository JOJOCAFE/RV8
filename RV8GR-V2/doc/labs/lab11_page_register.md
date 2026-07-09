# Lab 11: Page Register — กระโดด 16 บิต

**เป้าหมาย**: ต่อ U23 (74HC574, Page Register) ให้ CPU กำหนดหน้า (high byte) ของ address แล้วกระโดดไปได้ทั้ง 64KB

---

## ความรู้พื้นฐาน

- PC ของ RV8-GR = 16 บิต (A[15:0]) → address ได้ 64KB
- คำสั่ง J โหลดแค่ low byte (8 บิต) จาก IR_LOW → jump ได้แค่ภายใน 1 page (256 bytes)
- **Page Register (U23)** เก็บ high byte → ใช้เป็น PC[15:8] ตอน jump
- `SETPG imm` = ตั้งค่า page register ก่อน แล้ว `J addr` จะกระโดดไปหน้าอื่นได้

**PG_CLK** (clock U23) เกิดเมื่อ:
```
PG_CLK = /T2 OR /PG_cond
/PG_cond = NAND(MUX_SEL, /AC_WR)
→ PG loads เมื่อ: T2=1 AND MUX_SEL=1 AND AC_WR=0
→ นี่คือ SETPG instruction (opcode bit pattern: MUX=1, AC_WR=0, ไม่ write AC)
```

### Jump Address Formation (สูตรสำคัญ!)

```
PC_new = { PG[7:0], IRL[7:0] }
         ├────────┤ ├────────┤
          high byte   low byte
          (U3-U4)     (U1-U2)
```

สูตรนี้ใช้กับ **ทุก** คำสั่งที่โหลด PC:
- **J addr** → PC = {PG, addr} (unconditional)
- **BEQ addr** → PC = {PG, addr} (ถ้า Z=1)
- **BNE addr** → PC = {PG, addr} (ถ้า Z=0)

> ⚠️ **BEQ/BNE เป็น absolute address — ไม่ใช่ PC-relative!**
>
> `BEQ $20` หมายถึง "ถ้า Z=1 กระโดดไป {PG, $20}" ไม่ใช่ "PC + $20"
> ต่างจาก RISC-V หรือ 6502 ที่ branch เป็น relative offset
> ข้อดี: ง่าย, ไม่ต้อง adder เพิ่ม. ข้อเสีย: branch ข้าม page ต้อง SETPG ก่อน

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC574 (U23, Page Register) | 1 |
| 2 | LED สีเขียว 3mm | 8 |
| 3 | 330Ω resistor | 8 |
| 4 | 100nF capacitor | 1 |

---

## วงจร

### Pinout: 74HC574

```
        ┌───U───┐
 /OE  1 │       │ 20 VCC
  D1  2 │       │ 19 Q1
  D2  3 │ 574   │ 18 Q2
  D3  4 │       │ 17 Q3
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
U23 (Page Register):
  pin 20 (VCC) → 5V,  pin 10 (GND) → GND,  100nF คร่อม VCC-GND
  pin 1 (/OE) → GND (output ตลอด)
  pin 11 (CLK) ← PG_CLK (U25-11)

    74HC574 loads on RISING edge.
    PG_CLK goes LOW during T2 (when SETPG active),
    then returns HIGH at end of T2 → creates rising edge → U23 latches!

    Timing:
      T2 start → PG_CLK = LOW (hold)
      T2 end   → PG_CLK = HIGH (rising edge = latch!)
      IBUS still valid at this moment → PG gets correct value

  D inputs ← IBUS:
    pin 2 (D1) ← IBUS0    pin 3 (D2) ← IBUS1
    pin 4 (D3) ← IBUS2    pin 5 (D4) ← IBUS3
    pin 6 (D5) ← IBUS4    pin 7 (D6) ← IBUS5
    pin 8 (D7) ← IBUS6    pin 9 (D8) ← IBUS7

  Q outputs → PC high byte D inputs (สำหรับ jump):
    pin 19 (Q1) → PG0 → U3-3 (PC8 D-input)
    pin 18 (Q2) → PG1 → U3-4 (PC9 D-input)
    pin 17 (Q3) → PG2 → U3-5 (PC10 D-input)
    pin 16 (Q4) → PG3 → U3-6 (PC11 D-input)
    pin 15 (Q5) → PG4 → U4-3 (PC12 D-input)
    pin 14 (Q6) → PG5 → U4-4 (PC13 D-input)
    pin 13 (Q7) → PG6 → U4-5 (PC14 D-input)
    pin 12 (Q8) → PG7 → U4-6 (PC15 D-input)

  LED (ดู page value):
    PG0-PG7 → 330Ω → LED → GND (8 ดวง)
```

---

## ทดสอบ ✅

### Test 1: SETPG $10

Flash ROM:
```
$0000: $20  ; SETPG (MUX_SEL=1, AC_WR=0, others=0)
$0001: $10  ; page value = $10
```

| ขั้น | Phase | สิ่งที่เกิด | PG LED | ถูก? |
|:----:|:-----:|-------------|:------:|:----:|
| 1 | T0 | fetch $20 → IR_H | $00 (ยังไม่เปลี่ยน) | ☐ |
| 2 | T1 | fetch $10 → IR_L (→IBUS) | $00 | ☐ |
| 3 | T2 | PG_CLK pulses → U23 latches $10 | $10 ○○○●○○○○ | ☐ |

### Test 2: SETPG แล้ว J → PC = page:target

Flash ROM:
```
$0000: $20  ; SETPG
$0001: $10  ; page = $10
$0002: $01  ; J
$0003: $00  ; target low = $00
```

| ขั้น | Phase | สิ่งที่เกิด | PC | ถูก? |
|:----:|:-----:|-------------|:--:|:----:|
| 1-3 | SETPG | PG = $10 | $0002 | ☐ |
| 4 | T0 | fetch $01 (J) | $0002 | ☐ |
| 5 | T1 | fetch $00 (target) | $0003 | ☐ |
| 6 | T2 | /PC_LD=LOW → PC high←PG=$10, PC low←IRL=$00 | **$1000** | ☐ |

ดู PC LED (ถ้ามี) หรือดู ABUS ที่ address mux output

### Test 3: SETPG $00 (กลับหน้า ROM)

```
$1000: $20  ; SETPG
$1001: $00  ; page = $00
$1002: $01  ; J
$1003: $00  ; target = $00
→ PC should become $0000 (back to start!)
```

| หลัง execute | PC | PG LED | ถูก? |
|:------------:|:--:|:------:|:----:|
| J at $1002 | $0000 | $00 ○○○○○○○○ | ☐ |

### Long Jump Test (ตรวจ PG ครบทุกบิต)
- [ ] SETPG $FF, J $FF → PC = $FFFF (all bits HIGH)
- [ ] SETPG $AA, J $55 → PC = $AA55 (alternating pattern)
- [ ] ถ้าบิตใดไม่ถูก → PG-to-PC wiring (U23→U3/U4) ต่อผิดบิต

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| PG ไม่เปลี่ยนหลัง SETPG | CLK ไม่ pulse | เช็ค U25-11 → U23-11 |
| PG เปลี่ยนทุก instruction | PG_CLK ค้าง LOW | เช็ค U27-8 (/PG_cond) + U28-6 (/T2) |
| PC high ไม่เปลี่ยนหลัง J | U23-Q ไม่ต่อ U3/U4 D | เช็คสาย PG → PC high D-inputs |
| Jump ไปผิด page | PG สลับ bit order | เช็ค PG0→U3-3, PG4→U4-3 |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR-V2/sim/sim_lab
python3 lab11_page_register.py
```

---

## สิ่งที่ได้

- ✅ SETPG ตั้ง page register ได้ (loaded on rising edge of PG_CLK)
- ✅ J/BEQ/BNE ใช้ PC = {PG, IRL} = absolute 16-bit address
- ✅ CPU กระโดดได้ทั้ง 64KB address space (SETPG → J)
- ✅ ต่อ U23-Q → U3/U4 D-inputs (PC high byte) ถูกต้อง

**ผ่านทุกข้อ → ไป Lab 12!** 🎉
