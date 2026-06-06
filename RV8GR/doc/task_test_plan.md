# RV8GR Task Test Plan

Test milestones from simple to full system.

## Task 1: Reset

- PC starts at $8000
- Page Register starts at $80
- AC = $00
- Z = 1
- Halted = 0
- State = T0

## Task 2: Basic Fetch (T0, T1, T2)

- T0 latches control byte from ROM[$8000]
- PC becomes $8001 after T0
- T1 latches operand from ROM[$8001]
- PC becomes $8002 after T1
- T2 executes LI $42 → AC = $42
- State returns to T0 after T2

## Task 3: ALU Immediate Instructions

- LI immediate
- ADDI immediate
- SUBI immediate
- XORI immediate

## Task 4: Z Flag Updates

- XORI reaches zero → Z = 1

## Task 5: Register-Register Instructions

- ADD from RAM
- SUB from RAM
- XOR from RAM
- MV from RAM (LB)

## Task 6: Store Instructions

- Store writes RAM low page
- Store leaves AC unchanged

## Task 7: Branches (BEQ, BNE)

- BEQ taken when Z = 1
- BNE taken when Z = 0
- BNE not taken when Z = 1

## Task 8: Page Register and Jump

- SETPG immediate
- Jump uses page register
- SETPG_R from RAM
- Jump uses RAM-loaded page
- Target instruction after page jump
- Jump into RAM page
- Program fetched from RAM executes

## Task 9: Halt

- J self reports halted = 1
- Halt self target = $8000