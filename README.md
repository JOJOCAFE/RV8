# RV8 Project: Minimal 8-bit RISC-V Style CPU Family

Build real computers from 74HC chips. Run BASIC. Play games.

---

## The Family

| | **RV8** | **RV8-R** | **RV8-G** | **RV8-GR** |
|--|:---:|:---:|:---:|:---:|
| **Logic chips** | 28 | **19** | **38** | **33** |
| **Total** | 31 | 22 | 40 | 35 |
| **MIPS @5MHz** | 1.25 | 1.0 | **2.5** | **0.33*** |

\* RV8-GR: 1 MHz breadboard, 4 MHz PCB. 0.33 MIPS @ 1 MHz. 1.33 MIPS @ 4 MHz PCB.
| **ISA** | Full (35) | Full (35) | Full (35) | 18 instr |
| **Microcode** | Yes | Yes | **No** | **No** |
| **AND/OR/XOR** | ✅ | ✅ | ✅ | XOR only |
| **64K address** | ✅ | ✅ | ✅ | ✅ |
| **Execute RAM** | ✅ | ✅ | ✅ | **✅** |
| **Games** | ✅ | ✅ | ✅ | ✅ |
| **Verilog verified** | ✅ | ✅ | ⬜ | **✅** |

---

## Which to build?

| Priority | Build |
|----------|-------|
| **Learn microcode + proven** | **RV8** (28 chips) |
| **Fewest chips + full ISA** | **RV8-R** (19 chips) |
| **Full ISA + no microcode** | **RV8-G** (28 chips) |
| **Fastest + execute from RAM** | **RV8-GR** (33 chips) |

---

## Project Structure

```
RV8/
├── RV8/            ← 28 chips, hardware regs, microcode, IRQ (proven)
├── RV8R/           ← 19 chips, RAM regs, microcode, IRQ (fewest + full ISA)
├── RV8G/           ← 28 chips, full ISA, no microcode, fastest
├── RV8GR/          ← 33 chips, 18 instr, no microcode, 64K, execute RAM, IRQ
├── Programmer/     ← ESP32 board (works with all)
├── Old_Design/     ← Archived
├── Reference/      ← Gigatron, SAP-1, Nand2Tetris
└── README.md
```

---

## Shared Across All

- **RV8-Bus**: 40-pin system bus (A[15:0] + D[7:0] + CLK + /WR + /RD + /IRQ + /SLOT)
- **Programmer**: ESP32-WROOM-32 + TXS0108E (flash + terminal)
- **Registers**: 8 in RAM ($00-$07 via Data Page)
- **RISC-V naming**: ADD, SUB, LB, SB, BEQ, J

---

## Status

| | RV8 | RV8-R | RV8-G | RV8-GR |
|--|:---:|:---:|:---:|:---:|
| Instruction trace | ✅ | ✅ | ⬜ | ✅ |
| Verilog | ✅ 8/8 | ✅ (141 cycles) | ⬜ | ✅ (5 TBs, 512 opcode sweep) |
| Wiring guide (pin-level) | ✅ | ⬜ | ✅ | ✅ |
| Wiring Guide | ✅ | ✅ | ⬜ | ✅ |
| Module guide (Thai) | ✅ | ⬜ | ⬜ | ✅ |
| ISA reference | ✅ | ✅ | ⬜ | ✅ |
| Assembler | ⬜ | ⬜ | ⬜ | ✅ (page-safe) |
| Test ROM | ⬜ | ⬜ | ⬜ | ✅ |
| Hardware Labs | ⬜ | ⬜ | ⬜ | ✅ (14 labs) |
| KiCad modules | ⬜ | ⬜ | ⬜ | ✅ (6 modules) |
| Programmer | ✅ | ✅ | ✅ | ✅ |
| Physical build | ⬜ | ⬜ | ⬜ | ⬜ |