"""Lab 11: Page Register — SETPG and {PG, IRL} jump target formation."""

import sys

print("Lab 11: Page Register")
print("=" * 40)


def setpg(page_value: int) -> int:
    """U23 latches IBUS on PG_CLK rising edge."""
    return page_value & 0xFF


def jump_target(page_reg: int, ir_low: int) -> int:
    """PC new value for J/BEQ/BNE."""
    return ((page_reg & 0xFF) << 8) | (ir_low & 0xFF)


tests = [
    ("SETPG $10, J $00", 0x10, 0x00, 0x1000),
    ("SETPG $00, J $00", 0x00, 0x00, 0x0000),
    ("SETPG $FF, J $FF", 0xFF, 0xFF, 0xFFFF),
    ("SETPG $AA, J $55", 0xAA, 0x55, 0xAA55),
]

errors = 0
for desc, pg_val, ir_low, expected in tests:
    pg = setpg(pg_val)
    pc = jump_target(pg, ir_low)
    ok = pc == expected
    print(f"  [{'OK' if ok else 'FAIL'}] {desc} -> PC=${pc:04X}")
    if not ok:
        errors += 1

print()
if errors:
    print(f"Lab 11 FAILED ({errors} errors)")
    sys.exit(1)

print("Lab 11 PASSED")
