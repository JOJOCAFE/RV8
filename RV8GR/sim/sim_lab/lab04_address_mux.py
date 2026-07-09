"""
Lab 04: Address Mux — U15-U16 (74HC157 ×2)

Wiring:
  SEL (pin 1) ← ADDR_MODE (0=PC, 1=IRL)
  /E (pin 15) ← GND
  A inputs ← PC[7:0]
  B inputs ← IRL[7:0]
  Y outputs → ABUS A[7:0]

Test: switch between PC and IRL addresses
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc157

U15 = TTL_74hc157('U15')  # A0-A3
U16 = TTL_74hc157('U16')  # A4-A7

def set_pc_lo(val):
    """Set PC[7:0] on A-inputs."""
    # U15: 1A=pin2, 2A=pin5, 3A=pin11, 4A=pin14 → PC0-PC3
    U15.set(2,(val>>0)&1); U15.set(5,(val>>1)&1); U15.set(11,(val>>2)&1); U15.set(14,(val>>3)&1)
    # U16: 1A=pin2, 2A=pin5, 3A=pin11, 4A=pin14 → PC4-PC7
    U16.set(2,(val>>4)&1); U16.set(5,(val>>5)&1); U16.set(11,(val>>6)&1); U16.set(14,(val>>7)&1)

def set_irl(val):
    """Set IRL[7:0] on B-inputs."""
    U15.set(3,(val>>0)&1); U15.set(6,(val>>1)&1); U15.set(10,(val>>2)&1); U15.set(13,(val>>3)&1)
    U16.set(3,(val>>4)&1); U16.set(6,(val>>5)&1); U16.set(10,(val>>6)&1); U16.set(13,(val>>7)&1)

def read_abus_lo():
    """Read ABUS A[7:0] from Y outputs."""
    return (U15.get(4) | (U15.get(7)<<1) | (U15.get(9)<<2) | (U15.get(12)<<3) |
            (U16.get(4)<<4) | (U16.get(7)<<5) | (U16.get(9)<<6) | (U16.get(12)<<7))

# Test: (ADDR_MODE, PC_val, IRL_val, expected_ABUS)
TEST_VECTORS = [
    (0, 0x00, 0xFF, 0x00),   # SEL=0 → PC
    (0, 0x42, 0xFF, 0x42),   # SEL=0 → PC
    (1, 0x42, 0x10, 0x10),   # SEL=1 → IRL
    (1, 0x00, 0xAB, 0xAB),   # SEL=1 → IRL
    (0, 0x80, 0x00, 0x80),   # back to PC
]

if __name__ == '__main__':
    print("Lab 04: Address Mux (U15-U16)")
    print("-" * 40)

    U15.set(15, 0); U16.set(15, 0)  # /E=GND

    for i, (sel, pc, irl, exp) in enumerate(TEST_VECTORS):
        U15.set(1, sel); U16.set(1, sel)
        set_pc_lo(pc); set_irl(irl)
        U15.update(); U16.update()
        abus = read_abus_lo()
        status = "✅" if abus == exp else "❌"
        print(f"  {i}: SEL={sel} PC=${pc:02X} IRL=${irl:02X} → ABUS=${abus:02X}  {status}")
        assert abus == exp

    print("\n✅ Lab 04 PASS: Address mux selects PC or IRL correctly")
