# RV8-R FullHW Task Plan

This is the working task list for RV8-R FullHW after the hardware-path update.
FullHW means the old 19-chip reduced sketch is no longer the build target. The
current target is 49 logic chips plus 2 microcode ROMs, 1 program ROM, and 1
RAM package, for 53 total packages.

## Current Status

| Area | Status | Notes |
|------|--------|-------|
| Architecture docs | Done | FullHW paths are defined in `00_design.md` and `02_wiring_guide.md` |
| ISA encoding docs | Done | Fast page is `$FF00+imm8`; registers are `$FFF8-$FFFF` |
| Legacy trace | Done | `01_instruction_trace.md` is marked as legacy 19-chip history |
| Control word | Done | Frozen 16-bit direct-control contract is in `00_design.md` and mirrored in `02_wiring_guide.md` |
| Microcode generator | Pending | Existing generator is legacy 14-bit prototype |
| RTL | Pending | Existing RTL is old-map behavioral proof, not FullHW |
| Tests | Pending | Need FullHW ISA and bus-path tests |
| KiCad | Pending | Need convert FullHW paths into sheets and run ERC |
| Programmer audit | Pending | Need confirm RV8-Bus pin behavior for RV8-R FullHW |

## Task Order

### 1. Freeze FullHW Control Word - Done

**Goal:** Turn the FullHW direct-control description into one exact 16-bit
control word contract.

**Files:**
- `doc/00_design.md`
- `doc/02_wiring_guide.md`
- `tools/microcode_gen.py`

**Work:**
- Assign every control bit by name.
- Define active-high versus active-low polarity.
- Define legal bus-owner combinations.
- Define `ADDR_SRC[1:0]`, `ALU_SEL[1:0]`, `REG_SEL`, `SYS_*`, `IRQ_ACK`, `STEP_RST`.
- Add a bus-owner table for each micro-step type.

**Pass condition:**
- Every FullHW control signal in the wiring guide has a control-word source.
- No signal is still described as conceptual or implied.

**Result:** Done. The frozen ROM output bits are:
`BUF_OE_n`, `BUF_DIR`, `OPR_OE_n`, `ALUR_OE_n`, `ALUB_CLK`,
`ALUR_CLK`, `FLAGS_CLK`, `RAM_WE_n`, `PC_INC`, `PC_LOAD_n`,
`AR_LO_CLK`, `AR_HI_CLK`, `ADDR_SRC[1:0]`, and `ALU_SEL[1:0]`.
The default safe word is `0x028D`. Fetch clocks, memory strobes,
`STEP_RST`, SYS controls, helper IBUS drivers, and `REG_SEL` are defined as
deterministic decode rather than extra ROM bits.

### 2. Write FullHW Microcode Generator

**Goal:** Replace the old 14-bit prototype output with a FullHW generator.

**Files:**
- `tools/microcode_gen.py`
- generated `tools/microcode.hex`
- optional `tools/microcode_fullhw.hex` if keeping the legacy file for comparison

**Work:**
- Address format: `{IRQ_ACTIVE,C,Z,step[3:0],opcode[7:0]}`.
- Output width: 16-bit direct-control word.
- Emit default safe control word with no bus drivers and no writes.
- Generate fetch, ALU, load/store, branch, stack, SYS, IRQ, and IRET sequences.
- Fail loudly if an instruction needs more than 16 steps.

**Pass condition:**
- Generator exits nonzero on duplicate or invalid control states.
- It prints a coverage summary for all 256 opcodes.
- It writes deterministic output.

### 3. Migrate RTL To FullHW Map

**Goal:** Update behavioral RTL to match the frozen FullHW memory/control model.

**Files:**
- `rtl/rv8r_cpu.v`
- `tb/tb_rv8r.v`

**Work:**
- Reset PC to `$0000`.
- Program ROM range `$0000-$7FFF`.
- RAM range `$8000-$FFFF`.
- Registers at `$FFF8-$FFFF`.
- Fast page at `$FF00+imm8`.
- IRQ vector `$7F00`.
- IRQ saved PC at `$FFF6/$FFF7`.
- `IRET` restores from `$FFF6/$FFF7`.

**Pass condition:**
- Testbench fails the shell process on mismatch.
- Testbench proves reset fetches ROM at `$0000`.
- Testbench proves IRQ vector and return use the frozen map.

### 4. Add Full ISA Simulation Tests

**Goal:** Prove the RV8-R FullHW programmer surface before KiCad work.

**Test groups:**
- ALU: `ADD`, `SUB`, `AND`, `OR`, `XOR`, `SLL`, `SLT`.
- Immediate: `LI`, `ADDI`, `SUBI`, `ANDI`, `ORI`, `XORI`, `SLTI`, `LUI` assembler behavior.
- Memory: `LB/SB off(rs)`, `LBfp/SBfp`, `LBsp/SBsp`.
- Stack: `PUSH`, `POP`, SP returns to original value.
- Control: `BEQ`, `BNE`, `BLT`, `BGE`, `J`, `JAL`, `JALR`.
- System: `NOP`, `HLT`, `EI`, `DI`, `IRET`.
- IRQ: pending latch, vector, saved PC, return, re-enable.

**Pass condition:**
- Tests assert exact register, RAM, PC, flags, halt, and IRQ state.
- No test may pass by only printing `PASS`.

### 5. Build FullHW KiCad Module Split

**Goal:** Convert `02_wiring_guide.md` into schematic modules.

**Suggested sheets:**
- `CLK_RST_HALT`
- `PC_ABUS`
- `IR_MICROCODE`
- `IBUS_DBUS_MEMORY`
- `ALU_FLAGS`
- `ADDRESS_SOURCE`
- `REG_STACK_FASTPAGE`
- `IRQ_SYS`

**Pass condition:**
- Every FullHW chip in the wiring guide appears in exactly one sheet.
- Every shared bus has one owner table.
- ERC passes or each ERC warning is documented.

### 6. Programmer And RV8-Bus Audit

**Goal:** Decide whether the existing Programmer can safely program RV8-R FullHW.

**Work:**
- Verify RV8-Bus pins against RV8-R FullHW ABUS/DBUS/control pins.
- Confirm reset releases CPU drivers during programming.
- Confirm ROM `/WE`, `/OE`, and `/CE` behavior.
- Document whether in-system programming is supported or ROM must be removed.

**Pass condition:**
- `Programmer/README.md` or RV8-R docs say exactly which programming path is safe.

### 7. Student/Teacher Build Decision

**Goal:** Decide whether RV8-R FullHW is a teaching build or an advanced reference.

**Work:**
- Compare FullHW 53-package complexity against RV8GR-V2 35-package student baseline.
- If FullHW remains advanced, document it as a teacher/reference path.
- If building FullHW physically, create a staged build plan with manual-clock tests.

**Pass condition:**
- README clearly routes middle-school students to RV8GR-V2 unless the teacher deliberately chooses FullHW as an advanced build.

## Immediate Next Task

Start with **Task 2: Write FullHW Microcode Generator**. Replace the legacy
14-bit group-encoded prototype with a 15-bit address, 16-bit output generator
that emits `0x028D` as the safe default and rejects illegal bus-owner
combinations before writing ROM output.
