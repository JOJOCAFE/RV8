# RV4-Tiny

RV4-Tiny v1.3 is a real 4-bit CPU made from common logic chips. It is designed
for students to build, watch, and understand.

It can:

- read instructions from ROM;
- store numbers in RAM;
- add 4-bit numbers;
- read switches and control LEDs;
- jump and loop;
- stop with `HLT`.

## Read in this order

| Order | Document | Purpose |
|---:|---|---|
| 00 | [Architecture](00_architecture.md) | understand the CPU |
| 01 | [Control and timing](01_control_and_timing.md) | understand when things happen |
| 02 | [Signal assignment](02_signal_assignment.md) | see every chip connection |
| 03 | [Wiring guide](03_wiring_guide.md) | connect the modules |
| 04 | [Schematic checklist](04_schematic_checklist.md) | draw and check the schematic |
| 05 | [Bill of materials](05_bill_of_materials.md) | choose and buy parts |
| 06 | [Breadboard layout](06_breadboard_layout.md) | place the parts |
| 07 | [Build plan](07_build_plan.md) | build in tested stages |
| 08 | [Debug guide](08_debug_guide.md) | find hardware faults |
| 09 | [Simulator specification](09_simulator_spec.md) | build the software model |
| 10 | [Assembler specification](10_assembler_spec.md) | build the assembler |
| 11 | [Chip pinouts](11_chip_pinouts.md) | check physical pins |
| 12 | [Hardware review](12_hardware_review.md) | read design decisions and limits |
| 13 | [Student probe header plan](13_student_probe_header_plan.md) | observe CPU signals with plug-in LED boards |

The hardware source-of-truth pair is:

- [Control and timing](01_control_and_timing.md)
- [Signal assignment](02_signal_assignment.md)

Check the documents with:

```bash
python3 tools/verify_docs.py
python3 tools/rv4_sim.py --self-test
python3 tools/test_rv4_asm.py
```

Sample programs live in `programs/` and can be assembled with
`tools/rv4_asm.py`.

The complete CPU uses 14 logic ICs and two memory ICs: 16 packages total.

## Student build contract

The baseline is intentionally small. Keep optional ideas outside the first
physical build.

- Build one visible module at a time.
- Use STEP or a slow clean clock until every module passes.
- Every stage needs a visible pass condition: LEDs, probe values, or a recorded
  simulator state.
- Internal learning points should go to labelled headers for plug-in LED/probe
  boards instead of permanent LEDs on every signal.
- Every temporary jumper or forced test signal must be removed before the next
  integration step.
- Shared wires must have one driver at a time. Treat RAM_D as a bus, not as
  ordinary point-to-point wiring.
- Do not add serial I/O, video, interrupts, bank switching, or monitor software
  until the baseline CPU passes full programs.

Important rules:

- Every register uses the same `CPU_CLK`.
- U14/U15 form the clock/control support module.
- U11/U16 form the RAM module.
- U16 disconnects AC from the RAM data wires during reads.
- Do not build the whole CPU before each module passes its own test.
