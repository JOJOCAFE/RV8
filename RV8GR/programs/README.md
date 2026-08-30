# RV8GR Example Programs

These examples are source-only `.asm` programs for the current RV8GR assembler.
They avoid unsupported pseudo devices and use only the existing accumulator,
RAM/register aliases, page registers, branches, and memory-mapped load/store.

Assemble from `RV8GR/`:

```bash
python3 tools/rv8gr_asm.py programs/blink.asm -o /tmp/rv8gr-blink.bin
python3 tools/rv8gr_asm.py programs/counter.asm -o /tmp/rv8gr-counter.bin
python3 tools/rv8gr_asm.py programs/echo.asm -o /tmp/rv8gr-echo.bin
python3 tools/rv8gr_asm.py programs/basic_min.asm -o /tmp/rv8gr-basic-min.bin
```

## Programs

| File | Purpose | Notes |
|------|---------|-------|
| `blink.asm` | Alternates `$55` and `$AA` on memory-mapped output `$FF10`. | Requires an external device on I/O slot 1 to make the pattern visible; otherwise it still exercises `SETDP`, `SB`, and branch delays. |
| `counter.asm` | Counts from `$00` to `$0F`, mirrors each value to RAM `$8010`, and writes the same value to `$FF10`. | Final count `$10` is stored at RAM `$8011` before halt. |
| `echo.asm` | Closest supported echo equivalent: seeds a RAM input buffer and copies it to a RAM output buffer. | RV8GR v1.0 has no UART instruction or indirect indexed addressing, so the copy is intentionally fixed-size and unrolled. |
| `basic_min.asm` | B-011 phase 1 BASIC-style ROM runtime smoke. | Non-interactive by design: writes PRINT transcript `1,2,3` to RAM `$8040-$8042`, pass marker `$42` to `$8043`, and mirrors PRINT values to `$FF10`. |
| `game.asm` | B-024 "Reaction Countdown": a fully deterministic demo game. A countdown ticks `10`->`0`; a win is latched exactly once at count `7`, then the countdown always runs to `0` and halts. | Needs no external device. Latched result (`1`=win) is stored at RAM `$8020`, copied to `$8011` for verification, and mirrored to `$FF10`/`$FF20`. Deterministic and regression-tested by `sim/test_game.py` on both `CPUSim` and `ComponentsCPUSim`. |
