---
name: debug-mantra
description: Four-step hardware debugging discipline for RV8. Reproduce → trace → falsify → breadcrumbs. Trigger on /debug-mantra or when user reports a bug, failure, hang, or glitch.
---

# Debug Mantra

## Recite once per session (verbatim)

> **Mantra:**
> 1. **First is reproducibility.** Can the issue be reproduced reliably?
> 2. **Know the fail path.** Debugger first; then source trace; then instrumentation.
> 3. **Question your hypothesis.** What would disprove it?
> 4. **Every run is a breadcrumb.** Cross-reference all of them.

---

## 1. Reproduce

- Write minimal .bin/.asm triggering the bug deterministically.
- Run in BOTH `rv8gr_cpu.v` (iverilog) AND `chip_sim.py` — do they agree?
- Disagreement = bug is in one model. Agreement = logic/design bug.
- Pin: cycle count, initial state, register values, Z-flag.
- Physical: isolate to one instruction. Flaky → suspect timing.

## 2. Trace the fail path

**Sim**: VCD waveform or `--trace` mode. Check at T0/T1/T2 boundaries.
Compare: PC, AC, IBUS, address bus, control signals (expected vs actual).

**Knobs to flip** (one at a time):
- Opcode bits [7:0]
- T-state (T0/T1/T2)
- Data Page (U32)
- Z-flag (U21/U22)
- Bus direction (WR_DIR)
- A15 chip select
- SRC+STR guard

Does the bug follow the knob or stay fixed?

**Physical**: scope on CLK, /T2, IBUS, address MSB. Tag measurements `[HW-xxxx]`.

## 3. Falsify

- Does hypothesis explain symptom end-to-end?
- Run the **disproof first** (cheapest experiment that kills the theory).
- Top 5 hardware bug classes:
  1. Bus contention (two drivers)
  2. Timing race (setup/hold)
  3. Wrong wiring (pin swap)
  4. Logic error (inverted signal)
  5. Power/ground (floating input)

## 4. Breadcrumb ledger

| # | Changed | Result | Ruled in/out |
|---|---------|--------|--------------|
| 1 | ... | ... | ... |

Every new hypothesis must hold for ALL prior observations.

## RV8 quick checks (run early)

- [ ] SRC+STR conflict? (opcode & $0C) == $0C?
- [ ] Z-flag stable before T2↑?
- [ ] WR_DIR correct for this T2?
- [ ] SETDP decode conditions met? (T2 & XOR & !/ADDR & !/AC_WR)
- [ ] A15 hitting correct memory?
- [ ] Data page (U32) correct?

## Rules

- No fix before repro (step 1).
- No hypothesis before trace (step 2).
- No commitment before disproof (step 3).
- Always check both sim layers.
- Fix must pass: Verilog TB + chip_sim.py + hardware (if built).
