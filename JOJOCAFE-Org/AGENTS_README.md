# JOJOCAFE-Org: AI Team Operations Guide

## What Is This

A 7-agent AI team that builds the RV8 CPU project. Each agent has a specific role, its own skills, and persistent memory. The team enforces engineering discipline: separation of duties, non-implementer verification, and clear communication.

---

## How to Use

### Option A: Coordinator (recommended for complex tasks)

```
Ctrl+Shift+0  →  describe what you need
```

The coordinator breaks it down, dispatches to specialists, collects results, and summarizes.

**Best for**: multi-step tasks, tasks spanning multiple domains, "I want X but not sure how to start."

### Option B: Direct Access (for focused work)

Switch directly to a specialist when you know exactly who you need:

| Shortcut | Agent | When to use |
|----------|-------|-------------|
| Ctrl+Shift+1 | architect | "Should we use X or Y?" / "Design the RV8-R ISA" |
| Ctrl+Shift+2 | verifier | "Check this code" / "Why is test failing?" / "Debug X" |
| Ctrl+Shift+3 | rtl-coder | "Write a testbench for X" / "Add instruction Y to Verilog" |
| Ctrl+Shift+4 | hw-coder | "Design the ALU wiring" / "Create KiCad schematic" / "Verify a DIP pinout" |
| Ctrl+Shift+5 | sw-coder | "Write a blink program" / "Add macro to assembler" |
| Ctrl+Shift+6 | docs-writer | "Write lab 15" / "Translate module guide to Thai" |

---

## How It Works

### Knowledge Hierarchy (what each agent loads)

```
┌─────────────────────────────────────────────────┐
│  TEAM_MEMORY.md          (shared facts)         │  ← every agent reads
│  skill://team/SKILL.md   (shared rules)         │
├─────────────────────────────────────────────────┤
│  skill://role-<name>     (role patterns)        │  ← only that agent
│  .agent_state/<name>/MEMORY.md (personal mem)   │
├─────────────────────────────────────────────────┤
│  skill://cpu-design      (domain knowledge)     │  ← agents that need it
│  skill://wiring-rules    (pin-level rules)      │
│  skill://component-library (shared chips)        │
│  skill://debug-mantra    (debugging method)     │
│  skill://scrutinize      (review method)        │
│  skill://thai-labs       (doc format)           │
│  skill://dispatch-protocol (routing rules)      │
└─────────────────────────────────────────────────┘
```

### Economy Model

| Agent | Model | Why |
|-------|-------|-----|
| coordinator, architect, verifier, docs-writer | opus | Judgment, review, decisions |
| rtl-coder, hw-coder, sw-coder | economy (qwen3-coder-next) | Bulk implementation |

Coders escalate to opus automatically for safety/hard tasks.

### Quality Flow

```
User → coordinator → coder (implements) → verifier (checks) → done
                   ↑                                    │
                   └────── defect? route back ──────────┘
```

No code ships without non-author verification.

---

## Memory System

### Shared (everyone reads)
- `TEAM_MEMORY.md` — project facts, current sprint, critical rules
- `PROJECT_STATE.md` — what's done, what's next, recent decisions

### Personal (each agent updates their own)
- `.agent_state/<agent>/MEMORY.md` — what I've done, what I know, pending work

### Defects
- `.agent_state/defects/DEF-NNN.md` — filed by verifier, routed to coder

### Updating Memory

Agents should update their MEMORY.md after completing significant work. The coordinator updates dispatch history. The verifier updates test coverage.

---

## Portability

### Move to another project

```bash
cp -r JOJOCAFE-Org/.kiro /path/to/project/
cp JOJOCAFE-Org/{TEAM_MEMORY.md,PROJECT_STATE.md,AGENTS_README.md} /path/to/project/
mkdir -p /path/to/project/.agent_state/{coordinator,architect,verifier,rtl-coder,hw-coder,sw-coder,docs-writer,defects}
```

Then update `TEAM_MEMORY.md` and `PROJECT_STATE.md` for that project.

### Move to another machine

```bash
git clone <this-repo>
# Everything travels with the repo — no external dependencies
```

### Adapt for another domain

1. Replace `cpu-design` and `wiring-rules` skills with your domain knowledge
2. Edit role skills for your tech stack
3. Edit `TEAM_MEMORY.md` for your project facts
4. Keep the 7-role structure — it enforces good engineering

---

## File Inventory

```
JOJOCAFE-Org/
├── .kiro/agents/               7 agent configs
│   ├── coordinator.json        entry point, dispatch only
│   ├── architect.json          design authority
│   ├── verifier.json           quality gate
│   ├── rtl-coder.json          Verilog implementer
│   ├── hw-coder.json           circuit implementer
│   ├── sw-coder.json           tools/firmware implementer
│   └── docs-writer.json        documentation specialist
├── .kiro/skills/               15 skills (8 shared + 7 role-specific)
│   ├── team/                   org rules (all agents)
│   ├── cpu-design/             architecture knowledge
│   ├── component-library/      shared 74HC/memory model and datasheet workflow
│   ├── debug-mantra/           debugging method
│   ├── scrutinize/             review method
│   ├── wiring-rules/           pin-level rules
│   ├── thai-labs/              doc format
│   ├── dispatch-protocol/      routing rules
│   ├── role-coordinator/       coordinator patterns
│   ├── role-architect/         architect patterns
│   ├── role-verifier/          verifier patterns
│   ├── role-rtl-coder/         RTL patterns
│   ├── role-hw-coder/          HW patterns
│   ├── role-sw-coder/          SW patterns
│   └── role-docs-writer/       docs patterns
├── .agent_state/               per-agent memory
│   ├── coordinator/MEMORY.md
│   ├── architect/MEMORY.md
│   ├── verifier/MEMORY.md
│   ├── rtl-coder/MEMORY.md
│   ├── hw-coder/MEMORY.md
│   ├── sw-coder/MEMORY.md
│   ├── docs-writer/MEMORY.md
│   └── defects/                defect reports
├── TEAM_MEMORY.md              shared project knowledge
├── PROJECT_STATE.md            current status
├── AGENTS.md                   team directory (compact)
├── AGENTS_README.md            this file (operational guide)
└── README.md                   quick start
```

---

## Quick Reference Card

| I want to... | Do this |
|--------------|---------|
| Start a complex task | Ctrl+Shift+0, describe it |
| Write Verilog | Ctrl+Shift+3, ask for it |
| Debug a test failure | Ctrl+Shift+2, paste the error |
| Make a design decision | Ctrl+Shift+1, present the trade-off |
| Write a lab sheet | Ctrl+Shift+6, specify the topic |
| Design a circuit | Ctrl+Shift+4, describe the module |
| Write a tool/program | Ctrl+Shift+5, specify requirements |
| See who does what | Read AGENTS.md |
| See current project state | Read PROJECT_STATE.md |
| See shared knowledge | Read TEAM_MEMORY.md |
