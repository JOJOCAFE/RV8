# RV8GR KiCad Project

Generated on 2026-07-09

## Files

| File | Description |
|------|-------------|
| RV8GR.kicad_pro | Project file |
| RV8GR.kicad_sch | Top-level schematic |
| CLK_RST.kicad_sch | Clock, Reset, Ring Counter (U8) |
| PC.kicad_sch | Program Counter (U1-U4) |
| ADDR_MEM.kicad_sch | Address Mux + ROM + RAM (U15-U16, U29-U30) |
| IR_BUF.kicad_sch | Instruction Register + Bus Buffers (U5-U7, U14, U34) |
| ALU_AC.kicad_sch | ALU + Accumulator + Z Flag (U9-U22) |
| CTRL.kicad_sch | Control Logic (U23-U28, U31-U33) |
| RV8GR.net | Current KiCad netlist generated from `gen_kicad.py` |
| RV8GR-CPU-paul.EDF | Current-baseline EDIF/EDF netlist generated from `gen_kicad.py` |
| RV8GR-CPU-paul.pdf | Current-baseline merged KiCad PDF export |

## Chip Summary

| Module | Chips | Count |
|--------|-------|-------|
| CLK_RST | U8 (74HC164) | 1 |
| PC | U1-U4 (74HC161) | 4 |
| ADDR_MEM | U15, U16, U29, U30 (74HC157) + ROM + RAM | 6 |
| IR_BUF | U5, U6 (74HC574), U7 (74HC245), U14, U34 (74HC541) | 5 |
| ALU_AC | U9 (574), U10-U11 (283), U12-U13 (86), U17-U20 (157), U21 (74), U22 (688) | 11 |
| CTRL | U23 (574), U24 (04), U25 (32), U26-U27 (00), U28 (86), U31 (74), U32 (574), U33 (21) | 9 |
| **Total** | | **36** |

## ERC Status

`kicad-cli sch erc RV8GR.kicad_sch` currently reports 57 errors. They are all
expected dangling-label issues for this generated top-level scaffold:

1. **Unconnected pins** - All symbol pins need explicit net labels or wire connections
2. **Hierarchical label mismatch** - Top-level sheet symbols need to be created with matching pins
3. **Missing connections** - Internal wiring between chips not yet drawn

## Next Steps

To complete the schematic:

1. **Add hierarchical sheet symbols** on the top-level schematic
2. **Add net labels** to all chip pins according to the wiring guide
3. **Connect power pins** (VCC/GND) to power symbols
4. **Add bypass capacitors** near each chip's power pins
5. **Create the RV8-Bus connector** (40-pin IDC header)
6. **Run ERC again** and fix remaining issues

## Net Names (from wiring guide)

### Buses
- IBUS[7:0] - Internal data bus
- DBUS[7:0] - Memory data bus
- ABUS[15:0] - Address bus

### Control Signals
- CLK, /RST - System clock and reset
- T0, T1, T2 - Phase timing
- PC_INC, /PC_LD - Program counter control
- /ADDR_MODE - Address multiplexer select (LOW=data address, HIGH=PC)
- ACC_CLK - Accumulator clock
- /IRL_OE, /AC_BUF, BUF_OE_N, WR_DIR - Bus control

### Register Outputs
- PC[15:0] - Program counter
- IRL[7:0] - Instruction register low (operand)
- PG[7:0] - Page register
- DP[7:0] - Data page register
- AC[7:0] - Accumulator
- Z_flag - Zero flag

## Reference

See `doc/10_kicad_modules.md` and `doc/02_wiring_guide.md` for complete pin-level wiring details.

## Current PDF/EDF Files

`RV8GR-CPU-paul.pdf` and `RV8GR-CPU-paul.EDF` now follow the current RV8GR
source-of-truth netlist: `U34` is the 74HC541 IRL-to-IBUS immediate buffer,
and memory is named `ROM1` and `RAM1`.

Regenerate the single-page top-level PDF from this directory with:

```bash
kicad-cli sch export pdf --black-and-white --output RV8GR-CPU-paul.pdf RV8GR.kicad_sch
```

The committed PDF is a merged export of the top-level page plus generated
module sheets.
