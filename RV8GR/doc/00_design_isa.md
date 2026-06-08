# RV8-GR — Design & ISA Reference (Stable)

**32 logic chips + ROM + RAM. No microcode. 64K. IRQ. Verilog verified.**

---

## Architecture

```
3 cycles/instruction: T0 fetch control, T1 fetch operand, T2 execute
Accumulator machine: AC hardwired to ALU A-input
Registers in RAM ($00-$07)
Control byte bits → hardware signals (no microcode ROM)
```

---

## Memory Map

```
$0000-$7FFF  RAM 32KB (registers, data, executable)
$8000-$FEFF  ROM 32KB (bankable to 128KB)
$FF00-$FF0F  ROM: IRQ vector + ISR entry
$FF10-$FF1F  I/O Slot 1 (via /SLOT1 on RV8-Bus)
$FF20-$FF2F  I/O Slot 2 (via /SLOT2 on RV8-Bus)
$FF30-$FFFF  ROM: ISR code
Reset → $8000
```

### RV8-Bus

40-pin system bus — เชื่อม CPU board กับ expansion:
- A[15:0], D[7:0] — address + data
- CLK, /RST, /WR, /RD — timing + control
- /IRQ — interrupt from peripheral
- /SLOT1, /SLOT2 — I/O device select

---

## Control Byte Encoding

```
Byte 0 (Control): [7]SUB [6]XOR [5]MUX [4]AC_WR [3]SRC [2]STR [1]BR [0]JMP
Byte 1 (Operand): immediate, RAM address, or jump target
```

| Bit | Name | =0 | =1 |
|:---:|------|----|----|
| 7 | SUB | ADD | SUB (invert + Cin=1) |
| 6 | XOR | B=SUB bit | B=AC (XOR instr) |
| 5 | MUX | AC←Adder | AC←XOR output |
| 4 | AC_WR | AC hold | AC latch |
| 3 | SRC | IBUS=immediate | IBUS=RAM[addr] |
| 2 | STR | — | RAM[addr]=AC |
| 1 | BR | — | Conditional PC load |
| 0 | JMP | — | Unconditional PC load |

---

## Instructions (18)

| Hex | Binary | Mnemonic | Operation |
|:---:|:------:|----------|-----------|
| $00 | 00000000 | NOP | No operation |
| $01 | 00000001 | J addr | PC = {PG, addr} |
| $02 | 00000010 | BEQ addr | if Z: PC = {PG, addr} |
| $04 | 00000100 | SB addr | RAM[{DP, addr}] = AC |
| $08 | 00001000 | EI | IE = 1 |
| $10 | 00010000 | ADDI imm | AC = AC + imm |
| $18 | 00011000 | ADD rs | AC = AC + RAM[{DP, rs}] |
| $20 | 00100000 | SETPG imm | PageReg = imm |
| $28 | 00101000 | SETPG_R rs | PageReg = RAM[{DP, rs}] |
| $30 | 00110000 | LI imm | AC = imm |
| $38 | 00111000 | LB rs | AC = RAM[{DP, rs}] |
| $40 | 01000000 | SETDP imm | DataPageReg = imm |
| $48 | 01001000 | DI | IE = 0 |
| $70 | 01110000 | XORI imm | AC = AC ^ imm |
| $78 | 01111000 | XOR rs | AC = AC ^ RAM[{DP, rs}] |
| $82 | 10000010 | BNE addr | if !Z: PC = {PG, addr} |
| $90 | 10010000 | SUBI imm | AC = AC - imm |
| $98 | 10011000 | SUB rs | AC = AC - RAM[{DP, rs}] |

DP = Data Page Register (8 bits). Data address = {DP, operand} = 16-bit (full 64KB).
- DP=$00-$7F → RAM read/write ($0000-$7FFF)
- DP=$80-$FF → ROM read only ($8000-$FFFF, SB has no effect)

---

## Aliases & Macros

| Alias | Actual | Meaning |
|-------|--------|---------|
| LB addr | $38 addr | Load byte from RAM |
| SB addr | $04 addr | Store byte to RAM |
| MV a0,rs | $38 rs | Load register |
| MV rd,a0 | $04 rd | Store register |
| SLL | ADD rs,rs | Shift left 1 |
| HLT | J self | Halt (loop) |
| CLR | LI $00 | Clear AC |
| INC | ADDI $01 | Increment |
| DEC | SUBI $01 | Decrement |
| $C0 imm | = SETDP imm | Alias (SUB bit ignored by decode) |

---

## Data Path

```
DBUS ←→ [U7 Bus Buffer] ←→ IBUS
                                │
          ┌─────────────────────┼──────────────┐
          │                     │              │
     [U23 Page Reg]      [U12-U13 XOR]   [U14 AC buf]
     D←IBUS              A←IBUS           A←AC
     Q→PC[15:8]          B←mux(SUB/AC)    Y→IBUS(store)
                               │
                        XOR output
                         ╱        ╲
                 [U10-U11]      [U17-U18]
                 Adder           AC mux
                 A←AC            SEL: Adder/XOR
                 B←XOR_out
                 SUM────────────────→ [U9 AC]
```

---

## Chip List (32)

| U# | Chip | Role |
|:--:|------|------|
| U1-U4 | 74HC161 ×4 | PC 16-bit |
| U5 | 74HC574 | IR control byte |
| U6 | 74HC574 | IR operand |
| U7 | 74HC245 | DBUS↔IBUS bridge |
| U8 | 74HC164 | Ring counter T0/T1/T2 |
| U9 | 74HC574 | Accumulator |
| U10-U11 | 74HC283 ×2 | Adder |
| U12-U13 | 74HC86 ×2 | XOR array |
| U14 | 74HC541 | AC output buffer |
| U15-U16 | 74HC157 ×2 | Addr mux A[7:0] |
| U17-U18 | 74HC157 ×2 | AC input mux |
| U19-U20 | 74HC157 ×2 | XOR B-input mux |
| U21 | 74HC74 | Z flag FF |
| U22 | 74HC688 | Zero detect |
| U23 | 74HC574 | Page Register (jump) |
| U24 | 74HC04 | Inverters |
| U25 | 74HC32 | OR gates + bus guard |
| U26-U27 | 74HC00 ×2 | NAND gates |
| U28 | 74HC86 | Z_match, /T2, WR_DIR |
| U29-U30 | 74HC157 ×2 | Addr mux A[15:8] |
| U31 | 74HC74 | IRQ_FF + IE_FF |
| U32 | 74HC574 | Data Page Register |
| U33 | 74HC21 | SETDP decode |

---

## Derived Signals

```
ADDR_MODE    = SRC | STR
PC_INC       = T0 | T1
/IRL_OE      = NAND(T2, /ADDR_MODE)
/AC_BUF      = NAND(T2, STR)
BUF_OE_SAFE  = BUF_OE_N | STR        ← SRC+STR guard
/PC_LD       = NAND(T2, PC_LOAD_COND)
PC_LOAD_COND = JMP | (BR & Z_match)
Z_match      = Z_flag XOR SUB
PG_Load_N    = /T2 | /PG_cond
DP_Load      = T2 & XOR_MODE & /ADDR_MODE & /AC_WR  ← U33
```

---

## IBUS Drivers (only one active at T2)

| Condition | Driver | Source |
|-----------|--------|--------|
| SRC=0, STR=0 | U6 (IRL) | Immediate |
| SRC=1, STR=0 | U7 (RAM) | RAM read |
| STR=1 | U14 (AC buf) | AC value |

Guard: STR=1 → U7 disabled via BUF_OE_SAFE

---

## IRQ (U31)

```
/IRQ pin (falling edge) → IRQ_FF latch
At T2 end: if IRQ_FF=1 AND IE=1 AND no jump → IRQ-ack:
  - Force PC = $FF00
  - Clear IE, clear IRQ_FF
```

**PC save**: v1.0 = software (programmer saves return addr to RAM[$0E:$0F] before EI).
v2.0 = hardware auto-save (requires 2-3 extra chips).

---

## Key Design Decisions

1. **XOR reuse** — Same gates do ADD/SUB/XOR via B-input mux
2. **A15 chip select** — ROM /CE=/A15, RAM /CE=A15 (no decoder)
3. **Bus guard** — BUF_OE_SAFE = BUF_OE_N OR STR (U25 gate 3)
4. **Z flag /PR trick** — U22→U21 async preset (0 extra gates)
5. **BNE reuse** — Z_match = Z XOR SUB (reuse SUB bit as condition flip)
6. **PG_Load timing** — Edge from /T2 (sync with CLK)

---

## Verification

| Test | Result |
|------|--------|
| `tb_rv8gr_full.v` | ALL PASS (127 cycles) |
| `tb_rv8gr_irq.v` | ALL PASS (6 tests) |
| `tb_rv8gr_tasks.v` | ALL PASS |
| Assembler | `rv8gr_asm.py` + test ROM |

Source of truth: `03_wiring_guide.md`

---

## What's Missing vs Full RV8

| Feature | RV8-GR | Full RV8 |
|---------|:------:|:--------:|
| AND | ❌ Software | ✅ |
| OR | ❌ Software | ✅ |
| SRL | ❌ Software | ✅ |
| JAL/JALR | ❌ Software | ✅ |
| Relative branch | ❌ Absolute | ✅ |
| Carry flag | ❌ | ✅ |
| Stack pointer | ❌ Software | ✅ |
| Multiple ALU ops | 3 (ADD/SUB/XOR) | 8+ |
