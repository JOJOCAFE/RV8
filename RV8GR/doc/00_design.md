# RV8-GR — Design Document

**30 logic chips. No microcode. Full 64K. 16-bit jump. IRQ. Verified.**

---

## Architecture

- Accumulator (AC) hardwired to ALU A input
- Registers in RAM ($00-$07)
- 3-cycle execution: T0=fetch control, T1=fetch operand, T2=execute
- Control byte bits directly drive hardware
- 8-bit ALU: adder + XOR (shared chips for SUB and XOR instruction)
- Page Register for full 16-bit jump
- Ring counter (74HC164) generates T0/T1/T2 one-hot
- A15-based chip select: ROM $8000-$FFFF, RAM $0000-$7FFF
- Full 16-bit address mux (4× 74HC157)

## Memory Map

    $0000-$7FFF  RAM (32KB) — registers, data, executable
    $8000-$FFFF  ROM (32KB, bankable to 128KB)
    PC resets to $8000

## Data Path

    DBUS ←→ U7(245) ←→ IBUS
                           │
             ┌─────────────┼──────────────────┐
             │             │                  │
             ▼             ▼                  ▼
        U23(PG)       U12-U13(XOR)       U14(AC buf)
        D←IBUS        A←IBUS             A←AC
        Q→PC[15:8]    B←mux(SUB/AC)     Y→IBUS
                           │
                    XOR output
                      │       │
                      ▼       ▼
               U10-U11    U17-U18
               (Adder)    (AC mux B)
               A←AC           │
               B←XOR_out      │
               SUM→AC mux A   │
                      └─ SEL ─┘
                           │
                           ▼
                      U9 (AC)

## Chip List (30 logic)

| U# | Chip | Function |
|:--:|------|----------|
| U1-U4 | 74HC161 ×4 | PC (16-bit) |
| U5 | 74HC574 | IR_HIGH (control) |
| U6 | 74HC574 | IR_LOW (operand) |
| U7 | 74HC245 | Bus buffer |
| U8 | 74HC164 | Ring counter |
| U9 | 74HC574 | Accumulator |
| U10-U11 | 74HC283 ×2 | ALU adder |
| U12-U13 | 74HC86 ×2 | ALU XOR |
| U14 | 74HC541 | AC → IBUS buffer |
| U15-U16 | 74HC157 ×2 | Address mux A0-A7 |
| U17-U18 | 74HC157 ×2 | AC input mux |
| U19-U20 | 74HC157 ×2 | XOR B-input mux |
| U21 | 74HC74 | Z flag |
| U22 | 74HC688 | Zero detect |
| U23 | 74HC574 | Page Register |
| U24 | 74HC04 | Inverters (×6) |
| U25 | 74HC32 | OR gates (×4) |
| U26-U27 | 74HC00 ×2 | NAND gates (×8) |
| U28 | 74HC86 | XOR (Z_match, /T2, WR_DIR) |
| U29-U30 | 74HC157 ×2 | Address mux A8-A15 |
| U31 | 74HC74 | IRQ_FF + IE_FF |

## Key Design Decisions

1. **XOR encoding $70/$78** (MUX_SEL=1): XOR output goes to AC mux B-input. When XOR_MODE=0, XOR passes IBUS through (for LI/MV). When XOR_MODE=1, XOR computes AC^IBUS.

2. **A15 chip select**: ROM /CE = NOT(A15), RAM /CE = A15. Enables executing code from RAM and accessing full 64K.

3. **U7 DIR gated**: WR_DIR = NOT(/AC_BUF) = T2 AND STORE. Prevents bus conflict during fetch after STORE instruction.

4. **Z flag /PR trick**: U22 (688) /P=Q output directly presets U21 (74) when AC=0. No inverter needed.

5. **PG_Load timing**: PG_Load_N = /T2 OR /PG_cond. Rising edge at T2→T0 transition latches IBUS into Page Register.

## Verification

- Verilog: `rv8gr_cpu.v` — all tests pass (127 cycles + IRQ tests)
- Testbench: `tb/tb_rv8gr_full.v` — covers all ISA + 64K jump + subroutine
- Testbench: `tb/tb_rv8gr_irq.v` — EI/DI, IRQ fire, PC save, nested prevention
- Source of truth: `doc/Construct.md` (pin-level wiring)

## Interrupt (IRQ)

**1 extra chip: U31 (74HC74) — dual flip-flop for IRQ_FF + IE_FF.**

### Signals

| Signal | Direction | Description |
|--------|-----------|-------------|
| /IRQ | Input (active-low) | Edge-triggered interrupt request |
| IE | Internal | Interrupt Enable flag (U31 FF-A) |
| IRQ_FF | Internal | Latched pending interrupt (U31 FF-B) |

### Instructions

| Hex | Mnemonic | Operation |
|:---:|----------|-----------|
| $08 | EI | Set IE=1 (enable interrupts) |
| $48 | DI | Clear IE=0 (disable interrupts) |

### Behavior

1. Falling edge of /IRQ latches IRQ_FF=1
2. At end of T2, if IRQ_FF=1 AND IE=1 AND no jump in progress:
   - Save PC to RAM[$0E] (low) and RAM[$0F] (high)
   - Jump to vector $FF00
   - Clear IE (prevent nesting)
   - Clear IRQ_FF
3. If a jump/branch is in progress, IRQ is deferred to next instruction

### ISR Pattern

```asm
; ISR at $FF00
    SB $08          ; save AC
    ; ... handle device ...
    LB $08          ; restore AC
    ; Return to saved PC:
    LB $0F          ; load saved PC high
    SETPG_R $0F     ; page = saved high (via register)
    EI              ; re-enable before return
    LB $0E          ; load saved PC low to AC... 
    ; (needs indirect jump — use known return or SETPG+J)
```

### Hardware Notes

- U31 pin A: IE flip-flop — SET by EI decode, CLR by IRQ-ack or DI decode
- U31 pin B: IRQ latch — SET by /IRQ falling edge, CLR by IRQ-ack
- IRQ-ack = T2 AND IRQ_FF AND IE AND NOT(pc_load)
- PC force: gates page_reg load ($FF) and ir_low force ($00) during ack
- PC save: extra RAM write cycle using spare gate timing (or force address mux)
