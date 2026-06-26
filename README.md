# RV8 Project: Minimal 8-bit RISC-V Style CPU Family

Build real computers from 74HC chips. Run BASIC. Play games.

---

## The Family

| | **RV8** | **RV8-R** | **RV8-G** | **RV8-GR** |
|--|:---:|:---:|:---:|:---:|
| **Logic chips** | 28 | **19** | **38** | **33** |
| **Total** | 31 | 22 | 40 | 35 |
| **MIPS @5MHz** | 1.25 | 1.0 | **2.5** | **0.33*** |
| **ISA** | Full (35) | Full (35) | Full (35) | 18 instr |
| **Microcode** | Yes | Yes | **No** | **No** |
| **AND/OR/XOR** | ✅ | ✅ | ✅ | XOR only |
| **64K address** | ✅ | ✅ | ✅ | ✅ |
| **Execute RAM** | ✅ | ✅ | ✅ | **✅** |
| **Games** | ✅ | ✅ | ✅ | ✅ |
| **Verilog verified** | ✅ | ✅ | ⬜ | **✅** |

\* RV8-GR: official student baseline is 1 MHz breadboard. 0.33 MIPS @ 1 MHz.

---

## Which to build?

| Priority | Build |
|----------|-------|
| **Learn microcode + proven** | **RV8** (28 chips) |
| **Fewest chips + full ISA** | **RV8-R** (19 chips) |
| **Full ISA + no microcode** | **RV8-G** (28 chips) |
| **Student-friendly no-microcode build** | **RV8GR-V2** (33 chips) |

### RV8GR-V2 Student Baseline

RV8GR-V2 is the active physical-build target.

- 33 logic chips + ROM + RAM = 35 packages.
- No microcode ROM.
- No hardware IRQ vector; IRQ is a polling latch only.
- Every instruction uses T0, T1, T2.
- Build one module, test it, then continue.
- Start with `RV8GR-V2/doc/labs/README.md` for student labs.
- Use `RV8GR-V2/doc/02_wiring_guide.md` as the official pin-level source.

---

## Project Structure

```
RV8/
├── RV8/            ← 28 chips, hardware regs, microcode, IRQ (proven)
├── RV8R/           ← 19 chips, RAM regs, microcode, IRQ (fewest + full ISA)
├── RV8G/           ← 28 chips, full ISA, no microcode, fastest
├── RV8GR-V1/       ← previous RV8-GR baseline/reference
├── RV8GR-V2/       ← active 33-chip student baseline, labs, wiring, sim, RTL
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
| Hardware Labs | ⬜ | ⬜ | ⬜ | ✅ (14 labs + student baseline contract) |
| KiCad modules | ⬜ | ⬜ | ⬜ | ✅ (6 modules) |
| Student build guardrails | ⬜ | ⬜ | ⬜ | ✅ |
| Programmer | ✅ | ✅ | ✅ | ✅ |
| Physical build | ⬜ | ⬜ | ⬜ | ⬜ |
