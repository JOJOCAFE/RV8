"""RV8-GR Chip Behaviors — Logic for all 35 chips."""


# =============================================================================
# COMBINATIONAL: Simple Gates
# =============================================================================

def behav_hc04(chip):
    """74HC04: Hex inverter. 6 gates."""
    chip.set(2, 1 - chip.get(1))
    chip.set(4, 1 - chip.get(3))
    chip.set(6, 1 - chip.get(5))
    chip.set(8, 1 - chip.get(9))
    chip.set(10, 1 - chip.get(11))
    chip.set(12, 1 - chip.get(13))


def behav_hc00(chip):
    """74HC00: Quad NAND. 4 gates."""
    chip.set(3, 1 - (chip.get(1) & chip.get(2)))
    chip.set(6, 1 - (chip.get(4) & chip.get(5)))
    chip.set(8, 1 - (chip.get(9) & chip.get(10)))
    chip.set(11, 1 - (chip.get(12) & chip.get(13)))


def behav_hc32(chip):
    """74HC32: Quad OR. 4 gates."""
    chip.set(3, chip.get(1) | chip.get(2))
    chip.set(6, chip.get(4) | chip.get(5))
    chip.set(8, chip.get(9) | chip.get(10))
    chip.set(13, chip.get(11) | chip.get(12))


def behav_hc86(chip):
    """74HC86: Quad XOR. 4 gates."""
    chip.set(3, chip.get(1) ^ chip.get(2))
    chip.set(6, chip.get(4) ^ chip.get(5))
    chip.set(8, chip.get(9) ^ chip.get(10))
    chip.set(11, chip.get(12) ^ chip.get(13))


def behav_hc21(chip):
    """74HC21: Dual 4-input AND."""
    chip.set(6, chip.get(1) & chip.get(2) & chip.get(4) & chip.get(5))
    chip.set(8, chip.get(9) & chip.get(10) & chip.get(12) & chip.get(13))


# =============================================================================
# COMBINATIONAL: Mux, Adder, Compare, Buffer
# =============================================================================

def behav_hc157(chip):
    """74HC157: Quad 2-to-1 mux. SEL=0→A, SEL=1→B. /E=1→all 0."""
    if chip.get(15):  # /E = disabled
        chip.set(4, 0); chip.set(7, 0); chip.set(9, 0); chip.set(12, 0)
        return
    sel = chip.get(1)
    # Gate 1: A=pin2, B=pin3, Y=pin4
    chip.set(4, chip.get(3) if sel else chip.get(2))
    # Gate 2: A=pin5, B=pin6, Y=pin7
    chip.set(7, chip.get(6) if sel else chip.get(5))
    # Gate 3: A=pin11, B=pin10, Y=pin9
    chip.set(9, chip.get(10) if sel else chip.get(11))
    # Gate 4: A=pin14, B=pin13, Y=pin12
    chip.set(12, chip.get(13) if sel else chip.get(14))


def behav_hc283(chip):
    """74HC283: 4-bit full adder."""
    a = (chip.get(5) | (chip.get(3) << 1) | (chip.get(14) << 2) | (chip.get(12) << 3))
    b = (chip.get(6) | (chip.get(2) << 1) | (chip.get(15) << 2) | (chip.get(11) << 3))
    cin = chip.get(7)
    result = a + b + cin
    chip.set(4, (result >> 0) & 1)   # S0
    chip.set(1, (result >> 1) & 1)   # S1
    chip.set(13, (result >> 2) & 1)  # S2
    chip.set(10, (result >> 3) & 1)  # S3
    chip.set(9, (result >> 4) & 1)   # Cout


def behav_hc688(chip):
    """74HC688: 8-bit comparator. /P=Q=0 when P==Q and /OE=0."""
    if chip.get(1):  # /OE=1 → output HIGH
        chip.set(19, 1)
        return
    p = (chip.get(2) | (chip.get(4) << 1) | (chip.get(6) << 2) | (chip.get(8) << 3) |
         (chip.get(12) << 4) | (chip.get(14) << 5) | (chip.get(16) << 6) | (chip.get(18) << 7))
    q = (chip.get(3) | (chip.get(5) << 1) | (chip.get(7) << 2) | (chip.get(9) << 3) |
         (chip.get(11) << 4) | (chip.get(13) << 5) | (chip.get(15) << 6) | (chip.get(17) << 7))
    chip.set(19, 0 if p == q else 1)


def behav_hc541(chip):
    """74HC541: Octal buffer. Y=A when /OE1=0 AND /OE2=0."""
    enabled = (chip.get(1) == 0 and chip.get(19) == 0)
    for i in range(8):
        a_pin = 2 + i       # A1=pin2 ... A8=pin9
        y_pin = 18 - i      # Y1=pin18 ... Y8=pin11
        chip.set(y_pin, chip.get(a_pin) if enabled else 0)


def behav_hc245(chip):
    """74HC245: Octal bidirectional buffer. DIR=0: A→B, DIR=1: B→A."""
    enabled = (chip.get(19) == 0)  # /OE
    if not enabled:
        return  # high-Z (don't change pins)
    direction = chip.get(1)  # DIR
    for i in range(8):
        a_pin = 2 + i       # A1=pin2 ... A8=pin9
        b_pin = 18 - i      # B1=pin18 ... B8=pin11
        if direction == 0:
            chip.set(b_pin, chip.get(a_pin))  # A→B
        else:
            chip.set(a_pin, chip.get(b_pin))  # B→A


# =============================================================================
# SEQUENTIAL: Flip-flops, Counters, Shift Registers
# =============================================================================

def behav_hc574_edge(chip):
    """74HC574: Latch D→Q on rising edge of CLK (pin 11).
    /OE (pin 1) controls output enable (not modeled as tristate here).
    Internal register stored in chip._reg."""
    if not hasattr(chip, '_reg'):
        chip._reg = [0] * 8
    # Latch D inputs into internal register
    for i in range(8):
        chip._reg[i] = chip.get(2 + i)  # D1=pin2 ... D8=pin9
    # Drive Q outputs (Q1=pin19, Q8=pin12) — if /OE=0
    if chip.get(1) == 0:  # /OE
        for i in range(8):
            chip.set(19 - i, chip._reg[i])  # Q1=pin19 ... Q8=pin12


def behav_hc574_update(chip):
    """74HC574: Update outputs from internal register (called every cycle)."""
    if not hasattr(chip, '_reg'):
        chip._reg = [0] * 8
    if chip.get(1) == 0:  # /OE=0 → drive outputs
        for i in range(8):
            chip.set(19 - i, chip._reg[i])


def behav_hc161_edge(chip):
    """74HC161: 4-bit counter. On CLK rising edge:
    - /CLR=0: reset to 0
    - /LD=0: load D[3:0]
    - ENP=1 AND ENT=1: count+1
    """
    if not hasattr(chip, '_count'):
        chip._count = 0

    if chip.get(1) == 0:  # /CLR
        chip._count = 0
    elif chip.get(9) == 0:  # /LD=0: load
        chip._count = (chip.get(3) | (chip.get(4) << 1) |
                       (chip.get(5) << 2) | (chip.get(6) << 3))
    elif chip.get(7) and chip.get(10):  # ENP=1 AND ENT=1
        chip._count = (chip._count + 1) & 0xF

    # Drive outputs: QA=pin14, QB=pin13, QC=pin12, QD=pin11
    chip.set(14, (chip._count >> 0) & 1)
    chip.set(13, (chip._count >> 1) & 1)
    chip.set(12, (chip._count >> 2) & 1)
    chip.set(11, (chip._count >> 3) & 1)
    # RCO = pin15 (HIGH when count=15 AND ENT=1)
    chip.set(15, 1 if (chip._count == 0xF and chip.get(10)) else 0)


def behav_hc161_update(chip):
    """74HC161: Drive Q outputs from internal counter (combinational part)."""
    if not hasattr(chip, '_count'):
        chip._count = 0
    chip.set(14, (chip._count >> 0) & 1)
    chip.set(13, (chip._count >> 1) & 1)
    chip.set(12, (chip._count >> 2) & 1)
    chip.set(11, (chip._count >> 3) & 1)
    chip.set(15, 1 if (chip._count == 0xF and chip.get(10)) else 0)


def behav_hc164_edge(chip):
    """74HC164: 8-bit shift register. Serial = A AND B. Shift on CLK rising."""
    if not hasattr(chip, '_sr'):
        chip._sr = [0] * 8

    if chip.get(9) == 0:  # /CLR=0: clear all
        chip._sr = [0] * 8
    else:
        serial_in = chip.get(1) & chip.get(2)  # A AND B
        chip._sr = [serial_in] + chip._sr[:7]  # shift right, new bit at Q0

    # Q0=pin3, Q1=pin4, Q2=pin5, Q3=pin6, Q4=pin10, Q5=pin11, Q6=pin12, Q7=pin13
    q_pins = [3, 4, 5, 6, 10, 11, 12, 13]
    for i, p in enumerate(q_pins):
        chip.set(p, chip._sr[i])


def behav_hc164_update(chip):
    """74HC164: Drive outputs from shift register."""
    if not hasattr(chip, '_sr'):
        chip._sr = [0] * 8
    q_pins = [3, 4, 5, 6, 10, 11, 12, 13]
    for i, p in enumerate(q_pins):
        chip.set(p, chip._sr[i])


def behav_hc74_edge(chip):
    """74HC74: Dual D flip-flop with async /PR and /CLR."""
    if not hasattr(chip, '_q'):
        chip._q = [0, 0]

    # FF1: /CLR1=pin1, D1=pin2, CLK1=pin3, /PR1=pin4, Q1=pin5, /Q1=pin6
    if chip.get(1) == 0:       # /CLR1 active
        chip._q[0] = 0
    elif chip.get(4) == 0:     # /PR1 active
        chip._q[0] = 1
    else:
        chip._q[0] = chip.get(2)  # D1 latched at CLK edge

    # FF2: /CLR2=pin13, D2=pin12, CLK2=pin11, /PR2=pin10, Q2=pin9, /Q2=pin8
    if chip.get(13) == 0:      # /CLR2 active
        chip._q[1] = 0
    elif chip.get(10) == 0:    # /PR2 active
        chip._q[1] = 1
    else:
        chip._q[1] = chip.get(12)  # D2 latched at CLK edge

    chip.set(5, chip._q[0]);  chip.set(6, 1 - chip._q[0])
    chip.set(9, chip._q[1]);  chip.set(8, 1 - chip._q[1])


def behav_hc74_update(chip):
    """74HC74: Handle async /PR and /CLR (combinational), drive Q outputs."""
    if not hasattr(chip, '_q'):
        chip._q = [0, 0]

    # Async overrides
    if chip.get(1) == 0:
        chip._q[0] = 0
    elif chip.get(4) == 0:
        chip._q[0] = 1

    if chip.get(13) == 0:
        chip._q[1] = 0
    elif chip.get(10) == 0:
        chip._q[1] = 1

    chip.set(5, chip._q[0]);  chip.set(6, 1 - chip._q[0])
    chip.set(9, chip._q[1]);  chip.set(8, 1 - chip._q[1])


# =============================================================================
# MEMORY
# =============================================================================

def behav_rom_update(chip):
    """AT28C256: Output data when /CE=0 and /OE=0."""
    if not hasattr(chip, '_data'):
        chip._data = bytearray(32768)
    if chip.get(24) == 0 and chip.get(25) == 0:  # /CE=0, /OE=0
        addr = 0
        for i in range(15):
            addr |= chip.get(i + 1) << i
        data = chip._data[addr]
        for i in range(8):
            chip.set(16 + i, (data >> i) & 1)


def behav_ram_update(chip):
    """62256: Read when /CE=0, /OE=0, /WE=1. Write when /CE=0, /WE=0."""
    if not hasattr(chip, '_data'):
        chip._data = bytearray(32768)
    if chip.get(24) == 0:  # /CE=0
        addr = 0
        for i in range(15):
            addr |= chip.get(i + 1) << i
        if chip.get(26) == 0:  # /WE=0 → write
            data = 0
            for i in range(8):
                data |= chip.get(16 + i) << i
            chip._data[addr] = data
        elif chip.get(25) == 0:  # /OE=0 → read
            data = chip._data[addr]
            for i in range(8):
                chip.set(16 + i, (data >> i) & 1)


# =============================================================================
# ATTACH BEHAVIORS TO CHIPS
# =============================================================================

def attach_behaviors(chips):
    """Attach update() and clock_edge() to all chip instances."""

    # Simple gates (combinational only)
    chips['U24'].update = lambda: behav_hc04(chips['U24'])
    chips['U26'].update = lambda: behav_hc00(chips['U26'])
    chips['U27'].update = lambda: behav_hc00(chips['U27'])
    chips['U25'].update = lambda: behav_hc32(chips['U25'])
    chips['U12'].update = lambda: behav_hc86(chips['U12'])
    chips['U13'].update = lambda: behav_hc86(chips['U13'])
    chips['U28'].update = lambda: behav_hc86(chips['U28'])
    chips['U33'].update = lambda: behav_hc21(chips['U33'])

    # Muxes
    for u in ['U15', 'U16', 'U17', 'U18', 'U19', 'U20', 'U29', 'U30']:
        chips[u].update = lambda c=chips[u]: behav_hc157(c)

    # Adders
    chips['U10'].update = lambda: behav_hc283(chips['U10'])
    chips['U11'].update = lambda: behav_hc283(chips['U11'])

    # Comparator
    chips['U22'].update = lambda: behav_hc688(chips['U22'])

    # Buffers
    chips['U14'].update = lambda: behav_hc541(chips['U14'])
    chips['U7'].update = lambda: behav_hc245(chips['U7'])

    # Sequential: 74HC574 (U5, U6, U9, U23, U32)
    for u in ['U5', 'U6', 'U9', 'U23', 'U32']:
        chips[u].update = lambda c=chips[u]: behav_hc574_update(c)
        chips[u].clock_edge = lambda c=chips[u]: behav_hc574_edge(c)

    # Sequential: 74HC161 (U1-U4)
    for u in ['U1', 'U2', 'U3', 'U4']:
        chips[u].update = lambda c=chips[u]: behav_hc161_update(c)
        chips[u].clock_edge = lambda c=chips[u]: behav_hc161_edge(c)

    # Sequential: 74HC164 (U8)
    chips['U8'].update = lambda: behav_hc164_update(chips['U8'])
    chips['U8'].clock_edge = lambda: behav_hc164_edge(chips['U8'])

    # Sequential: 74HC74 (U21, U31)
    chips['U21'].update = lambda: behav_hc74_update(chips['U21'])
    chips['U21'].clock_edge = lambda: behav_hc74_edge(chips['U21'])
    chips['U31'].update = lambda: behav_hc74_update(chips['U31'])
    chips['U31'].clock_edge = lambda: behav_hc74_edge(chips['U31'])

    # Memory
    chips['ROM'].update = lambda: behav_rom_update(chips['ROM'])
    chips['RAM'].update = lambda: behav_ram_update(chips['RAM'])


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    from __init__ import create_cpu

    chips = create_cpu()
    attach_behaviors(chips)

    # Test HC04 inverter
    chips['U24'].set(1, 1)
    chips['U24'].update()
    assert chips['U24'].get(2) == 0, "HC04 failed"

    chips['U24'].set(1, 0)
    chips['U24'].update()
    assert chips['U24'].get(2) == 1, "HC04 failed"

    # Test HC00 NAND
    chips['U26'].set(1, 1); chips['U26'].set(2, 1)
    chips['U26'].update()
    assert chips['U26'].get(3) == 0, "HC00 NAND(1,1) should be 0"

    chips['U26'].set(1, 1); chips['U26'].set(2, 0)
    chips['U26'].update()
    assert chips['U26'].get(3) == 1, "HC00 NAND(1,0) should be 1"

    # Test HC283 adder
    # A=5 (A0=1,A1=0,A2=1,A3=0), B=3 (B0=1,B1=1,B2=0,B3=0), Cin=0
    chips['U10'].set(5, 1); chips['U10'].set(3, 0); chips['U10'].set(14, 1); chips['U10'].set(12, 0)
    chips['U10'].set(6, 1); chips['U10'].set(2, 1); chips['U10'].set(15, 0); chips['U10'].set(11, 0)
    chips['U10'].set(7, 0)
    chips['U10'].update()
    s = chips['U10'].get(4) | (chips['U10'].get(1) << 1) | (chips['U10'].get(13) << 2) | (chips['U10'].get(10) << 3)
    assert s == 8, f"HC283: 5+3={s}, expected 8"

    # Test HC574 latch
    for i in range(8):
        chips['U5'].set(2 + i, (0x42 >> i) & 1)
    chips['U5'].set(1, 0)  # /OE=0
    chips['U5'].clock_edge()
    q = 0
    for i in range(8):
        q |= chips['U5'].get(19 - i) << i
    assert q == 0x42, f"HC574: latched {q:02X}, expected $42"

    # Test HC161 counter
    chips['U1'].set(1, 1)  # /CLR=1
    chips['U1'].set(9, 1)  # /LD=1
    chips['U1'].set(7, 1)  # ENP=1
    chips['U1'].set(10, 1) # ENT=1
    chips['U1']._count = 0
    chips['U1'].clock_edge()
    assert chips['U1']._count == 1, "HC161 count failed"
    chips['U1'].clock_edge()
    assert chips['U1']._count == 2, "HC161 count failed"

    print("✅ All chip behaviors verified")
