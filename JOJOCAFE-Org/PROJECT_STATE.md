# Project State

## Owner: Team JOJOCAFE-Org

The team owns the entire RV8 project. All variants, all deliverables.

## Active Target: RV8-GR (Student Baseline)

- **Status**: Architecture frozen v1.0 — ready for physical build
- **Chips**: 33 logic + ROM + RAM = 35 packages
- **ISA**: 18 instructions (17 + SETDP), all verified
- **Verification**: 5 Verilog TBs pass, gate-level sim 8/8, soft_debug 4/4
- **Labs**: 14 hardware labs written (Thai, middle school level)
- **Clock**: 1 MHz breadboard target

## Current Sprint & Backlog

- **Backlog**: see `BACKLOG.md` (19 items, prioritized P0-P3)
- **Sprint 1**: see `SPRINT.md` (Physical Build Kickoff, individual task lists)

### Sprint 1 Summary
- [ ] Order parts for physical build
- [ ] Build Labs 01-14 on breadboard (sequential, verify each)
- [ ] Flash test ROM via Programmer
- [ ] Write example .asm programs
- [ ] Full ISA test on physical hardware

## Next Projects (queued)

- RV8-R: 18 chips, full 35-instruction ISA, microcode, RAM registers
- RV8-G: 38 chips, full ISA, no microcode, fastest

## Recent Decisions

| Date | Decision | By |
|------|----------|----|
| 2026-06-15 | Memory map swapped: ROM $0000-$7FFF, RAM $8000-$FFFF | architect |
| 2026-06-14 | Architecture frozen v1.0 — no more changes until physical build | architect |
| 2026-06-14 | Programmer design finalized (ESP32 + TXS0108E + 74HC595) | hw-coder |

## Known Issues

None blocking. All 11 hazards in risk analysis resolved.
