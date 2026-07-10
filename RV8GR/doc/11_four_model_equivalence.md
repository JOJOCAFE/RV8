# RV8GR Four-Model Equivalence Guide

Updated: 2026-07-10

RV8GR keeps four virtual CPU models because each one answers a different
question. They must agree before we trust a CPU logic change.

This is the short student-facing explanation. The full maintainer checklist and
required regression commands live in `08_cpu_logical_test_protocol.md`.

## Why This File Exists

Keep this file separate because it answers the first student question: "Why are
there four simulators?" It should stay short enough to read before running the
test.

Do not put the full regression protocol here. Use
`08_cpu_logical_test_protocol.md` for coverage rules, signoff lanes, exact
maintainer commands, and pass/fail policy.

## The Four Models

| Model | File | What it proves |
|---|---|---|
| Python CPU | `sim/chip_sim.py` | Fast CPU logic check for ISA, branches, RAM, ROM, pages, and IRQ flags. |
| Components-backed Python CPU | `sim/components_chip_sim.py` | The same Python CPU runner can use Components `chiplib` chip objects. |
| Behavioral Verilog CPU | `rtl/rv8gr_cpu.v` | HDL reference behavior for the CPU. |
| TTL chip-level Verilog CPU | `rtl/rv8gr_chip_level.v` | Components TTL-chip Verilog netlist agrees with the HDL reference. |

The Components-backed Python CPU is not a second independent CPU algorithm. It
is an adapter-backed runner that reuses the RV8GR Python CPU logic with
Components chip definitions.

## Shared Test Source

The all-ISA equivalence test comes from one assembly file:

```text
programs/all_isa_equivalence.asm
```

The Verilog runner assembles it to a temporary `.memh` file. The Python checker
assembles the same source in memory. This prevents the old problem where Python
and Verilog used hand-copied versions of the same test.

## What The Test Checks

Run:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/check_python_verilog_equivalence.py
```

Expected pass markers:

```text
Verilog checkpoint stream: 55 checkpoints
CPUSim matches Verilog checkpoint stream, final state, and RAM checkpoints
ComponentsCPUSim matches Verilog checkpoint stream, final state, and RAM checkpoints
RV8GR Python/Verilog equivalence PASS
```

The checker verifies:

- both Verilog models agree with each other at 55 architectural checkpoints;
- both Python CPU sims match the exported Verilog checkpoint stream;
- all four models finish at the same architectural state;
- selected RAM writes match.

## What The Test Does Not Prove

This is a CPU logic equivalence test. It does not replace:

- Components virtual physical checks for pin truth, bus contention, edge
  polarity, propagation delay, and R/C noise;
- physical board tests for voltage, clock, reset, wiring, bus ownership, and
  logic-analyzer timing evidence.

The equivalence program is also a simulator scoreboard fixture, not a physical
boot ROM. Physical ROMs and student programs must still initialize CPU state
explicitly before relying on PG, DP, AC, or Z.

## When To Run It

Run the four-model equivalence check after changing:

- assembler encoding;
- CPU instruction behavior;
- Python CPU simulation;
- Components chip definitions used by RV8GR;
- behavioral Verilog;
- chip-level Verilog export;
- the all-ISA equivalence program.

For full virtual CPU signoff, run:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/test_rv8gr_asm.py
python3 -B sim/chip_sim.py
python3 -B sim/components_chip_sim.py
python3 -B sim/test_cpu_logical_protocol.py
python3 -B tools/check_python_verilog_equivalence.py
tools/run_all_verilog_tb.sh
```
