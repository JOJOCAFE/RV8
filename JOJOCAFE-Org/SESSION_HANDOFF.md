# Session Handoff

Updated: 2026-07-10

## Current State

- B-010 example ASM programs are implemented and assembler-verified.
- B-007 non-physical verification report is available; physical B-007 remains blocked until hardware evidence exists.
- Components repo is pushed and clean at `87bcfdc Save Components student guide handoff`.
- Components remote: `git@github.com:JOJOCAFE/Components.git`, branch `main`.
- RV8 repo is pushed through `1470963 Fix RV8 README project status`.
- RV8 remote: `git@github.com:JOJOCAFE/RV8.git`, branch `team-setup`.
- RV8 team/skill updates are in this repo under `JOJOCAFE-Org/`; current work merges the latest Components skill/status into the RV8 team operating docs.
- RV8GR verification tooling now writes Verilog `.vvp/.vcd` artifacts to `RV8GR_BUILD_DIR` or `/tmp/rv8gr-verilog`, so source folders stay clean while testbenches still support manual local VCD names.
- RV8GR Python chip behavior tests now run from repo root with `python3 -B RV8GR/sim/chips/test_chips.py`.
- RV8GR now separates CPU logical tests from Components virtual physical tests. CPU logic is documented in `RV8GR/doc/11_cpu_logical_test_protocol.md`; Components remains responsible for pin/bus/edge/delay/noise screens.
- `RV8GR/sim/components_chip_sim.py` is the standalone Components-backed Python CPU runner using vendored `chiplib` chip definitions.
- `RV8GR/sim/test_cpu_logical_protocol.py` is the executable protocol test suite. It assembles directed CPU programs and scoreboards both `CPUSim` and `ComponentsCPUSim`.
- RV8GR Verilog signoff rule: behavioral `rtl/rv8gr_cpu.v` benches are comparison only. Shipping confidence must include `rtl/rv8gr_chip_level.v` compiled with Components TTL-chip Verilog models (`ttl_74hc*`, `62256`, `at28c256`) through the chip-level runner scripts.
- `Programmer/KICAD/.history` is clean at its nested `master` checkout.
- Existing untracked file `RV8GR/doc/10_real_build_timing_log.md` was left untouched; do not stage it unless Jo explicitly asks.

## Components Library Facts

- Shared library path: `/home/jo/kiro/Components`.
- Python package path: `/home/jo/kiro/Components/python`.
- Student guide: `/home/jo/kiro/Components/STUDENT_GUIDE.md`.
- Service/CLI/API contract: `/home/jo/kiro/Components/SERVICE_CONTRACT.md`.
- Python simulator uses DIP-style pin number/name access and propagation-delay scheduling.
- `StimulusController` default channels: 64 inputs (`IN0..IN63`) and 8 clocks (`CLK0..CLK7`).
- Clock stimulus is physical-pin and edge aware:
  - default rising edge
  - 74HC73 and 74HC112 use falling-edge `CP`
  - 74HC74 sections, 74HC595 `SRCLK`/`RCLK`, and 74HC593 `RCK`/`CCK` are pin-specific
- `chiplib.loader` preloads `.bin`, Intel HEX, or text-hex data into ROM/RAM `.data`.
- Python and Verilog component behavior must remain compatible.
- Python schematic backend now supports buses, pull-up/pull-down style normal states, probes/test logic, simple JSON-friendly schematics, and netlist/Verilog export paths for RV8GR-style chip-level work.
- Virtual physical checker command:
  `PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json`
- Checker focus: pin-number/name/active-low mistakes, unsafe output-output wiring, missing edge polarity statements, and timing/noise risk on shared or stress nets.
- Virtual R/C and delay-noise checks are early-risk instruments; physical build still needs real voltage, frequency, wiring, scope/logic-analyzer, and timing evidence.

## Verification Evidence

Last green checks:

```sh
cd /home/jo/kiro/RV8
python3 -B RV8GR/sim/chip_sim.py
python3 -B RV8GR/sim/components_chip_sim.py
python3 -B RV8GR/sim/test_cpu_logical_protocol.py
python3 -B RV8GR/sim/verify_wiring.py
python3 -B RV8GR/sim/soft_debug.py
python3 -B RV8GR/tools/test_rv8gr_asm.py
python3 -B RV8GR/sim/chips/test_chips.py
python3 -B RV8GR/sim/verify_components.py
cd /home/jo/kiro/RV8/RV8GR
tools/run_all_verilog_tb.sh

cd /home/jo/kiro/Components
PYTHONPATH=python python3 -B -m chiplib.cli validate Examples/nand.json
PYTHONPATH=python python3 -B -m chiplib.cli run Examples/nand.json
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
PYTHONPATH=python python3 -B -m chiplib.api --stdio
PYTHONPATH=python python3 -B -m tests.test_cli
PYTHONPATH=python python3 -B -m tests.test_api
PYTHONPATH=python python3 -B -m tests.test_contracts
git diff --check
```

Expected pass markers:

- RV8GR Python, chip behavior, Components package coverage, behavioral Verilog benches, and TTL-chip Components Verilog system benches pass.
- CLI/API tests pass.
- `circuit-faults` accepts the RV8GR whole-system virtual circuit with zero pin, bus-contention, edge-polarity, or propagation-delay/deadband findings.
- `git diff --check` reports no whitespace errors.

## Next Session

1. Keep physical B-007 blocked until hardware photos/logs/test output exist; cite the non-physical report separately.
2. Use B-010 example ASM programs for ROM/programmer prep once the physical ROM workflow is ready.
3. Continue remaining Components full-catalog mappings only after checking module ports and pin docs.
4. Keep RV8GR physical-build docs and lab scripts aligned with `RV8GR/doc/02_wiring_guide.md`.
5. Use Components schematic backend and `circuit-faults` as the reusable Python-first path for future UI/block/JSON/netlist work.
6. When chip behavior changes, verify with Components Python tests first, run Verilog smoke tests when RTL behavior is touched, and rerun virtual physical checks before circuit/system signoff.
7. Later Components task: review chip JSON/component definition output for student readability and document system wiring commands.
8. For RV8, do not stage unrelated dirty files unless Jo explicitly asks.

## Known Follow-Ups

- `74HC150` and `74HC260` were removed from the active Components catalog because manufacturer-verified HC-family DIP evidence was not available.
- SST39SF010A Python/Verilog write-trigger semantics are aligned for the simplified flash model: write occurs on the falling edge of `/WE` while selected with `/OE` high.
- RV8GR KiCad project files were kept under `RV8GR/Kicad/`; accidental root report/output files and duplicate `XCPU (1).pdf` were removed.
- `RV8GR/.gitignore` now ignores generated KiCad local artifacts such as `.kicad_prl`, backup folders, lock files, reports, EDF output, and Python cache.
- RV8GR canonical folder is `RV8GR/`; `RV8GR-V2/` was renamed and docs/tool paths were cleaned.
- Top-level `README.md` now treats `RV8-G` as a concept/history item, not an active folder in this checkout.
- Do not stage unrelated RV8 dirty files unless Jo explicitly asks.
