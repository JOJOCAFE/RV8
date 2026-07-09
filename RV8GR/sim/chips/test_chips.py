"""RV8-GR Chip Test Suite — Human-readable test vectors.

Combinational: [(inputs...), (expected_outputs...)]
Sequential:    Clock-by-clock: [(inputs_before_edge...), (expected_outputs_after...)]
"""
import sys
sys.path.insert(0, '.')
from chips import create_cpu


# =============================================================================
# HELPERS
# =============================================================================

def set_pins(chip, pins, values):
    for p, v in zip(pins, values):
        chip.set(p, v)

def get_pins(chip, pins):
    return tuple(chip.get(p) for p in pins)

def get_byte(chip, pins):
    return sum(chip.get(p) << i for i, p in enumerate(pins))

def set_byte(chip, pins, val):
    for i, p in enumerate(pins):
        chip.set(p, (val >> i) & 1)


# =============================================================================
# 74HC04 — Inverter: (A) → (Y)
# =============================================================================
HC04_VECTORS = [
    # (input,) → (expected_output,)
    ((0,), (1,)),
    ((1,), (0,)),
]

def test_hc04():
    chips = create_cpu()
    gates = [(1, 2), (3, 4), (5, 6), (9, 8), (11, 10), (13, 12)]  # (A, Y)
    for a_pin, y_pin in gates:
        for (a,), (y,) in HC04_VECTORS:
            chips['U24'].set(a_pin, a)
            chips['U24'].update()
            assert chips['U24'].get(y_pin) == y, f"NOT({a})≠{y} at pin {a_pin}"
    print("  ✅ HC04: 6 inverters — 12 vectors")


# =============================================================================
# 74HC00 — NAND: (A, B) → (Y)
# =============================================================================
HC00_VECTORS = [
    ((0, 0), (1,)),
    ((0, 1), (1,)),
    ((1, 0), (1,)),
    ((1, 1), (0,)),
]

def test_hc00():
    chips = create_cpu()
    for name in ['U26', 'U27']:
        gates = [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]
        for a_pin, b_pin, y_pin in gates:
            for (a, b), (y,) in HC00_VECTORS:
                set_pins(chips[name], [a_pin, b_pin], [a, b])
                chips[name].update()
                assert chips[name].get(y_pin) == y
    print("  ✅ HC00: 8 NAND gates — 32 vectors")


# =============================================================================
# 74HC32 — OR: (A, B) → (Y)
# =============================================================================
HC32_VECTORS = [
    ((0, 0), (0,)),
    ((0, 1), (1,)),
    ((1, 0), (1,)),
    ((1, 1), (1,)),
]

def test_hc32():
    chips = create_cpu()
    gates = [(1, 2, 3), (4, 5, 6), (9, 10, 8), (11, 12, 13)]
    for a_pin, b_pin, y_pin in gates:
        for (a, b), (y,) in HC32_VECTORS:
            set_pins(chips['U25'], [a_pin, b_pin], [a, b])
            chips['U25'].update()
            assert chips['U25'].get(y_pin) == y
    print("  ✅ HC32: 4 OR gates — 16 vectors")


# =============================================================================
# 74HC86 — XOR: (A, B) → (Y)
# =============================================================================
HC86_VECTORS = [
    ((0, 0), (0,)),
    ((0, 1), (1,)),
    ((1, 0), (1,)),
    ((1, 1), (0,)),
]

def test_hc86():
    chips = create_cpu()
    for name in ['U12', 'U13', 'U28']:
        gates = [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]
        for a_pin, b_pin, y_pin in gates:
            for (a, b), (y,) in HC86_VECTORS:
                set_pins(chips[name], [a_pin, b_pin], [a, b])
                chips[name].update()
                assert chips[name].get(y_pin) == y
    print("  ✅ HC86: 12 XOR gates — 48 vectors")


# =============================================================================
# 74HC21 — 4-input AND: (A, B, C, D) → (Y)
# =============================================================================
HC21_VECTORS = [
    ((1, 1, 1, 1), (1,)),
    ((1, 1, 1, 0), (0,)),
    ((0, 1, 1, 1), (0,)),
    ((1, 0, 1, 1), (0,)),
    ((0, 0, 0, 0), (0,)),
]

def test_hc21():
    chips = create_cpu()
    for (a, b, c, d), (y,) in HC21_VECTORS:
        set_pins(chips['U33'], [1, 2, 4, 5], [a, b, c, d])
        chips['U33'].update()
        assert chips['U33'].get(6) == y
    print("  ✅ HC21: 4-input AND — 5 vectors")


# =============================================================================
# 74HC157 — Mux: (/E, SEL, A, B) → (Y)
# =============================================================================
HC157_VECTORS = [
    # (/E, SEL, A, B) → (Y)
    ((0, 0, 1, 0), (1,)),   # enabled, SEL=0 → Y=A
    ((0, 0, 0, 1), (0,)),   # enabled, SEL=0 → Y=A
    ((0, 1, 1, 0), (0,)),   # enabled, SEL=1 → Y=B
    ((0, 1, 0, 1), (1,)),   # enabled, SEL=1 → Y=B
    ((1, 0, 1, 1), (0,)),   # disabled → Y=0
]

def test_hc157():
    chips = create_cpu()
    for (e, sel, a, b), (y,) in HC157_VECTORS:
        set_pins(chips['U15'], [15, 1, 2, 3], [e, sel, a, b])
        chips['U15'].update()
        assert chips['U15'].get(4) == y, f"MUX(/E={e},SEL={sel},A={a},B={b})≠{y}"
    print("  ✅ HC157: quad mux — 5 vectors")


# =============================================================================
# 74HC283 — 4-bit Adder: (A, B, Cin) → (Sum, Cout)
# =============================================================================
HC283_VECTORS = [
    # (A_4bit, B_4bit, Cin) → (Sum_4bit, Cout)
    (0,  0, 0,   0, 0),
    (5,  3, 0,   8, 0),
    (7,  8, 0,  15, 0),
    (15, 1, 0,   0, 1),
    (15, 15, 1, 15, 1),
    (9,  6, 1,   0, 1),
]

def test_hc283():
    chips = create_cpu()
    a_pins = [5, 3, 14, 12]
    b_pins = [6, 2, 15, 11]
    s_pins = [4, 1, 13, 10]
    for a, b, cin, exp_s, exp_cout in HC283_VECTORS:
        set_byte(chips['U10'], a_pins, a)
        set_byte(chips['U10'], b_pins, b)
        chips['U10'].set(7, cin)
        chips['U10'].update()
        s = get_byte(chips['U10'], s_pins)
        cout = chips['U10'].get(9)
        assert s == exp_s and cout == exp_cout, f"{a}+{b}+{cin}: got S={s},C={cout}"
    print("  ✅ HC283: 4-bit adder — 6 vectors")


# =============================================================================
# 74HC688 — Comparator: (/OE, P, Q) → (/P=Q)
# =============================================================================
HC688_VECTORS = [
    # (/OE, P_byte, Q_byte) → (/P=Q)
    (0, 0x00, 0x00, 0),   # equal → LOW
    (0, 0x42, 0x42, 0),   # equal → LOW
    (0, 0x01, 0x00, 1),   # not equal → HIGH
    (0, 0xFF, 0xFE, 1),   # not equal → HIGH
    (1, 0x00, 0x00, 1),   # disabled → HIGH
]

def test_hc688():
    chips = create_cpu()
    p_pins = [2, 4, 6, 8, 11, 13, 15, 17]
    q_pins = [3, 5, 7, 9, 12, 14, 16, 18]
    for oe, p, q, exp in HC688_VECTORS:
        chips['U22'].set(1, oe)
        set_byte(chips['U22'], p_pins, p)
        set_byte(chips['U22'], q_pins, q)
        chips['U22'].update()
        assert chips['U22'].get(19) == exp, f"P=${p:02X} Q=${q:02X} /OE={oe}"
    print("  ✅ HC688: 8-bit comparator — 5 vectors")


# =============================================================================
# 74HC541 — Buffer: (/OE1, /OE2, A_byte) → (Y_byte)
# =============================================================================
HC541_VECTORS = [
    # (/OE1, /OE2, A_byte) → (Y_byte)
    (0, 0, 0xA5, 0xA5),   # enabled → pass through
    (0, 0, 0xFF, 0xFF),
    (1, 0, 0xA5, 0x00),   # disabled → 0
    (0, 1, 0xA5, 0x00),
]

def test_hc541():
    chips = create_cpu()
    a_pins = [2, 3, 4, 5, 6, 7, 8, 9]
    y_pins = [18, 17, 16, 15, 14, 13, 12, 11]
    for oe1, oe2, a, exp_y in HC541_VECTORS:
        chips['U14'].set(1, oe1); chips['U14'].set(19, oe2)
        set_byte(chips['U14'], a_pins, a)
        chips['U14'].update()
        assert get_byte(chips['U14'], y_pins) == exp_y
    print("  ✅ HC541: octal buffer — 4 vectors")


# =============================================================================
# 74HC574 — D Latch (sequential): clock-by-clock
# Format: [(D_byte_before_edge, expected_Q_byte_after_edge), ...]
# =============================================================================
HC574_SEQUENCE = [
    (0x42, 0x42),   # clock 1: latch $42
    (0xFF, 0xFF),   # clock 2: latch $FF
    (0x00, 0x00),   # clock 3: latch $00
]

def test_hc574():
    chips = create_cpu()
    d_pins = [2, 3, 4, 5, 6, 7, 8, 9]
    q_pins = [19, 18, 17, 16, 15, 14, 13, 12]
    for name in ['U5', 'U6', 'U9', 'U23', 'U32']:
        chips[name].set(1, 0)  # /OE=0
        for d_val, exp_q in HC574_SEQUENCE:
            set_byte(chips[name], d_pins, d_val)
            chips[name].clock_edge()
            q = get_byte(chips[name], q_pins)
            assert q == exp_q, f"{name}: D=${d_val:02X} → Q=${q:02X}, expected ${exp_q:02X}"
    print("  ✅ HC574: D latch — 5 chips × 3 clocks")


# =============================================================================
# 74HC161 — Counter (sequential): clock-by-clock
# Format: [(/CLR, /LD, ENP, ENT, D_nibble, expected_Q_nibble, expected_RCO), ...]
# =============================================================================
HC161_SEQUENCE = [
    # /CLR, /LD, ENP, ENT, D, → Q, RCO
    (0, 1, 1, 1, 0,   0, 0),   # clear → Q=0
    (1, 1, 1, 1, 0,   1, 0),   # count → Q=1
    (1, 1, 1, 1, 0,   2, 0),   # count → Q=2
    (1, 0, 1, 1, 9,   9, 0),   # load 9
    (1, 1, 1, 1, 0,  10, 0),   # count → 10
    (1, 1, 0, 1, 0,  10, 0),   # ENP=0 → hold
    (1, 1, 1, 0, 0,  10, 0),   # ENT=0 → hold
    (1, 0, 1, 1, 15, 15, 1),   # load 15, RCO=1 (ENT=1)
    (1, 1, 1, 1, 0,   0, 0),   # count 15→0 (overflow)
]

def test_hc161():
    chips = create_cpu()
    d_pins = [3, 4, 5, 6]
    q_pins = [14, 13, 12, 11]
    for name in ['U1', 'U2', 'U3', 'U4']:
        for clr, ld, enp, ent, d, exp_q, exp_rco in HC161_SEQUENCE:
            set_pins(chips[name], [1, 9, 7, 10], [clr, ld, enp, ent])
            set_byte(chips[name], d_pins, d)
            chips[name].clock_edge()
            q = get_byte(chips[name], q_pins)
            rco = chips[name].get(15)
            assert q == exp_q and rco == exp_rco, \
                f"{name}: /CLR={clr} /LD={ld} ENP={enp} ENT={ent} D={d} → Q={q}(exp{exp_q}) RCO={rco}(exp{exp_rco})"
    print("  ✅ HC161: counter — 4 chips × 9 clocks")


# =============================================================================
# 74HC164 — Shift Register (sequential): clock-by-clock
# Format: [(/CLR, A, B, expected_Q0, expected_Q1, expected_Q2), ...]
# =============================================================================
HC164_SEQUENCE = [
    # /CLR, A, B → Q0, Q1, Q2 (first 3 bits)
    (0, 0, 0,  0, 0, 0),   # clear
    (1, 1, 1,  1, 0, 0),   # shift in 1 (A&B=1)
    (1, 1, 1,  1, 1, 0),   # shift in 1
    (1, 0, 1,  0, 1, 1),   # shift in 0 (A=0)
    (1, 1, 0,  0, 0, 1),   # shift in 0 (B=0)
]

def test_hc164():
    chips = create_cpu()
    for clr, a, b, q0, q1, q2 in HC164_SEQUENCE:
        set_pins(chips['U8'], [9, 1, 2], [clr, a, b])
        chips['U8'].clock_edge()
        assert get_pins(chips['U8'], [3, 4, 5]) == (q0, q1, q2), \
            f"/CLR={clr} A={a} B={b} → expected ({q0},{q1},{q2})"
    print("  ✅ HC164: shift register — 5 clocks")


# =============================================================================
# 74HC74 — D Flip-Flop (sequential): clock-by-clock
# Format: [(/CLR, /PR, D, expected_Q, expected_/Q), ...]
# =============================================================================
HC74_SEQUENCE = [
    # /CLR, /PR, D → Q, /Q
    (1, 1, 1,  1, 0),   # normal: D=1 → Q=1
    (1, 1, 0,  0, 1),   # normal: D=0 → Q=0
    (0, 1, 1,  0, 1),   # /CLR=0 → Q=0 (async)
    (1, 0, 0,  1, 0),   # /PR=0 → Q=1 (async)
    (1, 1, 1,  1, 0),   # back to normal
]

def test_hc74():
    chips = create_cpu()
    for name in ['U21', 'U31']:
        for clr, pr, d, exp_q, exp_nq in HC74_SEQUENCE:
            set_pins(chips[name], [1, 4, 2], [clr, pr, d])
            chips[name].clock_edge()
            q, nq = chips[name].get(5), chips[name].get(6)
            assert q == exp_q and nq == exp_nq, \
                f"{name}: /CLR={clr} /PR={pr} D={d} → Q={q}(exp{exp_q})"
    print("  ✅ HC74: D flip-flop — 2 chips × 5 clocks")


# =============================================================================
# Memory: ROM read, RAM write/read
# =============================================================================
MEMORY_VECTORS = [
    # (addr, write_data, read_expected)
    (0x0000, 0x42, 0x42),
    (0x1234, 0xAB, 0xAB),
    (0x7FFF, 0xFF, 0xFF),
]

def test_memory():
    chips = create_cpu()
    # ROM
    for addr, data, _ in MEMORY_VECTORS:
        chips['ROM']._data[addr] = data
    for addr, _, exp in MEMORY_VECTORS:
        set_byte(chips['ROM'], list(range(1, 16)), addr)
        chips['ROM'].set(24, 0); chips['ROM'].set(25, 0)
        chips['ROM'].update()
        d = get_byte(chips['ROM'], list(range(16, 24)))
        assert d == exp, f"ROM[${addr:04X}]=${d:02X}"

    # RAM write then read
    for addr, data, exp in MEMORY_VECTORS:
        set_byte(chips['RAM'], list(range(1, 16)), addr)
        set_byte(chips['RAM'], list(range(16, 24)), data)
        chips['RAM'].set(24, 0); chips['RAM'].set(25, 1); chips['RAM'].set(26, 0)
        chips['RAM'].update()  # write
        chips['RAM'].set(26, 1); chips['RAM'].set(25, 0)
        chips['RAM'].update()  # read
        d = get_byte(chips['RAM'], list(range(16, 24)))
        assert d == exp, f"RAM[${addr:04X}]=${d:02X}"
    print("  ✅ ROM + RAM: memory — 3 vectors each")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("RV8-GR Chip Behavior Test Suite (Vector-Based)")
    print("=" * 60)
    test_hc04(); test_hc00(); test_hc32(); test_hc86(); test_hc21()
    test_hc157(); test_hc283(); test_hc688(); test_hc541()
    test_hc574(); test_hc161(); test_hc164(); test_hc74()
    test_memory()
    print("=" * 60)
    print("ALL 14 CHIP TYPES VERIFIED ✅")
    print("=" * 60)
