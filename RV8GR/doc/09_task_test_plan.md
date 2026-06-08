# RV8-GR — Test Plan (Stable)

**Milestones from reset to full system. Matches Verilog testbenches.**

---

## Task 1: Reset

| Test | Expected |
|------|----------|
| PC starts at $8000 | ✅ |
| Page Register = $80 | ✅ |
| AC = $00, Z = 1 | ✅ |
| Ring counter at T0 | ✅ |

---

## Task 2: Fetch Cycle (T0/T1/T2)

| Test | Expected |
|------|----------|
| T0: latch control byte from ROM[$8000] | IR_HIGH = opcode |
| T0: PC increments to $8001 | ✅ |
| T1: latch operand from ROM[$8001] | IR_LOW = operand |
| T1: PC increments to $8002 | ✅ |
| T2: execute instruction | ✅ |
| T2→T0: returns to fetch | ✅ |

---

## Task 3: ALU Immediate

| Test | Opcode | Expected |
|------|--------|----------|
| LI $42 | $30 | AC=$42, Z=0 |
| ADDI $05 (AC=$10) | $10 | AC=$15, Z=0 |
| SUBI $15 (AC=$15) | $90 | AC=$00, Z=1 |
| XORI $AA (AC=$00) | $70 | AC=$AA, Z=0 |

---

## Task 4: Z Flag

| Test | Expected |
|------|----------|
| AC=$00 after SUB → Z=1 | ✅ |
| AC≠0 after ADD → Z=0 | ✅ |
| XORI reaches zero → Z=1 | ✅ |

---

## Task 5: Register Operations (RAM)

| Test | Opcode | Expected |
|------|--------|----------|
| SB $00 (AC=$AA) | $04 | RAM[$00]=$AA |
| LB $00 | $38 | AC=$AA |
| ADD $00 (AC=$55, RAM=$AA) | $18 | AC=$FF |
| SUB $00 (AC=$AA, RAM=$AA) | $98 | AC=$00, Z=1 |
| XOR $00 (AC=$54, RAM=$FF) | $78 | AC=$AB |

---

## Task 6: Store

| Test | Expected |
|------|----------|
| SB writes to RAM at $00xx | ✅ |
| AC unchanged after SB | ✅ |
| Multiple stores to different addresses | ✅ |

---

## Task 7: Branch

| Test | Expected |
|------|----------|
| BEQ taken (Z=1) | PC = {PG, addr} |
| BEQ not taken (Z=0) | PC continues |
| BNE taken (Z=0) | PC = {PG, addr} |
| BNE not taken (Z=1) | PC continues |

---

## Task 8: Page Register & Jump

| Test | Expected |
|------|----------|
| SETPG $90 | PG=$90 |
| J $00 (PG=$90) | PC=$9000 |
| SETPG_R $03 (RAM[$03]=$80) | PG=$80 |
| Cross-page jump and return | ✅ |
| Execute from RAM (PC < $8000) | ✅ |

---

## Task 9: IRQ

| Test | Expected |
|------|----------|
| EI sets IE=1 | ✅ |
| DI clears IE=0 | ✅ |
| /IRQ falling edge latches IRQ_FF | ✅ |
| IRQ fires at instruction boundary | PC=$FF00 |
| PC saved to RAM[$0E:$0F] | ✅ |
| IE cleared on IRQ entry | ✅ |
| IRQ blocked when IE=0 | ✅ |
| IRQ deferred during jump | ✅ |

---

## Task 10: SETDP (Data Page Register)

| Test | Expected |
|------|----------|
| SETDP $10, SB $00 | RAM[$1000] written |
| SETDP $10, LB $00 | AC = RAM[$1000] |
| SETDP $80, LB $00 | AC = ROM[$8000] |
| SETDP $00, LB $03 | AC = RAM[$0003] (registers) |
| Cross-page write/read (5KB) | All pages consistent |

---

## Task 11: Halt

| Test | Expected |
|------|----------|
| J self (e.g. $01 $36 at $8036) | PC loops |

---

## Testbench Files

| File | Tasks Covered |
|------|--------------|
| `tb/tb_rv8gr_full.v` | 1-8, 11 (127 cycles, ALL PASS) |
| `tb/tb_rv8gr_irq.v` | 9 (6 tests, ALL PASS) |
| `tb/tb_rv8gr_setdp.v` | 10 (160 cycles, ALL PASS) |

---

## Run Tests

```bash
cd RV8GR
iverilog -o tb/sim_full.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_full.v
vvp tb/sim_full.vvp
# === ALL TESTS PASSED ===

iverilog -o tb/sim_irq.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_irq.v
vvp tb/sim_irq.vvp
# === ALL IRQ TESTS PASSED ===

iverilog -o tb/sim_setdp.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_setdp.v
vvp tb/sim_setdp.vvp
# === SETDP TEST PASSED ===
```
