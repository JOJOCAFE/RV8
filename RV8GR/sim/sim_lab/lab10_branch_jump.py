"""Lab 10: Branch/Jump Logic — tests PC_LD, PC_INC, branch conditions"""
import sys

print("Lab 10: Branch/Jump Logic")
print("=" * 40)

# Control signals from IR bits
# JMP = ir_high[0], BR = ir_high[1], Z_MATCH from flag

def test_branch_logic(jmp, br, z_flag):
    """PC_LD = JMP OR (BR AND Z_MATCH)"""
    br_and_z = br & z_flag
    pc_ld = jmp | br_and_z
    pc_inc = ~pc_ld & 1
    return pc_ld, pc_inc

tests = [
    # (jmp, br, z, expected_pc_ld, desc)
    (0, 0, 0, 0, "NOP: no jump, no branch"),
    (0, 0, 1, 0, "NOP with Z=1: still no jump"),
    (1, 0, 0, 1, "J: unconditional jump"),
    (1, 0, 1, 1, "J with Z=1: still jumps"),
    (0, 1, 0, 0, "BEQ with Z=0: not taken"),
    (0, 1, 1, 1, "BEQ with Z=1: taken"),
]

errors = 0
for jmp, br, z, expected, desc in tests:
    pc_ld, pc_inc = test_branch_logic(jmp, br, z)
    ok = pc_ld == expected
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {desc}: PC_LD={pc_ld} PC_INC={pc_inc}")
    if not ok:
        errors += 1

print()
if errors == 0:
    print("Lab 10 PASSED")
else:
    print(f"Lab 10 FAILED ({errors} errors)")
    sys.exit(1)
