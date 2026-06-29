# SW Coder Memory

## Tools Built

| Tool | Status | Purpose |
|------|--------|---------|
| `tools/rv8gr_asm.py` | ✅ done | Assembler (18 opcodes + macros) |
| `sim/chip_sim.py` | ✅ done | Gate-level sim (35 chips) |
| `sim/soft_debug.py` | ✅ done | High-level trace sim |
| `rv8flash.py` | ✅ done | ROM programmer (flash/read/verify) |
| `rv8term.py` | ✅ done | Terminal bridge via /SLOT1 |

## Assembler Features

- 18 opcodes + macros (CLR, INC, DEC, NOT, NOTI)
- Cross-page validation
- Overlap detection
- .memh output for Verilog
- Page-safe branch checking

## ISA Quick Ref

- Immediate: opcode, imm (2 bytes, SRC=0)
- Register: opcode, rs/rd (2 bytes, SRC=1 or STR=1)
- Branch/Jump: opcode, addr_lo (2 bytes, uses Page Register)

## Programmer Protocol

- `?` → `Connected\n` (identify)
- `F` + 32KB → `D\n` (flash)
- `V` → 32KB (verify/read)
- `R` → `K\n` (run mode)

## Pending

- Example programs (.asm): blink, counter, game, BASIC stub
- RV8-R assembler (when ISA designed)
