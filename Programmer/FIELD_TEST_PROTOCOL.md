# RV8 Programmer Field-Test Protocol

Updated: 2026-07-10

Purpose: prove the ESP32 Programmer can safely program and verify RV8GR ROM images
before it is used as part of the full physical CPU build.

This protocol is for real hardware. The Python mock tests prove the PC-side tools
and serial protocol logic, but they do not prove voltage levels, cable wiring,
bus release, EEPROM write timing, or physical ROM protection state.

## Safety Rules

1. Use only one target path at a time:
   - ZIF Direct: bus cable disconnected.
   - RV8-Bus in-system: ZIF socket empty.
2. Power off before changing between ZIF, bus cable, PROG, and RUN setups.
3. In RV8-Bus PROG mode, the CPU must be held in reset and the Programmer owns
   A[14:0], D[7:0], `/WR`, and `/RD`.
4. In RUN mode, the Programmer must release `/WR`, `/RD`, and D[7:0] so the CPU
   owns the bus.
5. During normal CPU runtime, ROM `/WE` must stay inactive. The Programmer write
   path may drive ROM `/WE` only while the board is intentionally in PROG mode
   with the CPU stopped or while a bare ROM is in the ZIF socket.
6. Current firmware uses normal byte-write cycles. Use AT28C256 parts with
   software data protection disabled, or add SDP unlock support before relying
   on protected parts.

## Virtual Preflight

Run from repo root before touching hardware:

```sh
python3 -B Programmer/tools/test_rv8flash.py
python3 -B Programmer/tools/test_rv8term.py
python3 -B Programmer/tools/test_rv8ram-boot.py
```

Expected result on 2026-07-10: 51 total mock tests pass.

| Test file | Expected count | Purpose |
|---|---:|---|
| `test_rv8flash.py` | 19 | Flash, read, verify, CLI, serial protocol, error handling |
| `test_rv8term.py` | 17 | Terminal CLI and UART bridge behavior |
| `test_rv8ram-boot.py` | 15 | RAM boot upload and command handling |

Also run the RV8GR software/RTL signoff when the ROM image changes:

```sh
python3 -B RV8GR/tools/test_rv8gr_asm.py
python3 -B RV8GR/sim/test_cpu_logical_protocol.py
```

## Test Image

Use a small known ROM image first, then the full ISA test ROM.

Record for each image:

| Field | Value |
|---|---|
| File path | |
| File size | |
| SHA-256 | |
| Assembler command or source | |
| Expected behavior on CPU | |

## Instrument Checklist

Minimum:

- 5 V rail measurement at Programmer and CPU board.
- 3.3 V rail measurement at ESP32/TXS side.
- Continuity check for RV8-Bus pins 1-30, 39, and 40.
- Logic probe or logic analyzer on `/RST`, `/WR`, `/RD`, A0, D0, and D7.

Preferred:

- Oscilloscope capture of `/WR`, `/RD`, and one data bit during write/read.
- Current-limited bench supply for first power-up.

## Mode A: ZIF Direct Test

Use this when programming a bare AT28C256-compatible ROM in the Programmer ZIF.

1. Power off.
2. Disconnect RV8-Bus cable.
3. Insert ROM into ZIF socket, pin 1 correctly oriented, then lock ZIF.
4. Power on Programmer.
5. Confirm PC can see the serial device:

   ```sh
   python3 Programmer/tools/rv8flash.py -pl
   python3 Programmer/tools/rv8flash.py -c
   ```

6. Program the image:

   ```sh
   python3 Programmer/tools/rv8flash.py -w program.bin
   ```

7. Verify the image:

   ```sh
   python3 Programmer/tools/rv8flash.py -v program.bin
   ```

8. Read back to a new file and compare hashes:

   ```sh
   python3 Programmer/tools/rv8flash.py -r readback.bin -f
   sha256sum program.bin readback.bin
   ```

Pass condition: connection succeeds, write completes, verify passes, and readback
hash matches the input image.

## Mode B: RV8-Bus In-System Test

Use this only after the CPU ROM module is wired and checked.

1. Power off.
2. Remove any ROM from the Programmer ZIF socket.
3. Connect RV8-Bus cable to the CPU board.
4. Set switch to PROG.
5. Power on.
6. Confirm `/RST` is LOW at the CPU board before write/verify.
7. Confirm Programmer owns `/WR` and `/RD` only in PROG mode.
8. Run:

   ```sh
   python3 Programmer/tools/rv8flash.py -c
   python3 Programmer/tools/rv8flash.py -w program.bin
   python3 Programmer/tools/rv8flash.py -v program.bin
   ```

9. Power off or switch to RUN according to the board procedure.
10. Confirm `/WR`, `/RD`, and D[7:0] are released by the Programmer in RUN mode.
11. Reset the CPU and observe the expected ROM behavior.

Pass condition: the same program/verify result as ZIF Direct, plus no bus
contention signs when switching to RUN mode.

## Evidence Log

Create one log entry per field test:

| Field | Value |
|---|---|
| Date/time | |
| Operator | |
| Board revision / wiring photo link | |
| Mode | ZIF Direct / RV8-Bus |
| ROM part number | |
| ROM SDP state | disabled / unlock-supported / unknown |
| Supply voltage at board | |
| Serial port | |
| Command transcript | |
| SHA-256 input/readback | |
| Logic capture file/photo | |
| Result | PASS / FAIL |
| Failure notes / fix | |

## Failure Triage

| Symptom | First checks |
|---|---|
| No serial port | USB cable, ESP32 power, driver, `-pl` output |
| Programmer not responding | PROG/RUN switch, ESP32 boot delay, baud 115200 |
| Write timeout | ROM inserted/oriented, `/WE` path, 5 V rail, TXS OE |
| Verify mismatch | Protected AT28C256, write delay, address/data pin swap, weak cable |
| CPU fails after verified ROM | Wrong ROM image, CPU reset/run mode, ROM `/OE`, address wiring |
| Bus fight or heating | ZIF and bus both connected, RUN mode not releasing D bus, CPU not reset in PROG |

## B-012 Exit Criteria

B-012 can move from READY FOR FIELD TEST to DONE only after:

1. All 51 mock tests pass in this repo.
2. ZIF Direct field test passes with readback hash evidence.
3. RV8-Bus in-system field test passes or is explicitly deferred until the ROM
   module exists.
4. The evidence log is committed or linked from the project docs.
