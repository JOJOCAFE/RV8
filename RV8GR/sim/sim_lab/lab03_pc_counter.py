"""
Lab 03: PC Counter — U1-U4 (74HC161 ×4) cascaded

Wiring:
  U1-U4: /CLR ← /RST, ENP ← PC_INC, /LD ← /PC_LD
  U1-10 (ENT) ← PC_INC
  U2-10 (ENT) ← U1-15 (RCO)
  U3-10 (ENT) ← U2-15 (RCO)
  U4-10 (ENT) ← U3-15 (RCO)
  U1-3..6 (D) ← load value[3:0]
  U2-3..6 (D) ← load value[7:4]
  U3-3..6 (D) ← load value[11:8]
  U4-3..6 (D) ← load value[15:12]

Test: clear, count, load, count across nibble boundary
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc161

# Create 4 counters
U1 = TTL_74hc161('U1')
U2 = TTL_74hc161('U2')
U3 = TTL_74hc161('U3')
U4 = TTL_74hc161('U4')
pc_chips = [U1, U2, U3, U4]

def set_pc_control(rst, pc_inc, pc_ld):
    """Set control signals on all 4 counters."""
    for c in pc_chips:
        c.set(1, rst)       # /CLR
        c.set(7, pc_inc)    # ENP
        c.set(9, pc_ld)     # /LD
    U1.set(10, pc_inc)      # ENT (U1 gets PC_INC directly)

def wire_cascade():
    """Wire RCO cascade: U1→U2→U3→U4."""
    U2.set(10, U1.get(15))
    U3.set(10, U2.get(15))
    U4.set(10, U3.get(15))

def load_value(val):
    """Set D inputs for parallel load."""
    for i, c in enumerate(pc_chips):
        nibble = (val >> (i*4)) & 0xF
        c.set(3, (nibble>>0)&1); c.set(4, (nibble>>1)&1)
        c.set(5, (nibble>>2)&1); c.set(6, (nibble>>3)&1)

def read_pc():
    """Read 16-bit PC value."""
    val = 0
    for i, c in enumerate(pc_chips):
        val |= c._count << (i*4)
    return val

def step():
    """Clock all counters (cascade must be set before edge)."""
    # Update cascade (combinational) - RCO available before clock edge
    U1.update(); U2.set(10, U1.get(15))
    U2.update(); U3.set(10, U2.get(15))
    U3.update(); U4.set(10, U3.get(15))
    # Clock all simultaneously
    for c in pc_chips: c.clock_edge()

# Test: (/RST, PC_INC, /PC_LD, load_val, expected_PC)
TEST_SEQUENCE = [
    (0, 0, 1, 0x0000,  0x0000),    # clear
    (1, 1, 1, 0x0000,  0x0001),    # count +1
    (1, 1, 1, 0x0000,  0x0002),    # count +1
    (1, 1, 1, 0x0000,  0x0003),    # count +1
    (1, 0, 1, 0x0000,  0x0003),    # hold (PC_INC=0)
    (1, 1, 0, 0x8000,  0x8000),    # load $8000
    (1, 1, 1, 0x0000,  0x8001),    # count from $8000
    (1, 1, 1, 0x0000,  0x8002),    # count
    (1, 1, 0, 0xFFFF,  0xFFFF),    # load $FFFF
    (1, 1, 1, 0x0000,  0x0000),    # overflow → $0000
]

if __name__ == '__main__':
    print("Lab 03: PC Counter (U1-U4, 16-bit)")
    print("-" * 40)

    for i, (rst, inc, ld, load, exp) in enumerate(TEST_SEQUENCE):
        set_pc_control(rst, inc, ld)
        load_value(load)
        step()

        pc = read_pc()
        status = "✅" if pc == exp else "❌"
        print(f"  CLK{i}: /RST={rst} INC={inc} /LD={ld} D=${load:04X} → PC=${pc:04X}  {status}")
        assert pc == exp, f"Expected ${exp:04X}, got ${pc:04X}"

    print("\n✅ Lab 03 PASS: 16-bit counter with clear/count/load/overflow")
