# RV8-GR — Design & ISA Reference (Stable)

**34 logic chips + ROM + RAM. No microcode. 64K. Polling IRQ. Verilog verified.**

---

## Architecture

```
3 cycles/instruction: T0 fetch control, T1 fetch operand, T2 execute
Accumulator machine: AC hardwired to ALU A-input
Registers in RAM ($8000-$8007, via DP=$80)
Control byte bits → hardware signals (no microcode ROM)
Clock: 1 MHz breadboard, up to 5 MHz on PCB
```

---

## Memory Map

```
$0000-$7EFF  ROM 32KB (bankable to 128KB)
$7F00-$7FFF  ROM (available)
$8000-$FEFF  RAM 32KB (registers, data, executable)
$FF00-$FF0F  RAM (available; future vector area)
$FF10-$FF1F  I/O Slot 1 (via /SLOT1 on RV8-Bus)
$FF20-$FF2F  I/O Slot 2 (via /SLOT2 on RV8-Bus)
$FF30-$FFFF  RAM (available)
Reset → $0000
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

| Bit | ISA Name | Wire Name | =0 | =1 |
|:---:|----------|-----------|----|----|
| 7 | SUB | ALU_SUB | ADD | SUB (invert + Cin=1) |
| 6 | XOR | XOR_MODE | B=SUB bit | B=AC (XOR instr) |
| 5 | MUX | MUX_SEL | AC←Adder | AC←XOR output |
| 4 | AC_WR | AC_WR | AC hold | AC latch |
| 3 | SRC | SRC | IBUS=immediate | IBUS=RAM[addr] |
| 2 | STR | STR | — | RAM[addr]=AC |
| 1 | BR | BR | — | Conditional PC load |
| 0 | JMP | JMP | — | Unconditional PC load |

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
| $48 | 01001000 | DI | v1.0 inert marker; IE clears only on reset |
| $70 | 01110000 | XORI imm | AC = AC ^ imm |
| $78 | 01111000 | XOR rs | AC = AC ^ RAM[{DP, rs}] |
| $82 | 10000010 | BNE addr | if !Z: PC = {PG, addr} |
| $90 | 10010000 | SUBI imm | AC = AC - imm |
| $98 | 10011000 | SUB rs | AC = AC - RAM[{DP, rs}] |

DP = Data Page Register (8 bits). Data address = {DP, operand} = 16-bit (full 64KB).
- DP=$00-$7F → ROM read only ($0000-$7FFF)
- DP=$80-$FF → RAM read/write ($8000-$FFFF)
- **Note: SB to ROM address = ignored in normal CPU runtime**. The verified
  chip-level CPU model keeps ROM `/WE` inactive during runtime; a programmer may
  own ROM `/WE` only in PROG/reset isolation. CPU stores to DP<$80 do not change
  ROM contents.

> ⚠️ **สำคัญ: DP ต้อง ≥ $80 เพื่อเข้าถึง RAM**
>
> หลัง reset DP เป็นค่าไม่แน่นอน — คำสั่งแรกควรเป็น `SETDP $80`
>
> | DP Range | Address Space | ใช้ทำอะไร |
> |:--------:|:------------:|-----------|
> | $00-$7F | ROM ($0000-$7FFF) | อ่าน lookup table, constants |
> | $80-$FE | RAM ($8000-$FEFF) | อ่าน/เขียน data, registers |
> | $FF | RAM ($FF00-$FFFF) | RAM plus I/O slots; $FF00 reserved for future vector |

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

## Chip List (34 logic + ROM + RAM = 36 packages)

> 📌 **Master Reference**: All U# designators are frozen. Use this table for schematic, PCB, and wiring cross-reference.

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
| U25 | 74HC32 | OR gates |
| U26-U27 | 74HC00 ×2 | NAND gates |
| U28 | 74HC86 | Z_match, /T2, WR_DIR |
| U29-U30 | 74HC157 ×2 | Addr mux A[15:8] |
| U31 | 74HC74 | IRQ latch + IE flag |
| U32 | 74HC574 | Data Page Register |
| U33 | 74HC21 | SETDP decode (gate1) + EI decode (gate2) |
| U34 | 74HC541 | IRL-to-IBUS immediate buffer |

---

## Derived Signals

```
ADDR_REQ     = SRC | STR
PC_INC       = T0 | T1
ACC_CLK   = NAND(T2, AC_WR)          ← U27 gate D → U9 CLK, U21 CLK
/ADDR_MODE   = NAND(ADDR_REQ, T2)    ← LOW selects {DP,IRL}; HIGH selects PC
/IRL_OE      = NAND(T2, /ADDR_MODE)
/AC_BUF      = NAND(T2, STR)            ← also RAM /WE
BUF_OE_N     = NOT(/IRL_OE)             ← U7 /OE
WR_DIR       = NOT(/AC_BUF)             ← U7 DIR and ROM /OE
/PC_LD       = NAND(T2, PC_LOAD_COND)
PC_LOAD_COND = JMP | (BR & Z_match)
Z_match      = Z_flag XOR SUB
PG_CLK       = /T2 | /PG_cond           ← U23 latches on rising edge
DP_Load      = T2 & XOR_MODE & /ADDR_MODE & /AC_WR  ← U33 gate 1
EI_decode    = T2 & SRC & /XOR_MODE & /AC_WR        ← U33 gate 2
```

---

## Signal Naming Convention

### Polarity

| Type | Signals | Convention |
|------|---------|------------|
| **Active High** | AC_WR, SRC, STR, BR, JMP, PC_INC, ADDR_REQ, PC_LOAD_COND, DP_Load, EI_decode, Z_match, WR_DIR | Name = assert function. HIGH = active. |
| **Active Low** | /ADDR_MODE, /PC_LD, /IRL_OE, /AC_BUF, /BR_TAKEN, /RST, /IRQ | Prefix `/` = active LOW. LOW = assert. |
| **Clock-edge** | ACC_CLK (active LOW→latch on rise), PG_CLK (latch on rising edge), CLK | Edge-triggered. Action on specified edge. |

### Suffix Rules (cross-tool)

| Suffix | Meaning | Example |
|--------|---------|---------|
| (none) | Active HIGH | `AC_WR`, `STR`, `SRC` |
| `_N` | Active LOW (Verilog/FPGA) | `BUF_OE_N`, `PC_LD_N` |
| `/` prefix | Active LOW (schematic only) | `/PC_LD`, `/RST` |
| `_CLK` | Clock input (edge-triggered) | `ACC_CLK`, `PG_CLK` |
| `_FF` | Latched state (flip-flop output) | `IRQ_FF`, `Z_flag` |

> 📌 **Rule**: `/foo` in schematics = `foo_N` in Verilog/KiCad netlist.
> All signals without suffix or prefix are active-high.

---

## Architectural Invariants

These rules hold for **all** versions (v1.0, v1.1, future). Any change that violates them is an architecture break.

| # | Invariant | Rationale |
|:-:|-----------|-----------|
| 1 | Every instruction = exactly 3 phases (T0→T1→T2) | Fixed pipeline, no stalls |
| 2 | PC increments only during T0 and T1 | Fetch phases only |
| 3 | Execution occurs only during T2 | Single execute phase |
| 4 | At most one IBUS driver active at any time | Bus conflict prevention |
| 5 | At most one DBUS driver active at any time | Bus conflict prevention |
| 6 | Valid ISA changes PG/DP only during SETPG/SETDP | Reserved horizontal encodings may share physical gate side effects |
| 7 | AC changes only when AC_WR=1 at T2 | Explicit write control |

### Hardware Signal Invariants (Debug Reference)

| Condition | Guarantee |
|-----------|-----------|
| T0,T1 → PC_INC=1 | Fetch always increments PC |
| /PC_LD=0 → PC_INC ignored | Load wins over increment |
| STR=1 → U7 enabled with WR_DIR=1 | Store path drives IBUS to DBUS |
| SRC=1 → address={DP,IRL} | Data access (not PC) |
| JMP=1 → branch logic bypassed | Unconditional jump |
| AC_WR=0 → AC unchanged | Even if ALU produces result |
| XOR_MODE=1 + /ADDR_MODE + /AC_WR → DP_Load | SETDP decode (U33) |

> 📌 เมื่อ debug ให้ตรวจ invariant ก่อน — ถ้าผิดแปลว่าสายหลุดหรือต่อข้ามบิต

---

## IBUS Drivers (only one active at T2)

| Condition | Driver | Source |
|-----------|--------|--------|
| SRC=0, STR=0 | U6 (IRL) | Immediate |
| SRC=1, STR=0 | U7 (RAM) | RAM read |
| STR=1 | U14 (AC buf) | AC value |

Store: STR=1 → U14 drives IBUS and U7 writes IBUS to DBUS.

---

## IRQ (U31)

### v1.0: Polling IRQ Latch (U31 kept, no hardware vector)

```
/IRQ pin (active LOW, latch on release/rising edge) → IRQ_FF latch (U31 FF-B)
IE flag (U31 FF-A): EI enables, reset disables
Software polls IRQ_FF only if an external /SLOT peripheral exposes the latch
```

**How it works**:
- External device pulls /IRQ LOW, then releases it HIGH → U31 latches IRQ_FF=1 on the release/rising edge
- Main loop reads IRQ_FF through an external /SLOT status device, or observes the LED/test point during bring-up
- If set: branch to handler; avoid calling `EI` again unless software wants IE=1
- Games/TV: use fixed timing loop, poll input during vblank
- Same model as Gigatron (no interrupts, bit-bang everything)

**No hardware vector** — PC is not forced to $FF00 automatically.

### Future Upgrade: Hardware Vector $FF00 (not frozen)

```
Required functions:
- Select PC load data between normal {PG,IRL} and vector constant $FF00
- Assert /PC_LD during IRQ acknowledge
- Generate a safe IRQ_ack that cannot fight normal branch/jump
- Convert acknowledge into active-low clears for U31 IE and IRQ_FF if auto-clear is kept
```

> ⚠️ **Future hardware-vector design only:** `$FF00` อยู่ใน RAM — ต้อง initialize ISR ก่อน EI!
>
> Power-on: RAM มีค่า garbage → ถ้า EI แล้ว IRQ fire จะกระโดดไป garbage
>
> **ขั้นตอนถูกต้อง:**
> ```asm
> ; Boot sequence (first instructions in ROM):
>     SETDP $80       ; 1. ตั้ง DP ให้ชี้ RAM
>     ; ... initialize app ...
>     SETDP $FF       ; 2. ชี้ไป ISR page
>     LI $10          ; 3. โหลด ISR code ลง RAM $FF00+
>     SB $00          ;    (LI opcode → $FF00)
>     LI $FF
>     SB $01          ;    ($FF → $FF01)
>     LI $01
>     SB $02          ;    (J opcode → $FF02)
>     LI $02
>     SB $03          ;    (J target → $FF03)
>     SETDP $80       ; 4. กลับไป RAM page ปกติ
>     EI              ; 5. เปิด interrupt (ปลอดภัยแล้ว!)
> ```
>
> **ห้ามเรียก EI ก่อน initialize ISR ที่ $FF00!**

---

## Power-On State (Hardware)

| Register | Power-on Value | Source |
|----------|:--------------:|--------|
| PC | $0000 | 74HC161 /CLR ← /RST |
| T-state | T0 | 74HC164 /CLR ← /RST |
| PG | **UNKNOWN** | 74HC574 — no /CLR pin |
| DP | **UNKNOWN** | 74HC574 — no /CLR pin |
| AC | **UNKNOWN** | 74HC574 — no /CLR pin |
| Z | **UNKNOWN** | 74HC74 /CLR not connected |
| IE | 0 | 74HC74 /CLR ← /RST |
| IRQ_FF | 0 | 74HC74 /CLR ← /RST |

Boot sequence (first 3 instructions) initializes UNKNOWN registers:
`SETDP $80` → `SETPG $00` → `LI $00`

```
/RST (active LOW)
 │
 ├── U1-U4 /CLR → PC = $0000
 ├── U8 /CLR    → T-state = T0
 ├── U31 /CLR1  → IE = 0
 └── U31 /CLR2  → IRQ_FF = 0

NOT reset (74HC574 has no /CLR):
 ├── PG  = UNKNOWN → fix: SETPG $00
 ├── DP  = UNKNOWN → fix: SETDP $80
 ├── AC  = UNKNOWN → fix: LI $00
 └── Z   = UNKNOWN → fix: LI $00 sets Z=1
```

### Reset Contract (Architectural Guarantee)

```
Software may assume after /RST release:

  PC      = $0000       (guaranteed)
  T-state = T0          (guaranteed)
  IE      = 0           (guaranteed)
  IRQ_FF  = 0           (guaranteed)

  AC, Z, PG, DP = UNDEFINED (no assumption permitted)

Rules:
  • Reading undefined state is legal (will not cause hardware damage)
  • Software MUST initialize before depending on value
  • First 3 instructions MUST NOT use SRC, STR, J, or BEQ/BNE
  • Boot sequence: SETDP $80 → SETPG $00 → LI $00
```

---

## Opcode Freeze (v1.0)

```
┌─────────────────────────────────────────────────────┐
│  OPCODE ALLOCATION FROZEN — Version 1.0             │
│                                                     │
│  Do NOT change existing opcode values.              │
│  Future instructions must use unused encodings.     │
│  Assembler, simulator, and ROM images depend on     │
│  these exact bit patterns.                          │
└─────────────────────────────────────────────────────┘
```

**Reserved opcode policy**: Undefined opcodes execute deterministically
based on their control bits (horizontal encoding). No trap, no NOP override.
Each bit directly controls hardware — behavior is always predictable.

### Illegal Opcode Behavior (3 categories)

| Category | Count | Condition | What happens |
|----------|:-----:|-----------|-------------|
| Defined ISA | 18 | Documented opcodes | Normal operation |
| Undefined safe | 174 | `(opcode & $0C) != $0C` | Hardware does what bits say — deterministic |
| Store-dominant mixed | 64 | `(opcode & $0C) == $0C` (SRC+STR) | STR path writes AC; electrically safe |

**No opcode can crash or damage the CPU.** The horizontal encoding + hardware guard guarantees this.

**Example — undefined opcode $11** (00010001 = AC_WR + JMP):
```
T2: AC latches ALU output (AC_WR=1)
    AND PC loads {PG, IRL} (JMP=1)
    Both happen simultaneously — deterministic, just not useful.
```

**Example — mixed opcode $0C** (00001100 = SRC + STR):
```
T2: STR=1 → U14 drives IBUS and U7 writes IBUS→DBUS
    ROM /OE=WR_DIR=1, so ROM is tri-stated during the write direction
    RAM write proceeds only if A15=1
    No bus contention. Store wins.
```

**Mixed SRC+STR opcodes** are reserved but electrically safe. STR dominates
the bus direction; source/read semantics are ignored by the physical store path.

---

## Hardware Freeze Policy (v1.0)

```
┌─────────────────────────────────────────────────────┐
│  HARDWARE SIGNALS FROZEN — Version 1.0              │
│                                                     │
│  The following signals are architectural.           │
│  Future revisions MUST preserve their behavior.     │
└─────────────────────────────────────────────────────┘
```

| Signal | Function | Contract |
|--------|----------|----------|
| PC_INC | PC increment | =1 during T0,T1 only |
| /PC_LD | PC load | =0 → loads {PG,IRL} into PC |
| ACC_CLK | AC latch | Rising edge → AC captures mux output |
| /ADDR_MODE | Address select | =0 → ABUS={DP,IRL}; =1 → ABUS=PC |
| BUF_OE_N | U7 output enable | =0 → U7 enabled |
| WR_DIR | U7 direction | =1 → IBUS-to-DBUS (store path) |
| /AC_BUF | AC buffer + RAM /WE | =0 → U14 active + RAM write |
| DP_Load | Data Page latch | Rising edge → U32 captures IBUS |
| PG_CLK | Page Reg latch | Rising edge → U23 captures IBUS |

Any FPGA port, simulator, or hardware revision must produce identical
observable behavior for all 18 defined instructions when these signals
follow their contracts above.

---

## Bus Ownership

| Phase | ABUS | DBUS Driver | IBUS Driver |
|:-----:|:----:|:-----------:|:-----------:|
| T0 (fetch) | PC | ROM or RAM | U7 (DBUS→IBUS) |
| T1 (fetch) | PC | ROM or RAM | U7 (DBUS→IBUS) |
| T2 immediate | PC | (stale) | **U34** (IRL) |
| T2 load (SRC=1) | {DP,IRL} | RAM or ROM | **U7** (DBUS→IBUS) |
| T2 store (STR=1) | {DP,IRL} | **U7** (IBUS→DBUS) | **U14** (AC) |

**Rule: At no time may two drivers be active on the same bus.**
- IBUS: U34, U7, U14 — safe by direction and /OE timing
- DBUS: ROM, RAM, U7 — safe via /CE, /WE, ROM /OE=WR_DIR

### Forbidden Bus States

| # | Condition | Conflict | Hardware Safety |
|:-:|-----------|----------|----------------|
| 1 | U34 enabled AND U7 enabled (IBUS) | Two IBUS drivers | /IRL_OE requires /ADDR_MODE=1 → ADDR_REQ=0 → U7 disabled |
| 2 | U14 enabled AND U7 enabled | No conflict | U14 drives IBUS; U7 DIR=write treats IBUS as input and drives DBUS |
| 3 | ROM enabled AND U7 writing DBUS | ROM vs U7 on DBUS | ROM /OE=WR_DIR disables ROM output during store |
| 4 | RAM output AND U7 writing DBUS | RAM vs U7 on DBUS | RAM /WE=0 during store → RAM in write mode, not driving DBUS |

> ⚠️ Any v1.1 change to control logic **must** preserve these mutual-exclusion guarantees.
> Violation = bus contention = potential chip damage.

---

## Expansion Budget

```
Design Goal: keep v1.0 at the smallest easy-to-build baseline

RV8-GR v1.0:  36 packages (34 logic + ROM + RAM)
Hardware vector: future/unfrozen; not part of the 36-package wiring guide
```

Any feature proposal must justify chip cost against this budget.
See `04_bank_switch.md` for ROM banking contract (v2.x, +1 chip).

---

## Key Design Decisions

1. **XOR reuse** — Same gates do ADD/SUB/XOR via B-input mux
2. **A15 chip select** — ROM /CE=A15, RAM /CE=/A15 (no decoder)
3. **Store bus safety** — U7 /OE=BUF_OE_N and ROM /OE=WR_DIR
4. **Z flag /PR trick** — U22→U21 async preset (0 extra gates)
5. **BNE reuse** — Z_match = Z XOR SUB (reuse SUB bit as condition flip)
6. **PG_CLK timing** — Rising edge at end of T2 (sync with CLK)

---

## Verification

| Test | Result |
|------|--------|
| Assembler | `tools/test_rv8gr_asm.py` covers frozen opcodes, aliases, labels, `.org`, bounds, overlap, and page-safe branches |
| Python CPU sim | `sim/chip_sim.py` covers ISA smoke, SETDP, ROM reads, RAM reads/writes, SETPG, and polling IRQ state |
| Components-backed Python sim | `sim/components_chip_sim.py` runs the same CPU-level checks through Components chip adapters |
| TTL chip definitions | `sim/chips/test_chips.py` verifies the 14 chip types used by the RV8GR model |
| Wiring verifier | `sim/verify_wiring.py` checks package count, bus ownership, ROM `/WE` inactive, and representative programs |
| Components package verifier | `sim/verify_components.py` checks 16 part types and 36 packages |
| Behavioral Verilog | `tools/run_all_verilog_tb.sh` runs the behavioral RTL regression benches |
| Behavioral vs TTL-chip Verilog | `tools/run_dual_verilog_compare.sh` compares `rtl/rv8gr_cpu.v` with `rtl/rv8gr_chip_level.v` |
| Four-model equivalence | `tools/check_python_verilog_equivalence.py` compares both Python sims and both Verilog models over the shared all-ISA ROM with 55 checkpoints |

Source of Truth:
- `00_design_isa.md` — Architectural spec (this file)
- `02_wiring_guide.md` — Physical wiring spec (pin-level)
- `11_cpu_logical_test_protocol.md` — CPU logical verification protocol
- `06_debug_plan.md` — Physical debug/build verification steps

---

## Instruction Trace Contract

All simulators, testbenches, and debug logs **must** use this canonical format:

```
Cycle  Phase  PC    ABUS  IRH  IRL  Mnemonic  AC  Z  PG  DP  IE  IRQ  Notes
-----  -----  ----  ----  ---  ---  --------  --  -  --  --  --  ---  -----
1      T0     0000  0000  10   --   --        00  1  ??  ??  0   0    fetch ctrl
2      T1     0001  0001  10   42   --        00  1  ??  ??  0   0    fetch operand
3      T2     0002  0002  10   42   LI        42  0  ??  ??  0   0    AC=imm
4      T0     0003  0003  40   --   --        42  0  ??  ??  0   0    fetch ctrl
5      T1     0004  0004  40   80   --        42  0  ??  ??  0   0    fetch operand
6      T2     0005  0005  40   80   SETDP     42  0  ??  80  0   0    DP=80
```

| Field | Width | Description |
|-------|:-----:|-------------|
| Cycle | dec | Global clock count (1-based) |
| Phase | T0/T1/T2 | Ring counter state |
| PC | 4 hex | PC value at **start** of phase (before increment) |
| ABUS | 4 hex | Address bus output (=PC when /ADDR_MODE=1, ={DP,IRL} when /ADDR_MODE=0) |
| IRH | 2 hex | IR control byte (-- if not yet latched) |
| IRL | 2 hex | IR operand (-- if not yet latched) |
| Mnemonic | text | Decoded instruction name (-- until T2) |
| AC | 2 hex | Accumulator (value after phase completes) |
| Z | 0/1 | Zero flag |
| PG | 2 hex | Page Register (?? = unknown at boot) |
| DP | 2 hex | Data Page Register (?? = unknown at boot) |
| IE | 0/1 | Interrupt Enable flag |
| IRQ | 0/1 | IRQ latch state |
| Notes | text | Signal changes, result, or bus activity |

**Applies to**: Verilog (`$display`), chip_sim.py, soft_debug.py, FPGA port, hardware single-step log.

**PC convention**: PC is sampled at the **rising edge** of each phase (before PC_INC takes effect). Thus T0 shows the address being fetched, not the next address.

**ABUS convention**: Shows the actual address on the bus during that phase. For T2 data access (LB/SB/ADD/SUB/XOR with SRC=1 or STR=1), /ADDR_MODE=0 and ABUS={DP,IRL}. Otherwise /ADDR_MODE=1 and ABUS=PC.

**Minimal mode**: For quick checks, tools MAY omit ABUS/PG/DP/IE/IRQ columns and show only `Cycle Phase PC IRH IRL AC Z Notes`. The full format is required for regression tests and bug reports.

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
