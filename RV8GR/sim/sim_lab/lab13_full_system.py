"""
Lab 13: Full System — LI $42 runs through all chips, AC=$42

Integration of all modules:
  T0: fetch $30 → IR_HIGH
  T1: fetch $42 → IR_LOW
  T2: decode LI → MUX_SEL=1, AC_WR=1 → IBUS=$42 → XOR passthrough → AC mux B → AC latch

Verifies: The entire datapath from ROM to AC works.
"""
import sys; sys.path.insert(0, '..')
from chips import (TTL_74hc164, TTL_74hc04, TTL_74hc161, TTL_74hc157,
                   MEM_AT28C256, TTL_74hc245, TTL_74hc574,
                   TTL_74hc86, TTL_74hc283, TTL_74hc00, TTL_74hc32, TTL_74hc21)

# Create all needed chips
U8 = TTL_74hc164('U8'); U24 = TTL_74hc04('U24')
U1 = TTL_74hc161('U1'); U2 = TTL_74hc161('U2')
U15 = TTL_74hc157('U15'); U16 = TTL_74hc157('U16')
ROM = MEM_AT28C256('ROM'); U7 = TTL_74hc245('U7')
U5 = TTL_74hc574('U5'); U6 = TTL_74hc574('U6')
U9 = TTL_74hc574('U9')
U12 = TTL_74hc86('U12'); U13 = TTL_74hc86('U13')
U19 = TTL_74hc157('U19'); U20 = TTL_74hc157('U20')
U10 = TTL_74hc283('U10'); U11 = TTL_74hc283('U11')
U17 = TTL_74hc157('U17'); U18 = TTL_74hc157('U18')
U26 = TTL_74hc00('U26'); U27 = TTL_74hc00('U27')

# Load ROM
ROM._data[0x0000] = 0x30; ROM._data[0x0001] = 0x42  # LI $42

# Init
for c in [U5,U6,U9]: c.set(1,0)  # /OE=0
for c in [U15,U16,U17,U18,U19,U20]: c.set(15,0)  # /E=GND
U7.set(1,0); U7.set(19,0)  # DIR=0, /OE=0
U8.set(9,0); U8.clock_edge(); U8.set(9,1)  # reset ring

def do_phase():
    """Execute one phase (T0, T1, or T2)."""
    t0,t1,t2 = U8.get(3), U8.get(4), U8.get(5)

    if t0 or t1:
        # FETCH: PC→Mux→ROM→U7→IBUS→IR
        U1.update(); U2.update()
        U15.set(1,0); U16.set(1,0)  # ADDR_MODE=0
        U15.set(2,U1.get(14)); U15.set(5,U1.get(13)); U15.set(11,U1.get(12)); U15.set(14,U1.get(11))
        U16.set(2,U2.get(14)); U16.set(5,U2.get(13)); U16.set(11,U2.get(12)); U16.set(14,U2.get(11))
        U15.update(); U16.update()

        addr = U15.get(4)|(U15.get(7)<<1)|(U15.get(9)<<2)|(U15.get(12)<<3)|(U16.get(4)<<4)|(U16.get(7)<<5)|(U16.get(9)<<6)|(U16.get(12)<<7)
        for i in range(8): ROM.set(i+1,(addr>>i)&1)
        for i in range(8,15): ROM.set(i+1,0)
        ROM.set(24,0); ROM.set(25,0); ROM.update()

        for i in range(8): U7.set(2+i,ROM.get(16+i))
        U7.update()
        ibus = sum(U7.get(18-i)<<i for i in range(8))

        for i in range(8): U5.set(2+i,(ibus>>i)&1); U6.set(2+i,(ibus>>i)&1)
        if t0: U5.clock_edge(); U5.update()
        if t1: U6.clock_edge(); U6.update()

        # PC increment
        U1.set(1,1); U1.set(7,1); U1.set(9,1); U1.set(10,1)
        U2.set(1,1); U2.set(7,1); U2.set(9,1); U2.set(10,U1.get(15))
        U1.clock_edge(); U2.set(10,U1.get(15)); U2.clock_edge()

    elif t2:
        # EXECUTE: decode + ALU + AC latch
        ir_h = sum(U5.get(19-i)<<i for i in range(8))
        ir_l = sum(U6.get(19-i)<<i for i in range(8))
        sub=(ir_h>>7)&1; xor_m=(ir_h>>6)&1; mux=(ir_h>>5)&1; ac_wr=(ir_h>>4)&1
        src=(ir_h>>3)&1; stt=(ir_h>>2)&1

        # IBUS source during T2
        if not (src|stt):  # immediate mode
            ibus = ir_l
        else:
            ibus = 0  # would be RAM, not tested here

        # ALU: XOR B-mux → XOR → Adder → AC mux
        ac = sum(U9.get(19-i)<<i for i in range(8))
        # XOR B-mux
        U19.set(1,xor_m); U20.set(1,xor_m)
        for i in range(4):
            U19.set([2,5,11,14][i], sub)
            U19.set([3,6,10,13][i], (ac>>i)&1)
            U20.set([2,5,11,14][i], sub)
            U20.set([3,6,10,13][i], (ac>>(i+4))&1)
        U19.update(); U20.update()

        # XOR gates
        for i in range(4):
            U12.set([1,4,9,12][i], (ibus>>i)&1)
            U12.set([2,5,10,13][i], U19.get([4,7,9,12][i]))
            U13.set([1,4,9,12][i], (ibus>>(i+4))&1)
            U13.set([2,5,10,13][i], U20.get([4,7,9,12][i]))
        U12.update(); U13.update()

        # Adder
        U10.set(5,(ac>>0)&1); U10.set(3,(ac>>1)&1); U10.set(14,(ac>>2)&1); U10.set(12,(ac>>3)&1)
        U10.set(6,U12.get(3)); U10.set(2,U12.get(6)); U10.set(15,U12.get(8)); U10.set(11,U12.get(11))
        U10.set(7,sub); U10.update()
        U11.set(5,(ac>>4)&1); U11.set(3,(ac>>5)&1); U11.set(14,(ac>>6)&1); U11.set(12,(ac>>7)&1)
        U11.set(6,U13.get(3)); U11.set(2,U13.get(6)); U11.set(15,U13.get(8)); U11.set(11,U13.get(11))
        U11.set(7,U10.get(9)); U11.update()

        # AC mux: SEL=MUX_SEL, A=adder, B=XOR output
        U17.set(1,mux); U18.set(1,mux)
        U17.set(2,U10.get(4)); U17.set(5,U10.get(1)); U17.set(11,U10.get(13)); U17.set(14,U10.get(10))
        U17.set(3,U12.get(3)); U17.set(6,U12.get(6)); U17.set(10,U12.get(8)); U17.set(13,U12.get(11))
        U18.set(2,U11.get(4)); U18.set(5,U11.get(1)); U18.set(11,U11.get(13)); U18.set(14,U11.get(10))
        U18.set(3,U13.get(3)); U18.set(6,U13.get(6)); U18.set(10,U13.get(8)); U18.set(13,U13.get(11))
        U17.update(); U18.update()

        # AC latch (if AC_WR)
        if ac_wr:
            U9.set(2,U17.get(4)); U9.set(3,U17.get(7)); U9.set(4,U17.get(9)); U9.set(5,U17.get(12))
            U9.set(6,U18.get(4)); U9.set(7,U18.get(7)); U9.set(8,U18.get(9)); U9.set(9,U18.get(12))
            U9.clock_edge()

    # Advance ring counter
    U24.set(1,U8.get(3)); U24.set(3,U8.get(4)); U24.update()
    U8.set(1,U24.get(2)); U8.set(2,U24.get(4)); U8.clock_edge()


# Init ring counter to T0
U8.set(9,0); U8.clock_edge()  # clear
U8.set(9,1)
# Force T0 state: shift in 1
U8.set(1,1); U8.set(2,1); U8.clock_edge()
# Now Q0=1 (T0)


if __name__ == '__main__':
    print("Lab 13: Full System (LI $42 → AC=$42)")
    print("-" * 40)

    # 3 phases: T0, T1, T2
    for clk in range(3):
        t0,t1,t2 = U8.get(3),U8.get(4),U8.get(5)
        phase = 'T0' if t0 else 'T1' if t1 else 'T2'
        do_phase()
        ac = sum(U9.get(19-i)<<i for i in range(8))
        ir_h = sum(U5.get(19-i)<<i for i in range(8))
        ir_l = sum(U6.get(19-i)<<i for i in range(8))
        print(f"  CLK{clk}: {phase} → IR=${ir_h:02X},{ir_l:02X} AC=${ac:02X}")

    ac = sum(U9.get(19-i)<<i for i in range(8))
    print(f"\n  Final AC = ${ac:02X}")
    assert ac == 0x42, f"Expected $42, got ${ac:02X}"
    print("\n✅ Lab 13 PASS: LI $42 executed through all chips → AC=$42")
