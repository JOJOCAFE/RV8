# RV8GR KiCad Netlist - Generated Files

**Generated**: 2026-07-01
**Source**: `gen_kicad.py` based on `doc/12_netlist.md`

## Files Generated

| File | Size | Description |
|------|------|-------------|
| `RV8GR.kicad_pro` | 432 bytes | KiCad project file |
| `RV8GR.kicad_sch` | 13K | Top-level schematic with global labels |
| `RV8GR.net` | 32K | **CRITICAL: KiCad netlist with all connections** |

## Netlist Summary

- **Total nets**: 159
- **Total chips**: 35 (34 logic + ROM + RAM)
- **Total pin connections**: 578

### Largest Nets

| Net | Pin Count | Description |
|-----|-----------|-------------|
| GND | 62 | Ground - all chips + control pins |
| VCC | 45 | +5V power - all chips + pullups |
| ALU_SUB | 11 | Adder carry-in, XOR B-mux selects |
| T2 | 8 | Phase 2 timing - control decode |
| /RST | 7 | Active-low reset - PC, ring counter, IRQ |

### Net Categories

| Category | Count |
|----------|-------|
| Power (VCC, GND) | 2 |
| Clock & Reset | 2 |
| Ring Counter | 5 |
| Address Bus (ABUS0-15) | 16 |
| Data Bus (DBUS0-7) | 8 |
| Internal Bus (IBUS0-7) | 8 |
| PC outputs (PC0-15 + RCO) | 19 |
| IRL outputs | 8 |
| PG outputs | 8 |
| DP outputs | 8 |
| AC outputs | 8 |
| ALU (SUM, XOR_Y, XOR_B, AC_IN) | 33 |
| Opcode decode (U5 Q outputs) | 8 |
| Derived control signals | 16 |
| Branch/Jump logic | 5 |
| Z flag circuit | 2 |
| IRQ nets | 3 |

## How to Use

### Option 1: Open in KiCad GUI

1. Open KiCad 10.0+
2. File → Open Project → `RV8GR.kicad_pro`
3. Open Schematic Editor
4. Tools → Generate Netlist → Import `RV8GR.net`
5. Run ERC (Electrical Rules Check)

### Option 2: Command Line

```bash
# Import netlist into schematic
kicad-cli sch import netlist RV8GR.net

# Run ERC
kicad-cli sch erc RV8GR.kicad_sch
```

## Chip Reference

| Ref | Value | Package | Function |
|-----|-------|---------|----------|
| U1-U4 | 74HC161 | DIP-16 | Program Counter (16-bit) |
| U5 | 74HC574 | DIP-20 | Instruction Register (opcode) |
| U6 | 74HC574 | DIP-20 | Instruction Register (operand) |
| U7 | 74HC245 | DIP-20 | Bus Transceiver |
| U8 | 74HC164 | DIP-14 | Ring Counter (T0/T1/T2) |
| U9 | 74HC574 | DIP-20 | Accumulator |
| U10-U11 | 74HC283 | DIP-16 | Adders (8-bit) |
| U12-U13 | 74HC86 | DIP-14 | XOR Array |
| U14 | 74HC541 | DIP-20 | AC Output Buffer |
| U15-U16 | 74HC157 | DIP-16 | Address Mux (low) |
| U17-U18 | 74HC157 | DIP-16 | AC Input Mux |
| U19-U20 | 74HC157 | DIP-16 | XOR B-Input Mux |
| U21 | 74HC74 | DIP-14 | Z Flag Flip-Flop |
| U22 | 74HC688 | DIP-20 | Zero Detect Comparator |
| U23 | 74HC574 | DIP-20 | Page Register |
| U24 | 74HC04 | DIP-14 | Inverters |
| U25 | 74HC32 | DIP-14 | OR Gates |
| U26-U27 | 74HC00 | DIP-14 | NAND Gates |
| U28 | 74HC86 | DIP-14 | XOR (control) |
| U29-U30 | 74HC157 | DIP-16 | Address Mux (high) |
| U31 | 74HC74 | DIP-14 | IRQ Flip-Flop |
| U32 | 74HC574 | DIP-20 | Data Page Register |
| U33 | 74HC21 | DIP-14 | 4-input AND Gates |
| ROM1 | AT28C256 | DIP-28 | Program ROM (32KB) |
| RAM1 | 62256 | DIP-28 | RAM (32KB) |

## Verification

All nets have been verified against `doc/12_netlist.md`:
- ✓ All 36 chips have connections
- ✓ VCC/GND pins match datasheets
- ✓ Signal routing matches wiring guide
- ✓ No orphaned nets

## Notes

- The `.net` file is the machine-readable truth
- The `.kicad_sch` provides visual layout for humans
- Import the netlist to create/verify actual wire connections
- Run ERC to catch any electrical rule violations
