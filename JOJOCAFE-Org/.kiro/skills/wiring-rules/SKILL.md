---
name: wiring-rules
description: Pin-level wiring source of truth for RV8 CPU variants. Use when designing circuits, verifying wiring, or writing hardware labs. Contains chip assignments, bus connections, and critical signal paths.
---

# Wiring Rules

## Source of Truth

The official pin-level wiring for RV8GR lives in `RV8GR/doc/02_wiring_guide.md`; other variants keep their own wiring guide equivalent. This skill defines the RULES; the specific pin assignments are in the variant's wiring guide.

Reusable chip pinouts and package evidence live in the shared Components repo:

- Local path: `/home/jo/kiro/Components`
- GitHub: `git@github.com:JOJOCAFE/Components.git`

When a wiring guide needs a 74HC, EEPROM, flash, or SRAM pinout, use the matching `*-pin.md` file from the Components repo. If the part is not present or is marked blocked, do not infer pinout from memory; route to Ohm for datasheet-backed pinout work and Fern for verification.

## Universal Rules (all variants)

### Bus Discipline
- RV8GR A15 chip select: ROM `/CE = A15`, RAM `/CE = /A15` (both active-low)
- Data bus: bidirectional, only ONE driver at a time
- Address bus: output-only from CPU to memory
- Never drive bus from two sources simultaneously

### Naming Convention
- Chips: U1, U2, ... (sequential per board/module)
- Signals: CAPS_WITH_UNDERSCORES (e.g., AC_WR, BUF_OE, WR_DIR)
- Active-low: prefix with / (e.g., /CE, /OE, /WR, /IRQ)
- Pins: reference by chip number + pin number (e.g., U7-3, U14-11)

### Critical Hazards
- Pin-number mistakes: verify every U# pin against `RV8GR/doc/02_wiring_guide.md` and Components datasheet-backed pinouts.
- Output-output wiring: legal data flow is output→input, or multiple outputs feeding one input only when enables prove they cannot drive simultaneously.
- SRC+STR mixed opcodes: reserved but electrically safe in current RV8GR; STR dominates, U14 drives IBUS, U7 drives DBUS, ROM `/OE=WR_DIR` disables ROM output.
- ROM `/WE`: inactive during CPU runtime; only the Programmer may own it in PROG/reset isolation.
- Always verify: no two output-enable signals can be active simultaneously on same bus

### Timing
- ROM/RAM: 70ns access time (AT28C256-70, 62256-70)
- Max safe clock: limited by slowest path (ROM read → ALU → RAM write)
- Clock edges: data latched on rising edge, setup/hold must be met
- Async signals: must be synchronized or proven glitch-free at operating frequency

### Verification Checklist
When reviewing any wiring change:
1. Only one bus driver active at any time?
2. Chip select logic correct (active-low awareness)?
3. Unused inputs tied high or low (not floating)?
4. Decoupling caps on every IC?
5. Fan-out within spec (≤10 for 74HC at 5V)?
6. Propagation delay chain fits within clock period?
7. Component pinouts come from Components `*-pin.md` files or a cited manufacturer datasheet?
8. DIP/PDIP package evidence exists for any part that will be used on breadboard?

## RV8-GR Specific

- 34 logic chips + ROM + RAM = 36 packages
- 3-cycle: T0/T1/T2 (fetch ctrl, fetch operand, execute)
- Horizontal control: opcode byte IS the control word
- Encoding: [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
- Data page: SETDP loads U32 (Data Page Register)
- IRQ: v1.0 polling latch only. `/IRQ` release/rising edge sets IRQ_FF; no fixed vector or automatic PC save.
- Student docs are derived. `00_design_isa.md` and `02_wiring_guide.md` remain the source of truth; `05_understand_by_module.md` is explanatory only.
