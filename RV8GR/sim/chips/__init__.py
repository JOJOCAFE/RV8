"""RV8-GR Chip Simulator — All 35 chips with pin layout + behavior in one class."""


class Pin:
    __slots__ = ('name', 'value', 'direction')
    def __init__(self, name, direction='in'):
        self.name = name
        self.value = 0
        self.direction = direction


class Chip:
    def __init__(self, name, pin_defs):
        self.name = name
        self.pins = {n: Pin(pn, d) for n, (pn, d) in pin_defs.items()}

    def get(self, n): return self.pins[n].value
    def set(self, n, v): self.pins[n].value = v & 1
    def update(self): pass
    def clock_edge(self): pass


# =============================================================================
# 74HC04 — Hex Inverter
# =============================================================================
def TTL_74hc04(name):
    pins = {1:('1A','in'),2:('1Y','out'),3:('2A','in'),4:('2Y','out'),
            5:('3A','in'),6:('3Y','out'),7:('GND','power'),
            8:('4Y','out'),9:('4A','in'),10:('5Y','out'),11:('5A','in'),
            12:('6Y','out'),13:('6A','in'),14:('VCC','power')}
    c = Chip(name, pins)
    def update():
        c.set(2,1-c.get(1)); c.set(4,1-c.get(3)); c.set(6,1-c.get(5))
        c.set(8,1-c.get(9)); c.set(10,1-c.get(11)); c.set(12,1-c.get(13))
    c.update = update
    return c

# =============================================================================
# 74HC00 — Quad NAND
# =============================================================================
def TTL_74hc00(name):
    pins = {1:('1A','in'),2:('1B','in'),3:('1Y','out'),
            4:('2A','in'),5:('2B','in'),6:('2Y','out'),7:('GND','power'),
            8:('3Y','out'),9:('3A','in'),10:('3B','in'),
            11:('4Y','out'),12:('4A','in'),13:('4B','in'),14:('VCC','power')}
    c = Chip(name, pins)
    def update():
        c.set(3,1-(c.get(1)&c.get(2))); c.set(6,1-(c.get(4)&c.get(5)))
        c.set(8,1-(c.get(9)&c.get(10))); c.set(11,1-(c.get(12)&c.get(13)))
    c.update = update
    return c

# =============================================================================
# 74HC32 — Quad OR
# =============================================================================
def TTL_74hc32(name):
    pins = {1:('1A','in'),2:('1B','in'),3:('1Y','out'),
            4:('2A','in'),5:('2B','in'),6:('2Y','out'),7:('GND','power'),
            8:('3Y','out'),9:('3A','in'),10:('3B','in'),
            11:('4A','in'),12:('4B','in'),13:('4Y','out'),14:('VCC','power')}
    c = Chip(name, pins)
    def update():
        c.set(3,c.get(1)|c.get(2)); c.set(6,c.get(4)|c.get(5))
        c.set(8,c.get(9)|c.get(10)); c.set(13,c.get(11)|c.get(12))
    c.update = update
    return c

# =============================================================================
# 74HC86 — Quad XOR
# =============================================================================
def TTL_74hc86(name):
    pins = {1:('1A','in'),2:('1B','in'),3:('1Y','out'),
            4:('2A','in'),5:('2B','in'),6:('2Y','out'),7:('GND','power'),
            8:('3Y','out'),9:('3A','in'),10:('3B','in'),
            11:('4Y','out'),12:('4A','in'),13:('4B','in'),14:('VCC','power')}
    c = Chip(name, pins)
    def update():
        c.set(3,c.get(1)^c.get(2)); c.set(6,c.get(4)^c.get(5))
        c.set(8,c.get(9)^c.get(10)); c.set(11,c.get(12)^c.get(13))
    c.update = update
    return c

# =============================================================================
# 74HC21 — Dual 4-input AND
# =============================================================================
def TTL_74hc21(name):
    pins = {1:('1A','in'),2:('1B','in'),3:('NC','nc'),
            4:('1C','in'),5:('1D','in'),6:('1Y','out'),7:('GND','power'),
            8:('2Y','out'),9:('2A','in'),10:('2B','in'),
            11:('NC','nc'),12:('2C','in'),13:('2D','in'),14:('VCC','power')}
    c = Chip(name, pins)
    def update():
        c.set(6, c.get(1)&c.get(2)&c.get(4)&c.get(5))
        c.set(8, c.get(9)&c.get(10)&c.get(12)&c.get(13))
    c.update = update
    return c

# =============================================================================
# 74HC157 — Quad 2-to-1 Mux
# =============================================================================
def TTL_74hc157(name):
    pins = {1:('SEL','in'),2:('1A','in'),3:('1B','in'),4:('1Y','out'),
            5:('2A','in'),6:('2B','in'),7:('2Y','out'),8:('GND','power'),
            9:('3Y','out'),10:('3B','in'),11:('3A','in'),12:('4Y','out'),
            13:('4B','in'),14:('4A','in'),15:('/E','in'),16:('VCC','power')}
    c = Chip(name, pins)
    def update():
        if c.get(15):  # /E=1 disabled
            c.set(4,0); c.set(7,0); c.set(9,0); c.set(12,0); return
        s = c.get(1)
        c.set(4, c.get(3) if s else c.get(2))
        c.set(7, c.get(6) if s else c.get(5))
        c.set(9, c.get(10) if s else c.get(11))
        c.set(12, c.get(13) if s else c.get(14))
    c.update = update
    return c

# =============================================================================
# 74HC283 — 4-bit Full Adder
# =============================================================================
def TTL_74hc283(name):
    pins = {1:('S1','out'),2:('B1','in'),3:('A1','in'),4:('S0','out'),
            5:('A0','in'),6:('B0','in'),7:('Cin','in'),8:('GND','power'),
            9:('Cout','out'),10:('S3','out'),11:('B3','in'),12:('A3','in'),
            13:('S2','out'),14:('A2','in'),15:('B2','in'),16:('VCC','power')}
    c = Chip(name, pins)
    def update():
        a = c.get(5)|(c.get(3)<<1)|(c.get(14)<<2)|(c.get(12)<<3)
        b = c.get(6)|(c.get(2)<<1)|(c.get(15)<<2)|(c.get(11)<<3)
        r = a + b + c.get(7)
        c.set(4,(r>>0)&1); c.set(1,(r>>1)&1); c.set(13,(r>>2)&1); c.set(10,(r>>3)&1)
        c.set(9,(r>>4)&1)
    c.update = update
    return c

# =============================================================================
# 74HC688 — 8-bit Comparator
# =============================================================================
def TTL_74hc688(name):
    pins = {1:('/OE','in'),2:('P0','in'),3:('Q0','in'),4:('P1','in'),5:('Q1','in'),
            6:('P2','in'),7:('Q2','in'),8:('P3','in'),9:('Q3','in'),10:('GND','power'),
            11:('Q4','in'),12:('P4','in'),13:('Q5','in'),14:('P5','in'),
            15:('Q6','in'),16:('P6','in'),17:('Q7','in'),18:('P7','in'),
            19:('/P=Q','out'),20:('VCC','power')}
    c = Chip(name, pins)
    def update():
        if c.get(1): c.set(19,1); return
        p = c.get(2)|(c.get(4)<<1)|(c.get(6)<<2)|(c.get(8)<<3)|(c.get(12)<<4)|(c.get(14)<<5)|(c.get(16)<<6)|(c.get(18)<<7)
        q = c.get(3)|(c.get(5)<<1)|(c.get(7)<<2)|(c.get(9)<<3)|(c.get(11)<<4)|(c.get(13)<<5)|(c.get(15)<<6)|(c.get(17)<<7)
        c.set(19, 0 if p==q else 1)
    c.update = update
    return c

# =============================================================================
# 74HC541 — Octal Buffer
# =============================================================================
def TTL_74hc541(name):
    pins = {1:('/OE1','in'),19:('/OE2','in'),10:('GND','power'),20:('VCC','power')}
    for i in range(8): pins[2+i] = (f'A{i+1}','in'); pins[18-i] = (f'Y{i+1}','out')
    c = Chip(name, pins)
    def update():
        en = (c.get(1)==0 and c.get(19)==0)
        for i in range(8): c.set(18-i, c.get(2+i) if en else 0)
    c.update = update
    return c

# =============================================================================
# 74HC245 — Octal Bidirectional Buffer
# =============================================================================
def TTL_74hc245(name):
    pins = {1:('DIR','in'),19:('/OE','in'),10:('GND','power'),20:('VCC','power')}
    for i in range(8): pins[2+i] = (f'A{i+1}','bidir'); pins[18-i] = (f'B{i+1}','bidir')
    c = Chip(name, pins)
    def update():
        if c.get(19): return  # disabled
        if c.get(1)==0:  # A→B
            for i in range(8): c.set(18-i, c.get(2+i))
        else:  # B→A
            for i in range(8): c.set(2+i, c.get(18-i))
    c.update = update
    return c

# =============================================================================
# 74HC574 — Octal D Flip-Flop (edge-triggered)
# =============================================================================
def TTL_74hc574(name):
    pins = {1:('/OE','in'),11:('CLK','in'),10:('GND','power'),20:('VCC','power')}
    for i in range(8): pins[2+i] = (f'D{i+1}','in'); pins[19-i] = (f'Q{i+1}','out')
    c = Chip(name, pins)
    c._reg = [0]*8
    def clock_edge():
        for i in range(8): c._reg[i] = c.get(2+i)
        if c.get(1)==0:
            for i in range(8): c.set(19-i, c._reg[i])
    def update():
        if c.get(1)==0:
            for i in range(8): c.set(19-i, c._reg[i])
    c.clock_edge = clock_edge
    c.update = update
    return c

# =============================================================================
# 74HC161 — 4-bit Synchronous Counter
# =============================================================================
def TTL_74hc161(name):
    pins = {1:('/CLR','in'),2:('CLK','in'),3:('D0','in'),4:('D1','in'),
            5:('D2','in'),6:('D3','in'),7:('ENP','in'),8:('GND','power'),
            9:('/LD','in'),10:('ENT','in'),11:('QD','out'),12:('QC','out'),
            13:('QB','out'),14:('QA','out'),15:('RCO','out'),16:('VCC','power')}
    c = Chip(name, pins)
    c._count = 0
    def clock_edge():
        if c.get(1)==0: c._count = 0
        elif c.get(9)==0: c._count = c.get(3)|(c.get(4)<<1)|(c.get(5)<<2)|(c.get(6)<<3)
        elif c.get(7) and c.get(10): c._count = (c._count+1)&0xF
        _drive()
    def _drive():
        c.set(14,(c._count>>0)&1); c.set(13,(c._count>>1)&1)
        c.set(12,(c._count>>2)&1); c.set(11,(c._count>>3)&1)
        c.set(15, 1 if (c._count==0xF and c.get(10)) else 0)
    def update(): _drive()
    c.clock_edge = clock_edge
    c.update = update
    return c

# =============================================================================
# 74HC164 — 8-bit Shift Register
# =============================================================================
def TTL_74hc164(name):
    pins = {1:('A','in'),2:('B','in'),3:('Q0','out'),4:('Q1','out'),
            5:('Q2','out'),6:('Q3','out'),7:('GND','power'),8:('CLK','in'),
            9:('/CLR','in'),10:('Q4','out'),11:('Q5','out'),12:('Q6','out'),
            13:('Q7','out'),14:('VCC','power')}
    c = Chip(name, pins)
    c._sr = [0]*8
    q_pins = [3,4,5,6,10,11,12,13]
    def clock_edge():
        if c.get(9)==0: c._sr = [0]*8
        else: c._sr = [c.get(1)&c.get(2)] + c._sr[:7]
        for i,p in enumerate(q_pins): c.set(p, c._sr[i])
    def update():
        for i,p in enumerate(q_pins): c.set(p, c._sr[i])
    c.clock_edge = clock_edge
    c.update = update
    return c

# =============================================================================
# 74HC74 — Dual D Flip-Flop
# =============================================================================
def TTL_74hc74(name):
    pins = {1:('/CLR1','in'),2:('D1','in'),3:('CLK1','in'),4:('/PR1','in'),
            5:('Q1','out'),6:('/Q1','out'),7:('GND','power'),
            8:('/Q2','out'),9:('Q2','out'),10:('/PR2','in'),11:('CLK2','in'),
            12:('D2','in'),13:('/CLR2','in'),14:('VCC','power')}
    c = Chip(name, pins)
    c._q = [0,0]
    def clock_edge():
        if c.get(1)==0: c._q[0]=0
        elif c.get(4)==0: c._q[0]=1
        else: c._q[0]=c.get(2)
        if c.get(13)==0: c._q[1]=0
        elif c.get(10)==0: c._q[1]=1
        else: c._q[1]=c.get(12)
        _drive()
    def _drive():
        # Async: /CLR and /PR override
        if c.get(1)==0: c._q[0]=0
        elif c.get(4)==0: c._q[0]=1
        if c.get(13)==0: c._q[1]=0
        elif c.get(10)==0: c._q[1]=1
        c.set(5,c._q[0]); c.set(6,1-c._q[0])
        c.set(9,c._q[1]); c.set(8,1-c._q[1])
    def update(): _drive()
    c.clock_edge = clock_edge
    c.update = update
    return c

# =============================================================================
# Memory: AT28C256 (ROM) and 62256 (RAM)
# =============================================================================
def MEM_AT28C256(name):
    pins = {}
    for i in range(15): pins[i+1] = (f'A{i}','in')
    for i in range(8): pins[i+16] = (f'D{i}','out')
    pins[24]=('/CE','in'); pins[25]=('/OE','in'); pins[26]=('/WE','in')
    pins[27]=('GND','power'); pins[28]=('VCC','power')
    c = Chip(name, pins)
    c._data = bytearray(32768)
    def update():
        if c.get(24)==0 and c.get(25)==0:
            addr = sum(c.get(i+1)<<i for i in range(15))
            d = c._data[addr]
            for i in range(8): c.set(16+i,(d>>i)&1)
    c.update = update
    return c

def MEM_62256(name):
    pins = {}
    for i in range(15): pins[i+1] = (f'A{i}','in')
    for i in range(8): pins[i+16] = (f'D{i}','bidir')
    pins[24]=('/CE','in'); pins[25]=('/OE','in'); pins[26]=('/WE','in')
    pins[27]=('GND','power'); pins[28]=('VCC','power')
    c = Chip(name, pins)
    c._data = bytearray(32768)
    def update():
        if c.get(24)==0:
            addr = sum(c.get(i+1)<<i for i in range(15))
            if c.get(26)==0:  # write
                c._data[addr] = sum(c.get(16+i)<<i for i in range(8))
            elif c.get(25)==0:  # read
                d = c._data[addr]
                for i in range(8): c.set(16+i,(d>>i)&1)
    c.update = update
    return c


# =============================================================================
# CREATE ALL 35 CHIPS
# =============================================================================
def create_cpu():
    chips = {}
    chips['U1']=TTL_74hc161('U1'); chips['U2']=TTL_74hc161('U2')
    chips['U3']=TTL_74hc161('U3'); chips['U4']=TTL_74hc161('U4')
    chips['U5']=TTL_74hc574('U5'); chips['U6']=TTL_74hc574('U6')
    chips['U7']=TTL_74hc245('U7'); chips['U8']=TTL_74hc164('U8')
    chips['U9']=TTL_74hc574('U9')
    chips['U10']=TTL_74hc283('U10'); chips['U11']=TTL_74hc283('U11')
    chips['U12']=TTL_74hc86('U12'); chips['U13']=TTL_74hc86('U13')
    chips['U14']=TTL_74hc541('U14')
    for i in range(15,21): chips[f'U{i}']=TTL_74hc157(f'U{i}')
    chips['U21']=TTL_74hc74('U21'); chips['U22']=TTL_74hc688('U22')
    chips['U23']=TTL_74hc574('U23'); chips['U24']=TTL_74hc04('U24')
    chips['U25']=TTL_74hc32('U25')
    chips['U26']=TTL_74hc00('U26'); chips['U27']=TTL_74hc00('U27')
    chips['U28']=TTL_74hc86('U28')
    chips['U29']=TTL_74hc157('U29'); chips['U30']=TTL_74hc157('U30')
    chips['U31']=TTL_74hc74('U31'); chips['U32']=TTL_74hc574('U32')
    chips['U33']=TTL_74hc21('U33')
    chips['ROM']=MEM_AT28C256('ROM'); chips['RAM']=MEM_62256('RAM')
    return chips


if __name__ == '__main__':
    chips = create_cpu()
    print(f"Created {len(chips)} chips (behavior built-in)")
    # Quick test
    chips['U24'].set(1,1); chips['U24'].update(); assert chips['U24'].get(2)==0
    chips['U26'].set(1,1); chips['U26'].set(2,1); chips['U26'].update(); assert chips['U26'].get(3)==0
    for i in range(8): chips['U5'].set(2+i,(0x42>>i)&1)
    chips['U5'].set(1,0); chips['U5'].clock_edge()
    q = sum(chips['U5'].get(19-i)<<i for i in range(8))
    assert q==0x42
    print("✅ All chips: behavior built-in, tests pass")
