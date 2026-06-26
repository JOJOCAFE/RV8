"""
Lab 08: AC Mux + Latch — U17-U18 (mux) + U9 (74HC574)

Wiring:
  U17/U18 SEL ← MUX_SEL,  A ← Adder SUM,  B ← XOR output
  U17/U18 Y → U9 D
  U9 CLK ← ACC_CLK (rising edge)
  U9 /OE ← GND

Test: select adder or XOR output, latch into AC
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc157, TTL_74hc574

U17 = TTL_74hc157('U17'); U18 = TTL_74hc157('U18')
U9 = TTL_74hc574('U9')

def set_adder_sum(val):
    """Set SUM on A-inputs of U17/U18."""
    U17.set(2,(val>>0)&1); U17.set(5,(val>>1)&1); U17.set(11,(val>>2)&1); U17.set(14,(val>>3)&1)
    U18.set(2,(val>>4)&1); U18.set(5,(val>>5)&1); U18.set(11,(val>>6)&1); U18.set(14,(val>>7)&1)

def set_xor_out(val):
    """Set XOR output on B-inputs of U17/U18."""
    U17.set(3,(val>>0)&1); U17.set(6,(val>>1)&1); U17.set(10,(val>>2)&1); U17.set(13,(val>>3)&1)
    U18.set(3,(val>>4)&1); U18.set(6,(val>>5)&1); U18.set(10,(val>>6)&1); U18.set(13,(val>>7)&1)

def latch_ac(mux_sel):
    """Select mux, update, transfer to U9, latch."""
    U17.set(1, mux_sel); U17.set(15, 0)
    U18.set(1, mux_sel); U18.set(15, 0)
    U17.update(); U18.update()
    # Wire U17/U18 Y → U9 D
    U9.set(2, U17.get(4)); U9.set(3, U17.get(7)); U9.set(4, U17.get(9)); U9.set(5, U17.get(12))
    U9.set(6, U18.get(4)); U9.set(7, U18.get(7)); U9.set(8, U18.get(9)); U9.set(9, U18.get(12))
    U9.set(1, 0)  # /OE=0
    U9.clock_edge()
    return sum(U9.get(19-i)<<i for i in range(8))

# Test: (MUX_SEL, adder_val, xor_val, expected_AC)
TEST_VECTORS = [
    (0, 0x15, 0x42, 0x15),  # MUX=0 → adder
    (1, 0x15, 0x42, 0x42),  # MUX=1 → XOR output
    (0, 0xFF, 0x00, 0xFF),  # adder
    (1, 0xFF, 0xAA, 0xAA),  # XOR
]

if __name__ == '__main__':
    print("Lab 08: AC Mux + Latch (U17-U18 + U9)")
    print("-" * 40)

    for i, (sel, adder, xor, exp) in enumerate(TEST_VECTORS):
        set_adder_sum(adder); set_xor_out(xor)
        ac = latch_ac(sel)
        status = "✅" if ac == exp else "❌"
        src = "Adder" if sel == 0 else "XOR"
        print(f"  {i}: MUX={sel}({src}) Adder=${adder:02X} XOR=${xor:02X} → AC=${ac:02X}  {status}")
        assert ac == exp

    print("\n✅ Lab 08 PASS: AC mux selects and latches correctly")
