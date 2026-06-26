# RV8-R Architecture Design Document

## Overview

RV8-R FullHW is an 8-bit RV8-style CPU targeting 49 logic chips plus 2 microcode ROMs, 1 program ROM, and 1 RAM package (53 total). It keeps programmer-visible registers in high RAM, uses direct-control microcode for instruction sequencing, and boots standalone from low ROM.

**Target**: Middle school students (Thai language documentation available)  
**Clock**: 5 MHz  
**Performance**: ~0.91 MIPS (5.5 avg cycles/instruction)  
**ISA**: RV8-style native core with prototype, macro, and reserved slots

---

## Specs

| Feature | Value |
|:--------|:------|
| Logic chips | 49 FullHW target (74HC series) |
| ROM packages | 3 (2× microcode ROM + 1× program ROM) |
| RAM packages | 1 (CY7C199 or 62256) |
| Total packages | 53 |
| Register file | 8 × 8-bit at RAM `$FFF8-$FFFF` |
| Address space | 64 KB |
| Reset PC | `$0000` |
| Boot source | Program ROM at `$0000-$7FFF` |
| Microcode | 16-bit direct-control, 15-bit address with IRQ bank |
| Flags | Z (zero), C (carry/borrow) |
| Interrupts | `/IRQ` input, IE latch, IRQ pending latch, fixed vector `$7F00` |
| Execute from | ROM at reset; RAM execution optional at `$8000-$FFFF` after boot |

---

## Control Word Encoding (FullHW direct control)

```
Address[14:0] = {IRQ_ACTIVE, flag_C, flag_Z, step[3:0], opcode[7:0]}
Data[15:0]    = direct control word from two microcode ROMs
```

The older 8-bit group-encoded control sketch is superseded for FullHW because
it hid too many real enable signals behind decode prose. FullHW uses direct
control lines so every bus driver, address source, ALU operation, PC load, RAM
write, IRQ action, and halt action can be pinned and probed.

### Direct Control Lines

| Bits | Signal group | Purpose |
|------|--------------|---------|
| ROM0[0] | `BUF_OE_n` | Enable U12 memory data bridge |
| ROM0[1] | `BUF_DIR` | Select memory read/write direction |
| ROM0[2] | `OPR_OE_n` | Let operand register drive IBUS |
| ROM0[3] | `ALUR_OE_n` | Let ALU result latch drive IBUS |
| ROM0[4] | `ALUB_CLK` | Load ALU_B latch |
| ROM0[5] | `ALUR_CLK` | Load ALU result latch |
| ROM0[6] | `FLAGS_CLK` | Load Z/C flags |
| ROM0[7] | `RAM_WE_n` | Write RAM when address selects RAM |
| ROM1[0] | `PC_INC` | Count PC during fetch |
| ROM1[1] | `PC_LOAD_n` | Load PC from address register |
| ROM1[2] | `AR_LO_CLK` | Load address low register |
| ROM1[3] | `AR_HI_CLK` | Load address high register |
| ROM1[5:4] | `ADDR_SRC[1:0]` | Select normal, register, fast/IRQ, or vector/PC address source |
| ROM1[7:6] | `ALU_SEL[1:0]` | Select ADD/SUB, AND, OR, XOR result |

Extra decoded controls from opcode/operand and small gates are `ALU_SUB`,
`ALU_CIN`, `CONST_OE`, `SEXT_OE`, `PC_LO_OE`, `PC_HI_OE`, `REG_SEL[1:0]`,
`SYS_EI`, `SYS_DI`, `SYS_IRET`, `IRQ_ACK`, `HALT_SET`, and `STEP_RST`.

### Legacy 8-bit Group Sketch (superseded by FullHW)

The tables below describe the older low-chip control idea. They are kept as
design history only. FullHW uses the direct control lines above.

#### GROUP 00: BUS/MEMORY

| Bits [5:3] | Source | Bits [2:0] | Flags |
|:----------|:-------|:----------|:------|
| 000 | MEM[PC] → IR | [2] PC_INC |
| 001 | MEM[PC] → OPR | [1] end |
| 010 | MEM[rd] → REG_A | [0] save_flags |
| 011 | MEM[rs] → REG_B | |
| 100 | MEM[addr] → REG_A | |
| 101 | OPR → REG_B | |
| 110 | OPR → REG_A | |
| 111 | ZERO → REG_B | |

#### GROUP 01: ALU + WRITEBACK

| Bits [5:3] | ALU Op | Bits [2:0] | Destination |
|:----------|:-------|:----------|:------------|
| 000 | A + B | 000 → rd |
| 001 | A - B | 001 → rs |
| 010 | A ^ B | 010 → ADDR_LO |
| 011 | A & B | 011 → ADDR_HI |
| 100 | A \| B | 100 → rd + end |
| 101 | pass A | 101 → rd + flags |
| 110 | pass B | 110 → rd + flags + end |
| 111 | NOT A | 111 → MEM[addr] |

#### GROUP 10: BRANCH/JUMP

| Bits [5:4] | Condition | Bits [3:0] | Type |
|:----------|:----------|:----------|:-----|
| 00 | always | 0000 PC += sext(OPR) |
| 01 | Z | 0001 PC = ADDR |
| 10 | NZ | 0010 PC_HI → REG_A |
| 11 | C | 0011 PC_LO → REG_A |
| | | 0100 end |
| | | 0101-1111 reserved |

#### GROUP 11: SPECIAL

| Action | Description |
|:-------|:------------|
| 000000 | NOP |
| 000001 | HLT |
| 000010 | END (step reset) |
| 000011 | IRQ save PC low to `$FFF6` |
| 000100 | IRQ save PC high to `$FFF7` |
| 000101 | IRQ vector to `$7F00`, clear IE and IRQ pending |
| 000110 | SYS operand subdecode (`NOP`, `HLT`, `EI`, `DI`, `IRET`) |

---

## Microcode ROM Address (15 bits)

```
A[14]   = IRQ_ACTIVE (IE AND IRQ_PENDING)
A[13]   = flag_C
A[12]   = flag_Z
A[11:8] = step counter (0-15)
A[7:0]  = opcode (from IR)
```

- **Total entries**: 32768 (2^15)
- **ROM**: 2× AT28C256 or SST39SF010, one for low control byte and one for high control byte
- **Conditional branching**: Flags in address enable free conditional paths
- **IRQ entry**: When `IRQ_ACTIVE=1` at an instruction boundary, the IRQ bank overrides normal fetch and runs the fixed vector entry sequence.

---

## Memory Map

RV8-R is **ROM-first** for standalone use: reset clears `PC=$0000`, so the first
instruction is fetched from Program ROM without reset-vector remap hardware.
RAM occupies the upper half like RV8GR. The programmer-visible
registers live at the highest end of RAM so register access can be generated as
`$FFF8 + reg_id`.

| Range | Description |
|:------|:------------|
| $0000-$7FFF | Program ROM (boot, monitor, BASIC, game cartridge) |
| $7F00-$7FFF | ROM monitor / IRQ handler area |
| $8000-$FEFF | RAM data, arrays, video buffer, optional RAM-loaded program |
| $FF00-$FFF5 | RAM stack / fast page |
| $FFF6-$FFF7 | IRQ saved PC low/high |
| $FFF8-$FFFF | Registers r0-r7 in RAM |

**Address routing**:
- Fetch: 16-bit PC counter output drives ABUS through the ABUS mux. Reset clears PC to `$0000`, so ROM is selected.
- Data access: 16-bit address register drives ABUS through the same ABUS mux.
- `ADDR_SRC=REG`: address-source mux forces `$FFF8 + reg_id`.
- `ADDR_SRC=FAST/IRQ`: address-source mux forces `$FF00 + imm8`, `$FFF6`, or `$FFF7`.
- `ADDR_SRC=VECTOR/PC`: address-source mux loads `$7F00` for IRQ or `{PC_HI, ALU_LO}` for same-page branches.

**Address hardware**: FullHW uses 8× 74HC157 as a two-stage 16-bit address-source mux plus 4× 74HC157 to select PC or address register onto ABUS.

---

## Chip List

| Part | Qty | Function |
|:-----|:---:|:---------|
| 74HC161 | 5 | 16-bit PC + 4-bit step counter |
| 74HC574 | 6 | IR opcode, IR operand, ALU_B, ALU result, address low/high |
| 74HC283 | 2 | ALU adder |
| 74HC86 | 4 | SUB invert bank + XOR result |
| 74HC08 | 3 | AND result + control gating |
| 74HC32 | 2 | OR result |
| 74HC157 | 16 | ALU result mux, address-source mux, ABUS select |
| 74HC245/244 | 4 | memory bridge, PC_LO/PC_HI to IBUS, constant/sign drivers |
| 74HC74 | 3 | flags, IE/IRQ_PENDING, HALT |
| 74HC138 | 1 | SYS subdecode |
| 74HC00/04 | 3 | r0 guard, mutually-exclusive enables, reset/clock gates |
| **Logic** | **49** | |
| AT28C256/SST39SF010 | 2 | Microcode ROM low/high control bytes |
| AT28C256 | 1 | Program ROM |
| CY7C199/62256 | 1 | RAM (32 KB) |
| **Total** | **53** | |

---

## Datapath Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    RV8-R FullHW (49 logic chips)          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────┐    ┌────────┐    ┌────────────┐            │
│  │Microcode│    │Program │    │    RAM      │            │
│  │  ROM   │    │  ROM   │    │ (regs+data) │            │
│  │AT28C256│    │AT28C256│    │  CY7C199    │            │
│  └───┬────┘    └───┬────┘    └──────┬──────┘            │
│      │ctrl[15:0]   │data           │data                │
│      ▼             ▼               ▼                    │
│  ┌──────┐     ┌─────────────────────────┐              │
│  │DECODE│     │        IBUS (8-bit)      │              │
│  │HC139 │     └──┬──────┬──────┬────┬───┘              │
│  └──────┘        │      │      │    │                   │
│           ┌──────┴┐ ┌───┴──┐ ┌─┴──┐ ┌┴────┐           │
│           │ REG_A │ │REG_B │ │ IR │ │ OPR │           │
│           │ (574) │ │(574) │ │574 │ │ 574 │           │
│           └───┬───┘ └──┬──┘ └────┘ └─────┘           │
│               │         │                               │
│               ▼         ▼                               │
│           ┌─────────────────┐                           │
│           │ ALU add/logic+mux│                           │
│           │   A op B → R    │                           │
│           └────────┬────────┘                           │
│                    │result → IBUS                        │
│                    ▼                                     │
│  ┌────────────────────────────────┐                     │
│  │  PC (161×4) ↔ AR/ABUS muxes     │                    │
│  │  Step[3:0] → MCU ROM addr       │                    │
│  │  Flags(74)  → MCU ROM addr      │                    │
│  └─────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

---

## Cycle Counts

| Instruction | Cycles |
|:------------|-------:|
| J off8 | 3 |
| LI rd, imm | 4 |
| RET | 4 |
| ADDI/SUBI/XORI/ANDI/ORI rd, imm | 5 |
| ADD/SUB/XOR/AND/OR rd, rs | 5 |
| SLL rd | 5 |
| JAL rd, off8 | 5 |
| LB rd, addr (fast-page RAM) | 6 |
| SB rd, addr (fast-page RAM) | 6 |
| BEQ/BNE/BLT/BGE rs1,rs2,off | 6 |
| SLT rd, rs | 7 |
| LB rd, off(rs) | 8 |
| SB rd, off(rs) | 8 |
| PUSH rd | 9 |
| POP rd | 9 |
| SRL rd | Dropped (software macro) |

**Average**: 5.5 cycles → **0.91 MIPS @ 5 MHz**

---

## Key Design Decisions

1. **16-bit direct-control word** — Two microcode ROM bytes drive real enable lines directly. This costs more packages than the 19-chip sketch, but every bus owner and state change can be pinned and probed.

2. **IBUS-as-ALU-A plus ALU_B latch** — A operand is the current IBUS value; B operand is held in a latch. This keeps register values visible and avoids a hidden hardware register file.

3. **Flags in microcode address** — Free conditional branching. No SKIP logic needed. Z and C flags directly select microcode path.

4. **SRL dropped** — Software macro. Saves complexity (no barrel shifter). SRL implemented via software loop.

5. **JAL same-page only (±128 bytes)** — Cross-page via CALL/RET macros pushing 16-bit PC. Reduces microcode complexity.

6. **r0 protection** — Gate masks RAM writeback when a register write targets `r0` (`REG_SEL=000`). This is implemented in the RAM write-enable guard.

7. **ROM-first standalone boot** — Reset PC is `$0000`, so a socketed Program ROM can boot the machine without a host. A15 selects memory (`0` = Program ROM, `1` = RAM). RAM execution remains possible after ROM code loads or jumps to RAM.

8. **High-end RAM registers** — `r0-r7` live at `$FFF8-$FFFF`. This avoids conflict with ROM at reset and keeps the programmer model RISC-V-style. Hardware register access forces the high address bits to `1` and places the 3-bit register number on `A[2:0]`.

---

## ISA

RV8-R keeps the RV8 two-byte, RISC-V-style encoding. FullHW makes the target
hardware paths real, while still keeping `SRL` as a software macro and `LUI` as
an assembler pre-shift.

| Class | Opcode range | Hardware status | Instructions |
|-------|--------------|-----------------|--------------|
| ALU register | `$00-$27` | FullHW native | `ADD`, `SUB`, `AND`, `OR`, `XOR` |
| ALU register | `$28-$2F` | FullHW native | `SLT` |
| ALU register | `$30-$37` | Native | `SLL` (`rd = rd + rd`) |
| ALU register | `$38-$3F` | Software macro | `SRL` |
| ALU immediate | `$40-$6F` | FullHW native | `LI`, `ADDI`, `SUBI`, `ANDI`, `ORI`, `XORI` |
| ALU immediate | `$70-$77` | FullHW native | `SLTI` |
| ALU immediate | `$78-$7F` | Assembler pre-shift | `LUI` (`LI rd, imm << 4`) |
| Memory | `$80-$9F` | FullHW native | `LB off(rs)`, `SB off(rs)`, `LB fast`, `SB fast` |
| Memory | `$A0-$AF` | FullHW native | `PUSH`, `POP` |
| Memory | `$B0-$BF` | FullHW native | `LB off(sp)`, `SB off(sp)` |
| Control | `$C0-$DF` | FullHW native | `BEQ`, `BNE`, `BLT`, `BGE` |
| Control | `$E0-$F7` | FullHW native, same-page target contract | `JAL`, `JALR`, `J` |
| System | `$F8-$FF` | FullHW native | `SYS 0`=`NOP`, `SYS 1`=`HLT`, `SYS 2`=`EI`, `SYS 3`=`DI`, `SYS 4`=`IRET` |

**Baseline count:**
- FullHW native instructions: 35-slot ISA surface, with `SRL` retained as software macro and `LUI` as assembler pre-shift
- Hardware carry/borrow path is real for `SLT`, `SLTI`, `BLT`, and `BGE`
- Stack path is real for `PUSH`, `POP`, `LBsp`, and `SBsp`
- Software/pseudo instructions: `SRL`, `LUI` pre-shift form, assembler macros

The current `tools/microcode_gen.py` is still the old 14-bit prototype. FullHW
requires a regenerated 15-bit direct-control microcode generator before RTL or
ROM images can be called current.

**Encoding format**:
- Opcode byte: [7:6]=iclass, [5:3]=op, [2:0]=rd
- Operand byte: [7:5]=rs, [4:0]=off5/imm

See `RV8R/doc/01_isa_encoding.md` for the byte-level opcode map.

---

## Performance Comparison

| System | CPU | Clock | MIPS | BASIC lines/sec |
|:-------|:----|:------|:-----|:----------------|
| Apple II | 6502 | 1 MHz | ~0.3 | ~300 |
| MSX2 | Z80 | 3.58 MHz | ~0.5 | ~500 |
| RV8-R | 8-bit | 5 MHz | 0.91 | ~260 |

RV8-R trades throughput for simplicity. BASIC slower than MSX2 due to interpreted interpreter overhead.

---

## Microcode Step Sequences

### ADDI rd, imm (5 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | OPR → REG_B |
| 3 | MEM[rd] → REG_A |
| 4 | ALU(A+B) → MEM[rd], END |

### ADD rd, rs (5 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[rs] → REG_B |
| 3 | MEM[rd] → REG_A |
| 4 | ALU(A+B) → MEM[rd], END |

### BEQ rs1, rs2, off (6 cycles)

| Step | Action | Flag condition |
|:-----|:-------|:---------------|
| 0 | MEM[PC] → IR, PC++ | — |
| 1 | MEM[PC] → OPR, PC++ | — |
| 2 | MEM[rs1] → REG_A (rd from IR[2:0]) | — |
| 3 | MEM[rs2] → REG_B (rs from OPR[7:5]) | — |
| 4 | ALU(A-B), save flags | — |
| 5 | [Z=1] PC += sext(OPR[4:0]), END | Z=1 |
| 5 | END (no branch) | Z=0 |

### LB rd, off(rs) (8 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[rs] → REG_A |
| 3 | OPR → REG_B (offset, sign-extended) |
| 4 | ALU(A+B) → ADDR_LO |
| 5 | ZERO → ADDR_HI |
| 6 | MEM[addr] → REG_A |
| 7 | ALU(passA) → MEM[rd], END |

### PUSH rd (9 cycles)

| Step | Action |
|:-----|:-------|
| 0 | MEM[PC] → IR, PC++ |
| 1 | MEM[PC] → OPR, PC++ |
| 2 | MEM[sp] → REG_A (read SP) |
| 3 | load const 1 → REG_B |
| 4 | ALU(A-B) → MEM[sp] (SP--) |
| 5 | ALU(A-B) → ADDR_LO (new SP = address) |
| 6 | ZERO → ADDR_HI |
| 7 | MEM[rd] → REG_A (value to push) |
| 8 | ALU(passA) → MEM[addr], END |

---

## IRQ Design

### Hardware: U22 (74HC74) — 2 flip-flops

```
U22-A: IE_FF (Interrupt Enable)
  SET/CLK ← SYS 2 (EI)
  CLR     ← SYS 3 (DI) OR IRQ-ack OR /RST
  Q → IE

U22-B: IRQ_FF (Interrupt Pending)  
  CLK ← /IRQ pin (falling edge)
  /CLR ← IRQ-ack OR /RST
  Q → IRQ_PENDING
```

### Microcode ROM address (15 bits)

```
A[14]   = IRQ_ACTIVE (IE AND IRQ_PENDING)
A[13]   = flag_C
A[12]   = flag_Z
A[11:8] = step counter (0-15)
A[7:0]  = opcode (from IR)
```

Total: 15 bits = 32768 entries. Fits AT28C256 (32KB) exactly.

### IRQ entry sequence (when `IRQ_ACTIVE=1` at step 0):

```
Step 0: Save PC_LO → RAM[$FFF6]
Step 1: Save PC_HI → RAM[$FFF7]
Step 2: Load PC ← $7F00 (vector address in ROM)
Step 3: Clear IE, Clear IRQ_FF, END
```

### Instructions (sub-codes of SYS $F8):

| Operand | Mnemonic | Action |
|:-------:|----------|--------|
| $00 | NOP | no operation |
| $01 | HLT | halt CPU |
| $02 | EI | IE ← 1 (enable interrupts) |
| $03 | DI | IE ← 0 (disable interrupts) |
| $04 | IRET | PC ← RAM[$FFF7:$FFF6], IE ← 1 |

### ISR pattern:

```asm
; ISR at $7F00:
    DI                  ; prevent nesting (already cleared by HW)
    PUSH r2             ; save registers as needed
    ; ... handle interrupt ...
    POP r2
    IRET                ; restore PC from RAM[$FFF6/$FFF7], re-enable IRQ
```

---

## Status

- **Architecture**: FullHW revision: ROM low, RAM high, high-end RAM registers, real full-ISA hardware paths
- **Chip count**: 49 logic + 2 microcode ROM + 1 program ROM + 1 RAM = **53 packages**
- **Control**: 16-bit direct-control, 15-bit microcode address
- **Verification**: Previous behavioral RTL passed on the older `$8000` reset map; RTL/testbench, microcode generator, and KiCad proof must be migrated to FullHW

---

*Document version: 2026-06-14*  
*Source of truth for RV8-R architecture*  
*Next: RTL implementation in Verilog*
