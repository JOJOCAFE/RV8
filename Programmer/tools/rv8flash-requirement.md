# rv8flash.py — Requirements

**Purpose**: Flash, read, and verify AT28C256 ROM via ESP32 Programmer on RV8-Bus
**Platform**: Python 3.6+ with `pyserial`
**Usage**: `python3 rv8flash.py [options]`

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
| `-w FILE` | Write FILE to ROM |
| `-r FILE` | Read ROM to FILE |
| `-v FILE` | Verify ROM against FILE |
| `-d` | Debug (show serial traffic) |
| `-q` | Quiet (minimal output) |
| `-t N` | Retry N times (default: 3) |
| `-R` | Pulse /RST after flash |

---

## Serial Protocol

| PC → ESP32 | ESP32 → PC | Notes |
|------------|------------|-------|
| `?` | `Connected\n` | Connection check |
| `F` + len_hi + len_lo | `K\n` (ACK), receive data, `D\n` | Flash |
| `V` | 32768 raw bytes | Read ROM |
| `R` | `K\n` | Pulse /RST |

---

## Output Examples

```bash
$ python3 rv8flash.py -c
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected

$ python3 rv8flash.py -w testrom.bin
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Flashing testrom.bin (32768 bytes)...
[██████████] 100%
Done. 32768 bytes written.

$ python3 rv8flash.py -v testrom.bin
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Verifying...
[██████████] 100%
Verified
```

---

## Error Handling

| Exit | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | Error (message printed to stderr) |

Errors: no port, programmer not responding, timeout, file not found, file too large (>32KB), verify mismatch.

---

## Boot Delay

ESP32 resets when serial port opens (DTR). Tool waits 2s + drains buffer before sending commands.

---

## File Structure

```
tools/
├── rv8flash.py              # Implementation
├── test_rv8flash.py         # 16 tests (all passing)
└── rv8flash-requirement.md  # This document
```

---

## Checklist ✅

- [x] VirtualESP32 at top (bus-based pins)
- [x] SerialPort context manager with boot delay
- [x] Connection check (`?` → `Connected\n`)
- [x] Flash (`F` + len + data → `K\n` + `D\n`)
- [x] Read (`V` → 32768 bytes)
- [x] Verify (read + compare)
- [x] Port + baud display before operations
- [x] 16/16 tests passing
