# RV8GR Real Build Timing Log

Purpose: record timing, bus-race, edge-trigger, and propagation-delay findings
from the physical RV8GR build. This file is the main CPU project record. If a
finding changes reusable chip/circuit proof, mirror it into
`/home/jo/kiro/Components`.

This file is an **evidence log**, not a build tutorial and not a wiring source:

- Use `01_wiring_guide.md` for official pin-level wiring and timing estimates.
- Use `05_debug_plan.md` for the student-facing step-by-step physical tests.
- Use `08_cpu_logical_test_protocol.md` and `11_four_model_equivalence.md` for
  virtual CPU logic signoff.
- Use this file to record measured real-board results, failures, fixes, and
  retest evidence.

Keep this file separate from the debug plan. Merging real build entries into the
student debug instructions would make the instructions noisy and would make it
harder to see which physical board actually passed which test.

## Current Rule

Do not accept a whole-system hardware result until these four hazards are
checked at the relevant build stage:

1. Timing margin
2. Bus racing
3. Positive/negative edge trigger behavior
4. Propagation delay into the destination latch or control input

Software simulation can prepare the test. Physical timing signoff needs real
evidence from the build.

## Required Evidence Matrix

Record these conditions when each stage is ready for timing qualification:

| Condition | Required evidence |
|---|---|
| 100-tick push switch | One clean state advance per press; no skipped T-state |
| 50 kHz | Slow electronic clock pass before MHz testing |
| 1 MHz | Official target pass |
| 2 MHz | Breadboard stress pass/fail with notes |
| 5 MHz | PCB/short-wire experiment only; record as pass/fail, not baseline |
| 4.5 V | Low-voltage margin observation |
| 5.0 V | Nominal-voltage result |
| 5.5 V | High-voltage margin observation |

For each voltage/frequency run, record at least: build stage, clock source,
observed pass/fail state, worst suspicious signal, instrument used, and any
change made before rerun.

## Build Stage Checklist

### 1. Clock, Reset, And Ring Counter

- Signals: `CLK`, `/RST`, `T0`, `T1`, `T2`
- Edge focus: one clean active clock edge per step; reset release must not
  double-trigger.
- Bus-race focus: none yet.
- Propagation focus: ring feedback settles before the next active clock.
- Pass evidence: one-hot `T0/T1/T2` for at least 100 ticks.
- If failed, update: `doc/05_debug_plan.md`, lab 01/02 docs, KiCad clock/reset
  wiring, and Components `RV8GR_ResetClockBringup` or `RV8GR_RingCounter`.

### 2. Program Counter And Branch/Jump Load

- Signals: `CLK`, `/RST`, `PC_INC`, `/PC_LD`, `PC0..PC15`, `PG0..PG7`,
  `IRL0..IRL7`
- Edge focus: `74HC161` samples on the expected clock edge; `/PC_LD` is active
  LOW before that edge.
- Bus-race focus: none, unless PC outputs fight address mux wiring.
- Propagation focus: branch/jump control to `/PC_LD`; RCO cascade to the next
  nibble.
- Pass evidence: count, hold, load, BEQ/BNE/J all happen on the correct edge.
- If failed, update: `doc/01_wiring_guide.md`, lab 03/10 docs, RTL/KiCad if
  wiring changed, and Components `RV8GR_PC16` or `RV8GR_BranchJumpControl`.

### 3. ROM/RAM, DBUS, IBUS, And Address Mux

- Signals: `ABUS0..15`, `A15`, ROM `/CE`, ROM `/OE`, RAM `/CE`, RAM `/OE` or
  `/WE`, `U7 /OE`, `U7 DIR`, `IBUS0..7`, `DBUS0..7`
- Edge focus: memory read data is stable before the destination latch edge.
- Bus-race focus: ROM, RAM, U7, U14, and U34 must never create two active
  drivers on the same bus.
- Propagation focus: address mux to chip select, memory output to DBUS, U7 to
  IBUS.
- Pass evidence: no overlap between old bus driver disable and new driver
  enable; selected memory speed grade is recorded.
- If failed, update: `doc/01_wiring_guide.md`, lab 04/05/12 docs, KiCad, RTL
  if generated wiring changed, and Components `RV8GR_AddressMux16`,
  `RV8GR_BusOwnership`, `RV8GR_RomDbusRead`, `RV8GR_StorePath`, or
  `RV8GR_DataPageMemory`.

### 4. Instruction Register, ALU, AC, And Z

- Signals: `T0`, `T1`, `T2`, `/IRL_OE`, `ACC_CLK`, `AC0..7`, `Z_flag`,
  ALU intermediate outputs if available
- Edge focus: U5 captures only on T0, U6 only on T1, AC/Z only on `ACC_CLK`.
- Bus-race focus: U34, U7, and U14 are mutually exclusive IBUS drivers.
- Propagation focus: IBUS/AC through XOR, adders, mux, then AC setup; AC to Z
  settle before branch use.
- Pass evidence: LI/ADDI/SUBI/XORI and branch-after-Z tests pass by
  single-step.
- If failed, update: `doc/01_wiring_guide.md`, lab 06-09 docs, RTL/KiCad if
  wiring changed, and Components `RV8GR_InstructionLatch` or
  `RV8GR_AluAccumulator`.

### 5. Page Registers, Store/Load, And Full System

- Signals: `PG_CLK`, `DP_Load`, `/ADDR_MODE`, `/AC_BUF`, `WR_DIR`, RAM `/WE`,
  `PC`, `AC`, `PG`, `DP`
- Edge focus: SETPG and SETDP latch on the intended edge only; store `/WE`
  happens after data is valid.
- Bus-race focus: store direction must disable ROM/RAM output before U7 writes
  DBUS.
- Propagation focus: page register output to jump target; store data to RAM
  setup before `/WE`; RAM read to AC setup.
- Pass evidence: boot sequence, Lab 13 `$AA` marker, RAM read/write marker,
  and page jump marker all pass.
- If failed, update: `doc/02_instruction_trace.md`, lab 11-13 docs, RTL/KiCad
  if wiring changed, and Components `RV8GR_PageDataRegisters`,
  `RV8GR_PageJumpTrace`, `RV8GR_StoreLoadBranchTrace`, or relevant lower-level
  package.

### 6. IRQ And RV8-Bus

- Signals: `EI_decode`, `/IRQ`, `IE`, `IRQ_FF`, RV8-Bus `CLK`, `/RST`, `/WR`,
  `/IRQ`, address/data pins
- Edge focus: EI rising sets IE; `/IRQ` LOW holds; `/IRQ` release HIGH latches
  IRQ_FF.
- Bus-race focus: external RV8-Bus devices must not drive DBUS while CPU or
  memory drives it.
- Propagation focus: IRQ_FF is visible for polling/debug, but v1.0 has no PC
  force path.
- Pass evidence: IRQ LED/latch behavior passes and PC does not auto-jump.
- If failed, update: lab 14 docs, bus wiring docs, KiCad, and Components
  `RV8GR_IRQLatch` or `RV8GR_InterruptTrace`.

## Bug / Change Entry Template

```text
Date:
Build stage:
Hazard: timing_margin | bus_race | edge_trigger_polarity | propagation_delay
Module/circuit:
Signal(s):
Voltage:
Clock/frequency:
Instrument:
Expected:
Observed:
Root cause:
Fix in RV8GR:
Fix in Components:
Verification rerun:
Remaining risk:
```

## Entries

Add newest entries below this line.
