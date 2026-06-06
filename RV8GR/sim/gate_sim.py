#!/usr/bin/env python3
"""
RV8-GR Gate-Level Simulation (Simplified)
Models key chips to understand timing and data flow.
"""

class Wire:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
    def __repr__(self): return f"{self.name}={self.value}" if self.value is not None else f"{self.name}=?"

class HC164_RingCounter:
    """Ring counter: T0 → T1 → T2 → T0"""
    def __init__(self, name):
        self.name = name
        self.state = 0  # 0=T0, 1=T1, 2=T2

    def update(self, clk, clr):
        if clr and clr.value == 0: self.state = 0
        elif clk and hasattr(clk, 'rising') and clk.rising:
            self.state = (self.state + 1) % 3
        self.t0 = 1 if self.state == 0 else 0
        self.t1 = 1 if self.state == 1 else 0
        self.t2 = 1 if self.state == 2 else 0

class HC574:
    """Octal D flip-flop (register)"""
    def __init__(self, name):
        self.name = name
        self.q = [0] * 8

    def update(self, clk, d0_d7):
        if clk and hasattr(clk, 'rising') and clk.rising:
            for i in range(8):
                if d0_d7[i]: self.q[i] = d0_d7[i].value

class RV8GR:
    def __init__(self):
        self.clk = Wire("CLK", 0)
        self.rst_n = Wire("RST_n", 1)
        self.ring = HC164_RingCounter("U8")
        self.ir_high = HC574("U5")
        self.ir_low = HC574("U6")
        self.ac = HC574("U9")
        self.page_reg = HC574("U23")
        self.pc = 0x8000
        self.ie = 0
        self.irq_ff = 0
        self.rom = [0] * 32768
        self.ram = [0] * 32768
        self.load_test_program()

    def load_test_program(self):
        self.rom[0] = 0x30; self.rom[1] = 0x42  # LI $42
        self.rom[2] = 0x01; self.rom[3] = 0x02  # J $8002 (halt)

    def tick(self):
        prev = self.clk.value
        self.clk.value = 1 - self.clk.value
        self.clk.rising = (prev == 0 and self.clk.value == 1)
        self.ring.update(self.clk, self.rst_n)

        if self.ring.state == 0:  # T0: fetch control
            ctrl = self.rom[self.pc - 0x8000]
            for i in range(8): self.ir_high.q[i] = (ctrl >> (7-i)) & 1
            self.pc += 1
        elif self.ring.state == 1:  # T1: fetch operand
            op = self.rom[self.pc - 0x8000]
            for i in range(8): self.ir_low.q[i] = (op >> (7-i)) & 1
            self.pc += 1
        elif self.ring.state == 2:  # T2: execute
            ctrl = sum(self.ir_high.q[i] << (7-i) for i in range(8))
            if ctrl & 1:  # JUMP
                self.pc = (self.page_reg.q[0] << 8) | self.ir_low.q[0]
            elif ctrl & 0x10:  # AC_WR
                self.ac.q[0] = self.ir_low.q[0]

    def trace(self):
        print(f"PC=${self.pc:04X} | T0={self.ring.t0} T1={self.ring.t1} T2={self.ring.t2} | "
              f"IR=${sum(self.ir_high.q[i] << (7-i) for i in range(8)):02X} "
              f"AC=${self.ac.q[0]:02X} | IE={self.ie}")

if __name__ == "__main__":
    cpu = RV8GR()
    print("RV8-GR Simulation: LI $42, J self")
    print("=" * 50)
    for i in range(10):
        cpu.tick()
        cpu.trace()