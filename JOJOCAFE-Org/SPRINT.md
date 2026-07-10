# Sprint 1: Physical Build Kickoff

**Start:** 2026-06-29  
**Goal:** Parts ordered, first modules built and verified on breadboard  
**Status:** 🟡 In Progress

---

## Team Task Lists

### Pim (พิม) — Coordinator
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Maintain BACKLOG.md, SPRINT.md, TEAMLOG.md | — | 🔄 ONGOING | Update after every deliverable |
| Coordinate parts order with Jo | B-001 | ⬜ TODO | Get BOM approved, find suppliers |
| Track build progress (Labs 01-14) | B-002→005 | ⬜ TODO | Update this file as modules complete |
| Schedule student workshop dry run | B-023 | ⬜ TODO | After build verified |

### Bank (แบงค์) — Architect
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Review first physical build results | — | ⬜ TODO | Standby for Ohm's questions |
| Decide RV8-Bus connector pin assignment | B-021 | ⬜ TODO | Low priority, after build |
| Begin RV8-R architecture sketch | B-030 | ⬜ TODO | Background, when free |

### Fern (เฟิร์น) — Verifier
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Verify Programmer field test | B-012 | 🟡 READY | Use `Programmer/FIELD_TEST_PROTOCOL.md` when hardware is available |
| Verify each lab module on hardware | B-007 | ⛔ BLOCKED | Waiting for physical hardware build evidence; non-physical B-007 report is available |
| Run full ISA test on physical CPU | B-007 | ⛔ BLOCKED | Requires wired CPU and hardware evidence |
| Gate-sim coverage check (remaining .bin) | B-013 | ✅ DONE | Replaced by all-ISA dual Verilog scoreboard plus opcode sweep |

### Mint (มิ้นท์) — RTL Coder
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Add remaining .bin test coverage to gate-sim | B-013 | ✅ DONE | All-ISA dual Verilog scoreboard plus opcode sweep |
| Support debug if hardware ≠ simulation | — | ⬜ STANDBY | Activate on discrepancy |
| Maintain Verilog model if design tweaks needed | — | ⬜ STANDBY | Architecture frozen, unlikely |

### Ohm (โอม) — HW Coder
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Build Lab 01-03 (clock, reset, ROM read) | B-002 | ⬜ TODO | First priority |
| Build Lab 04-07 (fetch, AC, ALU, store) | B-003 | ⬜ TODO | After 01-03 verified |
| Build Lab 08-10 (branch, jump, Z-flag) | B-004 | ⬜ TODO | After 04-07 verified |
| Build Lab 11-14 (SETDP, IRQ, integration) | B-005 | ⬜ TODO | After 08-10 verified |
| Update wiring guide if discrepancies found | B-014 | ⬜ TODO | Document as you go |

### Bam (แบม) — SW Coder
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Write example .asm programs (blink, counter, echo) | B-010 | ✅ DONE | Implemented and assembler-verified |
| Prep Programmer field test suite | B-012 | ✅ DONE | `Programmer/FIELD_TEST_PROTOCOL.md`; 51 mock tests define virtual preflight |
| Flash test ROM onto physical hardware | B-006 | ⬜ TODO | After Ohm builds ROM module |
| Start BASIC interpreter design | B-011 | 🟡 PHASE 1 | `programs/basic_min.asm` and `sim/test_basic_min.py`; interactive interpreter needs I/O/runtime design |

### Noon (นุ่น) — Docs Writer
| Task | Backlog | Status | Notes |
|------|---------|--------|-------|
| Support Ohm with lab build (Thai instructions) | B-002 | ⬜ TODO | Clarify lab steps on request |
| Document physical build progress (photos/notes) | B-022 | ⬜ TODO | Start from Lab 01 |
| Update wiring guide with Ohm if needed | B-014 | ⬜ TODO | Keep 03_wiring_guide.md current |

---

## Sprint Rules

1. **Ohm builds sequentially** — one lab module at a time, verify before next
2. **Fern tests each module** — no "move on and fix later"
3. **Discrepancy → Mint + Bank** — if hardware ≠ sim, debug immediately
4. **Bam delivers test programs** — example ASM programs are implemented and assembler-verified
5. **Noon documents** — photos/notes as we go, not after

## Done This Sprint

| Task | Completed | By |
|------|-----------|-----|
| B-010 example ASM programs implemented | 2026-07-09 | Bam |
| B-010 example ASM programs assembler-verified | 2026-07-09 | Bam + Fern |
| B-012 Programmer field-test protocol prepared | 2026-07-10 | Bam + Fern |
| RV8GR doc integrity/source-of-truth pass saved and packaged | 2026-07-10 | Pim + Noon + Fern |
| B-011 minimal BASIC-style ROM phase 1 | 2026-07-10 | Bam + Fern |
