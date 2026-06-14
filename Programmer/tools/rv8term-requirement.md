# rv8term.py — Requirements

**Purpose**: Terminal bridge — send/receive bytes between PC and RV8 CPU via I/O slot
**Platform**: Python 3.6+ with `pyserial`
**Usage**: `python3 rv8term.py [options]`

---

## VirtualESP32 Board Definition

```python
class VirtualESP32:
    NAME = "RV8 Programmer ESP32"
    BAUD_RATE = 115200
    TIMEOUT = 5

    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7, TXS#2 → Bus pin 17-24
    SR_DATA_PIN = 23   # SER
    SR_CLK_PIN = 18    # SRCLK
    SR_LATCH_PIN = 19  # RCLK

    # Control signals (via TXS0108E #1 → RV8-Bus)
    PIN_nRST = 4       # → Bus pin 26 (/RST)
    PIN_nWR = 16       # → Bus pin 27 (/WR)
    PIN_nRD_O = 17     # → Bus pin 28 (/RD, output in PROG mode)

    # Input-only pins (from RV8-Bus)
    PIN_nSLOT = 34     # ← Bus pin 30 (/SLOT1)
    PIN_nRD = 35       # ← Bus pin 28 (/RD sense)
    PIN_nWR_S = 36     # ← Bus pin 27 (/WR sense)
    PIN_MODE = 39      # PROG/RUN switch
```

---

## CLI Options

| Option | Description |
|--------|-------------|
| `-h` | Show help |
| `-pl` | List available ports |
| `-p N` | Use port N (default: 0) |
| `-c` | Check connection and exit |
| `-b N` | Baud rate (default: 115200) |
| `-d` | Debug (show serial traffic) |
| `-q` | Quiet (no banner) |

---

## Behavior

1. Open serial port (2s boot delay + buffer drain)
2. Send `?`, expect `Connected\n` (verify programmer alive)
3. If `-c`: print status and exit
4. Enter terminal mode: bidirectional byte bridge (PC ↔ CPU via /SLOT1)
5. Ctrl+C to exit

---

## Output Examples

```bash
$ python3 rv8term.py -c
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected

$ python3 rv8term.py
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
RV8 BASIC 1.0
> 

$ python3 rv8term.py -b 9600
Port: /dev/ttyUSB0 @ 9600 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
```

---

## Error Handling

| Exit | Meaning |
|:----:|---------|
| 0 | Normal exit (Ctrl+C) |
| 1 | Error (no port, not responding, timeout) |

---

## Boot Delay

ESP32 resets when serial port opens (DTR). Tool waits 2s + drains buffer before sending `?`.

---

## File Structure

```
tools/
├── rv8term.py              # Implementation
├── test_rv8term.py         # 15 tests (all passing)
└── rv8term-requirement.md  # This document
```

---

## Checklist ✅

- [x] VirtualESP32 at top (bus-based pins)
- [x] SerialPort context manager with boot delay
- [x] Connection check (`?` → `Connected\n`)
- [x] `-c` option (check and exit)
- [x] Port + baud display before operations
- [x] Terminal mode (bidirectional bridge)
- [x] Ctrl+C to exit cleanly
- [x] Follows rv8flash.py patterns
- [x] 15/15 tests passing
