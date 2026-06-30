# Architect Memory

## Key Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-14 | RV8-GR architecture frozen v1.0 | All 11 docs consistent, gate-level verified |
| 2026-06-15 | Memory map: ROM $0000-$7FFF, RAM $8000-$FFFF | Reset vector at $0000 = direct ROM boot |
| 2026-06-14 | 33 chips frozen — no additions without strong justification | Student buildability |
| 2026-06-14 | IRQ v1.0 = polling latch (U31), hardware vector deferred to v2.0 | Simplicity first |

## Design Principles

- Fewer chips > more features
- Horizontal control (no decoder) = simpler to understand
- Student must be able to wire it on a breadboard
- Every instruction must be testable independently

## Pending Decisions

- RV8-R architecture: control word width, microcode format, register mapping
- PCB module partitioning for 4 MHz version

## Chip Budget

33 logic + ROM + RAM = 35 total. Spare gates: U25 (OR), U33 (AND).
