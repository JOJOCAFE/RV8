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

ส่วนนี้เขียนเป็นภาษาไทยสำหรับน้อง ๆ ม.ต้น

---

### เป้าหมาย

บอร์ด Programmer ทำหน้าที่อย่างเดียว: **เขียนโปรแกรมลงชิป ROM (AT28C256)**

เหมือนก๊อปไฟล์ลง USB แต่เป็นชิป ROM แทน!

---

### อุปกรณ์

| ชิ้น | ชื่อ | หน้าที่ | จำนวน | ราคาประมาณ |
|:----:|------|---------|:-----:|:----------:|
| 1 | ESP32-WROOM-32 | สมองบอร์ด ต่อ USB กับคอม | 1 | ~฿140 |
| 2 | TXS0108E (โมดูล 8 ช่อง) | แปลงไฟ 3.3V↔5V | 2 | ~฿70 |
| 3 | 74HC595 (shift register) | ส่ง address ไปหา ROM | 2 | ~฿20 |
| 4 | ซ็อกเก็ต ZIF 28 ขา | เสียบชิป ROM | 1 | ~฿50 |
| 5 | ตัวเก็บประจุ 100nF | กรองไฟ | 4 | ~฿4 |

**รวม ~฿285**

---

### วิธีใช้

1. ถอดชิป ROM ออกจากบอร์ด CPU
2. เสียบชิป ROM เข้า Programmer (ซ็อกเก็ต ZIF)
3. ต่อสาย USB เข้าคอม
4. เปิด Terminal พิมพ์:
   
5. รอจนขึ้น "Done" ✅
6. ถอดชิป ROM กลับไปเสียบบอร์ด CPU
7. เปิดไฟ CPU → ทำงาน!

---

### การต่อวงจร (ตาม schematic.md)

```
ESP32 → TXS0108E #1 → 74HC595 x2 → ROM Address (A0-A14)
                     → ROM Control (/CE, /OE, /WE)
ESP32 → TXS0108E #2 → ROM Data (D0-D7)
```

ดูรายละเอียดขาต่อขาที่ไฟล์ `schematic.md`

---

*เขียนสำหรับน้อง ๆ ม.ต้น — ถ้าติดตรงไหนถามพี่ได้เลย!*
