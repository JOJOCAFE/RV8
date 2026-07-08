# Coordinator Memory

## Team Roster

| Agent | For | Shortcuts |
|-------|-----|-----------|
| architect | design decisions, ISA, chip selection | Ctrl+Shift+1 |
| verifier | review, test, debug, defect RCA | Ctrl+Shift+2 |
| rtl-coder | Verilog, testbenches, gate-sim | Ctrl+Shift+3 |
| hw-coder | circuits, KiCad, wiring tables | Ctrl+Shift+4 |
| sw-coder | assembler, tools, ROM, firmware | Ctrl+Shift+5 |
| docs-writer | Thai labs, build guides | Ctrl+Shift+6 |

## Dispatch History

(Empty — populate as tasks are dispatched)

## Active Work

- Project: RV8-GR physical build (architecture frozen v1.0)
- Next: order parts, build labs 01-14 on breadboard
- Shared reusable components live at `/home/jo/kiro/Components` and `git@github.com:JOJOCAFE/Components.git`.
- Component-library routing: Ohm handles physical pinout/datasheet evidence, Mint handles Verilog models/tests, Fern verifies evidence/tests, Bank approves chip-selection decisions.

## Component Datasheet Routing

- Datasheet lookup/update requests go through `skill://.kiro/skills/component-library/SKILL.md`.
- AllDatasheet is a locator/download helper only; require manufacturer PDF evidence and DIP/PDIP package proof before marking a pinout usable.
- Current blocked pinout placeholders: `74HC/74hc150-pin.md`, `74HC/74hc260-pin.md`.

## Lessons Learned

(None yet)
