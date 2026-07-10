# RV8-GR Hardware Labs — สร้าง CPU จากศูนย์

**14 Lab sheets สำหรับน้อง ม.ต้น — ต่อวงจรทีละขั้น จนได้ CPU ที่ทำงานจริง**

---

## วิธีใช้

1. ทำทีละ Lab **ตามลำดับ** (ห้ามข้าม!)
2. ทุก Lab มี: อุปกรณ์ → ต่อวงจร → ทดสอบ → ✅ ผ่านแล้วค่อยไป Lab ถัดไป
3. ใช้ single-step clock (กดปุ่ม) ทดสอบ ก่อนใส่ oscillator module
4. ดู LED เพื่อเช็คว่าถูก

ใช้คู่กับเอกสารหลักเหล่านี้:

| เอกสาร | ใช้ทำอะไร |
|--------|-----------|
| `../04_understand_by_module.md` | เข้าใจว่าแต่ละ module ทำหน้าที่อะไร |
| `../05_debug_plan.md` | ไล่ debug ตามจุดวัดและอาการเสีย |
| `../06_kicad_modules.md` | เทียบ Lab กับแผ่น KiCad/module |
| `../07_real_build_timing_log.md` | บันทึกผลวัดไฟ, clock, edge, bus race, propagation delay |
| `../build_plan/01_student_incremental_build_plan.md` | แผนครู/พี่เลี้ยงสำหรับ build ทีละ stage |

## ข้อตกลงของ baseline

- สร้างเฉพาะ baseline: 34 logic chips + ROM + RAM.
- ไม่มี microcode.
- ไม่มี hardware IRQ vector.
- IRQ เป็น polling latch เท่านั้น.
- ถ้าต่อสายทดลองชั่วคราวใน Lab ใด ต้องถอดออกก่อนต่อ Lab ถัดไป.

ถ้าอยากเพิ่ม feature เช่น hardware vector, ROM bank, RETI ให้ทำหลังจาก Lab
14 ผ่านแล้วเท่านั้น และต้องแยกเป็น upgrade document.

---

## Lab List

| Lab | ชื่อ | ชิป | ทดสอบอะไร |
|:---:|------|:---:|-----------|
| 01 | [ไฟเลี้ยง + นาฬิกา](lab01_power_clock.md) | — | VCC/GND, กดปุ่ม clock |
| 02 | [Ring Counter](lab02_ring_counter.md) | U8, U24 | T0→T1→T2 วน |
| 03 | [Program Counter](lab03_pc_counter.md) | U1-U4 | นับ 0,1,2,3... |
| 04 | [Address Mux](lab04_address_mux.md) | U15-U16, U29-U30 | เลือก PC หรือ IRL |
| 05 | [ROM อ่านค่า](lab05_rom_buffer.md) | ROM, U7 | อ่าน byte จาก ROM |
| 06 | [IR Latch](lab06_ir_latch.md) | U5, U6, U34 | จำคำสั่ง + เตรียม immediate buffer |
| 07 | [Adder/Subtractor](lab07_alu.md) | U10-U13 | บวก ลบ 8 บิต |
| 08 | [AC + Mux = Full ALU](lab08_accumulator.md) | U17-U20, U9, U14 | AC + XOR op |
| 09 | [Z Flag](lab09_z_flag.md) | U21, U22 | ตรวจจับ AC=0 |
| 10 | [Branch/Jump](lab10_branch_jump.md) | U24-U28 | J, BEQ, BNE |
| 11 | [Page Register](lab11_page_register.md) | U23 | SETPG + jump 16 บิต |
| 12 | [RAM + Data Page](lab12_ram_datapage.md) | 62256, U32, U33 | SB, LB |
| 13 | [Full System](lab13_full_system.md) | ทุกตัว | รันโปรแกรมจริง! |
| 14 | [IRQ + RV8-Bus](lab14_irq_bus.md) | U31, 40-pin IDC | Interrupt + bus |

---

## Chip Checklist (34 logic + ROM + RAM = 36 packages)

| Lab | ชิป | หน้าที่ |
|:---:|------|---------|
| 01 | — | ไฟเลี้ยง + clock |
| 02 | U8 (74HC164), U24 (74HC04) | Ring counter T0/T1/T2 |
| 03 | U1-U4 (74HC161 ×4) | PC counter 16-bit |
| 04 | U15-U16, U29-U30 (74HC157 ×4) | Address mux |
| 05 | AT28C256 (ROM), U7 (74HC245) | Program ROM + bus buffer |
| 06 | U5, U6 (74HC574 ×2), U34 (74HC541) | IR latch + IRL immediate buffer |
| 07 | U10-U11 (74HC283 ×2), U12-U13 (74HC86 ×2) | Adder + B-invert |
| 08 | U9 (74HC574), U14 (74HC541), U17-U20 (74HC157 ×4) | AC + mux (Full ALU) |
| 09 | U21 (74HC74), U22 (74HC688) | Z flag |
| 10 | U25 (74HC32), U26-U27 (74HC00 ×2), U28 (74HC86) | Branch/Jump logic |
| 11 | U23 (74HC574) | Page register |
| 12 | 62256-70 (RAM), U32 (74HC574), U33 (74HC21) | RAM + data page |
| 13 | — (connect all) | Full integration |
| 14 | U31 (74HC74) | IRQ + RV8-Bus |

---

## ความสัมพันธ์กับ Debug Plan

Labs 01-14 ตรงกับ **ขั้นที่ 1-14** ใน `../05_debug_plan.md` ทุกประการ
และ map เข้ากับ module ใน `../06_kicad_modules.md`.

หลัง Lab 13-14 ผ่านบนบอร์ดจริง ให้บันทึกหลักฐาน timing/voltage ใน
`../07_real_build_timing_log.md` ก่อนถือว่า physical build ผ่านสมบูรณ์.

---

## เสร็จแล้วทำอะไรต่อ?

1. 🧪 ทดสอบทุก 18 คำสั่งด้วย test ROM
2. 📺 ต่อ 7-segment / LED array ที่ I/O slot
3. 🎮 เขียนเกม (นับเลข, ไฟวิ่ง, reaction timer)
4. 💻 ต่อ UART ผ่าน /SLOT1
5. รัน BASIC interpreter
