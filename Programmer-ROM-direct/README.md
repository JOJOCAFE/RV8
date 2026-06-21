# Programmer Board — ESP32-WROOM-32

**Purpose**: Flash AT28C256 ROM via RV8-Bus for all RV8 family CPUs
**Connection**: ESP32 ←USB→ PC ←ribbon→ RV8-Bus (40-pin) on target board

---

## Overview

```
PC ←──USB──→ [ESP32-WROOM-32] ←→ [TXS0108E ×2] ←→ [74HC595 ×2] ──→ RV8-Bus (40-pin)
                                                                         │
                                                                    CPU Board
                                                                  (ROM + RAM on board)
```

Programmer connects to the CPU board via the shared **RV8-Bus** (40-pin).
In PROG mode: holds /RST low, drives Address + Data + /WR to write ROM on the CPU board.
In RUN mode: releases bus, acts as UART bridge via /SLOT1.

---

## How to Use

1. Connect Programmer to CPU board via 40-pin ribbon cable (RV8-Bus)
2. Connect ESP32 to PC via USB
3. Flip switch to PROG
4. Flash: `python3 rv8flash.py -w program.bin`
5. Verify: `python3 rv8flash.py -v program.bin`
6. Flip switch to RUN → CPU boots, use `rv8term.py` for terminal

---

## ESP32-WROOM-32 Pin Mapping

### Data Bus (D[7:0]) — bidirectional, via TXS0108E #2 → RV8-Bus

| ESP32 GPIO | Signal | RV8-Bus Pin |
|:----------:|--------|:-----------:|
| GPIO 13 | D0 | pin 17 |
| GPIO 12 | D1 | pin 18 |
| GPIO 14 | D2 | pin 19 |
| GPIO 27 | D3 | pin 20 |
| GPIO 26 | D4 | pin 21 |
| GPIO 25 | D5 | pin 22 |
| GPIO 33 | D6 | pin 23 |
| GPIO 32 | D7 | pin 24 |

### Address (A[14:0]) — via 74HC595 ×2 shift register → RV8-Bus

| ESP32 GPIO | Function | 74HC595 Pin |
|:----------:|----------|:-----------:|
| GPIO 23 | SR_DATA (SER) | #1 pin 14 |
| GPIO 18 | SR_CLK (SRCLK) | Both pin 11 |
| GPIO 19 | SR_LATCH (RCLK) | Both pin 12 |

74HC595 #1 outputs Q0-Q7 → RV8-Bus pin 1-8 (A0-A7)
74HC595 #2 outputs Q0-Q6 → RV8-Bus pin 9-15 (A8-A14)

### Control Signals — via TXS0108E #1 → RV8-Bus

| ESP32 GPIO | Signal | RV8-Bus Pin |
|:----------:|--------|:-----------:|
| GPIO 4 | /RST | pin 26 |
| GPIO 16 | /WR | pin 27 |
| GPIO 17 | /RD | pin 28 (output in PROG, released in RUN) |

### Input Signals — from RV8-Bus (RUN mode)

| ESP32 GPIO | Signal | RV8-Bus Pin |
|:----------:|--------|:-----------:|
| GPIO 34 | /SLOT1 | pin 30 |
| GPIO 35 | /RD (sense) | pin 28 |
| GPIO 36 | /WR (sense) | pin 27 |
| GPIO 39 | MODE switch | — |

### Summary

| Function | ESP32 GPIOs | Count |
|----------|:-----------:|:-----:|
| D[7:0] | 13,12,14,27,26,25,33,32 | 8 |
| Shift Reg | 23,18,19 | 3 |
| Control out | 4,16,17 | 3 |
| Bus sense | 34,35,36 | 3 |
| Mode switch | 39 | 1 |
| **Total** | | **18 GPIO** |

---

## PROG Mode — ROM Flash Sequence

```
1. ESP32 holds /RST=LOW (CPU stops, releases bus)
2. A15=0 via shift register → ROM /CE active (address decode on CPU board)
3. PC sends 'F' + len_hi + len_lo over USB-serial
4. ESP32 replies 'K' (ACK), waits for data
5. For each byte:
   a. Shift out A[14:0] via 74HC595 ×2 (16 bits, MSB first, A15=0)
   b. Pulse RCLK to latch address
   c. Set D[7:0] (data) on bus
   d. Pulse /WR LOW for 1µs (bus pin 27 → ROM /WE)
   e. Page write delay (10ms at 64-byte boundary)
6. ESP32 sends 'D' (done) to PC
7. Verify: PC sends 'V', ESP32 pulses /RD LOW per byte → ROM outputs data
```

---

## Usage Scenarios

### Scenario A: ROM only (bare AT28C256 on breadboard)

```
[Programmer] ──ribbon──→ [Bus connector] → ROM wired to bus pins
```

| Signal | Programmer drives | ROM sees |
|--------|-------------------|----------|
| A[14:0] | 74HC595 → bus pin 1-15 | Address |
| A15=0 | 74HC595 bit15 = 0 | `/CE` = LOW (selected) |
| D[7:0] | ESP32 → bus pin 17-24 | Data in/out |
| `/WR` | GPIO 16 → bus pin 27 | `/WE` pulse (write) |
| `/RD` | GPIO 17 → bus pin 28 | `/OE` active (read) |
| `/RST` | GPIO 4 → bus pin 26 | Not connected (ignored) |

**Procedure:**
```bash
python3 rv8flash.py -w program.bin   # flash
python3 rv8flash.py -v program.bin   # verify
```

No CPU needed. Programmer controls all ROM signals directly via bus. ✅

---

### Scenario B: Full CPU board (RV8-GR, RV8, RV8-R)

```
[Programmer] ──ribbon──→ [RV8-Bus] → CPU board (CPU + ROM + RAM)
```

| Signal | Programmer drives | What happens |
|--------|-------------------|--------------|
| `/RST` | GPIO 4 = LOW | **CPU stops**, tri-states bus |
| A[14:0] | 74HC595 → bus | Reaches ROM through CPU board wiring |
| A15=0 | 74HC595 bit15 = 0 | CPU board decode: ROM `/CE` = LOW |
| D[7:0] | ESP32 → bus | Through CPU board buffer (tri-stated) to ROM |
| `/WR` | GPIO 16 → bus pin 27 | Routed to ROM `/WE` |
| `/RD` | GPIO 17 → bus pin 28 | Routed to ROM `/OE` |

**Procedure:**
```bash
# PROG mode (switch to PROG)
python3 rv8flash.py -w program.bin   # flash
python3 rv8flash.py -v program.bin   # verify

# RUN mode (switch to RUN)
python3 rv8term.py                   # terminal bridge
```

`/RST=LOW` is critical — without it, CPU fights Programmer for the bus. ✅

---

### Same firmware, same commands

Both scenarios use identical firmware and Python tools.
The only difference: Scenario B needs `/RST` to stop the CPU.

---


---

## Parts List

| Part | Qty | Notes |
|------|:---:|-------|
| ESP32-WROOM-32 | 1 | Main controller |✅ |   |
| TXS0108E module (8-ch) | 2 | Level shifters (control + data) |✅ |   |
| 74HC595 | 2 | Shift register (address A0-A14) | ✅ |   |
| 40-pin IDC connector | 1 | RV8-Bus connector |- |   |
| 40-pin ribbon cable | 1 | Connect to CPU board |- |   |
| SPDT switch | 1 | PROG/RUN mode select |waiting |   |
| 100nF capacitor | 4 | Bypass caps |waiting |   |
| USB cable (micro-B) | 1 | PC to ESP32 |- |   |
| zif socket wide | 1 | for 28C256 ROM |waiting |   |


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
# Output: Port: /dev/ttyUSB0 @ 115200 baud
#         Programmer: Connected

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
python3 Programmer/tools/rv8term.py -c                      # check only
python3 Programmer/tools/rv8term.py -p 0 -d                 # debug mode
```

### Options

| Option | Description |
|--------|-------------|
| `-h` | Show help |
| `-pl` | List ports |
| `-p N` | Use port N (default: 0) |
| `-c` | Check connection (rv8flash + rv8term) |
| `-w FILE` | Write to ROM |
| `-r FILE` | Read from ROM |
| `-v FILE` | Verify ROM |
| `-d` | Debug mode |
| `-q` | Quiet mode |
| `-t N` | Retry N times |
| `-R` | Reset CPU after flash |

---

## Compatibility

Works with any board that has AT28C256 on the RV8-Bus:

| Target | Scenario | Notes |
|--------|:--------:|-------|
| RV8-GR (33 chips) | B | Full CPU, /RST stops it |
| RV8 (27 chips) | B | Full CPU, /RST stops it |
| RV8-R (18 chips) | B | Full CPU, /RST stops it |
| Bare ROM on breadboard | A | No CPU, direct bus wiring |
| Any AT28C256 + bus connector | A | Wire A[14:0], D[7:0], /WR, /RD, /CE=A15 |

---

## Thai Version

ส่วนนี้เขียนเป็นภาษาไทยสำหรับน้อง ๆ ม.ต้น

---

### เป้าหมาย

บอร์ด Programmer ต่อเข้ากับ CPU board ผ่าน **RV8-Bus (40-pin)** เพื่อ:
- **PROG mode**: เขียนโปรแกรมลง ROM บน CPU board (ไม่ต้องถอดชิป!)
- **RUN mode**: เป็น Terminal bridge คุยกับ CPU ผ่าน I/O slot

---

### อุปกรณ์

| ชิ้น | ชื่อ | หน้าที่ | จำนวน | ราคาประมาณ |
|:----:|------|---------|:-----:|:----------:|
| 1 | ESP32-WROOM-32 | สมองบอร์ด ต่อ USB กับคอม | 1 | ~฿140 |
| 2 | TXS0108E (โมดูล 8 ช่อง) | แปลงไฟ 3.3V↔5V | 2 | ~฿70 |
| 3 | 74HC595 (shift register) | ส่ง address ออก bus | 2 | ~฿20 |
| 4 | IDC connector 40 pin | ต่อ RV8-Bus | 1 | ~฿15 |
| 5 | สายแพร 40 เส้น | เชื่อมไป CPU board | 1 | ~฿30 |
| 6 | ตัวเก็บประจุ 100nF | กรองไฟ | 4 | ~฿4 |
| 7 | สวิตช์ SPDT | เลือก PROG/RUN | 1 | ~฿5 |

**รวม ~฿285**

---

### วิธีใช้

1. ต่อสายแพร 40 เส้นจาก Programmer ไป CPU board (RV8-Bus)
2. ต่อสาย USB เข้าคอม
3. เลื่อนสวิตช์ไปที่ PROG
4. เปิด Terminal พิมพ์: `python3 rv8flash.py -w program.bin`
5. รอจนขึ้น "Done" ✅
6. เลื่อนสวิตช์ไปที่ RUN → CPU ทำงาน!
7. พิมพ์: `python3 rv8term.py` เพื่อคุยกับ CPU

---

### การต่อวงจร (ตาม schematic.md)

```
ESP32 → TXS0108E #1 → 74HC595 x2 → RV8-Bus A[14:0]
                     → RV8-Bus /RST, /WR, /RD
ESP32 → TXS0108E #2 → RV8-Bus D[7:0]
ESP32 ← RV8-Bus /SLOT1, /RD, /WR (ฟังอย่างเดียว, RUN mode)
```

ดูรายละเอียดขาต่อขาที่ไฟล์ `schematic.md`

---

*เขียนสำหรับน้อง ๆ ม.ต้น — ถ้าติดตรงไหนถามพี่ได้เลย!*
