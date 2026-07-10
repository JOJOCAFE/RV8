"""Lab 13: Full System — boot init, ALU/branch, RAM, page jump, stability programs."""

import sys
sys.path.insert(0, '..')

from chip_sim import CPUSim


def run_program(program: bytes, clocks: int = 200) -> CPUSim:
    sim = CPUSim()
    sim.load_rom(program)
    for _ in range(clocks):
        sim.step()
    return sim


def padded(pairs, size=0x2000):
    data = bytearray([0x00] * size)
    for addr, value in pairs:
        data[addr] = value & 0xFF
    return bytes(data)


def check(name, condition, detail):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    if not condition:
        raise AssertionError(name)


print("Lab 13: Full System")
print("=" * 40)

# Test 1: lab full-path ROM with official boot init and branch pass marker.
program = padded([
    (0x0000, 0x40), (0x0001, 0x80),  # SETDP $80
    (0x0002, 0x20), (0x0003, 0x00),  # SETPG $00
    (0x0004, 0x30), (0x0005, 0x00),  # LI $00
    (0x0006, 0x30), (0x0007, 0x10),  # LI $10
    (0x0008, 0x10), (0x0009, 0x05),  # ADDI $05 -> $15
    (0x000A, 0x90), (0x000B, 0x15),  # SUBI $15 -> $00, Z=1
    (0x000C, 0x02), (0x000D, 0x12),  # BEQ $12
    (0x000E, 0x01), (0x000F, 0x14),  # fail jump
    (0x0012, 0x30), (0x0013, 0xAA),  # pass marker
    (0x0014, 0x01), (0x0015, 0x14),  # halt loop
])
sim = run_program(program, 90)
check("boot + ALU + BEQ path", sim.ac == 0xAA, f"AC=${sim.ac:02X}, PC=${sim.pc:04X}")

# Test 5 from the lab: RAM write/read and branch to $BB marker.
program = padded([
    (0x0000, 0x40), (0x0001, 0x80),
    (0x0002, 0x20), (0x0003, 0x00),
    (0x0004, 0x30), (0x0005, 0x55),
    (0x0006, 0x04), (0x0007, 0x10),
    (0x0008, 0x30), (0x0009, 0x00),
    (0x000A, 0x38), (0x000B, 0x10),
    (0x000C, 0x90), (0x000D, 0x55),
    (0x000E, 0x02), (0x000F, 0x12),
    (0x0010, 0x01), (0x0011, 0x10),
    (0x0012, 0x30), (0x0013, 0xBB),
    (0x0014, 0x01), (0x0015, 0x14),
])
sim = run_program(program, 120)
check("RAM read/write validation", sim.ac == 0xBB and sim.chips['RAM']._data[0x10] == 0x55,
      f"AC=${sim.ac:02X}, RAM[$8010]=${sim.chips['RAM']._data[0x10]:02X}")

# Test 6 from the lab: SETPG cross-page jump and return to page 0.
program = padded([
    (0x0000, 0x20), (0x0001, 0x10),
    (0x0002, 0x01), (0x0003, 0x00),
    (0x1000, 0x20), (0x1001, 0x00),
    (0x1002, 0x01), (0x1003, 0x06),
    (0x0006, 0x30), (0x0007, 0xCC),
    (0x0008, 0x01), (0x0009, 0x08),
], size=0x4000)
sim = run_program(program, 80)
check("page register jump validation", sim.ac == 0xCC, f"AC=${sim.ac:02X}, PC=${sim.pc:04X}")

# Long-run counter smoke: include SETPG $00 before the loop, matching the lab text.
program = padded([
    (0x0000, 0x30), (0x0001, 0x00),
    (0x0002, 0x20), (0x0003, 0x00),
    (0x0004, 0x10), (0x0005, 0x01),
    (0x0006, 0x01), (0x0007, 0x04),
])
sim = run_program(program, 180)
check("counter loop stability smoke", sim.pc in (0x0004, 0x0005, 0x0006, 0x0007, 0x0008),
      f"AC=${sim.ac:02X}, PC=${sim.pc:04X}")

print()
print("Lab 13 PASSED")
