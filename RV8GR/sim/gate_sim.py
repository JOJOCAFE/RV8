#!/usr/bin/env python3
"""
RV8-GR Gate-Level Simulation (Simplified)
Models key chips to understand timing and data flow.
Not a full verification — use chip_sim.py for that.
"""

class RV8GR:
    def __init__(self):
        self.pc = 0x0000
        self.ir_high = 0x00
        self.ir_low = 0x00
        self.ac = 0x00
        self.page_reg = 0x00
        self.phase = 0  # 0=T0, 1=T1, 2=T2
        self.ie = 0
        self.rom = bytearray(32768)
        self.rom[0] = 0x30; self.rom[1] = 0x42  # LI $42
        self.rom[2] = 0x01; self.rom[3] = 0x02  # J $02 (halt)

    def tick(self):
        """One clock cycle = one phase advance."""
        if self.phase == 0:  # T0: fetch control
            self.ir_high = self.rom[self.pc] if self.pc < 0x8000 else 0
            self.pc = (self.pc + 1) & 0xFFFF
        elif self.phase == 1:  # T1: fetch operand
            self.ir_low = self.rom[self.pc] if self.pc < 0x8000 else 0
            self.pc = (self.pc + 1) & 0xFFFF
        elif self.phase == 2:  # T2: execute
            if self.ir_high & 0x01:  # JUMP
                self.pc = (self.page_reg << 8) | self.ir_low
            elif self.ir_high & 0x10:  # AC_WR
                # Simplified: LI = pass-through
                self.ac = self.ir_low
        self.phase = (self.phase + 1) % 3

    def trace(self):
        phases = ['T0', 'T1', 'T2']
        print(f"PC=${self.pc:04X} | {phases[self.phase]} | "
              f"IR=${self.ir_high:02X},{self.ir_low:02X} "
              f"AC=${self.ac:02X} | IE={self.ie}")

if __name__ == "__main__":
    cpu = RV8GR()
    print("RV8-GR Simplified Gate Sim: LI $42, J self")
    print("=" * 50)
    for i in range(9):
        cpu.tick()
        cpu.trace()
    assert cpu.ac == 0x42, f"FAIL: AC=${cpu.ac:02X}, expected $42"
    print(f"\n✅ PASS: AC=$42")
