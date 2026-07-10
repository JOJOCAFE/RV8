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

## Baseline Boundary

Debug only the RV8GR baseline first:

- 34 logic chips + ROM + RAM.
- IRQ is polling-only.
- DI has no hardware effect.
- No hardware vector to `$FF00`.
- No automatic PC save, restore, acknowledge, or RETI circuit.

If the CPU jumps when `/IRQ` is asserted, that is a wiring mistake for v2.

---

## Virtual Check Before Wiring

Before a student wires the full system, run the software checks from
`RV8GR/README.md`, then run the RV8GR soft debug trace and the Components
virtual physical checker:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B sim/soft_debug.py
```

```bash
cd /home/jo/kiro/Components
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
```

This checker is a virtual risk screen for pin-number mistakes, active-low
mistakes, unsafe output-output wiring, and timing/noise assumptions in the
whole-system circuit model. Passing it means the model is ready to compare
against the bench. It does not prove that the physical breadboard is correct.

> 📌 Simulator note: `sim/soft_debug.py` starts PG=$00, DP=$80, AC=$00, Z=1 so
> its built-in tests are deterministic. Real 74HC574 registers PG/DP/AC and the
> Z flag are not guaranteed after reset. The physical ROM must still start with
> the boot initialization sequence below.

---

## Probe Point Map

Use these points before guessing. A stage is not passed until the listed signal
matches the expected behavior.

| Signal | Probe at | Expected use |
|--------|----------|--------------|
| `CLK` | U8-8, U1-U4 pin 2 | One clean pulse per button press |
| `/RST` | U1-U4 pin 1, U8-9, U31-1/13 | LOW during reset, HIGH when running |
| `T0` | U8-3 | Opcode fetch phase |
| `T1` | U8-4 | Operand fetch phase |
| `T2` | U8-5 | Execute phase |
| `PC0..PC7` | U1/U2 Q outputs | Counts during T0/T1, loads on jump |
| `ABUS0..ABUS7` | U15/U16 outputs | PC or IRL selected by `/ADDR_MODE` |
| `ABUS8..ABUS15` | U29/U30 outputs | PC high or DP selected by `/ADDR_MODE` |
| `DBUS0..DBUS7` | ROM/RAM data pins, U7 B side | External memory data bus |
| `IBUS0..IBUS7` | U7 A side, U34 output, U14 output | Internal CPU data bus |
| `BUF_OE_N` | U24-12, U7-19 | LOW when U7 is enabled |
| `WR_DIR` | U28-8, U7-1, ROM `/OE` | 0 read, 1 store/write direction |
| `/IRL_OE` | U26-3, U34-1/19 | LOW when operand drives IBUS |
| `/AC_BUF` | U26-8, U14 enables, RAM `/WE` | LOW when AC stores to memory |
| `ACC_CLK` | U27-11, U9-11, U21-3 | AC/Z update pulse |
| `AC0..AC7` | U9 Q outputs | Accumulator value |
| `Z_flag` | U21-5 | HIGH when AC is zero |
| `/PC_LD` | U26-11, U1-U4 pin 9 | LOW only for taken jump/branch at T2 |
| `PG0..PG7` | U23 Q outputs | Jump page high byte |
| `DP0..DP7` | U32 Q outputs | Data page high byte |
| `DP_Load` | U33-6, U32-11 | Pulse on SETDP |
| `IE` | U31-5 | Set by EI, cleared by reset only |
| `IRQ_FF` | U31-9 | Latches after `/IRQ` release, cleared by reset |

---

## Clock Options

```
Mode 1: Single-step (debug)
  Button → debounce (RC + Schmitt) → CLK
  กดปุ่ม 1 ครั้ง = 1 clock = 1 state change

Mode 2: Low speed / timing qualification
  50 kHz first, then 1 MHz, 2 MHz, 5 MHz
  Use 50 kHz for safe visible bring-up before MHz tests

Mode 3: Full speed
  Crystal oscillator → CLK
  1 MHz = official target (ปลอดภัย, margin >700ns)
  2 MHz = achievable on short-wire breadboard
  5 MHz = PCB only (experimental, ~0ns margin)
```

---

## ขั้นที่ 0: Boot Sequence Sanity Check

**เมื่อไร**: หลังต่อวงจรครบทุกชิป (ขั้นที่ 12+) หรือเป็น first test ของ full system

**Reset state ที่ hardware รับประกัน:**
- PC = $0000
- T-state = T0
- IE = 0, IRQ_FF = 0

**State ที่ UNKNOWN หลัง reset** (ต้อง initialize ก่อนใช้):
- PG, DP, AC, Z = ค่าไม่แน่นอน

**Test ROM (flash ไว้ที่ $0000):**
```asm
SETDP $80       ; DP = $80
SETPG $00       ; PG = $00
LI $00          ; AC = $00, Z = 1
J $06           ; loop here (HLT macro = J self)
```

**ทดสอบ (single-step 12 clocks):**
- [ ] After 3 clocks (1 instr): DP LED = $80
- [ ] After 6 clocks (2 instr): PG LED = $00
- [ ] After 9 clocks (3 instr): AC LED = $00, Z LED = ON
- [ ] After 12 clocks (4 instr): PC = $0006 (J $06 loads PC back to same address → loop)

> 📌 ถ้า test นี้ผ่าน = CPU boot ได้ถูกต้อง ทุก architectural state defined แล้ว

---

## ขั้นที่ 1: Power + Clock + Reset

**ต่ออะไร**: 5V supply, clock (button), reset (RC), LED 1 ดวงบน CLK

**ทดสอบ**:
- [ ] VCC = 5.0V ± 0.2V ที่ทุกจุด
- [ ] GND ต่อถึงกันทุกจุด (วัดด้วย multimeter continuity)
- [ ] กดปุ่ม clock → LED CLK กระพริบ
- [ ] Reset: กด reset → ปล่อย → /RST ขึ้น HIGH
- [ ] Bypass cap 100nF ceramic ทุก IC (VCC↔GND ใกล้ขาชิปที่สุด)

> ⚠️ **Decoupling capacitor บังคับ**: 100nF ceramic 1 ตัวต่อ 1 IC.
> วางใกล้ขา VCC/GND ของชิปให้มากที่สุด ห้ามข้าม.
> ถ้าไม่ใส่: 1 MHz อาจผ่าน แต่ 2 MHz จะ glitch สุ่ม.

### Power Integrity Test (ทำหลังต่อชิปครบ ก่อน full-speed)

- [ ] รัน 1 MHz → วัด VCC ที่ชิปไกลสุดจากแหล่งจ่าย (U30, U32)
- [ ] เกณฑ์: 4.8V–5.2V = ผ่าน. < 4.7V = อันตราย (เพิ่ม bulk cap 100µF)

### Reset Recovery Test

- [ ] รันโปรแกรม loop ที่ 1 MHz (เช่น LI $55, ADDI $01, J $00)
- [ ] กด RESET ขณะรัน → PC ต้องกลับ $0000, T-state=T0 ทุกครั้ง
- [ ] ลองกด RESET 10 ครั้งที่จังหวะต่างกัน → ต้องผ่านทุกครั้ง

**LED**: 1 ดวงบน CLK output

### Clock Integrity Check (ก่อนต่อ Ring Counter)

- [ ] กดปุ่มค้าง → LED ติดค้าง (ไม่กระพริบ = debounce ดี)
- [ ] ปล่อยปุ่ม → LED ดับ (ไม่ bounce กลับ)
- [ ] กดแล้วปล่อยเร็ว → นับได้ 1 pulse เท่านั้น (ดูจาก ring counter ใน Step 2)
- [ ] 100-tick push-switch test: กด single-step 100 ครั้ง → ring counter ต้อง
      วน T0→T1→T2 ครบ 33 รอบ + T0 โดยไม่ข้าม state

> ⚠️ ถ้า clock bounce → ring counter จะ advance หลาย state ในปุ่มเดียว
> แก้: เพิ่ม RC debounce (10kΩ + 100nF) + 74HC14 Schmitt trigger

---

## ขั้นที่ 2: Ring Counter (U8 + U24 inverters)

**ต่ออะไร**: U8 (74HC164), U24 pin 1-4 (inverters 2 ตัว)

**ทดสอบ**:
- [ ] Reset → T0=1, T1=0, T2=0
- [ ] Clock 1 → T0=0, T1=1, T2=0
- [ ] Clock 2 → T0=0, T1=0, T2=1
- [ ] Clock 3 → T0=1, T1=0, T2=0 (wrap around)
- [ ] ทำซ้ำ 10 รอบ ไม่ skip ไม่ค้าง

**Endurance test** (555 timer @ 1 Hz, ปล่อย 1000+ cycles):
- [ ] ดู T0→T1→T2 ไม่เคยหลุด pattern (LED หมุน 3 ดวงสม่ำเสมอ)
- [ ] ถ้า skip หรือค้าง → ตรวจ inverter feedback (U24) หรือ clock bounce

**Illegal State Recovery** (ตรวจว่า ring counter self-corrects):
- [ ] ถอด /RST ชั่วคราว แล้วจ่าย noise เข้า U8 → state อาจเพี้ยน
- [ ] ต่อ /RST กลับ → กด reset → ต้องกลับ T0=1,T1=0,T2=0 ทันที
- [ ] ถ้า power-up ได้ state 000 (all-zero) → feedback NOT(Q0)&NOT(Q1) จะ inject 1 → recover ภายใน 3 clocks

**Ring Counter State Matrix** (74HC164 behavior):

| Q2 Q1 Q0 | State | Recovery |
|:---------:|-------|----------|
| 0  0  0 | All-zero | Self-recover in 3 clocks (feedback injects 1) |
| 0  0  1 | T0 | ✅ Normal |
| 0  1  0 | T1 | ✅ Normal |
| 1  0  0 | T2 | ✅ Normal |
| 0  1  1 | Illegal | Clears in 1-2 clocks (feedback = NOT(1)&NOT(1) = 0) |
| 1  0  1 | Illegal | Clears in 1-2 clocks |
| 1  1  0 | Illegal | Clears in 1-2 clocks |
| 1  1  1 | Illegal | Clears in 2-3 clocks |

> 📌 All illegal states self-correct within 3 clocks — no hardware fix needed.
> /RST forces immediate recovery to T0 (001).

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

> ⚠️ **ถอด VCC จาก PC_INC ก่อนเริ่มขั้นที่ 9 (Jump Logic)**
> ไม่งั้น PC จะนับขึ้นตลอดแม้ J/BEQ สั่ง load → jump test จะ fail

---

## ขั้นที่ 4: Address Mux (U15-U16, U29-U30)

**ต่ออะไร**: Mux 4 ตัว, ต่อ IRL/DP เข้า A-inputs และ PC เข้า B-inputs

**ทดสอบ**:
- [ ] /ADDR_MODE=1 (VCC) → ABUS = PC (ดู LED ตรงกับ PC)
- [ ] /ADDR_MODE=0 (GND) → ABUS = A-inputs (ต่อ DIP switch เข้า A)
- [ ] A15 output ถูกต้อง (U30-12)

**LED**: 8 ดวงบน ABUS A[7:0]

---

## ขั้นที่ 5: ROM (AT28C256)

**ต่ออะไร**: ROM, ต่อ ABUS → ROM A[14:0], /CE ← A15, /OE ← WR_DIR (U28-8)

> 📌 Chip Select (from Design ISA):
> ROM /CE = A15 (active when A15=0, address $0000-$7FFF)
> RAM /CE = /A15 (active when A15=1, address $8000-$FFFF)

**เตรียม ROM**: Flash test pattern ด้วย Programmer board:
```bash
python3 ../Programmer/tools/rv8flash.py program test_bytes.bin --base 0x0000
```

```
$0000: $30  (LI opcode)
$0001: $42  (operand)
$0002: $01  (J opcode)
$0003: $00  (jump to $00 → loop)
```

**ทดสอบ**:
- [ ] PC=$0000, A15=0 → ROM /CE=0 → DBUS = $30
- [ ] PC=$0001 → DBUS = $42
- [ ] PC=$0002 → DBUS = $01
- [ ] PC=$0003 → DBUS = $00

**ทดสอบ ROM inactive (สำหรับ RAM ขั้นที่ 11)**:
- [ ] Force A15=1 (ต่อ VCC ชั่วคราว) → ROM /CE=1 → ROM output hi-Z (DBUS ไม่ถูกขับ)

> 💡 Tip: ใส่ 10kΩ pull-up บน DBUS → ถ้า ROM hi-Z จริง DBUS จะอ่านได้ $FF ชัดเจน

**LED**: 8 ดวงบน DBUS D[7:0]

```
กด clock (PC นับ):
  $0000 → LED = 00110000 ($30)  ✓
  $0001 → LED = 01000010 ($42)  ✓
```

**ผิดพลาดที่พบบ่อย**:
- DBUS = $00 ตลอด → ROM /CE ไม่ LOW (เช็ค A15 = 0 จาก PC)
- DBUS ผิดค่า → address ต่อสลับ (A0↔A1 etc.)

---

## ขั้นที่ 6: Bus Buffer + IR (U7, U5, U6)

**ต่ออะไร**: U7 (245), U5 (IR_HIGH), U6 (IR_LOW), ROM /OE safety via WR_DIR

### Bus Ownership Verification (ตรวจก่อนต่อ ALU)

ใช้ LED probe ตรวจ IBUS driver ทีละ phase:

| Phase | IBUS driver ที่ถูกต้อง | ตรวจ |
|:-----:|:----------------------:|------|
| T0 | U7 (DBUS→IBUS) | U7-19=LOW, U34-1/19=HIGH, U14-1=HIGH |
| T1 | U7 (DBUS→IBUS) | (เหมือน T0) |
| T2 immediate | U34 (IRL→IBUS) | U34-1/19=LOW, U7-19=HIGH |
| T2 store | U14 (AC→IBUS), U7 writes IBUS→DBUS | U14-1=LOW, U7-19=LOW, U7-1=HIGH |

- [ ] Single-step ตรวจว่า IBUS driver ไม่ทับกัน (ทีละตัวเท่านั้น)

### Bus Float Test (ตรวจ IBUS ไม่ลอย)

- [ ] Force: U7 /OE=HIGH, U34 /OE=HIGH, U14 /OE=HIGH (ปิด driver ทั้ง 3)
- [ ] วัด IBUS ด้วย LED → ค่าต้องคงที่ (ไม่สุ่มเปลี่ยน)
- [ ] ถ้า LED กระพริบสุ่ม → IBUS ลอย → เพิ่ม 10kΩ pull-down/pull-up

### DBUS Float Test

- [ ] ปิด ROM (/CE=HIGH), RAM (/CE=HIGH), U7 (/OE=HIGH)
- [ ] วัด DBUS → ค่าต้องคงที่ (ถ้ามี pull-up → $FF)
- [ ] ถ้าสุ่มค่า → DBUS ลอย → ปกติไม่เป็นปัญหา (มี driver active ทุก phase) แต่ช่วยยืนยัน isolation

### Bus Fight Detection (กระแสผิดปกติ)

- [ ] วัดกระแสรวมขณะ single-step: ปกติ ≈ 50–150mA
- [ ] ถ้า > 200mA หรือ IC ร้อนผิดปกติ → bus fight (2 drivers active พร้อมกัน)
- [ ] จุดที่เสี่ยง: T2 store to ROM page (ROM /OE must go HIGH via WR_DIR)

**สำคัญ**: U7-19 (/OE) ต้องต่อจาก **U24-12** (BUF_OE_N)
```
U24-13 ← U26-3 (/IRL_OE)
U24-12 → U7-19 (BUF_OE_N)
U28-8  → U7-1 (WR_DIR) and ROM /OE
```

**ทดสอบ Store Path**:
- [ ] เมื่อ STR=1 ที่ T2: U7-19 ต้อง LOW, U7-1 ต้อง HIGH, ROM /OE ต้อง HIGH
- [ ] เมื่อ T2 immediate: U7-19 ต้อง HIGH (U7 disabled)

**ทดสอบ**: Single-step ผ่าน 1 คำสั่ง LI $42:
- [ ] T0: U7 enabled, DBUS($30) → IBUS → U5 latch → IR_HIGH=$30
- [ ] T1: DBUS($42) → IBUS → U6 latch → IR_LOW=$42
- [ ] ดูค่า U5 Q outputs (control signals) ตรง

**LED**: 8 ดวงบน IBUS (U7 A-side) หรือ U5 Q outputs

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
- [ ] ACC_CLK pulse → AC latches $42
- [ ] ดู U9 Q outputs = $42

**LED**: 8 ดวงบน AC (U9 Q outputs)

```
Before T2: AC = unknown (74HC574 has no /CLR)
After T2:  AC = $42 ← LI $42 ทำงานแล้ว!
```

**ทดสอบ ADDI $05** (flash ROM: $0004=$10, $0005=$05):
- [ ] After execute: AC = $42 + $05 = $47

---

## ขั้นที่ 8: Z Flag (U21, U22)

**ต่ออะไร**: U22 (688), U21 (74)

**ทดสอบ**:
- [ ] AC=$42 → Z LED = OFF (AC ≠ 0)
- [ ] SUBI $42 → AC=$00 → Z LED = ON

**ทดสอบ async preset toggle** (พิสูจน์ U22→U21 /PR path):
- [ ] LI $00 → Z ON
- [ ] LI $01 → Z OFF
- [ ] LI $00 → Z ON อีกครั้ง (toggle กลับได้ = async preset ทำงาน)

**LED**: 1 ดวงบน Z_flag (U21-5)

---

## ขั้นที่ 9: Branch/Jump Logic (U24-U28)

**ต่ออะไร**: Control logic gates

**ทดสอบ J (unconditional jump)**:
- [ ] Flash ROM: J $10 at $0006
- [ ] After T2: /PC_LD goes LOW → PC loads $0010

**ทดสอบ BEQ (Z=1)**:
- [ ] Set AC=0 (Z=1), BEQ $20
- [ ] After T2: PC = $0020

**LED**: 1 ดวงบน /PC_LD (U26-11)

**PC_LOAD vs PC_INC Priority Test**:
- [ ] Execute J $10 → PC must be exactly $0010 (not $0011)
- [ ] ถ้า PC=$0011 → /PC_LD ชนะ PC_INC ไม่ได้ → ตรวจ 74HC161 /LD wiring

---

## ขั้นที่ 10: Page Register + 16-bit Jump (U23)

**ต่ออะไร**: U23 (574)

**ทดสอบ**:
- [ ] SETPG $90 → PG LED = $90
- [ ] J $00 → PC = $9000

**Long Jump Test** (ตรวจ PG ครบทุกบิต):
- [ ] SETPG $FF, J $FF → PC = $FFFF (all bits HIGH)
- [ ] SETPG $AA, J $55 → PC = $AA55 (alternating pattern)
- [ ] ถ้าบิตใดไม่ถูก → PG-to-PC wiring (U23→U3/U4) ต่อผิดบิต

**LED**: 8 ดวงบน Page Reg (U23 Q outputs)

---

## ขั้นที่ 11: RAM (62256) + Data Page (U32)

**ต่ออะไร**: RAM, U32 (74HC574), ต่อ ABUS, DBUS, /CE ← /A15 (U24-6), /WE ← /AC_BUF

**U32 wiring**:
- D[7:0] ← IBUS
- Q[6:0] → U29/U30 A-inputs (A[14:8])
- Q[7] → U30-14 (A15 A-input)
- CLK ← DP_Load (U33-6)

**U33 wiring (SETDP decode — 74HC21 gate 1)**:
- Pin 1 ← T2 (U8-5)
- Pin 2 ← XOR_MODE (U5-13)
- Pin 4 ← /ADDR_MODE (U26-6 — inverted SRC|STR)
- Pin 5 ← /AC_WR (U24 — inverted AC_WR)
- Pin 6 → U32 CLK (DP_Load)

DP_Load = T2 & XOR_MODE & /ADDR_MODE & /AC_WR
→ triggers on SETDP ($40) and alias $C0 (SUB bit ignored by decode)

**ทดสอบ page $80 (SETDP $80)**:
- [ ] SETDP $80, AC=$AA, SB $03 → RAM[$8003] = $AA
- [ ] LB $03 → AC = $AA (read back)

**ทดสอบ page $90 (SETDP $90)**:
- [ ] SETDP $90, LI $55, SB $00 → RAM[$9000] = $55
- [ ] LB $00 → AC = $55 (read from page $90)

**ทดสอบ ROM read (SETDP $00)**:
- [ ] SETDP $00, LB $00 → AC = ROM[$0000] = first opcode

> 📌 **Architectural Contract**: LB can read ROM (DP < $80).
> SB to ROM address is ignored during normal CPU runtime. ROM `/WE` stays
> inactive unless the Programmer owns it in PROG/reset isolation.

**ทดสอบ boundary (ROM/RAM split at $8000)**:
- [ ] SETDP $7F, LB $FF → reads ROM[$7FFF] (A15=0 → ROM)
- [ ] SETDP $80, LB $00 → reads RAM[$8000] (A15=1 → RAM)

**Memory Contention Test** (ตรวจว่า ROM/RAM ไม่ขับ DBUS พร้อมกัน):
- [ ] SETDP $7F, LB $00 → ดู ROM /CE=LOW, RAM /CE=HIGH (วัดด้วย probe)
- [ ] SETDP $80, SB $00 → ดู RAM /CE=LOW, ROM /CE=HIGH
- [ ] ถ้า A15 หลุด → ทั้ง ROM+RAM active → DBUS contention → ค่าอ่านผิด

**LED**: 8 ดวงบน U32 Q outputs (ดู data page value)

---

## ขั้นที่ 12: Full System Test

**ต่อครบทุกชิป** แล้วรัน test ROM:

```asm
; Test ROM ($0000):
LI $10        ; AC=$10
ADDI $05      ; AC=$15
SUBI $15      ; AC=$00, Z=1
BEQ pass      ; should jump
J fail        ; should not reach
pass: J pass  ; success! (PC=$000A loop)
fail: J fail  ; failure  (PC=$000C loop)
```

**ทดสอบ**:
- [ ] Single-step ทีละ clock → ดู AC, Z, PC เปลี่ยนถูกต้อง
- [ ] Low-speed (1 Hz) → ดู LED pattern ถูก
- [ ] Full-speed (1 MHz) → halt ที่ pass (ไม่ใช่ fail)

**Expected PC values** (ดู LED ของ PC):
- pass = PC loops (ดู address คงที่)
- fail = PC loops ที่ address อื่น → ผิด

**Burn-in test**:
- [ ] Run Golden Bring-up at 1 MHz continuously for 1 hour
- [ ] PC must remain at pass address (no glitches, no drift)
- [ ] If fails after 10+ minutes: check power rail noise, contact resistance, long wire ringing

### Walking-1 Address Test (ROM)

Flash ROM with known pattern at power-of-2 addresses:

```
$0001: $01,  $0002: $02,  $0004: $04,  $0008: $08
$0010: $10,  $0020: $20,  $0040: $40,  $0080: $80
```

- [ ] PC advances → DBUS matches address pattern (catches swapped address lines)
- [ ] ถ้า $0004 อ่านได้ $08 → A2/A3 สลับกัน

### RAM March Test (ตรวจ address line shorts)

```asm
; Write unique value to each address, then read back:
SETDP $80
LI $01 → SB $00    ; RAM[$8000] = $01
LI $02 → SB $01    ; RAM[$8001] = $02
LI $04 → SB $02    ; RAM[$8002] = $04
LI $08 → SB $03    ; RAM[$8003] = $08
; ... then read back each:
LB $00 → should be $01
LB $01 → should be $02
; etc.
```

- [ ] ถ้า LB $02 ได้ $08 → A1/A2 short ใน RAM address wiring

### Clock Sweep (Timing Qualification)

รัน Golden Bring-up ที่ความถี่ต่าง ๆ บันทึกผล. เริ่มจาก slow/safe แล้วค่อยเพิ่ม:

| Clock | Result | Notes |
|:-----:|:------:|-------|
| 100-tick push switch | | One pulse per press, no skipped T-state |
| 50 kHz | | Slow electronic clock sanity check |
| 1 MHz | | Official target |
| 2 MHz | | Breadboard achievable |
| 5 MHz | | PCB only (experimental) |

- [ ] บันทึก max frequency ที่ pass → เป็น spec ของเครื่องตัวนี้
- [ ] บันทึกผลจริงและปัญหาที่เจอใน `07_real_build_timing_log.md`
- [ ] ถ้า fail ที่ 2 MHz → ตรวจ: long wires, missing bypass cap, stray capacitance

### Physical Signoff Boundary

Mark the build physically signed off only after the real hardware has evidence
for all of these:

- Stable VCC/GND at the farthest chips.
- Clean reset and one-pulse single-step clock.
- No observed IBUS/DBUS bus fight during fetch, immediate, load, and store.
- ROM and RAM select lines never drive DBUS together.
- Golden Bring-up passes at 1 MHz.
- Burn-in holds the pass loop for 1 hour.
- Clock sweep result is recorded for this exact build.

Python simulation, Verilog tests, and the Components virtual checker are
required pre-checks, but they are not a replacement for these bench results.

---

## ขั้นที่ 13: IRQ (U31)

**ต่ออะไร**: U31 (74HC74), /IRQ pin, EI decode (U33 gate 2)

**v1.0: Polling IRQ** (ไม่มี hardware vector)

U31 ทำหน้าที่ latch สัญญาณ /IRQ เพื่อให้เห็น event ด้วย LED/probe. CPU core
ไม่ auto-read `IRQ_FF`, ไม่ auto-jump, และไม่มี vector fetch. ถ้าจะให้ software
poll จริง ต้อง map peripheral/IRQ status ผ่าน I/O slot เพิ่มเติม; สำหรับ v1.0
build แนะนำให้ poll input device โดยตรงผ่าน I/O slot:
```asm
; Main loop:
loop:
  ; ... do work ...
  ; poll input/status via I/O slot
  ; if event visible in software → branch to handler
  J loop

handler:
  ; DI is inert in v1.0; avoid EI unless software wants IE=1
  ; ... handle event ...
  EI                    ; re-enable
  J loop               ; return to main
```

**ทดสอบ**:
- [ ] EI → IE LED = ON
- [ ] กดปุ่ม /IRQ ค้าง LOW → IRQ_FF ยังไม่ latch จาก edge นี้
- [ ] ปล่อยปุ่มให้กลับ HIGH → IRQ_FF LED = ON (latch จับที่ rising edge)
- [ ] กด clock 100+ ครั้ง → IRQ_FF ยัง ON (ยืนยัน latch ไม่ decay)
- [ ] DI → IE LED unchanged (no v1.0 hardware clear path)
- [ ] Reset → ทั้ง IE และ IRQ_FF = OFF

> 📌 **IRQ_FF clear mechanism (v1.0)**: Only /RST clears IRQ_FF.
> DI has no v1.0 hardware effect — IRQ_FF stays latched until next reset.
>
> **Practical impact**: IRQ is a one-shot "event detected" flag in v1.0.
> Software can use EI to set IE, but only reset clears IE and IRQ_FF in the 36-package build.
> For games/BASIC: poll input directly via I/O slot instead of relying on IRQ_FF re-arm.
>
> **Future small fix**: Route /SLOT2 write to U31 /CLR2 → software clear via `SB $20`.
> Hardware acknowledge/vector is a separate, unfrozen design.

**LED**: 1 ดวงบน IE (U31-5), 1 ดวงบน IRQ_FF (U31-9)

**FUTURE ONLY - DO NOT WIRE IN THE BASELINE**: hardware vector is not part of
v1.0. It requires PC mux, /PC_LD control, IRQ_ack, and clear logic. If this
is connected during the student build, the baseline tests and wiring guide no longer
match the hardware.

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
Pin 28:    /RD (NOT(T2) — informational only, not used by CPU core. For peripheral timing/debug.)
Pin 29:    /IRQ ← input จาก peripheral (ต่อ U31-11)
Pin 30:    /SLOT1 ← address decode ($FF1x)
Pin 31:    /SLOT2 ← address decode ($FF2x)
Pin 32:    T2 (U8-5)
Pin 33:    A15 duplicate จาก ABUS15 (U30-12)
Pin 34-38: reserved / NC
Pin 39:    VCC (+5V)
Pin 40:    GND
```

**ทดสอบ**:
- [ ] ต่อ Programmer board ผ่าน ribbon cable
- [ ] `python3 ../Programmer/tools/rv8flash.py -c` → "Connected"
- [ ] Flash test ROM → verify ด้วย `python3 ../Programmer/tools/rv8flash.py verify test.bin --base 0x0000`
- [ ] CLK บน bus pin 25 = oscillator (วัดด้วย probe)
- [ ] /RST บน bus pin 26 = HIGH ตอนปกติ, LOW ตอนกด reset
- [ ] /WR บน bus pin 27 = pulse LOW เฉพาะตอน STORE
- [ ] /IRQ bus pin 29 → กดแล้วปล่อยปุ่ม → IRQ_FF LED ON (software polls, no auto-jump in v1.0)

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
| DBUS = $00 ตลอด | ROM /CE ไม่ active, /OE/WR_DIR ผิด |
| AC ไม่เปลี่ยน | ACC_CLK ไม่ pulse, AC_WR=0 |
| Jump ไม่ทำงาน | /PC_LD ค้าง HIGH, Page Reg ผิด |
| RAM write ไม่ได้ | /WE ไม่ pulse, A15 ไม่ใช่ 1 |
| Ring counter ค้าง | Inverter ต่อผิด, /CLR ค้าง LOW |
| ผลไม่คงที่ (intermittent) | Floating HC input, loose wire, power noise |

---

## Floating Input Audit (ทำหลังต่อครบทุกชิป)

74HC ขาที่ไม่ได้ต่อ = ลอย = อาจ oscillate = intermittent failure

**ตรวจก่อนเปิดเครื่อง:**
- [ ] NAND/OR/XOR unused inputs → ต่อ VCC หรือ GND (ดูจาก wiring guide)
- [ ] Mux unused data inputs → ต่อ GND (ไม่กระทบถ้า SEL ไม่เลือก แต่ป้องกันเผื่อ)
- [ ] 74HC161 unused D-inputs (ถ้ามี) → ต่อ GND
- [ ] ตรวจ U24, U25, U26, U27, U28, U33 ว่า gate ที่ไม่ได้ใช้ → input ต่อ VCC/GND

> 📌 อาการ floating input: ทำงานถูก 90% ของเวลา แต่พลาดเป็นระยะ ๆ
> ถ้า single-step ผ่านแต่ full-speed fail → สงสัย floating input ก่อน

---

## Trace Sheet (สำหรับ Single-step Debug)

พิมพ์ตารางนี้แล้วกรอกด้วยมือขณะกดปุ่ม clock:

```
| Clock | Phase | PC   | IRH | IRL | AC | Z | PG | DP | Notes |
|-------|-------|------|-----|-----|----|----|----|----|-------|
|   1   | T0    |      |     |     |    |    |    |    |       |
|   2   | T1    |      |     |     |    |    |    |    |       |
|   3   | T2    |      |     |     |    |    |    |    |       |
|   4   | T0    |      |     |     |    |    |    |    |       |
|   5   | T1    |      |     |     |    |    |    |    |       |
|   6   | T2    |      |     |     |    |    |    |    |       |
|   7   | T0    |      |     |     |    |    |    |    |       |
|   8   | T1    |      |     |     |    |    |    |    |       |
|   9   | T2    |      |     |     |    |    |    |    |       |
|  10   | T0    |      |     |     |    |    |    |    |       |
|  11   | T1    |      |     |     |    |    |    |    |       |
|  12   | T2    |      |     |     |    |    |    |    |       |
```

> เทียบกับ Golden Trace ใน `02_instruction_trace.md` — ถ้าไม่ตรง = bug

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

---

## Appendix: Golden Bring-up Program

One program tests ~80% of the CPU. If this passes, only edge cases remain.

```asm
; RV8-GR Golden Bring-up — flash at $0000
; Tests: DP, PG, LI, SB, LB, SUBI, Z flag, BEQ, J, RAM, ROM

    SETDP $80       ; $0000: $40 $80 — DP = RAM page
    SETPG $00       ; $0002: $20 $00 — PG = page 0
    LI $55          ; $0004: $30 $55 — AC = $55
    SB $00          ; $0006: $04 $00 — RAM[$8000] = $55
    LB $00          ; $0008: $38 $00 — AC = RAM[$8000] = $55
    SUBI $55        ; $000A: $90 $55 — AC = $00, Z = 1
    BEQ pass        ; $000C: $02 $10 — Z=1 → jump to $0010
    J fail          ; $000E: $01 $12 — should not reach

pass:
    J pass          ; $0010: $01 $10 — ✅ success (LED: PC=$0010 loop)

fail:
    J fail          ; $0012: $01 $12 — ❌ failure (LED: PC=$0012 loop)
```

**ROM image (20 bytes):**
```
0000: 40 80 20 00 30 55 04 00 38 00 90 55 02 10 01 12
0010: 01 10 01 12
```

**Expected result**: PC halts at $0010 (pass). If PC=$0012 → one of the tested functions failed.

> 📌 Verified against ISA Freeze v1.0 (absolute addressing, BEQ target = low byte of {PG, operand}).

> 📌 IRQ_FF is architectural state. In v1.0 it clears only by /RST. It does NOT auto-clear like typical MCU interrupt flags.

**What this tests:**

| Function | Instruction | Pass if |
|----------|-------------|---------|
| Data Page | SETDP $80 | SB/LB access RAM |
| Page Reg | SETPG $00 | BEQ/J land correctly |
| Load Immediate | LI $55 | AC = $55 |
| Store | SB $00 | RAM[$8000] written |
| Load | LB $00 | AC reads back $55 |
| Subtract | SUBI $55 | AC = $00 |
| Z flag | — | Z = 1 after AC=0 |
| Branch | BEQ pass | Taken when Z=1 |
| Jump | J pass | PC = $0010 |
| RAM | SB + LB | Read = Write |
