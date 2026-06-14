# ESP32 Programmer Firmware — Requirements

**Target**: ESP32-WROOM-32 with Arduino framework
**File**: `firmware.ino` (single file)
**Purpose**: Flash/read/verify ROM on CPU board via RV8-Bus

---

## Connection

```
PC ←USB→ ESP32 ←TXS0108E×2→ RV8-Bus (40-pin) → ROM on target board
```

Two scenarios:
- **A (bare ROM)**: ROM wired directly to bus connector
- **B (full CPU)**: Hold /RST to stop CPU, then access ROM via bus

---

## Pin Configuration

```cpp
// Data bus D[7:0] (via TXS0108E #2 → Bus pin 17-24)
const uint8_t DATA_PINS[] = {13, 12, 14, 27, 26, 25, 33, 32};

// Address via 74HC595 ×2 (via TXS0108E #1 → Bus pin 1-16)
#define PIN_SR_DATA   23   // SER
#define PIN_SR_CLK    18   // SRCLK
#define PIN_SR_LATCH  19   // RCLK

// Control (via TXS0108E #1 → RV8-Bus)
#define PIN_nRST  4    // → Bus pin 26 (/RST)
#define PIN_nWR   16   // → Bus pin 27 (/WR)
#define PIN_nRD_O 17   // → Bus pin 28 (/RD, output in PROG mode)

// Input (from RV8-Bus, RUN mode sensing)
#define PIN_nSLOT1 34  // ← Bus pin 30
#define PIN_nRD_S  35  // ← Bus pin 28
#define PIN_nWR_S  36  // ← Bus pin 27
#define PIN_MODE   39  // PROG/RUN switch

#define SERIAL_BAUD 115200
```

---

## Protocol (PROG mode)

| PC → ESP32 | ESP32 → PC | Notes |
|------------|------------|-------|
| `?` | `Connected\n` | Connection check |
| `F` + len_hi + len_lo | `K\n`, then receive data, then `D\n` | Flash ROM |
| `V` | 32768 raw bytes | Read entire ROM |
| `R` | `K\n` | Pulse /RST |

### Flash sequence
1. PC sends `F` + 2-byte big-endian length
2. ESP32 replies `K\n` (ready)
3. PC sends `length` bytes
4. ESP32 writes each byte: set address (595), set data, pulse /WR
5. ESP32 replies `D\n` (done)

### Read sequence
1. PC sends `V`
2. ESP32 reads 32768 bytes: set address, pulse /RD, read data bus
3. ESP32 sends all 32768 bytes raw

---

## ROM Access via Bus

**Write**: A15=0 (595 bit15) → ROM /CE active. Pulse /WR → ROM latches data.
**Read**: A15=0 → ROM /CE active. Pulse /RD → ROM outputs data (/OE).
**CPU isolation**: /RST=LOW keeps CPU in reset, tri-states its bus drivers.

---

## Modes

| Mode | PIN_MODE | Behavior |
|------|----------|----------|
| PROG | LOW | Serial commands, drives bus |
| RUN | HIGH | Releases bus, UART bridge via /SLOT1 |

### PROG mode
- `/RST` held LOW (CPU stopped)
- `/RD_O` set as OUTPUT (drives ROM /OE)
- Responds to serial protocol commands

### RUN mode
- `/RST` released HIGH (CPU runs)
- `/RD_O` set as INPUT (CPU drives /RD)
- Listens for `/SLOT1` activity for UART bridging

---

## Error Responses

| Response | Meaning |
|----------|---------|
| `K\n` | ACK / success |
| `D\n` | Operation complete |
| `E:timeout\n` | Serial timeout waiting for data |
| `E:len\n` | Invalid length (0 or >32768) |

---

## Timing

| Parameter | Value |
|-----------|-------|
| Baud rate | 115200 |
| /WR pulse | 1 µs |
| /RD setup | 1 µs (before reading data bus) |
| Page write delay | 10 ms (every 64 bytes) |
| Boot delay | ~2s (ESP32 prints boot messages) |

---

## Post-Coding Checklist

- [x] Single file `firmware.ino`
- [x] Pin config at top
- [x] 74HC595 shift register for A[14:0] (A15 always 0)
- [x] Data bus bidirectional (set input for read, output for write)
- [x] `?` → `Connected\n`
- [x] `F` → ACK + receive + done
- [x] `V` → drives /RD per byte, sends 32KB
- [x] `R` → pulse /RST
- [x] MODE switch selects PROG/RUN
- [x] RUN mode releases /RD_O as input
- [x] PROG mode reclaims /RD_O as output
- [x] Compiles clean (286KB)
- [x] 31 Python tests pass
