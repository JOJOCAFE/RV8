# RV8-R — Minimal RISC-V with RAM Registers

**~18 logic chips. Full RISC-V ISA. 8 registers in RAM. Microcode ROM. 5 MHz.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | ~18 (target) |
| Total packages | ~21 (+ 2 ROM + 1 RAM) |
| ISA | RISC-V style, 35 instructions |
| Registers | 8 in RAM ($0000-$0007) |
| Clock | 5 MHz |
| Cycles/instr | 4-6 average |
| MIPS | 0.8-1.25 |
| Address space | 64KB (32K ROM + 32K RAM) |
| Execute from RAM | ✅ |
| Microcode | ROM (AT28C256, 70ns) |
| ALU | ADD, SUB, XOR (+AND/OR optional) |
| Standalone boot | ✅ (runs from ROM at power-on) |
| Programmable ISA | ✅ (change microcode ROM) |
| Target | BASIC + video games |

---

## Roadmap (RV8-GR style)

| # | Task | Status |
|:-:|------|:------:|
| 1 | Architecture design | ⬜ |
| 2 | ISA encoding (2-byte) | ⬜ |
| 3 | Microcode format + control word | ⬜ |
| 4 | Chip list + pin wiring | ⬜ |
| 5 | Verilog model | ⬜ |
| 6 | Testbench (all 35 instructions) | ⬜ |
| 7 | Assembler (Python) | ⬜ |
| 8 | Microcode generator (Python) | ⬜ |
| 9 | Gate-level simulation (sim_lab) | ⬜ |
| 10 | Documentation (Thai tutorial) | ⬜ |
| 11 | Programmer integration | ⬜ |
| 12 | Physical build | ⬜ |
| 13 | BASIC interpreter | ⬜ |
| 14 | Video game | ⬜ |

---

## Architecture (Draft)

```
┌──────────────┐     ┌──────────────┐
│ Microcode ROM│     │ Program ROM  │
│ AT28C256     │     │ AT28C256     │
│ 70ns         │     │ 70ns         │
│              │     │              │
│ Addr={op,stp}│     │ Addr=PC      │
│ Data=ctrl_wd │     │ Data=instr   │
└──────┬───────┘     └──────┬───────┘
       │ control word        │ instruction
       ▼                     ▼
┌────────────────────────────────────┐
│              CPU Datapath           │
│                                    │
│  PC(161×4) → Addr Mux → ABUS      │
│  DBUS ←→ RAM(CY7C199) ← registers │
│  IR(574) ← DBUS                   │
│  ALU(283+86) ← IBUS               │
│  Step(161) → Microcode addr        │
└────────────────────────────────────┘
```

### Memory Map

```
$0000-$0007  Registers r0-r7 (in RAM)
$0008-$00FF  Stack (sp starts at $FF)
$0100-$3FFF  Data / arrays / video buffer
$4000-$7FFF  RAM program (execute from RAM)
$8000-$FFFF  ROM program (BASIC, microcode table N/A here)
```

### Microcode ROM Address

```
Address[14:0] = {opcode[7:0], step[3:0], flags[2:0]}
  or simplified: {opcode[7:0], step[2:0]} = 11 bits (2048 entries)
Data[7:0] = control word (8 bits)
  If need 16-bit: use 2 ROMs or 2 reads per step
```

### Key Design Decisions

1. **Registers in RAM** — saves 8 chips (no 574×8), costs 1-2 extra cycles
2. **2 ROM chips** — one for microcode, one for program (no time-mux needed)
3. **Same RAM as RV8-GR** — 62256 or CY7C199 (pin-compatible)
4. **Same bus structure** — can reuse Programmer board + RV8-Bus
5. **Same ISA as RV8** — full 35 instructions, RISC-V style
6. **Microcode in ROM** — programmable ISA, just swap ROM chip

### Chip List (Target ~18)

| Module | Chips | Type |
|--------|:-----:|------|
| PC (15-bit) | 4 | 74HC161 |
| Step counter | 1 | 74HC161 |
| IR (opcode) | 1 | 74HC574 |
| IR (operand) | 1 | 74HC574 |
| ALU | 4 | 2× 283 + 2× 86 |
| Address mux | 2 | 74HC157 |
| Bus buffer | 1 | 74HC245 |
| Misc logic | 2 | 74HC04 + 74HC00 |
| Flag latch | 1 | 74HC74 |
| **Logic total** | **18** | |
| Microcode ROM | 1 | AT28C256-70 |
| Program ROM | 1 | AT28C256-70 |
| RAM | 1 | CY7C199-15PC (or 62256-70) |
| **Grand total** | **21 packages** | |

---

## Comparison

| | RV8 | **RV8-R** | RV8-GR |
|--|:---:|:---------:|:------:|
| Logic chips | 27 | **18** | 33 |
| Total packages | 31 | **21** | 35 |
| ISA | 35 (RISC-V) | **35 (RISC-V)** | 18 (custom) |
| Registers | 8 hardware | **8 in RAM** | 1 (AC) |
| Microcode | ✅ (Flash) | **✅ (ROM)** | ❌ |
| Clock | 5 MHz | **5 MHz** | 5 MHz |
| MIPS | 1.0-1.4 | **0.8-1.25** | 1.67 |
| Programmable ISA | ✅ | **✅** | ❌ |
| Execute from RAM | ✅ | **✅** | ✅ |
| BASIC + Games | ✅ | **✅** | ✅ |
| Fewest chips? | ❌ | **✅** | ❌ |

---

## Status

- ⬜ Architecture design
- ⬜ Everything else (follow RV8-GR development path)
