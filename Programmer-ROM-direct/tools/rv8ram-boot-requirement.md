# rv8ram-boot.py — Requirements

**Purpose**: Upload program to RV8 CPU RAM via bootloader (faster iteration than ROM flash)
**Platform**: Python 3.6+ with `pyserial`
**Usage**: `python3 rv8ram-boot.py [options] file.bin`

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
| `-d` | Debug (show serial traffic) |
| `-q` | Quiet (minimal output) |
| `-t N` | Retry N times (default: 3) |
| `-R` | Pulse /RST after upload |
| `file` | Binary file to upload (positional) |

---

## Bootloader Protocol

| Direction | Data | Notes |
|-----------|------|-------|
| Boot → PC | `R` | Ready signal (bootloader running) |
| PC → Boot | len_hi + len_lo | 2-byte big-endian length |
| PC → Boot | data[len] | One byte at a time, ~6ms delay |
| Boot → PC | `D` | Done (program loaded) |

**Max size**: 15871 bytes (RAM $C000-$FDFF)

---

## Output Examples

```bash
$ python3 rv8ram-boot.py hello.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
[██████████] 100%
Done. Program loaded and running.

$ python3 rv8ram-boot.py -p 0 -R test.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 1024 bytes...
[██████████] 100%
Done. 1024 bytes uploaded.
Auto-resetting CPU...
```

---

## Error Handling

| Exit | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | Error (timeout, file too large, port not found) |

---

## File Structure

```
tools/
├── rv8ram-boot.py              # Implementation
├── rv8ram-boot-requirement.md  # This document
```
