# RV8F — Fast Microcode RISC-V CPU

**34 logic chips. RISC-V ISA. 8 hardware registers. 15ns SRAM microcode. Programmable.**

---

## Specs

| Spec | Value |
|------|-------|
| Logic chips | 38 (34 CPU + 4 boot) |
| Total packages | 41 (38 logic + 2 SRAM + 1 Flash) |
| ISA | RISC-V style, 35 instructions |
| Registers | 8 hardware (74HC574) |
| Clock | 5 MHz (breadboard), 15 MHz (PCB target) |
| Cycles/instr | 3-4 average |
| MIPS | 1.4 @ 5MHz, 4.2 @ 15MHz |
| Program memory | 32KB SRAM (CY7C199-15PC, 15ns) |
| Microcode | 32KB SRAM (CY7C199-15PC, 15ns) |
| ALU | ADD, SUB, AND, OR, XOR, SLT, SLL, SRL |
| Control | Microcode-driven (programmable ISA) |
| Target | BASIC interpreter + video games |
| Boot | Standalone auto-copy Flash→SRAM at power-on (66ms) |

---

## Boot Circuit (Standalone, 4 chips)

CPU cannot run without microcode in SRAM. Boot circuit copies Flash → SRAM automatically at power-on, **without CPU involvement**.

### How It Works

```
Power On:
  1. Boot latch holds CPU /RST = LOW (CPU halted)
  2. Boot counter (16-bit) starts counting at ~1 MHz
  3. Counter[14:0] → Flash address AND SRAM address
  4. Counter[15] selects: 0=Microcode SRAM, 1=Program SRAM
  5. Flash data → SRAM data (direct copy, 1 byte per clock)
  6. After 65536 clocks (~66ms): counter overflows
  7. Overflow → boot latch SET → CPU /RST released
  8. Boot counter tri-states (disconnects from bus)
  9. CPU starts at 5 MHz with everything loaded
```

### Boot Circuit Chips

| Chip | Qty | Function |
|------|:---:|----------|
| 74HC161 | 3 | 16-bit address counter (A[15:0]) |
| 74HC74 | 1 | Boot-done latch (/RST control) |

### Boot Timing

```
Clock: ~1 MHz (RC oscillator or main clock ÷4)
Copies: 32KB microcode + 32KB program = 64KB total
Time: 65536 / 1 MHz = ~66ms (instant to user)
```

### Flash Memory Layout (SST39SF010A, 128KB)

```
$00000-$07FFF  Microcode table (32KB) → copies to Microcode SRAM
$08000-$0FFFF  Program + data (32KB) → copies to Program SRAM
$10000-$17FFF  Alternate program (selectable via DIP switch)
$18000-$1FFFF  spare
```

### Boot Sequence Diagram

```
            /RST ──────────────────────┐
                                       │ (held LOW)
┌────────────┐   ┌──────────┐   ┌─────┴─────┐
│Boot Counter│──▶│  Flash   │──▶│   SRAM    │
│ 74HC161 ×3 │   │SST39SF   │   │ CY7C199   │
│(16-bit)    │   │ /CE=0    │   │ /WE=clk   │
└─────┬──────┘   │ /OE=0    │   │ /CE=!bit15│
      │          └──────────┘   └───────────┘
      │ bit16 overflow
      ▼
┌──────────┐
│74HC74    │── Q → /RST released → CPU starts!
│Boot Latch│   (also tri-states boot counter)
└──────────┘
```

---

## Architecture

```
┌──────────────┐         ┌──────────────┐
│  Boot Flash  │──copy──▶│  Microcode   │
│SST39SF010A   │         │  SRAM (15ns) │
│ (slow, boot) │         │  CY7C199     │
└──────────────┘         └──────┬───────┘
                                │ control word (16-bit)
                                ▼
┌──────────────┐         ┌──────────────┐
│   Program    │◀───────▶│     CPU      │
│  SRAM (15ns) │         │  Datapath    │
│  CY7C199     │         │             │
│  32KB        │         │ 8 regs, ALU │
└──────────────┘         │ PC, IR      │
                         └──────────────┘
```

### Execution Flow

```
T0: PC → ABUS → Program SRAM → DBUS → IR latch (opcode), PC+1
T1: PC → ABUS → Program SRAM → DBUS → IR latch (operand), PC+1
T2: Microcode → control word → execute (ALU, reg read/write)
T3: (if needed) Memory access or branch resolve
```

### Microcode Lookup

```
Address = {opcode[7:0], step[3:0]} = 12 bits → 4096 entries
Each entry = 16-bit control word (2 bytes)
Total: 4096 × 2 = 8KB (fits in 32KB SRAM)
```

---

## ISA (35 Instructions, RISC-V Style)

### Class 00: Register-Register ALU

| Op | Mnemonic | Operation |
|:--:|----------|-----------|
| 000 | ADD rd, rd, rs | rd = rd + rs |
| 001 | SUB rd, rd, rs | rd = rd - rs |
| 010 | AND rd, rd, rs | rd = rd & rs |
| 011 | OR rd, rd, rs | rd = rd \| rs |
| 100 | XOR rd, rd, rs | rd = rd ^ rs |
| 101 | SLT rd, rd, rs | rd = (rd < rs) ? 1 : 0 |
| 110 | SLL rd | rd = rd << 1 |
| 111 | SRL rd | rd = rd >> 1 |

### Class 01: ALU Immediate

| Op | Mnemonic | Operation |
|:--:|----------|-----------|
| 000 | LI rd, imm | rd = imm |
| 001 | ADDI rd, imm | rd = rd + imm |
| 010 | SUBI rd, imm | rd = rd - imm |
| 011 | ANDI rd, imm | rd = rd & imm |
| 100 | ORI rd, imm | rd = rd \| imm |
| 101 | XORI rd, imm | rd = rd ^ imm |
| 110 | SLTI rd, imm | rd = (rd < imm) ? 1 : 0 |
| 111 | LUI rd, imm | rd = imm << 4 |

### Class 10: Load/Store

| Op | Mnemonic | Operation |
|:--:|----------|-----------|
| 000 | LB rd, off(rs) | rd = mem[rs + off] |
| 001 | SB rd, off(rs) | mem[rs + off] = rd |
| 010 | LB rd, addr | rd = mem[addr] |
| 011 | SB rd, addr | mem[addr] = rd |
| 100 | PUSH rd | sp--, mem[sp] = rd |
| 101 | POP rd | rd = mem[sp], sp++ |
| 110 | LB rd, off(sp) | rd = mem[sp + off] |
| 111 | SB rd, off(sp) | mem[sp + off] = rd |

### Class 11: Branch/Jump

| Op | Mnemonic | Operation |
|:--:|----------|-----------|
| 000 | BEQ rs1, rs2, off | if rs1==rs2: PC += off |
| 001 | BNE rs1, rs2, off | if rs1≠rs2: PC += off |
| 010 | BLT rs1, rs2, off | if rs1<rs2: PC += off |
| 011 | BGE rs1, rs2, off | if rs1≥rs2: PC += off |
| 100 | JAL rd, off | rd=PC, PC += off |
| 101 | JALR rd, rs | rd=PC, PC = rs |
| 110 | J off | PC += off |
| 111 | SYS imm | NOP/HLT/ECALL |

---

## Chip List (38 logic)

### CPU (34 chips)

| U# | Chip | Qty | Function |
|:--:|------|:---:|----------|
| U1-U8 | 74HC574 | 8 | Registers r0-r7 |
| U9-U10 | 74HC574 | 2 | IR (opcode + operand) |
| U11-U14 | 74HC161 | 4 | PC (15-bit counter) |
| U15 | 74HC161 | 1 | Step counter |
| U16-U17 | 74HC574 | 2 | Control word latch (16-bit) |
| U18-U19 | 74HC283 | 2 | Adder (8-bit) |
| U20-U21 | 74HC86 | 2 | XOR (SUB invert + XOR op) |
| U22-U23 | 74HC08 | 2 | AND (8-bit) |
| U24-U25 | 74HC32 | 2 | OR (8-bit) |
| U26-U27 | 74HC157 | 2 | ALU result mux + shift |
| U28 | 74HC574 | 1 | ALU B input latch |
| U29-U30 | 74HC574 | 2 | Address latch (15-bit) |
| U31-U32 | 74HC245 | 2 | Bus buffers |
| U33 | 74HC138 | 1 | Register read select |
| U34 | 74HC138 | 1 | Register write select |

### Boot Circuit (4 chips)

| U# | Chip | Qty | Function |
|:--:|------|:---:|----------|
| U35-U37 | 74HC161 | 3 | Boot address counter (16-bit) |
| U38 | 74HC74 | 1 | Boot-done latch (/RST control) |

### Memory (3 chips)

| Chip | Qty | Function |
|------|:---:|----------|
| CY7C199-15PC | 1 | Microcode SRAM (32KB, 15ns) |
| CY7C199-15PC | 1 | Program + Data SRAM (32KB, 15ns) |
| SST39SF010A | 1 | Boot Flash (128KB, standalone boot) |

---

## ALU Design

```
A (register) ────┬──────────┬──────────┬──────────┐
                 │          │          │          │
B (reg/imm) ─┬──┼──────────┼──────────┼──────────┤
             │  ▼          ▼          ▼          ▼
             │ [U18-19]  [U20-21]  [U22-23]  [U24-25]
             │  Adder     XOR       AND       OR
             │  A±B       A^B       A&B       A|B
             │   │          │          │          │
             │   └────┬─────┴──────┬───┘          │
             │        ▼            ▼              ▼
             │     [U26-27 Mux: ALU_OP selects result]
             │              │
             │              ▼ ALU output
             │
             └──[XOR with 1s for SUB: B^$FF + Cin=1]

ALU_OP (2 bits from control word):
  00 = Adder (ADD/SUB)
  01 = XOR
  10 = AND
  11 = OR

Shift: SLL/SRL handled by wiring B input shifted ±1 into adder
  SLL: A + A (= shift left 1)
  SRL: special mux path (bit7→bit6, bit6→bit5, ...)
```

---

## Control Word (16 bits)

```
Bit  [3:0]   REG_RD_SEL    Which register outputs to bus
Bit  [6:4]   REG_WR_SEL    Which register latches from bus
Bit  [7]     REG_WR_EN     Enable register write
Bit  [9:8]   ALU_OP        00=ADD 01=XOR 10=AND 11=OR
Bit  [10]    ALU_SUB       Invert B + Cin (for SUB/SLT)
Bit  [11]    ALU_SRC       0=register B, 1=immediate (IR_LOW)
Bit  [12]    MEM_RD        Enable program SRAM read
Bit  [13]    MEM_WR        Enable program SRAM write
Bit  [14]    PC_LD         Load PC (jump/branch taken)
Bit  [15]    STEP_RST      Reset step counter (end of instruction)
```

Additional control (from second byte or encoded):
```
PC_INC, IR_LD, ADDR_LD, FLAG_LD, SHIFT_SEL
```

---

## Memory Map (Program SRAM)

```
$0000-$00FF  Stack (256 bytes, sp starts at $FF)
$0100-$01FF  System variables
$0200-$3FFF  Program space (~15KB)
$4000-$5FFF  Data / arrays (8KB)
$6000-$7BFF  Video buffer (7KB)
$7C00-$7FFF  I/O (mapped via RV8-Bus)
```

---

## Boot Sequence

```
1. Power on: Boot Flash mapped, clock = 5 MHz
2. Boot ROM code:
   a. Copy microcode table (8KB) → Microcode SRAM
   b. Copy user program → Program SRAM
3. Set "boot complete" latch
4. Release CPU reset
5. CPU fetches from Program SRAM, microcode from Microcode SRAM
6. Full speed execution begins
```

---

## Comparison

| | Ben Eater | RV8 (orig) | RV8-GR | **RV8F** |
|--|:---------:|:----------:|:------:|:--------:|
| Chips | ~15 | 27 | 33 | **38** |
| ISA | Custom 8 | RISC-V 35 | Custom 18 | **RISC-V 35** |
| Registers | 2 | 8 | 1 (AC) | **8** |
| ALU ops | ADD/SUB | Full | ADD/SUB/XOR | **Full** |
| Clock | 1 MHz | 10 MHz | 5 MHz | **5 MHz** |
| MIPS | 0.2 | 1.25 | 1.67 | **1.4** |
| Programmable ISA | ✅ | ✅ | ❌ | **✅** |
| Standalone boot | ❌ | ✅ | ✅ | **✅ (66ms)** |
| BASIC capable | ❌ | ✅ | ✅ | **✅** |
| Games | ❌ | ❌ | Possible | **✅** |

---

## Status

- ⬜ Design document (this file)
- ⬜ Microcode format specification
- ⬜ Verilog model
- ⬜ Assembler
- ⬜ Microcode generator
- ⬜ Boot ROM code
- ⬜ BASIC interpreter
- ⬜ Physical build
