# Team Memory

Shared knowledge for all agents. Update when significant facts change.

## Project: RV8 CPU Family

- **Ownership**: Team JOJOCAFE owns the entire RV8 project
- **Main focus**: RV8-GR (33 chips, architecture frozen v1.0)
- Target: minimal 8-bit CPUs students can build on breadboards
- Language: Thai docs, English code/comments
- Repository: /home/jo/kiro/RV8

## Variants (all under our care)

| Variant | Status | Priority |
|---------|--------|----------|
| RV8-GR | **Active focus** — frozen, ready for physical build | 🔴 Now |
| RV8-R | Queued — full ISA, microcode, 18 chips | 🟢 Future |
| RV8-G | Queued — full ISA, no microcode, 38 chips | 🟢 Future |
| RV8 | Reference/exploratory only | 🟢 Archive |

## Architecture Quick Reference

- 8-bit data, 16-bit address, 64KB (ROM $0000-$7FFF, RAM $8000-$FFFF)
- Accumulator-based, 18 instructions, 3-cycle (T0/T1/T2)
- Horizontal control: opcode byte = control word, no decoder
- Encoding: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
- Chips: 33 logic (U1-U33) + AT28C256 ROM + 62256 RAM
- Clock: 1 MHz breadboard, 4-5 MHz PCB

## Verification Status

- Verilog: 5 TBs pass (full, IRQ, SETDP, tasks, 512-opcode sweep)
- Gate-level: chip_sim.py 8/8, soft_debug.py 4/4
- Physical: NOT YET BUILT

## File Paths (source of truth)

| What | Where |
|------|-------|
| ISA + design | `doc/00_design_isa.md` |
| Wiring (pin-level) | `doc/03_wiring_guide.md` |
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
- Contents: reusable 74HC Verilog models, memory models, DIP/PDIP pinout docs, smoke tests, and retained manufacturer datasheet evidence.
- Responsibility: Pim routes; Ohm owns physical pinout and DIP package evidence; Mint owns reusable Verilog models/tests; Fern verifies package evidence, source references, and smoke tests; Bank approves chip-selection questions.
- Current blocked pinout placeholders: `74HC/74hc150-pin.md`, `74HC/74hc260-pin.md`.
- Rule: pinout docs are physical wiring artifacts; do not create pin tables from memory. Require manufacturer datasheet evidence and explicit DIP/PDIP or equivalent through-hole package proof.

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

- RV8-R: 18 chips, full 35-instruction ISA, microcode
- RV8-G: 38 chips, full ISA, no microcode, fastest

## Critical Rules (all agents must know)

- 33 chip budget is FROZEN. No additions without architect approval.
- 64 forbidden opcodes: (opcode & $0C) == $0C (SRC+STR bus fight)
- A15 chip select: ROM active when A15=0, RAM active when A15=1
- Architecture frozen v1.0 — no design changes until physical build validates
- Shared component pinouts must cite manufacturer sources and DIP/PDIP evidence before breadboard use.
