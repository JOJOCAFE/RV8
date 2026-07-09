# Architect Memory

## Key Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-14 | RV8-GR architecture frozen v1.0 | All 11 docs consistent, gate-level verified |
| 2026-06-15 | Memory map: ROM $0000-$7FFF, RAM $8000-$FFFF | Reset vector at $0000 = direct ROM boot |
| 2026-07-09 | RV8GR baseline normalized to 34 logic chips + ROM + RAM = 36 packages | U34 immediate buffer is part of the frozen student baseline |
| 2026-06-14 | IRQ v1.0 = polling latch (U31), hardware vector deferred to v2.0 | Simplicity first |
| 2026-07-09 | Shared Components repo is reusable source for 74HC/memory models and pinout evidence | Avoid duplicating chip models across RV8 variants |
| 2026-07-09 | Components Python simulator must stay physical-pin and edge-aware | Supports future UI/backend wiring while matching datasheet behavior |

## Design Principles

- Fewer chips > more features
- Horizontal control (no decoder) = simpler to understand
- Student must be able to wire it on a breadboard
- Every instruction must be testable independently

## Pending Decisions

- RV8-R architecture: control word width, microcode format, register mapping
- PCB module partitioning for 4 MHz version
- Approve any new component family before it enters `/home/jo/kiro/Components`.
- Approve the probe/test-logic backend abstraction before it becomes a UI-visible contract.

## Chip Budget

34 logic + ROM + RAM = 36 total. U34 is the IRL-to-IBUS immediate buffer; spare gates remain limited and require architect approval before use.

## Components Policy

- Shared component repo: `/home/jo/kiro/Components`, remote `git@github.com:JOJOCAFE/Components.git`.
- Pinout docs must stay manufacturer/datasheet-backed for DIP/PDIP use.
- Do not let a substitute LS/TTL pinout stand in for an HC part unless a manufacturer HC-family datasheet confirms it.
- Python/Verilog component behavior must agree on active-low controls, asynchronous controls, tri-state behavior, memory controls, and rising/falling clock edges.
- Stimulus defaults: 64 input channels and 8 clock channels.
- Python schematic backend now includes bus abstractions, pull-up/pull-down default states, probes/test logic, JSON-friendly schematic mapping, netlist generation, and Verilog export. Keep that backend UI-agnostic.
