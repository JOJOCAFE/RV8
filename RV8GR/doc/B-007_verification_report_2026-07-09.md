# RV8GR Backlog B-007 Verification Report

Date: 2026-07-09
Workspace: `/home/jo/kiro/RV8`
Branch observed: `team-setup...origin/team-setup`
Scope: RV8GR verification/report/status only. Components were not edited.

## Summary

Status: PASS for all available non-physical RV8GR verification in this
environment.

Physical hardware status: BLOCKED. No assembled RV8GR hardware, ROM programmer
session, logic analyzer, oscilloscope, or live 1 MHz board run was available from
this environment, so no physical pass is claimed.

## Commands And Results

### Workspace discovery

Command:

```bash
git status --short --branch
```

Result:

```text
## team-setup...origin/team-setup
```

Command:

```bash
find RV8GR -maxdepth 3 -type f -name 'verify_docs.py' -o -name '*verify*.py' -o -name 'run_*.sh' | sort
```

Result:

```text
RV8GR/sim/verify_wiring.py
RV8GR/tools/run_all_verilog_tb.sh
RV8GR/tools/run_chip_level_full_verilog.sh
RV8GR/tools/run_chip_level_verilog.sh
```

Note: no `RV8GR/tools/verify_docs.py` exists in this checkout.

### Python simulator and tooling

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B sim/chip_sim.py
```

Result: PASS. Reported `ALL 8 CPU TESTS PASSED`; worst critical path margin at
5 MHz was 97 ns and max safe clock was 9.7 MHz.

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B sim/verify_wiring.py
```

Result: PASS. Reported `ALL WIRING VERIFIED` after LI, LI+ADDI, SB+LB,
SETDP+SB, and BEQ wiring checks.

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B sim/soft_debug.py
```

Result: PASS. Reported `ALL SOFT DEBUG TESTS PASSED`.

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/test_rv8gr_asm.py
```

Result: PASS. Python unittest reported `Ran 11 tests` and `OK`.

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR/sim
python3 -B chips/test_chips.py
```

Result: PASS. Reported `ALL 14 CHIP TYPES VERIFIED`.

### Simulation labs

Initial command:

```bash
cd /home/jo/kiro/RV8/RV8GR/sim
for f in sim_lab/lab*.py; do echo "=== $f ==="; python3 -B "$f"; done
```

Result: PARTIAL due to invocation/import path, not lab logic. Labs 01, 10, 12,
and 14 passed, while labs importing `chips` failed with:

```text
ModuleNotFoundError: No module named 'chips'
```

Corrected command:

```bash
cd /home/jo/kiro/RV8/RV8GR/sim
PYTHONPATH=. python3 -B sim_lab/lab01_power_clock.py && \
PYTHONPATH=. python3 -B sim_lab/lab02_ring_counter.py && \
PYTHONPATH=. python3 -B sim_lab/lab03_pc_counter.py && \
PYTHONPATH=. python3 -B sim_lab/lab04_address_mux.py && \
PYTHONPATH=. python3 -B sim_lab/lab05_rom_fetch.py && \
PYTHONPATH=. python3 -B sim_lab/lab06_ir_latch.py && \
PYTHONPATH=. python3 -B sim_lab/lab07_alu.py && \
PYTHONPATH=. python3 -B sim_lab/lab08_ac_mux.py && \
PYTHONPATH=. python3 -B sim_lab/lab09_z_flag.py && \
PYTHONPATH=. python3 -B sim_lab/lab10_branch_jump.py && \
PYTHONPATH=. python3 -B sim_lab/lab11_page_register.py && \
PYTHONPATH=. python3 -B sim_lab/lab12_ram_datapage.py && \
PYTHONPATH=. python3 -B sim_lab/lab13_full_system.py && \
PYTHONPATH=. python3 -B sim_lab/lab14_irq_bus.py
```

Result: PASS. Labs 01 through 14 all reported PASS.

### Verilog and chip-level HDL stack

Command:

```bash
cd /home/jo/kiro/RV8/RV8GR
tools/run_all_verilog_tb.sh
```

Result: PASS. Individual evidence:

```text
tb_rv8gr_asm: === ASSEMBLER TEST PASSED ===
tb_rv8gr_full: === ALL TESTS PASSED === (127 cycles)
tb_rv8gr_irq: ALL IRQ POLLING TESTS PASSED
tb_rv8gr_opcode_sweep: === OPCODE SWEEP PASSED: 512 cases (256 opcodes x Z=0/1) ===
tb_rv8gr_setdp: === SETDP TEST PASSED === (160 cycles)
tb_rv8gr_tasks: ALL TASK TESTS PASSED
tb_rv8gr_chip_level: RV8GR chip-level bring-up PASS
tb_rv8gr_chip_full: RV8GR chip-level full PASS
```

Icarus emitted repeated warnings that `rv8gr_cpu` has no explicit time unit or
precision. These warnings did not fail the benches.

## Physical Run Checklist

Use this checklist before marking B-007 physically complete.

| Step | Required evidence | Pass/Fail | Notes |
|------|-------------------|-----------|-------|
| Confirm assembled RV8GR board revision | Board photo or revision note matching current 36-package v1.0 docs | | |
| Power rails | Scope/DMM evidence for +5 V, GND continuity, no overcurrent | | |
| Clock/reset | Scope capture for reset release and 1 MHz clock | | |
| Ring counter | T0/T1/T2 probe capture showing one-hot sequence | | |
| ROM image | Exact `.asm`, `.bin`, and ROM programmer verify transcript | | |
| Fetch cycle | Probe/logic capture for PC $0000 -> $0001 -> $0002 and IR high/low latch | | |
| Full ISA smoke | Test ROM pass condition observed at LEDs/probe points | | |
| RAM page access | SB/LB or SETDP test evidence for RAM page $80 and one non-default page | | |
| Branch/page jump | Evidence for BEQ/J/SETPG expected PC behavior | | |
| IRQ polling | Evidence that IRQ latch is poll-visible and does not vector PC automatically | | |
| Clock margin | Repeat official target at 1 MHz; optional 2 MHz stress run | | |

## Blockers

- Physical RV8GR run is blocked by unavailable hardware access from this
  environment.
- No local `RV8GR/tools/verify_docs.py` exists, so the older doc-static checker
  mentioned in prior RV8GR memory could not be run here.
- There are unrelated untracked files under `RV8GR/programs/` before this report:
  `README.md`, `blink.asm`, `counter.asm`, and `echo.asm`. They were not touched.
