"""
Lab 01: Ring Counter — U8 (74HC164) + U24 gates 1,2 (inverters)

Wiring:
  U24-1 (1A) ← U8-3 (Q0)    → U24-2 (1Y) → U8-1 (A)
  U24-3 (2A) ← U8-4 (Q1)    → U24-4 (2Y) → U8-2 (B)
  U8-8 (CLK) ← CLK (external)
  U8-9 (/CLR) ← /RST (external)

Expected: T0→T1→T2→T0... one-hot ring counter

Test Vector (clock-by-clock):
  /RST=0 → all Q=0
  /RST=1, clock edges → T0,T1,T2 cycle
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc164, TTL_74hc04

# Create chips
U8 = TTL_74hc164('U8')
U24 = TTL_74hc04('U24')

# Wire: U8 Q0 → U24 inv1 → U8 A, U8 Q1 → U24 inv2 → U8 B
def propagate():
    """Wire signals between chips."""
    U24.set(1, U8.get(3))   # U24 1A ← U8 Q0
    U24.set(3, U8.get(4))   # U24 2A ← U8 Q1
    U24.update()
    U8.set(1, U24.get(2))   # U8 A ← U24 1Y (NOT Q0)
    U8.set(2, U24.get(4))   # U8 B ← U24 2Y (NOT Q1)

# Test sequence: (/RST, expected_T0, expected_T1, expected_T2)
TEST_SEQUENCE = [
    # /RST, → T0(Q0), T1(Q1), T2(Q2)
    (0,   0, 0, 0),    # clear
    (1,   1, 0, 0),    # first clock: T0
    (1,   0, 1, 0),    # T1
    (1,   0, 0, 1),    # T2
    (1,   1, 0, 0),    # T0 again (wrap)
    (1,   0, 1, 0),    # T1
    (1,   0, 0, 1),    # T2
]

if __name__ == '__main__':
    print("Lab 01: Ring Counter (U8 + U24)")
    print("-" * 40)

    for i, (rst, exp_t0, exp_t1, exp_t2) in enumerate(TEST_SEQUENCE):
        U8.set(9, rst)   # /CLR
        propagate()
        U8.clock_edge()
        propagate()

        t0, t1, t2 = U8.get(3), U8.get(4), U8.get(5)
        status = "✅" if (t0, t1, t2) == (exp_t0, exp_t1, exp_t2) else "❌"
        print(f"  CLK{i}: /RST={rst} → T0={t0} T1={t1} T2={t2}  {status}")
        assert (t0, t1, t2) == (exp_t0, exp_t1, exp_t2), \
            f"Expected ({exp_t0},{exp_t1},{exp_t2})"

    print("\n✅ Lab 01 PASS: Ring counter cycles T0→T1→T2→T0")
