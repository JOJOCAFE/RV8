---
name: dispatch-protocol
description: How the coordinator decomposes user requests and routes to specialist agents. Trigger on any multi-step task or when the coordinator needs to delegate work.
---

# Dispatch Protocol

## Routing Rules

| Task type | Route to | Verify with |
|-----------|----------|-------------|
| ISA design, chip selection, architecture trade-off | architect | — (architect is judgment) |
| Verilog RTL, testbench, gate-level sim code | rtl-coder | verifier |
| Circuit, wiring, KiCad, pin tables | hw-coder | verifier + architect |
| Assembler, tools, ROM, firmware | sw-coder | verifier |
| Lab sheets, guides, Thai docs | docs-writer | — (docs-writer self-checks accuracy) |
| Review, audit, test, debug | verifier | — (verifier is judgment) |
| Design decision or ADR | architect | verifier (for feasibility) |

## Decomposition

1. Read the user's request
2. Identify which domains it touches (RTL? HW? SW? Docs? Architecture?)
3. If single-domain → dispatch directly
4. If multi-domain → break into sub-tasks, dispatch in parallel where independent
5. If sequential dependency → chain: e.g., architect spec → rtl-coder implement → verifier check

## Dispatch Template

When dispatching, state:
- **To:** agent name
- **Task:** one-sentence description
- **Context:** relevant files or prior decisions
- **Verify:** who checks the result (if applicable)

## Escalation

- If a coder reports they need a design decision → escalate to architect
- If verifier finds a defect → route back to the original coder with the defect report
- If a task is "safety/hard" (bus timing, ISA encoding change, chip removal) → use opus model override

## Anti-patterns

- Coordinator writing code → NEVER
- Coder verifying own work → NEVER (route to verifier)
- Skipping verification on RTL changes → NEVER
- Dispatching without context → always include relevant file paths
