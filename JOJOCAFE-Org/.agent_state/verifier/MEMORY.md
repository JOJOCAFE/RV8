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
| Components 74HC smoke | ✅ pass | `iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v && vvp /tmp/tb_74hc_smoke.vvp` |
| Components Memory smoke | ✅ pass | `iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v && vvp /tmp/tb_memory_smoke.vvp` |
| Components Python chip tests | ✅ pass | `cd Components/python && python3 -B -m tests.test_chips` |

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

## Component Library Verification

- Shared repo: `/home/jo/kiro/Components`, remote `git@github.com:JOJOCAFE/Components.git`.
- Verify all local `*-pin.md` PDF references resolve under `Components/source`.
- Verify any breadboard pinout has manufacturer DIP/PDIP package evidence.
- Verify `source/` has no duplicate temporary datasheets or `Zone.Identifier` files.
- Current blocked pinout placeholders are expected: `74HC/74hc150-pin.md`, `74HC/74hc260-pin.md`.
- Verify Python/Verilog compatibility when chip behavior changes: controls, output polarity, tri-state, async controls, memory semantics, and rising/falling edge behavior.
- Current known follow-up: SST39SF010A Python/Verilog write-trigger alignment if exact flash `/WE` edge behavior is required.
- Next deferred backend feature to verify: probe/test-logic channels.
