"""Lab 14: IRQ + RV8-Bus — tests interrupt enable/disable and vector jump

NOTE: This simulates v1.1 hardware vector behavior (matching Verilog model).
v1.0 physical build (33 chips) uses polling only — no auto-jump to $FF00.
v1.0 IRQ_FF is sticky (cleared only by /RST).
"""
import sys

print("Lab 14: IRQ + RV8-Bus")
print("=" * 40)

# Simulate IRQ logic (U31: dual 74HC74)
ie_ff = 0   # Interrupt Enable flip-flop
irq_ff = 0  # IRQ pending flip-flop
pc = 0x0000

def ei():
    global ie_ff
    ie_ff = 1

def di():
    global ie_ff
    ie_ff = 0

def irq_trigger():
    """Falling edge on /IRQ pin"""
    global irq_ff
    irq_ff = 1

def check_irq_ack():
    """At end of T2: if IE=1 and IRQ_FF=1, jump to vector"""
    global pc, ie_ff, irq_ff
    if ie_ff and irq_ff:
        pc = 0xFF00  # IRQ vector
        ie_ff = 0    # auto-disable
        irq_ff = 0   # clear pending
        return True
    return False

errors = 0

# Test 1: IRQ disabled by default
print("  Test 1: IRQ disabled at reset")
irq_trigger()
taken = check_irq_ack()
if not taken:
    print("    OK: IRQ not taken (IE=0)")
else:
    print("    FAIL: IRQ should not fire when disabled")
    errors += 1
irq_ff = 0  # clear

# Test 2: EI then IRQ fires
print("  Test 2: EI + IRQ trigger")
ei()
irq_trigger()
old_pc = pc
taken = check_irq_ack()
if taken and pc == 0xFF00:
    print(f"    OK: PC jumped to $FF00 (from ${old_pc:04X})")
else:
    print(f"    FAIL: PC=${pc:04X}, expected $FF00")
    errors += 1

# Test 3: IE auto-cleared after IRQ
print("  Test 3: IE cleared after IRQ")
if ie_ff == 0:
    print("    OK: IE=0 (auto-disabled)")
else:
    print("    FAIL: IE should be 0 after IRQ")
    errors += 1

# Test 4: DI prevents IRQ
print("  Test 4: DI blocks IRQ")
pc = 0x8010
ei()
di()
irq_trigger()
taken = check_irq_ack()
if not taken and pc == 0x8010:
    print("    OK: IRQ blocked by DI")
else:
    print("    FAIL: IRQ should not fire after DI")
    errors += 1

print()
if errors == 0:
    print("Lab 14 PASSED")
else:
    print(f"Lab 14 FAILED ({errors} errors)")
    sys.exit(1)
