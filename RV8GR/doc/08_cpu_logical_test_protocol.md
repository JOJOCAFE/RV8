# RV8GR CPU Logical Test Protocol

RV8GR owns CPU logical correctness: what the processor does after reset, how
instructions execute, how programs halt or pass, and whether assembler output
matches CPU behavior.

Components owns reusable chip definitions and virtual physical checks: pin
truth, bus-contention risk, edge polarity, propagation delay, R/C noise, and
package evidence.

Both are required, but they answer different questions.

For a shorter student-facing explanation of the two Python sims, two Verilog
models, and the shared all-ISA test, see `doc/11_four_model_equivalence.md`.

## Relationship To Other Test Docs

Keep this document separate. It is the maintainer protocol for virtual CPU
logic signoff, not a student lab sheet and not a physical evidence log.

| Document | Purpose |
|---|---|
| `08_cpu_logical_test_protocol.md` | Canonical CPU logic regression lanes, coverage, commands, and signoff boundary. |
| `11_four_model_equivalence.md` | Short student explanation of why two Python sims and two Verilog models must agree. |
| `05_debug_plan.md` | Physical build procedure students follow on the bench. |
| `07_real_build_timing_log.md` | Real-board voltage/frequency, timing, bus-race, edge, propagation-delay, fix, and retest evidence. |

Merging these would hide the main distinction: RV8GR owns CPU behavior, while
Components and the physical build own pin truth, bus contention, edge polarity,
delay/noise assumptions, and measured hardware evidence.

## External Practices Adapted

This protocol borrows proven verification ideas and makes them small enough for
RV8GR:

- RISC-V architectural tests use self-checking assembly tests for a Device Under
  Test, but still warn that certification tests are not complete verification:
  https://github.com/riscv/riscv-arch-test
- RISCV-DV combines directed assembly, random instruction streams, coverage, and
  co-simulation against instruction-set simulators:
  https://github.com/chipsalliance/riscv-dv
- cocotb shows the value of Python-driven virtual testbenches, direct stimulus,
  monitors, and regression reporting:
  https://docs.cocotb.org/en/stable/
- UVM standard practice separates stimulus, monitor, scoreboard, and reusable
  verification components:
  https://www.accellera.org/downloads/standards/uvm

RV8GR does not need full UVM or RISC-V tooling. It needs the same discipline:
self-checking programs, a reference model, repeatable regression commands, and
clear pass/fail signals.

## Test Lanes

| Lane | Owner | Purpose | Tool |
|---|---|---|---|
| Assembler encoding | RV8GR | Prove source maps to frozen opcodes and bad source fails loudly | `tools/test_rv8gr_asm.py` |
| CPU reference behavior | RV8GR | Prove ISA, branches, memory map, and halt behavior in fast Python | `sim/chip_sim.py` |
| Components-backed CPU behavior | RV8GR + Components | Prove the same CPU tests run while using Components chip definitions | `sim/components_chip_sim.py` |
| RTL behavioral comparison | RV8GR | Compare optimized/behavioral HDL against CPU expectations | `tools/run_all_verilog_tb.sh` behavioral benches |
| TTL-chip HDL system | RV8GR + Components | Prove chip-level Verilog netlist runs using Components TTL models | `tools/run_chip_level_*.sh` |
| Behavioral vs chip-level HDL scoreboard | RV8GR + Components | Prove both Verilog levels agree at architectural checkpoints on the same ROM image | `tools/run_dual_verilog_compare.sh` |
| Python vs Verilog equivalence | RV8GR + Components | Prove both Python CPU sims and both Verilog CPU models agree on the same all-ISA ROM source | `tools/check_python_verilog_equivalence.py` |
| Virtual physical screen | Components | Check pin truth, bus contention, edge polarity, and delay/noise assumptions | `chiplib.cli circuit-faults` |
| Physical signoff | RV8GR physical build | Prove the real breadboard works | Lab/debug plan evidence |

## Required Logical Coverage

### Boot Contract

Every virtual CPU test must begin from the v1.0 boot contract:

- PC starts at `$0000`.
- T-state starts at T0.
- IRQ latch and IE are clear after reset.
- PG, DP, AC, and Z are treated as unknown on real hardware, even if a simulator
  initializes them for convenience.
- Test ROMs must initialize architectural state before relying on it:
  `SETDP $80`, `SETPG $00`, then a known AC/Z setup such as `LI $00`.

The all-ISA equivalence fixture is an exception because it is a simulator
scoreboard fixture, not a physical boot ROM. `tb_rv8gr_dual_compare.v` forces
the same reset-visible state into both Verilog models before release, and the
Python checker starts from the simulator reset contract. Physical ROMs and
student programs must still initialize state explicitly.

### Assembler

Run:

```bash
cd RV8GR
python3 -B tools/test_rv8gr_asm.py
```

Must cover:

- All frozen opcode encodings.
- Aliases/macros: `MV`, `HLT`, `CLR`, `INC`, `DEC`, `NOT`, `SLL`, `JMP`.
- `NOT` is assembler-only and must emit `XORI $FF`; it is not a new frozen ISA opcode.
- `.org`, `.db`, labels, `hi()` and `lo()`.
- Page-safe branch and jump validation.
- Output bounds and overlap errors.
- Unsupported macro rejection.

### ISA And Program Behavior

Run:

```bash
cd RV8GR
python3 -B sim/chip_sim.py
python3 -B sim/components_chip_sim.py
python3 -B sim/test_cpu_logical_protocol.py
python3 -B sim/test_basic_min.py
```

Minimum pass cases:

- `LI`, `ADDI`, `SUBI`, `XORI`.
- `NOT` pseudo-instruction truth table, assembled through `XORI $FF`, for
  boundary values `$00`, `$01`, `$55`, `$7F`, `$80`, `$AA`, `$F0`, `$0F`, `$FF`.
- Z flag set/clear from ALU results.
- `SB` and `LB` through RAM page `$80`.
- `SETDP` reads RAM page `$90` and ROM page `$00`.
- `SETPG` plus `J` reaches another ROM page.
- `BEQ` taken when Z=1.
- Halt loop is detected as `J self`.
- The same directed programs must pass on both `CPUSim` and
  `ComponentsCPUSim`.

### Full Program Tests

Assembly programs should be self-checking: failures halt early, success reaches
a known pass loop.

Required virtual programs:

- `programs/test_isa.asm`: instruction-level ISA smoke.
- `programs/test_all.asm`: broader assembler-to-CPU behavior.
- `programs/testrom.asm`: physical/virtual golden ROM.
- `programs/test_setdp.asm`: data-page and RAM-page behavior.
- `programs/test_not.asm`: assembler pseudo-instruction ROM test for `NOT`
  (`XORI $FF`) across boundary bit patterns.
- `programs/basic_min.asm`: B-011 phase 1 BASIC-style ROM runtime smoke.

The pass condition is not "simulation ended." The pass condition is reaching
the documented pass loop with expected AC/Z/PG/PC state.

For `tb/tb_rv8gr_asm.v`, do not accept `=== ASSEMBLER TEST PASSED ===` alone.
The bench must also show that `programs/testrom.hex` was found and reaches:

```text
Halted at PC=$0084 after 187 cycles
AC=$00 Z=1 PG=$00
=== ASSEMBLER TEST PASSED ===
```

A `$readmemh` missing-file warning invalidates that run even if the bench later
prints a pass banner.

### Dual Verilog Comparison

Run:

```bash
cd RV8GR
tools/run_dual_verilog_compare.sh
python3 -B tools/check_python_verilog_equivalence.py
```

This bench runs both Verilog versions together:

- `rtl/rv8gr_cpu.v` is the behavioral/logical CPU model.
- `rtl/rv8gr_chip_level.v` is the KiCad/Components TTL-chip netlist.
- `programs/all_isa_equivalence.asm` is the single shared source for the
  all-ISA equivalence program. The Verilog runner assembles it to a temporary
  `.memh`; the Python checker assembles the same source in memory.

The behavioral model records architectural checkpoints. The chip-level model
must later reach the same checkpoints with matching `PC`, `AC`, `Z`, `PG`, `DP`,
`IE`, `IRQ_FF`, and selected RAM bytes.

The dual comparison program must cover every frozen ISA command at least once:

| Group | Commands |
|---|---|
| Baseline/control | `NOP`, `EI`, `DI` |
| Jump/branch | `J`, `BEQ`, `BNE` |
| ALU immediate | `LI`, `ADDI`, `SUBI`, `XORI` |
| ALU memory/register | `ADD`, `SUB`, `XOR`, `LB`, `SB` |
| Page/data control | `SETPG`, `SETPG_R`, `SETDP` |
| IRQ protocol | `/IRQ` release/rising edge sets `IRQ_FF`; no automatic PC vector |

A pass means the two Verilog levels agree on the tested program-level CPU
behavior. It is not a formal proof that every internal wire or delay matches
cycle-by-cycle.

The Python equivalence checker then verifies:

- `tb_rv8gr_dual_compare.v` exports the Verilog architectural checkpoints as
  `VERILOG_CHECKPOINT` lines.
- `sim/chip_sim.py` matches the exported Verilog checkpoint stream.
- `sim/components_chip_sim.py` matches the exported Verilog checkpoint stream
  while using Components `chiplib` adapters for chip objects. It is not an
  independent net-level Python CPU algorithm.
- Both Python sims also match the final Verilog architectural state and the RAM
  checkpoints used by the Verilog dual comparison.

### IRQ Logical Behavior

RV8GR v1.0 has polling IRQ only.

Required checks:

- `EI` sets IE.
- `DI` is inert in the 36-package baseline.
- `/IRQ` release/rising edge latches IRQ_FF.
- IRQ never vectors the PC automatically.
- PC is not automatically saved to RAM.

### Memory Map

Required checks:

- ROM `$0000-$7FFF` fetches and data reads work.
- RAM `$8000-$FFFF` load/store works.
- `DP=$00-$7F` reads ROM.
- `DP=$80-$FF` reads/writes RAM.
- I/O slot addresses in `$FF10-$FF2F` are logical memory-map addresses; devices
  are external and must be tested separately.

## Regression Command

Run this before saying RV8GR virtual CPU logic is current. These commands are
the current non-physical CPU verification route; their PASS output is not
physical-board evidence:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/test_rv8gr_asm.py
python3 -B sim/chip_sim.py
python3 -B sim/components_chip_sim.py
python3 -B sim/test_cpu_logical_protocol.py
python3 -B sim/test_basic_min.py
python3 -B tools/check_python_verilog_equivalence.py
python3 -B sim/verify_wiring.py
python3 -B sim/verify_components.py
tools/run_all_verilog_tb.sh
```

Run this from the external Components checkout for the separate virtual
physical screen. It is a model-level screen, not a substitute for the measured
1 MHz breadboard baseline recorded in `07_real_build_timing_log.md`:

```bash
cd /home/jo/kiro/Components
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults examples/circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
```

## Scoreboard Rule

Every test must have an expected architectural result:

- PC expected value or pass-loop address.
- AC expected value.
- Z expected value.
- PG and DP expected values when used.
- RAM bytes expected after stores.
- IRQ/IE expected latch state when tested.

Tests that only print text without asserting expected state are not signoff
tests.

## Future Test Expansion

Add these after the current deterministic suite stays green:

1. Program-level runner that loads `.bin` files and checks pass-loop labels from
   `.lst` files.
2. Directed instruction matrix: every opcode with representative operands,
   including boundary values `$00`, `$01`, `$7F`, `$80`, `$FE`, `$FF`.
3. Small deterministic random program generator with a Python reference model.
4. Coverage report by instruction, branch taken/not-taken, memory page, and
   halt/pass outcome.
5. Boot-loader/programmer logical tests: ROM image loads, reset starts at
   `$0000`, and programmed bytes match assembled bytes.

## Signoff Boundary

Virtual CPU logic signoff means RV8GR behaves correctly in software and HDL.
It does not mean the breadboard is physically signed off.

Physical signoff still requires measured power, reset, clock, bus ownership,
ROM/RAM behavior, burn-in, and timing evidence from the real build.
