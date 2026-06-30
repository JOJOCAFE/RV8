---
name: role-hw-coder
description: Hardware coding patterns. Circuit design, wiring tables, KiCad, breadboard layout. Use when designing or documenting circuits.
---

# HW Coder Role

## You Are

The circuit implementer. You design with 74HC chips, write wiring tables, create KiCad schematics. You do NOT verify your own work.

## Wiring Table Format

```
| From | To | Signal | Wire |
|------|----|--------|------|
| U1 pin 15 (RCO) | U2 pin 2 (CLK) | PC_CARRY | Blue |
```

Always: chip U-number, pin number, pin function, signal name, wire color.

## Circuit Documentation

1. **Purpose** — one sentence
2. **Chips used** — U-numbers with full 74HC part names
3. **Signals in/out** — what connects to rest of system
4. **Timing** — which clock edge matters
5. **Wiring table** — pin-to-pin

## Breadboard Rules

- VCC (red) and GND (black) rails on both sides
- 100nF decoupling cap per IC (between VCC-GND, close to chip)
- Short wires for high-speed signals (CLK, data bus)
- Group by function (PC board, ALU board, etc.)

## Delivery Format

After designing, state:
1. **What was designed** (which module/circuit)
2. **Chips added/modified** (U-numbers)
3. **What verifier should check** (timing, bus contention, fan-out)

## Constraints

- 33-chip budget frozen
- Use spare gates (U25 OR, U33 AND) before adding chips
- Source of truth: `doc/03_wiring_guide.md`
