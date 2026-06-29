# Verifier Memory

## Test Coverage

| Layer | Status | Command |
|-------|--------|---------|
| Verilog full ISA | ✅ 127 cycles | `iverilog ... tb_rv8gr_full.v && vvp` |
| Verilog IRQ | ✅ pass | `tb_rv8gr_irq.v` |
| Verilog SETDP | ✅ 160 cycles | `tb_rv8gr_setdp.v` |
| Verilog opcode sweep | ✅ 512 cases | `tb_rv8gr_opcode_sweep.v` |
| Gate-level sim | ✅ 8/8 | `python3 sim/chip_sim.py` |
| Soft debug | ✅ 4/4 | `python3 sim/soft_debug.py` |
| Assembler | ✅ | `python3 tools/rv8gr_asm.py` |
| Physical hardware | ⬜ not yet built | — |

## Known Hazards (all resolved in design)

1. SRC+STR bus fight → guarded by BUF_OE_SAFE
2. WR_DIR timing → gated with T2+STORE
3. Z-flag async preset → safe at ≤5MHz
4. IRQ during jump → deferred to next instruction

## Defect Log

(Empty — no defects currently open)

## Review Checklist (use for every coder submission)

- [ ] Does it compile/assemble without errors?
- [ ] Does existing test suite still pass?
- [ ] Are new tests written for the change?
- [ ] Traced signal/code path end-to-end?
- [ ] No new SRC+STR conflicts?
- [ ] Both sim layers agree?
