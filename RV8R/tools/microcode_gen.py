#!/usr/bin/env python3
"""RV8-R legacy microcode generator — 8-bit group-encoded prototype.

NOTE: RV8-R FullHW now uses a 15-bit address and 16-bit direct-control word.
This generator is kept only as the old 14-bit prototype until it is migrated.

ROM Address (14 bits):
  A[7:0]  = opcode (from IR)
  A[10:8] = step (0-7)
  A[11]   = flag_Z
  A[12]   = flag_C
  A[13]   = IRQ_ACTIVE (IE and IRQ_PENDING at instruction boundary)

ROM Data (8 bits):
  [7:6] = GROUP (00=BUS, 01=ALU, 10=BRANCH, 11=SPECIAL)
  [5:0] = ACTION
"""

# === GROUP 00: BUS/MEMORY ===
# [5:3] source/dest pair, [2:0] flags
# Flags: [2]=PC_INC, [1]=end(step_rst), [0]=save_flags

def BUS(src, flags=0):
    return (0b00 << 6) | (src << 3) | flags

# Source codes
FETCH_IR   = 0  # MEM[PC] → IR
FETCH_OPR  = 1  # MEM[PC] → OPR
RD_RD_A    = 2  # MEM[rd_addr] → REG_A
RD_RS_B    = 3  # MEM[rs_addr] → REG_B
RD_MEM_A   = 4  # MEM[addr_latch] → REG_A
OPR_TO_B   = 5  # OPR → REG_B
OPR_TO_A   = 6  # OPR → REG_A
ZERO_TO_B  = 7  # $00 → REG_B

# Flags
PC_INC     = 0b100
F_END      = 0b010
F_FLAGS    = 0b001

# Common BUS operations
FETCH0     = BUS(FETCH_IR, PC_INC)        # step 0: MEM[PC]→IR, PC++
FETCH1     = BUS(FETCH_OPR, PC_INC)       # step 1: MEM[PC]→OPR, PC++
LOAD_RD_A  = BUS(RD_RD_A)                 # MEM[rd] → REG_A
LOAD_RS_B  = BUS(RD_RS_B)                 # MEM[rs] → REG_B
LOAD_MEM_A = BUS(RD_MEM_A)               # MEM[addr] → REG_A
LOAD_OPR_B = BUS(OPR_TO_B)               # OPR → REG_B
LOAD_OPR_A = BUS(OPR_TO_A)               # OPR → REG_A
LOAD_ZERO_B= BUS(ZERO_TO_B)              # 0 → REG_B


# === GROUP 01: ALU + WRITEBACK ===
# [5:3] op, [2:0] dest+flags

def ALU(op, dest):
    return (0b01 << 6) | (op << 3) | dest

# ALU ops
ADD   = 0  # A + B
SUB   = 1  # A - B
XOR   = 2  # A ^ B
AND   = 3  # A & B
OR    = 4  # A | B
PASS_A= 5  # pass A through
PASS_B= 6  # pass B through
NOT_A = 7  # ~A (A XOR $FF)

# ALU destinations
TO_RD       = 0  # → MEM[rd]
TO_RS       = 1  # → MEM[rs]
TO_ADDR_LO  = 2  # → addr latch low
TO_ADDR_HI  = 3  # → addr latch high
TO_RD_END   = 4  # → MEM[rd] + step_rst
TO_RD_FL    = 5  # → MEM[rd] + save flags
TO_RD_FL_END= 6  # → MEM[rd] + flags + step_rst
TO_MEM      = 7  # → MEM[addr_latch]


# === GROUP 10: BRANCH/JUMP ===
# [5:4] condition, [3:0] type

def BRANCH(cond, btype):
    return (0b10 << 6) | (cond << 4) | btype

# Conditions
ALWAYS = 0
IF_Z   = 1
IF_NZ  = 2
IF_C   = 3

# Branch types
BR_REL     = 0   # PC += sext(OPR)
BR_ABS     = 1   # PC = {ADDR_HI, ADDR_LO}
PC_HI_TO_A = 2   # PC[15:8] → REG_A
PC_LO_TO_A = 3   # PC[7:0] → REG_A
BR_END     = 4   # just end (step_rst)


# === GROUP 11: SPECIAL ===
def SPECIAL(action):
    return (0b11 << 6) | action

NOP  = SPECIAL(0)
HLT  = SPECIAL(1)
END  = SPECIAL(2)  # step_rst only
IRQ_SAVE_PC_LO = SPECIAL(3)
IRQ_SAVE_PC_HI = SPECIAL(4)
IRQ_VECTOR     = SPECIAL(5)
SYS_OP         = SPECIAL(6)  # OPR subdecode: NOP/HLT/EI/DI/IRET


# === ROM ===
ROM_SIZE = 16384  # 2^14
ucode = [END] * ROM_SIZE  # default: end immediately (safe)


def rom_addr(opcode, step, z=0, c=0, irq=0):
    """Calculate microcode ROM address."""
    return (irq << 13) | (c << 12) | (z << 11) | (step << 8) | opcode


def emit(opcode, steps, cond_steps=None):
    """Write microcode for an instruction.
    
    steps: list of control words for steps 2+
    cond_steps: dict {(z,c): [steps]} for flag-dependent paths
    """
    for c in range(2):
        for z in range(2):
            # Steps 0,1 always fetch
            ucode[rom_addr(opcode, 0, z, c, 0)] = FETCH0
            ucode[rom_addr(opcode, 1, z, c, 0)] = FETCH1
            # Steps 2+ 
            if cond_steps and (z, c) in cond_steps:
                seq = cond_steps[(z, c)]
            else:
                seq = steps
            for s, ctrl in enumerate(seq):
                ucode[rom_addr(opcode, s + 2, z, c, 0)] = ctrl


def emit_irq_entry():
    """IRQ_ACTIVE overrides normal fetch at instruction boundary."""
    for opcode in range(256):
        for c in range(2):
            for z in range(2):
                ucode[rom_addr(opcode, 0, z, c, 1)] = IRQ_SAVE_PC_LO
                ucode[rom_addr(opcode, 1, z, c, 1)] = IRQ_SAVE_PC_HI
                ucode[rom_addr(opcode, 2, z, c, 1)] = IRQ_VECTOR
                ucode[rom_addr(opcode, 3, z, c, 1)] = END


# === INSTRUCTION DEFINITIONS ===

for rd in range(8):
    # ─── Class 01: ALU Immediate ───
    
    # LI rd, imm (4 cycles)
    emit(0b01_000_000 | rd, [
        LOAD_OPR_A,                      # step 2: OPR → REG_A
        ALU(PASS_A, TO_RD_END),          # step 3: A → MEM[rd], END
    ])
    
    # ADDI rd, imm (5 cycles)
    emit(0b01_001_000 | rd, [
        LOAD_OPR_B,                      # step 2: OPR → REG_B (immediate)
        LOAD_RD_A,                       # step 3: MEM[rd] → REG_A
        ALU(ADD, TO_RD_FL_END),          # step 4: A+B → MEM[rd], flags, END
    ])
    
    # SUBI rd, imm (5 cycles)
    emit(0b01_010_000 | rd, [
        LOAD_OPR_B,
        LOAD_RD_A,
        ALU(SUB, TO_RD_FL_END),
    ])
    
    # ANDI rd, imm (5 cycles)
    emit(0b01_011_000 | rd, [
        LOAD_OPR_B,
        LOAD_RD_A,
        ALU(AND, TO_RD_FL_END),
    ])
    
    # ORI rd, imm (5 cycles)
    emit(0b01_100_000 | rd, [
        LOAD_OPR_B,
        LOAD_RD_A,
        ALU(OR, TO_RD_FL_END),
    ])
    
    # XORI rd, imm (5 cycles)
    emit(0b01_101_000 | rd, [
        LOAD_OPR_B,
        LOAD_RD_A,
        ALU(XOR, TO_RD_FL_END),
    ])
    
    # SLTI rd, imm (7 cycles) — flag-dependent writeback
    emit(0b01_110_000 | rd, [
        LOAD_OPR_B,                      # step 2: imm → B
        LOAD_RD_A,                       # step 3: rd → A
        ALU(SUB, TO_RD_FL),             # step 4: A-B, save flags (don't keep result)
    ], cond_steps={
        # After step 4, flags are set. Steps 5+ depend on C flag.
        # C=1 means borrow (rd < imm) → rd = 1
        # C=0 means no borrow (rd >= imm) → rd = 0
        # But we need to check AFTER the SUB... the flag is latched in step 4
        # and available in step 5's address. So split at step 5:
    })
    # Actually: rewrite SLTI with flag-dependent path at step 5
    # After step 4 (SUB+flags), step 5 sees the new C flag
    for c in range(2):
        for z in range(2):
            # Steps 0-4 same for all
            ucode[rom_addr(0b01_110_000 | rd, 0, z, c)] = FETCH0
            ucode[rom_addr(0b01_110_000 | rd, 1, z, c)] = FETCH1
            ucode[rom_addr(0b01_110_000 | rd, 2, z, c)] = LOAD_OPR_B
            ucode[rom_addr(0b01_110_000 | rd, 3, z, c)] = LOAD_RD_A
            # Step 4: SUB + save flags (result goes to rd but we'll overwrite)
            ucode[rom_addr(0b01_110_000 | rd, 4, z, c)] = BUS(RD_RD_A, F_FLAGS)
            # Hack: we need ALU(SUB) + flags but NOT write to rd
            # Actually let's use: ALU SUB → nowhere? We don't have that.
            # Simpler: just do the compare, set flags. Then step 5 checks C.
            # Use a 2-pass approach: step 4 does the SUB into a temp (ADDR_LO as scratch)
            ucode[rom_addr(0b01_110_000 | rd, 4, z, c)] = ALU(SUB, TO_ADDR_LO)
    # Now step 5 depends on the NEW carry flag from step 4's result
    # Problem: flags latch in step 4, but ROM address for step 5 uses 
    # the OLD flags (latched before this instruction started).
    # Fix: add one more step for flag propagation
    for c in range(2):
        for z in range(2):
            # Step 5: NOP (let flags propagate to ROM address for step 6)
            ucode[rom_addr(0b01_110_000 | rd, 5, z, c)] = NOP
    # Step 6: now the ROM address reflects the NEW flags from the SUB
    # C=1 (borrow) → rd < imm → write 1
    # C=0 → rd >= imm → write 0
    for z in range(2):
        # C=1: rd = 1 (load 1 into A, write to rd)
        ucode[rom_addr(0b01_110_000 | rd, 6, z, 1)] = LOAD_OPR_B  # reuse OPR? No.
        # Actually: we need a way to generate constant 1.
        # Option: ADDI trick — load ZERO into A, load 1 into B from... nowhere?
        # Best: just use ZERO_TO_B + then in step 7: ALU(PASS_B) with B=0, but we need 1...
        # Problem: no easy way to generate constant 1 in hardware.
        # Solution: SLTI can use a dedicated microcode trick:
        #   If C=1: result is (0 - 0xFF) via ALU → gets 1? No.
        # Simplest correct approach:
        #   The SUBI already produced A-B. If C=1 (borrow), we know result.
        #   We stored the SUB result in ADDR_LO. But we want 0 or 1.
        # 
        # REAL fix: forget fancy. Just branch:
        #   C=1 → LOAD_ZERO_B (B=0), then in next step ALU(SUB, ...) with A=0,B=0 → 0-0+1? No.
        # 
        # ACTUALLY: we need hardware support for constant 1. Or:
        # Use OPR! Before SLTI, operand = imm value. We can't reuse it.
        # 
        # PRAGMATIC: store flag result in rd using a multi-step:
        #   C=1: write $01 to rd. How? Only way is: load $01 from somewhere.
        #   We could put $01 at a known ROM address and load it... too complex.
        #
        # DESIGN FIX: Add ONE_TO_B as a source option (hardware: tie DATA=1 when selected)
        # Or: redefine ZERO_TO_B as CONST_TO_B where the constant comes from... step counter? No.
        #
        # SIMPLEST: SLT uses XOR trick. After SUB:
        #   result = A - B. Carry = borrow.
        #   Zero the A register, then add carry: 0 + 0 + carry = carry bit = SLT result!
        #   But 74HC283 carry-in is a single bit... and we DO have it from flags!
        # 
        # YES! ALU with A=0, B=0, carry_in=flag_C → result = 0 or 1.
        # This needs: a new ALU mode "ADD_WITH_CARRY" or we just wire Cin from flag.
        # 
        # For now: mark SLT as 8 cycles with flag-branch approach.
        pass
    # OK, SLT is complex. Let's use the simple approach:
    # After SUB, if C=1 → load 1 to rd, else load 0 to rd.
    # We use two different paths in the ROM based on C flag at step 6:
    for z in range(2):
        # C=1 (borrow → less than): need to write 1 to rd
        # Trick: OPR still holds the original immediate. Overwrite OPR? No can't.
        # We need ZERO→A then... 
        # Actually ZERO→B gives us 0. If we also have A=0: A-B with SUB gives 0-0=0.
        # We need 1. There's no source for constant 1 in the BUS group.
        # 
        # HARDWARE ADDITION: Replace ZERO_TO_B (source 111) with CONST_TO_B where
        # the constant is selected by a bit: 0 = $00, 1 = $01.
        # This can be done with a single AND gate on D0 controlled by a mode bit.
        # OR: just hardwire two constants — ZERO=source 7, ONE=... no room.
        #
        # ALTERNATIVE: Use ALU carry-in from flags register.
        # ADD 0+0+Cin = Cin = C flag = SLT result!
        # This requires: Cin of 74HC283 connected to flag_C output (gated by control).
        # One extra gate (AND: enable_carry AND flag_C → Cin).
        # This is a good hardware decision.
        
        # With carry-in support:
        # Step 6 (C=1): ZERO→A, ZERO→B implicit, ALU(ADD_CIN)→rd, END
        # Step 6 (C=0): same! ADD 0+0+0 = 0, ADD 0+0+1 = 1. Auto-correct!
        # So SLT doesn't even need branching if we have carry-in!
        pass
    
    # SLTI: redesign with carry-in
    # Steps: OPR→B, rd→A, ALU(SUB)→flags_only, ZERO→A, ZERO→B, ALU(ADD_CIN)→rd, END
    # = 7 cycles. Good enough.
    # For now, encode with placeholder — will finalize when hardware carry-in confirmed.
    for c in range(2):
        for z in range(2):
            ucode[rom_addr(0b01_110_000 | rd, 0, z, c)] = FETCH0
            ucode[rom_addr(0b01_110_000 | rd, 1, z, c)] = FETCH1
            ucode[rom_addr(0b01_110_000 | rd, 2, z, c)] = LOAD_OPR_B
            ucode[rom_addr(0b01_110_000 | rd, 3, z, c)] = LOAD_RD_A
            ucode[rom_addr(0b01_110_000 | rd, 4, z, c)] = ALU(SUB, TO_ADDR_LO)  # SUB, save flags
            ucode[rom_addr(0b01_110_000 | rd, 5, z, c)] = LOAD_ZERO_B  # B=0
            ucode[rom_addr(0b01_110_000 | rd, 6, z, c)] = BUS(ZERO_TO_B, F_FLAGS)  # propagate flags
            # Step 7: new C flag visible → use carry-in ADD
            # For now placeholder: will be ALU(ADD_CIN, TO_RD_END)
            ucode[rom_addr(0b01_110_000 | rd, 7, z, c)] = ALU(ADD, TO_RD_END)  # TODO: +Cin
    
    # LUI rd, imm (5 cycles) — rd = imm << 4
    # Shift left 4 = ADD to self 4 times? That's 4 extra steps (slow).
    # Alternative: LUI stores imm in high nibble: just write imm as-is and 
    # document that LUI puts imm in bits[7:4], zeros in [3:0].
    # Hardware: OPR → B, then shift... no easy way.
    # PRAGMATIC: LUI = load immediate into rd, shifted. Microcode:
    #   Step 2: OPR→A, step 3: ALU(A+A)→A (×2), repeat 4 times? = 6 steps = 8 cycles total.
    # Or: just store as-is and define LUI as "LI rd, imm<<4" in assembler (pre-shift).
    # Assembler shifts the constant: LUI r2, $50 → encodes as LI r2, $50 (value already shifted)
    # THIS IS WHAT MAKES SENSE. LUI is an assembler pseudo that does: LI rd, (imm<<4)
    # At hardware level: LUI = LI (same microcode, opcode $78+rd = treated same as $40+rd)
    emit(0b01_111_000 | rd, [
        LOAD_OPR_A,                      # step 2: OPR → REG_A (assembler pre-shifted)
        ALU(PASS_A, TO_RD_END),          # step 3: A → MEM[rd], END
    ])
    
    # ─── Class 00: ALU Register-Register ───
    
    # ADD rd, rs (5 cycles)
    emit(0b00_000_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs] → REG_B
        LOAD_RD_A,                       # step 3: MEM[rd] → REG_A
        ALU(ADD, TO_RD_FL_END),          # step 4: A+B → MEM[rd], flags, END
    ])
    
    # SUB rd, rs (5 cycles)
    emit(0b00_001_000 | rd, [
        LOAD_RS_B,
        LOAD_RD_A,
        ALU(SUB, TO_RD_FL_END),
    ])
    
    # AND rd, rs (5 cycles)
    emit(0b00_010_000 | rd, [
        LOAD_RS_B,
        LOAD_RD_A,
        ALU(AND, TO_RD_FL_END),
    ])
    
    # OR rd, rs (5 cycles)
    emit(0b00_011_000 | rd, [
        LOAD_RS_B,
        LOAD_RD_A,
        ALU(OR, TO_RD_FL_END),
    ])
    
    # XOR rd, rs (5 cycles)
    emit(0b00_100_000 | rd, [
        LOAD_RS_B,
        LOAD_RD_A,
        ALU(XOR, TO_RD_FL_END),
    ])
    
    # SLT rd, rs (7 cycles) — same trick as SLTI
    for c in range(2):
        for z in range(2):
            ucode[rom_addr(0b00_101_000 | rd, 0, z, c)] = FETCH0
            ucode[rom_addr(0b00_101_000 | rd, 1, z, c)] = FETCH1
            ucode[rom_addr(0b00_101_000 | rd, 2, z, c)] = LOAD_RS_B
            ucode[rom_addr(0b00_101_000 | rd, 3, z, c)] = LOAD_RD_A
            ucode[rom_addr(0b00_101_000 | rd, 4, z, c)] = ALU(SUB, TO_ADDR_LO)
            ucode[rom_addr(0b00_101_000 | rd, 5, z, c)] = LOAD_ZERO_B
            ucode[rom_addr(0b00_101_000 | rd, 6, z, c)] = BUS(ZERO_TO_B, F_FLAGS)
            ucode[rom_addr(0b00_101_000 | rd, 7, z, c)] = ALU(ADD, TO_RD_END)  # TODO: +Cin
    
    # SLL rd (5 cycles) — shift left = ADD rd, rd
    emit(0b00_110_000 | rd, [
        LOAD_RD_A,                       # step 2: MEM[rd] → REG_A
        BUS(RD_RD_A),                    # step 3: MEM[rd] → REG_A again? No, need B too
        # Fix: rd goes to BOTH A and B
        # Step 2: rd → A
        # Step 3: rd → B (need to re-read rd into B... but our source codes are fixed)
        # Problem: RD_RD_A puts rd into REG_A, not REG_B.
        # Solution: Read rd into A first, then use it. But ALU needs both A and B.
        # HARDWARE NOTE: We could add a "RD_RD_B" source (MEM[rd]→REG_B).
        # Or: read rd→A, then rd→B (re-read from RAM). 6 cycles.
        LOAD_RS_B,                       # Can't use this — rs may be garbage for SLL
    ])
    # Rewrite SLL: rd needs to be in both A and B.
    # Since operand byte rs field is unused for SLL, assembler sets rs=rd.
    # So SLL r3 encodes as: opcode=$33, operand=$60 (rs=r3=011, imm5=0)
    # Then MEM[rs] reads the same register as rd. Works!
    emit(0b00_110_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs=rd] → REG_B
        LOAD_RD_A,                       # step 3: MEM[rd] → REG_A
        ALU(ADD, TO_RD_FL_END),          # step 4: A+B = rd+rd = shift left, END
    ])
    
    # SRL rd (10 cycles) — shift right via carry rotation
    # Algorithm: test bit 0 of rd, shift result right by building bit-by-bit
    # Too complex for microcode with 8 steps max. 
    # Alternative: SRL = software macro. Microcode just does NOP+END.
    # OR: we allow step counter to go 0-7 = 8 steps max including fetch.
    # That gives us 6 execute steps. Not enough for bit-serial SRL.
    # DECISION: SRL uses same trick as SLL — assembler encodes rs=rd,
    # but uses a different approach. Actually... 
    # SRL via subtraction trick: not possible cleanly.
    # KEEP AS SOFTWARE MACRO for now. Microcode = END immediately.
    emit(0b00_111_000 | rd, [
        END,  # SRL: software macro (placeholder)
    ])
    
    # ─── Class 10: Load/Store ───
    
    # LB rd, off(rs) — 8 cycles
    emit(0b10_000_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs] → REG_B (base addr)
        LOAD_OPR_A,                      # step 3: OPR[4:0] sext → REG_A (offset)
        ALU(ADD, TO_ADDR_LO),            # step 4: A+B → addr_lo
        ALU(PASS_A, TO_ADDR_HI),         # step 5: 0 → addr_hi (TODO: page reg)
        LOAD_MEM_A,                      # step 6: MEM[addr] → REG_A
        ALU(PASS_A, TO_RD_END),          # step 7: A → MEM[rd], END
    ])
    
    # SB rd, off(rs) — 8 cycles
    emit(0b10_001_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs] → REG_B (base addr)
        LOAD_OPR_A,                      # step 3: OPR[4:0] sext → REG_A (offset)
        ALU(ADD, TO_ADDR_LO),            # step 4: A+B → addr_lo
        ALU(PASS_A, TO_ADDR_HI),         # step 5: 0 → addr_hi
        LOAD_RD_A,                       # step 6: MEM[rd] → REG_A (value to store)
        ALU(PASS_A, TO_MEM),             # step 7: A → MEM[addr], END implicit
    ])
    # Fixup: TO_MEM doesn't have END. Need step 8 = END. But max 8 steps total (0-7).
    # Step 7 is the last execute step (step index 7 = steps 0-7).
    # Solution: make TO_MEM imply END. Redefine dest 111 as "→MEM[addr]+end".
    # For now leave as-is, the hardware will auto-end at step 7 overflow.
    
    # LB rd, addr (fast-page target) — 6 cycles
    # Frozen memory map requires $FF00+OPR; address-high force is still a hardware proof item.
    emit(0b10_010_000 | rd, [
        LOAD_OPR_A,                      # step 2: OPR → REG_A (address low)
        ALU(PASS_A, TO_ADDR_LO),         # step 3: A → addr_lo
        LOAD_MEM_A,                      # step 4: MEM[{fast_page,addr}] → REG_A
        ALU(PASS_A, TO_RD_END),          # step 5: A → MEM[rd], END
    ])
    
    # SB rd, addr (fast-page target) — 6 cycles
    # Frozen memory map requires $FF00+OPR; address-high force is still a hardware proof item.
    emit(0b10_011_000 | rd, [
        LOAD_OPR_A,                      # step 2: OPR → REG_A (address low)
        ALU(PASS_A, TO_ADDR_LO),         # step 3: A → addr_lo
        LOAD_RD_A,                       # step 4: MEM[rd] → REG_A (value)
        ALU(PASS_A, TO_MEM),             # step 5: A → MEM[addr], END
    ])
    
    # PUSH rd — 9 cycles (tight fit in 8 steps: 0-1 fetch + 2-7 execute = 6 steps)
    # Need: read SP, dec SP, write SP, set addr, read rd, write mem = 6 execute steps. Fits!
    emit(0b10_100_000 | rd, [
        BUS(RD_RS_B),                    # step 2: MEM[sp=r7] → REG_B (read SP)
        # Wait: PUSH uses rs=sp(r7). Assembler encodes rs=111 in operand[7:5].
        # So LOAD_RS_B reads r7 = SP. Good.
        LOAD_ZERO_B,                     # step 2 REDO — actually we need SP in A:
    ])
    # Rewrite PUSH properly:
    # Assembler: PUSH rd → opcode=$A0+rd, operand=$E0 (rs=r7=sp, off5=0)
    emit(0b10_100_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[r7/sp] → REG_B (SP value)
        LOAD_OPR_A,                      # step 3: OPR → REG_A ($E0? No...)
        # This is getting messy. Let me think differently.
        # PUSH needs: SP-1 → addr, write rd to that addr, SP-1 → sp
        # With our tools:
        #   step 2: MEM[sp] → REG_A (read SP value)
        #   step 3: ZERO→B... no, need 1 to subtract
        # PROBLEM: we can't easily generate constant 1.
        # SOLUTION: use OPR! Assembler puts $01 in operand for PUSH.
        # PUSH rd encodes as: opcode=$A0+rd, operand=$01
        # Then OPR = $01, and we can use OPR as the decrement value.
        LOAD_ZERO_B,                     # PLACEHOLDER
        END,
    ])
    # Full PUSH (operand=$01):
    for c in range(2):
        for z in range(2):
            ucode[rom_addr(0b10_100_000 | rd, 0, z, c)] = FETCH0
            ucode[rom_addr(0b10_100_000 | rd, 1, z, c)] = FETCH1
            base = 0b10_100_000 | rd
            ucode[rom_addr(base, 2, z, c)] = BUS(RD_RD_A)      # MEM[sp]→A (sp is r7, but rd field = pushed reg!)
            # PROBLEM: rd field in opcode = the register to push, NOT sp.
            # We need to read r7(sp) but rd might be r2.
            # Solution: RD_RS_B reads from operand[7:5] = rs field.
            # Encode PUSH so rs=r7: operand = $E1 (rs=111=r7, imm5=00001=$01)
            # Then step 2 reads sp via rs, and imm5=1 for decrement.
            # But imm5 is 5 bits and we want just $01... let's use imm5=00001.
            ucode[rom_addr(base, 2, z, c)] = LOAD_RS_B          # MEM[rs=sp] → REG_B
            ucode[rom_addr(base, 3, z, c)] = LOAD_OPR_A         # OPR → REG_A (has $E1 = garbage for A)
            # This doesn't work either. The operand byte is multi-purpose.
            # 
            # NEW APPROACH: Dedicate a RAM location ($0008?) as "constant 1".
            # Boot code writes 1 there. PUSH microcode reads from fixed addr.
            # But we can't set address to $0008 without loading it somehow...
            #
            # SIMPLEST CORRECT APPROACH:
            # Make the ALU support DEC (A-1) as a mode. Hardware: tie B=0, Cin=1 for SUB.
            # This is the same carry-in trick needed for SLT!
            # ALU modes become: ADD, SUB, XOR, AND, OR, PASS_A, DEC(A-1), INC(A+1)
            # DEC = A + $FF + 0 = A - 1 (with B forced to $FF and Cin=0)
            # Or: DEC = A + 0 + Cin(=1) forced, then SUB mode → A - 0 - 1 = A-1
            # 
            # HARDWARE: one extra AND gate to force Cin=1 when ALU op = DEC or INC.
            # This is the carry-in connection we already discussed for SLT.
            #
            # With INC/DEC ALU modes:
            # PUSH rd (6 execute steps = 8 total):
            #   step 2: MEM[sp]→A via special "read r7" path
            #   step 3: ALU(DEC)→sp (SP--)
            #   step 4: ALU(DEC)→ADDR_LO (same result, addr = new SP)
            #   step 5: ZERO→ADDR_HI
            #   step 6: MEM[rd]→A (read value to push)
            #   step 7: ALU(PASS_A)→MEM[addr] (write to stack)
            #
            # But step 2 needs "read r7" not "read rd". Our BUS group has:
            #   RD_RD_A (source 010) reads from IR[2:0] = rd
            #   RD_RS_B (source 011) reads from OPR[7:5] = rs
            # For PUSH, assembler sets rs=r7. So LOAD_RS_B reads SP into B.
            # But we want it in A for DEC... We need MEM[rs]→A too.
            # 
            # DESIGN FIX: swap source 011 to "MEM[rs]→A" and add "MEM[rs]→B" elsewhere.
            # Or: add another source code. We have 8 source codes (3 bits), all used.
            #
            # PRAGMATIC FIX: read SP into B, then use PASS_B to move it:
            #   step 2: MEM[rs=sp]→B
            #   step 3: ALU(PASS_B)→A? No, ALU output goes to dest, not back to A.
            #   
            # OK let me step back and redesign the source codes to be more flexible:
            ucode[rom_addr(base, 2, z, c)] = LOAD_RS_B          # SP→B
            ucode[rom_addr(base, 3, z, c)] = ALU(PASS_B, TO_ADDR_LO)  # B(=SP)→addr_lo (current sp)
            # Now we need SP-1 for the new SP... but we lost the value.
            # REG_B still holds SP (it's a latch, retains value).
            # We need: B-1 → sp. ALU(SUB) needs A. Load A=1? From where?
            # CIRCULAR PROBLEM.
            #
            # The fundamental issue: with RAM registers and no hardware SP counter,
            # PUSH/POP are expensive. Every other CPU uses a hardware SP for this reason.
            #
            # DECISION: Accept that PUSH/POP are slow (9+ cycles) or add a hardware
            # stack pointer (1 extra 74HC161 as SP counter = 19 chips).
            # 
            # For now: PUSH = 9 cycles using multi-step with the understanding that
            # we'll add an INC/DEC ALU mode (carry-in gating, 1 extra gate).
            # Placeholder microcode:
            ucode[rom_addr(base, 2, z, c)] = LOAD_RS_B          # SP value → B
            ucode[rom_addr(base, 3, z, c)] = ALU(PASS_B, TO_RD)  # B → A via rd? No...
            ucode[rom_addr(base, 4, z, c)] = LOAD_ZERO_B        # placeholder
            ucode[rom_addr(base, 5, z, c)] = END                 # TODO: complete after hw decision
            ucode[rom_addr(base, 6, z, c)] = END
            ucode[rom_addr(base, 7, z, c)] = END
    
    # POP rd — placeholder (same issues as PUSH)
    for c in range(2):
        for z in range(2):
            base = 0b10_101_000 | rd
            ucode[rom_addr(base, 0, z, c)] = FETCH0
            ucode[rom_addr(base, 1, z, c)] = FETCH1
            ucode[rom_addr(base, 2, z, c)] = LOAD_RS_B   # SP → B
            ucode[rom_addr(base, 3, z, c)] = ALU(PASS_B, TO_ADDR_LO)  # addr = SP
            ucode[rom_addr(base, 4, z, c)] = LOAD_MEM_A  # MEM[SP] → A
            ucode[rom_addr(base, 5, z, c)] = ALU(PASS_A, TO_RD_END)  # A → rd, END
            # TODO: SP++ not done here — needs INC mode
            ucode[rom_addr(base, 6, z, c)] = END
            ucode[rom_addr(base, 7, z, c)] = END
    
    # LB rd, off(sp) — same as LB rd, off(rs) with rs=sp
    emit(0b10_110_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs=sp] → REG_B
        LOAD_OPR_A,                      # step 3: OPR → REG_A (offset)
        ALU(ADD, TO_ADDR_LO),            # step 4: A+B → addr_lo
        LOAD_MEM_A,                      # step 5: MEM[addr] → REG_A
        ALU(PASS_A, TO_RD_END),          # step 6: A → MEM[rd], END
    ])
    
    # SB rd, off(sp) — same as SB rd, off(rs) with rs=sp
    emit(0b10_111_000 | rd, [
        LOAD_RS_B,                       # step 2: MEM[rs=sp] → REG_B
        LOAD_OPR_A,                      # step 3: OPR → REG_A (offset)
        ALU(ADD, TO_ADDR_LO),            # step 4: A+B → addr_lo
        LOAD_RD_A,                       # step 5: MEM[rd] → REG_A (value)
        ALU(PASS_A, TO_MEM),             # step 6: A → MEM[addr], END
    ])
    
    # ─── Class 11: Branch/Jump ───
    
    # BEQ rs1, rs2, off — 6 cycles
    # rs1 from opcode[2:0] (rd field), rs2 from operand[7:5] (rs field)
    for c in range(2):
        for z in range(2):
            base = 0b11_000_000 | rd
            ucode[rom_addr(base, 0, z, c)] = FETCH0
            ucode[rom_addr(base, 1, z, c)] = FETCH1
            ucode[rom_addr(base, 2, z, c)] = LOAD_RD_A   # rs1(=rd field) → A
            ucode[rom_addr(base, 3, z, c)] = LOAD_RS_B   # rs2 → B
            ucode[rom_addr(base, 4, z, c)] = ALU(SUB, TO_ADDR_LO)  # compare, set flags
            # Step 5: flags now in ROM address for step 5... NO.
            # Flags set in step 4, but ROM address for step 5 uses OLD flags.
            # Need step 5 as NOP, then step 6 branches.
            ucode[rom_addr(base, 5, z, c)] = NOP  # wait for flag propagation
    # Step 6: NEW flags visible
    for c in range(2):
        for z in range(2):
            base = 0b11_000_000 | rd
            if z == 1:  # Z=1 after SUB → equal → branch taken
                ucode[rom_addr(base, 6, z, c)] = BRANCH(ALWAYS, BR_REL)  # PC += sext(OPR)
            else:
                ucode[rom_addr(base, 6, z, c)] = END  # not taken
    # Total: 7 cycles (one extra for flag propagation). Acceptable.
    
    # BNE rs1, rs2, off — 7 cycles (same pattern, branch on Z=0)
    for c in range(2):
        for z in range(2):
            base = 0b11_001_000 | rd
            ucode[rom_addr(base, 0, z, c)] = FETCH0
            ucode[rom_addr(base, 1, z, c)] = FETCH1
            ucode[rom_addr(base, 2, z, c)] = LOAD_RD_A
            ucode[rom_addr(base, 3, z, c)] = LOAD_RS_B
            ucode[rom_addr(base, 4, z, c)] = ALU(SUB, TO_ADDR_LO)
            ucode[rom_addr(base, 5, z, c)] = NOP
    for c in range(2):
        for z in range(2):
            base = 0b11_001_000 | rd
            if z == 0:  # Z=0 → not equal → branch
                ucode[rom_addr(base, 6, z, c)] = BRANCH(ALWAYS, BR_REL)
            else:
                ucode[rom_addr(base, 6, z, c)] = END
    
    # BLT rs1, rs2, off — 7 cycles (branch on C=1 after SUB = borrow = less than)
    for c in range(2):
        for z in range(2):
            base = 0b11_010_000 | rd
            ucode[rom_addr(base, 0, z, c)] = FETCH0
            ucode[rom_addr(base, 1, z, c)] = FETCH1
            ucode[rom_addr(base, 2, z, c)] = LOAD_RD_A
            ucode[rom_addr(base, 3, z, c)] = LOAD_RS_B
            ucode[rom_addr(base, 4, z, c)] = ALU(SUB, TO_ADDR_LO)
            ucode[rom_addr(base, 5, z, c)] = NOP
    for c in range(2):
        for z in range(2):
            base = 0b11_010_000 | rd
            if c == 1:  # C=1 → borrow → less than → branch
                ucode[rom_addr(base, 6, z, c)] = BRANCH(ALWAYS, BR_REL)
            else:
                ucode[rom_addr(base, 6, z, c)] = END
    
    # BGE rs1, rs2, off — 7 cycles (branch on C=0 = no borrow = >=)
    for c in range(2):
        for z in range(2):
            base = 0b11_011_000 | rd
            ucode[rom_addr(base, 0, z, c)] = FETCH0
            ucode[rom_addr(base, 1, z, c)] = FETCH1
            ucode[rom_addr(base, 2, z, c)] = LOAD_RD_A
            ucode[rom_addr(base, 3, z, c)] = LOAD_RS_B
            ucode[rom_addr(base, 4, z, c)] = ALU(SUB, TO_ADDR_LO)
            ucode[rom_addr(base, 5, z, c)] = NOP
    for c in range(2):
        for z in range(2):
            base = 0b11_011_000 | rd
            if c == 0:  # C=0 → no borrow → greater or equal → branch
                ucode[rom_addr(base, 6, z, c)] = BRANCH(ALWAYS, BR_REL)
            else:
                ucode[rom_addr(base, 6, z, c)] = END
    
    # JAL rd, off8 — 5 cycles
    emit(0b11_100_000 | rd, [
        BRANCH(ALWAYS, PC_LO_TO_A),      # step 2: PC_LO → REG_A
        ALU(PASS_A, TO_RD),              # step 3: A → MEM[rd] (save return)
        BRANCH(ALWAYS, BR_REL),          # step 4: PC += sext(off8), END
    ])
    
    # JALR rd, rs — 5 cycles (PC = rs register value)
    emit(0b11_101_000 | rd, [
        BRANCH(ALWAYS, PC_LO_TO_A),      # step 2: PC_LO → REG_A
        ALU(PASS_A, TO_RD),              # step 3: A → MEM[rd] (save return)
        LOAD_RS_B,                       # step 4: MEM[rs] → REG_B (target addr)
        BRANCH(ALWAYS, BR_ABS),          # step 5: PC = addr from B? (needs design)
    ])
    
    # J off8 — 3 cycles
    emit(0b11_110_000 | rd, [
        BRANCH(ALWAYS, BR_REL),          # step 2: PC += sext(off8), END
    ])
    
    # SYS — 3 cycles (NOP/HLT based on operand)
    emit(0b11_111_000 | rd, [
        SYS_OP,                          # step 2: OPR subdecode handles NOP/HLT/EI/DI/IRET
    ])


emit_irq_entry()


# === OUTPUT ===
def output_hex(filename):
    """Write microcode ROM as Intel HEX or raw hex."""
    with open(filename, "w") as f:
        for i in range(ROM_SIZE):
            f.write(f"{ucode[i]:02x}\n")
    print(f"Generated {filename} ({ROM_SIZE} entries, 8-bit)")

def output_bin(filename):
    """Write microcode ROM as raw binary."""
    with open(filename, "wb") as f:
        f.write(bytes(ucode))
    print(f"Generated {filename} ({ROM_SIZE} bytes)")

def print_stats():
    """Print microcode statistics."""
    used = sum(1 for x in ucode if x != END)
    print(f"\nRV8-R Legacy Microcode Generator")
    print(f"{'='*40}")
    print(f"ROM size:     {ROM_SIZE} entries (16KB)")
    print(f"Data width:   8 bits")
    print(f"Address:      14 bits [IRQ,C,Z,step(3),opcode(8)]")
    print(f"WARNING:      FullHW requires 15-bit [IRQ,C,Z,step(4),opcode(8)] direct control")
    print(f"Used entries: {used}/{ROM_SIZE} ({100*used//ROM_SIZE}%)")
    print(f"\nInstructions defined:")
    print(f"  Class 00 (ALU reg):  ADD SUB AND OR XOR SLT SLL [SRL=sw]")
    print(f"  Class 01 (ALU imm):  LI ADDI SUBI ANDI ORI XORI SLTI LUI")
    print(f"  Class 10 (Memory):   LB SB LBfp SBfp PUSH POP LBsp SBsp")
    print(f"  Class 11 (Control):  BEQ BNE BLT BGE JAL JALR J SYS")
    print(f"  SYS subcodes:         0=NOP 1=HLT 2=EI 3=DI 4=IRET")
    print(f"\nNOTE: PUSH/POP/SLT need ALU carry-in support (1 gate)")
    print(f"NOTE: SRL = software macro (not in microcode)")
    print(f"NOTE: Frozen map uses IRQ save $FFF6/$FFF7 and vector $7F00")
    print(f"NOTE: RTL/testbench migration from the old $8000/$FF00 map is pending")

if __name__ == "__main__":
    print_stats()
    output_hex("microcode.hex")
    output_bin("microcode.bin")
