"""
Lab 07: Adder/Subtractor — U12-U13 (XOR B-invert) + U10-U11 (Adder)

Wiring (lab simplified — no B-input mux):
  U12/U13 A ← IBUS,  B ← ALU_SUB (all 8 bits same)
  U10/U11 A ← AC,  B ← U12/U13 Y,  U10 Cin ← ALU_SUB

Test: ADD and SUB with carry chain
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc86, TTL_74hc283

U12 = TTL_74hc86('U12');  U13 = TTL_74hc86('U13')   # XOR (B invert)
U10 = TTL_74hc283('U10'); U11 = TTL_74hc283('U11')  # Adder

def addsub_compute(ac, ibus, sub):
    """Lab 07: XOR B-input = ALU_SUB (same signal to all 8 XOR B pins)."""
    # U12: A=IBUS[3:0], B=ALU_SUB
    U12.set(1,(ibus>>0)&1); U12.set(4,(ibus>>1)&1); U12.set(9,(ibus>>2)&1); U12.set(12,(ibus>>3)&1)
    U12.set(2, sub); U12.set(5, sub); U12.set(10, sub); U12.set(13, sub)
    # U13: A=IBUS[7:4], B=ALU_SUB
    U13.set(1,(ibus>>4)&1); U13.set(4,(ibus>>5)&1); U13.set(9,(ibus>>6)&1); U13.set(12,(ibus>>7)&1)
    U13.set(2, sub); U13.set(5, sub); U13.set(10, sub); U13.set(13, sub)
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

    # Read result
    result = (U10.get(4) | (U10.get(1)<<1) | (U10.get(13)<<2) | (U10.get(10)<<3) |
              (U11.get(4)<<4) | (U11.get(1)<<5) | (U11.get(13)<<6) | (U11.get(10)<<7))
    cout = U11.get(9)
    return result, cout

# (AC, IBUS, SUB, expected_result, expected_cout)
TEST_VECTORS = [
    # ADD tests
    (0x03, 0x05, 0, 0x08, 0),
    (0x10, 0x20, 0, 0x30, 0),
    (0xFF, 0x01, 0, 0x00, 1),  # carry
    (0x7F, 0x01, 0, 0x80, 0),  # signed overflow
    # SUB tests
    (0x05, 0x03, 1, 0x02, 1),  # no borrow
    (0x10, 0x10, 1, 0x00, 1),  # equal
    (0x03, 0x05, 1, 0xFE, 0),  # borrow
]

if __name__ == '__main__':
    print("Lab 07: Adder/Subtractor (U10-U13)")
    print("-" * 40)

    for i, (ac, ibus, sub, exp_r, exp_c) in enumerate(TEST_VECTORS):
        result, cout = addsub_compute(ac, ibus, sub)
        ok = result == exp_r and cout == exp_c
        op = "SUB" if sub else "ADD"
        borrow = " (borrow)" if sub and not cout else ""
        print(f"  {i}: ${ac:02X} {op} ${ibus:02X} = ${result:02X} C={cout}{borrow}  {'✅' if ok else '❌'}")
        assert ok, f"Expected ${exp_r:02X} C={exp_c}, got ${result:02X} C={cout}"

    print(f"\n✅ Lab 07 PASS: Adder/Subtractor computes correctly")
