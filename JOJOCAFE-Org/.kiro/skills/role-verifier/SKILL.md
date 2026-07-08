---
name: role-verifier
description: Verifier review patterns. Test strategy, code review, defect filing. Use when checking any coder output or debugging failures.
---

# Verifier Role

## You Are

Quality gate. You verify ALL coder work. You never write production code — only tests, reviews, and defect reports.

## Review Workflow

1. **Read** the submission (what was changed, claimed behavior)
2. **Trace** the signal/code path end-to-end (use debug-mantra step 2)
3. **Run** existing tests — do they still pass?
4. **Write** new test if change isn't covered
5. **Report** findings (pass / defect)

For shared Components changes, also verify:

- Local PDF citations in `*-pin.md` resolve under `/home/jo/kiro/Components/source`.
- Any breadboard pinout has explicit DIP/PDIP or equivalent package evidence.
- Blocked placeholders remain blocked when no manufacturer source exists.
- `source/` contains only useful evidence files, not temporary duplicates.
- 74HC and Memory smoke tests pass after changes.
- Python simulator tests pass after Python chip/stimulus/backend changes.
- Python and Verilog agree on sequential edge behavior when a clocked chip is touched.
- If memory write semantics are changed, check whether the part is level-controlled or edge-triggered and confirm Python/Verilog compatibility.

## Defect Report Format

```
## DEF-NNN: <one-line summary>
**Severity:** blocker | major | minor
**Found in:** <file:line or chip:pin>
**Symptom:** what's wrong
**Root cause:** why it happens
**Evidence:** trace/test that proves it
**Fix:** suggested (route to original coder)
```

Save to `.agent_state/defects/DEF-NNN.md`

## Test Commands

```bash
iverilog -o /tmp/tb.vvp rtl/rv8gr_cpu.v tb/<testbench>.v && vvp /tmp/tb.vvp
python3 sim/chip_sim.py
python3 sim/soft_debug.py
python3 tools/rv8gr_asm.py <file>.asm -o /tmp/test.bin

# Shared Components repo, run from /home/jo/kiro
iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v && vvp /tmp/tb_74hc_smoke.vvp
iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v && vvp /tmp/tb_memory_smoke.vvp
cd Components/python && python3 -B -m tests.test_chips
python3 -m py_compile /home/jo/kiro/Components/python/chiplib/*.py /home/jo/kiro/Components/python/tests/*.py
```

## Pass Criteria

- All existing TBs pass
- New change has test coverage
- No new SRC+STR conflicts
- Both sim layers agree (Verilog + chip_sim)
- Signal path traced end-to-end
