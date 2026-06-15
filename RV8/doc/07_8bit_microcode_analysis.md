# RV8 — 8-bit Control Word Redesign

## Analysis: What signal combinations actually occur?

Looking at all micro-steps across 35 instructions, only ~12 unique
combinations of the 16 control signals are ever used:

| # | Combination | Used in |
|:-:|-------------|---------|
| 1 | PC_ADDR + BUF_OE + IR_CLK + PC_INC | Fetch opcode (all instr) |
| 2 | PC_ADDR + BUF_OE + OPR_CLK + PC_INC | Fetch operand (all instr) |
| 3 | REG_RD_EN(rd) + ALUB_CLK | Load rd → ALU B |
| 4 | REG_RD_EN(rs) + ALUB_CLK | Load rs → ALU B |
| 5 | REG_RD_EN(rd) + ALUR_CLK + FLAGS_CLK | Compute (rd op B) |
| 6 | REG_RD_EN(rd) + ALUR_CLK + FLAGS_CLK + ALU_SUB | Compute SUB |
| 7 | REG_WR_EN + STEP_RST | Writeback + end |
| 8 | ALUR_CLK + FLAGS_CLK + STEP_RST | Compute + end (no writeback) |
| 9 | BUF_OE + ADDR_CLK | Setup memory address |
| 10 | BUF_OE + REG_WR_EN + STEP_RST | Memory read → reg + end |
| 11 | BUF_OE + BUF_DIR + STEP_RST | Memory write + end |
| 12 | PC_LOAD + STEP_RST | Branch taken + end |
| 13 | STEP_RST | End (no-op / branch not taken) |
| 14 | ADDR_HI_CLK | Latch address high |
| 15 | PC_LOAD + REG_WR_EN + STEP_RST | JAL (save PC + jump + end) |

That's only ~15 distinct micro-operations! 4 bits can encode 16 options.
But we also need ALU_SUB as a modifier, and reg select (rd vs rs).

## 8-bit Encoding

```
[7:4] = MICRO-OP (16 possible actions)
[3:2] = ALU_MODE (ADD/SUB/XOR/AND — for ops that use ALU)
[1:0] = REG_SEL modifier (00=rd, 01=rs, 10=sp, 11=unused)
```

### Micro-ops [7:4]:

| Code | Mnemonic | Signals activated |
|:----:|----------|-------------------|
| 0000 | FETCH_OP | PC_ADDR, BUF_OE, IR_CLK, PC_INC |
| 0001 | FETCH_OPR | PC_ADDR, BUF_OE, OPR_CLK, PC_INC |
| 0010 | LOAD_B | REG_RD_EN(sel), ALUB_CLK |
| 0011 | COMPUTE | REG_RD_EN(rd), ALUR_CLK, FLAGS_CLK |
| 0100 | WRITE_END | REG_WR_EN(sel), STEP_RST |
| 0101 | COMP_WR_END | REG_RD_EN(rd), ALUR_CLK, FLAGS_CLK, REG_WR_EN, STEP_RST |
| 0110 | CMP_END | REG_RD_EN(rd), FLAGS_CLK, STEP_RST |
| 0111 | MEM_RD_SETUP | BUF_OE, ADDR_CLK |
| 1000 | MEM_RD_REG | BUF_OE, REG_WR_EN(sel), STEP_RST |
| 1001 | MEM_WR_END | BUF_OE, BUF_DIR, REG_RD_EN(sel), STEP_RST |
| 1010 | BR_TAKEN | PC_LOAD, STEP_RST |
| 1011 | END | STEP_RST |
| 1100 | JAL_END | PC→result, REG_WR_EN(sel), PC_LOAD, STEP_RST |
| 1101 | ADDR_HI | ADDR_HI_CLK |
| 1110 | OPR_TO_B | OPR→ALUB (operand drives ALU B input) |
| 1111 | RESERVED | — |

### ALU_MODE [3:2] (active during COMPUTE / COMP_WR_END):

| Code | Mode |
|:----:|------|
| 00 | ADD |
| 01 | SUB |
| 10 | XOR |
| 11 | AND/OR (sub-select from opcode) |

### REG_SEL [1:0] (active during LOAD_B / WRITE_END / MEM ops):

| Code | Selects |
|:----:|---------|
| 00 | rd (from opcode[2:0]) |
| 01 | rs (from operand[7:5]) |
| 10 | sp (r7, hardwired) |
| 11 | r0 (zero, for zero-source) |

## Micro-step sequences with 8-bit encoding:

### LI rd, imm (3 cycles)
```
Step 0: FETCH_OP                    → $00
Step 1: FETCH_OPR                   → $10
Step 2: OPR_TO_B + WRITE_END(rd)   → can we combine? No, one op per step.
```

Hmm — with hardware regs, LI was 1 execute step (OPR → reg write).
With encoded micro-ops, we need that as a single operation.

Add: `LI_END` = OPR→rd, STEP_RST. Use op code $E0 (micro-op 1110, sel=rd=00)
Actually redefine OPR_TO_B:

Let me reconsider. The RV8 with hardware registers can do **multi-signal steps** because the 16-bit control word fires them all simultaneously. The question is: how many unique steps do we actually need?

## Better approach: Enumerate ALL unique micro-steps

Let me list every micro-step that any instruction uses:

| ID | What happens | Count of instructions using it |
|:--:|---|:---:|
| F0 | fetch opcode | ALL |
| F1 | fetch operand | ALL |
| A  | OPR → ALU_B (latch immediate into B) | Implicit in hardware |
| B  | rs → IBUS → ALU_B latch | ADD/SUB/AND/OR/XOR/SLT |
| C  | rd → IBUS, ALU computes, latch result+flags | All ALU |
| D  | ALU_result → rd, end | All ALU write |
| E  | OPR → rd directly, end | LI |
| F  | compute + no write + end (CMP) | CMP, CMPI, SLT |
| G  | address = rs+off → IBUS → ADDR latch | LB, SB |
| H  | mem[addr] → rd, end | LB |
| I  | rd → mem[addr], end | SB |
| J  | SP--, addr=SP | PUSH |
| K  | addr=SP, SP++ | POP |
| L  | if flag: PC += off, end; else: end | BEQ/BNE/BCS/BCC |
| M  | PC_lo → rd, PC += off, end | JAL |
| N  | PC ← rs, end | JALR/JMP |

That's about 14-15 unique operations. Fits in 4 bits (16 codes).

But several need **ALU mode** and **register select** as parameters.

## FINAL: Pragmatic 8-bit encoding for RV8

Since hardware registers let you read/write in one cycle, most instructions
only need 1-2 execute steps. The total unique micro-ops is small.

### Direct-mapped approach (no decode chip needed!):

Since we have only ~15 unique micro-steps, and 8 bits = 256 codes,
we can use a **lookup table in hardware** (another small ROM or PLA)
to expand 8→16 bits. But that defeats the purpose.

### ACTUAL simplest approach:

**Keep the 16 original signals but deliver them from TWO reads of the same ROM:**

```
Clock phase A: ROM[addr] → latch #1 (bus control byte)
Clock phase B: ROM[addr+1] → latch #2 (ALU control byte)
```

No wait, this is the time-multiplex I rejected before.

### THE REAL ANSWER:

Looking at the signal patterns carefully:

**Observation: During fetch (steps 0-1), the pattern is ALWAYS the same.**
So we can **hardwire** fetch — no microcode needed for steps 0-1!

With fetch hardwired:
- Step counter bits [2:1] = 00 → force fetch pattern (PC_ADDR, BUF_OE, etc.)
- Step counter bit [0] selects IR_CLK vs OPR_CLK
- Steps 2+ come from microcode ROM

This means microcode only controls **execute steps** (2-7), which need fewer
simultaneous signals (usually 2-3 at most). 8 bits is enough!

### Fetch hardwired (2 gates + step counter):

```
FETCH_ACTIVE = (step < 2)  → from step counter bit 1 (inverted)

When FETCH_ACTIVE:
  PC_ADDR = 1 (always)
  BUF_OE = 1 (always)  
  PC_INC = 1 (always)
  IR_CLK = !step[0]  (step 0 only)
  OPR_CLK = step[0]  (step 1 only)
  All other signals = 0

When !FETCH_ACTIVE:
  All signals from microcode ROM data[7:0]
```

Cost: 1 AND gate + 1 inverter (from spare 74HC04/00 already in design).

### Execute-only 8-bit control word:

Now we only need 8 bits for execute steps. The signals needed during execute:

```
Bit 0: REG_RD_EN   — register drives IBUS
Bit 1: REG_WR_EN   — write ALU result to register  
Bit 2: ALUB_CLK    — latch IBUS into ALU B
Bit 3: ALUR_CLK    — latch ALU result
Bit 4: ALU_SUB     — subtract mode
Bit 5: FLAGS_CLK   — update flags
Bit 6: STEP_RST    — end instruction
Bit 7: BUS_MODE    — 0=register bus, 1=memory bus (BUF_OE+ADDR)
```

That's exactly 8 signals! And they cover everything:

| Step | Byte | Action |
|------|:----:|--------|
| ADDI compute | $2D | REG_RD_EN + ALUR_CLK + FLAGS_CLK = bits 0+3+5 |
| ADDI write | $42 | REG_WR_EN + STEP_RST = bits 1+6 |
| SUB compute | $3D | REG_RD_EN + ALUR_CLK + FLAGS_CLK + ALU_SUB |
| Load rs→B | $05 | REG_RD_EN + ALUB_CLK |
| LI (OPR→rd) | $42 | REG_WR_EN + STEP_RST (OPR hardwired to ALU B) |
| MEM read | $80 | BUS_MODE (enable external bus) |
| Branch taken | $40+PC_LOAD? | Hmm, need PC_LOAD too... |

**Problem**: We need `PC_LOAD` for branches and `ADDR_CLK` for memory ops.
That's 2 more signals = 10 total. Doesn't fit in 8.

**Fix**: Dual-purpose bits:
- `BUS_MODE` (bit 7): when 1, BUF_OE=1 and replaces register bus
- Combine: `ALU_SUB` (bit 4) is only meaningful during ALUR_CLK. 
  When `STEP_RST=1` and `ALU_SUB=1`: means `PC_LOAD` instead of SUB.

```
Bit 7: BUS_MODE     — 1=external memory on IBUS
Bit 6: STEP_RST     — end instruction  
Bit 5: FLAGS_CLK    — update flags
Bit 4: ALU_OP/CTRL  — during ALU: SUB mode. With STEP_RST: PC_LOAD
Bit 3: ALUR_CLK     — latch ALU result
Bit 2: ALUB_CLK     — latch IBUS → ALU B
Bit 1: REG_WR_EN    — write to register
Bit 0: REG_RD_EN    — register → IBUS
```

### Derived signals:
```
PC_LOAD = bit4 AND bit6 (ALU_OP=1 during STEP_RST)
ALU_SUB = bit4 AND NOT bit6 (ALU_OP=1 during non-end step)
MEM_WR  = bit1 AND bit7 (REG_WR_EN + BUS_MODE = write to memory)
MEM_RD  = bit0 AND bit7 (REG_RD_EN + BUS_MODE = read from memory... wait, conflict)
```

Hmm, bit overloading gets messy. Let me try one more arrangement:

```
Bit 7: MEM/REG      — 0=register mode, 1=memory mode
Bit 6: END          — STEP_RST
Bit 5: FLAGS        — FLAGS_CLK
Bit 4: ALU_MODE     — 0=ADD, 1=SUB (XOR/AND from opcode bits directly)
Bit 3: ALU_LATCH    — ALUR_CLK (compute result)
Bit 2: B_LOAD       — ALUB_CLK (load B register)
Bit 1: WRITE        — REG_WR_EN (reg mode) or MEM_WR (mem mode)
Bit 0: READ         — REG_RD_EN (reg mode) or MEM_RD (mem mode)
```

### Dual-purpose bit 1 and bit 0 based on bit 7:
- Bit7=0 (register): bit0=REG_RD_EN, bit1=REG_WR_EN
- Bit7=1 (memory): bit0=BUF_OE(read), bit1=BUF_OE+BUF_DIR(write)

### What about PC_LOAD and ADDR_CLK?
- PC_LOAD = END + ALU_MODE + READ? Too hacky.
- ADDR_CLK: always active in memory mode? Or: B_LOAD in memory mode = ADDR_CLK?

Actually: in memory mode, "B_LOAD" (bit 2) makes no sense for ALU B.
Repurpose: in memory mode, bit2 = ADDR_CLK, bit3 = ADDR_HI_CLK.

```
When bit7=0 (REGISTER mode):
  bit0: REG_RD_EN (selected reg → IBUS)
  bit1: REG_WR_EN (ALU result → selected reg)
  bit2: ALUB_CLK (IBUS → ALU B latch)
  bit3: ALUR_CLK (ALU compute → result latch)
  bit4: ALU_SUB
  bit5: FLAGS_CLK

When bit7=1 (MEMORY mode):
  bit0: BUF_OE, BUF_DIR=0 (memory → IBUS, read)
  bit1: BUF_OE, BUF_DIR=1 (IBUS → memory, write)
  bit2: ADDR_CLK (latch IBUS → address register)
  bit3: PC_LOAD (load PC from address/offset)
  bit4: (unused or ADDR_HI)
  bit5: FLAGS_CLK

bit6: END (STEP_RST) — works in both modes
```

## This works! Let me verify with key instructions:

### LI rd, imm (3 cycles total = 2 fetch + 1 execute)
```
Step 0-1: hardwired fetch
Step 2: REG mode, REG_WR_EN + END = $42 + END = $42 | $40 = $42
  Actually: OPR already feeds ALU B. ALU = 0 + OPR = OPR (pass through).
  Need ALUR_CLK too: bit3. And REG_WR: bit1. And END: bit6.
  = $4A = 0_1_0_0_1_0_1_0
  Hmm: bits = [7:0] = 0(reg) 1(end) 0(no flags) 0(add) 1(ALUR) 0(no B_load) 1(WR) 0(no RD)
  = $4A. Result: ALU computes 0+OPR=OPR, latches result, writes to rd, ends.
  BUT: ALU A input? If no REG_RD_EN, what drives A? Needs to be 0.
  → Hardware: when REG_RD_EN=0, IBUS=0 (pull-down or tri-state=0). ALU A=0. 0+OPR=OPR. ✅
```

### ADDI rd, imm (4 cycles = 2 fetch + 2 execute)
```
Step 2: REG mode, REG_RD_EN + ALUR_CLK + FLAGS_CLK + REG_WR_EN + END
  But wait: we need rd on IBUS (for ALU A), and OPR on ALU B (hardwired).
  Result = rd + OPR. Write back to rd.
  = bit0(RD) + bit1(WR) + bit3(ALUR) + bit5(FLAGS) + bit6(END)
  = $6B = 0_1_1_0_1_0_1_1
  All in ONE step! rd→IBUS→ALU_A, OPR→ALU_B, A+B→result, result→rd, flags, end.
```

Wait — can we do read AND write in the same cycle? With hardware registers: yes!
The 138 decoder enables rd onto bus (read), ALU computes combinatorially,
and on the clock edge, result latches into rd (write). This is how the original
RV8 works. **Single-cycle compute+writeback.** ✅

### ADD rd, rs (5 cycles = 2 fetch + 3 execute)
```
Step 2: REG mode, REG_RD_EN(rs) + ALUB_CLK = load rs into ALU B
  = $05 = 0_0_0_0_0_1_0_1 (RD + B_LOAD)
  But REG_RD_EN reads which register? rd or rs?
  Need a SEL bit... we're out of bits!
```

**Problem**: With hardware registers, we need to select WHICH register to read.
The original RV8 uses the 138 decoder driven by either opcode[2:0] (rd) or
operand[7:5] (rs). A control signal selects which field drives the 138.

We need `REG_SEL` somewhere. Options:
- Sacrifice bit 4 (ALU_SUB) and encode ALU op from opcode instead
- Use bit 4 as REG_SEL (0=rd, 1=rs)

If ALU operation comes from opcode[5:3] directly (hardwired, no microcode control):
- ADD/SUB/XOR/AND/OR → opcode[5:3] drives XOR gate and logic muxes
- This is the RV8-GR approach (horizontal encoding)!

**YES!** The ALU mode doesn't need to be in the microcode — it's already in the opcode.
Hardware decodes opcode[5:3] → ALU operation directly. Microcode only sequences WHEN.

### Revised 8-bit (ALU op from opcode):

```
When bit7=0 (REGISTER mode):
  bit0: REG_RD_EN
  bit1: REG_WR_EN  
  bit2: ALUB_CLK
  bit3: ALUR_CLK
  bit4: REG_SEL (0=rd from opcode[2:0], 1=rs from operand[7:5])
  bit5: FLAGS_CLK
  bit6: END (STEP_RST)
  bit7: 0

When bit7=1 (MEMORY mode):
  bit0: MEM_RD (BUF_OE, DIR=in)
  bit1: MEM_WR (BUF_OE, DIR=out)
  bit2: ADDR_CLK
  bit3: PC_LOAD
  bit4: REG_SEL (which reg for data)
  bit5: FLAGS_CLK
  bit6: END
  bit7: 1
```

### Re-verify:

**ADDI rd, imm (3 cycles)**:
```
Step 2: RD(rd) + ALUR + FLAGS + WR + END
  = 0_1_1_0_1_0_1_1 = bit0+1+3+5+6 = $6B (REG_SEL=0=rd)
  rd → IBUS → ALU_A, OPR → ALU_B, compute, result → rd, flags, end.
```
ONE execute step. **3 cycles total.** Same as original RV8! ✅

**ADD rd, rs (4 cycles)**:
```
Step 2: RD(rs) + B_LOAD
  = 0_0_0_1_0_1_0_1 = bit0+2+4 = $15 (REG_SEL=1=rs)
  rs → IBUS → ALU_B latch.
Step 3: RD(rd) + ALUR + FLAGS + WR + END
  = 0_1_1_0_1_0_1_1 = $6B (REG_SEL=0=rd)
  rd → ALU_A, B_latch → ALU_B, compute, result → rd, end.
```
Two execute steps. **4 cycles total.** ✅ (original was 4-5)

**LI rd, imm (3 cycles)**:
```
Step 2: WR(rd) + ALUR + END (no RD, so IBUS=0, result = 0+OPR = OPR)
  = 0_1_0_0_1_0_1_0 = bit1+3+6 = $4A
```
**3 cycles.** ✅

**LB rd, [imm8] (5 cycles)**:
```
Step 2: MEM mode, ADDR_CLK (latch OPR as address — OPR on IBUS via hardwired path)
  = 1_0_0_0_0_1_0_0 = $84 — wait, need MEM_RD? No, just latching address.
  Actually: during MEM mode, who drives IBUS for ADDR_CLK? Need OPR→IBUS.
  Hmm. In register mode OPR feeds ALU_B directly (hardwired).
  In memory mode for address setup, we need the computed address on IBUS.
  For zero-page: address = {$00, imm8}. OPR = imm8. We need OPR → address latch.
  
  Fix: ADDR_CLK latches from OPR directly (not IBUS). Hardware: wire OPR output
  to address latch input. ADDR_CLK just clocks it.
  = 1_0_0_0_0_1_0_0 = bit2+7 = $84
  
Step 3: MEM mode, MEM_RD + END... but read data goes where?
  Need: data → IBUS → reg write.
  = 1_1_0_0_0_0_0_1 = bit0+6+7 = $C1? But REG_WR is bit1 in mem mode = MEM_WR...
```

There's a conflict. In memory mode, bit1 = MEM_WR. But for LB we need to read memory AND write to register simultaneously. 

**Fix**: After memory read, data is on IBUS. In the SAME step, we can write it to register if we add a register write path in memory mode. 

Redefine: In memory mode, REG_WR still works (bit5 or repurpose):
```
When bit7=1 (MEMORY mode):
  bit0: MEM_RD (external → IBUS)
  bit1: MEM_WR (IBUS → external)
  bit2: ADDR_CLK (OPR/ALU → address latch)
  bit3: PC_LOAD
  bit4: REG_SEL
  bit5: REG_WR_EN (IBUS → register, works with MEM_RD!)
  bit6: END
  bit7: 1
```

Now FLAGS_CLK is gone in memory mode. That's fine — memory ops don't set flags.

**LB rd, [imm8] (4 cycles)**:
```
Step 2: MEM, ADDR_CLK = $84 (latch address from OPR)
Step 3: MEM, MEM_RD + REG_WR(rd) + END = 1_1_1_0_0_0_0_1 = bit0+5+6+7 = $E1
  Memory data → IBUS → rd. Done!
```
**4 cycles.** ✅

**SB rd, [imm8] (4 cycles)**:
```
Step 2: MEM, ADDR_CLK = $84
Step 3: MEM, MEM_WR + REG_SEL=rd + END... but we need rd on IBUS.
  In mem mode bit0=MEM_RD, bit1=MEM_WR. Need rd → IBUS for writing.
  Who drives IBUS? In reg mode: REG_RD_EN. In mem mode: MEM_RD drives IBUS.
  For SB: register drives IBUS, then MEM_WR stores it. Need REG_RD in mem mode.
  
  FIX: bit0 in mem mode = "external drives IBUS" (read).
       To write memory, we need register → IBUS → memory.
       So: enter register mode to put rd on IBUS, with memory write?
       Or: bit0 in mem mode means "MEM_RD" and we add REG_RD elsewhere.
```

This is getting tangled. The problem is **store** instructions need the register value to drive the bus while the memory write signal is also active. Let me approach differently.

## FINAL CLEAN APPROACH

The key realization: we're overcomplicating this. What if we keep it fully horizontal but use **2 bits for source** and **2 bits for destination**?

```
[7:6] SOURCE (who drives IBUS):
  00 = register(sel)
  01 = ALU result  
  10 = memory data (external read)
  11 = OPR (operand register)

[5:4] DEST (who latches from IBUS):
  00 = nothing
  01 = register(sel)
  10 = ALU_B latch
  11 = memory write (external)

[3] ALU_LATCH — clock ALU result register (combinatorial → registered)
[2] FLAGS — update flags
[1] REG_SEL — 0=rd, 1=rs
[0] END — STEP_RST
```

### Verify all key instructions:

**LI rd, imm (3 cycles):**
```
Step 2: SRC=OPR, DST=reg(rd), END
  [11][01][0][0][0][1] = $D1 — OPR → rd, end. Done!
```

**ADDI rd, imm (4 cycles):**
```
Step 2: SRC=reg(rd), DST=ALU_B
  [00][10][0][0][0][0] = $08 — rd → ALU_B (but we want OPR in ALU_B, not rd!)
```

Wait. For ADDI, ALU needs: A=rd, B=imm. If OPR is hardwired to ALU_B... then:
```
Step 2: SRC=reg(rd), DST=nothing, ALU_LATCH + FLAGS + END, write back
  But we need ALU result to go to rd. DST=reg means "IBUS → reg". 
  If SRC=ALU_result: [01][01][1][1][0][1] = $75 — ALU→rd, latch, flags, end.
  But ALU input A = IBUS? No, A should = rd.
```

The issue: **when does ALU compute?** If ALU is combinatorial (always computing A op B), we need A and B stable before clocking the result.

In hardware register design:
- ALU A input = IBUS (whatever's driving it)
- ALU B input = either OPR register (hardwired) or ALU_B latch
- ALU output = A op B (continuous, combinatorial)
- ALUR_CLK latches the result

So for ADDI: 
1. Set SRC=reg(rd) → rd value appears on IBUS → ALU_A = rd
2. ALU_B = OPR (hardwired) → ALU computes rd + imm continuously
3. Clock ALUR → result latched
4. Now set SRC=ALU_result, DST=reg(rd) → result → rd

Can steps 3-4 happen in one cycle? If ALU result register feeds IBUS when SRC=ALU:
```
Step 2: SRC=reg(rd), DST=nothing, ALU_LATCH + FLAGS
  = [00][00][1][1][0][0] = $0C — rd on IBUS, ALU latches rd+OPR, flags update
Step 3: SRC=ALU, DST=reg(rd), END
  = [01][01][0][0][0][1] = $51 — ALU result → rd, end
```
**4 cycles.** Same as original! ✅

**But original RV8 does it in 3 cycles** (compute+write in one step). Can we?

The original does: rd→IBUS→ALU_A, ALU computes, result→rd all on same clock edge.
This works because 574 reads on /OE (level) but writes on CLK edge. So within one
cycle: /OE enables rd output, ALU computes, rising edge stores result back.

To do this in our encoding, we need: SRC=reg(rd) AND DST=reg(rd) AND ALU_LATCH + FLAGS + END simultaneously. That's:
```
[00][01][1][1][0][1] = $17 — reg(rd)→IBUS, ALU latches, result→reg(rd), flags, end.
```

BUT: DST=reg(rd) means "latch IBUS into rd". IBUS = rd (from source). 
We want to latch ALU RESULT into rd, not IBUS directly.

**The problem**: DST=reg(01) latches from IBUS. But we want to latch from ALU result.

**Fix**: Change DST=01 to mean "ALU_result → reg" (not IBUS → reg). Since ALU result
is the most common thing written to registers, this makes more sense:

```
[5:4] DEST:
  00 = nothing  
  01 = ALU_result → register(sel)  ← CHANGED
  10 = IBUS → ALU_B latch
  11 = IBUS → memory write (external)
```

And add a new way to write IBUS directly to register (for LI, LB):
- LI: SRC=OPR... but OPR→reg needs IBUS→reg path.
- Make DST=01 do ALU→reg, and encode "IBUS→reg" as... SRC=x + ALU_LATCH + DST=ALU→reg? 
  If ALU mode=PASS_B (B=OPR) and we latch: ALU_result = OPR. Then DST=01 writes it. Works!

But where does ALU mode come from? We said opcode[5:3] drives ALU mode directly.
For LI we need ALU=PASS_B, but opcode[5:3]=000 for LI which is ADD... ADD with A=0 and B=OPR = OPR. ✅ (same trick as before).

So:
**LI rd, imm (3 cycles):**
```
Step 2: SRC=nothing(IBUS=0), DST=ALU→reg(rd), ALU_LATCH, END
  [xx][01][1][0][0][1] = with SRC=00(reg) but REG_RD_EN=0?
```

Hmm, SRC=00 enables register read. We need "no source" = IBUS pulled to 0.

Add SRC=00 means "nothing/zero" and SRC=01 means "register"?

OK I think I've been going back and forth. Let me just commit to one clean design:

## FINAL FINAL: 8-bit Horizontal for RV8

```
Bit 7: SRC1 ─┐ Source
Bit 6: SRC0 ─┘
Bit 5: DST1 ─┐ Destination  
Bit 4: DST0 ─┘
Bit 3: ALU_LATCH (clock result)
Bit 2: FLAGS
Bit 1: SEL (0=rd, 1=rs)
Bit 0: END

SOURCE [7:6]:
  00 = none (IBUS = 0, for LI/LUI → ALU does 0+OPR=OPR)
  01 = REG(sel) → IBUS (register read)
  10 = MEM → IBUS (external memory read, addr from latch)
  11 = ALU_result → IBUS (for writeback)

DEST [5:4]:
  00 = none
  01 = IBUS → REG(sel) write
  10 = IBUS → ALU_B latch
  11 = IBUS → MEM write (external memory)
```

### Derived hardware signals:
```
REG_RD_EN = (SRC == 01)
REG_WR_EN = (DST == 01) 
ALUB_CLK  = (DST == 10)
BUF_OE    = (SRC == 10) OR (DST == 11)
BUF_DIR   = (DST == 11)
MEM_RD    = (SRC == 10)
MEM_WR    = (DST == 11)
ALUR_CLK  = bit3
FLAGS_CLK = bit2
REG_SEL   = bit1 (0=rd, 1=rs)
STEP_RST  = bit0
```

Decode: 2 bits → 4 states. A 74HC139 (dual 2-to-4) decodes both SOURCE and DEST fields. **1 chip.**

### All instructions verified:

| Instruction | Steps | Microcode bytes |
|---|:---:|---|
| **LI rd, imm** | 3 | `$19` = SRC=none, DST=reg(rd), ALU_L, END |
| | | (ALU: 0+OPR=OPR, latch, write rd, end) |
| **ADDI rd, imm** | 3 | `$5D` = SRC=reg(rd), DST=reg(rd), ALU_L, FLAGS, END |
| | | (rd→ALU_A, OPR→ALU_B, compute, result→rd) |
| **ADD rd, rs** | 4 | step2: `$62` = SRC=reg(rs), DST=ALU_B, SEL=rs |
| | | step3: `$5D` = SRC=reg(rd), DST=reg(rd), ALU_L, FLAGS, END |
| **LB rd,[imm]** | 4 | step2: addr setup (needs ADDR_CLK!) |
| | | step3: `$91` = SRC=mem, DST=reg(rd), END |
| **BEQ** | 4 | step2: `$62` = load rs→ALU_B |
| | | step3: `$44+flag` = SRC=reg(rd), ALU_L, FLAGS (compare) |
| | | step4: `$01` or PC_LOAD+END |

### Problem: Missing signals

We're still missing:
- **ADDR_CLK** (latch address for memory ops)
- **PC_LOAD** (branch/jump)
- **ADDR_HI** (16-bit address high byte)
- **PC_SAVE** (JAL: rd ← PC)

These are rare operations. Can we overload?

**PC_LOAD**: Only happens with END. Encode as: `SRC=11(ALU) + DST=00(none) + END = PC_LOAD`. 
When ALU_result is source but destination is "none" and END is set → means jump.
Decode: if SRC=ALU AND DST=none AND END → PC_LOAD. One AND gate.

**ADDR_CLK**: Use DST=11 without actually writing to memory? No, that fires BUF_DIR.
Alternative: ADDR_CLK is always active during any step where DST=10 or DST=11 in memory mode.
Actually simpler: **address latch = OPR value (hardwired)**. For zero-page loads, addr = {$00, OPR}. Always. No ADDR_CLK needed for simple cases.

For LB rd, off(rs): addr = rs + off5. Need ALU to compute it, then latch.
Solution: step 2 loads rs into ALU_B. step 3 computes addr (ALU_A=off5→ how?). 
Actually: step 2 reads rs→IBUS→ALU_B. Step 3: compute rs+OPR... but OPR has both rs field AND off5.

This is getting complex. For the **simple zero-page** load/store: hardwire address = {$00, OPR}. Whenever MEM mode is active, address bus = {$00, OPR}. This covers LB/SB zero-page.

For **offset addressing** (LB rd, off(rs)): need multi-step address computation. Use ALU to compute rs+off → put result somewhere that drives address bus.

**ADDR from ALU**: Add hardware path: ALU_result → address_latch. Activated by: `SRC=ALU + DST=none + ALU_LATCH`? Or a dedicated bit.

OK. I think the **honest answer** is:

## Verdict on 8-bit microcode for RV8

It's **possible** but requires:
1. A 74HC139 for source/dest decode (+1 chip)
2. Hardwired fetch (saves needing fetch in microcode)
3. ALU op hardwired from opcode[5:3] (saves ALU mode bits)
4. Compromises on complex addressing modes (offset addressing needs extra steps)
5. Some signal overloading decoded by extra gates

**Net result:**
- Saves 1 ROM chip (1× AT28C256 instead of 2)
- Adds 1× 74HC139 decode chip
- **Same total chip count!** (27+1 ROM vs 27+2 ROMs → saves 1 package)
- Adds ~1 cycle to memory addressing instructions
- More complex microcode development

**Is it worth it?** Barely. You save 1 chip but add complexity.
