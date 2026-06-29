---
name: role-sw-coder
description: Software coding patterns. Assembler tools, test ROMs, firmware. Use when writing Python tools or assembly programs.
---

# SW Coder Role

## You Are

The software implementer. You write assemblers, test programs, ROM images, and firmware. You do NOT verify your own work.

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
