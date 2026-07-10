"""Lab 10: Branch/Jump Logic — tests /PC_LD, PC_INC, BEQ/BNE, and page-zero setup."""
import sys

print("Lab 10: Branch/Jump Logic")
print("=" * 40)

def branch_signals(jmp, br, alu_sub, z_flag, t2=1):
    """Return lab-visible active-high PC_LOAD plus active-low /PC_LD."""
    z_match = z_flag ^ alu_sub
    br_taken_n = 0 if (br and z_match) else 1
    jump_n = 0 if jmp else 1
    pc_load_cond = 0 if (jump_n and br_taken_n) else 1
    pc_ld_n = 0 if (t2 and pc_load_cond) else 1
    pc_inc = 0 if t2 else 1
    return z_match, pc_load_cond, pc_ld_n, pc_inc

def load_pc(page_reg, ir_low):
    return ((page_reg & 0xFF) << 8) | (ir_low & 0xFF)

tests = [
    # jmp, br, sub, z, expected_pc_ld_n, desc
    (0, 0, 0, 0, 1, "NOP: no jump, no branch"),
    (1, 0, 0, 0, 0, "J: unconditional jump"),
    (0, 1, 0, 0, 1, "BEQ with Z=0: not taken"),
    (0, 1, 0, 1, 0, "BEQ with Z=1: taken"),
    (0, 1, 1, 0, 0, "BNE with Z=0: taken"),
    (0, 1, 1, 1, 1, "BNE with Z=1: not taken"),
]

errors = 0
for jmp, br, sub, z, expected_pc_ld_n, desc in tests:
    z_match, pc_load_cond, pc_ld_n, pc_inc = branch_signals(jmp, br, sub, z)
    ok = pc_ld_n == expected_pc_ld_n
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {desc}: Z_match={z_match} PC_LOAD_COND={pc_load_cond} /PC_LD={pc_ld_n} PC_INC={pc_inc}")
    if not ok:
        errors += 1

# Before Lab 11, PG is not present. Lab 10 ties high-load inputs low.
if load_pc(0x00, 0x06) == 0x0006 and load_pc(0x00, 0x20) == 0x0020:
    print("  [OK] page-zero lab setup: U3/U4 D inputs tied LOW gives $00xx jumps")
else:
    print("  [FAIL] page-zero load setup")
    errors += 1

print()
if errors == 0:
    print("Lab 10 PASSED")
else:
    print(f"Lab 10 FAILED ({errors} errors)")
    sys.exit(1)
