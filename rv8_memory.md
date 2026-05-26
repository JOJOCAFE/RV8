# RV8 Project — Session Memory

**Last updated**: 2026-05-27

---

## Focus: RV8-GR (redesigned, verified, ready for build)

### Architecture (29 chips):
- 3-cycle: T0=fetch ctrl, T1=fetch operand, T2=execute
- Ring counter (74HC164) for timing
- Full 64K: ROM $8000-$FFFF, RAM $0000-$7FFF
- A15 chip select: ROM /CE=NOT(A15), RAM /CE=A15
- Can execute from RAM (PC < $8000)
- Page Register for 16-bit jump
- XOR B-input mux for SUB/XOR dual-use
- AC input mux: adder (MUX=0) vs XOR output (MUX=1)
- No microcode — control byte bits drive hardware directly

### ISA (15 instructions):
    $00 NOP    $10 ADDI   $18 ADD    $90 SUBI   $98 SUB
    $70 XORI   $78 XOR    $30 LI     $38 MV a0  $04 MV rd
    $02 BEQ    $82 BNE    $01 J      $20 SETPG  $28 SETPG_R

### Key files:
    RV8GR/doc/Construct.md       ← SOURCE OF TRUTH (pin-level)
    RV8GR/rv8gr_cpu.v            ← Verilog (127 cycles pass)
    RV8GR/tb/tb_rv8gr_full.v     ← testbench

### Chip list (U1-U30):
    U1-U4:   PC (4× 74HC161)
    U5-U6:   IR_HIGH, IR_LOW (2× 74HC574)
    U7:      Bus buffer (74HC245)
    U8:      Ring counter (74HC164)
    U9:      Accumulator (74HC574)
    U10-U11: ALU adder (2× 74HC283)
    U12-U13: ALU XOR (2× 74HC86)
    U14:     AC buffer (74HC541)
    U15-U16: Addr mux A0-A7 (2× 74HC157)
    U17-U18: AC input mux (2× 74HC157)
    U19-U20: XOR B-input mux (2× 74HC157)
    U21:     Z flag (74HC74)
    U22:     Zero detect (74HC688)
    U23:     Page Register (74HC574)
    U24:     Inverters (74HC04)
    U25:     OR gates (74HC32)
    U26-U27: NAND gates (2× 74HC00)
    U28:     XOR gates (74HC86)
    U29-U30: Addr mux A8-A15 (2× 74HC157)

### What's next:
- Assembler (Python)
- Physical build on breadboard
- Programmer board (ESP32)
