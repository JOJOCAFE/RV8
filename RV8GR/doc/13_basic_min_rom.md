# RV8GR B-011 Minimal BASIC ROM

Status: phase 1 implemented as a BASIC-style ROM runtime smoke test.

## Boundary

RV8GR v1.0 can run a useful BASIC-style ROM, but a real interactive Tiny BASIC
is not practical in the frozen baseline yet:

- No UART or keyboard/display device is part of the CPU core.
- RV8-Bus I/O exists as address slots, but external devices still need physical
  field evidence.
- The ISA has no indirect or indexed load/store, so scanning arbitrary token
  streams in RAM is not a small ROM routine.
- There is no CALL/RET stack, so reusable interpreter subroutines require either
  conventions in RAM or a future software/runtime pattern.

## Phase 1 Deliverable

`programs/basic_min.asm` is a minimal BASIC-style ROM that proves the conventions
needed for a later interpreter:

- ROM boot initializes `DP=$80` and `PG=$00`.
- RAM `$8020` holds variable `A`.
- RAM `$8040-$8042` holds PRINT output.
- RAM `$8043=$42` is the pass marker.
- `$FF10` receives each PRINT value as an optional output mirror.
- A documented token stream is stored at ROM `$0100` for the same program, but
  the phase 1 runtime is direct-coded.

The represented BASIC program is:

```basic
10 LET A = 1
20 PRINT A
30 LET A = A + 1
40 PRINT A
50 LET A = A + 1
60 PRINT A
70 END
```

Expected result:

```text
RAM[$8020] = $03
RAM[$8040] = $01
RAM[$8041] = $02
RAM[$8042] = $03
RAM[$8043] = $42
RAM[$FF10 mirror] = $03
```

## Verification

Run:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/rv8gr_asm.py programs/basic_min.asm -o /tmp/rv8gr-basic-min.bin
python3 -B sim/test_basic_min.py
```

`sim/test_basic_min.py` assembles the ROM source and runs it on both Python CPU
paths: `CPUSim` and `ComponentsCPUSim`.

## Next Phase

The next useful B-011 step is not to expand syntax first. It is to choose the
runtime model:

1. Add an external UART/terminal device on RV8-Bus and define status/data
   registers.
2. Add a ROM monitor command loop that polls that device.
3. Decide whether the interpreter scans fixed ROM tokens, RAM tokens, or a
   line-buffer format.
4. Only then add commands such as `INPUT`, `GOTO`, and multi-line editing.
