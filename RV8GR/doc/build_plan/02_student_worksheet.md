# RV8-GR Student Build Worksheet

Use this beside `01_student_incremental_build_plan.md`.

The technical build plan tells the teacher exactly which pins to wire. This
worksheet tells the student what to do, what to see, and when to stop.

After all stage cards pass on the real board, the teacher records voltage,
frequency, edge, bus, and delay evidence in `../07_real_build_timing_log.md`.

Rules for every stage:
- Build only this stage.
- Add VCC, GND, and 100nF bypass capacitor before signal wires.
- Use the slow clock or push-button clock.
- Test before adding the next stage.
- If the result is wrong, stop and fix it first.

Student record:

```text
Name:
Board:
Date started:
Clock mode:
Power supply voltage:
```

---

## How To Use One Stage Card

For each stage:

```text
Goal: What this part should do.
Build: What to place and wire.
Look at: LEDs or probe points.
Expected: What you should see.
Pass: Tick only when it works.
Stop if: Do not continue until fixed.
Notes: What you changed or learned.
```

Teacher rule: do not let students continue with a guessed pass.

---

## Stage 0: Power, Clock, Reset

Goal: Make safe power, one clean clock pulse, and a reset signal.

Build:
- 5V and GND rails.
- Reset button or reset circuit.
- Slow clock button.
- LED on `CLK`.
- LED or probe on `/RST`.

Look at:
- VCC at far end of board.
- `CLK`.
- `/RST`.

Expected:
- VCC is 4.8V to 5.2V.
- One clock press gives one clock pulse.
- Reset goes LOW while pressed, then HIGH again.

Pass:
- [ ] VCC good.
- [ ] CLK clean.
- [ ] `/RST` clean.
- [ ] No chip or wire gets hot.

Stop if:
- CLK bounces.
- Reset floats.
- Power is below 4.8V.

Notes:

```text

```

---

## Stage 1: Ring Counter

Goal: Make the three CPU steps: `T0`, `T1`, `T2`.

Build:
- U8.
- U24 gates 1 and 2.
- LEDs on `T0`, `T1`, `T2`.

Look at:
- `T0 = U8-3`
- `T1 = U8-4`
- `T2 = U8-5`

Expected:

```text
Reset:  T0=1 T1=0 T2=0
Clock:  T0=0 T1=1 T2=0
Clock:  T0=0 T1=0 T2=1
Clock:  T0=1 T1=0 T2=0
```

Pass:
- [ ] T0/T1/T2 rotate in order.
- [ ] No skipped state.
- [ ] Reset returns to T0.

Stop if:
- Two LEDs are ON at the same time.
- All LEDs are OFF after clocking.
- The pattern skips.

Notes:

```text

```

---

## Stage 2: Program Counter Low Byte

Goal: Count from `$00` upward on PC low byte.

Build:
- U1 and U2.
- Temporary `PC_INC=HIGH`.
- Temporary `/LD=HIGH`.
- LEDs on PC0-PC7.

Look at:
- PC0-PC7 LEDs.

Expected:

```text
Reset: $00
Clock 1: $01
Clock 2: $02
...
Clock 15: $0F
Clock 16: $10
```

Pass:
- [ ] U1 counts 0 to 15.
- [ ] U2 changes when U1 rolls over.
- [ ] Reset returns to `$00`.

Stop if:
- Any bit is stuck.
- Count goes backward.
- Reset does not clear.

Before next stage:
- [ ] Remove temporary `PC_INC=HIGH` only when the teacher says.

Notes:

```text

```

---

## Stage 3: Full Program Counter

Goal: Make the full 16-bit PC count.

Build:
- U3 and U4.
- Carry chain from U2 to U3 to U4.
- LEDs on PC0-PC7, and PC8-PC15 if possible.

Look at:
- Low byte changes often.
- High byte changes only after carry.

Expected:
- Reset gives PC=`$0000`.
- PC counts upward.
- Carry reaches higher chips.

Pass:
- [ ] PC low byte counts.
- [ ] Carry reaches high byte.
- [ ] Reset gives `$0000`.

Stop if:
- U3 or U4 never changes.
- Bits are swapped.
- Reset only clears some chips.

Notes:

```text

```

---

## Stage 4: Address Mux Low Byte

Goal: Select address low byte from PC or test operand.

Build:
- U15 and U16.
- Temporary `SEL` switch.
- DIP switch for fake `IRL0..IRL7`.
- LEDs on `ABUS0..ABUS7`.

Look at:
- `ABUS0..ABUS7`.

Expected:
- `/ADDR_MODE=1`: ABUS follows PC low byte.
- `/ADDR_MODE=0`: ABUS follows DIP switch.

Pass:
- [ ] /ADDR_MODE=1 works.
- [ ] /ADDR_MODE=0 works.
- [ ] All 8 bits match.

Stop if:
- Output is inverted.
- A/B inputs are reversed.
- Any bit is swapped.

Notes:

```text

```

---

## Stage 5: Address Mux High Byte

Goal: Select address high byte from PC high or test data page.

Build:
- U29 and U30.
- Same temporary `SEL`.
- DIP switch for fake `DP0..DP7`.
- LED on `ABUS15`.

Look at:
- `ABUS8..ABUS15`.
- Especially `ABUS15`.

Expected:
- `/ADDR_MODE=1`: high address follows PC high.
- `/ADDR_MODE=0`, DP=`$80`: `ABUS15=1`.
- `/ADDR_MODE=0`, DP=`$00`: `ABUS15=0`.

Pass:
- [ ] High mux selects correctly.
- [ ] A15 is correct.

Stop if:
- A15 is reversed.
- DP bits are in the wrong order.

Notes:

```text

```

---

## Stage 6: ROM Read

Goal: Read known bytes from ROM onto `DBUS`.

Build:
- ROM.
- ROM address pins from `ABUS0..ABUS14`.
- ROM data pins to `DBUS0..DBUS7`.
- Temporary ROM `/OE=LOW` for this isolated test.

ROM bytes:

```text
$0000 = $30
$0001 = $42
$0002 = $01
$0003 = $00
```

Look at:
- `DBUS0..DBUS7`.

Expected:
- PC=`$0000`: DBUS=`$30`.
- PC=`$0001`: DBUS=`$42`.
- Force A15=1: ROM output off.

Pass:
- [ ] ROM byte `$30` appears.
- [ ] ROM byte `$42` appears.
- [ ] ROM turns off when not selected.

Stop if:
- DBUS is always `$00` or `$FF`.
- ROM gets hot.
- Address bits are swapped.

Before full CPU wiring:
- [ ] Remove temporary ROM `/OE=LOW`.
- [ ] Connect ROM `/OE` to `WR_DIR` before any store/RAM test.

Notes:

```text

```

---

## Stage 7: U7 Bus Bridge

Goal: Move bytes between `DBUS` and `IBUS`.

Build:
- U7.
- U7 A side to `IBUS`.
- U7 B side to `DBUS`.
- Temporary switches for DIR and `/OE`.

Look at:
- `DBUS`.
- `IBUS`.
- U7-1 DIR.
- U7-19 `/OE`.

Expected:
- DIR=0 and `/OE=0`: ROM byte on DBUS appears on IBUS.
- `/OE=1`: U7 stops driving IBUS.

Pass:
- [ ] DBUS to IBUS works.
- [ ] U7 disables correctly.

Stop if:
- A/B sides are swapped.
- DIR meaning is backwards.
- IBUS is driven when `/OE=1`.

Remember:

```text
Real wiring: A=IBUS, B=DBUS.
DIR=0 means B->A = DBUS->IBUS.
DIR=1 means A->B = IBUS->DBUS.
```

Notes:

```text

```

---

## Stage 8: Instruction Registers

Goal: Latch instruction byte and operand byte.

Build:
- U5 `IR_HIGH`.
- U6 `IR_LOW`.
- U5/U6 D inputs from `IBUS`.
- U5 clock from `T0`.
- U6 clock from `T1`.

Look at:
- U5 outputs.
- U6 outputs.
- `T0`, `T1`.

Expected with ROM `$30 $42`:
- At T0, U5 latches `$30`.
- At T1, U6 latches `$42`.

Pass:
- [ ] U5 holds `$30`.
- [ ] U6 holds `$42`.
- [ ] PC advanced two bytes.

Stop if:
- U5 and U6 latch at the wrong time.
- U34 output fights IBUS during fetch.

Notes:

```text

```

---

## Stage 9A: Fetch Control Signals

Goal: Make PC count during fetch and U7 drive during fetch.

Build:
- U25 gate 2 for `PC_INC`.
- Connect `PC_INC` to U1-U4 enable pins.
- Keep slow clock.

Look at:
- `PC_INC`.
- `T0`, `T1`, `T2`.
- U7-19.

Expected:
- T0/T1: `PC_INC=1`.
- T2: `PC_INC=0`.
- T0/T1: U7 enabled.

Pass:
- [ ] PC counts only during T0/T1.
- [ ] Fetch still reads ROM.

Stop if:
- PC counts during T2.
- PC stops counting during fetch.

Notes:

```text

```

---

## Stage 9B: Immediate vs Memory Address

Goal: Select immediate operand or data address correctly.

Build:
- U25 gate 1 for `ADDR_REQ`.
- U26 gate 2 for `/ADDR_MODE`.
- U26 gate 1 for `/IRL_OE`.
- U24 gate 6 for `BUF_OE_N`.

Look at:
- `/ADDR_MODE`.
- `/IRL_OE`.
- `BUF_OE_N`.
- U34-1/19.
- U7-19.

Expected:
- Immediate instruction: U34 drives IBUS during T2.
- Load/store instruction: address mux uses `{DP, IRL}`.
- U34 and U7 do not drive IBUS at the same time.

Pass:
- [ ] Immediate path works.
- [ ] Address mode path works.
- [ ] No two IBUS drivers fight.

Stop if:
- U34 and U7 are both enabled in T2 immediate.
- IBUS flickers randomly.

Notes:

```text

```

---

## Stage 9C: Store Direction Safety

Goal: Make store direction safe before using RAM.

Build:
- U26 gate 3 for `/AC_BUF`.
- U28 gate C for `WR_DIR`.
- Connect `BUF_OE_N` to U7-19.
- Connect `WR_DIR` to U7-1 and ROM `/OE`.

Look at:
- `/AC_BUF`.
- `WR_DIR`.
- U7-19.
- U7-1.
- ROM `/OE`.

Expected during store:
- `/AC_BUF=0`.
- U7-19 LOW.
- U7-1 HIGH.
- ROM `/OE` HIGH.

Pass:
- [ ] U7 remains enabled during store.
- [ ] U7 direction is IBUS to DBUS.
- [ ] ROM output is off during store.

Stop if:
- ROM `/OE` stays LOW during store.
- U7-19 is HIGH during store.
- Any chip gets warm during store test.

Notes:

```text

```

---

## Stage 10: ALU Core

Goal: Build ADD, SUB, and XOR math.

Build:
- U10 and U11 adders.
- U12 and U13 XOR array.
- U19 and U20 XOR B-input mux.

Look at:
- Adder sum.
- XOR output.
- Carry from U10 to U11.

Expected:
- `$10 + $05 = $15`.
- `$10 - $05 = $0B`.
- `$AA XOR $0F = $A5`.

Pass:
- [ ] ADD works.
- [ ] SUB works.
- [ ] XOR works.
- [ ] Carry chain works.

Stop if:
- Low nibble correct but high nibble wrong.
- SUB is off by one.

Notes:

```text

```

---

## Stage 11A: AC Mux and Load Immediate

Goal: Load a value into AC.

Build:
- U17 and U18 AC input mux.
- U9 accumulator.
- Manual pulse for U9 CLK during isolated test.

Look at:
- `AC0..AC7`.
- `MUX_SEL`.

Expected:
- IBUS=`$42`, MUX_SEL=1, XOR_MODE=0, ALU_SUB=0.
- Pulse AC clock.
- AC becomes `$42`.

Pass:
- [ ] AC loads `$42`.
- [ ] AC holds value after clock stops.

Stop if:
- AC changes without clock.
- AC bits are reversed.

Notes:

```text

```

---

## Stage 11B: AC Add Path

Goal: Add through the ALU and store result in AC.

Build:
- Same chips as Stage 11A.
- Use ALU output through AC mux.

Look at:
- AC.
- Adder sum.

Expected:
- Start AC=`$42`.
- IBUS=`$01`.
- MUX_SEL=0.
- Pulse AC clock.
- AC becomes `$43`.

Pass:
- [ ] ADDI-like path works.

Stop if:
- Adder output is correct but AC is wrong.
- AC mux select is backwards.

Notes:

```text

```

---

## Stage 12: AC Output Buffer and Store Direction

Goal: Send AC to DBUS for store.

Build:
- U14 AC output buffer.
- U14 outputs to IBUS.
- U14 enables from `/AC_BUF`.
- U7 DIR from `WR_DIR`.
- ROM `/OE` from `WR_DIR`.

Look at:
- IBUS.
- DBUS.
- U14 `/OE`.
- U7 DIR and `/OE`.
- ROM `/OE`.

Expected during store:
- U14 drives AC onto IBUS.
- U7 sends IBUS to DBUS.
- DBUS equals AC.
- ROM output is off.

Pass:
- [ ] Store path moves AC to DBUS.
- [ ] ROM is off during store.

Stop if:
- DBUS has two drivers.
- ROM or U7 gets hot.

Notes:

```text

```

---

## Stage 13: Z Flag

Goal: Show whether AC is zero.

Build:
- U22 zero comparator.
- U21 Z flag flip-flop.
- LED on `Z_flag`.

Look at:
- AC.
- U22-19 `/P=Q`.
- U21-5 `Z_flag`.

Expected:
- AC=`$01`: Z LED off.
- AC=`$00`: Z LED on.
- AC=`$01` again: Z LED off.

Pass:
- [ ] Z=1 only when AC is zero.
- [ ] Z changes after AC changes.

Stop if:
- Z LED is always on.
- Z LED is always off.
- U21 unused FF2 pins are not tied correctly.

Notes:

```text

```

---

## Stage 14A: Jump Control

Goal: Make `J` load PC.

Build:
- U24 `/JMP`.
- U27 PC load condition.
- U26 `/PC_LD`.
- Connect `/PC_LD` to U1-U4 pin 9.

Look at:
- `JMP`.
- `/PC_LD`.
- PC.

Expected:
- During T2 with `JMP=1`, `/PC_LD` goes LOW.
- PC loads target instead of counting.

Pass:
- [ ] J loads PC only during T2.

Stop if:
- PC loads during T0 or T1.
- PC counts instead of loading.

Notes:

```text

```

---

## Stage 14B: Branch Control

Goal: Make `BEQ` and `BNE` use Z flag.

Build:
- U28 gate 1 for `Z_match`.
- U27 branch gate.
- Use existing `/PC_LD`.

Look at:
- `Z_flag`.
- `ALU_SUB`.
- `Z_match`.
- `/PC_LD`.

Expected:
- BEQ: Z=1 branches, Z=0 does not.
- BNE: Z=0 branches, Z=1 does not.

Pass:
- [ ] BEQ works.
- [ ] BNE works.
- [ ] Branch only acts in T2.

Stop if:
- BEQ and BNE act the same.
- Branch ignores Z.

Notes:

```text

```

---

## Stage 15: Page Register

Goal: Jump outside page `$00`.

Build:
- U23 page register.
- U23 outputs to U3/U4 D inputs.
- PG clock logic.

Look at:
- `PG0..PG7`.
- `PG_CLK`.
- PC high byte.

Expected:
- `SETPG $90`: PG LEDs show `$90`.
- `J $00`: PC becomes `$9000`.

Pass:
- [ ] SETPG loads PG.
- [ ] J uses PG as PC high byte.

Stop if:
- PG changes on every instruction.
- PC low byte is correct but high byte wrong.

Notes:

```text

```

---

## Stage 16A: Data Page Register

Goal: Set the high byte for data access.

Build:
- U32 data page register.
- U33 gate 1 for `DP_Load`.
- U32 outputs to U29/U30 A inputs.

Look at:
- `DP0..DP7`.
- `DP_Load`.
- `ABUS15`.

Expected:
- `SETDP $80`: DP=`$80`, A15 HIGH during data access.
- `SETDP $00`: DP=`$00`, A15 LOW during data access.

Pass:
- [ ] SETDP `$80` works.
- [ ] SETDP `$00` works.

Stop if:
- DP changes on SETPG.
- DP bits are reversed.

Notes:

```text

```

---

## Stage 16B: RAM Read and Write

Goal: Store to RAM and load back.

Build:
- RAM.
- RAM address from ABUS.
- RAM data to DBUS.
- RAM `/CE` from `/A15`.
- RAM `/WE` from `/AC_BUF`.
- RAM `/OE` LOW.

Look at:
- RAM `/CE`.
- RAM `/WE`.
- DBUS.
- AC.

Expected program:

```asm
SETDP $80
LI $AA
SB $10
LB $10
```

Expected result:
- AC returns to `$AA`.

Pass:
- [ ] RAM write works.
- [ ] RAM read works.
- [ ] ROM read via `SETDP $00; LB $00` still works.

Stop if:
- RAM and ROM are both selected.
- Store to ROM page makes chips hot.
- AC does not match stored byte.

Notes:

```text

```

---

## Stage 17: EI and IRQ Polling Latch

Goal: Add interrupt enable and sticky IRQ flag.

Build:
- U31.
- U33 gate 2 for `EI_decode`.
- LED on IE.
- LED on `IRQ_FF`.
- Pull-up resistor on `/IRQ`.

Look at:
- U31-5 IE.
- U31-9 `IRQ_FF`.
- `/IRQ`.

Expected:
- Reset: both LEDs off.
- EI `$08`: IE LED on.
- DI `$48`: IE unchanged.
- Pull `/IRQ` LOW, then release HIGH: `IRQ_FF` LED on.
- CPU does not jump automatically.

Pass:
- [ ] EI sets IE.
- [ ] DI has no v1.0 hardware effect.
- [ ] IRQ_FF latches on release/rising edge.
- [ ] Reset clears both LEDs.

Stop if:
- IRQ_FF turns on while `/IRQ` is held low before release.
- CPU jumps when IRQ happens.
- IRQ_FF does not clear on reset.

Notes:

```text

```

---

## Stage 18A: RV8-Bus Continuity

Goal: Route the 40-pin bus without disturbing the CPU.

Build:
- IDC 40-pin connector.
- Address pins 1-16 from ABUS.
- Data pins 17-24 from DBUS.
- VCC pin 39.
- GND pin 40.

Look at:
- Continuity from CPU board to connector.
- No shorts between neighbor pins.

Expected:
- Every connected pin reaches the correct CPU signal.
- Reserved pins are not accidentally connected.

Pass:
- [ ] Address pins pass continuity test.
- [ ] Data pins pass continuity test.
- [ ] VCC/GND correct.
- [ ] No shorts.

Stop if:
- Ribbon connector is reversed.
- VCC and GND are swapped.

Notes:

```text

```

---

## Stage 18B: RV8-Bus Control Signals

Goal: Export clock, reset, write, read/debug, IRQ, and T2.

Build:
- Pin 25 `CLK`.
- Pin 26 `/RST`.
- Pin 27 `/WR`.
- Pin 28 `/RD` or debug read timing signal.
- Pin 29 `/IRQ`.
- Pin 32 `T2`.
- Pin 33 duplicate A15.

Look at:
- Bus pins with logic probe.

Expected:
- CLK appears on pin 25.
- Reset appears on pin 26.
- STORE makes `/WR` LOW on pin 27.
- Pull `/IRQ` LOW then release: IRQ_FF LED latches.
- T2 appears on pin 32.

Pass:
- [ ] Control pins work.
- [ ] CPU still runs after connector is attached.

Stop if:
- CPU stops after connecting bus.
- `/WR` pulses when not storing.
- `/IRQ` floats.

Notes:

```text

```

---

## Stage 19: Full Boot Test

Goal: Prove the CPU starts from ROM without help.

ROM:

```asm
SETDP $80
SETPG $00
LI $00
J $06
```

Look at:
- PC.
- DP.
- PG.
- AC.
- Z.

Expected:
- After 3 clocks: first instruction in progress.
- After 9 clocks: DP=`$80`, PG=`$00`, AC=`$00`, Z=1.
- Then PC loops at `$0006`.

Pass:
- [ ] CPU boots from ROM.
- [ ] State is defined after boot sequence.
- [ ] PC loops at expected address.

Stop if:
- First instruction is not `SETDP`.
- Jump uses unknown PG.
- RAM access happens before DP is initialized.

Notes:

```text

```

---

## Stage 20A: Small Instruction Smoke Test

Goal: Run a tiny program before the full test ROM.

ROM idea:

```asm
SETDP $80
SETPG $00
LI $05
ADDI $03
SUBI $08
BEQ pass
J fail
pass:
J pass
fail:
J fail
```

Expected:
- AC becomes `$00`.
- Z becomes 1.
- PC reaches `pass`, not `fail`.

Pass:
- [ ] LI works.
- [ ] ADDI works.
- [ ] SUBI works.
- [ ] BEQ works.

Stop if:
- AC is not `$00`.
- Z is not 1.
- PC reaches fail loop.

Notes:

```text

```

---

## Stage 20B: Full Instruction Smoke Test

Goal: Run the larger ROM that checks the important instructions.

Test:
- LI
- ADDI
- SUBI
- BEQ
- BNE
- J
- SETPG
- SETDP
- SB
- LB
- EI/DI inert behavior if included

Expected:
- Program reaches pass loop.
- Program does not reach fail loop.

Pass:
- [ ] Pass loop reached.
- [ ] Fail loop not reached.
- [ ] Runs at slow clock.
- [ ] Runs at 1 MHz after slow-clock pass.
- [ ] Teacher recorded timing evidence in `../07_real_build_timing_log.md`.

Stop if:
- Any single-step trace differs from expected.
- 1 MHz fails but slow clock passes; this is likely timing or wiring length.

Notes:

```text

```

---

## Student Daily Log

Use one block per class day.

```text
Date:
Stage worked on:
What worked:
What failed:
What we fixed:
Teacher checked:
```

---

## Teacher Checkpoints

Do not skip these checks:

| Checkpoint | Must Pass Before |
|------------|------------------|
| Power good and no hot chips | Any logic IC |
| T0/T1/T2 correct | PC and IR fetch |
| PC counts and resets | ROM fetch |
| ROM byte correct on DBUS | IR latch |
| U7 direction verified | Any IBUS work |
| Store path safe | RAM |
| Z flag correct | Branch |
| SETPG works | Long jump |
| SETDP works | RAM tests |
| IRQ release/rising edge works | RV8-Bus finish |

---

## Simple Fault Map

| Symptom | First place to check |
|---------|----------------------|
| LEDs random | Missing pull-up/down or floating bus |
| Chip warm | Power pin wrong or bus contention |
| Ring skips | Clock bounce |
| PC wrong | PC_INC, carry chain, `/RST` |
| ROM wrong byte | Address bit order |
| IBUS wrong | U7 direction or `/OE` |
| LI works, ADDI fails | ALU or AC mux |
| ADDI works, BEQ fails | Z flag or branch logic |
| J goes wrong page | PG register wiring |
| RAM fails | DP, RAM `/CE`, RAM `/WE`, U7 direction |
| IRQ LED never lights after release | `/IRQ` pull-up, U31-11, U31 pinout |
