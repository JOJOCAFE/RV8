# Lab 14: IRQ + RV8-Bus — อินเตอร์รัปต์ + บัสภายนอก

**เป้าหมาย**: ต่อ U31 (74HC74, IRQ/IE flip-flops) + 40-pin IDC connector (RV8-Bus) ให้ CPU รับ interrupt และต่ออุปกรณ์ภายนอกได้

---

## ความรู้พื้นฐาน

- **U31 FF-A (IE flag)**: Interrupt Enable — EI เปิด, /RST ปิด (DI ไม่มีผลใน v1.0)
- **U31 FF-B (IRQ latch)**: /IRQ เป็น active-low; latch ตอนปล่อยสัญญาณกลับ HIGH (rising edge) → จำไว้จนกว่าจะ reset
- **เมื่อ /IRQ ถูกปล่อยกลับ HIGH**: IRQ_FF latches = 1 (software polls, no auto-jump in v1.0)
- **RV8-Bus (40-pin)**: connector ส่งสัญญาณออกให้ programmer, peripheral, expansion

> ⚠️ **IRQ v1.0 — ข้อจำกัดสำคัญ**
>
> **ไม่มี hardware vector/RETI**: PC ไม่กระโดดเองและไม่มี hardware stack สำหรับ PC
>
> **ไม่มี acknowledge อัตโนมัติ**: IE และ IRQ_FF ไม่ auto-clear เมื่อ software เห็น IRQ
>
> **ใช้สำหรับ**: event flag แบบ one-shot; software poll แล้ว branch เอง
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
  pin 8 (/Q2) → NC
  pin 9 (Q2) → IRQ_FF → LED (software polls this)
  pin 10(/PR2) → VCC
  pin 11(CLK2) ← /IRQ input (latch on rising edge = device releases /IRQ)
  pin 12(D2) → VCC (D=1, so CLK↑ latches IRQ)
  pin 13(/CLR2) ← /RST (clear on reset → IRQ_FF=0 at boot)
```

> 💡 **v1.0: Software Polling — ไม่มี hardware vector**
>
> U31 เป็น latch เท่านั้น — software poll IRQ_FF แล้ว branch เอง
> ไม่มี "force PC to $FF00" ใน v1.0 (hardware vector เป็น future/unfrozen)
>
> **Wiring Guide v1.0**: /CLR1 และ /CLR2 ต่อ /RST เท่านั้น
> ไม่มี IRQ_ack, ไม่มี PC force, ไม่มี auto-clear

/IRQ input:
  10kΩ pull-up ← VCC
  push button → GND (กดค้าง = /IRQ LOW, ปล่อย = rising edge → IRQ_FF latches!)

LED:
  U31-5 (IE) → 330Ω → LED → GND   [IE=1: LED ติด = interrupts enabled]
  U31-9 (IRQ_FF) → 330Ω → LED → GND [IRQ latched: LED ติด]

DI ($48):
  [v1.0: no hardware effect; IE clears only via /RST]
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
Pin 15: A14 ← ABUS14 (U30-9)  Pin 16: A15 ← ABUS15 (U30-12)
Pin 17: D0  ↔ DBUS0       Pin 18: D1  ↔ DBUS1
Pin 19: D2  ↔ DBUS2       Pin 20: D3  ↔ DBUS3
Pin 21: D4  ↔ DBUS4       Pin 22: D5  ↔ DBUS5
Pin 23: D6  ↔ DBUS6       Pin 24: D7  ↔ DBUS7
Pin 25: CLK ← oscillator   Pin 26: /RST ← reset circuit
Pin 27: /WR ← /AC_BUF (U26-8)
Pin 28: /RD ← GND (always read when /CE active; or NOT(T2))
Pin 29: /IRQ → U31-11 (input from peripheral)
Pin 30: /SLOT1 ← address decode ($FF1x)
Pin 31: /SLOT2 ← address decode ($FF2x)
Pin 32: T2 ← U8-5
Pin 33: A15 duplicate ← ABUS15 (U30-12)
Pin 34-38: NC (reserved)
Pin 39: VCC (+5V)
Pin 40: GND
```

---

## ทดสอบ ✅

### Test 1: IE flag (EI/reset)

| ขั้น | ทำอะไร | IE LED | IRQ LED | ถูก? |
|:----:|--------|:------:|:-------:|:----:|
| 1 | Reset | ดับ (IE=0) | ดับ | ☐ |
| 2 | กดปุ่ม EI (หรือ execute EI opcode) | ติด (IE=1) | ดับ | ☐ |
| 3 | Execute DI ($48) | ติดเหมือนเดิม (v1.0 inert) | ดับ | ☐ |
| 4 | Reset | ดับ (IE=0) | ดับ | ☐ |

### Test 2: IRQ latch

| ขั้น | ทำอะไร | IRQ LED | ถูก? |
|:----:|--------|:-------:|:----:|
| 1 | IE=0, กดปุ่ม /IRQ แล้วปล่อย | ติด (IRQ latched on release) | ☐ |
| 2 | CPU ไม่ jump (polling-only) | PC นับปกติ | ☐ |

> 📌 **v1.0: IRQ_FF cleared only by /RST!**
> กดปุ่ม /IRQ แล้วปล่อย → IRQ_FF=1 → ค้างจนกว่าจะ reset
> v1.1 fix: Route /SLOT2 write → U31 /CLR2 (software clear via SB $20)

### Test 2B: IRQ_FF Sticky Verification
- [ ] กด /IRQ ค้าง LOW → IRQ_FF LED ยังไม่ควรเปลี่ยนจาก edge นี้
- [ ] ปล่อยปุ่มให้กลับ HIGH → IRQ_FF LED ON และค้าง (sticky!)
- [ ] กด clock 100+ ครั้ง → IRQ_FF ยัง ON
- [ ] กด Reset → IRQ_FF LED ดับ (only /RST clears it)

### Test 3: IRQ visible to polling software (IE=1 + /IRQ)

Flash main program into ROM:
```
; Main program at $0000 (ROM):
$0000: $30  ; LI $00  (AC=0)
$0001: $00
$0002: $08  ; EI (enable interrupt)
$0003: $00  ; (operand, ignored)
$0004: $10  ; ADDI $01  (loop: count up)
$0005: $01
$0006: $01  ; J $04
$0007: $04
```

> v1.0 ไม่มี CPU-visible status register in the core wiring yet.
> Use the IRQ_FF LED or an external /SLOT peripheral to let software poll the latch.

| ขั้น | ทำอะไร | PC | AC | ถูก? |
|:----:|--------|:--:|:--:|:----:|
| 1 | Run main (counting) | $000x | $01,$02... | ☐ |
| 2 | กดปุ่ม /IRQ แล้วปล่อย | ยัง loop $0004-$0007 | นับต่อ | ☐ |
| 3 | IRQ_FF LED ติด | PC ไม่เปลี่ยนเพราะ IRQ | นับต่อ | ☐ |

### Test 4: RV8-Bus signals

| Bus Pin | สัญญาณ | ทดสอบ | คาดหวัง | ถูก? |
|:-------:|--------|-------|---------|:----:|
| 25 | CLK | probe / LED | กระพริบ (full speed) | ☐ |
| 26 | /RST | กด reset | LOW แล้วกลับ HIGH | ☐ |
| 27 | /WR | execute SB | pulse LOW 1 cycle | ☐ |
| 29 | /IRQ | กดแล้วปล่อยปุ่ม IRQ | LOW then rising edge → IRQ_FF LED latches | ☐ |

### Test 5: Programmer via bus

- [ ] ต่อ Programmer board ผ่าน ribbon cable
- [ ] `python3 /home/jo/Codex/Programmer/tools/rv8flash.py -c` → "Connected" ✅
- [ ] `python3 /home/jo/Codex/Programmer/tools/rv8flash.py verify test.bin --base 0x0000` → verify pass ✅

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| IE ไม่เปลี่ยน | EI decode ไม่ pulse CLK | เช็ค U31-3 |
| IRQ LED ไม่ติดหลังปล่อยปุ่ม | /IRQ ไม่ถึง U31-11 หรือไม่มี pull-up rising edge | เช็ค pull-up + button |
| CPU jump เมื่อ IRQ | เผลอต่อวงจร v1.1/vector | v1.0 ต้องไม่มี PC force path |
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
- ✅ CPU ไม่ jump เองเมื่อ interrupt เกิด; software ต้อง poll เอง
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
