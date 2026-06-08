# RV8 Project: Minimal 8-bit RISC-V Style CPU Family

Build real computers from 74HC chips. Run BASIC. Play games.

---

## The Family

| | **RV8** | **RV8-R** | **RV8-G** | **RV8-GR** |
|--|:---:|:---:|:---:|:---:|
| **Logic chips** | 27 | **18** | **38** | **30** |
| **Total** | 29 | 21 | 40 | 32 |
| **MIPS @10MHz** | 1.25 | 1.0 | **2.5** | **3.3** |
| **ISA** | Full (35) | Full (35) | Full (35) | 17 instr |
| **Microcode** | Yes | Yes | **No** | **No** |
| **AND/OR/XOR** | ✅ | ✅ | ✅ | XOR only |
| **64K address** | ✅ | ✅ | ✅ | ✅ |
| **Execute RAM** | ❌ | ❌ | ✅ | **✅** |
| **Games** | ✅ | ✅ | ✅ | ✅ |
| **Verilog verified** | ✅ | ⬜ | ⬜ | **✅** |

---

## Which to build?

| Priority | Build |
|----------|-------|
| **Learn microcode + proven** | **RV8** (27 chips) |
| **Fewest chips + full ISA** | **RV8-R** (18 chips) |
| **Full ISA + no microcode** | **RV8-G** (28 chips) |
| **Fastest + execute from RAM** | **RV8-GR** (30 chips) |

---

## Project Structure

```
RV8/
├── RV8/            ← 27 chips, hardware regs, microcode (proven)
├── RV8R/           ← 18 chips, RAM regs, microcode (fewest + full ISA)
├── RV8G/           ← 28 chips, full ISA, no microcode, fastest
├── RV8GR/          ← 30 chips, 17 instr, no microcode, 64K, execute RAM, IRQ
├── Programmer/     ← ESP32 board (works with all)
├── Old_Design/     ← Archived
├── Reference/      ← Gigatron, SAP-1, Nand2Tetris
└── README.md
```

---

## Shared Across All

- **RV8-Bus**: 40-pin system bus (A[15:0] + D[7:0] + CLK + /WR + /RD + /IRQ + /SLOT)
- **Programmer**: ESP32 + TXB0108 (flash + terminal)
- **Registers**: 8 in RAM ($00-$07)
- **RISC-V naming**: ADD, SUB, LB, SB, BEQ, J

---

## Status

| | RV8 | RV8-R | RV8-G | RV8-GR |
|--|:---:|:---:|:---:|:---:|
| Instruction trace | ✅ | ✅ | ⬜ | ✅ |
| Verilog | ✅ 8/8 | ⬜ | ⬜ | ✅ (127 cycles) |
| Wiring guide (pin-level) | ✅ | ⬜ | ✅ | ✅ |
| Wiring Guide | ✅ | ✅ | ⬜ | ✅ |
| Module guide (Thai) | ✅ | ⬜ | ⬜ | ✅ |
| ISA reference | ✅ | ⬜ | ⬜ | ✅ |
| Assembler | ⬜ | ⬜ | ⬜ | ✅ |
| Test ROM | ⬜ | ⬜ | ⬜ | ✅ |
| Programmer | ✅ | ✅ | ✅ | ✅ |
| Physical build | ⬜ | ⬜ | ⬜ | ⬜ |
