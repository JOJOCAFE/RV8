"""Lab 14: IRQ + RV8-Bus — tests v1.0 polling IRQ latch.

36-package v1.0 behavior:
  - EI sets IE.
  - DI is an inert software marker.
  - /IRQ is active-low; U31 latches IRQ_FF on release/rising edge.
  - PC never auto-jumps to $FF00; IRQ_FF clears only by /RST.
"""
import sys

print("Lab 14: IRQ + RV8-Bus")
print("=" * 40)

# Simulate IRQ logic (U31: dual 74HC74) plus U33 gate-2 EI_decode.
ie_ff = 0   # Interrupt Enable flip-flop
irq_ff = 0  # IRQ pending flip-flop
pc = 0x0000

def ei_decode(opcode, t2=1):
    """U33 gate 2: T2 AND SRC AND /XOR_MODE AND /AC_WR."""
    src = (opcode >> 3) & 1
    xor_mode = (opcode >> 6) & 1
    ac_wr = (opcode >> 4) & 1
    return int(bool(t2 and src and (not xor_mode) and (not ac_wr)))

def clock_ie(opcode=0x08):
    global ie_ff
    if ei_decode(opcode):
        ie_ff = 1

def di():
    """DI has no v1.0 hardware effect."""

def irq_assert():
    """/IRQ asserted low; no latch until release/rising edge."""
    return 0

def irq_release():
    """/IRQ released high; U31 CLK2 rising edge latches IRQ_FF."""
    global irq_ff
    irq_ff = 1
    return 1

def poll_irq():
    """Software-visible pending condition; no PC side effect."""
    return bool(ie_ff and irq_ff)

errors = 0

# Test 1: IRQ disabled by default
print("  Test 1: IRQ disabled at reset")
irq_assert()
if irq_ff != 0:
    print("    FAIL: IRQ_FF should not latch while /IRQ is held low")
    errors += 1
irq_release()
pending = poll_irq()
if not pending and pc == 0x0000:
    print("    OK: IRQ latched, but not enabled and PC unchanged")
else:
    print("    FAIL: IRQ should not be serviceable when disabled")
    errors += 1
irq_ff = 0  # reset between tests

# Test 2: EI then IRQ becomes poll-visible
print("  Test 2: EI_decode + IRQ trigger")
clock_ie(0x08)
irq_assert()
if irq_ff != 0:
    print("    FAIL: IRQ_FF should wait for /IRQ release")
    errors += 1
irq_release()
old_pc = pc
pending = poll_irq()
if pending and pc == old_pc:
    print(f"    OK: IRQ is poll-visible and PC stayed ${pc:04X}")
else:
    print(f"    FAIL: pending={pending}, PC=${pc:04X}, expected no jump")
    errors += 1

# Test 3: IRQ_FF is sticky
print("  Test 3: IRQ_FF sticky until reset")
if ie_ff == 1 and irq_ff == 1:
    print("    OK: IE remains set and IRQ_FF remains latched")
else:
    print("    FAIL: v1.0 should not auto-clear IE or IRQ_FF")
    errors += 1

# Test 4: DI does not add a clear path
print("  Test 4: DI has no v1.0 hardware effect")
pc = 0x8010
irq_ff = 0
clock_ie(0x08)
di()
irq_assert()
irq_release()
pending = poll_irq()
if pending and ie_ff == 1 and pc == 0x8010:
    print("    OK: DI did not clear IE and PC did not jump")
else:
    print("    FAIL: DI should be inert in v1.0")
    errors += 1

# Test 5: U33 EI_decode only accepts opcode $08 in T2.
print("  Test 5: EI_decode gate selectivity")
decode_tests = {
    0x08: 1,  # EI
    0x18: 0,  # ADD uses SRC but AC_WR blocks
    0x38: 0,  # LB uses SRC but AC_WR blocks
    0x48: 0,  # DI has XOR bit, so /XOR_MODE blocks
    0x78: 0,  # XOR has XOR and AC_WR set
}
for opcode, expected in decode_tests.items():
    got = ei_decode(opcode)
    if got != expected:
        print(f"    FAIL: opcode ${opcode:02X} EI_decode={got}, expected {expected}")
        errors += 1
if errors == 0:
    print("    OK: only EI opcode clocks U31 IE")

print()
if errors == 0:
    print("Lab 14 PASSED")
else:
    print(f"Lab 14 FAILED ({errors} errors)")
    sys.exit(1)
