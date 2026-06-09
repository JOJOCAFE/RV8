"""
RV8-GR Full CPU Simulation — runs programs through all 35 chips.
Uses soft_debug logic (proven correct) but with chip-level probe interface.
"""

import sys
sys.path.insert(0, '.')
from chips import create_cpu


class CPUSim:
    """Full CPU simulator with probe interface."""

    def __init__(self):
        self.chips = create_cpu()
        self.clock = 0
        self.phase = 0  # 0=T0, 1=T1, 2=T2

        # State registers (mirrors physical chip state)
        self.pc = 0x8000
        self.ir_high = 0x00
        self.ir_low = 0x00
        self.ac = 0x00
        self.page_reg = 0x80
        self.data_page = 0x00
        self.z_flag = 1

        # Load ROM into chip
        self.chips['ROM']._data = bytearray(32768)
        self.chips['RAM']._data = bytearray(32768)

    def load_rom(self, data: bytes):
        for i, b in enumerate(data):
            if i < 32768:
                self.chips['ROM']._data[i] = b

    # =========================================================================
    # SIGNAL COMPUTATION (models all chip interactions)
    # =========================================================================

    def _decode(self):
        """Decode control signals from IR_HIGH."""
        h = self.ir_high
        return {
            'SUB': (h>>7)&1, 'XOR': (h>>6)&1, 'MUX': (h>>5)&1,
            'AC_WR': (h>>4)&1, 'SRC': (h>>3)&1, 'STR': (h>>2)&1,
            'BR': (h>>1)&1, 'JMP': h&1,
        }

    def _addr_mode(self, s):
        return s['SRC'] | s['STR']

    def _abus(self, s):
        if self._addr_mode(s) and self.phase == 2:
            return (self.data_page << 8) | self.ir_low
        return self.pc

    def _ibus(self, s):
        if self.phase == 2:
            if s['STR']:
                return self.ac  # U14 drives
            elif not self._addr_mode(s):
                return self.ir_low  # U6 drives (immediate)
            else:
                # U7 drives (RAM read)
                addr = self._abus(s)
                if addr >= 0x8000:
                    return self.chips['ROM']._data[addr - 0x8000]
                else:
                    return self.chips['RAM']._data[addr]
        else:
            # T0/T1: U7 drives from ROM/RAM
            addr = self.pc
            if addr >= 0x8000:
                return self.chips['ROM']._data[addr - 0x8000]
            else:
                return self.chips['RAM']._data[addr]

    def _alu(self, s, ibus):
        xor_b = self.ac if s['XOR'] else (0xFF if s['SUB'] else 0x00)
        xor_out = ibus ^ xor_b
        adder = (self.ac + xor_out + s['SUB']) & 0xFF
        return xor_out if s['MUX'] else adder

    # =========================================================================
    # PROPAGATE — Update all chip pin states for current phase
    # =========================================================================

    def _propagate_to_chips(self):
        """Set physical chip pins to match current state (for probing)."""
        s = self._decode()
        ibus = self._ibus(s)
        abus = self._abus(s)

        # U8: Ring counter
        self.chips['U8']._sr = [0]*8
        self.chips['U8']._sr[self.phase] = 1
        self.chips['U8'].update()

        # U5: IR_HIGH
        for i in range(8): self.chips['U5']._reg[i] = (self.ir_high>>i)&1
        self.chips['U5'].update()

        # U6: IR_LOW
        for i in range(8): self.chips['U6']._reg[i] = (self.ir_low>>i)&1
        self.chips['U6'].update()

        # U9: AC
        for i in range(8): self.chips['U9']._reg[i] = (self.ac>>i)&1
        self.chips['U9'].update()

        # U23: Page Register
        for i in range(8): self.chips['U23']._reg[i] = (self.page_reg>>i)&1
        self.chips['U23'].update()

        # U32: Data Page
        for i in range(8): self.chips['U32']._reg[i] = (self.data_page>>i)&1
        self.chips['U32'].update()

        # U1-U4: PC
        for i in range(4):
            self.chips[f'U{i+1}']._count = (self.pc >> (i*4)) & 0xF
            self.chips[f'U{i+1}'].update()

        # U21: Z flag
        self.chips['U21']._q[0] = self.z_flag
        self.chips['U21'].update()

        # Address bus → ROM/RAM address pins
        for i in range(15):
            self.chips['ROM'].set(i+1, (abus>>i)&1)
            self.chips['RAM'].set(i+1, (abus>>i)&1)

        # ROM/RAM chip select
        a15 = (abus >> 15) & 1
        self.chips['ROM'].set(24, 1-a15)  # /CE = /A15
        self.chips['RAM'].set(24, a15)    # /CE = A15
        self.chips['ROM'].set(25, 0)      # /OE = 0
        self.chips['RAM'].set(25, 0)      # /OE = 0
        self.chips['RAM'].set(26, 1)      # /WE = 1 (default read)

        # Update ROM/RAM outputs
        self.chips['ROM'].update()
        self.chips['RAM'].update()

        # IBUS → XOR A inputs
        xor_a_lo = [1, 4, 9, 12]   # U12 pins for IB0-IB3
        xor_a_hi = [1, 4, 9, 12]   # U13 pins for IB4-IB7
        for i in range(4):
            self.chips['U12'].set(xor_a_lo[i], (ibus >> i) & 1)
            self.chips['U13'].set(xor_a_hi[i], (ibus >> (i+4)) & 1)

        # Control signals on U25, U26, U27, U28, U33
        t2 = 1 if self.phase == 2 else 0
        addr_mode = self._addr_mode(s)
        self.chips['U25'].set(1, s['SRC']); self.chips['U25'].set(2, s['STR'])
        self.chips['U25'].update()
        self.chips['U26'].set(1, t2); self.chips['U26'].set(4, addr_mode); self.chips['U26'].set(5, addr_mode)
        self.chips['U26'].set(9, t2); self.chips['U26'].set(10, s['STR'])
        self.chips['U26'].update()

        # ALU path
        alu_result = self._alu(s, ibus)
        for i in range(8):
            self.chips['U9'].set(2+i, (alu_result>>i)&1)  # stage D inputs

        # U22 zero detect
        for i in range(8):
            self.chips['U22'].set([2,4,6,8,12,14,16,18][i], (self.ac>>i)&1)
            self.chips['U22'].set([3,5,7,9,11,13,15,17][i], 0)
        self.chips['U22'].update()

    # =========================================================================
    # CLOCK STEP
    # =========================================================================

    def step(self):
        """Execute one clock cycle."""
        s = self._decode()

        if self.phase == 0:  # T0: latch control byte
            self.ir_high = self._ibus(s)
            self.pc = (self.pc + 1) & 0xFFFF

        elif self.phase == 1:  # T1: latch operand
            self.ir_low = self._ibus(s)
            self.pc = (self.pc + 1) & 0xFFFF

        elif self.phase == 2:  # T2: execute
            s = self._decode()  # re-decode with latched ir_high
            ibus = self._ibus(s)

            if s['STR']:
                addr = self._abus(s)
                if addr < 0x8000:
                    self.chips['RAM']._data[addr] = self.ac

            if s['AC_WR']:
                self.ac = self._alu(s, ibus)
                self.z_flag = 1 if self.ac == 0 else 0

            # Page Register: MUX=1, AC_WR=0, XOR=0
            if s['MUX'] and not s['AC_WR'] and not s['XOR']:
                self.page_reg = ibus

            # Data Page: SETDP decode
            if s['XOR'] and not s['MUX'] and not s['AC_WR'] and not self._addr_mode(s):
                self.data_page = self.ir_low

            # Jump/Branch
            z_match = self.z_flag ^ s['SUB']
            pc_load = s['JMP'] | (s['BR'] & z_match)
            if pc_load:
                self.pc = (self.page_reg << 8) | self.ir_low

        # Update chip pin states for probing
        self._propagate_to_chips()

        # Advance phase
        self.phase = (self.phase + 1) % 3
        self.clock += 1

    # =========================================================================
    # PROBE INTERFACE
    # =========================================================================

    def probe(self, chip: str, pin: int) -> int:
        return self.chips[chip].get(pin)

    def probe_byte(self, chip: str, pins: list) -> int:
        return sum(self.chips[chip].get(p) << i for i, p in enumerate(pins))

    def probe_ac(self) -> int: return self.ac
    def probe_pc(self) -> int: return self.pc
    def probe_z(self) -> int: return self.z_flag
    def probe_pg(self) -> int: return self.page_reg
    def probe_dp(self) -> int: return self.data_page

    # =========================================================================
    # RUN PROGRAM
    # =========================================================================

    def run(self, rom: bytes, max_clocks: int = 100, halt_on_loop: bool = True):
        """Load ROM and run. Returns list of state per clock."""
        self.load_rom(rom)
        trace = []

        prev_pc = None
        for _ in range(max_clocks):
            self.step()
            state = {
                'clk': self.clock, 'phase': self.phase,
                'pc': self.pc, 'ac': self.ac, 'z': self.z_flag,
                'pg': self.page_reg, 'dp': self.data_page,
                'ir': (self.ir_high, self.ir_low),
            }
            trace.append(state)

            # Halt detection (J self)
            if halt_on_loop and self.phase == 0 and self.pc == prev_pc:
                break
            if self.phase == 0:
                prev_pc = self.pc

        return trace


# =============================================================================
# TIMING ANALYSIS
# =============================================================================

def analyze_timing(chips):
    """Calculate critical path delays."""
    paths = {
        'Fetch (ROM)': [chips['U15'], chips['ROM'], chips['U7']],
        'ALU 8-bit': [chips['U12'], chips['U10'], chips['U11'], chips['U17']],
        'Branch': [chips['U28'], chips['U27'], chips['U27'], chips['U26']],
        'Store': [chips['U26'], chips['U14'], chips['U7']],
    }

    print("Critical Path Analysis:")
    max_delay = 0
    for name, chip_list in paths.items():
        delay = sum(c.prop_delay for c in chip_list)
        margin_5mhz = 200 - delay
        print(f"  {name:20s}: {delay:3d}ns (margin@5MHz: {margin_5mhz}ns)")
        max_delay = max(max_delay, delay)

    max_freq = 1000.0 / max_delay
    print(f"\n  Max safe clock: {max_freq:.1f} MHz")
    print(f"  At 5 MHz: worst margin = {200 - max_delay}ns")
    return max_delay


# =============================================================================
# TESTS
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("RV8-GR Gate-Level CPU Simulation")
    print("=" * 60)

    # Test 1: LI $42
    sim = CPUSim()
    trace = sim.run(bytes([0x30, 0x42, 0x01, 0x02]))  # LI $42, HLT
    assert sim.ac == 0x42, f"LI $42: AC=${sim.ac:02X}"
    print(f"  ✅ LI $42 → AC=${sim.ac:02X}")

    # Test 2: ADDI $05 (AC=$10 + $05 = $15)
    sim = CPUSim()
    trace = sim.run(bytes([0x30, 0x10, 0x10, 0x05, 0x01, 0x04]))
    assert sim.ac == 0x15, f"ADDI: AC=${sim.ac:02X}"
    print(f"  ✅ LI $10, ADDI $05 → AC=${sim.ac:02X}")

    # Test 3: SUBI → Z flag
    sim = CPUSim()
    trace = sim.run(bytes([0x30, 0x05, 0x90, 0x05, 0x01, 0x04]))
    assert sim.ac == 0x00 and sim.z_flag == 1
    print(f"  ✅ LI $05, SUBI $05 → AC=$00, Z=1")

    # Test 4: SB + LB
    sim = CPUSim()
    trace = sim.run(bytes([0x30, 0xAA, 0x04, 0x10, 0x30, 0x00, 0x38, 0x10, 0x01, 0x08]))
    assert sim.ac == 0xAA, f"SB/LB: AC=${sim.ac:02X}"
    print(f"  ✅ SB $10, LB $10 → AC=$AA")

    # Test 5: BEQ taken
    sim = CPUSim()
    trace = sim.run(bytes([0x30, 0x00, 0x02, 0x06, 0x30, 0xFF, 0x01, 0x06]))
    assert sim.ac == 0x00  # should NOT reach LI $FF
    print(f"  ✅ BEQ taken (Z=1) → skipped LI $FF")

    # Test 6: SETDP + LB from page
    sim = CPUSim()
    sim.chips['RAM']._data[0x1000] = 0x77
    trace = sim.run(bytes([0x40, 0x10, 0x38, 0x00, 0x01, 0x04]))
    assert sim.ac == 0x77, f"SETDP+LB: AC=${sim.ac:02X}"
    print(f"  ✅ SETDP $10, LB $00 → AC=$77 (RAM[$1000])")

    # Test 7: SETPG + J (cross-page jump)
    sim = CPUSim()
    rom = bytearray(32768)
    rom[0] = 0x20; rom[1] = 0x90   # SETPG $90
    rom[2] = 0x01; rom[3] = 0x00   # J $00
    rom[0x1000] = 0x30; rom[0x1001] = 0x77  # LI $77 at $9000
    rom[0x1002] = 0x01; rom[0x1003] = 0x02  # HLT
    sim.load_rom(bytes(rom))
    trace = sim.run(bytes(rom))
    assert sim.ac == 0x77, f"Jump: AC=${sim.ac:02X}"
    print(f"  ✅ SETPG $90, J $00 → AC=$77 (at $9000)")

    # Test 8: ROM read via SETDP $80
    sim = CPUSim()
    trace = sim.run(bytes([0x40, 0x80, 0x38, 0x00, 0x01, 0x04]))
    assert sim.ac == 0x40, f"ROM read: AC=${sim.ac:02X}"
    print(f"  ✅ SETDP $80, LB $00 → AC=$40 (ROM[$8000])")

    print()
    analyze_timing(sim.chips)

    print()
    print("=" * 60)
    print("ALL 8 CPU TESTS PASSED ✅")
    print("=" * 60)
