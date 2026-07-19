# RV4-Tiny v1.3 Build Plan

Build one module, test it, then continue. Stop when a test fails.

Each module must have:

- visible probe points or LEDs;
- one exact pass condition;
- a list of temporary test wires;
- a "remove before next stage" check.

## 0. Prepare

- Run `python3 tools/verify_docs.py`.
- Choose exact IC, ROM, and SRAM part numbers.
- Get their datasheets.
- Confirm all 16 ICs, sockets, capacitors, resistors, and test tools.

Pass: no unknown part or pinout.

## 1. Power rails

- Wire +5 V and GND.
- Add bypass and bulk capacitors.
- Check for shorts before inserting ICs.

Pass: correct voltage at every socket.

## 2. Clock/control support

Build U14/U15.

Check:

- one STEP press gives one CPU clock pulse;
- EXT and STEP are never joined;
- CPU_CLK_N is the inverse of CPU_CLK;
- forced inputs make the expected AC_LOAD_N and HLT_D.

Pass: clean waveforms on an oscilloscope or logic analyzer.

Remove before next stage:

- any forced `AC_LOAD_N`;
- any forced `HLT_D`;
- any direct STEP/EXT tie used only for testing.

## 3. Phase and HALT

Add U2.

Check:

```text
T: FETCH, EXECUTE, FETCH, EXECUTE...
```

Force HLT_D high for one edge. Later clock pulses must be blocked. RESET must
restore `T=FETCH`, `HALT=0`, and `RUN=1`.

Remove before next stage:

- forced `HLT_D`;
- any manual `RUN` or `HALT` override.

## 4. PC

Add U1.

Check:

- count only on FETCH;
- wrap from F to 0;
- load ARG on a forced taken jump;
- reset to 0.

Remove before next stage:

- forced `PC_LOAD_N`;
- forced `ARG0..ARG3` jump target wires.

## 5. ROM and IR

Program ROM with:

```text
41 90 F0 F0 ... F0
```

Add U10 and U3. IR must read `41`, `90`, `F0` on FETCH edges only.

Remove before next stage:

- any forced ROM data or IR input wires.

## 6. Decoder

Add U7. A selected output may go low only during:

```text
EXECUTE and CPU_CLK low
```

All outputs must stay high during FETCH and clock-high.

Remove before next stage:

- any forced `OP0..OP3`;
- any forced decoder enable.

## 7. AC and OUT

Add U8, U9, U4, U5.

Run:

```asm
LI 5
OUT
HLT
```

Pass: AC becomes 5, then OUT becomes 5 and stays 5.

Remove before next stage:

- any forced AC mux input;
- any temporary OUT LED bypass.

## 8. RAM module

Add U11, U16, and four series resistors.

Run:

```asm
LI 3
SW $E
LW $E
OUT
HLT
```

Pass: one safe write pulse, RAM[E]=3, OUT=3, no bus fight.

Remove before next stage:

- any forced `SW_N`;
- any direct AC-to-RAM_D jumper used before U16 is connected.

## 9. Adder

Add U6.

Run:

```asm
LI 14
SW $E
LI 3
SW $F
LW $E
ADD $F
OUT
HLT
```

Pass: OUT=1.

Remove before next stage:

- any forced RAM_D or ALU output test wires.

## 10. Zero and branch

Add U13 and U12.

- Check Z for all AC values: high only at 0.
- Test J to every target.
- Test JZ at zero and every nonzero value.

Remove before next stage:

- forced `Z`;
- forced `PC_LOAD_N`;
- any manual branch/jump override.

## 11. Full programs

Run:

- moving LED values;
- RAM counter;
- input echo;
- taken and not-taken branches;
- HLT and reset recovery.

Pass: recorded states match the simulator.

## 12. Headers

Check continuity, pin 1, input pulls, external clock level, and output
ownership. Optional modules must not drive against core outputs.

## Failure rule

When a lab fails:

1. stop;
2. record signals before and after the failing edge;
3. compare with the simulator and wiring source of truth;
4. fix the cause;
5. repeat the same lab.
