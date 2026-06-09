"""
RV8-GR Wiring Verifier — checks that chip_sim pin states
match what wiring.py says they should be connected to.

For every wire (src_chip, src_pin) → (dest_chip, dest_pin):
  verify dest pin value == src pin value after propagation.
"""

import sys
sys.path.insert(0, '.')
from chip_sim import CPUSim
from wiring import WIRING


def verify_wiring(sim: CPUSim, verbose=False):
    """Check all wiring connections after propagation.
    Returns (pass_count, fail_count, failures)."""
    passes = 0
    fails = 0
    failures = []

    for entry in WIRING:
        if len(entry) != 4:
            continue  # skip VCC/GND/signal-name entries

        dest_chip, dest_pin, src_chip, src_pin = entry

        src_val = sim.chips[src_chip].get(src_pin)
        dest_val = sim.chips[dest_chip].get(dest_pin)

        if src_val == dest_val:
            passes += 1
        else:
            fails += 1
            msg = f"  ❌ {src_chip}-{src_pin}={src_val} → {dest_chip}-{dest_pin}={dest_val} (MISMATCH)"
            failures.append(msg)
            if verbose:
                print(msg)

    return passes, fails, failures


def run_verify(program: bytes, label: str, num_clocks: int = 9, verbose=False):
    """Run program, then verify wiring at each clock."""
    sim = CPUSim()
    sim.load_rom(program)

    total_pass = 0
    total_fail = 0
    all_failures = []

    for clk in range(num_clocks):
        sim.step()
        sim._propagate_to_chips()
        p, f, fails = verify_wiring(sim, verbose=verbose)
        total_pass += p
        total_fail += f
        all_failures.extend([(clk, msg) for msg in fails])

    if total_fail == 0:
        print(f"  ✅ {label}: {total_pass} connections verified over {num_clocks} clocks")
    else:
        print(f"  ❌ {label}: {total_fail} failures out of {total_pass+total_fail}")
        for clk, msg in all_failures[:10]:
            print(f"     CLK{clk}: {msg}")

    return total_fail == 0


if __name__ == '__main__':
    print("=" * 60)
    print("RV8-GR Wiring Verification")
    print("=" * 60)
    print()

    all_pass = True

    # Test 1: LI $42 (3 clocks = 1 instruction)
    all_pass &= run_verify(bytes([0x30, 0x42, 0x01, 0x02]), "LI $42", 9)

    # Test 2: ADDI $05
    all_pass &= run_verify(bytes([0x30, 0x10, 0x10, 0x05, 0x01, 0x04]), "LI+ADDI", 9)

    # Test 3: SB + LB
    all_pass &= run_verify(bytes([0x30, 0xAA, 0x04, 0x10, 0x38, 0x10, 0x01, 0x0A]), "SB+LB", 12)

    # Test 4: SETDP
    all_pass &= run_verify(bytes([0x40, 0x10, 0x30, 0x55, 0x04, 0x00, 0x01, 0x06]), "SETDP+SB", 12)

    # Test 5: BEQ
    all_pass &= run_verify(bytes([0x30, 0x00, 0x02, 0x06, 0x30, 0xFF, 0x01, 0x06]), "BEQ taken", 12)

    print()
    if all_pass:
        print("=" * 60)
        print("ALL WIRING VERIFIED ✅")
        print("=" * 60)
    else:
        print("⚠️ Some wiring mismatches found — check connections")
