# Architect Memory

## Key Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-14 | RV8-GR architecture frozen v1.0 | All 11 docs consistent, gate-level verified |
| 2026-06-15 | Memory map: ROM $0000-$7FFF, RAM $8000-$FFFF | Reset vector at $0000 = direct ROM boot |
| 2026-06-14 | 33 chips frozen — no additions without strong justification | Student buildability |
| 2026-06-14 | IRQ v1.0 = polling latch (U31), hardware vector deferred to v2.0 | Simplicity first |
| 2026-07-09 | Shared Components repo is reusable source for 74HC/memory models and pinout evidence | Avoid duplicating chip models across RV8 variants |

## Design Principles

- Fewer chips > more features
- Horizontal control (no decoder) = simpler to understand
- Student must be able to wire it on a breadboard
- Every instruction must be testable independently

## Pending Decisions

- RV8-R architecture: control word width, microcode format, register mapping
- PCB module partitioning for 4 MHz version
- Approve any new component family before it enters `/home/jo/kiro/Components`.

## Chip Budget

33 logic + ROM + RAM = 35 total. Spare gates: U25 (OR), U33 (AND).

## Components Policy

- Shared component repo: `/home/jo/kiro/Components`, remote `git@github.com:JOJOCAFE/Components.git`.
- Pinout docs must stay manufacturer/datasheet-backed for DIP/PDIP use.
- Do not let a substitute LS/TTL pinout stand in for an HC part unless a manufacturer HC-family datasheet confirms it.
