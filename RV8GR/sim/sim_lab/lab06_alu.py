"""
Lab 06: ALU — U12-U13 (XOR), U10-U11 (Adder), U19-U20 (XOR B-mux)

Wiring:
  U19/U20 SEL ← XOR_MODE,  A ← ALU_SUB,  B ← AC[7:0]
  U12/U13 A ← IBUS,  B ← U19/U20 Y
  U10/U11 A ← AC,  B ← U12/U13 Y,  U10 Cin ← ALU_SUB,  U11 Cin ← U10 Cout

Test: ADD, SUB, XOR operations
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc86, TTL_74hc283, TTL_74hc157

U19 = TTL_74hc157('U19'); U20 = TTL_74hc157('U20')  # XOR B-mux
U12 = TTL_74hc86('U12');  U13 = TTL_74hc86('U13')   # XOR array
U10 = TTL_74hc283('U10'); U11 = TTL_74hc283('U11')  # Adder

def alu_compute(ac, ibus, sub, xor_mode):
    """Wire and compute ALU result."""
    # U19/U20: SEL=XOR_MODE, A=ALU_SUB(all bits same), B=AC bits
    for mux, ac_bits in [(U19, ac&0xF), (U20, (ac>>4)&0xF)]:
        mux.set(1, xor_mode); mux.set(15, 0)
        mux.set(2, sub); mux.set(5, sub); mux.set(11, sub); mux.set(14, sub)
    # U19 B: AC[3:0]
    U19.set(3,(ac>>0)&1); U19.set(6,(ac>>1)&1); U19.set(10,(ac>>2)&1); U19.set(13,(ac>>3)&1)
    # U20 B: AC[7:4]
    U20.set(3,(ac>>4)&1); U20.set(6,(ac>>5)&1); U20.set(10,(ac>>6)&1); U20.set(13,(ac>>7)&1)
    U19.update(); U20.update()

    # U12: A=IBUS[3:0], B=U19 Y
    U12.set(1,(ibus>>0)&1); U12.set(4,(ibus>>1)&1); U12.set(9,(ibus>>2)&1); U12.set(12,(ibus>>3)&1)
    U12.set(2, U19.get(4)); U12.set(5, U19.get(7)); U12.set(10, U19.get(9)); U12.set(13, U19.get(12))
    # U13: A=IBUS[7:4], B=U20 Y
    U13.set(1,(ibus>>4)&1); U13.set(4,(ibus>>5)&1); U13.set(9,(ibus>>6)&1); U13.set(12,(ibus>>7)&1)
    U13.set(2, U20.get(4)); U13.set(5, U20.get(7)); U13.set(10, U20.get(9)); U13.set(13, U20.get(12))
    U12.update(); U13.update()

    # U10: A=AC[3:0], B=XOR_Y[3:0], Cin=SUB
    U10.set(5,(ac>>0)&1); U10.set(3,(ac>>1)&1); U10.set(14,(ac>>2)&1); U10.set(12,(ac>>3)&1)
    U10.set(6, U12.get(3)); U10.set(2, U12.get(6)); U10.set(15, U12.get(8)); U10.set(11, U12.get(11))
    U10.set(7, sub)
    U10.update()

    # U11: A=AC[7:4], B=XOR_Y[7:4], Cin=U10.Cout
    U11.set(5,(ac>>4)&1); U11.set(3,(ac>>5)&1); U11.set(14,(ac>>6)&1); U11.set(12,(ac>>7)&1)
    U11.set(6, U13.get(3)); U11.set(2, U13.get(6)); U11.set(15, U13.get(8)); U11.set(11, U13.get(11))
    U11.set(7, U10.get(9))
    U11.update()

    # Read adder SUM
    adder_sum = (U10.get(4) | (U10.get(1)<<1) | (U10.get(13)<<2) | (U10.get(10)<<3) |
                 (U11.get(4)<<4) | (U11.get(1)<<5) | (U11.get(13)<<6) | (U11.get(10)<<7))
    # Read XOR output
    xor_out = (U12.get(3) | (U12.get(6)<<1) | (U12.get(8)<<2) | (U12.get(11)<<3) |
               (U13.get(3)<<4) | (U13.get(6)<<5) | (U13.get(8)<<6) | (U13.get(11)<<7))

    return adder_sum, xor_out

# Test: (AC, IBUS, SUB, XOR_MODE, MUX_SEL, expected_result)
# MUX_SEL: 0=adder, 1=xor_output
TEST_VECTORS = [
    # ADD: SUB=0, XOR=0, MUX=0 → AC + IBUS
    (0x10, 0x05, 0, 0, 0, 0x15),
    (0xFF, 0x01, 0, 0, 0, 0x00),  # overflow
    # SUB: SUB=1, XOR=0, MUX=0 → AC - IBUS
    (0x10, 0x05, 1, 0, 0, 0x0B),
    (0x00, 0x01, 1, 0, 0, 0xFF),  # underflow
    # LI: SUB=0, XOR=0, MUX=1 → IBUS passthrough (XOR out = IBUS^0 = IBUS)
    (0x00, 0x42, 0, 0, 1, 0x42),
    # XOR: SUB=0, XOR=1, MUX=1 → AC ^ IBUS
    (0xFF, 0x55, 0, 1, 1, 0xAA),
    (0xAA, 0x55, 0, 1, 1, 0xFF),
]

if __name__ == '__main__':
    print("Lab 06: ALU (U10-U13, U19-U20)")
    print("-" * 40)

    for i, (ac, ibus, sub, xor_mode, mux_sel, exp) in enumerate(TEST_VECTORS):
        adder_sum, xor_out = alu_compute(ac, ibus, sub, xor_mode)
        result = xor_out if mux_sel else adder_sum
        status = "✅" if result == exp else "❌"
        op = ['ADD','SUB','LI','XOR'][[0,1,0,1][sub*2+xor_mode]]
        print(f"  {i}: AC=${ac:02X} {op} ${ibus:02X} → ${result:02X}  {status}")
        assert result == exp, f"Expected ${exp:02X}, got ${result:02X}"

    print("\n✅ Lab 06 PASS: ALU computes ADD/SUB/XOR/LI correctly")
