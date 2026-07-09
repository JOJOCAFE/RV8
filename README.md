# RV8 Project: Minimal 8-bit RISC-V Style CPU Family

Build real computers from 74HC chips. Run BASIC. Play games.

---

## The Family

| | **RV8** | **RV8-R** | **RV8-G** | **RV8-GR** |
|--|:---:|:---:|:---:|:---:|
| **Logic chips** | 28 | **49 FullHW** | **38** | **34** |
| **Total** | 31 | 53 | 40 | 36 |
| **MIPS @5MHz** | 1.25 | 1.0 | **2.5** | **0.33*** |
| **ISA** | Full target, not frozen | FullHW RV8-style surface | Full (35) | 18 instr |
| **Microcode** | Yes | Yes | **No** | **No** |
| **AND/OR/XOR** | ✅ | ✅ | ✅ | XOR only |
| **64K address** | ✅ | ✅ | ✅ | ✅ |
| **ROM-first boot** | ✅ | ✅ | ✅ | **✅** |
| **Games** | ✅ | ✅ | ✅ | ✅ |
| **Verilog verified** | ⚠️ behavioral only / benches need cleanup | ⚠️ old-map RTL pass; frozen-map pending | ⬜ | **✅** |

\* RV8-GR: official student baseline is 1 MHz breadboard. 0.33 MIPS @ 1 MHz.

---

## Which to build?

| Priority | Build |
|----------|-------|
| **Learn microcode / experimental reference** | **RV8** (28 chips target, not build-ready) |
| **Full RV8-style ISA with real TTL paths** | **RV8-R FullHW** (49 logic chips, KiCad/RTL proof pending) |
| **Full ISA + no microcode concept** | **RV8-G** (38 logic chips, no active folder) |
| **Student-friendly no-microcode build** | **RV8GR** (34 logic chips) |

### RV8GR Student Baseline

RV8GR is the active physical-build target.

- 34 logic chips + ROM + RAM = 36 packages.
- No microcode ROM.
- No hardware IRQ vector; IRQ is a polling latch only.
- Every instruction uses T0, T1, T2.
- Build one module, test it, then continue.
- Start with `RV8GR/doc/labs/README.md` for student labs.
- Use `RV8GR/doc/02_wiring_guide.md` as the official pin-level source.

### RV8 vs RV8-R Analysis

| Area | RV8 | RV8-R |
|------|-----|-------|
| Current role | Exploratory microcoded reference | FullHW full-ISA TTL path candidate |
| Chip-count confidence | ⚠️ Docs disagree between 27/28/31 package claims | ✅ FullHW count documented as 49 logic / 53 total |
| ISA confidence | ⚠️ Full 35-instruction target, but generator contains simplified/skipped operations | ✅ FullHW gives real paths for ALU logic, stack, IRQ, and IRET; `SRL` remains software macro |
| Verification | ⚠️ Behavioral Verilog exists; microcode benches need cleanup before claiming pass | ⚠️ FullHW docs updated; RTL/testbench/microcode generator migration pending |
| Microcode tools | ⚠️ Generator exists but has simplified branch/addressing/logic paths | ⚠️ Existing generator is legacy 14-bit; FullHW needs 15-bit direct-control generator |
| Wiring | ⚠️ Pin-level guide exists but is tied to stale chip-count/control assumptions | ✅ FullHW wiring paths documented; Programmer/RV8-Bus pin audit still required |
| Build readiness | Not ready for student physical build | Not ready for physical build until KiCad/ERC and sim proof |

**Decision:** keep RV8 as a learning/reference branch, but do not present it as proven. Use RV8-R FullHW when the goal is to make the full RV8-style ISA real in TTL, and use RV8GR when the goal is a student-buildable physical CPU today.

---

## Project Structure

```
RV8/
├── RV8/            ← 28-chip target, hardware regs, microcode, IRQ (exploratory)
├── RV8R/           ← 49-chip FullHW target, RAM regs, microcode, IRQ (full RV8-style hardware)
├── RV8GR/          ← active 34-logic-chip student baseline, labs, wiring, sim, RTL
├── Programmer/     ← ESP32 board; per-CPU bus/pin audit required
├── Old_Design/     ← Archived
├── Reference/      ← Gigatron, SAP-1, Nand2Tetris
└── README.md
```

`RV8-G` is retained as a documented concept/history item, not as an active
folder in this checkout.

---

## Shared Across All

- **RV8-Bus**: 40-pin system bus target (A[15:0] + D[7:0] + CLK + /WR + /RD + /IRQ + /SLOT)
- **Programmer**: ESP32-WROOM-32 + TXS0108E (flash + terminal); compatibility must be checked per CPU wiring guide
- **Registers**: Variant-specific RAM window. RV8R freezes `r0-r7` at `$FFF8-$FFFF`; RV8GR uses its own data-page model.
- **RISC-V naming**: ADD, SUB, LB, SB, BEQ, J

---

## Status

| | RV8 | RV8-R | RV8-G | RV8-GR |
|--|:---:|:---:|:---:|:---:|
| Instruction trace | ✅ | ✅ | ⬜ | ✅ |
| Verilog | ⚠️ benches need cleanup | ⚠️ old-map RTL passed; FullHW RTL pending | ⬜ | ✅ (behavioral + chip-level TBs, 512 opcode sweep) |
| Wiring guide (pin-level) | ⚠️ stale assumptions | ✅ FullHW paths documented | ⬜ | ✅ |
| Module guide (Thai) | ✅ | ⬜ | ⬜ | ✅ |
| ISA reference | ⚠️ target ISA, not fully proven | ✅ FullHW encoding + hardware paths | ⬜ | ✅ |
| Assembler | ⬜ | ⬜ | ⬜ | ✅ (page-safe) |
| Test ROM | ⬜ | ⬜ | ⬜ | ✅ |
| Hardware Labs | ⬜ | ⬜ | ⬜ | ✅ (14 labs + student baseline contract) |
| KiCad modules | ⬜ | ⬜ | ⬜ | ✅ (6 modules) |
| Student build guardrails | ⬜ | ⬜ | ⬜ | ✅ |
| Programmer | ⚠️ needs bus/pin audit | ⚠️ needs bus/pin audit | ⚠️ needs bus/pin audit | ✅ |
| Physical build | ⬜ | ⬜ | ⬜ | ⬜ |
