# Team Memory

Shared knowledge for all agents. Update when significant facts change.

## Project: RV8 CPU Family

- **Ownership**: Team JOJOCAFE owns the entire RV8 project
- **Main focus**: RV8-GR (34 logic chips, architecture frozen v1.0)
- Target: minimal 8-bit CPUs students can build on breadboards
- Language: Thai docs, English code/comments
- Repository: /home/jo/kiro/RV8

## Variants (all under our care)

| Variant | Status | Priority |
|---------|--------|----------|
| RV8-GR | **Active focus** — frozen, ready for physical build | 🔴 Now |
| RV8-R FullHW | Queued — 49 logic / 53 total packages, full RV8-style ISA hardware path | 🟢 Future |
| RV8-G | Concept/history — full ISA, no microcode, 38 logic chips, no active folder | 🟢 Future |
| RV8 | Reference/exploratory only | 🟢 Archive |

## Architecture Quick Reference

- 8-bit data, 16-bit address, 64KB (ROM $0000-$7FFF, RAM $8000-$FFFF)
- Accumulator-based, 18 instructions, 3-cycle (T0/T1/T2)
- Horizontal control: opcode byte = control word, no decoder
- Encoding: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
- Chips: 34 logic (U1-U34) + AT28C256 ROM + 62256 RAM
- Clock: 1 MHz breadboard, 4-5 MHz PCB

## Verification Status

- Verilog: 5 TBs pass (full, IRQ, SETDP, tasks, 512-opcode sweep)
- Gate-level: chip_sim.py 8/8, soft_debug.py 4/4
- Physical: NOT YET BUILT

## File Paths (source of truth)

| What | Where |
|------|-------|
| ISA + design | `doc/00_design_isa.md` |
| Wiring (pin-level) | `doc/01_wiring_guide.md` |
| Verilog CPU | `rtl/rv8gr_cpu.v` |
| Testbenches | `tb/tb_rv8gr_*.v` |
| Gate sim | `sim/chip_sim.py` |
| Assembler | `tools/rv8gr_asm.py` |
| Labs (Thai) | `doc/labs/` |

## Shared Components Library

- Local path: `/home/jo/kiro/Components`
- GitHub: `git@github.com:JOJOCAFE/Components.git`
- Branch: `main`
- Initial pushed commit: `f674250 Initial shared component library`
- Latest known pushed commit: `87bcfdc Save Components student guide handoff`
- Contents: canonical chip definitions, reusable 74HC Verilog models, memory models, DIP/PDIP pinout docs, circuit libraries, student docs, CLI/API contract docs, smoke tests, virtual physical-system checkers, and retained manufacturer datasheet evidence.
- Python library: `/home/jo/kiro/Components/python`, pin-level DIP-style chip models, ROM/RAM image loader, 64 input stimulus channels (`IN0..IN63`), 8 clocks (`CLK0..CLK7`), propagation-delay simulation, edge-aware clock dispatch, JSON-friendly schematics, buses, pull defaults, probes/test logic, netlist generation, Verilog export, and CLI/API workflows.
- Student guide: `/home/jo/kiro/Components/docs/STUDENT_GUIDE.md` explains Components for CLI and API use.
- Responsibility: Pim routes; Bank owns package/service/circuit-library boundaries and virtual checker architecture; Ohm owns physical pinout, DIP package evidence, and breadboard realism; Mint owns reusable Verilog models/tests and RTL edge compatibility; Bam owns Python backend, CLI/API, schematic JSON, and virtual test instruments; Fern verifies package evidence, source references, tests, bus-race/timing/edge proofs, and release confidence; Noon owns beginner clarity, student examples, and learner-facing docs.
- `74HC150` and `74HC260` were removed from the active Components catalog because no manufacturer-verified HC-family DIP evidence was available.
- Rule: pinout docs are physical wiring artifacts; do not create pin tables from memory. Require manufacturer datasheet evidence and explicit DIP/PDIP or equivalent through-hole package proof.
- Rule: Python and Verilog component behavior must remain compatible for observable controls, output polarity, tri-state behavior, async controls, memory behavior, and rising/falling clock edges.
- Python schematic backend supports buses, pull-up/pull-down style default states, probes/test logic, JSON-friendly script mapping, netlist generation, and Verilog export for chip-level workflows.
- SST39SF010A Python/Verilog write-trigger semantics are aligned: the simplified flash model writes on the falling edge of `/WE` while selected with `/OE` high.
- Virtual physical checker command:
  `PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults examples/circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json`
- The checker must catch four common AI/circuit mistakes before circuit/system-level work: wrong pin number/name/active-low marker; output-output wiring without bus/enable proof; missing positive/negative or rising/falling edge statement for edge-sensitive chips; and shared-bus or stress-net timing without R/C, delay-noise, setup/hold, float, or deadband coverage.
- Virtual R/C and delay-noise components are test instruments for finding risk early. They do not replace physical voltage, frequency, scope/logic-analyzer, or breadboard wiring tests at 4.5 V, 5.0 V, 5.5 V and target clock rates.
- Future Components lane: review chip JSON/component definition output for student readability and document the system wiring commands used by Components.

### Datasheet Access Notes

- Prefer direct manufacturer PDFs when they prove the required package.
- Use AllDatasheet only as locator/download helper when direct manufacturer access is hard.
- AllDatasheet reliable route: search `https://www.alldatasheet.com/view.jsp?Searchword=<part>`, open exact result, open `/datasheet-pdf/view/<id>/<maker>/<part>.html`, parse the PDF.js iframe `file=` URL ending in `/datasheet.pdf`, download it, and confirm `%PDF`.
- Alternate AllDatasheet route: open `/datasheet-pdf/download/<id>/<maker>/<part>.html`, parse the visible 5-digit code and hidden `tmpinfo1aa`, POST `innum=<code>&tmpinfo1aa=<token>`, then confirm `%PDF`.
- Keep only the final cited manufacturer PDF in `Components/source`; remove failed downloads, duplicates, HTML dumps, and `Zone.Identifier` files.

## Current Sprint

- [ ] Order parts for physical build
- [ ] Build labs 01-14 on breadboard (1 MHz)
- [ ] Write example programs (.asm collection)

## Queued Projects

- RV8-R FullHW: 49 logic / 53 total packages, full RV8-style ISA hardware path
- RV8-G: 38 logic chips, full ISA, no microcode concept/history item

## Critical Rules (all agents must know)

- RV8GR baseline is 34 logic chips + ROM + RAM = 36 packages. No additions without architect approval.
- 64 forbidden opcodes: (opcode & $0C) == $0C (SRC+STR bus fight)
- A15 chip select: ROM active when A15=0, RAM active when A15=1
- Architecture frozen v1.0 — no design changes until physical build validates
- Shared component pinouts must cite manufacturer sources and DIP/PDIP evidence before breadboard use.
- Shared Components simulator backend must remain frontend-agnostic for future JS/web or Python UI use.
- RV8GR virtual physical checks must run before treating Components-derived chip/circuit/system behavior as ready for physical build steps.
