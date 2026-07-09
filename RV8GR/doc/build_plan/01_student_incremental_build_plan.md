# RV8-GR Student Incremental Build Plan

Build the CPU in small modules. Test each module before adding the next one.
The goal is to reduce mistakes: fewer chips powered at once, fewer wires to
debug, and one clear pass condition per stage.

This plan follows the v1.0 34-logic-chip wiring guide:
- IRQ is polling-only. No hardware vector.
- DI has no hardware effect.
- U7 `/OE` is `BUF_OE_N` from U24-12.
- ROM `/OE` is `WR_DIR` from U28-8.
- U31 IRQ latch uses Q2 on U31-9 and `/IRQ` clock on U31-11.

Use this document with:
- `doc/02_wiring_guide.md` for exact pin wiring.
- `doc/06_debug_plan.md` for deeper fault checks.
- `doc/10_kicad_modules.md` for KiCad sheet/module names.
- `doc/build_plan/02_student_worksheet.md` for student-facing stage cards.

---

## Student Baseline Contract

Build only this baseline before attempting any upgrade:

- 34 logic chips + ROM + RAM = 36 packages.
- No microcode ROM.
- No hardware IRQ vector.
- Every instruction uses T0, T1, T2.
- Only one IBUS driver may be active.
- Only one DBUS driver may be active.
- Each stage must pass before the next stage starts.

Future features such as hardware IRQ vectoring, ROM banking hardware, RETI,
and automatic PC save/restore are not part of this build plan.

---

## Build Rules

1. Build only one stage at a time.
2. Add power and 100nF bypass capacitor to every IC as soon as it is placed.
3. Keep a slow single-step clock until the full system test passes.
4. Put LEDs on the signal listed in each stage.
5. Do not continue if the stage does not pass.
6. When a stage fails, check power, ground, pin numbers, then signal polarity.

Recommended debug tools:
- 8 LED probe board for buses.
- 1 LED for single control signals.
- Logic probe or multimeter.
- Single-step clock button with debounce.
- Known ROM bytes for tests.

---

## Stage 0: Power, Clock, Reset

**Chips added**: none of the CPU logic yet.

**Build**
- 5V power rails.
- Ground rails.
- Reset circuit generating `/RST`.
- Single-step clock or slow 555 clock.
- LED on `CLK`.

**Test**
- VCC is 4.8V to 5.2V at the far end of the breadboard.
- GND continuity is good everywhere.
- Press clock once: exactly one pulse.
- Press reset: `/RST` goes LOW, then returns HIGH.

**Pass**
- Clock is clean.
- Reset is clean.
- No chips are hot.

**Do not continue if**
- Clock bounces.
- VCC drops below 4.8V.
- Reset floats.

---

## Stage 1: Ring Counter

**Chips added**: U8, U24 gates 1-2.

**Chip count in this stage**: 2 packages placed, but U24 is shared later.

**Build**
- U8 74HC164.
- U24 gates:
  - U24-1 <- T0, U24-2 -> U8-1.
  - U24-3 <- T1, U24-4 -> U8-2.
- U8-8 <- CLK.
- U8-9 <- `/RST`.
- LEDs on:
  - T0 = U8-3.
  - T1 = U8-4.
  - T2 = U8-5.

**Test**
- Reset.
- Single-step clock.

**Expected**
```text
Reset: T0=1 T1=0 T2=0
Clock 1: T0=0 T1=1 T2=0
Clock 2: T0=0 T1=0 T2=1
Clock 3: T0=1 T1=0 T2=0
```

**Pass**
- T0, T1, T2 rotate cleanly and repeat.

**Common mistakes**
- U24 inverter inputs/outputs swapped.
- U8 A/B inputs not both connected to feedback.
- Clock bounce makes the ring skip states.

---

## Stage 2: Program Counter Low Byte

**Chips added**: U1, U2.

**Total logic chips now**: 4 packages placed including U8/U24.

**Build**
- U1-U2 74HC161.
- U1-2, U2-2 <- CLK.
- U1-1, U2-1 <- `/RST`.
- Temporarily tie `PC_INC` HIGH for this isolated test:
  - U1-7, U1-10, U2-7 <- VCC.
- U2-10 <- U1-15.
- Tie `/LD` HIGH for count test:
  - U1-9, U2-9 <- VCC.
- LEDs on PC0-PC7:
  - U1 QA-QD = PC0-PC3.
  - U2 QA-QD = PC4-PC7.

**Test**
- Reset.
- Single-step 20 clocks.

**Expected**
```text
Reset: PC low = $00
Clock 1: $01
Clock 2: $02
...
Clock 15: $0F
Clock 16: $10
```

**Pass**
- U1 counts 0-15.
- U2 increments when U1 rolls over.

**Before continuing**
- Remove temporary VCC from `PC_INC`.
- Later `PC_INC` will come from U25-6.

**Remove temporary wiring**
- `PC_INC=HIGH` test jumper.
- `/LD=HIGH` test jumper.

---

## Stage 3: Full Program Counter

**Chips added**: U3, U4.

**Total logic chips now**: 6 packages placed.

**Build**
- U3-U4 74HC161.
- U3-2, U4-2 <- CLK.
- U3-1, U4-1 <- `/RST`.
- U3-10 <- U2-15.
- U4-10 <- U3-15.
- Temporarily tie:
  - U3-7, U4-7 <- VCC.
  - U3-9, U4-9 <- VCC.
- LEDs on at least PC0-PC7. If possible also PC8-PC15.

**Test**
- Reset.
- Step enough clocks to prove carry moves upward.

**Pass**
- PC counts upward without stuck bits.
- Reset always returns PC to `$0000`.

**Do not continue if**
- A bit is inverted or swapped.
- U2/U3/U4 never receive carry.

---

## Stage 4: Address Mux Low Byte

**Chips added**: U15, U16.

**Total logic chips now**: 8 packages placed.

**Build**
- U15-U16 74HC157.
- U15/U16 `SEL` temporarily switchable:
  - `/ADDR_MODE=1`: PC low.
  - `/ADDR_MODE=0`: IRL low test value from DIP switches.
- U15/U16 `/E` -> GND.
- LEDs on A0-A7.

**Test**
- With `/ADDR_MODE=1`, A0-A7 follow PC0-PC7.
- With `/ADDR_MODE=0`, A0-A7 follow DIP-switch IRL0-IRL7.

**Pass**
- All 8 address bits follow the selected source.

**Common mistakes**
- 74HC157 A/B inputs reversed.
- Output pins 4,7,9,12 confused with input pins.

---

## Stage 5: Address Mux High Byte

**Chips added**: U29, U30.

**Total logic chips now**: 10 packages placed.

**Build**
- U29-U30 74HC157.
- `SEL` tied to same temporary `/ADDR_MODE` as Stage 4.
- A input = temporary DP0-DP7 from DIP switches.
- B input = PC8-PC15.
- U30-12 is A15.
- LED on A15 at minimum. Better: LEDs on A8-A15.

**Test**
- `/ADDR_MODE=1`: A8-A15 follow PC high.
- `/ADDR_MODE=0`: A8-A15 follow DIP-switch DP.
- Set DP=$80: A15 should be HIGH.
- Set DP=$00: A15 should be LOW.

**Pass**
- High address mux selects PC or DP correctly.
- A15 is correct.

**Remove temporary wiring**
- Temporary `SEL` switch when real `/ADDR_MODE` is connected in Stage 9.
- Temporary DP DIP-switch wires when real DP outputs are connected in Stage 16.

---

## Stage 6: ROM Read

**Chips added**: ROM.

**Total packages now**: 10 logic + ROM.

**Build**
- ROM address A0-A14 <- ABUS A0-A14.
- ROM D0-D7 -> DBUS.
- ROM `/CE` <- A15.
- ROM `/OE` temporarily -> GND for this isolated fetch test.
- ROM `/WE` -> `/WR` / programmer write path. During CPU-only bring-up, hold
  `/WR` HIGH unless you are specifically testing store timing.

**Test ROM bytes**
```text
$0000 = $30
$0001 = $42
$0002 = $01
$0003 = $00
```

**Test**
- PC=$0000, A15=0: DBUS should be `$30`.
- PC=$0001: DBUS should be `$42`.
- Force A15=1: ROM output should be off.

**Pass**
- DBUS shows the programmed bytes.

**Before full CPU wiring**
- Change ROM `/OE` to `WR_DIR` from U28-8.
- This is required so ROM turns off during STORE direction.

**Remove temporary wiring**
- ROM `/OE` to GND test wire before STORE testing.

---

## Stage 7: U7 Bus Bridge

**Chips added**: U7.

**Total logic chips now**: 11 + ROM.

**Build**
- U7 74HC245.
- Physical wiring:
  - U7 A side pins 2-9 -> IBUS.
  - U7 B side pins 18-11 -> DBUS.
- U7-1 DIR <- temporary switch for now.
- U7-19 `/OE` <- temporary switch for now.

**Test Read Direction**
- Set U7-1 DIR=0.
- Set U7-19 `/OE`=0.
- ROM drives DBUS.
- IBUS should equal ROM byte.

**Test Disabled**
- Set U7-19 `/OE`=1.
- IBUS should not be driven by U7.

**Pass**
- U7 passes DBUS to IBUS when enabled and DIR=0.
- U7 releases bus when `/OE`=1.

**Remove temporary wiring**
- U7-1 temporary DIR switch before connecting `WR_DIR`.
- U7-19 temporary `/OE` switch before connecting `BUF_OE_N`.

**Common mistakes**
- A/B sides swapped.
- DIR polarity misunderstood:
  - Real 74HC245 with A=IBUS and B=DBUS:
  - DIR=0 means B->A, DBUS->IBUS.
  - DIR=1 means A->B, IBUS->DBUS.

---

## Stage 8: Instruction Registers

**Chips added**: U5, U6.

**Total logic chips now**: 13 + ROM.

**Build**
- U5 74HC574 IR_HIGH.
- U6 74HC574 IR_LOW.
- U5/U6 D inputs <- IBUS.
- U5 CLK <- T0.
- U6 CLK <- T1.
- U5 `/OE` -> GND.
- U6 `/OE` -> GND. Use LEDs/probes on IRL outputs when testing operand latch.

**Test**
- ROM at `$0000=$30`, `$0001=$42`.
- Reset PC.
- Clock T0: U5 should latch `$30`.
- Clock T1: U6 should latch `$42`.

**Expected U5 outputs for `$30`**
```text
MUX_SEL=1
AC_WR=1
all others 0
```

**Pass**
- U5 holds control byte.
- U6 holds operand byte.
- PC advanced twice.

**Remove temporary wiring**
- Temporary LEDs/probes on IRL outputs after U34 is added.

---

## Stage 9: Basic Control for Fetch and Immediate

**Chips added**: U34, U25 gate 1-2, U26 gate 1-2, U24 gate 6.

**Total packages now**: U24/U25/U26 are added, but some gates remain unused.

**Build**
- U25-1 <- SRC, U25-2 <- STR, U25-3 -> ADDR_REQ.
- U25-4 <- T0, U25-5 <- T1, U25-6 -> PC_INC.
- U26 gate 2 makes `/ADDR_MODE`.
- U26 gate 1 makes `/IRL_OE`.
- U24 gate 6 makes `BUF_OE_N`.
- U34 74HC541 immediate buffer:
  - A inputs <- IRL0-IRL7.
  - Y outputs -> IBUS0-IBUS7.
  - `/OE1` and `/OE2` <- `/IRL_OE`.
- Connect:
  - PC_INC -> U1/U2/U3/U4 enable pins.
  - /ADDR_MODE -> U15/U16/U29/U30 SEL.
  - `/IRL_OE` -> U34-1 and U34-19.
  - `BUF_OE_N` -> U7-19.

**Test**
- During T0 and T1:
  - PC_INC=1.
  - U7-19 LOW.
  - U34-1/19 HIGH.
- During T2 immediate instruction:
  - PC_INC=0.
  - U7-19 HIGH.
  - U34-1/19 LOW.

**Pass**
- Fetch path and immediate path alternate correctly.

**Remove temporary wiring**
- Any remaining manual `PC_INC`, `/ADDR_MODE`, `/IRL_OE`, or `BUF_OE_N`
  controls. These are now generated by U24/U25/U26.

---

## Stage 10: ALU Core

**Chips added**: U10, U11, U12, U13, U19, U20.

**Total logic chips now**: about 21 + ROM.

**Build**
- U19/U20 choose XOR B input:
  - XOR_MODE=0: ALU_SUB copied to all B bits.
  - XOR_MODE=1: AC bits.
- U12/U13 XOR IBUS with selected B.
- U10/U11 add AC + XOR result + ALU_SUB.

**Isolated Tests**
- Set AC=$10, IBUS=$05, ALU_SUB=0, XOR_MODE=0:
  - sum should be `$15`.
- Set AC=$10, IBUS=$05, ALU_SUB=1, XOR_MODE=0:
  - subtract path should compute `$0B`.
- Set AC=$AA, IBUS=$0F, XOR_MODE=1:
  - XOR output should be `$A5`.

**Pass**
- Low nibble and high nibble both correct.
- Carry from U10 to U11 works.

---

## Stage 11: AC Mux and Accumulator

**Chips added**: U17, U18, U9.

**Total logic chips now**: about 24 + ROM.

**Build**
- U17/U18 select adder sum or XOR output.
- U9 latches mux output.
- U9 CLK will later be ACC_CLK. For isolated test use manual pulse.
- U9 `/OE` -> GND.

**Test LI-like Path**
- Put `$42` on IBUS.
- MUX_SEL=1.
- XOR_MODE=0.
- ALU_SUB=0.
- Pulse U9 CLK.
- AC should become `$42`.

**Test ADDI-like Path**
- AC=`$42`.
- IBUS=`$01`.
- MUX_SEL=0.
- Pulse U9 CLK.
- AC should become `$43`.

**Pass**
- AC changes only when clocked.
- Mux select works.

**Remove temporary wiring**
- Manual U9 clock pulse before connecting `ACC_CLK` in the integrated CPU.

---

## Stage 12: AC Output Buffer and Store Direction

**Chips added**: U14 if not already placed with IR_BUF.

**Build**
- U14 inputs <- AC0-AC7.
- U14 outputs -> IBUS.
- U14 `/OE1` and `/OE2` <- `/AC_BUF`.
- U7 DIR <- WR_DIR.
- ROM `/OE` <- WR_DIR.

**Test Store Contract**
- Force T2 store condition:
  - `/AC_BUF=0`.
  - WR_DIR=1.
  - `BUF_OE_N=0`.
- Check:
  - U14 drives IBUS.
  - U7-19 LOW.
  - U7-1 HIGH.
  - DBUS equals AC.
  - ROM `/OE` HIGH.

**Pass**
- Store drives AC to DBUS.
- ROM is off during store direction.

**Do not continue if**
- U7-19 is HIGH during store.
- ROM `/OE` stays LOW during store.

---

## Stage 13: Z Flag

**Chips added**: U21, U22.

**Total logic chips now**: about 26 + ROM.

**Build**
- U22 compares AC with zero.
- U22-19 `/P=Q` -> U21-4 `/PR1`.
- U21-3 CLK <- ACC_CLK.
- U21-2 D1 -> GND.
- U21-1 `/CLR1` -> VCC.
- U21-5 -> Z_flag LED.
- U21 FF2 unused:
  - U21-8 `/Q2` NC.
  - U21-9 Q2 NC.
  - U21-10 `/PR2` VCC.
  - U21-11 CLK2 GND.
  - U21-12 D2 GND.
  - U21-13 `/CLR2` VCC.

**Test**
- Load AC=`$01`: Z LED off.
- Load AC=`$00`: Z LED on.
- Repeat `$01`, `$00` to prove it toggles.

**Pass**
- Z follows whether AC is zero after AC updates.

---

## Stage 14: Branch and Jump Control

**Chips added**: U27, U28 gates, remaining U24 gates.

**Build**
- U28 gate 1: Z_match = Z_flag XOR ALU_SUB.
- U24 gate 4: `/JMP`.
- U27 gate 1: `/BR_TAKEN`.
- U27 gate 2: PC_LOAD_COND.
- U26 gate 4: `/PC_LD`.
- Connect `/PC_LD` to U1-U4 pin 9.

**Test J**
- Set JMP=1.
- During T2, `/PC_LD` should go LOW.

**Test BEQ**
- BR=1, ALU_SUB=0.
- Z=1: `/PC_LD` LOW.
- Z=0: `/PC_LD` HIGH.

**Test BNE**
- BR=1, ALU_SUB=1.
- Z=0: `/PC_LD` LOW.
- Z=1: `/PC_LD` HIGH.

**Pass**
- Jump/branch never loads PC outside T2.

**Remove temporary wiring**
- Any manual `/PC_LD`, `JMP`, `BR`, `ALU_SUB`, or `Z` test forcing wires
  before running ROM tests.

---

## Stage 15: Page Register

**Chips added**: U23.

**Build**
- U23 D inputs <- IBUS.
- U23 Q outputs -> U3/U4 D inputs.
- U27 gate 3 makes `/PG_cond`.
- U28 gate 2 makes `/T2`.
- U25 gate 4 makes PG_CLK.
- U23 CLK <- PG_CLK.
- U23 `/OE` -> GND.

**Test**
- Execute or force SETPG `$90`.
- PG LEDs should show `$90`.
- Execute J `$00`.
- PC should load `$9000`.

**Pass**
- Page register holds high byte for jump target.

**Remove temporary wiring**
- Any forced `PG_CLK` or IBUS test pattern wires before full boot testing.

---

## Stage 16: RAM and Data Page

**Chips added**: RAM, U32, U33.

**Total packages now**: 34 logic + ROM + RAM if all previous stages are present.

**Build**
- RAM:
  - A0-A14 <- ABUS.
  - D0-D7 <-> DBUS.
  - `/CE` <- `/A15` from U24-6.
  - `/OE` -> GND.
  - `/WE` <- `/AC_BUF`.
- U32 Data Page:
  - D inputs <- IBUS.
  - Q outputs -> U29/U30 A inputs.
  - CLK <- DP_Load from U33-6.
  - `/OE` -> GND.
- U33 gate 1:
  - T2, XOR_MODE, `/ADDR_MODE`, `/AC_WR` -> DP_Load.

**Test SETDP**
- SETDP `$80`: DP LEDs show `$80`.
- SETDP `$90`: DP LEDs show `$90`.

**Test RAM**
- SETDP `$80`.
- LI `$AA`.
- SB `$10`.
- LB `$10`.
- AC should be `$AA`.

**Test ROM Read via DP**
- SETDP `$00`.
- LB `$00`.
- AC should equal ROM byte at `$0000`.

**Pass**
- RAM read/write works.
- ROM read through data access works.
- SB to ROM page does not corrupt ROM and does not cause DBUS fight. ROM `/WE`
  may see `/WR`, but normal CPU stores do not perform the EEPROM/flash unlock
  sequence.

**Remove temporary wiring**
- Any forced `DP_Load`, DP DIP input, RAM `/WE`, or RAM `/OE` test controls
  that bypass the official control signals.

---

## Stage 17: EI and IRQ Polling Latch

**Chips added**: U31, U33 gate 2.

**Build**
- U33 gate 2 makes EI_decode:
  - U33-9 <- T2.
  - U33-10 <- SRC.
  - U33-12 <- `/XOR_MODE`.
  - U33-13 <- `/AC_WR`.
  - U33-8 -> U31-3.
- U31 FF1 IE:
  - U31-1 `/CLR1` <- `/RST`.
  - U31-2 D1 -> VCC.
  - U31-3 CLK1 <- EI_decode.
  - U31-4 `/PR1` -> VCC.
  - U31-5 Q1 -> IE LED.
- U31 FF2 IRQ_FF:
  - U31-8 `/Q2` -> NC.
  - U31-9 Q2 -> IRQ_FF LED.
  - U31-10 `/PR2` -> VCC.
  - U31-11 CLK2 <- `/IRQ`.
  - U31-12 D2 -> VCC.
  - U31-13 `/CLR2` <- `/RST`.

**Test**
- Reset: IE LED off, IRQ_FF LED off.
- Execute EI `$08`: IE LED on.
- Execute DI `$48`: IE LED unchanged.
- Pull `/IRQ` low, then release it HIGH: IRQ_FF LED on.
- Continue clocking: PC does not jump automatically.
- Reset: both LEDs off.

**Pass**
- IRQ is a sticky polling latch.
- No hardware vector behavior exists.

**Do not add**
- No PC force path.
- No `$FF00` vector mux.
- No IRQ acknowledge/clear circuit.

---

## Stage 18: RV8-Bus Connector

**Chips added**: connector only.

**Build**
- A0-A15 to bus pins 1-16.
- D0-D7 to bus pins 17-24.
- CLK to pin 25.
- `/RST` to pin 26.
- `/WR` = `/AC_BUF` to pin 27.
- `/RD` informational to pin 28.
- `/IRQ` from bus pin 29 to U31-11.
- T2 to pin 32.
- VCC pin 39, GND pin 40.

**Test**
- Clock appears on bus pin 25.
- Reset appears on pin 26.
- STORE produces LOW pulse on pin 27.
- Pull `/IRQ` low then release: IRQ_FF LED latches.

**Pass**
- Bus does not disturb CPU operation.

**Do not add**
- No expansion card may drive DBUS unless it is selected and the CPU is in a
  read phase.

---

## Stage 19: Full Boot Test

**Test ROM**
```asm
SETDP $80
SETPG $00
LI $00
J $06
```

**Expected**
- After 3 clocks: DP=`$80`.
- After 6 clocks: PG=`$00`.
- After 9 clocks: AC=`$00`, Z=1.
- After 12 clocks: PC loops at `$0006`.

**Pass**
- CPU boots without programmer intervention.
- PC, DP, PG, AC, and Z are defined.

---

## Stage 20: Full Instruction Smoke Test

Use a ROM that tests:
- LI
- ADDI
- SUBI
- BEQ
- J
- SETDP
- SETPG
- SB
- LB

**Pass condition**
- Program reaches the pass loop, not the fail loop.
- Suggested pass loop: PC=`$0010`.
- Suggested fail loop: PC=`$0012`.

---

## Minimum Continue Checklist

Before moving to the next stage, write down:

```text
Stage:
Date:
Clock mode:
VCC measured:
Observed LEDs:
Temporary wires removed:
Pass/fail:
If failed, fixed what:
```

If a later stage fails, return to the last passed stage and retest it first.

---

## Quick Fault Map

| Symptom | Likely area |
|---------|-------------|
| T0/T1/T2 skip | Clock debounce or U8/U24 feedback |
| PC does not count | PC_INC, `/RST`, CLK, 74HC161 cascade |
| ROM byte wrong | Address bit swap, ROM `/CE`, ROM image |
| U5/U6 latch wrong | U7 direction, T0/T1, IBUS wiring |
| LI works but ADDI fails | ALU path U10-U13/U17-U20 |
| ADDI works but BEQ fails | Z flag or branch logic |
| J jumps to wrong page | U23 PG wiring to U3/U4 |
| SB/LB fails | U7 store/read direction, RAM `/WE`, DP value |
| STORE causes hot chip | ROM `/OE` not tied to WR_DIR, DBUS fight |
| IRQ LED never lights after release | `/IRQ` not reaching U31-11, missing pull-up/rising edge, U31 pinout wrong |
| CPU jumps on IRQ | You accidentally built future vector logic; remove it for v1.0 |
