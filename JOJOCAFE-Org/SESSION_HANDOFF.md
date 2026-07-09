# Session Handoff

Updated: 2026-07-09

## Current State

- B-010 example ASM programs are implemented and assembler-verified.
- B-007 non-physical verification report is available; physical B-007 remains blocked until hardware evidence exists.
- Components netlist mapping expansion is verified and pushed at `a2ee62c Expand component netlist mappings`.
- Components repo is pushed and clean at `a2ee62c Expand component netlist mappings`.
- Components remote: `git@github.com:JOJOCAFE/Components.git`, branch `main`.
- RV8 repo is pushed through `1470963 Fix RV8 README project status`.
- RV8 remote: `git@github.com:JOJOCAFE/RV8.git`, branch `team-setup`.
- RV8 team/skill updates are in this repo under `JOJOCAFE-Org/`.
- `Programmer/KICAD/.history` is clean at its nested `master` checkout.

## Components Library Facts

- Shared library path: `/home/jo/kiro/Components`.
- Python package path: `/home/jo/kiro/Components/python`.
- Python simulator uses DIP-style pin number/name access and propagation-delay scheduling.
- `StimulusController` default channels: 64 inputs (`IN0..IN63`) and 8 clocks (`CLK0..CLK7`).
- Clock stimulus is physical-pin and edge aware:
  - default rising edge
  - 74HC73 and 74HC112 use falling-edge `CP`
  - 74HC74 sections, 74HC595 `SRCLK`/`RCLK`, and 74HC593 `RCK`/`CCK` are pin-specific
- `chiplib.loader` preloads `.bin`, Intel HEX, or text-hex data into ROM/RAM `.data`.
- Python and Verilog component behavior must remain compatible.
- Python schematic backend now supports buses, pull-up/pull-down style normal states, probes/test logic, simple JSON-friendly schematics, and netlist/Verilog export paths for RV8GR-style chip-level work.

## Verification Evidence

Last green checks:

```sh
cd /home/jo/kiro/Components/python && python3 -B -m tests.test_chips
python3 -m py_compile /home/jo/kiro/Components/python/chiplib/*.py /home/jo/kiro/Components/python/tests/*.py
cd /home/jo/kiro && iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v && vvp /tmp/tb_74hc_smoke.vvp
cd /home/jo/kiro && iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v && vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `Components Python chip tests passed`
- `74HC SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`

## Next Session

1. Keep physical B-007 blocked until hardware photos/logs/test output exist; cite the non-physical report separately.
2. Use B-010 example ASM programs for ROM/programmer prep once the physical ROM workflow is ready.
3. Continue remaining Components full-catalog mappings only after checking module ports and pin docs.
4. Keep RV8GR physical-build docs and lab scripts aligned with `RV8GR/doc/02_wiring_guide.md`.
5. Use Components schematic backend as the reusable Python-first path for future UI/block/JSON/netlist work.
6. When chip behavior changes, verify with Components Python tests first and run Verilog smoke tests.
7. For RV8, do not stage unrelated dirty `RV8R/` or `rv8_memory.md` changes unless Jo explicitly asks.

## Known Follow-Ups

- `74HC150` and `74HC260` were removed from the active Components catalog because manufacturer-verified HC-family DIP evidence was not available.
- SST39SF010A Python/Verilog write-trigger semantics are aligned for the simplified flash model: write occurs on the falling edge of `/WE` while selected with `/OE` high.
- RV8GR KiCad project files were kept under `RV8GR/Kicad/`; accidental root report/output files and duplicate `XCPU (1).pdf` were removed.
- `RV8GR/.gitignore` now ignores generated KiCad local artifacts such as `.kicad_prl`, backup folders, lock files, reports, EDF output, and Python cache.
- RV8GR canonical folder is `RV8GR/`; `RV8GR-V2/` was renamed and docs/tool paths were cleaned.
- Top-level `README.md` now treats `RV8-G` as a concept/history item, not an active folder in this checkout.
- Do not stage unrelated RV8 dirty files unless Jo explicitly asks.
