# RV8-R — Legacy 19-Chip Instruction Trace

**Legacy trace for `ADDI r1, 5`. The current buildable full-ISA hardware target is FullHW in `02_wiring_guide.md`; this file is retained to explain why the old 19-chip idea was not enough.**

---

## RV8-R = RV8 minus hardware registers

RV8 has: 8× 574 (registers) + 2× 138 (decode) = 10 chips for register file.
RV8-R removes these. Registers live in high RAM at `$FFF8-$FFFF`.

**But**: RV8's microcode sequences assume registers are on IBUS (instant /OE access). With RAM registers, reading a register requires a full RAM access cycle (set address, read, latch).

---

## RV8-R Chip List (early 17-chip claim):

| U# | Chip | Function |
|:--:|------|----------|
| U1-U2 | 74HC574 ×2 | IR (opcode + operand) |
| U3 | 74HC574 | ALU B latch |
| U4-U5 | 74HC283 ×2 | ALU adder |
| U6-U7 | 74HC86 ×2 | XOR (SUB) |
| U8-U9 | 74HC574 ×2 | PC (low + high, /OE) |
| U10-U11 | 74HC574 ×2 | Address latches (low + high) |
| U12 | 74HC245 | Bus buffer (IBUS ↔ RAM) |
| U13 | SST39SF010A | Microcode Flash #1 |
| U14 | 74HC74 | Flags (Z, C) |
| U15 | 74HC574 | ALU result latch |
| U16 | 74HC161 | Step counter |
| U17 | SST39SF010A | Microcode Flash #2 |
| U22 | 74HC74 | IRQ state (IE + IRQ_PENDING) |
| — | AT28C256 | Program ROM |
| — | 62256 | RAM (registers at $FFF8-$FFFF) |

**PC warning:** this early trace still shows the old `U8-U9` 74HC574 PC sketch.
The architecture table now targets a 16-bit `74HC161` counter PC, while the
wiring guide marks the PC implementation as a blocker until one pinout is
chosen and proven.

---

## Trace: `ADDI r1, 5` (r1 = r1 + 5)

r1 lives at RAM[$FFF9]. Current value: $10. Expected result: $15.

### Step 0: Fetch opcode

```
Microcode outputs: PC_ADDR=1, BUF_OE=1, BUF_DIR=0, IR_CLK=1, PC_INC=1
PC ($0000) → address bus → ROM → D[7:0] = opcode → U12 (245) → IBUS → U1 (IR) latches
PC increments to $0001.
```

**Check**: PC (U8-U9, 574 with /OE) drives address bus. /OE=LOW (PC_ADDR=1). ✅
Buffer (U12) enabled, direction=read. ✅
IR (U1) CLK pulses. ✅

### Step 1: Fetch operand

```
Same as step 0 but OPR_CLK instead of IR_CLK.
PC ($0001) → ROM → $05 → IBUS → U2 (operand) latches.
PC increments to $0002.
```
✅ No issues.

### Step 2: Read register r1 from RAM

```
Need: RAM[$FFF9] → IBUS → ALU B latch

Microcode outputs: PC_ADDR=0, ADDR_CLK=1, BUF_OE=1, BUF_DIR=0
```

**Wait**: To read RAM[$FFF9], need address `$FFF8 + rd` on the address bus. Where does that come from?

In RV8 (hardware registers): microcode enables register /OE → value on IBUS instantly.
In RV8-R (RAM registers): must put `$FFF8 + reg_id` on address bus, then read RAM.

**How to put `$FFF9` on address bus:**
- Address latches (U10-U11) drive address bus when PC disconnects.
- But address latches get their value from IBUS.
- IBUS currently has... nothing (buffer not yet enabled for this address).

**Need to put register address `$FFF8 + rd` onto address bus.** Where does the low register number come from?

From the **opcode**: `rd` field = opcode[2:0] = register number. This is in U1 (IR opcode) Q outputs.

**But**: IR Q outputs go to Flash address pins (for microcode lookup). They don't go to IBUS or address bus!

**Problem**: Register address (from opcode rd field) needs to reach the address bus. In RV8, this went to the 138 decoder. In RV8-R, it needs to become the low 3 bits of `$FFF8 + rd`.

**Path needed**: IR opcode[2:0] → somehow → address bus A[2:0] with A[15:3] forced to 1.

**Options**:
1. Wire IR opcode[2:0] directly to address latch D inputs (hardwired, always) — but address latches also need IBUS data for memory access addresses!
2. Put register address on IBUS first, then latch into address register — but how does 3-bit rd field get onto 8-bit IBUS?
3. Use operand byte as register address — operand[7:5] = rs field. This IS on IBUS (from U2 outputs)!

**Option 3 works for rs (source register)**! The operand byte contains rs[7:5]. Microcode can:
- Step 2a: Enable U2 (operand) /OE → IBUS = operand byte → address latch captures
- Step 2b: But address latch gets the FULL operand byte, not just rs field...

For `ADDI r1, 5`: operand = $05 (immediate value). There's no rs field — it's all immediate!

**For ADDI**: the destination register (rd) comes from opcode[2:0]. The value to add is the operand. We need to:
1. Read RAM[rd] (current r1 value)
2. Add operand (5)
3. Write result back to RAM[rd]

**Step 2 needs rd on address bus.** rd = opcode[2:0] = 3 bits. These are in U1 Q outputs (pins 12-14).

**Fix**: In register-address mode, wire U1.Q[2:0] (opcode rd field) to address low bits A[2:0], force A[7:3]=11111, and force address high byte A[15:8]=$FF.

**But**: Address latch D inputs also need IBUS data (for LB/SB with computed addresses). Can't hardwire them to opcode bits!

**Need a MUX / force network** on address inputs: select between normal memory address and `{13'b1111111111111, reg[2:0]}` for register access.

**+1× 74HC157 (4-bit mux) for address low D-input select.** Or use the existing address latch differently.

**Actually**: Simpler approach. Microcode can sequence:
1. Put $00 on IBUS (how? ALU: 0+0=0, latch result, put on IBUS... complex)
2. Put rd on IBUS (how? opcode bits aren't on IBUS!)

**The fundamental problem**: In RV8-R, the register address (from opcode) has no path to the address bus without extra routing.

---

## Issue found: Register address routing

In RV8: opcode[2:0] → 138 decoder → register /OE. Direct, simple.
In RV8-R: opcode[2:0] needs to reach address bus A[2:0]. No direct path exists.

**Fix options**:
1. Use the existing address-mux budget to select normal address vs forced register address `$FFF8+reg`.
2. Wire opcode[2:0] into the low address mux and force A[15:3]=1 during register access.
3. If pin-level proof shows the force network cannot fit cleanly, add one small mux/buffer chip and update the count.

**Legacy conclusion**: the old 19-chip target tried to keep register address generation inside the existing address mux/force budget. FullHW replaces this with a real full address-source mux.

**Intermediate legacy revision for register access: 18 chips before adding IRQ state.**

The later IRQ-capable RV8-R target adds one more `74HC74` package for `IE` and
`IRQ_PENDING`, so the old reduced target was **19 logic chips + ROM + RAM = 22
packages**. This is no longer the buildable full-ISA target.

---

## Continue trace with fix:

### Step 2: Set register address

```
Microcode: REG_ADDR_MODE=1 (address force network selects $FFF8 + rd)
           ADDR_CLK=1 (latch captures low byte $F9 for r1)
           ADDR_HI_CLK=1 (latch captures $FF)
```

Address latch low = $F9. Address latch high = $FF. ✅

### Step 3: Read register from RAM

```
Microcode: PC_ADDR=0 (PC disconnects, addr latches drive)
           BUF_OE=1, BUF_DIR=0 (read RAM → IBUS)
           ALUB_CLK=1 (latch RAM data into ALU B)
```

RAM[$FFF9] = $10 → D[7:0] → U12 (245) → IBUS = $10 → U3 (ALU B latch) captures $10. ✅

### Step 4: Load operand into... wait

For ADDI, ALU B should be the IMMEDIATE value ($05), not the register value ($10)!

The register value ($10) should be ALU A. But ALU A comes from IBUS (in RV8's design, ALU A = register output on IBUS).

**In RV8-R**: We just read the register onto IBUS. ALU A input comes from IBUS. But we latched it into ALU B (U3)!

**Fix the sequence**:
- Step 3: Read RAM[r1] → IBUS → this IS ALU A (IBUS feeds adder A inputs directly? Or needs latch?)

**Check RV8 design**: In RV8, ALU A = IBUS (the selected register drives IBUS, adder A reads from IBUS). ALU B = from ALU B latch (U3, loaded separately).

So for ADDI:
- Step 2-3: Read RAM[r1] → IBUS (this feeds adder A directly)
- Step 3: Simultaneously, operand ($05) needs to be in ALU B latch

**But**: ALU B latch was loaded WHEN? It needs the operand value. The operand is in U2 (IR operand register). Microcode can enable U2 /OE → IBUS → ALU B latch. But that conflicts with RAM data on IBUS!

**Can't have both register value AND operand on IBUS simultaneously.**

**Solution**: Two separate steps:
- Step 2: Load operand → ALU B latch (U2 drives IBUS → U3 latches)
- Step 3: Read RAM[r1] → IBUS → adder A reads it → compute → latch result

**This works!** Adder A reads from IBUS (which has RAM[r1] value). Adder B reads from U3 latch (which has operand $05). Result = $10 + $05 = $15. ✅

### Step 4: Compute and latch result

```
Microcode: ALUR_CLK=1 (latch adder output into U15)
           FLAGS_CLK=1 (update Z, C)
```

ALU result = $15 → U15 latches. ✅

### Step 5: Write result back to RAM[r1]

```
Microcode: PC_ADDR=0, REG_ADDR_MODE=1 (address = $FFF9 again)
           Need result ($15) on IBUS → RAM write

But U15 (result latch) needs to drive IBUS. Does it have /OE?
```

U15 is 74HC574. /OE pin exists! If /OE=LOW, Q outputs drive IBUS. ✅

```
Microcode: ALUR_OE=1 (U15 drives IBUS with $15)
           BUF_OE=1, BUF_DIR=1 (write IBUS → RAM)
           RAM /WE pulse
```

RAM[$FFF9] = $15. ✅

### Step 6: Done

```
Microcode: STEP_RST=1 (reset step counter, back to fetch)
```

---

## Total steps: 7 (fetch 2 + load_B 1 + read_reg 1 + compute 1 + write_reg 1 + end 1)

At 5 MHz: 7 steps = ~0.71 MIPS.

---

## Issues found:

| Issue | Fix | Extra chips |
|-------|-----|:-----------:|
| Register address (`$FFF8+reg`) needs path to address bus | address mux/force network | target included |
| IRQ state (`IE`, `IRQ_PENDING`) | +1× 74HC74 | +1 |
| **Total** | | **19 logic chips** |

---

## Legacy Reduced RV8-R: 19 logic chips + ROM + RAM = 22 packages

| Claimed | Honest | Difference |
|:-------:|:------:|:----------:|
| 17 | **19** | +1 register address mux, +1 IRQ latch |

The original 17-chip sketch missed the register-address route. The IRQ-capable
version also needs the second `74HC74` package for interrupt enable and pending
state.

---

## Verified paths:

| Path | Works? |
|------|:------:|
| PC → address bus → ROM → buffer → IBUS → IR | ✅ |
| Operand (U2) → IBUS → ALU B latch | ✅ |
| Register address (`$FFF8+reg`) → addr latch/address force network → address bus | ⚠️ concept frozen, pin-level proof pending |
| RAM[reg] → buffer → IBUS → adder A | ✅ |
| Adder result → result latch → IBUS → buffer → RAM[reg] | ✅ |
| PC disconnect (/OE) during RAM access | ✅ |
| Step counter sequences all steps | ✅ |
| IRQ latch (`IE` + `IRQ_PENDING`) → microcode address A13 | ✅ in behavioral RTL; pin-level proof pending |
