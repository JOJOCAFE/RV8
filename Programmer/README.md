# Programmer Board — ESP32-WROOM-32

**Purpose**: Flash AT28C256 ROM for all RV8 family CPUs
**Connection**: ESP32 ←USB→ PC, ROM inserted in ZIF socket

---

## Overview

```
PC ←──USB──→ [ESP32-WROOM-32] ←→ [TXS0108E ×2] ←→ [74HC595 ×2] ←→ [AT28C256 ROM]
```

Standalone ROM programmer. Insert ROM chip, flash, put back in CPU board.

---

## How to Use

1. Remove ROM (AT28C256) from CPU board
2. Insert into Programmer board socket
3. Connect ESP32 to PC via USB
4. Flash: `python3 rv8flash.py -w program.bin`
5. Verify: `python3 rv8flash.py -v program.bin`
6. Remove ROM, insert back into CPU board
7. Power on CPU → runs program

---

## ESP32-WROOM-32 Pin Mapping

### Data Bus (D[7:0]) — bidirectional, via TXS0108E #2

| ESP32 GPIO | Signal | ROM Pin |
|:----------:|--------|:-------:|
| GPIO 13 | D0 | I/O 0 (pin 11) |
| GPIO 12 | D1 | I/O 1 (pin 12) |
| GPIO 14 | D2 | I/O 2 (pin 13) |
| GPIO 27 | D3 | I/O 3 (pin 15) |
| GPIO 26 | D4 | I/O 4 (pin 16) |
| GPIO 25 | D5 | I/O 5 (pin 17) |
| GPIO 33 | D6 | I/O 6 (pin 18) |
| GPIO 32 | D7 | I/O 7 (pin 19) |

### Address (A[14:0]) — via 74HC595 ×2 shift register, through TXS0108E #1

| ESP32 GPIO | Function | 74HC595 Pin |
|:----------:|----------|:-----------:|
| GPIO 23 | SR_DATA (SER) | #1 pin 14 |
| GPIO 18 | SR_CLK (SRCLK) | Both pin 11 |
| GPIO 19 | SR_LATCH (RCLK) | Both pin 12 |

74HC595 #1 outputs Q0-Q7 → ROM A0-A7
74HC595 #2 outputs Q0-Q6 → ROM A8-A14 (daisy-chained from #1 Q7S → #2 SER)

### Control Signals — via TXS0108E #1

| ESP32 GPIO | Signal | ROM Pin |
|:----------:|--------|:-------:|
| GPIO 4 | /CE | pin 20 |
| GPIO 16 | /OE | pin 22 |
| GPIO 17 | /WE | pin 27 |

### Summary

| Function | ESP32 GPIOs | Count |
|----------|:-----------:|:-----:|
| D[7:0] | 13,12,14,27,26,25,33,32 | 8 |
| Shift Reg | 23,18,19 | 3 |
| ROM Control | 4,16,17 | 3 |
| **Total** | | **14 GPIO** |

---

## PROG Mode — ROM Flash Sequence

```
1. ESP32 sets /CE=LOW, /OE=HIGH
2. PC sends data over USB-serial
3. For each byte:
   a. Shift out A[14:0] via 74HC595 (2 bytes, MSB first)
   b. Pulse RCLK to latch address
   c. Set D[7:0] (data)
   d. Pulse /WE LOW for 1µs
   e. Wait for write completion (10ms delay)
4. Verify: read back all bytes, compare
5. ESP32 sends "OK\n" to PC
```

---


---

## Parts List

| Part | Qty | Notes |
|------|:---:|-------|
| ESP32-WROOM-32 | 1 | Main controller |
| TXS0108E module (8-ch) | 2 | Level shifters (control + data) |
| 74HC595 | 2 | Shift register (address A0-A14) |
| 28-pin ZIF socket | 1 | ROM socket (easy insert/remove) |
| 100nF capacitor | 4 | Bypass caps |
| USB cable (micro-B) | 1 | PC to ESP32 |

---

## PC Software

### Tools (in `tools/` directory)

| Tool | Purpose | File |
|------|---------|------|
| rv8flash.py | Flash ROM | rv8flash.py |
| rv8ram-boot.py | Upload to RAM via bootloader | rv8ram-boot.py |
| rv8term.py | Terminal bridge | rv8term.py |

### Workflow (assemble → flash → run → interact)

```bash
# 1. List available ports
python3 Programmer/tools/rv8flash.py -pl

# 2. Assemble your program (from RV8GR/tools)
python3 RV8GR/tools/rv8gr_asm.py hello.asm -f bin -o hello.bin

# 3. Flip switch to PROG → flash ROM
python3 Programmer/tools/rv8flash.py -w hello.bin
# Output: "Flashing hello.bin (xxx bytes)... [██████████] 100% Done."

# 4. Flip switch to RUN → CPU boots
python3 Programmer/tools/rv8term.py
# Output: "Hello World!" from CPU
# Type to send input to CPU. Ctrl+C to exit.
```

### Quick Reference

```bash
# List ports
python3 Programmer/tools/rv8flash.py -pl

# Check connection
python3 Programmer/tools/rv8flash.py -c

# Flash ROM (PROG mode)
python3 Programmer/tools/rv8flash.py -w program.bin          # auto port 0
python3 Programmer/tools/rv8flash.py -p 0 -w program.bin    # explicit port

# Read ROM
python3 Programmer/tools/rv8flash.py -r backup.bin

# Verify ROM
python3 Programmer/tools/rv8flash.py -v program.bin

# Upload to RAM (via bootloader)
python3 Programmer/tools/rv8ram-boot.py program.bin

# Terminal (RUN mode)
python3 Programmer/tools/rv8term.py
python3 Programmer/tools/rv8term.py -p 0 -d    # debug mode
```

### Options

| Option | Description |
|--------|-------------|
| `-h` | Show help |
| `-pl` | List ports |
| `-p N` | Use port N (default: 0) |
| `-c` | Check connection |
| `-w FILE` | Write to ROM |
| `-r FILE` | Read from ROM |
| `-v FILE` | Verify ROM |
| `-d` | Debug mode |
| `-q` | Quiet mode |
| `-t N` | Retry N times |
| `-R` | Reset CPU after flash |

---

## Compatibility

Works with any board using AT28C256 (28-pin DIP, 32KB):

| CPU Board | Flash ROM |
|-----------|:---------:|
| RV8-GR (33 chips) | ✅ |
| RV8 (27 chips) | ✅ |
| RV8-R (18 chips) | ✅ |
| Any AT28C256 project | ✅ |

---

## Thai Version

ส่วนนี้เขียนเป็นภาษาไทยสำหรับน้อง ๆ ม.ต้น ที่อยากสร้างบอร์ด Programmer ให้ CPU RV8

---

### 1. เป้าหมาย

บอร์ด Programmer ทำหน้าที่ 2 อย่าง:

1. **โหมด PROG** — เขียนโปรแกรมลง ROM (เหมือนก๊อปไฟล์ลง USB แต่เป็นชิป)
2. **โหมด RUN** — เป็น "หน้าจอ" ให้ CPU คุยกับคอมพิวเตอร์ผ่านสาย USB (พิมพ์ตัวอักษรไป-กลับ)

สลับโหมดด้วยสวิตช์ตัวเดียว ง่ายมาก!

---

### 2. อุปกรณ์

| ชิ้น | ชื่อ | หน้าที่ | จำนวน | ราคาประมาณ |
|:----:|------|---------|:-----:|:----------:|
| 1 | ESP32-WROOM-32 (30 ขา) | สมองของบอร์ด — ต่อ USB กับคอม, ควบคุมทุกอย่าง | 1 | ~฿140 |
| 2 | TXS0108E (โมดูล 8 ช่อง) | แปลงไฟ 3.3V↔5V ให้ ESP32 คุยกับ CPU ได้ | 3 | ~฿105 |
| 3 | 74HC595 (shift register) | ส่ง address สูง A8-A14 ไปหา ROM (ใช้สายแค่ 3 เส้น) | 1 | ~฿10 |
| 4 | สาย IDC 40 พิน + หัวต่อ | เชื่อมบอร์ด Programmer กับบอร์ด CPU | 1 | ~฿70 |
| 5 | สวิตช์ SPDT (3 ขา) | เลือก PROG หรือ RUN | 1 | ~฿15 |
| 6 | ตัวต้านทาน 10kΩ | pull-up สำหรับ GPIO 0 (ป้องกัน boot ผิดโหมด) | 1 | ~฿1 |
| 7 | ตัวเก็บประจุ 100nF | กรองไฟให้ TXS0108E (ติดข้าง ๆ ขา VCC) | 6 | ~฿6 |

**รวม ~฿350** (ไม่รวมบอร์ด CPU)

---

### 3. ขั้นตอนต่อวงจร

ต่อทีละส่วน ทดสอบแต่ละขั้นก่อนไปขั้นถัดไป

#### ขั้นที่ 1 — จ่ายไฟ

| จาก | ไป | หมายเหตุ |
|------|-----|----------|
| ESP32 VIN (5V จาก USB) | Bus pin 39 (VCC) | จ่ายไฟ 5V ให้บอร์ด CPU |
| ESP32 3.3V | TXS0108E ทุกตัว ขา VCCA | ฝั่งแรงดันต่ำ |
| Bus pin 39 (5V) | TXS0108E ทุกตัว ขา VCCB | ฝั่งแรงดันสูง |
| ESP32 3.3V | 74HC595 ขา 16 (VCC) | จ่ายไฟ shift register |
| ESP32 GND | Bus pin 40 (GND) | กราวด์ร่วม |
| TXS0108E ขา OE | ต่อเข้า VCCA (3.3V) | เปิดใช้งานตลอด |

> ⚡ ติด C 100nF ข้างขา VCCA และ VCCB ของ TXS0108E ทุกตัว (6 ตัว)

#### ขั้นที่ 2 — Data Bus (D0-D7)

| ESP32 GPIO | → TXS0108E #1 ช่อง | → Bus Pin | สัญญาณ |
|:----------:|:-----------------:|:---------:|--------|
| 32 | A1/B1 | 17 | D0 |
| 33 | A2/B2 | 18 | D1 |
| 25 | A3/B3 | 19 | D2 |
| 26 | A4/B4 | 20 | D3 |
| 27 | A5/B5 | 21 | D4 |
| 14 | A6/B6 | 22 | D5 |
| 12 | A7/B7 | 23 | D6 |
| 13 | A8/B8 | 24 | D7 |

#### ขั้นที่ 3 — Address Bus ต่ำ (A0-A7)

| ESP32 GPIO | → TXS0108E #2 ช่อง | → Bus Pin | สัญญาณ |
|:----------:|:-----------------:|:---------:|--------|
| 15 | A1/B1 | 1 | A0 |
| 2 | A2/B2 | 2 | A1 |
| 4 | A3/B3 | 3 | A2 |
| 16 | A4/B4 | 4 | A3 |
| 17 | A5/B5 | 5 | A4 |
| 5 | A6/B6 | 6 | A5 |
| 18 | A7/B7 | 7 | A6 |
| 19 | A8/B8 | 8 | A7 |

#### ขั้นที่ 4 — Shift Register (74HC595) สำหรับ A8-A14

| 74HC595 ขา | ต่อไปที่ | หมายเหตุ |
|:-----------:|----------|----------|
| 14 (SER) | ESP32 GPIO 23 | ข้อมูลเข้า |
| 11 (SRCLK) | ESP32 GPIO 18 | นาฬิกาเลื่อนบิต |
| 12 (RCLK) | ESP32 GPIO 5 | สั่งให้ output ออก |
| 10 (/SRCLR) | ต่อเข้า 3.3V | ไม่ clear (ค้างไว้) |
| 13 (/OE) | ต่อเข้า GND | เปิด output ตลอด |
| 16 (VCC) | 3.3V | ไฟเลี้ยง |
| 8 (GND) | GND | กราวด์ |
| 15 (Q0) | TXS0108E #3 A1 → Bus pin 9 | A8 |
| 1 (Q1) | TXS0108E #3 A2 → Bus pin 10 | A9 |
| 2 (Q2) | TXS0108E #3 A3 → Bus pin 11 | A10 |
| 3 (Q3) | TXS0108E #3 A4 → Bus pin 12 | A11 |
| 4 (Q4) | TXS0108E #3 A5 → Bus pin 13 | A12 |
| 5 (Q5) | TXS0108E #3 A6 → Bus pin 14 | A13 |
| 6 (Q6) | TXS0108E #3 A7 → Bus pin 15 | A14 |

#### ขั้นที่ 5 — สัญญาณควบคุม

| จาก | ไป | หน้าที่ |
|------|-----|---------|
| ESP32 GPIO 0 | TXS0108E #3 A8/B8 → Bus pin 28 | /RST (รีเซ็ต CPU) |
| ESP32 GPIO 21 | สายตรงไปขา /WE ของ ROM | เขียน ROM (PROG mode) |

#### ขั้นที่ 6 — สวิตช์ PROG/RUN

| ขาสวิตช์ | ต่อไปที่ | หมายเหตุ |
|:---------:|----------|----------|
| ขากลาง (COM) | ESP32 GPIO 0 | อ่านค่าสวิตช์ |
| ขาซ้าย (PROG) | GND | กด PROG = LOW = CPU หยุด |
| ขาขวา (RUN) | 3.3V | กด RUN = HIGH = CPU ทำงาน |

> 💡 ต่อตัวต้านทาน 10kΩ จาก GPIO 0 ไป 3.3V (pull-up) เพื่อให้ ESP32 บูตได้ปกติ

---

### 4. วิธีใช้

#### โหมด PROG — เขียนโปรแกรมลง ROM

1. เลื่อนสวิตช์ไปตำแหน่ง **PROG**
2. ต่อสาย USB จากคอมเข้า ESP32
3. เปิด Terminal แล้วพิมพ์:
   ```
   python3 rv8flash.py /dev/ttyUSB0 program.bin
   ```
4. รอจนขึ้น progress bar เต็ม ✅
5. เลื่อนสวิตช์ไป **RUN** — CPU จะเริ่มทำงานทันที

#### โหมด RUN — เป็นหน้าจอ Terminal

1. เลื่อนสวิตช์ไปตำแหน่ง **RUN**
2. เปิด Terminal แล้วพิมพ์:
   ```
   python3 rv8term.py /dev/ttyUSB0
   ```
3. ตอนนี้คุณพิมพ์อะไร CPU จะได้รับ, CPU ส่งอะไรมาจะขึ้นจอ
4. กด **Ctrl+C** เพื่อออก

#### สรุปง่าย ๆ

| ทำอะไร | สวิตช์ | คำสั่ง |
|--------|:------:|--------|
| เขียน ROM | PROG | `python3 rv8flash.py <port> <file>` |
| คุยกับ CPU | RUN | `python3 rv8term.py <port>` |

---

### 5. ทดสอบ

ทำตามลำดับ ✅ ทุกข้อก่อนไปข้อถัดไป:

| # | ทดสอบ | วิธีเช็ค | ผ่าน? |
|:-:|--------|----------|:-----:|
| 1 | ไฟเข้า ESP32 | ต่อ USB → ไฟ LED บน ESP32 ติด | ☐ |
| 2 | ไฟ 5V ถึง Bus | วัดไฟ Bus pin 39-40 ได้ ~5V | ☐ |
| 3 | ไฟ 3.3V ถึง TXS0108E | วัดขา VCCA ได้ ~3.3V ทุกตัว | ☐ |
| 4 | สวิตช์ทำงาน | PROG → วัด GPIO 0 ได้ 0V, RUN → ได้ 3.3V | ☐ |
| 5 | /RST ถึง Bus | PROG → วัด Bus pin 28 ได้ ~0V, RUN → ได้ ~5V | ☐ |
| 6 | Flash ROM | รัน rv8flash.py → ขึ้น "Done" ไม่มี error | ☐ |
| 7 | Verify ROM | ถอด ROM ไปอ่านด้วย TL866 → ข้อมูลตรง | ☐ |
| 8 | CPU บูต | สวิตช์ RUN → CPU เริ่มทำงาน (ดูจาก LED หรือ terminal) | ☐ |
| 9 | Terminal ส่งได้ | พิมพ์ใน rv8term → CPU ได้รับ (echo กลับมา) | ☐ |
| 10 | Terminal รับได้ | CPU ส่งข้อความ → ขึ้นจอใน rv8term | ☐ |

> 🎉 ถ้าผ่านครบ 10 ข้อ = บอร์ด Programmer ใช้งานได้สมบูรณ์!

---

*เขียนสำหรับน้อง ๆ ม.ต้น — ถ้าติดตรงไหนถามพี่ได้เลย!*
