# rv8term.py — Requirements Document

**Purpose**: Terminal program for RV8 CPU — send/receive bytes via I/O slot

**Platform**: Linux, WSL, Windows, macOS (Python 3.6+)

**Dependency**: `pyserial` (`pip install pyserial`)

**Usage**: `python3 rv8term.py [options]`

---

## Virtual ESP32 Board Definition

The program uses a `VirtualESP32` class to define pin mappings. Pin assignment is defined at the **top of the program** in a single location for easy modification.

### Pin Configuration (Header Section)

```python
# =============================================================================
# VIRTUAL ESP32 BOARD DEFINITION
# Edit these values to match your hardware wiring
# =============================================================================

class VirtualESP32:
    """Virtual ESP32 board with configurable pin assignments."""
    NAME = "RV8 Programmer ESP32"

    # Serial port settings
    BAUD_RATE = 115200
    TIMEOUT = 5  # seconds

    # Data bus D[7:0] — bidirectional (via TXS0108E #2)
    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7

    # Address via 74HC595 x2 shift register (via TXS0108E #1)
    SR_DATA_PIN = 23   # SER
    SR_CLK_PIN = 18    # SRCLK
    SR_LATCH_PIN = 19  # RCLK

    # Control signals (via TXS0108E #1 → RV8-Bus)
    PIN_nRST = 4       # → Bus pin 26 (/RST)
    PIN_nWR = 16       # → Bus pin 27 (/WR)
    PIN_nRD_O = 17     # → Bus pin 28 (/RD, output in PROG mode)

# Create global board instance
ESP32 = VirtualESP32()
```

### Supported Board Variations

| Board Variant | Data Pins | Notes |
|---------------|-----------|-------|
| Default | 13,12,14,27,26,25,33,32 | TXS0108E |

To use a different board, edit the `VirtualESP32` class values at the top of the program.

---

## Options Class (Reusable)

All options are handled by a single `Options` class for reusability.

```python
class Options:
    """Parsed command-line options."""
    def __init__(self):
        self.port_index = 0
        self.port_name = None
        self.help = False
        self.port_list = False
        self.check = False      # -c: check connection and exit
        self.baud = 115200     # -b, --baud
        self.no_echo = False    # --no-echo
        self.debug = False       # -d: show serial traffic
        self.auto_port = True   # use port 0 if not specified
        self.quiet = False     # -q: minimal output
        self.raw = False        # --raw: binary mode
```

---

## Command-Line Options Summary

| Short | Long | Args | Description |
|-------|------|------|-------------|
| -h | --help | none | Show help |
| -pl | --portlist | none | List available ports |
| -p | --port | N | Port index (0, 1, ...) |
| -c | --check | none | Check connection and exit |
| -b | --baud | N | Baud rate (default: 115200) |
| -d | --debug | none | Show serial traffic |
| -t | --timeout | N | Timeout in seconds (default: 0.1) |
| --no-echo | | none | Disable local echo |
| --raw | | none | Binary mode (no CR/LF translation) |
| -q | --quiet | none | Minimal output |

---

## Options Detail

### -h, --help
Show help message.

```bash
$ python3 rv8term.py -h
```

---

### -pl, --portlist
List available serial ports with indices.

```bash
$ python3 rv8term.py -pl
[0] ttyUSB0
[1] ttyUSB1

# Windows
[0] COM3
[1] COM4
```

---

### -p [no.], --port [no.]
Specify port by index number. If omitted, use port 0.

```bash
$ python3 rv8term.py -pl
[0] /dev/ttyUSB0

$ python3 rv8term.py -p 0
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
hello from RV8!
```

### -c, --check
Check if programmer is connected and exit.

```bash
$ python3 rv8term.py -c
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected

$ python3 rv8term.py -c
Port: /dev/ttyUSB0 @ 115200 baud
Error: Programmer not responding
```

| Index | Linux/WSL | Windows | macOS |
|:-----:|-----------|---------|-------|
| 0 | ttyUSB0 | COM3 | cu.usbserial-0001 |
| 1 | ttyUSB1 | COM4 | cu.usbserial-0002 |

---

### -b [baud], --baud [baud]
Set baud rate (default: 115200).

```bash
$ python3 rv8term.py -p 0 -b 9600
Terminal mode. Press Ctrl+C to exit.
```

**Common Rates**: 9600, 19200, 38400, 57600, 115200 (default)

---

### -t [N], --timeout [N]
Set serial timeout in seconds (default: 0.1).

```bash
$ python3 rv8term.py -p 0 -t 1
Terminal mode. Press Ctrl+C to exit.
```

---

### -d, --debug
Show serial traffic (verbose mode).

```bash
$ python3 rv8term.py -d
Terminal mode. Press Ctrl+C to exit.
[DEBUG] RX: 68 65 6C 6C 6F 0D 0A  (hello\r\n in hex)
A
[DEBUG] TX: 41  (A in hex)
```

**Debug Output Format**:
```
[DEBUG] RX: <bytes in hex>
[DEBUG] TX: <bytes in hex>
```

---

### --no-echo
Disable local echo.

```bash
$ python3 rv8term.py --no-echo
Terminal mode. Press Ctrl+C to exit.
```

**Normal mode**: Characters you type are echoed to screen.  
**No-echo mode**: Characters you type are NOT echoed (useful when CPU echoes).

---

### --raw
Binary mode (no CR/LF translation).

```bash
$ python3 rv8term.py --raw
Terminal mode. Press Ctrl+C to exit.
```

**Default mode**: CR → CRLF, LF → CRLF (for terminal compatibility)  
**Raw mode**: No translation, pass bytes as-is (for binary data)

---

### -q, --quiet
Minimal output (no banner, no status).

```bash
$ python3 rv8term.py -q
A
hello
```

**Normal mode**:
```
Terminal mode. Press Ctrl+C to exit.
hello from RV8!
>
```

**Quiet mode**: Just the data, no banner.

---

## Interactive Session

```
$ python3 rv8term.py -p 0
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
hello from RV8!     <-- CPU output
A                   <-- You type 'A', sent to CPU
B                   <-- You type 'B'
goodbye             <-- CPU output
^C                  <-- Ctrl+C to exit
Exiting...
```

### Bidirectional Flow

| Direction | Trigger | Action |
|-----------|---------|--------|
| PC → CPU | Type on keyboard | Send byte to programmer → CPU |
| CPU → PC | CPU writes to I/O slot | Display byte on screen |

**I/O Slot Map** (RV8 family):
- Write to `PAGE $F0` → `SB $00` sends byte to PC
- Read from `PAGE $F0` → `LB $00` receives byte from PC

---

## Key Handling

| Key | Action |
|-----|--------|
| Ctrl+C | Exit terminal (send SIGINT) |
| Ctrl+D | Send EOF (if raw mode) |
| Ctrl+Z | Send SUB (if raw mode) |
| Enter | Send CR + LF (default) |
| Ctrl+H | Backspace (erase) |

---

## Exit Behavior

| Operation | On Success | On Failure |
|-----------|------------|------------|
| Help | Exit 0 | N/A |
| Port list | Exit 0 | N/A |
| Connect | Open terminal, stay open | Print error, exit 1 |
| Session | Exit on Ctrl+C | On error, exit 1 |

**On Success (Ctrl+C)**: Clean exit, return code 0  
**On Failure**: Error message, return code 1

---

## Error Messages

| Message | Cause |
|---------|-------|
| `"Error: No port found"` | No serial ports available |
| `"Error: Port <n> not found"` | Index >= available ports |
| `"Error: Cannot open port"` | Port in use or permission denied |
| `"Error: Timeout"` | No response from programmer |

---

## Examples

**Linux/WSL**:
```bash
$ python3 rv8term.py -pl
[0] /dev/ttyUSB0
[1] /dev/ttyUSB1

$ python3 rv8term.py -c
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected

$ python3 rv8term.py -p 0
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
RV8 BASIC 1.0
> 

$ python3 rv8term.py -p 0 -d
Port: /dev/ttyUSB0 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
[DEBUG] RX: 52 56 38 20 42 41 53 49 43 20 31 2E 30 0D 0A
RV8 BASIC 1.0
>
```

**Windows**:
```cmd
> python rv8term.py -c
Port: COM3 @ 115200 baud
Programmer: Connected

> python rv8term.py -p 0
Port: COM3 @ 115200 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
RV8 BASIC 1.0
>
```

**Custom baud rate**:
```bash
$ python3 rv8term.py -p 0 -b 9600
Port: /dev/ttyUSB0 @ 9600 baud
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
```

**Debug mode**:
```bash
$ python3 rv8term.py -p 0 -d
Port: /dev/ttyUSB0 @ 115200 baud
[DEBUG] TX: 3F (?)
[DEBUG] RX: Connected
Programmer: Connected
Terminal mode. Press Ctrl+C to exit.
---
[DEBUG] RX: 52 56 38 20
RV8
```

---

## Installation

```bash
pip install pyserial
python3 rv8term.py -p 0
```

---

## Return Codes

| Code | Meaning |
|:----:|---------|
| 0 | Normal exit (Ctrl+C) |
| 1 | Error |

---

## Post-Coding Checklist

### Completed ✅

- [x] VirtualESP32 class at top
- [x] Options class for CLI parsing
- [x] All options: -h, -pl, -p, -c, -b, -t, -d, --no-echo, --raw, -q
- [x] Connection check before terminal (same as rv8flash.py)
- [x] Port + baud display on connect
- [x] Terminal handler (bidirectional PC↔CPU)
- [x] Keyboard input (non-blocking)
- [x] Screen output
- [x] Ctrl+C detection
- [x] Boot delay + buffer drain (ESP32 resets on DTR)
- [x] rv8term.py implementation
- [x] test_rv8term.py tests (15/15 passing)

### Test Results

```
$ python3 -m unittest test_rv8term -v
Ran 15 tests in 0.000s
OK
```

### Files

```
tools/
├── rv8term.py           # Main implementation (289 lines)
├── test_rv8term.py      # Test suite (294 lines, 15 tests)
└── rv8term-requirement.md # Requirements document
```

---

## Program Structure (Single File)

```
rv8term.py
|
+-- VirtualESP32 class (pin definitions at top)
|
+-- Options class (parsed command-line options)
|
+-- Terminal class (terminal session handling)
|
+-- SerialBridge class (serial I/O wrapper)
|
+-- rv8term() function (main logic)
|
+-- main() entry point
```

All in one file. No separate configuration files needed.