"""
RV8-GR Wiring — Connect all 35 chips per 03_wiring_guide.md

Wiring style: define shared wire names, then connect chip pins to them.
Easy to read, easy to edit, mirrors the wiring guide exactly.

Usage:
    chips = create_cpu()
    wires = wire_cpu(chips)
"""


class Wire:
    """A named wire connecting multiple chip pins."""
    def __init__(self, name: str):
        self.name = name
        self.value = 0

    def __repr__(self):
        return f"{self.name}={'H' if self.value else 'L'}"


def wire_cpu(chips):
    """Wire all chips according to 03_wiring_guide.md. Returns wire dict."""
    w = {}  # all wires by name

    # Helper: create wire and return it
    def net(name):
        w[name] = Wire(name)
        return w[name]

    # =========================================================================
    # BUS WIRES (shared multi-chip connections)
    # =========================================================================

    # DBUS — External Data Bus (ROM, RAM, U7 A-side)
    for i in range(8):
        net(f'D{i}')

    # IBUS — Internal Bus (U7 B-side, U6*, U14*, inputs to U12/U13/U5/U23/U32)
    for i in range(8):
        net(f'IB{i}')

    # ABUS — Address Bus (mux outputs → ROM, RAM)
    for i in range(16):
        net(f'A{i}')

    # =========================================================================
    # CONTROL WIRES
    # =========================================================================

    net('CLK')          # System clock → U1-2, U2-2, U3-2, U4-2, U8-8
    net('/RST')         # Reset → U1-1, U2-1, U3-1, U4-1, U8-9
    net('T0')           # U8-3 → U5-11, U25-4, U24-1
    net('T1')           # U8-4 → U6-11, U25-5, U24-3
    net('T2')           # U8-5 → U26-1, U26-9, U26-12, U27-12, U28-4, U33-1

    # IR_HIGH outputs (U5 Q) = control signals
    net('ALU_SUB')      # U5-12
    net('XOR_MODE')     # U5-13
    net('MUX_SEL')      # U5-14
    net('AC_WR')        # U5-15
    net('SRC')          # U5-16
    net('STR')          # U5-17
    net('BR')           # U5-18
    net('JMP')          # U5-19

    # Derived signals
    net('ADDR_MODE')    # U25-3
    net('PC_INC')       # U25-6
    net('BUF_OE_SAFE')  # U25-8
    net('PG_Load_N')    # U25-13
    net('/IRL_OE')      # U26-3
    net('/ADDR_MODE')   # U26-6
    net('/AC_BUF')      # U26-8
    net('/PC_LD')       # U26-11
    net('/BR_TAKEN')    # U27-3
    net('PC_LOAD_COND') # U27-6
    net('/PG_cond')     # U27-8
    net('Acc_Load_N')   # U27-11
    net('Z_match')      # U28-3
    net('/T2')          # U28-6
    net('WR_DIR')       # U28-8
    net('BUF_OE_N')     # U24-12
    net('/JUMP')        # U24-8
    net('/AC_WR')       # U24-10
    net('/A15')         # U24-6
    net('DP_Load')      # U33-6
    net('Z_flag')       # U21-5

    # PC bits (U1-U4 Q outputs)
    for i in range(16):
        net(f'PC{i}')

    # IRL bits (U6 Q outputs)
    for i in range(8):
        net(f'IRL{i}')

    # AC bits (U9 Q outputs)
    for i in range(8):
        net(f'AC{i}')

    # Page Register bits (U23 Q outputs)
    for i in range(8):
        net(f'PG{i}')

    # Data Page bits (U32 Q outputs)
    for i in range(8):
        net(f'DP{i}')

    # Adder outputs
    for i in range(8):
        net(f'SUM{i}')
    net('Carry')        # U10-9 → U11-7

    # XOR outputs
    for i in range(8):
        net(f'XOR_Y{i}')

    # =========================================================================
    # WIRING CONNECTIONS (from 03_wiring_guide.md)
    # =========================================================================

    # Format: connections[wire_name] = [(chip, pin), ...]
    # First entry = driver, rest = listeners (for tristate: managed separately)

    connections = {
        # --- Clock & Reset ---
        'CLK':   [('U1',2), ('U2',2), ('U3',2), ('U4',2), ('U8',8)],
        '/RST':  [('U1',1), ('U2',1), ('U3',1), ('U4',1), ('U8',9)],

        # --- Ring Counter (U8) outputs ---
        'T0':    [('U8',3),  ('U5',11), ('U25',4), ('U24',1)],
        'T1':    [('U8',4),  ('U6',11), ('U25',5), ('U24',3)],
        'T2':    [('U8',5),  ('U26',1), ('U26',9), ('U26',12), ('U27',12), ('U28',4), ('U33',1)],

        # --- U5 IR_HIGH Q outputs (control signals) ---
        'ALU_SUB':  [('U5',12), ('U10',7), ('U19',2), ('U19',5), ('U19',11), ('U19',14),
                     ('U20',2), ('U20',5), ('U20',11), ('U20',14), ('U28',2)],
        'XOR_MODE': [('U5',13), ('U19',1), ('U20',1), ('U33',2)],
        'MUX_SEL':  [('U5',14), ('U17',1), ('U18',1), ('U27',9)],
        'AC_WR':    [('U5',15), ('U24',11), ('U27',13)],
        'SRC':      [('U5',16), ('U25',1)],
        'STR':      [('U5',17), ('U25',2), ('U26',10), ('U25',10)],
        'BR':       [('U5',18), ('U27',1)],
        'JMP':      [('U5',19), ('U24',9)],

        # --- U24 Inverter outputs ---
        # NOT(T0) → U8-1, NOT(T1) → U8-2 (ring counter feedback)
        # /A15 → ROM /CE
        # /JUMP, /AC_WR, BUF_OE_N
        '/A15':     [('U24',6), ('ROM',24)],
        '/JUMP':    [('U24',8), ('U27',4)],
        '/AC_WR':   [('U24',10), ('U27',10), ('U33',5)],
        'BUF_OE_N': [('U24',12), ('U25',9)],

        # --- U25 OR gate outputs ---
        'ADDR_MODE':  [('U25',3), ('U15',1), ('U16',1), ('U29',1), ('U30',1), ('U26',4), ('U26',5)],
        'PC_INC':     [('U25',6), ('U1',7), ('U1',10), ('U2',7), ('U3',7), ('U4',7)],
        'BUF_OE_SAFE':[('U25',8), ('U7',19)],
        'PG_Load_N':  [('U25',13), ('U23',11)],

        # --- U26 NAND outputs ---
        '/IRL_OE':    [('U26',3), ('U6',1), ('U24',13)],
        '/ADDR_MODE': [('U26',6), ('U26',2), ('U33',4)],
        '/AC_BUF':    [('U26',8), ('U14',1), ('U14',19), ('RAM',26), ('U28',9)],
        '/PC_LD':     [('U26',11), ('U1',9), ('U2',9), ('U3',9), ('U4',9)],

        # --- U27 NAND outputs ---
        '/BR_TAKEN':   [('U27',3), ('U27',5)],
        'PC_LOAD_COND':[('U27',6), ('U26',13)],
        '/PG_cond':    [('U27',8), ('U25',12)],
        'Acc_Load_N':  [('U27',11), ('U9',11), ('U21',3)],

        # --- U28 XOR outputs ---
        'Z_match':  [('U28',3), ('U27',2)],
        '/T2':      [('U28',6), ('U25',11)],
        'WR_DIR':   [('U28',8), ('U7',1)],

        # --- U33 AND output ---
        'DP_Load':  [('U33',6), ('U32',11)],

        # --- Z flag ---
        'Z_flag':   [('U21',5), ('U28',1)],

        # --- A15 (from mux to RAM /CE and U24 input) ---
        'A15':      [('U30',12), ('RAM',24), ('U24',5)],

        # --- Carry chain ---
        'Carry':    [('U10',9), ('U11',7)],
    }

    # --- PC bits: U1 QA-QD = PC0-3, U2 = PC4-7, U3 = PC8-11, U4 = PC12-15 ---
    pc_q_pins = [(14,'U1'),(13,'U1'),(12,'U1'),(11,'U1'),  # PC0-3
                 (14,'U2'),(13,'U2'),(12,'U2'),(11,'U2'),  # PC4-7
                 (14,'U3'),(13,'U3'),(12,'U3'),(11,'U3'),  # PC8-11
                 (14,'U4'),(13,'U4'),(12,'U4'),(11,'U4')]  # PC12-15
    # PC → Address mux A-inputs
    addr_lo_a = [(2,'U15'),(5,'U15'),(11,'U15'),(14,'U15'),  # PC0-3 → U15
                 (2,'U16'),(5,'U16'),(11,'U16'),(14,'U16')]  # PC4-7 → U16
    addr_hi_a = [(2,'U29'),(5,'U29'),(11,'U29'),(14,'U29'),  # PC8-11 → U29
                 (2,'U30'),(5,'U30'),(11,'U30'),(14,'U30')]  # PC12-15 → U30
    for i in range(8):
        pin, chip = pc_q_pins[i]
        a_pin, a_chip = addr_lo_a[i]
        connections[f'PC{i}'] = [(chip, pin), (a_chip, a_pin)]
    for i in range(8):
        pin, chip = pc_q_pins[8+i]
        a_pin, a_chip = addr_hi_a[i]
        connections[f'PC{8+i}'] = [(chip, pin), (a_chip, a_pin)]

    # --- IRL bits: U6 Q → addr mux B-inputs + PC D-inputs ---
    # IRL0(pin19)→U15-3,U1-3 ... IRL7(pin12)→U16-13,U2-6
    irl_q_pins = [19, 18, 17, 16, 15, 14, 13, 12]  # Q1-Q8 = IRL0-IRL7
    irl_to_mux = [(3,'U15'),(6,'U15'),(10,'U15'),(13,'U15'),  # IRL0-3 → U15 B
                  (3,'U16'),(6,'U16'),(10,'U16'),(13,'U16')]  # IRL4-7 → U16 B
    irl_to_pc  = [(3,'U1'),(4,'U1'),(5,'U1'),(6,'U1'),       # IRL0-3 → U1 D
                  (3,'U2'),(4,'U2'),(5,'U2'),(6,'U2')]        # IRL4-7 → U2 D
    for i in range(8):
        connections[f'IRL{i}'] = [('U6', irl_q_pins[i]),
                                  (irl_to_mux[i][1], irl_to_mux[i][0]),
                                  (irl_to_pc[i][1], irl_to_pc[i][0])]

    # --- PG bits: U23 Q → U3/U4 D-inputs ---
    pg_q_pins = [19, 18, 17, 16, 15, 14, 13, 12]  # PG0-PG7
    pg_to_pc  = [(3,'U3'),(4,'U3'),(5,'U3'),(6,'U3'),  # PG0-3 → U3 D
                 (3,'U4'),(4,'U4'),(5,'U4'),(6,'U4')]   # PG4-7 → U4 D
    for i in range(8):
        connections[f'PG{i}'] = [('U23', pg_q_pins[i]), (pg_to_pc[i][1], pg_to_pc[i][0])]

    # --- DP bits: U32 Q → U29/U30 B-inputs ---
    dp_q_pins = [19, 18, 17, 16, 15, 14, 13, 12]  # DP0-DP7
    dp_to_mux = [(3,'U29'),(6,'U29'),(10,'U29'),(13,'U29'),   # DP0-3 → U29 B
                 (3,'U30'),(6,'U30'),(10,'U30'),(13,'U30')]    # DP4-7 → U30 B
    for i in range(8):
        connections[f'DP{i}'] = [('U32', dp_q_pins[i]), (dp_to_mux[i][1], dp_to_mux[i][0])]

    # --- AC bits: U9 Q → adder A + XOR B-mux B + U14 A + U22 P ---
    ac_q_pins = [19, 18, 17, 16, 15, 14, 13, 12]  # AC0-AC7
    ac_to_adder_lo = [(5,'U10'),(3,'U10'),(14,'U10'),(12,'U10')]  # AC0-3
    ac_to_adder_hi = [(5,'U11'),(3,'U11'),(14,'U11'),(12,'U11')]  # AC4-7
    ac_to_xmux_lo = [(3,'U19'),(6,'U19'),(10,'U19'),(13,'U19')]   # AC0-3 → U19 B
    ac_to_xmux_hi = [(3,'U20'),(6,'U20'),(10,'U20'),(13,'U20')]   # AC4-7 → U20 B
    ac_to_buf = [2, 3, 4, 5, 6, 7, 8, 9]                          # U14 A1-A8
    ac_to_zero = [2, 4, 6, 8, 12, 14, 16, 18]                     # U22 P0-P7
    for i in range(4):
        connections[f'AC{i}'] = [('U9', ac_q_pins[i]),
                                 (ac_to_adder_lo[i][1], ac_to_adder_lo[i][0]),
                                 (ac_to_xmux_lo[i][1], ac_to_xmux_lo[i][0]),
                                 ('U14', ac_to_buf[i]),
                                 ('U22', ac_to_zero[i])]
    for i in range(4):
        connections[f'AC{4+i}'] = [('U9', ac_q_pins[4+i]),
                                   (ac_to_adder_hi[i][1], ac_to_adder_hi[i][0]),
                                   (ac_to_xmux_hi[i][1], ac_to_xmux_hi[i][0]),
                                   ('U14', ac_to_buf[4+i]),
                                   ('U22', ac_to_zero[4+i])]

    # --- XOR outputs → Adder B + AC mux B ---
    xor_lo_pins = [3, 6, 8, 11]   # U12 Y1-Y4
    xor_hi_pins = [3, 6, 8, 11]   # U13 Y1-Y4
    adder_b_lo = [(6,'U10'),(2,'U10'),(15,'U10'),(11,'U10')]
    adder_b_hi = [(6,'U11'),(2,'U11'),(15,'U11'),(11,'U11')]
    acmux_b_lo = [(3,'U17'),(6,'U17'),(10,'U17'),(13,'U17')]
    acmux_b_hi = [(3,'U18'),(6,'U18'),(10,'U18'),(13,'U18')]
    for i in range(4):
        connections[f'XOR_Y{i}'] = [('U12', xor_lo_pins[i]),
                                    (adder_b_lo[i][1], adder_b_lo[i][0]),
                                    (acmux_b_lo[i][1], acmux_b_lo[i][0])]
    for i in range(4):
        connections[f'XOR_Y{4+i}'] = [('U13', xor_hi_pins[i]),
                                      (adder_b_hi[i][1], adder_b_hi[i][0]),
                                      (acmux_b_hi[i][1], acmux_b_hi[i][0])]

    # --- Adder SUM → AC mux A ---
    sum_lo_pins = [4, 1, 13, 10]  # U10 S0-S3
    sum_hi_pins = [4, 1, 13, 10]  # U11 S0-S3
    acmux_a_lo = [(2,'U17'),(5,'U17'),(11,'U17'),(14,'U17')]
    acmux_a_hi = [(2,'U18'),(5,'U18'),(11,'U18'),(14,'U18')]
    for i in range(4):
        connections[f'SUM{i}'] = [('U10', sum_lo_pins[i]), (acmux_a_lo[i][1], acmux_a_lo[i][0])]
    for i in range(4):
        connections[f'SUM{4+i}'] = [('U11', sum_hi_pins[i]), (acmux_a_hi[i][1], acmux_a_hi[i][0])]

    # --- AC mux Y → U9 D inputs ---
    acmux_y_lo = [(4,'U17'),(7,'U17'),(9,'U17'),(12,'U17')]
    acmux_y_hi = [(4,'U18'),(7,'U18'),(9,'U18'),(12,'U18')]
    u9_d = [2, 3, 4, 5, 6, 7, 8, 9]  # U9 D1-D8
    for i in range(4):
        w[f'ACMUX{i}'] = Wire(f'ACMUX{i}')
        connections[f'ACMUX{i}'] = [(acmux_y_lo[i][1], acmux_y_lo[i][0]), ('U9', u9_d[i])]
    for i in range(4):
        w[f'ACMUX{4+i}'] = Wire(f'ACMUX{4+i}')
        connections[f'ACMUX{4+i}'] = [(acmux_y_hi[i][1], acmux_y_hi[i][0]), ('U9', u9_d[4+i])]

    # --- IBUS connections ---
    # IB0-IB7 connect to: U7 B-side, U6 Q*, U14 Y*, U12/U13 A, U5 D, U23 D, U32 D
    ibus_to_xor_a = [(1,'U12'),(4,'U12'),(9,'U12'),(12,'U12'),
                     (1,'U13'),(4,'U13'),(9,'U13'),(12,'U13')]
    u7_b = [18, 17, 16, 15, 14, 13, 12, 11]  # U7 B1-B8
    u5_d = [2, 3, 4, 5, 6, 7, 8, 9]
    u23_d = [2, 3, 4, 5, 6, 7, 8, 9]
    u32_d = [2, 3, 4, 5, 6, 7, 8, 9]
    for i in range(8):
        connections[f'IB{i}'] = [
            ('U7', u7_b[i]),             # U7 B-side (driver/reader)
            ('U6', irl_q_pins[i]),       # U6 Q (tristate driver)
            ('U14', 18-i),               # U14 Y (tristate driver)
            (ibus_to_xor_a[i][1], ibus_to_xor_a[i][0]),  # XOR A input
            ('U5', u5_d[i]),             # U5 D input
            ('U23', u23_d[i]),           # U23 D input
            ('U32', u32_d[i]),           # U32 D input
        ]

    # --- DBUS connections ---
    u7_a = [2, 3, 4, 5, 6, 7, 8, 9]  # U7 A1-A8
    for i in range(8):
        connections[f'D{i}'] = [('U7', u7_a[i]), ('ROM', 16+i), ('RAM', 16+i)]

    # --- ABUS connections (mux Y → ROM/RAM address) ---
    mux_y_lo = [(4,'U15'),(7,'U15'),(9,'U15'),(12,'U15'),
                (4,'U16'),(7,'U16'),(9,'U16'),(12,'U16')]
    mux_y_hi = [(4,'U29'),(7,'U29'),(9,'U29'),(12,'U29'),
                (4,'U30'),(7,'U30'),(9,'U30'),(12,'U30')]
    for i in range(8):
        connections[f'A{i}'] = [(mux_y_lo[i][1], mux_y_lo[i][0]), ('ROM', i+1), ('RAM', i+1)]
    for i in range(7):  # A8-A14
        connections[f'A{8+i}'] = [(mux_y_hi[i][1], mux_y_hi[i][0]), ('ROM', 8+i+1), ('RAM', 8+i+1)]
    # A15 already defined above → RAM /CE, U24-5

    # --- U8 ring counter feedback (NOT Q0 → A, NOT Q1 → B) ---
    # U24-1←T0, U24-2→U8-1; U24-3←T1, U24-4→U8-2
    connections['NOT_Q0'] = [('U24',2), ('U8',1)]
    connections['NOT_Q1'] = [('U24',4), ('U8',2)]
    w['NOT_Q0'] = Wire('NOT_Q0')
    w['NOT_Q1'] = Wire('NOT_Q1')

    # --- U22 Q pins tied to GND (compare with $00) ---
    # (handled in test setup - Q pins set to 0)

    # --- U22 /P=Q → U21 /PR1 ---
    w['ZERO_DET'] = Wire('ZERO_DET')
    connections['ZERO_DET'] = [('U22',19), ('U21',4)]

    # --- U2 ENT ← U1 RCO, U3 ENT ← U2 RCO, U4 ENT ← U3 RCO ---
    w['RCO1'] = Wire('RCO1'); connections['RCO1'] = [('U1',15), ('U2',10)]
    w['RCO2'] = Wire('RCO2'); connections['RCO2'] = [('U2',15), ('U3',10)]
    w['RCO3'] = Wire('RCO3'); connections['RCO3'] = [('U3',15), ('U4',10)]

    # --- U28-5 and U28-10 tied to VCC (XOR with 1 = NOT) ---
    # (handled by setting those pins HIGH in simulation)

    # =========================================================================
    # Store connection map for propagation
    # =========================================================================
    w['_connections'] = connections
    return w


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    from chips import create_cpu

    chips = create_cpu()
    wires = wire_cpu(chips)

    # Count
    wire_count = len([k for k in wires if not k.startswith('_')])
    conn_count = len(wires['_connections'])
    total_pins = sum(len(v) for v in wires['_connections'].values())

    print(f"Wiring complete:")
    print(f"  Wires defined: {wire_count}")
    print(f"  Connections: {conn_count}")
    print(f"  Total pin endpoints: {total_pins}")
    print(f"\n✅ All wiring defined per 03_wiring_guide.md")
