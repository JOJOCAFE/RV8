# RV8-GR — Debug Plan (Physical Build)

**สร้างทีละโมดูล ทดสอบทุกขั้น ไม่ต้องรีบ ใช้ LED + single-step clock**

---

## อุปกรณ์ Debug

| อุปกรณ์ | จำนวน | ใช้ทำอะไร |
|---------|:-----:|-----------|
| LED + 330Ω resistor | 8 | ดู bus 8 บิต |
| Push button (NO) | 1 | Single-step clock |
| 555 timer module | 1 | Low-speed clock (1-10 Hz) |
| DIP switch 8-bit | 1 | ป้อน data bus ด้วยมือ |
| Logic probe / multimeter | 1 | เช็ค HIGH/LOW |

---

## Clock Options

```
Mode 1: Single-step (debug)
  Button → debounce (RC + Schmitt) → CLK
  กดปุ่ม 1 ครั้ง = 1 clock = 1 state change

Mode 2: Low speed (1-10 Hz)
  555 timer → CLK
  ดู LED กระพริบทีละ state

Mode 3: Full speed (10 MHz)
  Crystal oscillator → CLK
  ใช้ตอนทำงานจริง
```

---

## ขั้นที่ 1: Power + Clock + Reset

**ต่ออะไร**: 5V supply, clock (button), reset (RC), LED 1 ดวงบน CLK

**ทดสอบ**:
- [ ] VCC = 5.0V ± 0.2V ที่ทุกจุด
- [ ] GND ต่อถึงกันทุกจุด (วัดด้วย multimeter continuity)
- [ ] กดปุ่ม clock → LED CLK กระพริบ
- [ ] Reset: กด reset → ปล่อย → /RST ขึ้น HIGH

**LED**: 1 ดวงบน CLK output

---

## ขั้นที่ 2: Ring Counter (U8 + U24 inverters)

**ต่ออะไร**: U8 (74HC164), U24 pin 1-4 (inverters 2 ตัว)

**ทดสอบ**:
- [ ] Reset → T0=1, T1=0, T2=0
- [ ] Clock 1 → T0=0, T1=1, T2=0
- [ ] Clock 2 → T0=0, T1=0, T2=1
- [ ] Clock 3 → T0=1, T1=0, T2=0 (wrap around)
- [ ] ทำซ้ำ 10 รอบ ไม่ skip ไม่ค้าง

**LED**: 3 ดวงบน T0 (U8-3), T1 (U8-4), T2 (U8-5)

```
กดปุ่ม:  LED pattern:
  1       T0=on  T1=off T2=off
  2       T0=off T1=on  T2=off
  3       T0=off T1=off T2=on
  4       T0=on  T1=off T2=off  ← ถูกต้อง!
```

**ผิดพลาดที่พบบ่อย**:
- T0 ค้าง HIGH → U24 inverter ต่อผิดขา
- ไม่ wrap → U8 pin A,B ต่อผิด (ต้องเป็น NOT(Q0), NOT(Q1))

---

## ขั้นที่ 3: PC Counter (U1-U4)

**ต่ออะไร**: U1-U4 (74HC161 ×4), ต่อ CLK, /RST, cascade (RCO)

**ก่อนต่อ memory**: ยังไม่ต่อ ROM/RAM — ทดสอบ counter เปล่า

**ทดสอบ**:
- [ ] Reset → PC = $0000 (ดูจาก LED บน QA-QD ของ U1)
- [ ] ENP=1, ENT=1 → กด clock → PC นับขึ้น 0,1,2,3...
- [ ] /LD=0, D=$42 → กด clock → PC = $42
- [ ] Cascade: U1 RCO → U2 ENT (นับเกิน 15 ขึ้น U2)

**LED**: 8 ดวงบน PC[7:0] (U1 QA-QD + U2 QA-QD)

```
Reset:    00000000
Clock 1:  00000001
Clock 2:  00000010
...
Clock 15: 00001111
Clock 16: 00010000  ← U2 เริ่มนับ (cascade ทำงาน!)
```

**สำคัญ**: ต่อ PC_INC (U25-6) = VCC ชั่วคราว เพื่อให้นับตลอด

---

## ขั้นที่ 4: Address Mux (U15-U16, U29-U30)

**ต่ออะไร**: Mux 4 ตัว, ต่อ PC outputs เข้า A-inputs

**ทดสอบ**:
- [ ] SEL=0 (GND) → ABUS = PC (ดู LED ตรงกับ PC)
- [ ] SEL=1 (VCC) → ABUS = B-inputs (ต่อ DIP switch เข้า B)
- [ ] A15 output ถูกต้อง (U30-12)

**LED**: 8 ดวงบน ABUS A[7:0]

---

## ขั้นที่ 5: ROM (AT28C256)

**ต่ออะไร**: ROM, ต่อ ABUS → ROM A[14:0], /CE ← /A15, /OE ← GND

**เตรียม ROM**: Flash test pattern ด้วย Programmer board:
```
$8000: $30  (LI opcode)
$8001: $42  (operand)
$8002: $01  (J opcode)
$8003: $00  (jump to $00 → loop)
```

**ทดสอบ**:
- [ ] PC=$8000, A15=1 → ROM /CE=0 → DBUS = $30
- [ ] PC=$8001 → DBUS = $42
- [ ] PC=$8002 → DBUS = $01
- [ ] PC=$8003 → DBUS = $00

**LED**: 8 ดวงบน DBUS D[7:0]

```
กด clock (PC นับ):
  $8000 → LED = 00110000 ($30)  ✓
  $8001 → LED = 01000010 ($42)  ✓
```

**ผิดพลาดที่พบบ่อย**:
- DBUS = $00 ตลอด → ROM /CE ไม่ LOW (เช็ค A15 → U24 inverter)
- DBUS ผิดค่า → address ต่อสลับ (A0↔A1 etc.)

---

## ขั้นที่ 6: Bus Buffer + IR (U7, U5, U6)

**ต่ออะไร**: U7 (245), U5 (IR_HIGH), U6 (IR_LOW), **U25 gate 3 (SRC+STR guard)**

**สำคัญ**: U7-19 (/OE) ต้องต่อจาก **U25-8** (BUF_OE_SAFE) ไม่ใช่ U24-12!
```
U25-9  ← U24-12 (BUF_OE_N)
U25-10 ← U5-17 (STR)
U25-8  → U7-19 (BUF_OE_SAFE = BUF_OE_N OR STR)
```

**ทดสอบ Guard**:
- [ ] เมื่อ STR=1 (force U5-17 HIGH): U7-19 ต้อง HIGH (U7 disabled)
- [ ] เมื่อ STR=0 + BUF_OE_N=0: U7-19 = LOW (U7 enabled ปกติ)

**ทดสอบ**: Single-step ผ่าน 1 คำสั่ง LI $42:
- [ ] T0: U7 enabled, DBUS($30) → IBUS → U5 latch → IR_HIGH=$30
- [ ] T1: DBUS($42) → IBUS → U6 latch → IR_LOW=$42
- [ ] ดูค่า U5 Q outputs (control signals) ตรง

**LED**: 8 ดวงบน IBUS (U7 B-side) หรือ U5 Q outputs

```
After T0: U5-15(AC_WR)=1, U5-14(MUX)=1 → ถูกต้องสำหรับ LI!
After T1: U6-19(IRL0)=0, U6-18(IRL1)=1, U6-17(IRL2)=0... = $42
```

---

## ขั้นที่ 7: ALU + AC (U10-U13, U19-U20, U17-U18, U9)

**ต่ออะไร**: XOR gates, adder, muxes, accumulator

**ทดสอบ LI $42**:
- [ ] T2: IBUS=$42, XOR B-mux=0, XOR output=$42
- [ ] MUX_SEL=1 → AC mux selects XOR output
- [ ] Acc_Load_N pulse → AC latches $42
- [ ] ดู U9 Q outputs = $42

**LED**: 8 ดวงบน AC (U9 Q outputs)

```
Before T2: AC = $00 (reset)
After T2:  AC = $42 ← LI $42 ทำงานแล้ว!
```

**ทดสอบ ADDI $05** (flash ROM: $8004=$10, $8005=$05):
- [ ] After execute: AC = $42 + $05 = $47

---

## ขั้นที่ 8: Z Flag (U21, U22)

**ต่ออะไร**: U22 (688), U21 (74)

**ทดสอบ**:
- [ ] AC=$42 → Z LED = OFF (AC ≠ 0)
- [ ] SUBI $42 → AC=$00 → Z LED = ON

**LED**: 1 ดวงบน Z_flag (U21-5)

---

## ขั้นที่ 9: Branch/Jump Logic (U24-U28)

**ต่ออะไร**: Control logic gates

**ทดสอบ J (unconditional jump)**:
- [ ] Flash ROM: J $10 at $8006
- [ ] After T2: /PC_LD goes LOW → PC loads $8010

**ทดสอบ BEQ (Z=1)**:
- [ ] Set AC=0 (Z=1), BEQ $20
- [ ] After T2: PC = $8020

**LED**: 1 ดวงบน /PC_LD (U26-11)

---

## ขั้นที่ 10: Page Register + 16-bit Jump (U23)

**ต่ออะไร**: U23 (574)

**ทดสอบ**:
- [ ] SETPG $90 → PG LED = $90
- [ ] J $00 → PC = $9000

**LED**: 8 ดวงบน Page Reg (U23 Q outputs)

---

## ขั้นที่ 11: RAM (62256) + Data Page (U32)

**ต่ออะไร**: RAM, U32 (74HC574), ต่อ ABUS, DBUS, /CE ← A15, /WE ← /AC_BUF

**U32 wiring**:
- D[7:0] ← IBUS
- Q[6:0] → U29/U30 B-inputs (A[14:8])
- Q[7] → U30-13 (A15 B-input)
- CLK ← DP_Load decode (T2 AND ir_high==$40)

**ทดสอบ page 0 (SETDP $00)**:
- [ ] SETDP $00, AC=$AA, SB $03 → RAM[$0003] = $AA
- [ ] LB $03 → AC = $AA (read back)

**ทดสอบ page $10 (SETDP $10)**:
- [ ] SETDP $10, LI $55, SB $00 → RAM[$1000] = $55
- [ ] LB $00 → AC = $55 (read from page $10)

**ทดสอบ ROM read (SETDP $80)**:
- [ ] SETDP $80, LB $00 → AC = ROM[$8000] = first opcode

**LED**: 8 ดวงบน U32 Q outputs (ดู data page value)

---

## ขั้นที่ 12: Full System Test

**ต่อครบทุกชิป** แล้วรัน test ROM:

```asm
; Test ROM ($8000):
LI $10        ; AC=$10
ADDI $05      ; AC=$15
SUBI $15      ; AC=$00, Z=1
BEQ pass      ; should jump
J fail        ; should not reach
pass: HLT     ; success!
fail: HLT     ; failure
```

**ทดสอบ**:
- [ ] Single-step ทีละ clock → ดู AC, Z, PC เปลี่ยนถูกต้อง
- [ ] Low-speed (1 Hz) → ดู LED pattern ถูก
- [ ] Full-speed (10 MHz) → halt ที่ pass (ไม่ใช่ fail)

---

## ขั้นที่ 13: IRQ (U31)

**ต่ออะไร**: U31 (74HC74), /IRQ pin, decode logic

**v1.0: IRQ ใช้ software save-PC** (ไม่มี hardware auto-save)

ก่อน EI ต้อง save return address ด้วย software:
```asm
; ก่อนเปิด interrupt:
LI lo(return_here)
SB $0E                  ; save low byte
LI hi(return_here)
SB $0F                  ; save high byte
EI                      ; enable interrupt

; ... code runs ...

return_here:            ; ISR จะกลับมาตรงนี้
```

ISR at $FF00:
```asm
; handle interrupt ...
SETDP $00
LB $0F
SETPG_R $0F             ; page = saved high byte (ผ่าน register)
LB $0E                  ; AC = saved low byte
; ... need indirect jump mechanism ...
EI
; (v1.0: return to fixed known address)
```

**ทดสอบ**:
- [ ] EI → IE LED = ON
- [ ] กดปุ่ม /IRQ → PC jumps to $FF00
- [ ] DI → IE LED = OFF → IRQ ไม่ fire
- [ ] ISR ทำงานแล้วกลับมาที่ return_here ได้

**LED**: 1 ดวงบน IE (U31-5), 1 ดวงบน IRQ_FF (U31-12)

---

## ขั้นที่ 14: RV8-Bus (40-pin connector)

**ต่ออะไร**: IDC 40-pin socket, route สัญญาณจาก CPU board ออก bus

**สายที่ต้อง route ไป bus connector:**
```
Pin 1-16:  A[0:15] จาก ABUS (U15/U16/U29/U30 outputs)
Pin 17-24: D[0:7] จาก DBUS
Pin 25:    CLK จาก oscillator
Pin 26:    /RST จาก reset circuit
Pin 27:    /WR = /AC_BUF (U26-8)
Pin 28:    /RD (ใช้ NOT(T2) หรือ fetch indicator)
Pin 29:    /IRQ ← input จาก peripheral (ต่อ U31-10)
Pin 30:    /SLOT1 ← address decode ($FF1x)
Pin 31:    /SLOT2 ← address decode ($FF2x)
Pin 32:    T2 (U8-5)
Pin 39:    VCC (+5V)
Pin 40:    GND
```

**ทดสอบ**:
- [ ] ต่อ Programmer board ผ่าน ribbon cable
- [ ] `rv8flash.py -c` → "Connected"
- [ ] Flash test ROM → verify ด้วย `rv8flash.py -v`
- [ ] CLK บน bus pin 25 = oscillator (วัดด้วย probe)
- [ ] /RST บน bus pin 26 = HIGH ตอนปกติ, LOW ตอนกด reset
- [ ] /WR บน bus pin 27 = pulse LOW เฉพาะตอน STORE
- [ ] /IRQ bus pin 29 → กดปุ่ม → CPU jump $FF00

**LED**: ดูบน bus connector: CLK (กระพริบ), /WR (pulse ตอน store)

**ทดสอบ I/O Slot:**
```asm
; Test SLOT1 ($FF10):
SETPG $FF       ; page = $FF
LI $42          ; AC = $42
SB $10          ; write to $FF10 → /SLOT1 should go LOW
```
- [ ] /SLOT1 (pin 30) goes LOW during SB $10 at page $FF

---

## Debug Tips

| อาการ | สาเหตุที่พบบ่อย |
|-------|----------------|
| LED ไม่ติดเลย | VCC/GND ไม่ถึง, IC ใส่กลับด้าน |
| PC ไม่นับ | ENP/ENT ไม่ HIGH, clock ไม่ถึง |
| DBUS = $00 ตลอด | ROM /CE ไม่ active, /OE ไม่ต่อ GND |
| AC ไม่เปลี่ยน | Acc_Load_N ไม่ pulse, AC_WR=0 |
| Jump ไม่ทำงาน | /PC_LD ค้าง HIGH, Page Reg ผิด |
| RAM write ไม่ได้ | /WE ไม่ pulse, A15 ไม่ใช่ 0 |
| Ring counter ค้าง | Inverter ต่อผิด, /CLR ค้าง LOW |

---

## LED Probe Board (แนะนำ)

ทำบอร์ด LED 8 ดวง + header สำหรับเสียบดู bus:

```
[GND]─┬─[330Ω]─[LED]─[pin0]
      ├─[330Ω]─[LED]─[pin1]
      ├─[330Ω]─[LED]─[pin2]
      ├─[330Ω]─[LED]─[pin3]
      ├─[330Ω]─[LED]─[pin4]
      ├─[330Ω]─[LED]─[pin5]
      ├─[330Ω]─[LED]─[pin6]
      └─[330Ω]─[LED]─[pin7]
```

ใช้เสียบดูที่ไหนก็ได้: DBUS, IBUS, ABUS, AC, PC, IR...

---

## Checklist สรุป

| # | โมดูล | ชิป | LED ดูตรงไหน | ผ่าน? |
|:-:|-------|-----|-------------|:-----:|
| 1 | Power + Clock | - | CLK | ☐ |
| 2 | Ring Counter | U8, U24 | T0,T1,T2 | ☐ |
| 3 | PC Counter | U1-U4 | PC[7:0] | ☐ |
| 4 | Address Mux | U15-U16,U29-U30 | ABUS | ☐ |
| 5 | ROM | AT28C256 | DBUS | ☐ |
| 6 | Bus + IR | U7, U5, U6 | IBUS / IR_HIGH | ☐ |
| 7 | ALU + AC | U10-U13,U17-U20,U9 | AC | ☐ |
| 8 | Z Flag | U21, U22 | Z | ☐ |
| 9 | Jump Logic | U24-U28 | /PC_LD | ☐ |
| 10 | Page Register | U23 | PG[7:0] | ☐ |
| 11 | RAM + Data Page | 62256, U32, U33 | DBUS, DP[7:0] | ☐ |
| 12 | Full System | all | AC, PC, Z | ☐ |
| 13 | IRQ | U31 | IE, IRQ_FF | ☐ |
| 14 | RV8-Bus | 40-pin IDC | CLK, /WR, /SLOT | ☐ |
