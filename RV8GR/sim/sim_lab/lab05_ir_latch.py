"""
Lab 05: IR Latch — U5 (IR_HIGH) + U6 (IR_LOW)

Wiring:
  U5 D[1:8] ← IBUS,  U5 CLK ← T0
  U6 D[1:8] ← IBUS,  U6 CLK ← T1

Test: present data on IBUS, clock T0→U5 latches, clock T1→U6 latches
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc574

U5 = TTL_74hc574('U5')  # IR_HIGH
U6 = TTL_74hc574('U6')  # IR_LOW

def set_ibus(val):
    """Set IBUS value on D inputs of both U5 and U6."""
    for i in range(8):
        U5.set(2+i, (val>>i)&1)
        U6.set(2+i, (val>>i)&1)

def read_ir_high():
    return sum(U5.get(19-i)<<i for i in range(8))

def read_ir_low():
    return sum(U6.get(19-i)<<i for i in range(8))

# Test sequence: (IBUS_val, clock_which, expected_IR_HIGH, expected_IR_LOW)
TEST_SEQUENCE = [
    # Set /OE=0 for both
    (0x30, 'U5', 0x30, 0x00),   # T0 edge: U5 latches $30
    (0x42, 'U6', 0x30, 0x42),   # T1 edge: U6 latches $42
    (0x10, 'U5', 0x10, 0x42),   # new T0: U5 latches $10
    (0x05, 'U6', 0x10, 0x05),   # new T1: U6 latches $05
]

if __name__ == '__main__':
    print("Lab 05: IR Latch (U5 + U6)")
    print("-" * 40)

    U5.set(1, 0); U6.set(1, 0)  # /OE=0

    for i, (ibus, clk_chip, exp_h, exp_l) in enumerate(TEST_SEQUENCE):
        set_ibus(ibus)
        if clk_chip == 'U5': U5.clock_edge(); U5.update()
        else: U6.clock_edge(); U6.update()

        h, l = read_ir_high(), read_ir_low()
        status = "✅" if h == exp_h and l == exp_l else "❌"
        print(f"  CLK{i}: IBUS=${ibus:02X} → {clk_chip} edge → IR_H=${h:02X} IR_L=${l:02X}  {status}")
        assert h == exp_h and l == exp_l

    print("\n✅ Lab 05 PASS: IR latches control byte and operand separately")
