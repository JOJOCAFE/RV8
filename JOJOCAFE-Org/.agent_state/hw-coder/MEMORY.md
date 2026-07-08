# HW Coder Memory

## Build Status

- RV8-GR: designed, wiring guide complete, NOT YET BUILT physically
- BOM finalized, 5-board breadboard layout planned
- Programmer board: designed (ESP32 + TXS0108E + 74HC595)

## Source of Truth

- Pin-level wiring: `doc/03_wiring_guide.md`
- Circuit design: `doc/00_design_isa.md`
- Module guide: `doc/05_understand_by_module.md`
- Shared components: `/home/jo/kiro/Components`
- Components remote: `git@github.com:JOJOCAFE/Components.git`

## Board Layout (5 breadboards)

1. Clock + Reset + Power
2. PC + Ring Counter + IR
3. ALU + Accumulator + Z-flag
4. Address Mux + Page Registers
5. Bus Buffer + RAM/ROM + I/O

## Key Constraints

- 33 logic chips frozen (U1-U33)
- 1 MHz for breadboard (generous timing margin)
- Every IC needs 100nF decoupling cap
- Wire colors: red=VCC, black=GND, yellow=data, blue=address, green=control

## Programmer Pinout

- ESP32 GPIOs: DATA=[13,12,14,27,26,25,33,32]
- Shift register: DATA=23, CLK=18, LATCH=19
- Control: /CE=4, /OE=16, /WE=17

## Pending

- Physical build of all 14 labs
- PCB layout for 4 MHz version
- KiCad schematics (6 modules planned)

## Component Library Responsibility

- Own `*-pin.md` physical pinout docs for 74HC and memory components.
- Every non-blocked pinout must cite a manufacturer datasheet and explicitly prove DIP/PDIP or equivalent through-hole package form.
- Use AllDatasheet as helper only: search, open exact result, fetch PDF view page, parse PDF.js `file=` datasheet URL, download, confirm `%PDF`; or POST visible security code + `tmpinfo1aa` to the download endpoint.
- Keep `/home/jo/kiro/Components/source` clean: only retained cited manufacturer PDFs, no duplicates or `Zone.Identifier`.
- Current blocked pinout placeholders: `74HC/74hc150-pin.md`, `74HC/74hc260-pin.md`.
