---
name: scrutinize
description: Outsider-perspective review of RV8 hardware designs, Verilog changes, wiring modifications, or ISA decisions. Questions intent (is there a simpler way?), traces the actual signal/code path, verifies the change does what it claims. Output is concise, actionable, with rationale. Trigger on /scrutinize and proactively when user asks to review, audit, sanity-check, or get a second opinion on a design change, wiring mod, Verilog diff, or ISA addition.
---

# Scrutinize (RV8 Hardware)

Stand outside the change and ask whether it should exist at all, then verify it actually does what it claims end-to-end.

## Operating stance

- **Outsider.** Forget who designed it. Read the artifact cold.
- **End-to-end, not diff-local.** Trace the signal path through the full system, not just the changed chip.
- **Actionable, concise, with rationale.** Every finding states *what to change*, *why*, and *what evidence* led you there.

## Workflow — run in order, do not skip

### 1. Intent — what is this actually trying to do?

- State the goal in one sentence. If you cannot, the design is underspecified — say so and stop.
- Ask: **is there a simpler, smaller way to achieve the same goal?** Consider:
  - Doing nothing (is the problem real? Does the current design already handle it?)
  - Using a gate that's already spare (U25 has unused gates; U33 has spare inputs)
  - Fewer chips (can an existing chip absorb this function?)
  - Solving it in software instead of hardware (SETDP sequence, assembler macro)
  - A different instruction encoding that avoids the issue entirely
- If a simpler alternative exists, name it with rationale. This is the most valuable output.

### 2. Trace — walk the actual signal/code path

**For hardware/wiring changes:**
- Trace the signal from source chip pin → wire → destination chip pin.
- Check: does the signal arrive with correct polarity? (active-high vs active-low)
- Check: timing — is it stable before the consuming edge (CLK↑, /T2↓)?
- Check: loading — how many inputs are driven? (74HC fanout = 10 LSTTL loads, usually fine)
- Check: bus contention — can two outputs ever drive the same wire simultaneously?
- Include unchanged signals on either side. Bugs hide at the seams.

**For Verilog changes:**
- Trace: input → combinational logic → register → output.
- Check: does the TB actually exercise this path? (not just happy-path)
- Check: does chip_sim.py agree with the Verilog model?

**For ISA/encoding changes:**
- Trace the opcode bits through the control logic.
- Check: does any existing instruction break? (all 256 opcodes have deterministic behavior)
- Check: does it create a new SRC+STR conflict? (bit3 AND bit2 = forbidden)
- Check: does it interact with SETDP, IRQ, or Z-flag in unexpected ways?

Note every place the trace surprises you. Surprises are signal.

### 3. Verify — does it actually do what it claims?

For each claim the change makes:
- **Does the traced path actually produce that behavior?** Walk it explicitly.
- **What inputs/states would break it?** Edge cases for hardware:
  - Power-on reset state (are latches/FFs in known state?)
  - Back-to-back instructions (pipeline hazards in 3-cycle machine?)
  - Interrupt arriving mid-instruction
  - Data page = $00 vs $FF (boundary)
  - Z-flag set by previous instruction affecting current branch
- **What does it silently change?** Timing margin, power draw, chip count, forbidden opcode space.
- **How is it tested?** Does the Verilog TB cover it? Does chip_sim.py cover it? Is there a .asm test program?

### 4. Report

One section per finding. Order by severity: **blocker → major → nit**.

For each:
- **Finding** — one sentence. Cite chip:pin or file:line.
- **Why it matters** — the consequence (bus fight, wrong data, timing violation, extra chip needed).
- **Evidence** — the trace step that exposes it.
- **Suggested change** — concrete, minimal.

Close with a one-line verdict: **ship / fix-then-ship / rework / reject** — with the single biggest reason.

## Operating rules

- **No rubber-stamps.** If you find nothing, state what you traced and checked.
- **Cite or it didn't happen.** Every claim references a specific chip, pin, signal, file, or line.
- **One simpler-alternative pass is mandatory.** Even on small changes. Skip only if user says "don't question scope."
- **Don't pad with nits when there's a structural problem.** Lead with it.
- **No flattery, no hedging.** State the finding.
- **Physical build awareness.** On a breadboard, every wire is a failure point. Fewer wires = fewer bugs. Flag changes that add wiring complexity disproportionate to their benefit.
- **33-chip budget.** The RV8-GR is signed off at 33 logic + ROM + RAM. Any change adding a chip needs strong justification.
