"""RV8-GR Chip Simulator — Probe and Test Tools."""

import sys
sys.path.insert(0, '.')
from chips import Chip, create_cpu
from chips.behaviors import attach_behaviors


# =============================================================================
# PROBE — Read chip pins like LED
# =============================================================================

class Probe:
    """Attach to chip pin(s) and read like LED indicator."""

    def __init__(self, chips: dict):
        self.chips = chips

    def pin(self, chip_name: str, pin_num: int) -> int:
        """Read single pin (0 or 1)."""
        return self.chips[chip_name].get(pin_num)

    def byte(self, chip_name: str, pins: list) -> int:
        """Read multiple pins as byte (LSB first)."""
        val = 0
        for i, p in enumerate(pins):
            val |= self.chips[chip_name].get(p) << i
        return val

    def hc574_q(self, chip_name: str) -> int:
        """Read 74HC574 Q outputs as byte. Q1(pin19)=bit0 ... Q8(pin12)=bit7."""
        return self.byte(chip_name, [19, 18, 17, 16, 15, 14, 13, 12])

    def hc161_q(self, chip_name: str) -> int:
        """Read 74HC161 Q outputs as nibble. QA(pin14)=bit0 ... QD(pin11)=bit3."""
        return self.byte(chip_name, [14, 13, 12, 11])

    def hc164_q(self, chip_name: str) -> int:
        """Read 74HC164 Q outputs. Q0(pin3)=bit0 ... Q7(pin13)=bit7."""
        return self.byte(chip_name, [3, 4, 5, 6, 10, 11, 12, 13])

    def show(self, chip_name: str, pin_num: int, label: str = ""):
        """Print pin state like LED."""
        v = self.pin(chip_name, pin_num)
        name = self.chips[chip_name].pins[pin_num].name
        lbl = f" ({label})" if label else ""
        print(f"  💡 {chip_name}-{pin_num} ({name}){lbl} = {'HIGH ●' if v else 'LOW  ○'}")


# =============================================================================
# DIP SWITCH — Set chip input pins
# =============================================================================

class DipSwitch:
    """Set chip input pins like DIP switch or signal generator."""

    def __init__(self, chips: dict):
        self.chips = chips

    def pin(self, chip_name: str, pin_num: int, value: int):
        """Set single pin."""
        self.chips[chip_name].set(pin_num, value)

    def byte(self, chip_name: str, pins: list, value: int):
        """Set multiple pins from byte (LSB first)."""
        for i, p in enumerate(pins):
            self.chips[chip_name].set(p, (value >> i) & 1)

    def hc574_d(self, chip_name: str, value: int):
        """Set 74HC574 D inputs. D1(pin2)=bit0 ... D8(pin9)=bit7."""
        self.byte(chip_name, [2, 3, 4, 5, 6, 7, 8, 9], value)

    def hc161_d(self, chip_name: str, value: int):
        """Set 74HC161 D inputs. D0(pin3)=bit0 ... D3(pin6)=bit3."""
        self.byte(chip_name, [3, 4, 5, 6], value)

    def hc283_a(self, chip_name: str, value: int):
        """Set 74HC283 A inputs. A0(pin5), A1(pin3), A2(pin14), A3(pin12)."""
        self.byte(chip_name, [5, 3, 14, 12], value)

    def hc283_b(self, chip_name: str, value: int):
        """Set 74HC283 B inputs. B0(pin6), B1(pin2), B2(pin15), B3(pin11)."""
        self.byte(chip_name, [6, 2, 15, 11], value)


# =============================================================================
# TEST ALL CHIP BEHAVIORS
# =============================================================================

def test_hc04():
    """Test 74HC04 (U24): all 6 inverters."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for gate, (a, y) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)], 1):
        sw.pin('U24', a, 0); chips['U24'].update()
        assert pr.pin('U24', y) == 1, f"Gate {gate}: NOT(0) should be 1"
        sw.pin('U24', a, 1); chips['U24'].update()
        assert pr.pin('U24', y) == 0, f"Gate {gate}: NOT(1) should be 0"
    print("  ✅ HC04 (U24): 6 inverters OK")


def test_hc00():
    """Test 74HC00 (U26, U27): all 4 NAND gates."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for name in ['U26', 'U27']:
        gates = [(1,2,3), (4,5,6), (9,10,8), (12,13,11)]
        for g, (a, b, y) in enumerate(gates, 1):
            for va, vb, expected in [(0,0,1),(0,1,1),(1,0,1),(1,1,0)]:
                sw.pin(name, a, va); sw.pin(name, b, vb)
                chips[name].update()
                assert pr.pin(name, y) == expected, f"{name} gate{g} NAND({va},{vb})≠{expected}"
    print("  ✅ HC00 (U26,U27): 8 NAND gates OK")


def test_hc32():
    """Test 74HC32 (U25): all 4 OR gates."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    gates = [(1,2,3), (4,5,6), (9,10,8), (11,12,13)]
    for g, (a, b, y) in enumerate(gates, 1):
        for va, vb in [(0,0),(0,1),(1,0),(1,1)]:
            sw.pin('U25', a, va); sw.pin('U25', b, vb)
            chips['U25'].update()
            expected = va | vb
            assert pr.pin('U25', y) == expected, f"Gate{g} OR({va},{vb})≠{expected}"
    print("  ✅ HC32 (U25): 4 OR gates OK")


def test_hc86():
    """Test 74HC86 (U12,U13,U28): all XOR gates."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for name in ['U12', 'U13', 'U28']:
        gates = [(1,2,3), (4,5,6), (9,10,8), (12,13,11)]
        for g, (a, b, y) in enumerate(gates, 1):
            for va, vb in [(0,0),(0,1),(1,0),(1,1)]:
                sw.pin(name, a, va); sw.pin(name, b, vb)
                chips[name].update()
                expected = va ^ vb
                assert pr.pin(name, y) == expected, f"{name} XOR({va},{vb})≠{expected}"
    print("  ✅ HC86 (U12,U13,U28): 12 XOR gates OK")


def test_hc21():
    """Test 74HC21 (U33): dual 4-input AND."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    # Gate 1: pins 1,2,4,5 → pin 6
    for a, b, c, d in [(1,1,1,1),(1,1,1,0),(0,1,1,1),(1,0,1,1)]:
        sw.pin('U33', 1, a); sw.pin('U33', 2, b)
        sw.pin('U33', 4, c); sw.pin('U33', 5, d)
        chips['U33'].update()
        expected = a & b & c & d
        assert pr.pin('U33', 6) == expected, f"AND({a},{b},{c},{d})≠{expected}"
    print("  ✅ HC21 (U33): 4-input AND OK")


def test_hc157():
    """Test 74HC157 (U15): quad mux."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    sw.pin('U15', 15, 0)  # /E=0 (enabled)

    # Gate 1: A=pin2, B=pin3, Y=pin4
    sw.pin('U15', 2, 1); sw.pin('U15', 3, 0)
    sw.pin('U15', 1, 0); chips['U15'].update()  # SEL=0 → A
    assert pr.pin('U15', 4) == 1, "SEL=0 should select A"

    sw.pin('U15', 1, 1); chips['U15'].update()  # SEL=1 → B
    assert pr.pin('U15', 4) == 0, "SEL=1 should select B"

    # Test /E=1 (disabled → output 0)
    sw.pin('U15', 15, 1); chips['U15'].update()
    assert pr.pin('U15', 4) == 0, "/E=1 should force output 0"
    print("  ✅ HC157 (U15): quad mux OK")


def test_hc283():
    """Test 74HC283 (U10,U11): 4-bit adder."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    test_cases = [(0,0,0, 0), (5,3,0, 8), (7,8,0, 15), (15,15,1, 31), (9,6,1, 16)]
    for a, b, cin, expected in test_cases:
        sw.hc283_a('U10', a); sw.hc283_b('U10', b)
        sw.pin('U10', 7, cin)
        chips['U10'].update()
        s = pr.byte('U10', [4, 1, 13, 10])
        cout = pr.pin('U10', 9)
        result = s | (cout << 4)
        assert result == expected, f"{a}+{b}+{cin}={result}, expected {expected}"
    print("  ✅ HC283 (U10): 4-bit adder OK")


def test_hc688():
    """Test 74HC688 (U22): 8-bit comparator."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    sw.pin('U22', 1, 0)  # /OE=0

    # P=Q=0 → /P=Q should be 0 (equal)
    for i in range(8):
        p_pins = [2, 4, 6, 8, 12, 14, 16, 18]
        q_pins = [3, 5, 7, 9, 11, 13, 15, 17]
        sw.pin('U22', p_pins[i], 0)
        sw.pin('U22', q_pins[i], 0)
    chips['U22'].update()
    assert pr.pin('U22', 19) == 0, "P==Q should give /P=Q=0"

    # Make P≠Q
    sw.pin('U22', 2, 1)  # P0=1, Q0=0
    chips['U22'].update()
    assert pr.pin('U22', 19) == 1, "P≠Q should give /P=Q=1"
    print("  ✅ HC688 (U22): 8-bit comparator OK")


def test_hc541():
    """Test 74HC541 (U14): octal buffer."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    # Set A inputs = $A5
    for i in range(8):
        sw.pin('U14', 2 + i, (0xA5 >> i) & 1)

    # Enable
    sw.pin('U14', 1, 0); sw.pin('U14', 19, 0)
    chips['U14'].update()
    y = pr.byte('U14', [18, 17, 16, 15, 14, 13, 12, 11])
    assert y == 0xA5, f"Buffer output ${y:02X}, expected $A5"

    # Disable
    sw.pin('U14', 1, 1)
    chips['U14'].update()
    y = pr.byte('U14', [18, 17, 16, 15, 14, 13, 12, 11])
    assert y == 0, "Disabled buffer should output 0"
    print("  ✅ HC541 (U14): octal buffer OK")


def test_hc574():
    """Test 74HC574 (U5,U6,U9,U23,U32): D latch."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for name in ['U5', 'U6', 'U9', 'U23', 'U32']:
        sw.pin(name, 1, 0)  # /OE=0
        sw.hc574_d(name, 0x5A)
        chips[name].clock_edge()
        q = pr.hc574_q(name)
        assert q == 0x5A, f"{name}: got ${q:02X}, expected $5A"

        # Change D, Q should NOT change until next edge
        sw.hc574_d(name, 0xFF)
        chips[name].update()
        q = pr.hc574_q(name)
        assert q == 0x5A, f"{name}: Q changed without clock edge!"

        # Clock again
        chips[name].clock_edge()
        q = pr.hc574_q(name)
        assert q == 0xFF, f"{name}: got ${q:02X} after 2nd edge"
    print("  ✅ HC574 (U5,U6,U9,U23,U32): D latch OK")


def test_hc161():
    """Test 74HC161 (U1-U4): counter."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for name in ['U1', 'U2', 'U3', 'U4']:
        # Clear
        sw.pin(name, 1, 0)  # /CLR=0
        chips[name].clock_edge()
        assert pr.hc161_q(name) == 0, f"{name} clear failed"

        # Count
        sw.pin(name, 1, 1); sw.pin(name, 9, 1)  # /CLR=1, /LD=1
        sw.pin(name, 7, 1); sw.pin(name, 10, 1)  # ENP=1, ENT=1
        chips[name].clock_edge()
        assert pr.hc161_q(name) == 1, f"{name} count to 1 failed"
        chips[name].clock_edge()
        assert pr.hc161_q(name) == 2, f"{name} count to 2 failed"

        # Load
        sw.pin(name, 9, 0)  # /LD=0
        sw.hc161_d(name, 0xA)
        chips[name].clock_edge()
        assert pr.hc161_q(name) == 0xA, f"{name} load failed"
    print("  ✅ HC161 (U1-U4): counter OK")


def test_hc164():
    """Test 74HC164 (U8): shift register."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    # Clear
    sw.pin('U8', 9, 0)
    chips['U8'].clock_edge()
    assert pr.hc164_q('U8') == 0, "Clear failed"

    # Shift in 1 (A=1, B=1)
    sw.pin('U8', 9, 1); sw.pin('U8', 1, 1); sw.pin('U8', 2, 1)
    chips['U8'].clock_edge()
    assert pr.pin('U8', 3) == 1, "Q0 should be 1 after shift"

    # Shift in 0 (A=0)
    sw.pin('U8', 1, 0)
    chips['U8'].clock_edge()
    assert pr.pin('U8', 3) == 0, "Q0 should be 0"
    assert pr.pin('U8', 4) == 1, "Q1 should be 1 (shifted)"
    print("  ✅ HC164 (U8): shift register OK")


def test_hc74():
    """Test 74HC74 (U21,U31): dual D flip-flop."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    for name in ['U21', 'U31']:
        # FF1: /CLR=1, /PR=1, D=1 → clock → Q=1
        sw.pin(name, 1, 1); sw.pin(name, 4, 1); sw.pin(name, 2, 1)
        chips[name].clock_edge()
        assert pr.pin(name, 5) == 1, f"{name} FF1 Q should be 1"
        assert pr.pin(name, 6) == 0, f"{name} FF1 /Q should be 0"

        # /CLR → Q=0
        sw.pin(name, 1, 0)
        chips[name].update()
        assert pr.pin(name, 5) == 0, f"{name} FF1 /CLR failed"

        # /PR → Q=1
        sw.pin(name, 1, 1); sw.pin(name, 4, 0)
        chips[name].update()
        assert pr.pin(name, 5) == 1, f"{name} FF1 /PR failed"
    print("  ✅ HC74 (U21,U31): D flip-flop OK")


def test_memory():
    """Test ROM and RAM."""
    chips = create_cpu(); attach_behaviors(chips)
    sw = DipSwitch(chips); pr = Probe(chips)

    # ROM: write data, then read
    chips['ROM']._data = bytearray(32768)
    chips['ROM']._data[0x0000] = 0x42
    chips['ROM']._data[0x1234] = 0xAB

    # Read ROM[0]: set addr=0, /CE=0, /OE=0
    for i in range(15): sw.pin('ROM', i+1, 0)
    sw.pin('ROM', 24, 0); sw.pin('ROM', 25, 0)
    chips['ROM'].update()
    d = pr.byte('ROM', [16,17,18,19,20,21,22,23])
    assert d == 0x42, f"ROM[0]=${d:02X}"

    # RAM: write then read
    chips['RAM']._data = bytearray(32768)
    # Write $77 to addr 5: set addr, data, /CE=0, /WE=0
    for i in range(15): sw.pin('RAM', i+1, (5>>i)&1)
    for i in range(8): sw.pin('RAM', 16+i, (0x77>>i)&1)
    sw.pin('RAM', 24, 0); sw.pin('RAM', 25, 1); sw.pin('RAM', 26, 0)  # /CE=0, /OE=1, /WE=0
    chips['RAM'].update()
    assert chips['RAM']._data[5] == 0x77, "RAM write failed"

    # Read back
    sw.pin('RAM', 26, 1); sw.pin('RAM', 25, 0)  # /WE=1, /OE=0
    chips['RAM'].update()
    d = pr.byte('RAM', [16,17,18,19,20,21,22,23])
    assert d == 0x77, f"RAM read=${d:02X}"
    print("  ✅ ROM + RAM: memory OK")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("RV8-GR Chip Behavior Test Suite")
    print("=" * 60)
    print()

    test_hc04()
    test_hc00()
    test_hc32()
    test_hc86()
    test_hc21()
    test_hc157()
    test_hc283()
    test_hc688()
    test_hc541()
    test_hc574()
    test_hc161()
    test_hc164()
    test_hc74()
    test_memory()

    print()
    print("=" * 60)
    print("ALL 14 CHIP TYPES VERIFIED ✅")
    print("=" * 60)
