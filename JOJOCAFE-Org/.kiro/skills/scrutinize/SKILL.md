---
name: scrutinize
description: Outsider-perspective review of hardware, Verilog, wiring, or ISA changes. Questions intent, traces signal path, verifies claims. Trigger on /scrutinize or when asked to review/audit/sanity-check.
---

# Scrutinize

Stand outside the change. Ask if it should exist. Verify it does what it claims.

## Stance

- **Outsider** — read the artifact cold, forget who designed it.
- **End-to-end** — trace through the full system, not just the diff.
- **Actionable** — every finding: what to change, why, evidence.

## Workflow (in order, don't skip)

### 1. Intent

- State the goal in one sentence. Can't? → underspecified, stop.
- **Is there a simpler way?** Consider:
  - Doing nothing (is the problem real?)
  - Using a spare gate (U25 OR, U33 AND)
  - Fewer chips (can existing chip absorb?)
  - Software instead of hardware (macro, SETDP sequence)
  - Different encoding that avoids the issue

### 2. Trace

**Hardware**: source pin → wire → destination pin. Check:
- Polarity correct? (active-high vs active-low)
- Timing stable before consuming edge?
- Fan-out within spec? (≤10 for 74HC)
- Bus contention possible?

**Verilog**: input → combinational → register → output. Check:
- TB exercises this path?
- chip_sim.py agrees?

**ISA**: opcode bits → control logic. Check:
- Existing instructions break?
- New SRC+STR conflict? (bit3 & bit2)
- SETDP/IRQ/Z-flag interaction?

### 3. Verify

For each claim:
- Does the traced path produce that behavior?
- Edge cases: reset state, back-to-back instructions, IRQ mid-instruction, DP boundary ($00/$FF), Z-flag from previous instruction.
- What does it silently change? (timing margin, chip count, forbidden opcodes)
- How is it tested?

### 4. Report

Order by severity: **blocker → major → nit**.

Each finding:
- **What**: one sentence, cite chip:pin or file:line.
- **Why**: consequence (bus fight, wrong data, timing violation).
- **Evidence**: trace step that exposes it.
- **Fix**: concrete, minimal.

Verdict: **ship / fix-then-ship / rework / reject** + one-line reason.

## Rules

- No rubber-stamps. State what you checked.
- Cite or it didn't happen.
- Simpler-alternative pass is mandatory.
- Don't pad nits when there's a structural problem.
- 33-chip budget is frozen. Adding a chip needs strong justification.
