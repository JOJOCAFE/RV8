# RV4-Tiny v1.3 Student Probe Header Plan

Use Plug-in LED/probe boards instead of permanent LEDs on every internal
signal. The CPU board exposes headers; students plug in the probe board for the
module they are learning.

## Purpose

- Keep the CPU board electrically cleaner than an LED on every net.
- Preserve the Ben Eater style of visible state.
- Follow the Petzold path: wires, switches, gates, memory, clock, registers,
  bus, control, jumps.
- Let one LED board move from header to header during the build.

## Probe Board Rule

The probe board must be high impedance except for LED current through a safe
resistor. Do not let a probe board drive a CPU signal unless that header is
explicitly an input header such as `IN`.

Recommended probe boards:

- 4-bit LED board for nibbles.
- 8-bit LED board for ROM/IR bytes.
- 8-switch input board for forced test values.
- 1-bit LED/probe board for control signals.

## Header Map

| Header | Signals | What students learn |
|---|---|---|
| H1 CLOCK | `CLK_COND`, `CPU_CLK`, `CPU_CLK_N`, `RESET_N` | clean clock and reset |
| H2 PHASE | `FETCH`, `EXEC`, `HALT`, `RUN` | CPU does one step per edge |
| H3 PC | `PC0..PC3`, `PC_LOAD_N` | program counter and jumps |
| H4 ROM | `ROM_D0..ROM_D7` | program bytes come from memory |
| H5 IR | `OP0..OP3`, `ARG0..ARG3` | instruction = opcode + operand |
| H6 DECODE | `LI_N`, `LW_N`, `ADD_N`, `IN_N`, `SW_N`, `OUT_N`, `JZ_N`, `J_N`, `HLT_N` | one selected action |
| H7 AC | `AC_D0..AC_D3`, `AC0..AC3` | selected input becomes stored value |
| H8 OUT | `OUT0..OUT3` | output register remembers a value |
| H9 RAM | `RAM_D0..RAM_D3`, `SW_N` | shared data bus and write control |
| H10 ALU | `AC0..AC3`, `RAM_D0..RAM_D3`, `ALU_OUT0..ALU_OUT3` | addition from two inputs |
| H11 BRANCH | `Z`, `JZ_N`, `J_N`, `PC_LOAD_N` | condition controls PC load |
| H12 IN | `IN0..IN3`, `GND`, `VCC` | switches provide external input |

If board space is tight, combine H1/H2, H7/H8, and H11 with nearby control
signals. Do not combine `IN` with output-only headers.

## Stage Use

| Build stage | Plug in header | Expected visible result |
|---|---|---|
| Power/clock | H1 | one clean `CPU_CLK` per STEP |
| Phase/HALT | H2 | `FETCH` and `EXEC` alternate; HALT stops RUN |
| PC | H3 | PC counts on FETCH and loads on jump |
| ROM/IR | H4 then H5 | ROM byte appears, then IR holds opcode/operand |
| Decoder | H6 | only one decode output low during EXECUTE clock-low |
| AC/OUT | H7 then H8 | AC changes on LI/LW/ADD/IN; OUT holds display |
| RAM | H9 | U16 owns RAM_D only during SW |
| Adder | H10 | `AC + RAM_D` appears on `ALU_OUT` |
| Branch | H11 | `PC_LOAD_N` goes low only for taken J/JZ |
| Input | H12 | switches appear on IN and can load AC |

## Schematic Rules

- Label every header pin with the exact signal name from
  `02_signal_assignment.md`.
- Mark pin 1 on every header.
- Put GND beside each multi-bit header for the probe board.
- Add VCC only on headers that need switch boards or active probe boards.
- Do not route high-current LEDs directly on internal nets.
- Keep `CPU_CLK`, `RESET_N`, and `RAM_D` probe stubs short.
- Probe headers must not drive CPU signals or create a second bus driver.

## Student Explanation Cards

Each header should have a small card:

```text
Header:
Signals:
Before clock:
After clock:
What changed:
If wrong, check:
```

Example for H5 IR:

```text
Before FETCH edge: ROM_D shows the next instruction byte.
After FETCH edge: OP and ARG hold that instruction.
If wrong: check PC, ROM address bits, ROM data bits, and U3 /E=T.
```

## Pass Requirement

A stage passes only when the student can point to the header, name the signal
group, and explain what changed after the clock edge.
