"""
Lab 09: Full Fetch — All modules together fetch 'LI $42' from ROM

Uses: Ring counter + PC + Address Mux + ROM + U7 + IR latch

Sequence:
  T0: PC→Mux→ROM→U7→IBUS→U5 latches $30 (LI opcode), PC+1
  T1: PC→Mux→ROM→U7→IBUS→U6 latches $42 (operand), PC+1
"""
import sys; sys.path.insert(0, '..')
from chips import (TTL_74hc164, TTL_74hc04, TTL_74hc161,
                   TTL_74hc157, MEM_AT28C256, TTL_74hc245, TTL_74hc574)

# Create chips
U8 = TTL_74hc164('U8'); U24 = TTL_74hc04('U24')
U1 = TTL_74hc161('U1'); U2 = TTL_74hc161('U2')
U15 = TTL_74hc157('U15'); U16 = TTL_74hc157('U16')
ROM = MEM_AT28C256('ROM'); U7 = TTL_74hc245('U7')
U5 = TTL_74hc574('U5'); U6 = TTL_74hc574('U6')

# Load ROM: LI $42 at $8000
ROM._data[0x0000] = 0x30  # $8000: LI
ROM._data[0x0001] = 0x42  # $8001: $42

# Init: PC=$8000 → U1=0, U2=0 (low byte), high byte has A15=1
U1._count = 0; U2._count = 0
U5.set(1, 0); U6.set(1, 0)  # /OE=0
U15.set(15, 0); U16.set(15, 0)  # /E=0
U15.set(1, 0); U16.set(1, 0)  # SEL=0 (PC mode)
U7.set(1, 0); U7.set(19, 0)  # DIR=0(A→B), /OE=0

def propagate_and_clock():
    """Full cycle: read state → clock edge → advance."""
    # Ring counter feedback
    U24.set(1, U8.get(3)); U24.set(3, U8.get(4)); U24.update()
    U8.set(1, U24.get(2)); U8.set(2, U24.get(4))

    t0 = U8.get(3); t1 = U8.get(4)

    # PC → Mux → ROM → U7 → IBUS (propagate current address)
    U1.update(); U2.set(10, U1.get(15)); U2.update()
    U15.set(2, U1.get(14)); U15.set(5, U1.get(13))
    U15.set(11, U1.get(12)); U15.set(14, U1.get(11))
    U16.set(2, U2.get(14)); U16.set(5, U2.get(13))
    U16.set(11, U2.get(12)); U16.set(14, U2.get(11))
    U15.update(); U16.update()

    addr = (U15.get(4) | (U15.get(7)<<1) | (U15.get(9)<<2) | (U15.get(12)<<3) |
            (U16.get(4)<<4) | (U16.get(7)<<5) | (U16.get(9)<<6) | (U16.get(12)<<7))
    for i in range(8): ROM.set(i+1, (addr>>i)&1)
    for i in range(8, 15): ROM.set(i+1, 0)
    ROM.set(24, 0); ROM.set(25, 0)
    ROM.update()

    for i in range(8): U7.set(2+i, ROM.get(16+i))
    U7.update()

    for i in range(8):
        ibus_bit = U7.get(18-i)
        U5.set(2+i, ibus_bit)
        U6.set(2+i, ibus_bit)

    # Latch IR on appropriate phase edge
    if t0: U5.clock_edge(); U5.update()
    if t1: U6.clock_edge(); U6.update()

    # PC increment (happens at same clock edge)
    pc_inc = t0 | t1
    U1.set(1, 1); U1.set(7, pc_inc); U1.set(9, 1); U1.set(10, pc_inc)
    U2.set(1, 1); U2.set(7, pc_inc); U2.set(9, 1); U2.set(10, U1.get(15))
    if pc_inc:
        U1.clock_edge(); U2.set(10, U1.get(15)); U2.clock_edge()

    # Advance ring counter
    U8.clock_edge()

def read_ir_high():
    return sum(U5.get(19-i)<<i for i in range(8))

def read_ir_low():
    return sum(U6.get(19-i)<<i for i in range(8))

def read_pc():
    return U1._count | (U2._count << 4)


if __name__ == '__main__':
    print("Lab 09: Full Fetch (LI $42 from ROM)")
    print("-" * 40)

    # Reset ring counter
    U8.set(9, 0); U8.clock_edge(); U8.set(9, 1)

    # Clock 1: should be T0 → fetch control byte
    propagate_and_clock()
    print(f"  CLK1: T0={U8.get(3)} T1={U8.get(4)} T2={U8.get(5)} PC={read_pc()} IR_H=${read_ir_high():02X}")

    # Clock 2: should be T1 → fetch operand
    propagate_and_clock()
    print(f"  CLK2: T0={U8.get(3)} T1={U8.get(4)} T2={U8.get(5)} PC={read_pc()} IR_L=${read_ir_low():02X}")

    # Clock 3: T2 → execute (we just verify fetch was correct)
    propagate_and_clock()
    print(f"  CLK3: T0={U8.get(3)} T1={U8.get(4)} T2={U8.get(5)}")

    ir_h = read_ir_high()
    ir_l = read_ir_low()
    print(f"\n  Result: IR_HIGH=${ir_h:02X} IR_LOW=${ir_l:02X}")
    assert ir_h == 0x30, f"IR_HIGH=${ir_h:02X}, expected $30"
    assert ir_l == 0x42, f"IR_LOW=${ir_l:02X}, expected $42"
    print("\n✅ Lab 09 PASS: Fetched LI $42 from ROM correctly")
