# RV8GR CPU Logical Test Protocol

RV8GR owns CPU logical correctness: what the processor does after reset, how
instructions execute, how programs halt or pass, and whether assembler output
matches CPU behavior.

Components owns reusable chip definitions and virtual physical checks: pin
truth, bus-contention risk, edge polarity, propagation delay, R/C noise, and
package evidence.

Both are required, but they answer different questions.

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

### Assembler

Run:

```bash
cd RV8GR
python3 -B tools/test_rv8gr_asm.py
```

Must cover:

- All frozen opcode encodings.
- Aliases/macros: `MV`, `HLT`, `CLR`, `INC`, `DEC`, `SLL`, `JMP`.
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
```

Minimum pass cases:

- `LI`, `ADDI`, `SUBI`, `XORI`.
- Z flag set/clear from ALU results.
- `SB` and `LB` through RAM page `$80`.
- `SETDP` reads RAM page `$90` and ROM page `$00`.
- `SETPG` plus `J` reaches another ROM page.
- `BEQ` taken when Z=1.
- Halt loop is detected as `J self`.

### Full Program Tests

Assembly programs should be self-checking: failures halt early, success reaches
a known pass loop.

Required virtual programs:

- `programs/test_isa.asm`: instruction-level ISA smoke.
- `programs/test_all.asm`: broader assembler-to-CPU behavior.
- `programs/testrom.asm`: physical/virtual golden ROM.
- `programs/test_setdp.asm`: data-page and RAM-page behavior.

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

Run this before saying RV8GR virtual CPU logic is current:

```bash
cd /home/jo/kiro/RV8/RV8GR
python3 -B tools/test_rv8gr_asm.py
python3 -B sim/chip_sim.py
python3 -B sim/components_chip_sim.py
python3 -B sim/verify_wiring.py
python3 -B sim/verify_components.py
tools/run_all_verilog_tb.sh
```

Run this from Components for the separate virtual physical screen:

```bash
cd /home/jo/kiro/Components
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
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
