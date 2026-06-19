---
name: rv8-cpu-design
description: RV8 8-bit RISC-V style CPU design patterns. 64K address space, RAM-backed registers, no microcode, direct-encoded control. Use for homebrew CPU projects, Verilog RTL, TTL hardware builds, and educational CPU architecture.
---

# RV8 CPU Design Knowledge

## Architecture Principles

- **8-bit data bus**, 16-bit address bus (64KB address space)
- **RISC-V style mnemonics**: ADD, SUB, LB, SB, BEQ, J
- **RAM-backed registers**: 8 registers at $8000-$8007 (DP=$80, operand $00-$07)
- **Accumulator-based**: AC is the primary ALU input/output
- **RV8-Bus**: 40-pin (A[15:0] + D[7:0] + control signals)

## Design Variants

| Variant | Chips | Microcode | ISA | MIPS | Notes |
|---------|-------|-----------|-----|------|-------|
| **RV8** | 27 | Yes | 35 | 1.25 | Proven, full ISA |
| **RV8-R** | 18 | Yes | 35 | 1.0 | Fewest + full ISA |
| **RV8-G** | 38 | No | 35 | 2.5 | Full ISA, no microcode |
| **RV8-GR** | 30 | No | 17 | 3.3 | Fastest, execute RAM |

### RV8-GR (current — BUILDING)

- **33 logic chips** + ROM + RAM = 35 packages
- **No microcode** — direct-encoded control bytes
- **3-cycle execution**: T0=fetch control, T1=fetch operand, T2=execute
- **Full 64K**: A15 chip select (ROM $0000-$7FFF, RAM $8000-$FFFF)
- **Chip select**: ROM /CE=A15 (direct), RAM /CE=/A15 (U24 inverter)
- **16-bit jump**: Page Register for full address space
- **Execute from RAM**: PC in $8000-$FFFF fetches from RAM
- **Reset**: PC=$0000 → boots directly from ROM (standalone, no Programmer needed)
- **Registers**: $8000-$8007 via default DP=$80
- **IRQ**: v1.0=polling (U31), v1.1=hardware vector $FF00 (+2 chips)
- **Memory layout**:
  - $0000-$7FFF: ROM (program, lookup tables)
  - $8000-$8007: RAM (registers r0-r7)
  - $8008-$FEFF: RAM (general data, stack, executable)
  - $FF00-$FF0F: RAM (ISR vector, v1.1)
  - $FF10-$FF2F: I/O slots (/SLOT1, /SLOT2)
  - $FF30-$FFFF: RAM (available)

## Control Byte Encoding (RV8-GR)

```
Bit 7: ALU_SUB    — 0=ADD, 1=SUB (invert + Cin=1)
Bit 6: XOR_MODE   — 0=XOR B=ALU_SUB, 1=XOR B=AC (for XOR instr)
Bit 5: MUX_SEL    — 0=AC←Adder, 1=AC←XOR output
Bit 4: AC_WR      — 0=AC unchanged, 1=AC latches new value
Bit 3: SOURCE     — 0=IBUS=IR_LO (immediate), 1=IBUS=RAM[IR_LO]
Bit 2: STORE      — 0=no store, 1=RAM[IR_LO]=AC
Bit 1: BRANCH     — 0=no branch, 1=conditional PC load (check Z)
Bit 0: JUMP       — 0=no jump, 1=unconditional PC load
```

### Instructions (17 total)

| Hex | Mnemonic | Operation |
|-----|----------|-----------|
| $00 | NOP | no operation |
| $10 | ADDI imm | AC = AC + imm |
| $18 | ADD rs | AC = AC + RAM[rs] |
| $90 | SUBI imm | AC = AC - imm |
| $98 | SUB rs | AC = AC - RAM[rs] |
| $70 | XORI imm | AC = AC ^ imm |
| $78 | XOR rs | AC = AC ^ RAM[rs] |
| $30 | LI imm | AC = imm |
| $38 | MV a0,rs | AC = RAM[rs] (load byte) |
| $04 | MV rd,a0 | RAM[rd] = AC (store byte) |
| $02 | BEQ addr | if Z=1: PC = {PG, addr} |
| $82 | BNE addr | if Z=0: PC = {PG, addr} |
| $01 | J addr | PC = {PG, addr} |
| $20 | SETPG imm | PG = imm |
| $28 | SETPG_R rs | PG = RAM[rs] |
| $08 | EI | IE = 1 (enable interrupts) |
| $48 | DI | IE = 0 (disable interrupts) |

## IRQ Design (RV8-GR)

### Hardware (1 chip: 74HC74)

- **U31-A (IE FF)**: Set by EI decode, cleared by DI or IRQ-ack
- **U31-B (IRQ FF)**: Set by /IRQ falling edge, cleared by IRQ-ack
- **IRQ-ack**: T2 AND IE AND IRQ_FF AND NOT(pc_load)

### Behavior

1. Falling edge of /IRQ latches IRQ_FF=1
2. At end of T2, if IRQ_FF=1 AND IE=1 AND no jump in progress:
   - Save PC to RAM[$800E] (low) and RAM[$800F] (high)
   - Jump to vector $FF00 (in RAM — user must set up ISR before EI)
   - Clear IE (prevent nesting)
   - Clear IRQ_FF
3. If a jump is in progress, IRQ is deferred to next instruction

### ISR Pattern

```asm
; ISR at $FF00
    SB $08          ; save AC
    ; ... handle device ...
    LB $08          ; restore AC
    ; Return:
    LB $0F
    SETPG_R $0F     ; restore page
    LB $0E
    J $0E           ; jump to saved PC
```

## Chip Selection (RV8-GR)

| U# | Chip | Function |
|----|------|----------|
| U1-U4 | 74HC161 ×4 | PC (16-bit counter) |
| U5 | 74HC574 | IR_HIGH (control) |
| U6 | 74HC574 | IR_LOW (operand) |
| U7 | 74HC245 | Bus buffer (DBUS ↔ IBUS) |
| U8 | 74HC164 | Ring counter (T0/T1/T2) |
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
| U24 | 74HC04 | Inverters |
| U25 | 74HC32 | OR gates |
| U26-U27 | 74HC00 ×2 | NAND gates |
| U28 | 74HC86 | XOR (Z_match, /T2, WR_DIR) |
| U29-U30 | 74HC157 ×2 | Address mux A8-A15 |
| U31 | 74HC74 | IRQ_FF + IE_FF |
| U32 | 74HC574 | Data Page Register |
| U33 | 74HC21 | SETDP decode + EI decode |

## Verilog Conventions

- Single-file CPU module with FSM-based control
- Behavioral model (not gate-level)
- Testbench uses $readmemh for ROM loading
- iverilog + GTKWave for simulation

### Key Signals

```verilog
// Timing
localparam T0=0, T1=1, T2=2;
reg [1:0] state;

// Memory
reg [7:0] rom[0:32767];
reg [7:0] ram[0:32767];

// Derived control
wire pc_load = jump | (branch & z_match);
wire pg_load = mux_sel & ~ac_wr;
```

## Key Design Patterns

### 1. A15 Chip Select
```verilog
wire [7:0] mem_read = pc[15] ? ram[pc[14:0]] : rom[pc[14:0]];
```
- ROM at $0000-$7FFF (A15=0, ROM /CE=A15)
- RAM at $8000-$FFFF (A15=1, RAM /CE=/A15)

### 2. IBUS During T2
```verilog
wire [7:0] ibus = source_type ? ram[{7'b0, ir_low}] : ir_low;
```
- SRC=0: IBUS = immediate (IR_LO)
- SRC=1: IBUS = RAM[IR_LO]

### 3. ALU with XOR Sharing
```verilog
wire [7:0] xor_b = xor_mode ? ac : {8{alu_sub}};
wire [7:0] xor_out = ibus ^ xor_b;
wire [8:0] adder_full = {1'b0, ac} + {1'b0, xor_out} + {8'b0, alu_sub};
wire [7:0] adder_sum = adder_full[7:0];
wire [7:0] ac_mux = mux_sel ? xor_out : adder_sum;
```
- XOR_MODE=0: XOR passes IBUS through (for LI/MV)
- XOR_MODE=1: XOR computes AC^IBUS (for XORI/XOR)
- ALU_SUB=1: Adder computes AC - IBUS (SUB)
- MUX_SEL=1: XOR output goes to AC (XORI/XOR)
- MUX_SEL=0: Adder output goes to AC (ADD/SUB/ADDI/SUBI)

### 4. WR_DIR Gating
```verilog
// U7 DIR = T2 AND STORE
// Prevents bus conflict during fetch after STORE
```

## Subroutine Pattern (Software CALL/RET)

```asm
; CALL sub at page P, address A:
LI lo(return)       ; $30, ret_lo
MV $07, a0          ; $04, $07  (save return addr low)
SETPG P             ; $20, P
J A                 ; $01, A

; RET (at end of sub, return address known at compile time):
SETPG ret_page      ; $20, ret_pg
J ret_lo            ; $01, ret_lo
```

## Verification Commands

```bash
# Full ISA test
cd RV8GR
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_full.v && vvp /tmp/tb.vvp
# === ALL TESTS PASSED === (127 cycles)

# IRQ test
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_irq.v && vvp /tmp/tb.vvp
# === ALL IRQ TESTS PASSED ===

# SETDP test
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_setdp.v && vvp /tmp/tb.vvp
# === SETDP TEST PASSED === (160 cycles)

# Opcode sweep (256 opcodes × Z=0/1 = 512 cases)
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/tb_rv8gr_opcode_sweep.v && vvp /tmp/tb.vvp
# === OPCODE SWEEP PASSED: 512 cases (256 opcodes x Z=0/1) ===

# Python gate-level sim
python3 sim/chip_sim.py
# ALL 8 CPU TESTS PASSED ✅

# Soft debug trace
python3 sim/soft_debug.py
# ALL SOFT DEBUG TESTS PASSED ✅

# Assemble program
python3 tools/rv8gr_asm.py programs/testrom.asm -o programs/testrom.bin
```

## 74HC Family Notes

- Use **74HCT** for better TTL compatibility
- 74HC161: synchronous 4-bit counter
- 74HC574: octal D flip-flop (positive edge, 3-state)
- 74HC157: 4:1 mux (active low enable)
- 74HC245: octal bus transceiver (direction + enable)
- 74HC164: serial-in parallel-out shift register
- 74HC74: dual D flip-flop (set + clear)
- 74HC688: 8-bit magnitude comparator
- 74HC283: 4-bit binary full adder (carry in/out)

## Common Issues

1. **Bus conflict**: U7 DIR must be gated with T2+STORE
2. **IRQ during jump**: Defer to next instruction
3. **Z flag update**: Must check AC after ALU, not before
4. **XOR encoding**: Need MUX_SEL=1 for XORI/XOR

## Build Strategy

1. Clock, reset, power
2. Memory subsystem (ROM/RAM + chip select)
3. PC and fetch (ring counter, IR)
4. Page register and address formation
5. Register window in RAM
6. Internal bus driver
7. ALU and condition logic
8. Branch and halt
9. Load/store and stack operations
10. Interrupt controller
11. Memory-mapped I/O
12. Assembler and board bring-up tests

## Programmer Board (2026-06-14)

- Board: ESP32-WROOM-32
- Design: Connects via **RV8-Bus (40-pin)** — not direct to ROM
- Level shifter: TXS0108E ×2
- Address: 74HC595 ×2 (daisy-chain, full A0-A14 via bus)
- Data: GPIO [13,12,14,27,26,25,33,32] → Bus pin 17-24
- Shift: DATA=23, CLK=18, LATCH=19
- Control out: /RST=4 (bus 26), /WR=16 (bus 27), /RD=17 (bus 28)
- Input: /SLOT1=34 (bus 30), /RD=35 (bus 28), /WR=36 (bus 27), MODE=39
- ROM selected by A15=0 (ROM /CE=A15, active when A15=0)
- PROG mode: hold /RST, drive A+D+/WR+/RD → flash ROM on CPU board
- RUN mode: release bus, UART bridge via /SLOT1
- Scenarios: A=bare ROM on bus, B=full CPU board (hold /RST)
- Firmware protocol: `?`→`Connected\n`, `F`→`K\n`+data→`D\n`, `V`→32KB, `R`→`K\n`
- Tools: rv8flash.py (flash/read/verify), rv8term.py (terminal bridge)
- 31 tests passing (16 flash + 15 term)

## Current Status (2026-06-15)

- **Design**: Signed off, gate-level verified, ready for physical build
- **Verilog**: ALL 4 TESTBENCHES PASS (full 127 cycles, IRQ, tasks, SETDP 160 cycles)
- **Gate-level sim**: chip_sim.py 8/8, soft_debug.py 4/4
- **Memory map**: ROM $0000-$7FFF, RAM $8000-$FFFF (swapped 2026-06-15)
- **Timing**: max 9.7 MHz theoretical, 1 MHz recommended for breadboard
- **Hardware labs**: 14 of 14 written (Thai, middle school level)
- **Source of truth**: `doc/00_design_isa.md` + `doc/02_wiring_guide.md`

## Skills (Agent)
- `debug-mantra`: 4-step hardware debugging discipline (reproduce → trace → falsify → breadcrumbs)
- `scrutinize`: Outsider-perspective review of hardware/RTL changes

## Current TODO
- Order parts for physical build
- Build Lab 01-14 on breadboard (1 MHz)
- PCB layout for 4 MHz version (when breadboard verified)
- Example Programs (.asm collection: blink, counter, game)
- RV8-R architecture design (when ready)

## Design Status
- RV8-GR: **Architecture Frozen v1.0** — all 11 docs consistent and signed off
- Verilog: ALL 5 TESTBENCHES PASS (full 127 cycles, IRQ, SETDP, tasks, opcode sweep 512 cases)
- Gate-level sim: chip_sim.py 8/8, soft_debug.py 4/4
- Assembler: cross-page validation, overlap detection, memh output
- Timing: 1 MHz breadboard (808ns margin), 4 MHz PCB target (88ns margin)
- BOM finalized, 5-board breadboard layout planned
- Hardware labs: 14 written (Thai, middle school level)
- Future upgrades documented (doc/11_future_upgrades.md)
- RV8GR-Codex (speculative AI redesign) evaluated and rejected; useful bits extracted
