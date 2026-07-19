# RV4-Tiny v1.3 Hardware Review

Status: architecture approved; graphical schematic still required.

## Why this version is safe to build

Earlier drafts had three serious problems:

- register clocks could pulse twice;
- zero detection was wrong;
- one logic chip was assigned more gates than it contained.

v1.3 fixes them:

- every register uses one shared `CPU_CLK`;
- U13 is a direct four-input NOR zero detector;
- every U12/U14/U15 gate has an assigned job;
- U16 disconnects AC from RAM during reads.

## Package count

```text
U1  74HC161   PC
U2  74HC74    phase/HALT
U3  74HC377   IR
U4  74HC161   AC
U5  74HC161   OUT
U6  74HC283   adder
U7  74HC154   decoder
U8  74HC153   AC mux bits 0-1
U9  74HC153   AC mux bits 2-3
U10 EEPROM    program ROM
U11 SRAM      data RAM
U12 74HC00    branch logic
U13 74HC4002  zero detector
U14 74HC14    conditioning/inverters
U15 74HC20    load/clock control
U16 74HC125   RAM write driver
```

Total: 16 packages.

## Teaching choices

- AC and OUT are separate, so LEDs keep their value while AC changes.
- RAM and U16 stay visible, so students learn bus ownership.
- U14/U15 are taught as one support module, but their signals remain probeable.
- Hardwired control is visible; there is no microcode or programmable logic.

## Checks required before hardware

- The graphical schematic matches `02_signal_assignment.md`.
- ERC finds no floating input or output conflict.
- Exact ROM and SRAM datasheets are selected.
- The simulator passes all tests.
- Manual clock and reset are checked with an oscilloscope or logic analyzer.

## Important limits

This review does not prove a maximum clock speed or breadboard signal quality.
Use slow clocks first. Increase speed only after checking worst-case datasheet
timing and real waveforms.

An ESP32-C3 uses 3.3 V logic. Do not connect it to 5 V HC logic without checking
input thresholds and voltage limits.
