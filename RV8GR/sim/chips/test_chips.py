"""RV8-GR Chip Test Suite — Tests all 14 chip types."""
import sys
sys.path.insert(0, '.')
from chips import create_cpu


class Probe:
    def __init__(self, chips): self.chips = chips
    def pin(self, c, p): return self.chips[c].get(p)
    def byte(self, c, pins): return sum(self.chips[c].get(p)<<i for i,p in enumerate(pins))

class Sw:
    def __init__(self, chips): self.chips = chips
    def pin(self, c, p, v): self.chips[c].set(p, v)
    def byte(self, c, pins, v):
        for i,p in enumerate(pins): self.chips[c].set(p, (v>>i)&1)


def test_hc04():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for a,y in [(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]:
        sw.pin('U24',a,0); chips['U24'].update(); assert pr.pin('U24',y)==1
        sw.pin('U24',a,1); chips['U24'].update(); assert pr.pin('U24',y)==0
    print("  ✅ HC04: 6 inverters")

def test_hc00():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for name in ['U26','U27']:
        for a,b,y in [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]:
            for va,vb,exp in [(0,0,1),(0,1,1),(1,0,1),(1,1,0)]:
                sw.pin(name,a,va); sw.pin(name,b,vb); chips[name].update()
                assert pr.pin(name,y)==exp
    print("  ✅ HC00: 8 NAND gates")

def test_hc32():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for a,b,y in [(1,2,3),(4,5,6),(9,10,8),(11,12,13)]:
        for va,vb in [(0,0),(0,1),(1,0),(1,1)]:
            sw.pin('U25',a,va); sw.pin('U25',b,vb); chips['U25'].update()
            assert pr.pin('U25',y)==(va|vb)
    print("  ✅ HC32: 4 OR gates")

def test_hc86():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for name in ['U12','U13','U28']:
        for a,b,y in [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]:
            for va,vb in [(0,0),(0,1),(1,0),(1,1)]:
                sw.pin(name,a,va); sw.pin(name,b,vb); chips[name].update()
                assert pr.pin(name,y)==(va^vb)
    print("  ✅ HC86: 12 XOR gates")

def test_hc21():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for a,b,c,d,exp in [(1,1,1,1,1),(1,1,1,0,0),(0,1,1,1,0)]:
        sw.pin('U33',1,a); sw.pin('U33',2,b); sw.pin('U33',4,c); sw.pin('U33',5,d)
        chips['U33'].update(); assert pr.pin('U33',6)==exp
    print("  ✅ HC21: 4-input AND")

def test_hc157():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    sw.pin('U15',15,0); sw.pin('U15',2,1); sw.pin('U15',3,0)
    sw.pin('U15',1,0); chips['U15'].update(); assert pr.pin('U15',4)==1
    sw.pin('U15',1,1); chips['U15'].update(); assert pr.pin('U15',4)==0
    sw.pin('U15',15,1); chips['U15'].update(); assert pr.pin('U15',4)==0
    print("  ✅ HC157: quad mux")

def test_hc283():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for a,b,cin,exp in [(5,3,0,8),(15,15,1,31),(0,0,0,0)]:
        sw.byte('U10',[5,3,14,12],a); sw.byte('U10',[6,2,15,11],b); sw.pin('U10',7,cin)
        chips['U10'].update()
        s = pr.byte('U10',[4,1,13,10]) | (pr.pin('U10',9)<<4)
        assert s==exp, f"{a}+{b}+{cin}={s}"
    print("  ✅ HC283: 4-bit adder")

def test_hc688():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    sw.pin('U22',1,0)
    for i in range(8):
        sw.pin('U22',[2,4,6,8,12,14,16,18][i],0)
        sw.pin('U22',[3,5,7,9,11,13,15,17][i],0)
    chips['U22'].update(); assert pr.pin('U22',19)==0  # equal
    sw.pin('U22',2,1); chips['U22'].update(); assert pr.pin('U22',19)==1  # not equal
    print("  ✅ HC688: 8-bit comparator")

def test_hc541():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    sw.byte('U14',[2,3,4,5,6,7,8,9],0xA5)
    sw.pin('U14',1,0); sw.pin('U14',19,0); chips['U14'].update()
    assert pr.byte('U14',[18,17,16,15,14,13,12,11])==0xA5
    sw.pin('U14',1,1); chips['U14'].update()
    assert pr.byte('U14',[18,17,16,15,14,13,12,11])==0
    print("  ✅ HC541: octal buffer")

def test_hc574():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for name in ['U5','U6','U9','U23','U32']:
        sw.pin(name,1,0); sw.byte(name,[2,3,4,5,6,7,8,9],0x5A)
        chips[name].clock_edge()
        assert pr.byte(name,[19,18,17,16,15,14,13,12])==0x5A
    print("  ✅ HC574: D latch (5 chips)")

def test_hc161():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for name in ['U1','U2','U3','U4']:
        sw.pin(name,1,0); chips[name].clock_edge()  # clear
        assert pr.byte(name,[14,13,12,11])==0
        sw.pin(name,1,1); sw.pin(name,9,1); sw.pin(name,7,1); sw.pin(name,10,1)
        chips[name].clock_edge(); assert pr.byte(name,[14,13,12,11])==1
        chips[name].clock_edge(); assert pr.byte(name,[14,13,12,11])==2
    print("  ✅ HC161: counter (4 chips)")

def test_hc164():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    sw.pin('U8',9,0); chips['U8'].clock_edge()  # clear
    assert pr.byte('U8',[3,4,5,6,10,11,12,13])==0
    sw.pin('U8',9,1); sw.pin('U8',1,1); sw.pin('U8',2,1)
    chips['U8'].clock_edge(); assert pr.pin('U8',3)==1
    sw.pin('U8',1,0); chips['U8'].clock_edge()
    assert pr.pin('U8',3)==0 and pr.pin('U8',4)==1
    print("  ✅ HC164: shift register")

def test_hc74():
    chips = create_cpu(); pr = Probe(chips); sw = Sw(chips)
    for name in ['U21','U31']:
        sw.pin(name,1,1); sw.pin(name,4,1); sw.pin(name,2,1)
        chips[name].clock_edge(); assert pr.pin(name,5)==1
        sw.pin(name,1,0); chips[name].update(); assert pr.pin(name,5)==0
        sw.pin(name,1,1); sw.pin(name,4,0); chips[name].update(); assert pr.pin(name,5)==1
    print("  ✅ HC74: D flip-flop (2 chips)")

def test_memory():
    chips = create_cpu()
    chips['ROM']._data[0]=0x42
    for i in range(15): chips['ROM'].set(i+1,0)
    chips['ROM'].set(24,0); chips['ROM'].set(25,0); chips['ROM'].update()
    d = sum(chips['ROM'].get(16+i)<<i for i in range(8))
    assert d==0x42
    # RAM write/read
    for i in range(15): chips['RAM'].set(i+1,(5>>i)&1)
    for i in range(8): chips['RAM'].set(16+i,(0x77>>i)&1)
    chips['RAM'].set(24,0); chips['RAM'].set(25,1); chips['RAM'].set(26,0)
    chips['RAM'].update(); assert chips['RAM']._data[5]==0x77
    chips['RAM'].set(26,1); chips['RAM'].set(25,0); chips['RAM'].update()
    assert sum(chips['RAM'].get(16+i)<<i for i in range(8))==0x77
    print("  ✅ ROM + RAM: memory")


if __name__=='__main__':
    print("="*60); print("RV8-GR Chip Behavior Test Suite"); print("="*60)
    test_hc04(); test_hc00(); test_hc32(); test_hc86(); test_hc21()
    test_hc157(); test_hc283(); test_hc688(); test_hc541()
    test_hc574(); test_hc161(); test_hc164(); test_hc74(); test_memory()
    print("="*60); print("ALL 14 CHIP TYPES VERIFIED ✅"); print("="*60)
