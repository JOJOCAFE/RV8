"""DIP chip behavior models used by RV8GR-V2 and future TTL projects."""

from __future__ import annotations

from .core import Chip, Delay, Z, bit, pins_from
from .catalog import CATALOG_PARTS, MEMORY_CATALOG_PARTS, create_catalog_chip


class HC04(Chip):
    part = "74HC04"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1Y", "out"), 3: ("2A", "in"), 4: ("2Y", "out"),
                5: ("3A", "in"), 6: ("3Y", "out"), 7: ("GND", "power"),
                8: ("4Y", "out"), 9: ("4A", "in"), 10: ("5Y", "out"), 11: ("5A", "in"),
                12: ("6Y", "out"), 13: ("6A", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        for a, y in [(1, 2), (3, 4), (5, 6), (9, 8), (11, 10), (13, 12)]:
            self.output(y, 1 - bit(self.read(a)))


class HC00(Chip):
    part = "74HC00"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("1Y", "out"),
                4: ("2A", "in"), 5: ("2B", "in"), 6: ("2Y", "out"), 7: ("GND", "power"),
                8: ("3Y", "out"), 9: ("3A", "in"), 10: ("3B", "in"),
                11: ("4Y", "out"), 12: ("4A", "in"), 13: ("4B", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, 1 - (bit(self.read(a)) & bit(self.read(b))))


class HC32(Chip):
    part = "74HC32"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("1Y", "out"),
                4: ("2A", "in"), 5: ("2B", "in"), 6: ("2Y", "out"), 7: ("GND", "power"),
                8: ("3Y", "out"), 9: ("3A", "in"), 10: ("3B", "in"),
                11: ("4Y", "out"), 12: ("4A", "in"), 13: ("4B", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, bit(self.read(a)) | bit(self.read(b)))


class HC86(Chip):
    part = "74HC86"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("1Y", "out"),
                4: ("2A", "in"), 5: ("2B", "in"), 6: ("2Y", "out"), 7: ("GND", "power"),
                8: ("3Y", "out"), 9: ("3A", "in"), 10: ("3B", "in"),
                11: ("4Y", "out"), 12: ("4A", "in"), 13: ("4B", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(15))

    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, bit(self.read(a)) ^ bit(self.read(b)))


class HC21(Chip):
    part = "74HC21"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("NC", "nc"),
                4: ("1C", "in"), 5: ("1D", "in"), 6: ("1Y", "out"), 7: ("GND", "power"),
                8: ("2Y", "out"), 9: ("2A", "in"), 10: ("2B", "in"),
                11: ("NC2", "nc"), 12: ("2C", "in"), 13: ("2D", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(15))

    def update(self) -> None:
        self.output(6, bit(self.read(1)) & bit(self.read(2)) & bit(self.read(4)) & bit(self.read(5)))
        self.output(8, bit(self.read(9)) & bit(self.read(10)) & bit(self.read(12)) & bit(self.read(13)))


class HC157(Chip):
    part = "74HC157"

    def __init__(self, name: str):
        pins = {1: ("SEL", "in"), 2: ("1A", "in"), 3: ("1B", "in"), 4: ("1Y", "out"),
                5: ("2A", "in"), 6: ("2B", "in"), 7: ("2Y", "out"), 8: ("GND", "power"),
                9: ("3Y", "out"), 10: ("3B", "in"), 11: ("3A", "in"), 12: ("4Y", "out"),
                13: ("4B", "in"), 14: ("4A", "in"), 15: ("/E", "in"), 16: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(18))

    def update(self) -> None:
        if bit(self.read(15)):
            for y in [4, 7, 9, 12]:
                self.output(y, 0)
            return
        sel = bit(self.read(1))
        for a, b, y in [(2, 3, 4), (5, 6, 7), (11, 10, 9), (14, 13, 12)]:
            self.output(y, bit(self.read(b if sel else a)))


class HC283(Chip):
    part = "74HC283"

    def __init__(self, name: str):
        pins = {1: ("S1", "out"), 2: ("B1", "in"), 3: ("A1", "in"), 4: ("S0", "out"),
                5: ("A0", "in"), 6: ("B0", "in"), 7: ("Cin", "in"), 8: ("GND", "power"),
                9: ("Cout", "out"), 10: ("S3", "out"), 11: ("B3", "in"), 12: ("A3", "in"),
                13: ("S2", "out"), 14: ("A2", "in"), 15: ("B2", "in"), 16: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(35))

    def update(self) -> None:
        a = byte_from_pins(self, [5, 3, 14, 12])
        b = byte_from_pins(self, [6, 2, 15, 11])
        r = a + b + bit(self.read(7))
        write_pins(self, [4, 1, 13, 10], r)
        self.output(9, (r >> 4) & 1)


class HC688(Chip):
    part = "74HC688"

    def __init__(self, name: str):
        pins = {1: ("/OE", "in"), 2: ("P0", "in"), 3: ("Q0", "in"), 4: ("P1", "in"),
                5: ("Q1", "in"), 6: ("P2", "in"), 7: ("Q2", "in"), 8: ("P3", "in"),
                9: ("Q3", "in"), 10: ("GND", "power"), 11: ("Q4", "in"), 12: ("P4", "in"),
                13: ("Q5", "in"), 14: ("P5", "in"), 15: ("Q6", "in"), 16: ("P6", "in"),
                17: ("Q7", "in"), 18: ("P7", "in"), 19: ("/P=Q", "out"), 20: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(30))

    def update(self) -> None:
        if bit(self.read(1)):
            self.output(19, 1)
            return
        p = byte_from_pins(self, [2, 4, 6, 8, 12, 14, 16, 18])
        q = byte_from_pins(self, [3, 5, 7, 9, 11, 13, 15, 17])
        self.output(19, 0 if p == q else 1)


class HC541(Chip):
    part = "74HC541"

    def __init__(self, name: str):
        pins = {1: ("/OE1", "in"), 19: ("/OE2", "in"), 10: ("GND", "power"), 20: ("VCC", "power")}
        for i in range(8):
            pins[2 + i] = (f"A{i + 1}", "in")
            pins[18 - i] = (f"Y{i + 1}", "out")
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        enabled = not bit(self.read(1)) and not bit(self.read(19))
        for i in range(8):
            self.output(18 - i, bit(self.read(2 + i)) if enabled else Z)


class HC245(Chip):
    part = "74HC245"

    def __init__(self, name: str):
        pins = {1: ("DIR", "in"), 19: ("/OE", "in"), 10: ("GND", "power"), 20: ("VCC", "power")}
        for i in range(8):
            pins[2 + i] = (f"A{i + 1}", "bidir")
            pins[18 - i] = (f"B{i + 1}", "bidir")
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        if bit(self.read(19)):
            for i in range(8):
                self.output(2 + i, Z)
                self.output(18 - i, Z)
            return
        a_to_b = bit(self.read(1)) == 1
        for i in range(8):
            a_pin = 2 + i
            b_pin = 18 - i
            if a_to_b:
                self.output(a_pin, Z)
                self.output(b_pin, bit(self.read(a_pin)))
            else:
                self.output(b_pin, Z)
                self.output(a_pin, bit(self.read(b_pin)))


class HC574(Chip):
    part = "74HC574"

    def __init__(self, name: str):
        pins = {1: ("/OE", "in"), 11: ("CLK", "in"), 10: ("GND", "power"), 20: ("VCC", "power")}
        for i in range(8):
            pins[2 + i] = (f"D{i + 1}", "in")
            pins[19 - i] = (f"Q{i + 1}", "out")
        super().__init__(name, pins_from(pins), Delay(20))
        self._reg = [0] * 8

    def clock_edge(self, pin: int | str | None = None) -> None:
        self._reg = [bit(self.read(2 + i)) for i in range(8)]
        self.update()

    def update(self) -> None:
        enabled = not bit(self.read(1))
        for i in range(8):
            self.output(19 - i, self._reg[i] if enabled else Z)


class HC161(Chip):
    part = "74HC161"

    def __init__(self, name: str):
        pins = {1: ("/CLR", "in"), 2: ("CLK", "in"), 3: ("D0", "in"), 4: ("D1", "in"),
                5: ("D2", "in"), 6: ("D3", "in"), 7: ("ENP", "in"), 8: ("GND", "power"),
                9: ("/LD", "in"), 10: ("ENT", "in"), 11: ("QD", "out"), 12: ("QC", "out"),
                13: ("QB", "out"), 14: ("QA", "out"), 15: ("RCO", "out"), 16: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(22))
        self._count = 0

    def clock_edge(self, pin: int | str | None = None) -> None:
        if not bit(self.read(1)):
            self._count = 0
        elif not bit(self.read(9)):
            self._count = byte_from_pins(self, [3, 4, 5, 6])
        elif bit(self.read(7)) and bit(self.read(10)):
            self._count = (self._count + 1) & 0xF
        self.update()

    def update(self) -> None:
        if not bit(self.read(1)):
            self._count = 0
        write_pins(self, [14, 13, 12, 11], self._count)
        self.output(15, 1 if self._count == 0xF and bit(self.read(10)) else 0)


class HC164(Chip):
    part = "74HC164"

    def __init__(self, name: str):
        pins = {1: ("A", "in"), 2: ("B", "in"), 3: ("Q0", "out"), 4: ("Q1", "out"),
                5: ("Q2", "out"), 6: ("Q3", "out"), 7: ("GND", "power"), 8: ("CLK", "in"),
                9: ("/CLR", "in"), 10: ("Q4", "out"), 11: ("Q5", "out"), 12: ("Q6", "out"),
                13: ("Q7", "out"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(20))
        self._sr = [0] * 8
        self._q_pins = [3, 4, 5, 6, 10, 11, 12, 13]

    def clock_edge(self, pin: int | str | None = None) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        else:
            self._sr = [bit(self.read(1)) & bit(self.read(2))] + self._sr[:7]
        self.update()

    def update(self) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        for i, pin in enumerate(self._q_pins):
            self.output(pin, self._sr[i])


class HC74(Chip):
    part = "74HC74"

    def __init__(self, name: str):
        pins = {1: ("/CLR1", "in"), 2: ("D1", "in"), 3: ("CLK1", "in"), 4: ("/PR1", "in"),
                5: ("Q1", "out"), 6: ("/Q1", "out"), 7: ("GND", "power"),
                8: ("/Q2", "out"), 9: ("Q2", "out"), 10: ("/PR2", "in"), 11: ("CLK2", "in"),
                12: ("D2", "in"), 13: ("/CLR2", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(20))
        self._q = [0, 0]

    def clock_edge(self, pin: int | str | None = None) -> None:
        blocks = [0, 1]
        if pin is not None:
            number = self.pin_number(pin)
            blocks = [0] if number == 3 else ([1] if number == 11 else [])
        for block in blocks:
            if block == 0:
                if not bit(self.read(1)):
                    self._q[0] = 0
                elif not bit(self.read(4)):
                    self._q[0] = 1
                else:
                    self._q[0] = bit(self.read(2))
            else:
                if not bit(self.read(13)):
                    self._q[1] = 0
                elif not bit(self.read(10)):
                    self._q[1] = 1
                else:
                    self._q[1] = bit(self.read(12))
        self.update()

    def update(self) -> None:
        if not bit(self.read(1)):
            self._q[0] = 0
        elif not bit(self.read(4)):
            self._q[0] = 1
        if not bit(self.read(13)):
            self._q[1] = 0
        elif not bit(self.read(10)):
            self._q[1] = 1
        self.output(5, self._q[0])
        self.output(6, 1 - self._q[0])
        self.output(9, self._q[1])
        self.output(8, 1 - self._q[1])


class AT28C256(Chip):
    part = "AT28C256"

    def __init__(self, name: str):
        pins = memory_28_pin_defs("bidir")
        super().__init__(name, pins_from(pins), Delay(70))
        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        if selected and bit(self.read("/OE")) and not bit(self.read("/WE")):
            self.data[memory_address(self)] = byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and not bit(self.read("/OE")) and bit(self.read("/WE"))
        if not read_enabled:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)
            return
        write_pins(self, MEMORY_DQ_PINS, self.data[memory_address(self)])


class SRAM62256(Chip):
    part = "62256"

    def __init__(self, name: str):
        pins = memory_28_pin_defs("bidir")
        super().__init__(name, pins_from(pins), Delay(70))
        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        addr = memory_address(self)
        if selected and not bit(self.read("/WE")):
            self.data[addr] = byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and bit(self.read("/WE")) and not bit(self.read("/OE"))
        if read_enabled:
            write_pins(self, MEMORY_DQ_PINS, self.data[addr])
        else:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)


MEMORY_ADDR_PINS = {
    0: 10,
    1: 9,
    2: 8,
    3: 7,
    4: 6,
    5: 5,
    6: 4,
    7: 3,
    8: 25,
    9: 24,
    10: 21,
    11: 23,
    12: 2,
    13: 26,
    14: 1,
}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


def memory_28_pin_defs(data_direction: str) -> dict[int, tuple[str, str]]:
    pins = {
        14: ("GND", "power"),
        20: ("/CE", "in"),
        22: ("/OE", "in"),
        27: ("/WE", "in"),
        28: ("VCC", "power"),
    }
    for bit_index, pin in MEMORY_ADDR_PINS.items():
        pins[pin] = (f"A{bit_index}", "in")
    for bit_index, pin in enumerate(MEMORY_DQ_PINS):
        pins[pin] = (f"I/O{bit_index}", data_direction)
    return pins


def memory_address(chip: Chip) -> int:
    value = 0
    for bit_index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << bit_index
    return value


def byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for i, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << i
    return value


def write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for i, pin in enumerate(pins):
        chip.output(pin, (value >> i) & 1)


CHIP_FACTORIES = {
    "74HC00": HC00,
    "74HC04": HC04,
    "74HC21": HC21,
    "74HC32": HC32,
    "74HC74": HC74,
    "74HC86": HC86,
    "74HC157": HC157,
    "74HC161": HC161,
    "74HC164": HC164,
    "74HC245": HC245,
    "74HC283": HC283,
    "74HC541": HC541,
    "74HC574": HC574,
    "74HC688": HC688,
    "AT28C256": AT28C256,
    "28C256": AT28C256,
    "62256": SRAM62256,
}
for _part in sorted(CATALOG_PARTS):
    CHIP_FACTORIES[_part] = lambda name, part=_part: create_catalog_chip(part, name)
for _part in sorted(MEMORY_CATALOG_PARTS):
    CHIP_FACTORIES[_part] = lambda name, part=_part: create_catalog_chip(part, name)


def create_chip(part: str, name: str) -> Chip:
    key = part.upper().replace("-", "")
    if key in CATALOG_PARTS or key in MEMORY_CATALOG_PARTS:
        return create_catalog_chip(key, name)
    aliases = {
        "74HC00": "74HC00",
        "74HC04": "74HC04",
        "74HC21": "74HC21",
        "74HC32": "74HC32",
        "74HC74": "74HC74",
        "74HC86": "74HC86",
        "74HC157": "74HC157",
        "74HC161": "74HC161",
        "74HC164": "74HC164",
        "74HC245": "74HC245",
        "74HC283": "74HC283",
        "74HC541": "74HC541",
        "74HC574": "74HC574",
        "74HC688": "74HC688",
        "AT28C256": "AT28C256",
        "28C256": "28C256",
        "62256": "62256",
    }
    factory_key = aliases.get(key)
    if not factory_key:
        raise KeyError(f"unsupported chip part {part!r}")
    return CHIP_FACTORIES[factory_key](name)
