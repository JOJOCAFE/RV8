# RV8GR Example Programs

These examples are source-only `.asm` programs for the current RV8GR assembler.
They avoid unsupported pseudo devices and use only the existing accumulator,
RAM/register aliases, page registers, branches, and memory-mapped load/store.

Assemble from `RV8GR/`:

```bash
python3 tools/rv8gr_asm.py programs/blink.asm -o /tmp/rv8gr-blink.bin
python3 tools/rv8gr_asm.py programs/counter.asm -o /tmp/rv8gr-counter.bin
python3 tools/rv8gr_asm.py programs/echo.asm -o /tmp/rv8gr-echo.bin
```

## Programs

| File | Purpose | Notes |
|------|---------|-------|
| `blink.asm` | Alternates `$55` and `$AA` on memory-mapped output `$FF10`. | Requires an external device on I/O slot 1 to make the pattern visible; otherwise it still exercises `SETDP`, `SB`, and branch delays. |
| `counter.asm` | Counts from `$00` to `$0F`, mirrors each value to RAM `$8010`, and writes the same value to `$FF10`. | Final count `$10` is stored at RAM `$8011` before halt. |
| `echo.asm` | Closest supported echo equivalent: seeds a RAM input buffer and copies it to a RAM output buffer. | RV8GR v1.0 has no UART instruction or indirect indexed addressing, so the copy is intentionally fixed-size and unrolled. |

