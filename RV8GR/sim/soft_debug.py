#!/usr/bin/env python3
"""
RV8-GR Soft Debug: Pin-level logic simulation
Traces signals through all 36 packages clock-by-clock.
Simulates with slow clock to verify wiring correctness.

NOTE: This sim models the 36-package v1.0 CPU:
  - EI ($08) sets IE; DI ($48) is an inert software marker
  - DP/PG/AC/Z initialized to known values (hardware = indeterminate at power-on)
  - IRQ is polling-only: /IRQ latches IRQ_FF, no hardware vector
  Physical v1.0 programs must begin with: SETDP $80, SETPG $00, LI $00

Usage: python3 soft_debug.py
"""

# =============================================================================
# CHIP MODELS (simplified, pin-level accurate)
# =============================================================================

class CPU:
    def __init__(self):
        # Registers
        self.pc = 0x0000
        self.ir_high = 0x00
        self.ir_low = 0x00
        self.ac = 0x00
        self.page_reg = 0x00
        self.data_page = 0x80
        self.z_flag = 1
        self.ie = 0
        self.irq_ff = 0

        # Ring counter state (one-hot: 0=T0, 1=T1, 2=T2)
        self.phase = 0  # starts at T0

        # Memory
        self.rom = bytearray(32768)
        self.ram = bytearray(32768)

        # Bus signals (updated each clock)
        self.abus = 0x0000
        self.dbus = 0x00
        self.ibus = 0x00

        # Control signals
        self.signals = {}

        # Clock count
        self.clock = 0

    def load_rom(self, data, base=0x0000):
        for i, b in enumerate(data):
            if i < 32768:
                self.rom[i] = b

    # =========================================================================
    # SIGNAL DECODE (models U5 outputs + derived logic)
    # =========================================================================

    def decode_control(self):
        """Decode IR_HIGH into control signals (U5 Q outputs)."""
        s = {}
        s['SUB'] = (self.ir_high >> 7) & 1       # U5-12
        s['XOR_MODE'] = (self.ir_high >> 6) & 1  # U5-13
        s['MUX_SEL'] = (self.ir_high >> 5) & 1   # U5-14
        s['AC_WR'] = (self.ir_high >> 4) & 1     # U5-15
        s['SRC'] = (self.ir_high >> 3) & 1       # U5-16
        s['STR'] = (self.ir_high >> 2) & 1       # U5-17
        s['BR'] = (self.ir_high >> 1) & 1        # U5-18
        s['JMP'] = self.ir_high & 1              # U5-19

        # Derived (U25, U26, U27, U28)
        s['ADDR_MODE'] = s['SRC'] | s['STR']                       # U25-3
        s['PC_INC'] = 1 if self.phase in (0, 1) else 0             # U25-6
        s['/ADDR_MODE'] = 1 if s['ADDR_MODE'] == 0 else 0          # U26-6
        s['/IRL_OE'] = 0 if (self.phase == 2 and s['/ADDR_MODE']) else 1  # U26-3
        s['BUF_OE_N'] = 1 - s['/IRL_OE']                           # U24-12 (NOT /IRL_OE) → U7 /OE
        s['/AC_BUF'] = 0 if (self.phase == 2 and s['STR']) else 1  # U26-8
        s['WR_DIR'] = 1 - s['/AC_BUF']                             # U28-8

        # Branch/Jump
        s['Z_match'] = self.z_flag ^ s['SUB']                       # U28-3
        s['BR_TAKEN'] = s['BR'] & s['Z_match']
        s['PC_LOAD_COND'] = s['JMP'] | s['BR_TAKEN']               # U27-6
        s['/PC_LD'] = 0 if (self.phase == 2 and s['PC_LOAD_COND']) else 1  # U26-11

        # Page Register (U23 clock): physical gate ignores XOR/SUB/JMP/BR bits.
        s['PG_LOAD'] = s['MUX_SEL'] and not s['AC_WR']

        # Data Page (SETDP decode = U33)
        s['DP_LOAD'] = (self.phase == 2 and s['XOR_MODE'] and
                        not s['ADDR_MODE'] and not s['AC_WR'])      # U33-6

        # Accumulator
        s['ACC_LOAD'] = (self.phase == 2 and s['AC_WR'])            # U27-11 (inverted)

        self.signals = s
        return s

    # =========================================================================
    # BUS LOGIC (models address mux, bus buffer, memory)
    # =========================================================================

    def compute_buses(self):
        """Compute ABUS, DBUS, IBUS values based on current state and signals."""
        s = self.signals

        # Address bus (U15-U16, U29-U30): only switch to data address during T2
        if self.phase == 2 and s['ADDR_MODE']:
            # Data mode: ABUS = {data_page, ir_low}
            self.abus = (self.data_page << 8) | self.ir_low
        else:
            # Fetch mode: ABUS = PC
            self.abus = self.pc

        # Memory read: A15=0 → ROM, A15=1 → RAM
        if self.abus >= 0x8000:
            self.dbus = self.ram[self.abus - 0x8000]
        else:
            self.dbus = self.rom[self.abus]

        # IBUS source selection
        if self.phase == 2:
            if s['STR']:
                # U14 drives IBUS = AC
                self.ibus = self.ac
            elif s['/IRL_OE'] == 0:
                # U34 drives IBUS = IRL (immediate)
                self.ibus = self.ir_low
            else:
                # U7 drives IBUS = DBUS (RAM read)
                self.ibus = self.dbus
        else:
            # During T0/T1: U7 drives IBUS from ROM/RAM
            self.ibus = self.dbus

    # =========================================================================
    # ALU (models U10-U13, U19-U20, U17-U18)
    # =========================================================================

    def compute_alu(self):
        """Compute ALU result."""
        s = self.signals

        # XOR B-input mux (U19-U20)
        if s['XOR_MODE']:
            xor_b = self.ac
        else:
            xor_b = 0xFF if s['SUB'] else 0x00

        # XOR array (U12-U13)
        xor_out = self.ibus ^ xor_b

        # Adder (U10-U11)
        adder_sum = (self.ac + xor_out + s['SUB']) & 0xFF

        # AC mux (U17-U18)
        if s['MUX_SEL']:
            return xor_out
        else:
            return adder_sum

    # =========================================================================
    # CLOCK TICK
    # =========================================================================

    def tick(self):
        """Execute one clock cycle."""
        self.clock += 1
        self.decode_control()
        self.compute_buses()

        if self.phase == 0:
            # T0: Latch control byte from IBUS into U5
            self.ir_high = self.ibus
            self.pc = (self.pc + 1) & 0xFFFF

        elif self.phase == 1:
            # T1: Latch operand from IBUS into U6
            self.ir_low = self.ibus
            self.pc = (self.pc + 1) & 0xFFFF

        elif self.phase == 2:
            # T2: Execute
            s = self.signals

            # Re-decode with final ir_high (was latched at T0)
            self.decode_control()
            self.compute_buses()

            # Store: RAM write only if A15=1
            if s['STR'] and self.abus >= 0x8000:
                self.ram[self.abus - 0x8000] = self.ac

            # AC update
            if s['AC_WR']:
                self.ac = self.compute_alu()
                self.z_flag = 1 if self.ac == 0 else 0

            # Page Register
            if s['PG_LOAD']:
                self.page_reg = self.ibus

            # Data Page Register (SETDP)
            if s['DP_LOAD']:
                self.data_page = self.ir_low

            # Jump/Branch
            if s['PC_LOAD_COND']:
                self.pc = (self.page_reg << 8) | self.ir_low

            # EI physical decode is U33 gate 2. DI has no hardware clear path.
            if s['SRC'] and not s['XOR_MODE'] and not s['AC_WR']:
                self.ie = 1

        # Advance ring counter
        self.phase = (self.phase + 1) % 3

    # =========================================================================
    # DEBUG OUTPUT
    # =========================================================================

    def trace(self, verbose=False):
        """Print current state."""
        phase_names = ['T0', 'T1', 'T2']
        s = self.signals
        print(f"CLK{self.clock:4d} | {phase_names[self.phase]} | "
              f"PC=${self.pc:04X} AC=${self.ac:02X} Z={self.z_flag} "
              f"PG=${self.page_reg:02X} DP=${self.data_page:02X} | "
              f"ABUS=${self.abus:04X} DBUS=${self.dbus:02X} IBUS=${self.ibus:02X} | "
              f"IR=${self.ir_high:02X},{self.ir_low:02X}")

        if verbose and s:
            print(f"       U1-U4: PC=${self.pc:04X} PC_INC={s['PC_INC']} /PC_LD={s['/PC_LD']}")
            print(f"       U5:    IR_HIGH=${self.ir_high:02X} → SUB={s['SUB']} XOR={s['XOR_MODE']} MUX={s['MUX_SEL']} "
                  f"AC_WR={s['AC_WR']} SRC={s['SRC']} STR={s['STR']} BR={s['BR']} JMP={s['JMP']}")
            print(f"       U6:    IR_LOW=${self.ir_low:02X} /OE={s['/IRL_OE']}")
            print(f"       U7:    DIR={s['WR_DIR']} /OE={s['BUF_OE_N']} {'WRITE' if s['WR_DIR'] else 'READ'}")
            print(f"       U8:    phase={phase_names[self.phase]} T0={1 if self.phase==0 else 0} "
                  f"T1={1 if self.phase==1 else 0} T2={1 if self.phase==2 else 0}")
            print(f"       U9:    AC=${self.ac:02X}")
            # ALU (U10-U13, U19-U20)
            if self.phase == 2:
                xor_b = self.ac if s['XOR_MODE'] else (0xFF if s['SUB'] else 0x00)
                xor_out = self.ibus ^ xor_b
                adder_sum = (self.ac + xor_out + s['SUB']) & 0xFF
                ac_mux = xor_out if s['MUX_SEL'] else adder_sum
                print(f"       U10-11: Adder A(AC)=${self.ac:02X} + B(XOR)=${xor_out:02X} + Cin={s['SUB']} = ${adder_sum:02X}")
                print(f"       U12-13: XOR A(IBUS)=${self.ibus:02X} ^ B(mux)=${xor_b:02X} = ${xor_out:02X}")
                print(f"       U17-18: AC_mux SEL={s['MUX_SEL']} → ${ac_mux:02X}")
                print(f"       U19-20: XOR_B_mux SEL={s['XOR_MODE']} → ${xor_b:02X}")
            print(f"       U14:   /OE={s['/AC_BUF']} {'(driving IBUS=AC)' if not s['/AC_BUF'] else '(disabled)'}")
            print(f"       U15-16: Addr_lo SEL={s['ADDR_MODE']} → ${self.abus & 0xFF:02X}")
            print(f"       U21:   Z_flag={self.z_flag}")
            print(f"       U22:   AC==0? {'YES' if self.ac==0 else 'NO'}")
            print(f"       U23:   PG=${self.page_reg:02X}")
            print(f"       U24:   /A15={'0' if self.abus>=0x8000 else '1'}→RAM_CE "
                  f"/JUMP={1-s['JMP']} /AC_WR={1-s['AC_WR']} BUF_OE_N={s['BUF_OE_N']}")
            print(f"       U25:   ADDR_MODE={s['ADDR_MODE']} PC_INC={s['PC_INC']} "
                  f"U7_OE_N={s['BUF_OE_N']} PG_Load={'1' if s['PG_LOAD'] else '0'}")
            print(f"       U26:   /IRL_OE={s['/IRL_OE']} /AC_BUF={s['/AC_BUF']} /PC_LD={s['/PC_LD']}")
            print(f"       U27:   BR_TAKEN={s['BR_TAKEN']} PC_LOAD_COND={s['PC_LOAD_COND']} "
                  f"ACC_LOAD={'1' if s.get('ACC_LOAD') else '0'}")
            print(f"       U28:   Z_match={s['Z_match']} WR_DIR={s['WR_DIR']}")
            print(f"       U29-30: Addr_hi SEL={s['ADDR_MODE']} → ${(self.abus>>8)&0xFF:02X} A15={1 if self.abus>=0x8000 else 0}")
            print(f"       U31:   IE={self.ie} IRQ_FF={self.irq_ff}")
            print(f"       U32:   DP=${self.data_page:02X}")
            print(f"       U33:   DP_LOAD={'1' if s['DP_LOAD'] else '0'}")
            print(f"       ROM:   /CE={'0(active)' if self.abus<0x8000 else '1(off)'} "
                  f"D=${self.rom[self.abus] if self.abus<0x8000 else 0:02X}")
            print(f"       RAM:   /CE={'0(active)' if self.abus>=0x8000 else '1(off)'} "
                  f"D=${self.ram[self.abus-0x8000] if self.abus>=0x8000 else 0:02X} "
                  f"/WE={s['/AC_BUF']}")
            print()


# =============================================================================
# TEST PROGRAMS
# =============================================================================

def test_basic():
    """Test: LI $42, ADDI $05, SUBI $47, BEQ pass"""
    cpu = CPU()
    program = [
        0x30, 0x42,  # LI $42
        0x10, 0x05,  # ADDI $05 → AC=$47
        0x90, 0x47,  # SUBI $47 → AC=$00, Z=1
        0x02, 0x08,  # BEQ $08 (pass)
        0x01, 0x08,  # J $08 (fail - shouldn't reach)
    ]
    # pass: HLT at $0008
    program += [0x01, 0x08]  # J self (halt)

    cpu.load_rom(bytes(program))

    print("=" * 80)
    print("TEST: LI $42, ADDI $05, SUBI $47, BEQ pass")
    print("=" * 80)

    for _ in range(18):  # 6 instructions × 3 clocks
        cpu.trace()
        cpu.tick()

    cpu.trace()
    assert cpu.ac == 0x00, f"FAIL: AC=${cpu.ac:02X} expected $00"
    assert cpu.z_flag == 1, f"FAIL: Z={cpu.z_flag} expected 1"
    assert cpu.pc == 0x0008, f"FAIL: PC=${cpu.pc:04X} expected $0008 (HLT loop)"
    print("\n✅ PASS: Basic ALU + Branch\n")


def test_setdp():
    """Test: SETDP $90, LI $AA, SB $00, SETDP $90, LB $00"""
    cpu = CPU()
    program = [
        0x40, 0x90,  # SETDP $90
        0x30, 0xAA,  # LI $AA
        0x04, 0x00,  # SB $00 → RAM[$9000] = $AA
        0x40, 0x90,  # SETDP $90
        0x30, 0x00,  # LI $00 → AC=0
        0x38, 0x00,  # LB $00 → AC=RAM[$9000]=$AA
        0x01, 0x0C,  # HLT
    ]
    cpu.load_rom(bytes(program))

    print("=" * 80)
    print("TEST: SETDP $90, write/read RAM[$9000]")
    print("=" * 80)

    for _ in range(21):  # 7 instructions × 3 clocks
        cpu.trace()
        cpu.tick()

    cpu.trace()
    assert cpu.ac == 0xAA, f"FAIL: AC=${cpu.ac:02X} expected $AA"
    assert cpu.data_page == 0x90, f"FAIL: DP=${cpu.data_page:02X} expected $90"
    print("\n✅ PASS: SETDP + RAM page access\n")


def test_rom_read():
    """Test: SETDP $00, LB $00 → reads ROM[$0000] = first opcode ($40)"""
    cpu = CPU()
    program = [
        0x40, 0x00,  # SETDP $00
        0x38, 0x00,  # LB $00 → AC=ROM[$0000]=$40
        0x01, 0x04,  # HLT
    ]
    cpu.load_rom(bytes(program))

    print("=" * 80)
    print("TEST: SETDP $00, LB $00 → read own ROM")
    print("=" * 80)

    for _ in range(9):
        cpu.trace()
        cpu.tick()

    cpu.trace()
    assert cpu.ac == 0x40, f"FAIL: AC=${cpu.ac:02X} expected $40 (first ROM byte)"
    print("\n✅ PASS: ROM read via SETDP\n")


def test_jump():
    """Test: SETPG $10, J $00 → PC=$1000"""
    cpu = CPU()
    # At $0000:
    program = bytearray(32768)
    program[0] = 0x20; program[1] = 0x10   # SETPG $10
    program[2] = 0x01; program[3] = 0x00   # J $00 → PC=$1000
    # At $1000 (offset $1000 in ROM):
    program[0x1000] = 0x30; program[0x1001] = 0x77  # LI $77
    program[0x1002] = 0x01; program[0x1003] = 0x02  # HLT

    cpu.load_rom(bytes(program))

    print("=" * 80)
    print("TEST: SETPG $10, J $00 → jump to $1000")
    print("=" * 80)

    for _ in range(12):
        cpu.trace()
        cpu.tick()

    cpu.trace()
    assert cpu.ac == 0x77, f"FAIL: AC=${cpu.ac:02X} expected $77"
    assert cpu.page_reg == 0x10, f"FAIL: PG=${cpu.page_reg:02X} expected $10"
    print("\n✅ PASS: Cross-page jump\n")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    import sys
    verbose = '-v' in sys.argv

    print("RV8-GR Soft Debug — Pin-Level Logic Simulation")
    print(f"Mode: {'VERBOSE (34 logic chips + ROM/RAM)' if verbose else 'compact'}")
    print(f"Usage: python3 soft_debug.py [-v]")
    print()

    test_basic()
    test_setdp()
    test_rom_read()
    test_jump()

    if verbose:
        print("=" * 80)
        print("VERBOSE TRACE: ADDI $05 (all 35 chip signals)")
        print("=" * 80)
        cpu = CPU()
        cpu.load_rom(bytes([0x10, 0x05, 0x01, 0x02]))  # ADDI $05, HLT
        cpu.ac = 0x10  # pre-set AC
        for _ in range(3):
            cpu.tick()
            cpu.trace(verbose=True)

    print("=" * 80)
    print("ALL SOFT DEBUG TESTS PASSED ✅")
    print("=" * 80)
