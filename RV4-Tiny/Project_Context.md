# RV4-Tiny Project Context

## Repository Layout

```text
RV4-Tiny/
├── README.md
├── Project_Context.md
├── 00_architecture.md
├── 01_control_and_timing.md
├── 02_signal_assignment.md
├── 03_wiring_guide.md
├── 04_schematic_checklist.md
├── 05_bill_of_materials.md
├── 06_breadboard_layout.md
├── 07_build_plan.md
├── 08_debug_guide.md
├── 09_simulator_spec.md
├── 10_assembler_spec.md
├── 11_chip_pinouts.md
├── 12_hardware_review.md
├── 13_student_probe_header_plan.md
├── programs/               sample assembly programs
├── tools/
│   ├── rv4_asm.py
│   ├── rv4_sim.py
│   ├── test_rv4_asm.py
│   └── verify_docs.py
└── Reference/              optional source/reference material
```

The current repo uses top-level numbered documents, not a `docs/` folder.
The simulator is implemented in `tools/rv4_sim.py`. The assembler is
implemented in `tools/rv4_asm.py`.

## Goal

Create the simplest real TTL CPU for education.

## Target

- Students age 12-18.
- Breadboard build.
- Understand CPU behavior from hardware, not from a black box.

## Baseline Contract

- RV4-Tiny v1.3.
- 14 logic ICs + ROM + RAM = 16 packages total.
- No control ROM.
- Hardwired control only.
- One shared rising-edge `CPU_CLK` for all state-holding devices.
- Visible datapath.
- Minimal chip count.
- Modular build with one tested stage at a time.
- Plug-in LED/probe headers instead of permanent LEDs on every internal signal.

## Source Of Truth

- Architecture: `00_architecture.md`
- Timing/control: `01_control_and_timing.md`
- Signal names and chip assignments: `02_signal_assignment.md`
- Wiring guide: `03_wiring_guide.md`
- Schematic checklist: `04_schematic_checklist.md`
- Simulator contract: `09_simulator_spec.md`
- Assembler contract: `10_assembler_spec.md`
- Hardware review and limits: `12_hardware_review.md`
- Student probe headers: `13_student_probe_header_plan.md`

Run this after every documentation change:

```bash
python3 tools/verify_docs.py
python3 tools/rv4_sim.py --self-test
python3 tools/test_rv4_asm.py
```

## Inspiration

- Ben Eater: staged breadboard computer build, visible modules, clock/debug discipline.
- FULXOR - Dominic LeBoeuf: first-principles computer architecture, shared buses, RAM, binary arithmetic, and logic-gate explanation.

RV4-Tiny differs by staying smaller, avoiding microcode, and requiring source-of-truth documents before implementation.

## Design Decisions

### Decision 001: Use A Hardwired Decoder

Reason: students can trace gates and control lines directly.

Rejected: control ROM or microcode.

### Decision 002: Use One Shared CPU Clock

Reason: avoids gated register clocks and double-pulse bugs.

Reference: `01_control_and_timing.md` and `12_hardware_review.md`.

### Decision 003: Keep RAM_D As An Explicit Shared Bus

Reason: students must learn bus ownership and high impedance behavior.

Rule: U16 drives `RAM_D` only during `SW`; otherwise SRAM owns `RAM_D`.

### Decision 004: Use Plug-In Probe Headers

Reason: students still see every important CPU signal without loading every net
with permanent LEDs.

Rule: probe headers must not drive CPU signals except for explicit input
headers.

## Agent Instructions

Always preserve:

- architecture;
- ISA;
- timing;
- chip count;
- signal names.

Never:

- invent new instructions;
- change chip count;
- rename signals;
- introduce gated register clocks;
- hide baseline features behind optional upgrades.

Every modification must:

- update all affected documents;
- keep simulator and assembler specs consistent;
- run `python3 tools/verify_docs.py`.

If uncertain:

1. Stop.
2. Explain the conflict.
3. Point to the exact source-of-truth files that disagree.

## Current TODO

1. Review timing using selected ROM/SRAM/74HC datasheets.
2. Draw KiCad schematic from `02_signal_assignment.md`,
   `04_schematic_checklist.md`, and `13_student_probe_header_plan.md`.
3. Build physical hardware stage by stage using `07_build_plan.md`.

Do not start physical Lab 7 until earlier build stages have recorded pass evidence.
