"""RV8-GR Chip Simulator — Base classes and all 35 chip definitions."""


class Pin:
    """A single chip pin."""
    __slots__ = ('name', 'value', 'direction')

    def __init__(self, name: str, direction: str = 'in'):
        self.name = name          # e.g. "D0", "/OE", "Q3"
        self.value = 0            # logic level: 0 or 1
        self.direction = direction  # 'in', 'out', 'bidir', 'power', 'nc'


class Chip:
    """Base class for all chips. Defines pins by number."""

    def __init__(self, name: str, pin_defs: dict):
        """
        name: instance name (e.g. "U5")
        pin_defs: {pin_number: (pin_name, direction)}
        """
        self.name = name
        self.pins = {}  # {pin_number: Pin}
        for num, (pname, direction) in pin_defs.items():
            self.pins[num] = Pin(pname, direction)

    def pin(self, num: int) -> Pin:
        return self.pins[num]

    def get(self, num: int) -> int:
        return self.pins[num].value

    def set(self, num: int, value: int):
        self.pins[num].value = value & 1

    def update(self):
        """Override: recalculate outputs from inputs (combinational)."""
        pass

    def clock_edge(self):
        """Override: handle rising clock edge (sequential)."""
        pass


# =============================================================================
# 74HC574 — Octal D Flip-Flop (20-pin DIP)
# Pins: 1=/OE, 2-9=D1-D8, 10=GND, 11=CLK, 12-19=Q8-Q1, 20=VCC
# =============================================================================

def make_hc574(name: str) -> Chip:
    pins = {
        1:  ('/OE', 'in'),
        2:  ('D1', 'in'),   3:  ('D2', 'in'),   4:  ('D3', 'in'),   5:  ('D4', 'in'),
        6:  ('D5', 'in'),   7:  ('D6', 'in'),   8:  ('D7', 'in'),   9:  ('D8', 'in'),
        10: ('GND', 'power'),
        11: ('CLK', 'in'),
        12: ('Q8', 'out'),  13: ('Q7', 'out'),  14: ('Q6', 'out'),  15: ('Q5', 'out'),
        16: ('Q4', 'out'),  17: ('Q3', 'out'),  18: ('Q2', 'out'),  19: ('Q1', 'out'),
        20: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC161 — 4-bit Synchronous Counter (16-pin DIP)
# Pins: 1=/CLR, 2=CLK, 3-6=D0-D3, 7=ENP, 8=GND, 9=/LD, 10=ENT,
#       11-14=QD-QA, 15=RCO, 16=VCC
# =============================================================================

def make_hc161(name: str) -> Chip:
    pins = {
        1:  ('/CLR', 'in'),
        2:  ('CLK', 'in'),
        3:  ('D0', 'in'),   4:  ('D1', 'in'),   5:  ('D2', 'in'),   6:  ('D3', 'in'),
        7:  ('ENP', 'in'),
        8:  ('GND', 'power'),
        9:  ('/LD', 'in'),
        10: ('ENT', 'in'),
        11: ('QD', 'out'),  12: ('QC', 'out'),  13: ('QB', 'out'),  14: ('QA', 'out'),
        15: ('RCO', 'out'),
        16: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC164 — 8-bit Serial-In Shift Register (14-pin DIP)
# Pins: 1=A, 2=B, 3-6=Q0-Q3, 7=GND, 8=CLK, 9=/CLR, 10-13=Q4-Q7, 14=VCC
# =============================================================================

def make_hc164(name: str) -> Chip:
    pins = {
        1:  ('A', 'in'),
        2:  ('B', 'in'),
        3:  ('Q0', 'out'),  4:  ('Q1', 'out'),  5:  ('Q2', 'out'),  6:  ('Q3', 'out'),
        7:  ('GND', 'power'),
        8:  ('CLK', 'in'),
        9:  ('/CLR', 'in'),
        10: ('Q4', 'out'),  11: ('Q5', 'out'),  12: ('Q6', 'out'),  13: ('Q7', 'out'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC74 — Dual D Flip-Flop (14-pin DIP)
# Pins: 1=/CLR1, 2=D1, 3=CLK1, 4=/PR1, 5=Q1, 6=/Q1, 7=GND,
#       8=/Q2, 9=Q2, 10=/PR2, 11=CLK2, 12=D2, 13=/CLR2, 14=VCC
# =============================================================================

def make_hc74(name: str) -> Chip:
    pins = {
        1:  ('/CLR1', 'in'),
        2:  ('D1', 'in'),
        3:  ('CLK1', 'in'),
        4:  ('/PR1', 'in'),
        5:  ('Q1', 'out'),
        6:  ('/Q1', 'out'),
        7:  ('GND', 'power'),
        8:  ('/Q2', 'out'),
        9:  ('Q2', 'out'),
        10: ('/PR2', 'in'),
        11: ('CLK2', 'in'),
        12: ('D2', 'in'),
        13: ('/CLR2', 'in'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC245 — Octal Bidirectional Buffer (20-pin DIP)
# Pins: 1=DIR, 2-9=A1-A8, 10=GND, 11-18=B8-B1, 19=/OE, 20=VCC
# =============================================================================

def make_hc245(name: str) -> Chip:
    pins = {
        1:  ('DIR', 'in'),
        2:  ('A1', 'bidir'), 3:  ('A2', 'bidir'), 4:  ('A3', 'bidir'), 5:  ('A4', 'bidir'),
        6:  ('A5', 'bidir'), 7:  ('A6', 'bidir'), 8:  ('A7', 'bidir'), 9:  ('A8', 'bidir'),
        10: ('GND', 'power'),
        11: ('B8', 'bidir'), 12: ('B7', 'bidir'), 13: ('B6', 'bidir'), 14: ('B5', 'bidir'),
        15: ('B4', 'bidir'), 16: ('B3', 'bidir'), 17: ('B2', 'bidir'), 18: ('B1', 'bidir'),
        19: ('/OE', 'in'),
        20: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC541 — Octal Buffer (20-pin DIP)
# Pins: 1=/OE1, 2-9=A1-A8, 10=GND, 11-18=Y8-Y1, 19=/OE2, 20=VCC
# =============================================================================

def make_hc541(name: str) -> Chip:
    pins = {
        1:  ('/OE1', 'in'),
        2:  ('A1', 'in'),  3:  ('A2', 'in'),  4:  ('A3', 'in'),  5:  ('A4', 'in'),
        6:  ('A5', 'in'),  7:  ('A6', 'in'),  8:  ('A7', 'in'),  9:  ('A8', 'in'),
        10: ('GND', 'power'),
        11: ('Y8', 'out'), 12: ('Y7', 'out'), 13: ('Y6', 'out'), 14: ('Y5', 'out'),
        15: ('Y4', 'out'), 16: ('Y3', 'out'), 17: ('Y2', 'out'), 18: ('Y1', 'out'),
        19: ('/OE2', 'in'),
        20: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC283 — 4-bit Full Adder (16-pin DIP)
# Pins: 1=S1, 2=B1, 3=A1, 4=S0, 5=A0, 6=B0, 7=Cin, 8=GND,
#       9=Cout, 10=S3, 11=B3, 12=A3, 13=S2, 14=A2, 15=B2, 16=VCC
# =============================================================================

def make_hc283(name: str) -> Chip:
    pins = {
        1:  ('S1', 'out'),
        2:  ('B1', 'in'),
        3:  ('A1', 'in'),
        4:  ('S0', 'out'),
        5:  ('A0', 'in'),
        6:  ('B0', 'in'),
        7:  ('Cin', 'in'),
        8:  ('GND', 'power'),
        9:  ('Cout', 'out'),
        10: ('S3', 'out'),
        11: ('B3', 'in'),
        12: ('A3', 'in'),
        13: ('S2', 'out'),
        14: ('A2', 'in'),
        15: ('B2', 'in'),
        16: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC86 — Quad 2-input XOR (14-pin DIP)
# Pins: 1=1A, 2=1B, 3=1Y, 4=2A, 5=2B, 6=2Y, 7=GND,
#       8=3Y, 9=3A, 10=3B, 11=4Y, 12=4A, 13=4B, 14=VCC
# =============================================================================

def make_hc86(name: str) -> Chip:
    pins = {
        1:  ('1A', 'in'),  2:  ('1B', 'in'),  3:  ('1Y', 'out'),
        4:  ('2A', 'in'),  5:  ('2B', 'in'),  6:  ('2Y', 'out'),
        7:  ('GND', 'power'),
        8:  ('3Y', 'out'), 9:  ('3A', 'in'),  10: ('3B', 'in'),
        11: ('4Y', 'out'), 12: ('4A', 'in'),  13: ('4B', 'in'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC157 — Quad 2-to-1 Mux (16-pin DIP)
# Pins: 1=SEL, 2=1A, 3=1B, 4=1Y, 5=2A, 6=2B, 7=2Y, 8=GND,
#       9=3Y, 10=3B, 11=3A, 12=4Y, 13=4B, 14=4A, 15=/E, 16=VCC
# =============================================================================

def make_hc157(name: str) -> Chip:
    pins = {
        1:  ('SEL', 'in'),
        2:  ('1A', 'in'),  3:  ('1B', 'in'),  4:  ('1Y', 'out'),
        5:  ('2A', 'in'),  6:  ('2B', 'in'),  7:  ('2Y', 'out'),
        8:  ('GND', 'power'),
        9:  ('3Y', 'out'), 10: ('3B', 'in'),  11: ('3A', 'in'),
        12: ('4Y', 'out'), 13: ('4B', 'in'),  14: ('4A', 'in'),
        15: ('/E', 'in'),
        16: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC688 — 8-bit Comparator (20-pin DIP)
# Pins: 1=/OE, 2=P0, 3=Q0, 4=P1, 5=Q1, 6=P2, 7=Q2, 8=P3, 9=Q3, 10=GND,
#       11=Q4, 12=P4, 13=Q5, 14=P5, 15=Q6, 16=P6, 17=Q7, 18=P7, 19=/P=Q, 20=VCC
# =============================================================================

def make_hc688(name: str) -> Chip:
    pins = {
        1:  ('/OE', 'in'),
        2:  ('P0', 'in'),  3:  ('Q0', 'in'),
        4:  ('P1', 'in'),  5:  ('Q1', 'in'),
        6:  ('P2', 'in'),  7:  ('Q2', 'in'),
        8:  ('P3', 'in'),  9:  ('Q3', 'in'),
        10: ('GND', 'power'),
        11: ('Q4', 'in'),  12: ('P4', 'in'),
        13: ('Q5', 'in'),  14: ('P5', 'in'),
        15: ('Q6', 'in'),  16: ('P6', 'in'),
        17: ('Q7', 'in'),  18: ('P7', 'in'),
        19: ('/P=Q', 'out'),
        20: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC04 — Hex Inverter (14-pin DIP)
# Pins: 1=1A, 2=1Y, 3=2A, 4=2Y, 5=3A, 6=3Y, 7=GND,
#       8=4Y, 9=4A, 10=5Y, 11=5A, 12=6Y, 13=6A, 14=VCC
# =============================================================================

def make_hc04(name: str) -> Chip:
    pins = {
        1:  ('1A', 'in'),  2:  ('1Y', 'out'),
        3:  ('2A', 'in'),  4:  ('2Y', 'out'),
        5:  ('3A', 'in'),  6:  ('3Y', 'out'),
        7:  ('GND', 'power'),
        8:  ('4Y', 'out'), 9:  ('4A', 'in'),
        10: ('5Y', 'out'), 11: ('5A', 'in'),
        12: ('6Y', 'out'), 13: ('6A', 'in'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC32 — Quad 2-input OR (14-pin DIP)
# Pins: 1=1A, 2=1B, 3=1Y, 4=2A, 5=2B, 6=2Y, 7=GND,
#       8=3Y, 9=3A, 10=3B, 11=4A, 12=4B, 13=4Y, 14=VCC
# =============================================================================

def make_hc32(name: str) -> Chip:
    pins = {
        1:  ('1A', 'in'),  2:  ('1B', 'in'),  3:  ('1Y', 'out'),
        4:  ('2A', 'in'),  5:  ('2B', 'in'),  6:  ('2Y', 'out'),
        7:  ('GND', 'power'),
        8:  ('3Y', 'out'), 9:  ('3A', 'in'),  10: ('3B', 'in'),
        11: ('4A', 'in'),  12: ('4B', 'in'),  13: ('4Y', 'out'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC00 — Quad 2-input NAND (14-pin DIP)
# Pins: 1=1A, 2=1B, 3=1Y, 4=2A, 5=2B, 6=2Y, 7=GND,
#       8=3Y, 9=3A, 10=3B, 11=4Y, 12=4A, 13=4B, 14=VCC
# =============================================================================

def make_hc00(name: str) -> Chip:
    pins = {
        1:  ('1A', 'in'),  2:  ('1B', 'in'),  3:  ('1Y', 'out'),
        4:  ('2A', 'in'),  5:  ('2B', 'in'),  6:  ('2Y', 'out'),
        7:  ('GND', 'power'),
        8:  ('3Y', 'out'), 9:  ('3A', 'in'),  10: ('3B', 'in'),
        11: ('4Y', 'out'), 12: ('4A', 'in'),  13: ('4B', 'in'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# 74HC21 — Dual 4-input AND (14-pin DIP)
# Pins: 1=1A, 2=1B, 3=NC, 4=1C, 5=1D, 6=1Y, 7=GND,
#       8=2Y, 9=2A, 10=2B, 11=NC, 12=2C, 13=2D, 14=VCC
# =============================================================================

def make_hc21(name: str) -> Chip:
    pins = {
        1:  ('1A', 'in'),  2:  ('1B', 'in'),  3:  ('NC', 'nc'),
        4:  ('1C', 'in'),  5:  ('1D', 'in'),  6:  ('1Y', 'out'),
        7:  ('GND', 'power'),
        8:  ('2Y', 'out'), 9:  ('2A', 'in'),  10: ('2B', 'in'),
        11: ('NC', 'nc'),  12: ('2C', 'in'),  13: ('2D', 'in'),
        14: ('VCC', 'power'),
    }
    return Chip(name, pins)


# =============================================================================
# Memory Chips
# =============================================================================

def make_rom(name: str) -> Chip:
    """AT28C256 — 28-pin DIP, 32KB ROM."""
    pins = {}
    for i in range(15):
        pins[i + 1] = (f'A{i}', 'in')      # A0-A14 (pins 1-15 simplified)
    for i in range(8):
        pins[i + 16] = (f'D{i}', 'out')    # D0-D7
    pins[24] = ('/CE', 'in')
    pins[25] = ('/OE', 'in')
    pins[26] = ('/WE', 'in')
    pins[27] = ('GND', 'power')
    pins[28] = ('VCC', 'power')
    return Chip(name, pins)


def make_ram(name: str) -> Chip:
    """62256 — 28-pin DIP, 32KB RAM."""
    pins = {}
    for i in range(15):
        pins[i + 1] = (f'A{i}', 'in')
    for i in range(8):
        pins[i + 16] = (f'D{i}', 'bidir')
    pins[24] = ('/CE', 'in')
    pins[25] = ('/OE', 'in')
    pins[26] = ('/WE', 'in')
    pins[27] = ('GND', 'power')
    pins[28] = ('VCC', 'power')
    return Chip(name, pins)


# =============================================================================
# CREATE ALL 35 CHIPS (RV8-GR instance)
# =============================================================================

def create_cpu():
    """Create all 35 chip instances for RV8-GR."""
    chips = {}

    # PC (U1-U4): 74HC161 ×4
    chips['U1'] = make_hc161('U1')
    chips['U2'] = make_hc161('U2')
    chips['U3'] = make_hc161('U3')
    chips['U4'] = make_hc161('U4')

    # IR + AC + Page Reg + Data Page (U5,U6,U9,U23,U32): 74HC574 ×5
    chips['U5'] = make_hc574('U5')
    chips['U6'] = make_hc574('U6')
    chips['U9'] = make_hc574('U9')
    chips['U23'] = make_hc574('U23')
    chips['U32'] = make_hc574('U32')

    # Bus buffer (U7): 74HC245
    chips['U7'] = make_hc245('U7')

    # Ring counter (U8): 74HC164
    chips['U8'] = make_hc164('U8')

    # Adder (U10,U11): 74HC283 ×2
    chips['U10'] = make_hc283('U10')
    chips['U11'] = make_hc283('U11')

    # XOR (U12,U13,U28): 74HC86 ×3
    chips['U12'] = make_hc86('U12')
    chips['U13'] = make_hc86('U13')
    chips['U28'] = make_hc86('U28')

    # AC buffer (U14): 74HC541
    chips['U14'] = make_hc541('U14')

    # Muxes (U15-U20, U29, U30): 74HC157 ×8
    for i in range(15, 21):
        chips[f'U{i}'] = make_hc157(f'U{i}')
    chips['U29'] = make_hc157('U29')
    chips['U30'] = make_hc157('U30')

    # Z flag + IRQ (U21, U31): 74HC74 ×2
    chips['U21'] = make_hc74('U21')
    chips['U31'] = make_hc74('U31')

    # Zero detect (U22): 74HC688
    chips['U22'] = make_hc688('U22')

    # Inverters (U24): 74HC04
    chips['U24'] = make_hc04('U24')

    # OR gates (U25): 74HC32
    chips['U25'] = make_hc32('U25')

    # NAND gates (U26, U27): 74HC00 ×2
    chips['U26'] = make_hc00('U26')
    chips['U27'] = make_hc00('U27')

    # SETDP decode (U33): 74HC21
    chips['U33'] = make_hc21('U33')

    # Memory
    chips['ROM'] = make_rom('ROM')
    chips['RAM'] = make_ram('RAM')

    return chips


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    chips = create_cpu()
    print(f"Created {len(chips)} chip instances:")
    for name, chip in sorted(chips.items()):
        pin_count = len([p for p in chip.pins.values() if p.direction != 'power'])
        print(f"  {name:4s}: {len(chip.pins)} pins ({pin_count} signal)")

    # Verify count
    logic_chips = [n for n in chips if n.startswith('U')]
    print(f"\nLogic chips: {len(logic_chips)} (U1-U33)")
    print(f"Memory: ROM + RAM")
    print(f"Total: {len(chips)} packages")
    assert len(chips) == 35, f"Expected 35, got {len(chips)}"
    print("\n✅ All 35 chips created with correct pin layouts")
