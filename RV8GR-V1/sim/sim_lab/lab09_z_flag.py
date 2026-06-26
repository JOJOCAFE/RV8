"""
Lab 09: Z Flag + Control Logic — U21-U22, U24-U28, U33

Tests derived signals from IR_HIGH control bits:
  ADDR_MODE, PC_INC, /IRL_OE, /AC_BUF, /PC_LD, Z_match, WR_DIR, DP_Load
"""
import sys; sys.path.insert(0, '..')
from chips import TTL_74hc04, TTL_74hc32, TTL_74hc00, TTL_74hc86, TTL_74hc21

U24 = TTL_74hc04('U24')
U25 = TTL_74hc32('U25')
U26 = TTL_74hc00('U26')
U27 = TTL_74hc00('U27')
U28 = TTL_74hc86('U28')
U33 = TTL_74hc21('U33')

def compute_signals(t2, sub, xor_mode, mux, ac_wr, src, stt, br, jmp, z_flag):
    """Compute all derived signals. Returns dict."""
    # U25 gate 1: ADDR_MODE = SRC | STR
    U25.set(1, src); U25.set(2, stt); U25.update()
    addr_mode = U25.get(3)

    # U25 gate 2: PC_INC = T0 | T1 (we pass t0/t1 as !t2 for simplicity)
    t0 = 1 if not t2 else 0
    U25.set(4, t0); U25.set(5, 0); U25.update()  # simplified
    pc_inc = U25.get(6)

    # U26 gate 2: /ADDR_MODE = NAND(ADDR_MODE, ADDR_MODE) = NOT
    U26.set(4, addr_mode); U26.set(5, addr_mode); U26.update()
    not_addr_mode = U26.get(6)

    # U26 gate 1: /IRL_OE = NAND(T2, /ADDR_MODE)
    U26.set(1, t2); U26.set(2, not_addr_mode); U26.update()
    irl_oe_n = U26.get(3)

    # U26 gate 3: /AC_BUF = NAND(T2, STR)
    U26.set(9, t2); U26.set(10, stt); U26.update()
    ac_buf_n = U26.get(8)

    # U24: /JUMP = NOT(JMP), /AC_WR = NOT(AC_WR), BUF_OE_N = NOT(/IRL_OE)
    U24.set(9, jmp); U24.set(11, ac_wr); U24.set(13, irl_oe_n)
    U24.update()
    not_jump = U24.get(8)
    not_ac_wr = U24.get(10)
    buf_oe_n = U24.get(12)

    # U25 gate 3: BUF_OE_SAFE = BUF_OE_N | STR
    U25.set(9, buf_oe_n); U25.set(10, stt); U25.update()
    buf_oe_safe = U25.get(8)

    # U28 gate 1: Z_match = Z_flag XOR SUB
    U28.set(1, z_flag); U28.set(2, sub); U28.update()
    z_match = U28.get(3)

    # U27 gate 1: /BR_TAKEN = NAND(BR, Z_match)
    U27.set(1, br); U27.set(2, z_match); U27.update()
    br_taken_n = U27.get(3)

    # U27 gate 2: PC_LOAD_COND = NAND(/JUMP, /BR_TAKEN)
    U27.set(4, not_jump); U27.set(5, br_taken_n); U27.update()
    pc_load_cond = U27.get(6)

    # U26 gate 4: /PC_LD = NAND(T2, PC_LOAD_COND)
    U26.set(12, t2); U26.set(13, pc_load_cond); U26.update()
    pc_ld_n = U26.get(11)

    # U28 gate 3: WR_DIR = /AC_BUF XOR VCC = NOT(/AC_BUF)
    U28.set(9, ac_buf_n); U28.set(10, 1); U28.update()
    wr_dir = U28.get(8)

    # U33: DP_Load = T2 & XOR_MODE & /ADDR_MODE & /AC_WR
    U33.set(1, t2); U33.set(2, xor_mode); U33.set(4, not_addr_mode); U33.set(5, not_ac_wr)
    U33.update()
    dp_load = U33.get(6)

    return {
        'ADDR_MODE': addr_mode, '/IRL_OE': irl_oe_n, '/AC_BUF': ac_buf_n,
        'BUF_OE_SAFE': buf_oe_safe, '/PC_LD': pc_ld_n, 'Z_match': z_match,
        'WR_DIR': wr_dir, 'DP_Load': dp_load, 'PC_LOAD_COND': pc_load_cond,
    }

# Test: (T2, SUB,XOR,MUX,AC_WR,SRC,STR,BR,JMP, Z, expected_signals)
TEST_VECTORS = [
    # LI $42 at T2: $30 = 0011_0000
    (1, 0,0,1,1,0,0,0,0, 0, {'ADDR_MODE':0, '/IRL_OE':0, '/AC_BUF':1, 'WR_DIR':0, '/PC_LD':1, 'DP_Load':0}),
    # SB $03 at T2: $04 = 0000_0100
    (1, 0,0,0,0,0,1,0,0, 0, {'ADDR_MODE':1, '/IRL_OE':1, '/AC_BUF':0, 'WR_DIR':1, '/PC_LD':1, 'DP_Load':0}),
    # J $20 at T2: $01 = 0000_0001
    (1, 0,0,0,0,0,0,0,1, 0, {'/PC_LD':0, 'PC_LOAD_COND':1, 'DP_Load':0}),
    # BEQ at T2 with Z=1: $02
    (1, 0,0,0,0,0,0,1,0, 1, {'Z_match':1, '/PC_LD':0}),
    # BNE at T2 with Z=0: $82 (SUB=1)
    (1, 1,0,0,0,0,0,1,0, 0, {'Z_match':1, '/PC_LD':0}),
    # SETDP at T2: $40 = 0100_0000
    (1, 0,1,0,0,0,0,0,0, 0, {'DP_Load':1, 'ADDR_MODE':0}),
    # Not T2 → most signals inactive
    (0, 0,0,0,0,0,0,0,0, 0, {'/IRL_OE':1, '/AC_BUF':1, '/PC_LD':1, 'DP_Load':0}),
]

if __name__ == '__main__':
    print("Lab 09: Z Flag + Control Logic (U21-U22, U24-U28, U33)")
    print("-" * 40)

    for i, (t2, sub,xor_m,mux,acwr,src,stt,br,jmp, z, expected) in enumerate(TEST_VECTORS):
        result = compute_signals(t2, sub, xor_m, mux, acwr, src, stt, br, jmp, z)
        ok = all(result[k] == v for k, v in expected.items())
        status = "✅" if ok else "❌"
        ir = (sub<<7)|(xor_m<<6)|(mux<<5)|(acwr<<4)|(src<<3)|(stt<<2)|(br<<1)|jmp
        print(f"  {i}: T2={t2} IR=${ir:02X} Z={z} → {status}")
        if not ok:
            for k, v in expected.items():
                if result[k] != v:
                    print(f"     {k}: got {result[k]}, expected {v}")
        assert ok

    print("\n✅ Lab 09 PASS: All control signals decode correctly")
