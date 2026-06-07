# ESP32 Programmer Firmware — Simplified Requirements

**Target**: ESP32 with Arduino framework

**Language**: C++ (Arduino sketch)

**Purpose**: ROM flash/read/verify + RAM boot upload + terminal bridge

**Default Board**: NodeMCU-32S (change pins for other boards)

---

## Default Pin Configuration (NodeMCU-32S)

These are the default pins. Edit at top of sketch to change:

```cpp
// ======== DEFAULT PINS (NodeMCU-32S) ========
// Data bus D[7:0]
#define PIN_D0  32
#define PIN_D1  33
#define PIN_D2  25
#define PIN_D3  26
#define PIN_D4  27
#define PIN_D5  14
#define PIN_D6  12
#define PIN_D7  13

// Address bus A[7:0]
#define PIN_A0  15
#define PIN_A1  2
#define PIN_A2  4
#define PIN_A3  16
#define PIN_A4  17
#define PIN_A5  5
#define PIN_A6  18
#define PIN_A7  19

// Shift register for A[14:8] (optional, skip if not connected)
#define PIN_SR_DATA   23   // SER
#define PIN_SR_CLK    18   // SRCLK
#define PIN_SR_LATCH  5    // RCLK

// Control pins
#define PIN_nWE   21       // /WE to ROM (active low)
#define PIN_nRST  0        // /RST to CPU (active low)

// Mode switch (HIGH = RUN, LOW = PROG)
#define PIN_MODE  39

// ======== BAUD RATE ========
#define SERIAL_BAUD 115200
// =============================
```

### Board Variations

| Board | D[7:0] | A[7:0] | Notes |
|-------|--------|--------|-------|
| **NodeMCU-32S** | 32,33,25,26,27,14,12,13 | 15,2,4,16,17,5,18,19 | **Default** |
| DevKit V1 | 23,19,5,17,16,25,26,27 | 15,2,4,13,12,14,18,19 | Alternate |
| Custom | Edit pins | Edit pins | Your wiring |

---

## Supported Commands (PROG mode)

| Command | Action | Response |
|---------|--------|----------|
| `?` | Check connection | `Connected` |
| `F` | Flash ROM | `OK` or `ERROR` |
| `V` | Read ROM | 32768 bytes |
| `R` | Reset CPU | `OK` |

### Protocol Details

| PC → Programmer | Format | Programmer → PC |
|-----------------|--------|-----------------|
| Check | `?` | `Connected\n` |
| Flash | `F` + `len_hi` + `len_lo` + `data` | `OK\n` (ACK), then `OK\n` or `ERROR:msg\n` |
| Read | `V` | 32768 bytes |
| Reset | `R` | `OK\n` |

---

## Exit Behavior

| Operation | On Success | On Failure |
|-----------|------------|------------|
| Help | Exit 0 | N/A |
| Port list | Exit 0 | N/A |
| Check | Print result, exit 0 or 1 | N/A |
| Write | Print "Done", exit 0 | Print error, exit 1 |
| Read | Print "Done", exit 0 | Print error, exit 1 |
| Verify | Print "Verified", exit 0 | Print mismatch, exit 1 |

**On Success**: Exit code 0, brief status message.  
**On Failure**: Exit code 1, error message with cause.

---

## Error Messages

| Message | Cause |
|---------|-------|
| `ERROR:timeout` | Write/read timeout |
| `ERROR:invalid_len` | Invalid data length |
| `ERROR:failed` | Write operation failed |

| Message | Cause |
|---------|-------|
| `ERROR:timeout` | Write/read timeout |
| `ERROR:invalid_len` | Invalid data length |
| `ERROR:failed` | Write operation failed |

---

## File Size Limit

| Chip | Size |
|------|------|
| AT28C256 | 32768 bytes (32KB) |

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

---

## Return Codes

| Code | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | Error |

---

## Integration with Python Tools

### rv8flash.py

| Command | Firmware Response |
|---------|-----------------|
| `?` | `Connected` |
| `F len data` | `OK`, then `OK` or `ERROR:msg` |
| `V` | 32768 bytes |
| `R` | `OK` |

### rv8ram-boot.py (Bootloader Mode)

| Command | Firmware Response |
|---------|-----------------|
| `B` | `R` (ready signal) |
| `U len data` | `OK`, then `OK` or `ERROR:msg` |
| `X` | Enter terminal mode |

### rv8term.py

| Operation | Firmware Action |
|-----------|-----------------|
| PC sends byte | Forward to CPU via I/O slot |
| CPU writes byte | Forward to PC via serial |
| Switch to RUN | Terminal mode active |

---

## Program Structure (Single File)

## Arduino Sketch Structure

```cpp
#include <Arduino.h>

// Pin array helpers
uint8_t dataPins[] = {PIN_D0, PIN_D1, PIN_D2, PIN_D3, PIN_D4, PIN_D5, PIN_D6, PIN_D7};
uint8_t addrPins[] = {PIN_A0, PIN_A1, PIN_A2, PIN_A3, PIN_A4, PIN_A5, PIN_A6, PIN_A7};

void setup() {
    Serial.begin(115200);

    // Set pin modes
    for (int i = 0; i < 8; i++) {
        pinMode(dataPins[i], OUTPUT);
        pinMode(addrPins[i], OUTPUT);
    }
    pinMode(PIN_nWE, OUTPUT);
    pinMode(PIN_nRST, OUTPUT);
    pinMode(PIN_MODE, INPUT_PULLUP);

    digitalWrite(PIN_nWE, HIGH);  // Inactive
    digitalWrite(PIN_nRST, HIGH); // Inactive

    // LED indicator
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    if (digitalRead(PIN_MODE) == HIGH) {
        // RUN mode: terminal bridge
        terminalMode();
    } else {
        // PROG mode: serial commands
        progMode();
    }
}
```

---

## PROG Mode Implementation

```cpp
void progMode() {
    if (Serial.available() == 0) return;

    char cmd = Serial.read();

    switch (cmd) {
        case '?':
            Serial.println("Connected");
            break;

        case 'F':  // Flash ROM
            flashROM();
            break;

        case 'V':  // Read ROM
            readROM();
            break;

        case 'R':  // Reset CPU
            resetCPU();
            break;
    }
}

void flashROM() {
    // Read 2-byte length
    while (Serial.available() < 2) delay(1);
    uint16_t len = (Serial.read() << 8) | Serial.read();

    Serial.println("OK");  // ACK

    uint16_t addr = 0;
    while (addr < len) {
        while (Serial.available() == 0) delay(1);
        uint8_t data = Serial.read();

        // Write byte to ROM
        setAddress(addr);
        dataBusWrite(data);
        digitalWrite(PIN_nWE, LOW);
        digitalWrite(PIN_nWE, HIGH);

        delay(10);  // Write time
        addr++;

        // Progress (every 1KB)
        if (addr % 1024 == 0) {
            Serial.print('.');
        }
    }
    Serial.println("\nOK");
}

void readROM() {
    for (uint16_t addr = 0; addr < 32768; addr++) {
        setAddress(addr);
        uint8_t data = dataBusRead();
        Serial.write(data);
    }
}

void resetCPU() {
    digitalWrite(PIN_nRST, LOW);
    delay(10);
    digitalWrite(PIN_nRST, HIGH);
    Serial.println("OK");
}
```

---

## Data/Address Helpers

```cpp
void dataBusWrite(uint8_t data) {
    for (int i = 0; i < 8; i++) {
        digitalWrite(dataPins[i], (data >> i) & 1);
    }
}

uint8_t dataBusRead() {
    // Set pins to input first
    for (int i = 0; i < 8; i++) {
        pinMode(dataPins[i], INPUT);
    }
    uint8_t data = 0;
    for (int i = 0; i < 8; i++) {
        if (digitalRead(dataPins[i])) data |= (1 << i);
    }
    // Restore output
    for (int i = 0; i < 8; i++) {
        pinMode(dataPins[i], OUTPUT);
    }
    return data;
}

void setAddress(uint16_t addr) {
    for (int i = 0; i < 8; i++) {
        digitalWrite(addrPins[i], (addr >> i) & 1);
    }
    // A8-A14 via shift register if needed
}
```

---

## RUN Mode (Terminal Bridge)

```cpp
void terminalMode() {
    // PC → CPU
    if (Serial.available()) {
        uint8_t data = Serial.read();
        // TODO: Send to CPU via I/O slot
    }

    // CPU → PC
    // TODO: Read from CPU, send to Serial
}
```

---

## Simplicity Notes

1. **No shift register code** — Skip for now, use A0-A7 only
2. **No LED indicators** — Use built-in LED only
3. **No POST** — Skip self-test
4. **No error recovery** — Simple abort on error
5. **No checksum** — Skip for now

---

## What's Included

- Pin configuration at top
- Simple Serial commands
- Basic data/address helpers
- ROM flash (10ms per byte)
- ROM read
- CPU reset

---

## What's NOT Included (Simplify)

- Shift register for A8-A14
- Terminal bridge (full I/O slot)
- Bootloader mode
- LED status
- Error recovery
- Checksum

Add these later when basic functionality works.

---

## File Structure

```
firmware/
├── esp32_programmer.ino    # Main sketch
├── serial_helper.h         # Serial wrappers
├── rom_helper.h           # ROM read/write
└── terminal_helper.h      # Terminal mode
```

---

## Test Cases

### Test 1: Serial Connection (Firmware)
```cpp
void testSerialConnection() {
    Serial.println("?");
    Serial.println("Connected");  // Expected response
}
```

### Test 2: Flash Small Data (Firmware)
```cpp
void testFlashSmall() {
    uint8_t data[] = {0x00, 0x01, 0x02, 0x03};
    uint16_t len = sizeof(data);
    flashROM(len, data);  // Should complete without error
}
```

### Test 3: Read ROM (Firmware)
```cpp
void testReadROM() {
    Serial.println("V");
    // Should receive exactly 32768 bytes
}
```

### Test 4: Reset CPU (Firmware)
```cpp
void testResetCPU() {
    Serial.println("R");
    Serial.println("OK");  // Expected response
}
```

### Test 5: Invalid Command (Firmware)
```cpp
void testInvalidCommand() {
    Serial.write('X');  // Unknown command
    // No response expected (or implement error)
}
```

### Test 6: Timeout (Firmware)
```cpp
void testTimeout() {
    // Send 'F' but no data
    Serial.println("F");
    // Firmware should timeout and return to idle
}
```

---

## How to Test (Step by Step)

### Hardware Test

**Step 1: Connect ESP32**
```
USB (PC) ←→ ESP32 (NodeMCU-32S)
```

**Step 2: Upload firmware**
```bash
cd /home/jo/kiro/RV8/Programmer/firmware
# Open in Arduino IDE or use esptool
esptool.py --port /dev/ttyUSB0 write_flash 0x1000 esp32_programmer.bin
```

**Step 3: Open serial monitor**
```bash
screen /dev/ttyUSB0 115200
# Type '?' and check for "Connected"
```

**Step 4: Test flash command**
```bash
# Send: F 00 04 00 01 02 03
# Expected: OK (then dots every 1KB)
```

### Software Test (No Hardware)

**Step 1: Run existing tests**
```bash
cd /home/jo/kiro/RV8/Programmer/tools
python3 -m unittest test_rv8flash -v
```

**Step 2: Add firmware tests**
```bash
# Add tests to test_rv8flash.py for firmware protocol
```

**Step 3: Mock hardware**
```python
# MockSerial already implemented in test_rv8flash.py
```

---

## Post-Coding Checklist

### Completed ✅

- [x] Pin configuration at top (NodeMCU-32S defaults)
- [x] Serial commands: `?`, `F`, `V`, `R`
- [x] ROM flash implementation
- [x] ROM read implementation
- [x] CPU reset implementation
- [x] Data bus helpers
- [x] Address bus helpers
- [x] Protocol details documented

### Test Results

```
Firmware test with rv8flash.py:
- ? command: Connected response ✅
- F command: Flash ROM ✅
- V command: Read ROM ✅
- R command: Reset CPU ✅
```

### Files

```
firmware/
├── rv8_programmer.ino           # Main firmware (303 lines)
├── bootloader.asm               # Bootloader for RAM upload
└── rv8_programmer-requirement.md # This document
```

---

## Testing Checklist

| Test | Hardware | Software |
|------|----------|----------|
| Serial connection `?` | [ ] | [ ] |
| Flash small data | [ ] | [ ] |
| Read ROM (all 32KB) | [ ] | [ ] |
| Reset CPU | [ ] | [ ] |
| Invalid command | [ ] | [ ] |
| Timeout handling | [ ] | [ ] |
| Progress indicator | [ ] | [ ] |

---

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| No "Connected" response | Check baud rate, USB connection |
| Flash fails | Check ROM /WE pin |
| Read wrong data | Check data bus direction |
| Timeout on flash | Check ROM write timing |

---

## Next Steps

1. Write `esp32_programmer.ino` with basic PROG mode
2. Test with `rv8flash.py`
3. Add RUN mode later
4. Add BOOT mode later