# Lab 14: IRQ + RV8-Bus — อินเตอร์รัปต์ + บัสภายนอก

**เป้าหมาย**: ต่อ U31 (74HC74, IRQ/IE flip-flops) + 40-pin IDC connector (RV8-Bus) ให้ CPU รับ interrupt และต่ออุปกรณ์ภายนอกได้

---

## ความรู้พื้นฐาน

- **U31 FF-A (IE flag)**: Interrupt Enable — EI เปิด, DI ปิด
- **U31 FF-B (IRQ latch)**: จับสัญญาณ /IRQ ขาลง → จำไว้จนกว่า CPU จะตอบ
- **เมื่อ /IRQ active**: IRQ_FF latches = 1 (software polls, no auto-jump in v1.0)
- **RV8-Bus (40-pin)**: connector ส่งสัญญาณออกให้ programmer, peripheral, expansion

> ⚠️ **IRQ v1.0 — ข้อจำกัดสำคัญ**
>
> **ไม่มี RETI**: ISR return address ต้อง save ด้วย software ก่อน EI
> (ไม่มี hardware stack สำหรับ PC)
>
> **ไม่มี nested interrupt**: IRQ_ack clear IE อัตโนมัติ → ต้อง EI ใหม่ใน ISR
>
> **ใช้สำหรับ**: event handler แบบ one-shot (เช่น อ่าน input, set flag)
> หรือ periodic timer ที่ jump ไป known address ที่กำหนดไว้ล่วงหน้า
>
> v2.0 (อนาคต): hardware save-PC to RAM → ISR return ได้จริง

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | 74HC74 (U31, IRQ flip-flops) | 1 |
| 2 | IDC 40-pin connector (2×20) | 1 |
| 3 | Push button (จำลอง /IRQ) | 1 |
| 4 | 10kΩ resistor (pull-up /IRQ) | 1 |
| 5 | LED สีแดง 3mm | 2 |
| 6 | 330Ω resistor | 2 |
| 7 | 100nF capacitor | 1 |

---

## วงจร

### Pinout: 74HC74 (U31)

```
        ┌───U───┐
/CLR1 1 │       │ 14 VCC
   D1 2 │       │ 13 /CLR2
 CLK1 3 │  74   │ 12 D2
/PR1  4 │       │ 11 CLK2
  Q1  5 │       │ 10 /PR2
 /Q1  6 │       │  9 Q2
 GND  7 │       │  8 /Q2
        └───────┘
```

### การต่อสาย — U31 (IRQ)

```
U31 ไฟเลี้ยง: pin 14=VCC, pin 7=GND, 100nF คร่อม VCC-GND

FF-A (IE flag — Interrupt Enable):
  pin 1 (/CLR1) ← /RST (reset clears IE → interrupts disabled at boot)
  pin 2 (D1) → VCC (D=1, so CLK↑ sets IE=1)
  pin 3 (CLK1) ← EI_decode
    [EI_decode = T2 AND specific opcode pattern for EI]
    [สำหรับ lab: ใช้ปุ่มกดจำลอง EI]
  pin 4 (/PR1) → VCC (ไม่ preset)
  pin 5 (Q1) → IE flag → LED + IRQ logic
  pin 6 (/Q1) → NC

FF-B (IRQ latch):
  pin 8 (/CLR2) ← /RST (clear on reset → IRQ_FF=0 at boot)
  pin 9 (D2) → VCC (D=1, so CLK↑ latches IRQ)
  pin 10(CLK2) ← /IRQ input (latch on rising edge = device releases /IRQ)
  pin 11(/PR2) → VCC
  pin 12(Q2) → IRQ_FF → LED (software polls this)
  pin 13(/Q2) → NC
```

> 💡 **v1.0: Software Polling — ไม่มี hardware vector**
>
> U31 เป็น latch เท่านั้น — software poll IRQ_FF แล้ว branch เอง
> ไม่มี "force PC to $FF00" ใน v1.0 (ต้อง +2 chips สำหรับ v1.1)
>
> **Wiring Guide (full)**: /CLR2 ← IRQ_ack signal
> ```
> IRQ_ack = T2 AND IE AND IRQ_FF AND NOT(PC_LOAD_COND)
> ```
> เมื่อ CPU acknowledge → clear IRQ_FF + clear IE อัตโนมัติ
> → PC force $FF00, ISR เริ่มทำงาน, interrupt disabled จนกว่า EI ใหม่

/IRQ input:
  10kΩ pull-up ← VCC
  push button → GND (กดค้าง = /IRQ LOW, ปล่อย = rising edge → IRQ_FF latches!)

LED:
  U31-5 (IE) → 330Ω → LED → GND   [IE=1: LED ติด = interrupts enabled]
  U31-12(IRQ_FF) → 330Ω → LED → GND [IRQ latched: LED ติด]

DI (disable interrupts):
  [DI clears IE → U31 /CLR1 pulse LOW]
  [v1.0: ใช้ปุ่มกดแยก หรือ decode จาก opcode]
```

### RV8-Bus (40-pin IDC connector)

```
ต่อสาย CPU → IDC connector:

Pin  1: A0  ← U15-4        Pin  2: A1  ← U15-7
Pin  3: A2  ← U15-9        Pin  4: A3  ← U15-12
Pin  5: A4  ← U16-4        Pin  6: A5  ← U16-7
Pin  7: A6  ← U16-9        Pin  8: A7  ← U16-12
Pin  9: A8  ← U29-4        Pin 10: A9  ← U29-7
Pin 11: A10 ← U29-9        Pin 12: A11 ← U29-12
Pin 13: A12 ← U30-4        Pin 14: A13 ← U30-7
Pin 15: A14 ← U30-9        Pin 16: A15 ← U30-12
Pin 17: D0  ↔ DBUS         Pin 18: D1  ↔ DBUS
Pin 19: D2  ↔ DBUS         Pin 20: D3  ↔ DBUS
Pin 21: D4  ↔ DBUS         Pin 22: D5  ↔ DBUS
Pin 23: D6  ↔ DBUS         Pin 24: D7  ↔ DBUS
Pin 25: CLK ← oscillator   Pin 26: /RST ← reset circuit
Pin 27: /WR ← /AC_BUF (U26-8)
Pin 28: /RD ← GND (always read when /CE active; or NOT(T2))
Pin 29: /IRQ → U31-10 (input from peripheral)
Pin 30: /SLOT1 ← address decode ($FF1x)
Pin 31: /SLOT2 ← address decode ($FF2x)
Pin 32: T2 ← U8-5
Pin 33-38: NC (reserved)
Pin 39: VCC (+5V)
Pin 40: GND
```

---

## ทดสอบ ✅

### Test 1: IE flag (EI/DI)

| ขั้น | ทำอะไร | IE LED | IRQ LED | ถูก? |
|:----:|--------|:------:|:-------:|:----:|
| 1 | Reset | ดับ (IE=0) | ดับ | ☐ |
| 2 | กดปุ่ม EI (หรือ execute EI opcode) | ติด (IE=1) | ดับ | ☐ |
| 3 | กดปุ่ม DI | ดับ (IE=0) | ดับ | ☐ |

### Test 2: IRQ latch

| ขั้น | ทำอะไร | IRQ LED | ถูก? |
|:----:|--------|:-------:|:----:|
| 1 | IE=0, กดปุ่ม /IRQ | ติด (IRQ latched) | ☐ |
| 2 | แต่ CPU ไม่ jump (IE=0) | PC นับปกติ | ☐ |

> 📌 **v1.0: IRQ_FF cleared only by /RST!**
> กดปุ่ม /IRQ → IRQ_FF=1 → ค้างจนกว่าจะ reset
> v1.1 fix: Route /SLOT2 write → U31 /CLR2 (software clear via SB $20)

### Test 2B: IRQ_FF Sticky Verification
- [ ] กด /IRQ → IRQ_FF LED ON
- [ ] ปล่อยปุ่ม → IRQ_FF LED ยังคง ON (sticky!)
- [ ] กด clock 100+ ครั้ง → IRQ_FF ยัง ON
- [ ] กด Reset → IRQ_FF LED ดับ (only /RST clears it)

### Test 3: IRQ fires (IE=1 + /IRQ)

> ⚠️ **Test 3 ใช้ได้เฉพาะ v1.1 hardware vector (+2 chips)**
> v1.0 (33 chips): IRQ_FF เป็น latch เท่านั้น — software poll แล้ว branch เอง
> ถ้าสร้าง v1.0: ข้าม Test 3 → ทดสอบแค่ Test 1 + Test 2 + Test 4

Flash main program into ROM + pre-load ISR into RAM:
```
; Main program at $0000 (ROM — flash ด้วย programmer):
$0000: $30  ; LI $00  (AC=0)
$0001: $00
$0002: $08  ; EI (enable interrupt)
$0003: $00  ; (operand, ignored)
$0004: $10  ; ADDI $01  (loop: count up)
$0005: $01
$0006: $01  ; J $04
$0007: $04

; ISR at $FF00 (RAM — ต้อง pre-load ก่อน run!):
; ใช้ programmer เขียน RAM address $FF00-$FF03:
$FF00: $30  ; LI $FF  (marker: we got here!)
$FF01: $FF
$FF02: $01  ; J $02  (loop forever in ISR)
$FF03: $02
```

> ⚠️ **ISR อยู่ใน RAM ไม่ใช่ ROM!**
>
> Memory map: $FF00 = RAM (A15=1)
> ต้อง pre-load ISR code ลง RAM ก่อนรัน:
> - ทำผ่าน programmer (เขียน RAM ขณะ /RST=LOW)
> - หรือให้ boot code ใน ROM เขียน ISR ลง RAM เอง (ผ่าน SETDP $FF + SB)

| ขั้น | ทำอะไร | PC | AC | ถูก? |
|:----:|--------|:--:|:--:|:----:|
| 1 | Run main (counting) | $000x | $01,$02... | ☐ |
| 2 | กดปุ่ม /IRQ | jumps! | — | ☐ |
| 3 | PC = $FF00 (ISR!) | $FF00 | — | ☐ |
| 4 | Execute LI $FF | $FF02 | **$FF** | ☐ |

### Test 4: RV8-Bus signals

| Bus Pin | สัญญาณ | ทดสอบ | คาดหวัง | ถูก? |
|:-------:|--------|-------|---------|:----:|
| 25 | CLK | probe / LED | กระพริบ (full speed) | ☐ |
| 26 | /RST | กด reset | LOW แล้วกลับ HIGH | ☐ |
| 27 | /WR | execute SB | pulse LOW 1 cycle | ☐ |
| 29 | /IRQ | กดปุ่ม IRQ | LOW → CPU jumps | ☐ |

### Test 5: Programmer via bus

- [ ] ต่อ Programmer board ผ่าน ribbon cable
- [ ] `python3 rv8flash.py -c` → "Connected" ✅
- [ ] `python3 rv8flash.py -v test.bin --base 0x0000` → verify pass ✅

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| IE ไม่เปลี่ยน | EI decode ไม่ pulse CLK | เช็ค U31-3 |
| IRQ LED ไม่ติดเมื่อกด | /IRQ ไม่ถึง U31-10 | เช็ค pull-up + button |
| CPU ไม่ jump เมื่อ IRQ | IE=0 หรือ logic ไม่ AND | เช็ค IE × IRQ_FF → PC force |
| Bus pin ไม่มีสัญญาณ | สายไม่ถึง connector | ใช้ multimeter ⌀ continuity |
| Programmer ไม่เชื่อม | CPU conflict กับ bus | ต้อง hold CPU reset ก่อน flash |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab14_irq_bus.py
```

---

## สิ่งที่ได้

- ✅ IRQ latch จับ interrupt request ได้
- ✅ IE flag ควบคุม enable/disable
- ✅ CPU jump ไป ISR เมื่อ interrupt เกิด
- ✅ RV8-Bus 40-pin ส่งสัญญาณออกถูกต้อง
- ✅ Programmer เชื่อมผ่าน bus ได้

---

## ขั้นตอนถัดไป

1. 🧪 ทดสอบทุก 18 คำสั่ง (ใช้ test ROM จาก assembler)
2. 📺 ต่อ LED array / 7-segment ที่ I/O slot
3. 🎮 เขียนเกมง่ายๆ (นับเลข, ไฟวิ่ง, reaction timer)
4. 💻 ต่อ UART ผ่าน /SLOT1 เพื่อ terminal
5. 🚀 ลอง BASIC interpreter!

**ยินดีด้วย! คุณสร้าง RV8-GR CPU สมบูรณ์แล้ว!** 🎉🎉🎉
