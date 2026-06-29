# RV8-R — Minimal RISC-V with RAM Registers

**FullHW target: 49 logic chips. RV8-style ISA. 8 registers in RAM. Microcode ROM. 5 MHz.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 49 FullHW target |
| Total packages | 53 FullHW target (+ 2 microcode ROM + 1 program ROM + 1 RAM) |
| ISA | RV8-style full hardware surface; `SRL` remains software macro, `LUI` assembler pre-shift |
| Registers | 8 in RAM at `$FFF8-$FFFF` |
| Reset PC | `$0000` |
| Boot source | Program ROM first (`$0000-$7FFF`) |
| Clock | 5 MHz |
| Cycles/instr | 4-6 average |
| MIPS | 0.8-1.25 |
| Address space | 64KB (32K ROM + 32K RAM) |
| Execute from RAM | ✅ optional at `$8000-$FFFF` after ROM boot |
| Microcode | 2× ROM, 15-bit address with IRQ bank and 4-bit step |
| ALU | ADD, SUB, AND, OR, XOR, SLL, SLT/SLTI via carry/borrow path |
| Standalone boot | ✅ reset clears PC to `$0000`, first fetch is ROM |
| Programmable ISA | ✅ (change microcode ROM) |
| Interrupts | ✅ `/IRQ`, `EI`, `DI`, `IRET`, fixed vector `$7F00` in frozen architecture |
| Target | BASIC + video games |

---

## Roadmap (RV8-GR style)

| # | Task | Status |
|:-:|------|:------:|
| 1 | Architecture design | ✅ |
| 2 | ISA encoding (2-byte) | ✅ |
| 3 | Microcode format + control word | ✅ FullHW 15-bit direct-control target |
| 4 | Chip list + pin wiring | ✅ real FullHW paths documented; KiCad proof pending |
| 5 | Verilog model | ⚠️ needs migration to frozen ROM-low/RAM-high map |
| 6 | Testbench | ⚠️ old `$8000` reset map passed; frozen map test pending |
| 7 | Assembler (Python) | ⬜ |
| 8 | Microcode generator (Python) | ⚠️ legacy 14-bit prototype; FullHW 15-bit generator pending |
| 9 | Gate-level simulation (sim_lab) | ⬜ |
| 10 | Documentation (Thai tutorial) | ⬜ |
| 11 | Programmer integration | ⬜ needs RV8-Bus pin audit |
| 12 | Physical build | ⬜ |
| 13 | BASIC interpreter | ⬜ |
| 14 | Video game | ⬜ |

Task details are tracked in `doc/03_fullhw_task_plan.md`.

---

## Architecture (Prototype)

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
Reset PC = $0000. The CPU always boots from Program ROM first.

$0000-$7FFF  Program ROM (boot, monitor, BASIC, game cartridge)
$7F00-$7FFF  ROM monitor / IRQ handler area
$8000-$FEFF  RAM data, buffers, optional RAM-loaded program
$FF00-$FFF5  RAM stack / fast page
$FFF6-$FFF7  RAM IRQ saved PC low/high
$FFF8-$FFFF  RAM registers r0-r7
```

### Microcode ROM Address

```
Address[14:0] = {irq_active, flag_C, flag_Z, step[3:0], opcode[7:0]}
Data[15:0] = direct control word from two microcode ROMs
```

### Key Design Decisions

1. **Registers in RAM** — saves 8 chips (no 574×8), costs 1-2 extra cycles
2. **3 ROM chips** — two microcode ROMs plus one program ROM (no time-mux needed)
3. **Same RAM as RV8-GR** — 62256 or CY7C199 (pin-compatible)
4. **RV8-Bus-like structure** — Programmer reuse is not frozen until pin audit
5. **ROM-first standalone boot** — reset clears PC to `$0000`; ROM occupies the lower half like RV8GR
6. **RV8-style ISA** — real FullHW paths for the full target surface; `SRL` stays a software macro
7. **Microcode in ROM** — programmable ISA, just swap ROM chip

### Chip List (FullHW Target)

| Module | Chips | Type |
|--------|:-----:|------|
| PC + step | 5 | 4× 74HC161 PC, 1× 74HC161 step[3:0] |
| IR/latches/registers | 7 | opcode, operand, ALU_B, result, address low/high, halt |
| ALU arithmetic/logic | 12 | add/sub, AND, OR, XOR, result mux |
| Address/PC routing | 14 | address-source muxes, ABUS muxes, PC-to-IBUS buffers |
| Bus/memory bridge | 1 | 74HC245 |
| Flags/IRQ/SYS/gates | 10 | flags, IE/IRQ, SYS decode, r0 guard, enable gates |
| **Logic total** | **49** | |
| Microcode ROM | 2 | AT28C256-70 / SST39SF010 |
| Program ROM | 1 | AT28C256-70 |
| RAM | 1 | CY7C199-15PC (or 62256-70) |
| **Grand total** | **53 packages** | |

---

## Comparison

| | RV8 | **RV8-R** | RV8-GR |
|--|:---:|:---------:|:------:|
| Logic chips | 27 | **49 FullHW** | 33 |
| Total packages | 31 | **53 FullHW** | 35 |
| ISA | 35 (RISC-V) | **RV8-style subset/prototype** | 18 (custom) |
| Registers | 8 hardware | **8 in high RAM** | 1 (AC) |
| Microcode | ✅ (Flash) | **✅ (ROM)** | ❌ |
| Clock | 5 MHz | **5 MHz** | 5 MHz |
| MIPS | 1.0-1.4 | **0.8-1.25** | 1.67 |
| Programmable ISA | ✅ | **✅** | ❌ |
| ROM-first boot | ✅ | **✅** | ✅ |
| BASIC + Games | ✅ | **✅** | ✅ |
| Fewest chips? | ❌ | ❌ FullHW favors real full-ISA paths | ❌ |

---

## Status

- ✅ Architecture concept and ISA encoding drafted
- ⚠️ Behavioral Verilog core + IRQ test passed on the previous `$8000` reset map; RTL/testbench migration to this frozen map is pending
- ⚠️ Legacy microcode generator still uses 14-bit prototype output; FullHW needs a 15-bit direct-control generator
- ✅ FullHW chip/pin paths are now concrete in `doc/02_wiring_guide.md`
- ⚠️ Chip count is now 49 logic / 53 packages for the full-ISA hardware path
- ✅ `SLT`, `SLTI`, `PUSH`, `POP`, IRQ, and IRET have real hardware paths in FullHW; RTL/KiCad proof is pending
- ⬜ Assembler, pin-level final wiring, gate-level sim, Programmer pin audit, Thai tutorial, and physical build
