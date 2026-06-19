---
name: debug-mantra
description: Four-mantra hardware debugging discipline for RV8 CPU builds. Reproduce → trace the fail path → falsify the hypothesis → cross-reference every breadcrumb. Applies to Verilog sim, gate-level sim (chip_sim.py), and physical breadboard debugging. Trigger on /debug-mantra and proactively when debugging starts — user reports a bug, signal glitch, test failure, hang, or unexpected behavior in simulation or hardware.
---

# Debug Mantra (RV8 Hardware)

Four-step discipline for any debug session. Recite verbatim, then apply in order.

## Recite this — verbatim, as the first thing in your first response

> **Mantra:**
> 1. **First is reproducibility.** Can the issue be reproduced reliably?
> 2. **Know the fail path.** Debugger first; then source trace + knob enumeration; then in-code instrumentation.
> 3. **Question your hypothesis.** What would disprove it?
> 4. **Every run is a breadcrumb.** Cross-reference all of them.

Then begin work.

---

## 1. Reproduce reliably

Build a runnable repro before anything else.

### Verilog / gate-level sim
- Write a minimal .bin or .asm test that triggers the bug deterministically.
- Run through both `rv8gr_cpu.v` (iverilog) AND `chip_sim.py` — do they agree?
- If they disagree, the bug is in ONE of them. That's already a clue.
- Pin: clock cycle count, initial RAM/ROM state, register values.

### Physical hardware
- Isolate to a single instruction or sequence. Use the programmer to flash a minimal test ROM.
- Record: which instruction, what address, what data page, what Z-flag state.
- Flaky? Suspect timing. Try: slower clock, add decoupling caps, check probe loading.
- No repro at all? Ask for scope captures, LED states, or bus analyzer output. Do **not** hypothesise.

Target: a fast, deterministic pass/fail signal. One instruction sequence, one expected result.

## 2. Know the fail path

Once reproducible, find *where* it breaks. Try in this order — escalate only when prior tactic fails.

### Level 1: Simulation trace
- Run `chip_sim.py` with `--trace` or add prints at the suspected cycle.
- Check the Verilog VCD waveform (`$dumpvars`). Look at T0/T1/T2 cycle boundaries.
- Compare expected vs actual: PC, AC, IBUS, address bus, control signals.

### Level 2: Knob enumeration
For RV8-GR, the knobs that influence behavior:
- **Opcode bits** [7:0]: SUB, XOR, MUX, AC_WR, SRC, STR, BR, JMP
- **T-state**: T0, T1, T2 — which phase fails?
- **Data Page** (U32): is SETDP state correct?
- **Z-flag** (U21/U22): async preset timing
- **Bus direction**: WR_DIR = T2 AND STORE
- **A15 chip select**: ROM vs RAM selection
- **SRC+STR guard**: BUF_OE_SAFE (U25 gate 3)

Flip one knob at a time. Does the bug follow the knob or stay fixed?

### Level 3: Physical instrumentation
- Scope on suspected signal. Priority: CLK, /T2, IBUS, address bus MSB.
- Logic analyzer on control signals during the failing instruction.
- Tag each measurement: `[HW-xxxx]` prefix for easy reference.
- Check: setup/hold violations, glitches at T-state transitions, bus contention (two drivers active).

## 3. Falsify the hypothesis

When a candidate root cause surfaces:

- Does it explain the symptom **end-to-end**? Walk the signal path through the schematic.
- What is the simplest **proof**? (e.g., "if I change this opcode bit, the bug should move")
- What is the cleanest **disproof**? Run the **disproof first**.
- Generate 3–5 ranked hypotheses. For hardware bugs, common classes:
  1. Bus contention (two outputs driving same bus)
  2. Timing/race (signal arrives too late for clock edge)
  3. Wrong wiring (pin swap, missing connection)
  4. Logic error (wrong gate, inverted signal)
  5. Power/ground (floating inputs, inadequate decoupling)

## 4. Every run is a breadcrumb

Maintain a running **ledger** of every experiment:

| # | What changed | Result | Ruled in/out |
|---|---|---|---|
| 1 | ... | ... | ... |

- When a new hypothesis surfaces, walk the ledger. Does it hold for **every** prior observation?
- If any past run contradicts it → hypothesis is wrong or incomplete.
- Design the **single experiment** whose outcome makes it certain. Run that next.

---

## RV8-specific checks (run these early)

Before deep debugging, rule out the known hazards:

- [ ] **SRC+STR conflict?** Does opcode have bit3 AND bit2 set? (64 forbidden opcodes)
- [ ] **Z-flag timing?** Is branch decision stable before T2 rising edge?
- [ ] **Bus direction?** Is WR_DIR correct for this instruction's T2 phase?
- [ ] **SETDP decode?** U33 = T2 & XOR_MODE & /ADDR_MODE & /AC_WR — all conditions met?
- [ ] **A15 select?** Is the access hitting ROM vs RAM correctly?
- [ ] **Data page?** Is U32 holding the expected value from last SETDP?

## Operating rules

- Recite the mantra block **once** per debug session, verbatim. Do not re-recite mid-session.
- If user says "skip the mantra" → skip recital but apply the four steps silently.
- Apply steps **in order**:
  - No fix before step 1 (reliable repro exists).
  - No hypothesis testing before step 2 (fail path narrowed).
  - No commitment before step 3 (disproof attempted).
  - No declaration before step 4 (all breadcrumbs consistent).
- **Sim vs hardware**: always check if the bug exists in BOTH sim layers. If only in hardware → physical issue. If only in sim → sim bug. If in both → logic/design bug.
- When fix is found, verify it passes in: (1) Verilog testbench, (2) chip_sim.py, (3) hardware (if built).
