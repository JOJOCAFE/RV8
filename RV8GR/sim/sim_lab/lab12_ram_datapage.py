"""Lab 12: RAM + Data Page — tests SB/LB with page register"""
import sys

print("Lab 12: RAM + Data Page")
print("=" * 40)

# Simulate RAM read/write with data page register
ram = [0] * 32768  # 32KB RAM at $8000-$FFFF

def ram_write(data_page, addr_lo, value):
    """Write to RAM using data page + low address"""
    full_addr = (data_page << 8) | addr_lo
    if full_addr >= 0x8000:  # RAM region only (A15=1)
        ram[full_addr - 0x8000] = value & 0xFF
        return True
    return False  # ROM region, can't write

def ram_read(data_page, addr_lo):
    """Read from RAM using data page + low address"""
    full_addr = (data_page << 8) | addr_lo
    if full_addr >= 0x8000:
        return ram[full_addr - 0x8000]
    return None  # Would read ROM

errors = 0

# Test 1: Write/read page $80 (default data page = RAM)
print("  Test 1: SB/LB page $80")
ram_write(0x80, 0x03, 0xAA)
val = ram_read(0x80, 0x03)
if val == 0xAA:
    print(f"    OK: RAM[$8003] = ${val:02X}")
else:
    print(f"    FAIL: RAM[$8003] = ${val:02X}, expected $AA")
    errors += 1

# Test 2: Write/read page $90
print("  Test 2: SB/LB page $90")
ram_write(0x90, 0x00, 0x55)
val = ram_read(0x90, 0x00)
if val == 0x55:
    print(f"    OK: RAM[$9000] = ${val:02X}")
else:
    print(f"    FAIL: RAM[$9000] = ${val:02X}, expected $55")
    errors += 1

# Test 3: Pages don't interfere
print("  Test 3: Pages independent")
val_p80 = ram_read(0x80, 0x03)
val_p90 = ram_read(0x90, 0x00)
if val_p80 == 0xAA and val_p90 == 0x55:
    print(f"    OK: page $80[$03]=${val_p80:02X}, page $90[$00]=${val_p90:02X}")
else:
    print(f"    FAIL: cross-page corruption")
    errors += 1

# Test 4: ROM region blocked
print("  Test 4: Write to ROM region rejected")
result = ram_write(0x00, 0x00, 0xFF)
if not result:
    print(f"    OK: Write to $0000 rejected (ROM)")
else:
    print(f"    FAIL: Should not write to ROM region")
    errors += 1

print()
if errors == 0:
    print("Lab 12 PASSED")
else:
    print(f"Lab 12 FAILED ({errors} errors)")
    sys.exit(1)
