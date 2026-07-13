# RV8GR Components Verification Protocol

Date: 2026-07-10

Purpose: one Components-side reference for RV8GR chip readiness, split-record
testing, virtual bench mapping, circuit gates, system proof, and physical
build signoff.

This file replaces the older separate RV8GR DB notes for chip-level planning,
multi-level protocol, virtual bench mapping, Batch 2 audit, and the status
report. The machine-readable companions remain:

- `RV8GR/doc/rv8gr_chip_level_readiness.json`
- `RV8GR/doc/rv8gr_virtual_bench_plan.json`
- `lib/standard/VIRTUAL_TEST_GENERATOR_CONTRACT.json`
- `examples/circuits/RV8GR_COVERAGE_INDEX.json`
- `examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md`

## Current Status

| Level | Status | Evidence |
|---|---|---|
| Source/definition gate | PASS | `tests.test_db` passed |
| Chip-level behavior gate | PASS | `tests.test_generated_split_records` passed |
| Circuit-level package gate | PASS | `tests.test_lib_circuits` passed |
| Block UI/tooling gate | PASS | `tests.test_block_ui` passed |
| RV8GR whole-system Verilog gate | Recorded virtual checkpoint | Run `RV8GR/tools/run_all_verilog_tb.sh` from this checkout for current evidence; the Components end-to-end plan is a separate external artifact |
| Physical hardware signoff | BLOCKED | voltage/frequency/scope evidence still missing |

| Item | Count | Status |
|---|---:|---|
| RV8GR required chips | 18 | all listed in `RV8GR/doc/rv8gr_chip_level_readiness.json` |
| Chip split-record sets | 18 | all have truth/timing/tri-state/bus-fight/propagation records |
| RV8GR circuit packages | 22 | all indexed in `examples/circuits/RV8GR_COVERAGE_INDEX.json` |
| Indexed packages marked `Tested` | 22 | README/index/package/test checks pass |

## Required Chip Set

The machine-readable status lives in `RV8GR/doc/rv8gr_chip_level_readiness.json` and
is enforced by `tests.test_generated_split_records`.

| Part | RV8GR role | Current chip-level gate |
|---|---|---|
| `74HC00` | NAND gates for control decode and glue logic | Ready for circuit functional tests |
| `74HC04` | Inverters for active-low control and reset/clock glue | Ready for circuit functional tests |
| `74HC21` | Dual 4-input AND gates for decode and control qualification | Ready for circuit functional tests |
| `74HC32` | OR gates for control composition | Ready for circuit functional tests |
| `74HC74` | Positive-edge D flip-flops for flags, IRQ latch, and synchronous state | Ready for circuit functional tests |
| `74HC86` | XOR gates for ALU and compare/control paths | Ready for circuit functional tests |
| `74HC157` | Quad muxes for address and data path selection | Ready for circuit functional tests |
| `74HC161` | Positive-edge program counter and counter-style state | Ready for circuit functional tests |
| `74HC164` | Serial-in parallel-out ring/control sequencing support | Ready for circuit functional tests |
| `74HC245` | Bidirectional bus transceiver for shared bus isolation | Ready for circuit functional tests |
| `74HC283` | 4-bit binary adders for the ALU | Ready for circuit functional tests |
| `74HC541` | Octal buffers for unidirectional bus and visible outputs | Ready for circuit functional tests |
| `74HC574` | Positive-edge octal registers for IR, AC, page, and data-path latches | Ready for circuit functional tests |
| `74HC688` | 8-bit equality comparator for branch/page/control decisions | Ready for circuit functional tests |
| `62256` | Generic 32K x 8 SRAM-compatible RAM footprint | Ready for circuit functional tests when Samsung KM62256C-compatible SRAM is installed |
| `AS6C62256` | Alliance 32K x 8 SRAM option for RAM | Ready for circuit functional tests |
| `AT28C256` | 32K x 8 EEPROM option for program ROM | Ready for circuit functional tests |
| `SST39SF010A` | Flash ROM option for program storage | Ready for circuit functional tests |

Each part has a layered package with `definition/definition.json`, local
simulation files, symbol metadata, generated artifacts, and split test records
for truth table, timing, tri-state, bus-fight, and propagation coverage.

## Level 0: Source And Definition Gate

Required evidence for every real chip:

- local or stable manufacturer datasheet reference
- package and pinout
- active-low names and bus directions
- behavior equation or truth table
- timing/electrical rows when present in the datasheet
- explicit missing-property status when any row is not available

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_db
```

Virtual instruments: `InputSource`, `Probe`, `OutputAssert`.

## Level 1: Chip-Level Behavior Gate

Required split records for every RV8GR chip:

- `truth_table.json`
- `timing.json`
- `tri_state.json`
- `bus_fight.json`
- `propagation.json`

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

Pass condition: all 18 RV8GR chips have all split records, every truth-table
record declares `edge_criteria`, and generated record tests pass. This is a
functional/model gate, not physical timing signoff.

Every clocked chip must identify its trigger edge and no-edge hold behavior.
Level-sensitive chips use `trigger_edge: none`. Memory chips must declare their
write/read control window and high-Z cases.

## Level 2: Circuit-Level Gate

Each `examples/circuits/RV8GR_*` package must include:

- `circuit.json`
- `README.md`
- at least one `tests/*.json` proof file
- package entry in `examples/circuits/RV8GR_COVERAGE_INDEX.json`
- executable coverage in `python/tests/test_lib_circuits.py`

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

Pass condition: all indexed circuit packages are tested, all proof vectors
execute, bus conflicts are caught, and physical timing claims remain blocked
unless bench evidence exists.

## Level 3: System-Level Gate

Components-side pass commands, run from `/home/jo/kiro/Components`:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

RV8GR-side whole-system command:

```sh
/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh
```

Required RV8GR pass markers:

- `=== ASSEMBLER TEST PASSED ===`
- `=== ALL TESTS PASSED ===`
- `ALL IRQ POLLING TESTS PASSED`
- `=== OPCODE SWEEP PASSED: 512 cases`
- `=== SETDP TEST PASSED ===`
- `ALL TASK TESTS PASSED`
- `RV8GR chip-level bring-up PASS`
- `RV8GR chip-level full PASS`

Pass condition: Components proofs and RV8GR benches agree on instruction
behavior, bus ownership, reset/boot behavior, page/data behavior, and IRQ v1.0
boundaries. This is non-physical evidence only. The physical gate remains
blocked until the real board records the 1 MHz baseline and required measured
power, edge, bus-deadband, memory, and timing evidence.

## Virtual Bench Mapping

Chip-level virtual bench generation is defined by
`lib/standard/VIRTUAL_TEST_GENERATOR_CONTRACT.json`; generated RV8GR coverage lives in
`RV8GR/doc/rv8gr_virtual_bench_plan.json`.

Summary:

- RV8GR chips: 18
- Split records per chip: 5
- Total chip/record mappings: 90
- OutputAssert mappings: 90
- DelayNoise propagation-stress mappings: 18
- Required instruments all declared: true

| Split record | Virtual instruments | Generated checks |
|---|---|---|
| `truth_table` | `InputSource`, `Probe`, `OutputAssert` | drive each input vector; sample every named output; assert expected logic value |
| `timing` | `ClockSource`, `Switch`, `Probe`, `OutputAssert` | apply required clock profile; sample after declared delay; assert setup/hold or no-edge behavior |
| `tri_state` | `InputSource`, `BusProbe`, `OutputAssert` | enable output; disable output; assert high-Z when disabled |
| `bus_fight` | `BusProbe`, `OutputAssert` | force safe single-driver vector; force conflict vector; assert conflict is reported |
| `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` | apply source transition; inject optional delay/noise; sample destination after timing budget; assert output still meets expectation |

Virtual benches prove model behavior and stress selected assumptions. They are
not physical signoff.

## Virtual Physical-System Fault Gate

Every chip-level, circuit-level, and whole-system virtual test must include
traps for common AI-generated hardware mistakes that can look plausible in text
but fail on a real breadboard.

| Fault class | Required virtual test | Fix method |
|---|---|---|
| Wrong physical pin number or pin name | Compare every circuit pin reference against DB pin number, pin name, direction, active-low marker, and local pinout evidence before simulation starts. | Fix the chip definition or source-backed pin map first; do not move circuit wires to hide a bad definition. |
| Output-to-output wiring with no valid bus condition | Allow direct output-to-input wiring. Allow multiple outputs only on a named bus when enable conditions prove at most one driver at a time; force a conflict vector with `BusProbe`. | Add tri-state control, buffer/transceiver direction, or output-enable sequencing so the old driver is high-Z before the new driver turns on. |
| Wrong positive/negative or rising/falling edge | For every edge-triggered part, prove the declared trigger edge captures and the opposite edge holds; reset/load priority must be explicit. | Move the signal to the correct clock phase or add an intentional inverter. Keep expected behavior tied to the datasheet edge. |
| Propagation delay or R/C delay creates bus overlap or early sampling | Use `RCParasitic` and `DelayNoise` on `CLK`, `/RST`, `IBUS`, `DBUS`, `/OE`, and `/WE`; assert positive disable-to-enable deadband and destination setup/hold margin. | Add phase separation, delay the new enable, disable the old driver earlier, shorten or buffer the net, or lower the clock until measured margin is positive. |

Pass condition: a virtual physical-system test must fail loudly for wrong pin
truth, meaningless output-output wiring, bad edge polarity, and negative delay
deadband. The report must name the fix method instead of changing the expected
result to match the bug.

## Physical Build Signoff Gate

Required physical voltage points:

- 4.5 V
- 5.0 V
- 5.5 V

Required clock profiles:

- 100 manual push-switch ticks
- 50 kHz
- 1 MHz

Optional profiles, recorded separately and never used as breadboard signoff
gates:

- 2 MHz breadboard stress
- 5 MHz PCB-only experiment

Required physical evidence:

- installed EEPROM and SRAM markings
- selected datasheet timing rows
- VCC at power entry and far IC
- clock/reset edge quality
- memory output-float deadband
- bus turn-off before turn-on deadband
- representative driver-pin and destination-pin scope captures
- breadboard R/C calibration for `CLK`, `/RST`, `IBUS`, `DBUS`, and memory
  control nets

Pass condition: the real build passes the 1 MHz breadboard baseline and its
required measurements without bus fights, bad edge triggers, timing-window
failures, or supply/edge-quality violations. Record 5 MHz separately only as
an optional PCB-only experiment.

Do not write "hardware ready" unless Level 4 passes.

## Report Rule

Every RV8GR report must separate:

- passed virtual/model evidence
- passed whole-system simulation evidence
- blocked physical evidence
- next required physical capture

## Commands

```sh
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_block_ui
```

Last recorded results:

- `Components DB tests passed`
- `Components generated split-record tests passed`
- `Components library circuit tests passed`
- `Components block UI tests passed`

## Next Target

Extend the same complete-set gate from the RV8GR-used chips to the rest of the
migrated IC catalog, while keeping physical hardware signoff separate from
virtual/model readiness.
