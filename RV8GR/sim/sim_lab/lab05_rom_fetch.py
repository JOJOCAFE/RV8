"""
Lab 05: ROM Fetch — ROM (AT28C256) + U7 (74HC245)

Wiring:
  ROM A[14:0] ← ABUS
  ROM /CE ← 0 (enabled for test)
  ROM /OE ← 0
  Physical U7: A-side=IBUS, B-side=DBUS, DIR=0 means B→A = DBUS→IBUS
  Local chip model has legacy inverted DIR semantics, so the script compensates.
  U7 /OE ← 0 (enabled)

Test: set address, read ROM data through U7 to IBUS
"""
import sys; sys.path.insert(0, '..')
from chips import MEM_AT28C256, TTL_74hc245

ROM = MEM_AT28C256('ROM')
U7 = TTL_74hc245('U7')

# Pre-load ROM
ROM._data[0x0000] = 0x30  # LI
ROM._data[0x0001] = 0x42  # $42
ROM._data[0x0002] = 0x10  # ADDI
ROM._data[0x0003] = 0x05  # $05
ROM._data[0x1000] = 0xAB  # at $1000 (offset $1000 in ROM)

def fetch(addr):
    """Set address, read ROM→U7→IBUS."""
    # Set ROM address
    for i in range(15): ROM.set(i+1, (addr>>i)&1)
    ROM.set(24, 0); ROM.set(25, 0)  # /CE=0, /OE=0
    ROM.update()

    # Physical wiring: ROM DBUS → U7 B-side, U7 A-side → IBUS.
    # Legacy TTL_74hc245 model drives B→A when DIR=1, so set 1 here to
    # represent physical DIR=0 read behavior.
    for i in range(8): U7.set(18-i, ROM.get(16+i))
    U7.set(1, 1)   # model B→A == physical DIR=0 read
    U7.set(19, 0)  # /OE=0
    U7.update()

    # Read IBUS from physical U7 A-side
    return sum(U7.get(2+i)<<i for i in range(8))

# Test: (address, expected_data)
TEST_VECTORS = [
    (0x0000, 0x30),
    (0x0001, 0x42),
    (0x0002, 0x10),
    (0x0003, 0x05),
    (0x1000, 0xAB),
]

if __name__ == '__main__':
    print("Lab 05: ROM Fetch (ROM + U7)")
    print("-" * 40)

    for addr, exp in TEST_VECTORS:
        data = fetch(addr)
        status = "✅" if data == exp else "❌"
        print(f"  ROM[${addr:04X}] → IBUS = ${data:02X}  {status}")
        assert data == exp

    print("\n✅ Lab 05 PASS: ROM fetch through U7 to IBUS")
