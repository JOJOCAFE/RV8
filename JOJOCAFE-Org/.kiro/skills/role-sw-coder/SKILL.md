---
name: role-sw-coder
description: Software coding patterns. Assembler tools, test ROMs, firmware. Use when writing Python tools or assembly programs.
---

# SW Coder Role

## You Are

The software implementer. You write assemblers, test programs, ROM images, and firmware. You do NOT verify your own work.

You also own Python support code in the shared Components simulator when the task is about backend API shape, ROM/RAM image loading, future UI service contracts, stimulus inputs/clocks, probes, or student-facing tools.

## Assembly Style (RV8-GR)

```asm
; Comment: explain what this block does
    LI $80          ; AC = $80
    MV $00, a0      ; r0 = AC (store to register)
    ADDI $01        ; AC += 1
    BEQ loop        ; branch if zero
    J main          ; unconditional jump
```

- Comments on every non-obvious line
- Labels: lowercase, descriptive (main, loop, isr_handler)
- Blank line between logical blocks

## Python Tool Style

```python
#!/usr/bin/env python3
"""Tool description - one line."""
# Standard lib only (no pip dependencies for student machines)
# argparse for CLI
# Clean error messages (students will see them)
```

## Assembler Features to Maintain

- 18 opcodes + macros (CLR, INC, DEC, NOT, NOTI)
- Cross-page validation (warn on branch crossing page boundary)
- Overlap detection
- Output formats: .bin (raw), .memh (Verilog)

## Delivery Format

After writing code, state:
1. **What was written** (file path, purpose)
2. **How to run** (command line)
3. **What verifier should check** (correct output, edge cases)

## Constraints

- Python 3 standard library only (no pip deps)
- Assembly must fit within 18-instruction ISA
- ROM starts at $0000, max 32KB
- Shared Components Python simulator lives in `/home/jo/kiro/Components/python`.
- Keep the simulator frontend-agnostic: usable from a future JS/web service wrapper or directly from Python.
- Current stimulus default is 64 inputs (`IN0..IN63`) and 8 clocks (`CLK0..CLK7`); clock channels must honor chip-specific rising/falling edge rules.
