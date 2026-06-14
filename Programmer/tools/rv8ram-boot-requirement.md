# rv8ram-boot.py — Requirements Document

**Purpose**: Upload program to RV8 CPU RAM via bootloader (not ROM)

**Platform**: Linux, WSL, Windows, macOS (Python 3.6+)

**Dependency**: `pyserial` (`pip install pyserial`)

**Usage**: `python3 rv8ram-boot.py [options]`

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

| Board Variant | D[7:0] | A[7:0] | Notes |
|---------------|--------|--------|-------|
| Default | 13,12,14,27,26,25,33,32 | via 74HC595 x2 | TXS0108E |
| Custom | Edit pins | Edit pins | Your wiring |

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
        self.file = None
        self.debug = False      # -d: show serial traffic
        self.retry = 3          # -t N: retry N times on failure
        self.quiet = False      # -q: minimal output
        self.auto_port = True   # use port 0 if not specified
        self.force = False      # -f: overwrite existing file
        self.format = 'bin'     # --format hex|bin
        self.auto_reset = False # -R: pulse /RST after upload
```

---

## Command-Line Options Summary

| Short | Long | Args | Description |
|-------|------|------|-------------|
| -h | --help | none | Show help |
| -pl | --portlist | none | List available ports |
| -p | --port | N | Port index (0, 1, ...) |
| -d | --debug | none | Show serial traffic |
| -t | --retry | N | Retry N times on failure (default: 3) |
| -q | --quiet | none | Minimal output |
| --format | FORMAT | hex\|bin | File format (default: bin) |
| -f | --force | none | Overwrite existing file |
| -R | --reset | none | Pulse /RST after upload |
| file | positional | file.bin | Binary file to upload |

---

## Options Detail

### -h, --help
Show help message.

```bash
$ python3 rv8ram-boot.py -h
```

---

### -pl, --portlist
List available serial ports with index numbers.

```bash
$ python3 rv8ram-boot.py -pl
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
$ python3 rv8ram-boot.py -pl
[0] ttyUSB0

$ python3 rv8ram-boot.py -p 0 hello.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
Done. Program loaded and running.
```

| Index | Linux/WSL | Windows | macOS |
|:-----:|-----------|---------|-------|
| 0 | ttyUSB0 | COM3 | cu.usbserial-0001 |
| 1 | ttyUSB1 | COM4 | cu.usbserial-0002 |

---

### Positional Argument: file
Binary file to upload to RAM.

```bash
$ python3 rv8ram-boot.py hello.bin        # Use port 0
$ python3 rv8ram-boot.py -p 0 test.bin   # Use port 0 explicit
$ python3 rv8ram-boot.py -p 1 prog.bin  # Use port 1
```

---

### -d, --debug
Show serial traffic (verbose mode).

```bash
$ python3 rv8ram-boot.py -d hello.bin
Waiting for bootloader ready signal...
[DEBUG] RX: 52  (R in hex)
Got 'R'. Sending 256 bytes...
[DEBUG] TX: 00 01
[DEBUG] TX: 48 65 6C 6C 6F ...
Done. Program loaded and running.
```

**Debug Output Format**:
```
[DEBUG] RX: <bytes in hex>
[DEBUG] TX: <bytes in hex>
```

---

### -t [N], --retry [N]
Retry N times on failure (default: 3).

```bash
$ python3 rv8ram-boot.py -t 5 hello.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
[ERROR] Timeout waiting for 'D'. Retry (1/5)...
[ERROR] Timeout waiting for 'D'. Retry (2/5)...
[ERROR] Timeout waiting for 'D'. Retry (3/5)...
[ERROR] Timeout waiting for 'D'. Retry (4/5)...
[ERROR] Timeout waiting for 'D'. Retry (5/5)...
[ERROR] Upload failed after 5 retries
```

---

### -q, --quiet
Minimal output (no progress bar, no extra text).

```bash
$ python3 rv8ram-boot.py -q hello.bin
Done. 256 bytes uploaded.
```

---

### -f, --format hex|bin
Specify file format (default: bin).

```bash
$ python3 rv8ram-boot.py program.bin --format bin    # raw binary
$ python3 rv8ram-boot.py program.hex --format hex    # Intel HEX
```

**Supported Formats**:
| Format | Extension | Description |
|--------|-----------|-------------|
| bin | .bin | Raw binary (default) |
| hex | .hex | Intel HEX (text) |

---

### -f, --force
Overwrite existing file without asking (not applicable for upload, reserved for consistency).

```bash
$ python3 rv8ram-boot.py -f file.bin
```

---

### -R, --reset
Pulse /RST after successful upload.

```bash
$ python3 rv8ram-boot.py hello.bin -R
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
[██████████] 100%
Done. 256 bytes uploaded.
Auto-resetting CPU...
Done. CPU is now running.
```

---

## Default Behavior Matrix

| Options | Result |
|---------|--------|
| (no args) | Show help |
| `-h` | Show help |
| `-pl` | List ports with indices |
| `-c` | Check port 0 |
| `-p N` | Check port N |
| `file` | Upload file to port 0 |
| `-p N file` | Upload file to port N |

**Implicit Defaults**:
- Port: 0 (if not specified)
- Retry: 3
- Progress: on
- Debug: off

---

## Protocol (Bootloader)

| Direction | Signal | Format |
|-----------|--------|--------|
| Boot → PC | Ready | `R` (single byte) |
| PC → Boot | Length | `len_hi` (byte 1) + `len_lo` (byte 2) |
| PC → Boot | Data | One byte at a time, with ~6ms delay |
| Boot → PC | Done | `D` (single byte) |

**Timing**: 6ms per byte = ~100 bytes/second max throughput

---

## File Size Limit

| Max Size | Address Range |
|----------|---------------|
| 15871 bytes | $C000 - $FDFF |

```bash
$ python3 rv8ram-boot.py big.bin
ERROR: max 15871 bytes (RAM $C000-$FDFF)
```

---

## Intel HEX Format Support

### Format Specification

Intel HEX is text-based, 1 line per 16 bytes:

```
:BBAAAATTHH...HHCC
```

| Field | Description |
|-------|-------------|
| `:` | Start code |
| `BB` | Byte count (2 hex digits) |
| `AAAA` | Address (4 hex digits) |
| `TT` | Record type (00=data, 01=end) |
| `HH...HH` | Data bytes |
| `CC` | Checksum (2's complement XOR) |

### Example

```
:10C000003162696E61727920646174610000000000AB
:10C0100031303030206C696E657300000000000080
:00000001FF
```

### Parser Rules

```python
def parse_hex(file_path):
    """Parse Intel HEX file, return binary data."""
    data = bytearray()
    for line in open(file_path):
        line = line.strip()
        if not line.startswith(':'):
            continue
        # Parse line, extract data bytes
        # Return bytes object
    return bytes(data)
```

### Supported Types

| Type | Meaning | Action |
|------|---------|--------|
| 00 | Data | Append to output |
| 01 | End of file | Stop parsing |
| 04 | Extended linear address | Set high address |
| Other | Unsupported | Skip with warning |

### Auto-detect

If file extension is `.hex` → parse as Intel HEX  
If file extension is `.bin` → raw binary  
If no extension → try both or default to binary

```python
def load_file(path):
    if path.endswith('.hex'):
        return parse_hex(path)
    elif path.endswith('.bin'):
        return open(path, 'rb').read()
    else:
        # Try binary first, then hex
        try:
            return open(path, 'rb').read()
        except:
            return parse_hex(path)
```

---

## Progress Indicator

**Format**: `[██████████] 25%` (10-character bar)

```
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
[███░░░░░░]  30%
[██████████] 100%
Done. Program loaded and running.
```

**Updates**: Every 256 bytes (1KB).

**Quiet mode**: Just `30%` without bar.

---

## Exit Behavior

| Operation | On Success | On Failure |
|-----------|------------|------------|
| Help | Exit 0 | N/A |
| Port list | Exit 0 | N/A |
| Check | Print result, exit 0 or 1 | N/A |
| Upload | Print "Done", exit 0 | Print error, exit 1 |

**On Success**: Exit code 0, brief status message.  
**On Failure**: Exit code 1, error message with cause.

---

## Error Messages

| Message | Cause |
|---------|-------|
| `"ERROR: max 15871 bytes (RAM $C000-$FDFF)"` | File too large |
| `"Timeout waiting for 'R'. Reset the board?"` | No ready signal |
| `"ERROR: expected 'D', got <byte>"` | Bootloader returned error |
| `"ERROR: Cannot open port"` | Port in use or permission denied |
| `"Retry limit exceeded"` | N retries failed |
| `"ERROR: File not found"` | File doesn't exist |

---

## Examples

**Linux/WSL**:
```bash
$ python3 rv8ram-boot.py -pl
[0] ttyUSB0

$ python3 rv8ram-boot.py -p 0 hello.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 256 bytes...
[██████████] 100%
Done. Program loaded and running.

$ python3 rv8ram-boot.py hello.bin -d
Waiting for bootloader ready signal...
[DEBUG] RX: 52
Got 'R'. Sending 256 bytes...
[DEBUG] TX: 00 01
[DEBUG] TX: 48 65 6C 6C 6F ...
Done. Program loaded and running.
```

**Windows**:
```cmd
> python rv8ram-boot.py -pl
[0] COM3

> python rv8ram-boot.py -p 0 test.bin
Waiting for bootloader ready signal...
Got 'R'. Sending 1024 bytes...
[██████████] 100%
Done. Program loaded and running.
```

**macOS**:
```bash
$ python3 rv8ram-boot.py -pl
[0] cu.usbserial-0001

$ python3 rv8ram-boot.py -p 0 -d hello.bin
Waiting for bootloader ready signal...
[DEBUG] RX: 52
Got 'R'. Sending 256 bytes...
[██████████] 100%
Done. Program loaded and running.
```

---

## Installation

```bash
pip install pyserial
python3 rv8ram-boot.py program.bin
```

---

## Checksum

Program calculates XOR checksum of uploaded data for integrity check.

**Checksum Algorithm**: XOR of all bytes (byte-level).

```python
def calc_checksum(data):
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum
```

**Usage**:
- Calculated before upload
- Debug output shows checksum
- Used for verify (if implemented)

---

## Return Codes

| Code | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | Error |

---

## Post-Coding Checklist

### Completed ✅

- [x] VirtualESP32 class at top
- [x] Options class for CLI parsing
- [x] All options: -h, -pl, -p, -d, -t, -q, --format, -f, -R, file
- [x] Bootloader protocol (B→R→data→D)
- [x] Intel HEX parser
- [x] Checksum calculation
- [x] Progress bar
- [x] rv8ram-boot.py implementation (430 lines)
- [x] test_rv8ram-boot.py tests (15/15 passing)

### Test Results

```
$ python3 -m unittest test_rv8ram-boot -v
Ran 15 tests in 0.002s
OK
```

### Files

```
tools/
├── rv8ram-boot.py           # Main implementation (430 lines)
├── test_rv8ram-boot.py      # Test suite (347 lines, 15 tests)
└── rv8ram-boot-requirement.md # Requirements document
```

---

## Program Structure (Single File)

```
rv8ram-boot.py
|
+-- VirtualESP32 class (pin definitions at top)
|
+-- Options class (parsed command-line options)
|
+-- SerialPort class (wraps pyserial with board pins)
|
+-- BootloaderProtocol class (upload protocol logic)
|
+-- rv8ram_boot() function (main logic)
|
+-- main() entry point
```

All in one file. No separate configuration files needed.