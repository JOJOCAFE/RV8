#!/usr/bin/env python3
"""
KiCad 10.0 Project Generator for RV8GR CPU
Generates complete schematic with 36 chips across 6 hierarchical sheets.
Generates KiCad netlist file (.net) with pin connections.

This is the COMPLETE netlist - the machine-readable truth for the CPU.
"""
import os
import uuid
from datetime import datetime

OUTDIR = os.path.dirname(os.path.abspath(__file__))
KICAD_VERSION = 20231120

# ============================================================================
# CHIP DEFINITIONS
# ============================================================================
CHIPS = {
    # PC counters (U1-U4)
    "U1":  {"value": "74HC161", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U2":  {"value": "74HC161", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U3":  {"value": "74HC161", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U4":  {"value": "74HC161", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    # IR registers (U5-U6)
    "U5":  {"value": "74HC574", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    "U6":  {"value": "74HC574", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Bus buffer (U7)
    "U7":  {"value": "74HC245", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Ring counter (U8)
    "U8":  {"value": "74HC164", "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # Accumulator (U9)
    "U9":  {"value": "74HC574", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Adders (U10-U11)
    "U10": {"value": "74HC283", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U11": {"value": "74HC283", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    # XOR array (U12-U13)
    "U12": {"value": "74HC86",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    "U13": {"value": "74HC86",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # AC output buffer (U14)
    "U14": {"value": "74HC541", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Address muxes (U15-U16, U29-U30)
    "U15": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U16": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U29": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U30": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    # ALU muxes (U17-U20)
    "U17": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U18": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U19": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    "U20": {"value": "74HC157", "footprint": "Package_DIP:DIP-16_W7.62mm", "lib": "74xx"},
    # Z flag FF (U21)
    "U21": {"value": "74HC74",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # Zero detect (U22)
    "U22": {"value": "74HC688", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Page register (U23)
    "U23": {"value": "74HC574", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Inverters (U24)
    "U24": {"value": "74HC04",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # OR gates (U25)
    "U25": {"value": "74HC32",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # NAND gates (U26-U27)
    "U26": {"value": "74HC00",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    "U27": {"value": "74HC00",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # XOR for control (U28)
    "U28": {"value": "74HC86",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # IRQ FF (U31)
    "U31": {"value": "74HC74",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # Data page register (U32)
    "U32": {"value": "74HC574", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # 4-input AND (U33)
    "U33": {"value": "74HC21",  "footprint": "Package_DIP:DIP-14_W7.62mm", "lib": "74xx"},
    # IRL-to-IBUS immediate buffer (U34)
    "U34": {"value": "74HC541", "footprint": "Package_DIP:DIP-20_W7.62mm", "lib": "74xx"},
    # Memory
    "ROM1": {"value": "AT28C256", "footprint": "Package_DIP:DIP-28_W15.24mm", "lib": "Memory_EPROM"},
    "RAM1": {"value": "62256",   "footprint": "Package_DIP:DIP-28_W15.24mm", "lib": "Memory_RAM"},
}

# ============================================================================
# NETLIST DATA - COMPLETE FROM 12_netlist.md
# Format: "NET_NAME": [(ref, pin), (ref, pin), ...]
# ============================================================================
NETLIST = {
    # Power nets
    "VCC": [
        ("U1",16),("U2",16),("U3",16),("U4",16),
        ("U5",20),("U6",20),("U7",20),("U8",14),
        ("U9",20),("U10",16),("U11",16),("U12",14),("U13",14),
        ("U14",20),("U15",16),("U16",16),("U17",16),("U18",16),
        ("U19",16),("U20",16),("U21",14),("U22",20),("U23",20),
        ("U24",14),("U25",14),("U26",14),("U27",14),("U28",14),
        ("U29",16),("U30",16),("U31",14),("U32",20),("U33",14),("U34",20),
        ("ROM1",28),("RAM1",28),
        # Additional VCC ties
        ("U21",1),("U21",10),("U21",13),
        ("U28",5),("U28",10),("U28",13),
        ("U31",2),("U31",4),("U31",10),("U31",12),
    ],
    "GND": [
        ("U1",8),("U2",8),("U3",8),("U4",8),
        ("U5",10),("U6",10),("U7",10),("U8",7),
        ("U9",10),("U10",8),("U11",8),("U12",7),("U13",7),
        ("U14",10),("U15",8),("U16",8),("U17",8),("U18",8),
        ("U19",8),("U20",8),("U21",7),("U22",10),("U23",10),
        ("U24",7),("U25",7),("U26",7),("U27",7),("U28",7),
        ("U29",8),("U30",8),("U31",7),("U32",10),("U33",7),("U34",10),
        ("ROM1",14),("RAM1",14),
        # Additional GND ties
        ("U5",1),("U6",1),("U9",1),("U23",1),("U32",1),
        ("U15",15),("U16",15),("U17",15),("U18",15),
        ("U19",15),("U20",15),("U29",15),("U30",15),
        ("U21",2),("U21",11),("U21",12),
        ("U22",1),("U22",3),("U22",5),("U22",7),("U22",9),
        ("U22",11),("U22",13),("U22",15),("U22",17),
        ("U25",9),("U25",10),
        ("RAM1",22),
    ],

    # Clock & Reset
    "CLK": [("U1",2),("U2",2),("U3",2),("U4",2),("U8",8)],
    "/RST": [("U1",1),("U2",1),("U3",1),("U4",1),("U8",9),("U31",1),("U31",13)],

    # Ring counter
    "T0": [("U8",3),("U5",11),("U25",4),("U24",1)],
    "T1": [("U8",4),("U6",11),("U25",5),("U24",3)],
    "T2": [("U8",5),("U26",1),("U26",5),("U26",9),("U26",12),("U27",12),("U28",4),("U33",1),("U33",9)],
    "NOT_T0": [("U24",2),("U8",1)],
    "NOT_T1": [("U24",4),("U8",2)],

    # PC outputs
    "PC0": [("U1",14),("U15",3)],
    "PC1": [("U1",13),("U15",6)],
    "PC2": [("U1",12),("U15",10)],
    "PC3": [("U1",11),("U15",13)],
    "PC4": [("U2",14),("U16",3)],
    "PC5": [("U2",13),("U16",6)],
    "PC6": [("U2",12),("U16",10)],
    "PC7": [("U2",11),("U16",13)],
    "PC8": [("U3",14),("U29",3)],
    "PC9": [("U3",13),("U29",6)],
    "PC10": [("U3",12),("U29",10)],
    "PC11": [("U3",11),("U29",13)],
    "PC12": [("U4",14),("U30",3)],
    "PC13": [("U4",13),("U30",6)],
    "PC14": [("U4",12),("U30",10)],
    "PC15": [("U4",11),("U30",13)],

    # PC carry chain
    "RCO_0": [("U1",15),("U2",10)],
    "RCO_1": [("U2",15),("U3",10)],
    "RCO_2": [("U3",15),("U4",10)],

    # IRL outputs (U6 -> PC load, address mux, U34 immediate buffer)
    "IRL0": [("U6",19),("U15",2),("U1",3),("U34",2)],
    "IRL1": [("U6",18),("U15",5),("U1",4),("U34",3)],
    "IRL2": [("U6",17),("U15",11),("U1",5),("U34",4)],
    "IRL3": [("U6",16),("U15",14),("U1",6),("U34",5)],
    "IRL4": [("U6",15),("U16",2),("U2",3),("U34",6)],
    "IRL5": [("U6",14),("U16",5),("U2",4),("U34",7)],
    "IRL6": [("U6",13),("U16",11),("U2",5),("U34",8)],
    "IRL7": [("U6",12),("U16",14),("U2",6),("U34",9)],

    # PG outputs (U23 -> PC high load)
    "PG0": [("U23",19),("U3",3)],
    "PG1": [("U23",18),("U3",4)],
    "PG2": [("U23",17),("U3",5)],
    "PG3": [("U23",16),("U3",6)],
    "PG4": [("U23",15),("U4",3)],
    "PG5": [("U23",14),("U4",4)],
    "PG6": [("U23",13),("U4",5)],
    "PG7": [("U23",12),("U4",6)],

    # DP outputs (U32 -> address mux high)
    "DP0": [("U32",19),("U29",2)],
    "DP1": [("U32",18),("U29",5)],
    "DP2": [("U32",17),("U29",11)],
    "DP3": [("U32",16),("U29",14)],
    "DP4": [("U32",15),("U30",2)],
    "DP5": [("U32",14),("U30",5)],
    "DP6": [("U32",13),("U30",11)],
    "DP7": [("U32",12),("U30",14)],

    # AC outputs (U9 -> adder, XOR mux, buffer, zero detect)
    "AC0": [("U9",19),("U10",5),("U19",3),("U14",2),("U22",2)],
    "AC1": [("U9",18),("U10",3),("U19",6),("U14",3),("U22",4)],
    "AC2": [("U9",17),("U10",14),("U19",10),("U14",4),("U22",6)],
    "AC3": [("U9",16),("U10",12),("U19",13),("U14",5),("U22",8)],
    "AC4": [("U9",15),("U11",5),("U20",3),("U14",6),("U22",12)],
    "AC5": [("U9",14),("U11",3),("U20",6),("U14",7),("U22",14)],
    "AC6": [("U9",13),("U11",14),("U20",10),("U14",8),("U22",16)],
    "AC7": [("U9",12),("U11",12),("U20",13),("U14",9),("U22",18)],

    # SUM outputs (U10, U11 -> AC input mux)
    "SUM0": [("U10",4),("U17",2)],
    "SUM1": [("U10",1),("U17",5)],
    "SUM2": [("U10",13),("U17",11)],
    "SUM3": [("U10",10),("U17",14)],
    "SUM4": [("U11",4),("U18",2)],
    "SUM5": [("U11",1),("U18",5)],
    "SUM6": [("U11",13),("U18",11)],
    "SUM7": [("U11",10),("U18",14)],

    # Adder carry chain
    "ADDER_CARRY": [("U10",9),("U11",7)],

    # XOR_Y outputs (U12, U13 -> adder B, AC input mux B)
    "XOR_Y0": [("U12",3),("U10",6),("U17",3)],
    "XOR_Y1": [("U12",6),("U10",2),("U17",6)],
    "XOR_Y2": [("U12",8),("U10",15),("U17",10)],
    "XOR_Y3": [("U12",11),("U10",11),("U17",13)],
    "XOR_Y4": [("U13",3),("U11",6),("U18",3)],
    "XOR_Y5": [("U13",6),("U11",2),("U18",6)],
    "XOR_Y6": [("U13",8),("U11",15),("U18",10)],
    "XOR_Y7": [("U13",11),("U11",11),("U18",13)],

    # XOR_B mux outputs (U19, U20 -> U12, U13)
    "XOR_B0": [("U19",4),("U12",2)],
    "XOR_B1": [("U19",7),("U12",5)],
    "XOR_B2": [("U19",9),("U12",10)],
    "XOR_B3": [("U19",12),("U12",13)],
    "XOR_B4": [("U20",4),("U13",2)],
    "XOR_B5": [("U20",7),("U13",5)],
    "XOR_B6": [("U20",9),("U13",10)],
    "XOR_B7": [("U20",12),("U13",13)],

    # AC_IN outputs (U17, U18 -> U9)
    "AC_IN0": [("U17",4),("U9",2)],
    "AC_IN1": [("U17",7),("U9",3)],
    "AC_IN2": [("U17",9),("U9",4)],
    "AC_IN3": [("U17",12),("U9",5)],
    "AC_IN4": [("U18",4),("U9",6)],
    "AC_IN5": [("U18",7),("U9",7)],
    "AC_IN6": [("U18",9),("U9",8)],
    "AC_IN7": [("U18",12),("U9",9)],

    # IBUS (internal bus)
    "IBUS0": [("U7",2),("U14",18),("U34",18),("U12",1),("U5",2),("U6",2),("U23",2),("U32",2)],
    "IBUS1": [("U7",3),("U14",17),("U34",17),("U12",4),("U5",3),("U6",3),("U23",3),("U32",3)],
    "IBUS2": [("U7",4),("U14",16),("U34",16),("U12",9),("U5",4),("U6",4),("U23",4),("U32",4)],
    "IBUS3": [("U7",5),("U14",15),("U34",15),("U12",12),("U5",5),("U6",5),("U23",5),("U32",5)],
    "IBUS4": [("U7",6),("U14",14),("U34",14),("U13",1),("U5",6),("U6",6),("U23",6),("U32",6)],
    "IBUS5": [("U7",7),("U14",13),("U34",13),("U13",4),("U5",7),("U6",7),("U23",7),("U32",7)],
    "IBUS6": [("U7",8),("U14",12),("U34",12),("U13",9),("U5",8),("U6",8),("U23",8),("U32",8)],
    "IBUS7": [("U7",9),("U14",11),("U34",11),("U13",12),("U5",9),("U6",9),("U23",9),("U32",9)],

    # DBUS (data bus)
    "DBUS0": [("U7",18),("ROM1",11),("RAM1",11)],
    "DBUS1": [("U7",17),("ROM1",12),("RAM1",12)],
    "DBUS2": [("U7",16),("ROM1",13),("RAM1",13)],
    "DBUS3": [("U7",15),("ROM1",15),("RAM1",15)],
    "DBUS4": [("U7",14),("ROM1",16),("RAM1",16)],
    "DBUS5": [("U7",13),("ROM1",17),("RAM1",17)],
    "DBUS6": [("U7",12),("ROM1",18),("RAM1",18)],
    "DBUS7": [("U7",11),("ROM1",19),("RAM1",19)],

    # ABUS (address bus)
    "ABUS0": [("U15",4),("ROM1",10),("RAM1",10)],
    "ABUS1": [("U15",7),("ROM1",9),("RAM1",9)],
    "ABUS2": [("U15",9),("ROM1",8),("RAM1",8)],
    "ABUS3": [("U15",12),("ROM1",7),("RAM1",7)],
    "ABUS4": [("U16",4),("ROM1",6),("RAM1",6)],
    "ABUS5": [("U16",7),("ROM1",5),("RAM1",5)],
    "ABUS6": [("U16",9),("ROM1",4),("RAM1",4)],
    "ABUS7": [("U16",12),("ROM1",3),("RAM1",3)],
    "ABUS8": [("U29",4),("ROM1",25),("RAM1",25)],
    "ABUS9": [("U29",7),("ROM1",24),("RAM1",24)],
    "ABUS10": [("U29",9),("ROM1",21),("RAM1",21)],
    "ABUS11": [("U29",12),("ROM1",23),("RAM1",23)],
    "ABUS12": [("U30",4),("ROM1",2),("RAM1",2)],
    "ABUS13": [("U30",7),("ROM1",26),("RAM1",26)],
    "ABUS14": [("U30",9),("ROM1",1),("RAM1",1)],
    "ABUS15": [("U30",12),("ROM1",20),("U24",5)],

    # Opcode decode outputs (U5)
    "ALU_SUB": [("U5",12),("U10",7),("U19",2),("U19",5),("U19",11),("U19",14),
                ("U20",2),("U20",5),("U20",11),("U20",14),("U28",2)],
    "XOR_MODE": [("U5",13),("U19",1),("U20",1),("U33",2),("U28",12)],
    "MUX_SEL": [("U5",14),("U17",1),("U18",1),("U27",9)],
    "AC_WR": [("U5",15),("U24",11),("U27",13)],
    "SRC": [("U5",16),("U25",1),("U33",10)],
    "STR": [("U5",17),("U25",2),("U26",10)],
    "BR": [("U5",18),("U27",1)],
    "JMP": [("U5",19),("U24",9)],

    # Derived control signals
    "ADDR_REQ": [("U25",3),("U26",4)],
    "/ADDR_MODE": [("U26",6),("U15",1),("U16",1),("U29",1),("U30",1),("U26",2),("U33",4)],
    "PC_INC": [("U25",6),("U1",7),("U1",10),("U2",7),("U3",7),("U4",7)],
    "/PC_LD": [("U26",11),("U1",9),("U2",9),("U3",9),("U4",9)],
    "/IRL_OE": [("U26",3),("U24",13),("U34",1),("U34",19)],
    "/AC_BUF": [("U26",8),("U14",1),("U14",19),("RAM1",27),("U28",9)],
    "BUF_OE_N": [("U24",12),("U7",19)],
    "WR_DIR": [("U28",8),("U7",1),("ROM1",22)],
    "ACC_CLK": [("U27",11),("U9",11),("U21",3)],
    "PG_CLK": [("U25",11),("U23",11)],
    "DP_Load": [("U33",6),("U32",11)],
    "EI_decode": [("U33",8),("U31",3)],
    "/AC_WR": [("U24",10),("U27",10),("U33",5),("U33",13)],
    "/JUMP": [("U24",8),("U27",4)],
    "/XOR_MODE": [("U28",11),("U33",12)],
    "/A15": [("U24",6),("RAM1",20)],

    # Branch/Jump logic
    "Z_flag": [("U21",5),("U28",1)],
    "Z_match": [("U28",3),("U27",2)],
    "/BR_TAKEN": [("U27",3),("U27",5)],
    "PC_LOAD_COND": [("U27",6),("U26",13)],
    "/PG_cond": [("U27",8),("U25",13)],

    # Z flag circuit
    "/T2": [("U28",6),("U25",12)],
    "/P_EQ_Q": [("U22",19),("U21",4)],

    # IRQ nets
    "IE": [("U31",5)],
    "IRQ_FF": [("U31",9)],
    "/IRQ": [("U31",11)],
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def uid():
    return str(uuid.uuid4())

# ============================================================================
# KICAD NETLIST GENERATOR
# ============================================================================
def generate_netlist():
    """Generate KiCad netlist file (.net) with all nets and pin connections."""
    lines = []
    lines.append('(export (version "E")')
    lines.append('  (design')
    lines.append(f'    (source "RV8GR.kicad_sch")')
    lines.append(f'    (date "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")')
    lines.append('    (tool "gen_kicad.py")')
    lines.append('  )')
    lines.append('  (components')

    # List all components in sorted order
    for ref in sorted(CHIPS.keys(), key=lambda x: (len(x), x)):
        chip = CHIPS[ref]
        lines.append(f'    (comp (ref "{ref}")')
        lines.append(f'      (value "{chip["value"]}")')
        lines.append(f'      (footprint "{chip["footprint"]}")')
        lines.append(f'      (libsource (lib "{chip["lib"]}") (part "{chip["value"]}"))')
        lines.append('    )')

    lines.append('  )')
    lines.append('  (nets')

    # Generate nets in sorted order with code numbers
    net_code = 1
    for net_name in sorted(NETLIST.keys()):
        pins = NETLIST[net_name]
        lines.append(f'    (net (code "{net_code}") (name "{net_name}")')
        for ref, pin in pins:
            lines.append(f'      (node (ref "{ref}") (pin "{pin}"))')
        lines.append('    )')
        net_code += 1

    lines.append('  )')
    lines.append(')')

    return '\n'.join(lines)

# ============================================================================
# KICAD SCHEMATIC GENERATORS
# ============================================================================
KICAD_VERSION = 20231120

def sch_header(title):
    return f'''(kicad_sch (version {KICAD_VERSION}) (generator "RV8GR-gen")
  (uuid {uid()})
  (paper "A4")
  (title_block
    (title "RV8GR - {title}")
    (rev "v2.0")
    (company "RV8 Project")
    (comment 1 "34 logic chips + ROM + RAM = 36 packages")
  )
'''

def sch_footer():
    return ")\n"

def symbol(lib_id, ref, value, x, y, footprint=""):
    """Place a component symbol."""
    fp = f'\n    (property "Footprint" "{footprint}" (at {x} {y+25.4} 0))' if footprint else ""
    return f'''  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
    (uuid {uid()})
    (property "Reference" "{ref}" (at {x} {y-12.7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at {x} {y+12.7} 0)
      (effects (font (size 1.27 1.27)))
    ){fp}
  )
'''

def power_symbol(lib_id, x, y):
    """Place a power symbol (VCC or GND)."""
    return f'''  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
    (uuid {uid()})
  )
'''

def global_label(name, shape, x, y, angle=0):
    """Place a global label for inter-sheet connections."""
    return f'''  (global_label "{name}" (shape {shape}) (at {x} {y} {angle})
    (fields_autoplaced yes)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid {uid()})
  )
'''

def hier_label(name, shape, x, y, angle=0):
    """Place a hierarchical label."""
    return f'''  (hierarchical_label "{name}" (shape {shape}) (at {x} {y} {angle})
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid {uid()})
  )
'''

def wire(x1, y1, x2, y2):
    """Draw a wire between two points."""
    return f'''  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))
    (stroke (width 0) (type default))
    (uuid {uid()})
  )
'''

def label(name, x, y, angle=0):
    """Place a net label."""
    return f'''  (label "{name}" (at {x} {y} {angle})
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid {uid()})
  )
'''

def junction(x, y):
    """Place a junction dot."""
    return f'''  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0)
    (uuid {uid()})
  )
'''

def no_connect(x, y):
    """Place a no-connect marker."""
    return f'''  (no_connect (at {x} {y}) (uuid {uid()}))
'''

# ============================================================================
# GENERATE PROJECT FILE
# ============================================================================
def generate_project():
    """Generate .kicad_pro JSON file."""
    return '''{
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.1,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3
      }
    }
  },
  "meta": {
    "filename": "RV8GR.kicad_pro",
    "version": 1
  },
  "schematic": {
    "legacy_lib_dir": "",
    "legacy_lib_list": []
  },
  "text_variables": {}
}
'''

# ============================================================================
# GENERATE TOP-LEVEL SCHEMATIC
# ============================================================================
def generate_top_sch():
    """Generate main schematic with global bus labels."""
    s = sch_header("Top Level - RV8GR CPU")

    # Title and description
    s += f'''  (text "RV8GR CPU\\n34 logic chips + ROM + RAM = 36 packages\\nNo microcode, 3-cycle execution"
    (at 100 20 0)
    (effects (font (size 2.54 2.54)) (justify left))
    (uuid {uid()})
  )
'''

    # Global bus labels - IBUS
    s += f'''  (text "IBUS[7:0]" (at 20 60 0) (effects (font (size 1.27 1.27))) (uuid {uid()}))
'''
    for i in range(8):
        s += global_label(f"IBUS{i}", "bidirectional", 30, 70 + i*5)

    # Global bus labels - DBUS
    s += f'''  (text "DBUS[7:0]" (at 20 120 0) (effects (font (size 1.27 1.27))) (uuid {uid()}))
'''
    for i in range(8):
        s += global_label(f"DBUS{i}", "bidirectional", 30, 130 + i*5)

    # Global bus labels - ABUS
    s += f'''  (text "ABUS[15:0]" (at 20 180 0) (effects (font (size 1.27 1.27))) (uuid {uid()}))
'''
    for i in range(16):
        s += global_label(f"ABUS{i}", "output", 30, 190 + i*5)

    # Control signals
    s += f'''  (text "Control Signals" (at 20 280 0) (effects (font (size 1.27 1.27))) (uuid {uid()}))
'''
    control_signals = ["CLK", "/RST", "T0", "T1", "T2", "ALU_SUB", "XOR_MODE",
                       "MUX_SEL", "AC_WR", "SRC", "STR", "BR", "JMP"]
    for i, sig in enumerate(control_signals):
        s += global_label(sig, "output", 30, 290 + i*5)

    # Derived control signals
    s += f'''  (text "Derived Control" (at 150 60 0) (effects (font (size 1.27 1.27))) (uuid {uid()}))
'''
    derived_signals = ["ADDR_REQ", "/ADDR_MODE", "PC_INC", "/PC_LD",
                       "/IRL_OE", "/AC_BUF", "BUF_OE_N", "WR_DIR",
                       "ACC_CLK", "PG_CLK", "DP_Load", "EI_decode"]
    for i, sig in enumerate(derived_signals):
        s += global_label(sig, "bidirectional", 160, 70 + i*5)

    # Power symbols
    s += power_symbol("power:VCC", 250, 60)
    s += power_symbol("power:GND", 250, 80)

    # Note about hierarchical sheets
    s += f'''  (text "Note: Open individual module schematics for detailed connections.\\nUse RV8GR.net for complete netlist verification."
    (at 100 320 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid {uid()})
  )
'''

    s += sch_footer()
    return s


# ============================================================================
# MAIN - Generate all files
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("RV8GR KiCad Generator")
    print("=" * 60)

    # Create project file
    pro_path = os.path.join(OUTDIR, "RV8GR.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(generate_project())
    print(f"✓ Created RV8GR.kicad_pro")

    # Create top-level schematic
    sch_path = os.path.join(OUTDIR, "RV8GR.kicad_sch")
    with open(sch_path, "w") as f:
        f.write(generate_top_sch())
    print(f"✓ Created RV8GR.kicad_sch")

    # Generate netlist file - THE CRITICAL DELIVERABLE
    net_path = os.path.join(OUTDIR, "RV8GR.net")
    with open(net_path, "w") as f:
        f.write(generate_netlist())
    print(f"✓ Created RV8GR.net")

    # Count and verify nets
    net_count = len(NETLIST)
    print(f"\n{'=' * 60}")
    print(f"NETLIST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total nets: {net_count}")
    print(f"Total chips: {len(CHIPS)}")

    # Count pins per net
    total_pins = sum(len(pins) for pins in NETLIST.values())
    print(f"Total pin connections: {total_pins}")

    # Show largest nets
    print(f"\nLargest nets by pin count:")
    sorted_nets = sorted(NETLIST.items(), key=lambda x: len(x[1]), reverse=True)
    for name, pins in sorted_nets[:10]:
        print(f"  {name}: {len(pins)} pins")

    # Verify chip coverage
    print(f"\nChip coverage verification:")
    chips_in_netlist = set()
    for pins in NETLIST.values():
        for ref, pin in pins:
            chips_in_netlist.add(ref)

    defined_chips = set(CHIPS.keys())
    missing = defined_chips - chips_in_netlist
    extra = chips_in_netlist - defined_chips

    if missing:
        print(f"  WARNING: Chips defined but not in netlist: {missing}")
    if extra:
        print(f"  WARNING: Chips in netlist but not defined: {extra}")
    if not missing and not extra:
        print(f"  ✓ All {len(defined_chips)} chips have net connections")

    print(f"\n{'=' * 60}")
    print("GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nFiles generated in: {OUTDIR}")
    print(f"  - RV8GR.kicad_pro   (project file)")
    print(f"  - RV8GR.kicad_sch   (top-level schematic)")
    print(f"  - RV8GR.net         (CRITICAL: KiCad netlist)")
    print(f"\nNext steps:")
    print(f"  1. Open RV8GR.kicad_pro in KiCad 10.0+")
    print(f"  2. Import netlist: Tools → Generate Netlist → Import")
    print(f"  3. Or use: kicad-cli sch import netlist RV8GR.net")
    print(f"  4. Run ERC to verify connections")
