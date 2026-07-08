# Session Handoff

Updated: 2026-07-09

## Current State

- Components repo is pushed and clean at `a55bec5 Remove unverified 74HC parts`.
- Components remote: `git@github.com:JOJOCAFE/Components.git`, branch `main`.
- RV8 repo is pushed and clean at `4e474b9 Add RV8GR-V2 KiCad project`.
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

1. Implement backend probe/test-logic channels in `/home/jo/kiro/Components/python`.
2. Probes should attach to chip pins or named nets, sample logic over simulated time, and expose serializable state for future JS/web or Python UI.
3. Assertion helpers should cover `0`, `1`, `Z`, `X`, rising/falling transitions, pulse counts, and timing windows.
4. Verify with Python tests first; run Verilog smoke only if chip behavior changes.

## Known Follow-Ups

- `74HC150` and `74HC260` were removed from the active Components catalog because manufacturer-verified HC-family DIP evidence was not available.
- SST39SF010A Python/Verilog write-trigger semantics are aligned for the simplified flash model: write occurs on the falling edge of `/WE` while selected with `/OE` high.
- RV8GR-V2 KiCad project files were kept under `RV8GR-V2/Kicad/`; accidental root report/output files and duplicate `XCPU (1).pdf` were removed.
- `RV8GR-V2/.gitignore` now ignores generated KiCad local artifacts such as `.kicad_prl`, backup folders, lock files, reports, EDF output, and Python cache.
- Do not stage unrelated RV8 dirty files unless Jo explicitly asks.
