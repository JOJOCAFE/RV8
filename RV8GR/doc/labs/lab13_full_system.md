# Lab 13: Full System — รันโปรแกรมแรก!

**เป้าหมาย**: ต่อทุกชิปเข้าด้วยกัน ทดสอบด้วย single-step แล้วรันที่ full speed

---

## ความรู้พื้นฐาน

ถึงตอนนี้ทุกโมดูลถูกทดสอบแยกแล้ว:
- PC counter + address mux (Lab 03-04)
- ROM + bus buffer + IR (Lab 05-06)
- ALU + AC (Lab 07-08)
- Z flag (Lab 09)
- Branch/Jump (Lab 10)
- Page register (Lab 11)
- RAM + data page (Lab 12)

**Lab นี้**: เชื่อมทุกส่วนเข้าด้วยกัน (ถ้ายังไม่ได้) แล้วรันโปรแกรมจริง!

---

## อุปกรณ์

| ชิ้น | ชื่อ | จำนวน |
|:----:|------|:-----:|
| 1 | Crystal oscillator 5 MHz | 1 |
| 2 | Crystal oscillator 1 MHz (สำรอง) | 1 |
| 3 | 74HC14 (Schmitt trigger, clock switch) | 1 |
| 4 | Slide switch (เลือก: ปุ่มกด / crystal) | 1 |
| 5 | LED สีเหลือง 3mm (AC display) | 8 |
| 6 | 330Ω resistor | 8 |

> ⚠️ **แนะนำ: เริ่มที่ 1 MHz ก่อน!**
>
> Breadboard มี stray capacitance สูง → propagation delay มากกว่า PCB
> Critical path (PC → mux → ROM → buffer → IR → decode → ALU → AC) ≈ 200-300ns
> - **1 MHz** (1000ns period): margin ~700ns → ปลอดภัยมาก ✅
> - **5 MHz** (200ns period): margin ~0ns → อาจไม่เสถียร ⚠️
>
> ถ้า 1 MHz PASS แล้วค่อยลอง 5 MHz
> ถ้า 5 MHz fail → ไม่ใช่ bug ในวงจร แค่ timing ไม่พอ

---

## วงจร

### เชื่อมต่อสุดท้าย

ตรวจสอบว่าสายเหล่านี้ต่อจากจริง (ไม่ใช่ temporary จาก lab ก่อน):

```
จาก Lab 06: U6 pin 1 (/OE)  ← /IRL_OE (U26-3)      [ไม่ใช่ GND แล้ว!]
จาก Lab 08: U9 pin 11 (CLK) ← ACC_CLK (U27-11)   [ไม่ใช่ปุ่มแล้ว!]
จาก Lab 08: U14 pin 1,19    ← /AC_BUF (U26-8)
จาก Lab 05: U7 pin 19 (/OE) ← BUF_OE_N (U24-12)   [ไม่ใช่ GND แล้ว!]
จาก Lab 05: U7 pin 1 (DIR)  ← WR_DIR (U28-8)        [ไม่ใช่ GND แล้ว!]
จาก Lab 03: U1-U4 pin 9 (/LD) ← /PC_LD (U26-11)
จาก Lab 03: U1 pin 7,10 (ENP,ENT) ← PC_INC (U25-6)
จาก Lab 03: U3-U4 D inputs ← U23 Q outputs (Page Reg)
จาก Lab 03: U1-U2 D inputs ← U6 Q outputs (IRL → jump target)
```

### Clock switch

```
Slide switch:
  position A → single-step button → debounce → CLK
  position B → crystal oscillator 5 MHz → CLK

ทั้ง 2 ผ่าน 74HC14 (Schmitt trigger) เพื่อ clean edge
```

---

## เตรียมโปรแกรม

### Test ROM: Verify ALL paths

```asm
; Flash to $0000:
; Test: LI, ADDI, SUBI, BEQ, J

$0000: $30    ; LI (MUX+AC_WR=1)
$0001: $10    ; AC = $10

$0002: $10    ; ADDI (AC_WR=1)
$0003: $05    ; AC = $10 + $05 = $15

$0004: $90    ; SUBI (AC_WR=1, SUB=1)
$0005: $15    ; AC = $15 - $15 = $00, Z=1

$0006: $02    ; BEQ (BR=1, SUB=0)
$0007: $0C    ; target: $000C (pass)

$0008: $01    ; J (JMP=1) — should NOT reach here
$0009: $0E    ; target: $000E (fail)

; --- should NOT reach $000A-$000B ---
$000A: $00    ; NOP
$000B: $00    ; NOP

; pass:
$000C: $30    ; LI
$000D: $AA    ; AC = $AA (success marker!)

; halt (loop forever):
$000E: $01    ; J
$000F: $0E    ; jump to self ($000E)
```

**Flash ด้วย programmer**:
```bash
python3 ../Programmer/tools/rv8flash.py program test_full.bin --base 0x0000
```

---

## ทดสอบ ✅

### Test 1: Single-step trace

ใช้ปุ่มกด clock ทีละครั้ง:

| Clock | Phase | PC | IR_H | IR_L | AC | Z | ถูก? |
|:-----:|:-----:|:--:|:----:|:----:|:--:|:-:|:----:|
| 1 | T0 | $0000 | $10 | — | $00 | 1 | ☐ |
| 2 | T1 | $0001 | $10 | $10 | $00 | 1 | ☐ |
| 3 | T2 | $0002 | $10 | $10 | **$10** | 0 | ☐ |
| 4 | T0 | $0002 | $10 | — | $10 | 0 | ☐ |
| 5 | T1 | $0003 | $10 | $05 | $10 | 0 | ☐ |
| 6 | T2 | $0004 | $10 | $05 | **$15** | 0 | ☐ |
| 7 | T0 | $0004 | $90 | — | $15 | 0 | ☐ |
| 8 | T1 | $0005 | $90 | $15 | $15 | 0 | ☐ |
| 9 | T2 | $0006 | $90 | $15 | **$00** | **1** | ☐ |
| 10 | T0 | $0006 | $02 | — | $00 | 1 | ☐ |
| 11 | T1 | $0007 | $02 | $0C | $00 | 1 | ☐ |
| 12 | T2 | **$000C** | $02 | $0C | $00 | 1 | ☐ |
| 13 | T0 | $000C | $10 | — | $00 | 1 | ☐ |
| 14 | T1 | $000D | $10 | $AA | $00 | 1 | ☐ |
| 15 | T2 | $000E | $10 | $AA | **$AA** | 0 | ☐ |

**ผลลัพธ์สุดท้าย: AC = $AA (10101010) → PASS!** ✅

ถ้า AC = $FF หรือค่าอื่น → มีบั๊ก ดู LED ที่ไหนเพี้ยน

### Test 2: Low speed (555 timer ~1 Hz)

- [ ] สลับ clock switch ไป 555 timer
- [ ] ดู AC LED เปลี่ยนตาม pattern: $00→$10→$15→$00→$AA→ค้าง
- [ ] PC LED (ถ้ามี) หยุดที่ $000E (loop)

### Test 3: Full speed (5 MHz crystal)

- [ ] สลับ clock switch ไป crystal
- [ ] AC LED ค้างที่ $AA (10101010) → ทุก LED สลับติด-ดับ
- [ ] จับ IC ทุกตัว 10 วินาที → ไม่ร้อน
- [ ] กด reset → CPU เริ่มใหม่ → AC กลับเป็น $AA (ถูกต้อง)

### Test 4: Count program

Flash count ROM:
```
$0000: $30  ; LI $00
$0001: $00
$0002: $10  ; ADDI $01
$0003: $01
$0004: $01  ; J $02
$0005: $02
```

- [ ] Full speed → AC LED = counter (bit 7 กระพริบ ~6.5 Hz)
- [ ] ความถี่ LED AC7 ≈ 5M ÷ 3 cycles ÷ 256 ÷ 2 ≈ **3.3 Hz** — ช้าพอเห็น!

---

## System Validation Programs (เพิ่มเติม)

### Test 5: RAM Read/Write

```asm
; Write $55 to RAM, read back, verify
$0000: $30  ; LI $55
$0001: $55
$0002: $40  ; SETDP $80
$0003: $80
$0004: $04  ; SB $10 → RAM[$8010] = $55
$0005: $10
$0006: $30  ; LI $00 → AC = 0 (clear)
$0007: $00
$0008: $38  ; LB $10 → AC = RAM[$8010] = $55?
$0009: $10
$000A: $90  ; SUBI $55 → AC = $55 - $55 = $00, Z=1
$000B: $55
$000C: $02  ; BEQ $10 (pass)
$000D: $10
$000E: $01  ; J $0E (fail — halt)
$000F: $0E
; pass:
$0010: $30  ; LI $BB (RAM pass marker)
$0011: $BB
$0012: $01  ; J $12 (halt)
$0013: $12
```

- [ ] AC = $BB (10111011) → RAM read/write PASS!

### Test 6: Page Register Jump

```asm
; Jump to $1000 then back to $0000
$0000: $20  ; SETPG $10
$0001: $10
$0002: $01  ; J $00 → PC = $1000
$0003: $00

; At $1000:
$1000: $20  ; SETPG $00
$1001: $00
$1002: $01  ; J $06 → PC = $0006
$1003: $06

; Back at $0006:
$0006: $30  ; LI $CC (page jump pass marker)
$0007: $CC
$0008: $01  ; J $08 (halt)
$0009: $08
```

- [ ] AC = $CC (11001100) → Page Register Jump PASS!

### Test 7: Long Run Counter (stability test)

```asm
$0000: $30  ; LI $00
$0001: $00
$0002: $10  ; ADDI $01 (loop)
$0003: $01
$0004: $01  ; J $02
$0005: $02
```

- [ ] ปล่อยรัน 1-2 ชั่วโมง
- [ ] AC LED bit 7 ต้องกระพริบสม่ำเสมอ (ไม่หยุด ไม่กระตุก)
- [ ] ถ้ากระตุก/หยุด → timing issue → ลด clock เป็น 1 MHz

> 💡 **ถ้าผ่าน Test 7 ที่ full speed ได้ 1 ชั่วโมง**
>
> = CPU รันได้ ~6 ล้าน instructions โดยไม่ error
> = ถือว่าเสถียรในระดับ "ใช้งานจริง" ไม่ใช่แค่ demo!

---

## ถ้าไม่ถูก?

| อาการ | สาเหตุ | แก้ |
|-------|--------|-----|
| AC ไม่เปลี่ยนเลย | ACC_CLK ค้าง HIGH | เช็ค U27 gate D |
| PC ไม่ jump ที่ BEQ | Z=0 หรือ Z_match ผิด | เช็ค U21-5, U28-3 |
| AC ได้ค่าผิด (ไม่ใช่ $AA) | ALU ผิด หรือ bus path ผิด | เช็ค BUF_OE_N / WR_DIR |
| IC ร้อนมาก! | Bus fight | ถอด clock ทันที! เช็ค /OE ทุกตัว |
| Crystal ไม่ oscillate | load cap ไม่มี | เพิ่ม 22pF ×2 ที่ crystal |
| นับข้ามค่า | bounce (ปุ่มกดเท่านั้น) | ใช้ 74HC14 debounce |
| T0/T1/T2 overlap (logic probe) | ring counter ผิด | เช็ค U8 connections, ดูว่าไม่มี 2 phase HIGH พร้อมกัน |

---

## ซอฟต์แวร์จำลอง

```bash
cd RV8GR/sim/sim_lab
python3 lab13_full_system.py
```

---

## Chip Count (34 logic + ROM + RAM = 35):

| Lab | ชิป | หน้าที่ |
|:---:|------|---------|
| 01 | — | ไฟเลี้ยง + clock |
| 02 | U8, U24 | Ring counter |
| 03 | U1-U4 | PC counter |
| 04 | U15-U16, U29-U30 | Address mux |
| 05 | ROM, U7 | ROM + bus buffer |
| 06 | U5, U6 | IR latch |
| 07 | U10-U13 | ALU (adder + XOR) |
| 08 | U9, U14, U17-U20 | AC + mux |
| 09 | U21, U22 | Z flag |
| 10 | U25-U28 | Branch/Jump logic |
| 11 | U23 | Page register |
| 12 | RAM, U32, U33 | RAM + data page |
| **รวม** | **34 logic + ROM + RAM** | **= 36 packages** |

---

## สิ่งที่ได้

- ✅ CPU ทำงานครบ: fetch → decode → execute
- ✅ รันโปรแกรมจาก ROM ได้ (ALU + Branch + Jump)
- ✅ RAM read/write ผ่าน data page
- ✅ Page register jump 16-bit address
- ✅ Long-run stability (counter test)
- ✅ **คุณสร้าง CPU ที่ทำงานจริงได้แล้ว!** 🏆

### ก่อนไป Lab 14 — Checklist

| Test | Speed | ผล | ✓ |
|:----:|:-----:|:--:|:-:|
| 1 | Single-step | AC=$AA | ☐ |
| 4 | 1 MHz | Counter กระพริบ | ☐ |
| 5 | 1 MHz | AC=$BB (RAM) | ☐ |
| 6 | 1 MHz | AC=$CC (Page) | ☐ |
| 7 | 1 MHz | 1hr stable | ☐ |
| 7 | 5 MHz | 1hr stable (optional) | ☐ |

**ผ่าน Test 1-7 ที่ 1 MHz → ไป Lab 14!** 🎉
