# RV8GR KiCad vs RV8GR-CPU-paul.pdf Comparison Report

Date: 2026-07-09

## Scope

Compared:

- Reference PDF: `RV8GR-CPU-paul.pdf`
- Current generated KiCad source: `RV8GR.kicad_pro`, `RV8GR.kicad_sch`, `RV8GR.net`, and module sheets
- Current source-of-truth docs: `../doc/02_wiring_guide.md` and `../doc/12_netlist.md`

## Method

- Extracted PDF text with `pdftotext -layout`.
- Rendered the PDF page and visually checked the schematic.
- Parsed `RV8GR.net` component references and values.
- Searched current KiCad/doc files for matching designators, bus names, and chip values.

Limit: `RV8GR-CPU-paul.pdf` is a graphical schematic print, not a KiCad netlist. This report can confirm visible designator/value/name mismatches, but it cannot prove every drawn wire connection automatically.

## Summary

The current generated KiCad project does **not** fully match `RV8GR-CPU-paul.pdf`.

The largest mismatch is design intent/version: Paul's PDF appears to be a one-page schematic using memory designators `U34` and `U35`, while the current RV8GR generated KiCad/netlist follows the newer 34-logic-chip baseline where `U34` is a 74HC541 IRL-to-IBUS immediate buffer and memory parts are named `ROM1` and `RAM1`.

## Confirmed Matches

| Area | Match |
|------|-------|
| Core PC counters | PDF uses U1-U4 74HC161; current KiCad uses U1-U4 74HC161 |
| IR registers | PDF uses U5/U6 74HC574; current KiCad uses U5/U6 74HC574 |
| Bus transceiver | PDF uses U7 74HC245; current KiCad uses U7 74HC245 |
| Ring counter | PDF uses U8 74HC164; current KiCad uses U8 74HC164 |
| Accumulator | PDF uses U9 74HC574; current KiCad uses U9 74HC574 |
| Adders/XOR/muxes | PDF uses 74HC283/74HC86/74HC157 blocks; current KiCad uses the same families for U10-U20 |
| Z detect | PDF uses U21 74HC74 and U22 74HC688; current KiCad uses U21 74HC74 and U22 74HC688 |
| Page/Data page registers | PDF uses U23/U32 74HC574; current KiCad uses U23/U32 74HC574 |
| Control glue | PDF uses U24 74HC04, U25 74HC32, U28 74HC86, U33 74HC21; current KiCad uses the same designators/families |
| Bus names | PDF visibly uses address/data/internal-style buses such as `A[0..15]`, `D[0..7]`, `I[0..7]`, `AC[0..7]`, `DP[0..7]`; current KiCad/netlist has equivalent ABUS, DBUS, IBUS, AC, DP nets |

## Confirmed Mismatches

| # | Area | PDF `RV8GR-CPU-paul.pdf` | Current KiCad/netlist | Impact |
|---|------|--------------------------|------------------------|--------|
| 1 | U34 designator | `U34` is the 28C256 ROM | `U34` is 74HC541 IRL-to-IBUS immediate buffer | Major designator conflict. A BOM or wiring guide using U34 from the PDF will not match current RV8GR docs/netlist. |
| 2 | RAM designator | `U35` is 62256 RAM | RAM is `RAM1`; no `U35` component exists | Major designator conflict. |
| 3 | ROM designator | ROM is `U34` and value text is `28C256` | ROM is `ROM1` and value is `AT28C256` | Same part family intent, different reference naming. |
| 4 | Immediate buffer | No visible separate U34 74HC541 immediate buffer in the PDF | Current design has U34 74HC541 controlled by `/IRL_OE` and connected IRL -> IBUS | Major baseline-version mismatch. Current RV8GR uses U34 to avoid immediate/IBUS ownership ambiguity. |
| 5 | RV8-Bus connector | PDF has `P1` labeled RV8Bus with A0-A15, D0-D7, CLK/RST/WRn/RDn/IRQn/SLT pins | Current generated KiCad netlist has no `P1` component; RV8-Bus pins are documented in `doc/12_netlist.md` but not instantiated in `RV8GR.net` | Schematic capture mismatch. A physical KiCad schematic should add P1 if it is meant to match the PDF. |
| 6 | NAND family label | PDF labels several NAND gates as `74AHC00` | Current KiCad uses `74HC00` for U26/U27 | Family mismatch. Check whether Paul intended AHC for timing or this is a symbol/library label choice. |
| 7 | Control signal naming | PDF uses names such as `IRLoe`, `ACbuff`, `BUFFoeN`, `WRDIR`/`WRDIRn`, `WRn`, `RDn`, `IRQn` | Current docs/netlist use `/IRL_OE`, `/AC_BUF`, `BUF_OE_N`, `WR_DIR`, `/WR`, `/RD`, `/IRQ` | Naming mismatch only if electrical polarity is equivalent. Needs a net-name mapping table before manual schematic reconciliation. |
| 8 | Schematic organization | PDF is a complete one-page schematic with symbols and drawn wiring | Current generated KiCad top sheet is a generated scaffold/global-label view plus separate module sheets and machine-readable netlist | Form mismatch. Current KiCad is not a hand-drawn one-page schematic matching Paul’s PDF layout. |

## Current KiCad Netlist Facts

Parsed from `RV8GR.net`:

- Nets: 159
- Components/packages: 36
- Pin connections: 598
- `P1`: absent
- `U34`: 74HC541
- `U35`: absent
- `ROM1`: AT28C256
- `RAM1`: 62256
- `U26`: 74HC00
- `U27`: 74HC00

## Recommended Fix Path

Choose one direction before editing KiCad:

1. **Keep current RV8GR baseline as source of truth**
   Treat Paul’s PDF as an older/reference schematic. Keep `U34 = 74HC541`, `ROM1`, `RAM1`, and add a clear note that the PDF is not pin/designator-compatible with current RV8GR.

2. **Make KiCad visually match Paul’s PDF**
   Rename current `U34` immediate buffer to a new logic designator, rename memory to `U34`/`U35`, instantiate `P1`, and update every doc/netlist/sim/RTL reference. This is a large migration and risks breaking the current verified 34-logic-chip baseline.

3. **Create a compatibility mapping sheet**
   Keep current netlist naming, but add a manual `PDF_TO_CURRENT_KICAD_MAP.md` that maps PDF names (`I[0..7]`, `WRn`, `U34 ROM`, `U35 RAM`, `P1`) to current RV8GR names (`IBUS`, `/WR`, `ROM1`, `RAM1`, documented RV8-Bus pins).

## Recommendation

Use option 1 or 3. The current RV8GR docs, simulator, chip-level Verilog, and netlist have already converged on the newer baseline with `U34` as the immediate buffer. Reverting to Paul’s PDF designators would require a broad renumbering pass and fresh verification.
