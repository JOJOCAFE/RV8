# Project Backlog

Last updated: 2026-07-10

## Priority Legend
- 🔴 P0 — Must do now (blocks physical build)
- 🟠 P1 — Should do this sprint
- 🟡 P2 — Next sprint
- 🟢 P3 — Queued / future

---

## 🔴 P0 — Physical Build (RV8-GR)

| # | Task | Owner | Status |
|---|------|-------|--------|
| B-001 | Order parts (BOM finalized) | Boss (Jo) | ⬜ TODO |
| B-002 | Build Lab 01-03 on breadboard (clock, reset, ROM) | Ohm + Noon | ⬜ TODO |
| B-003 | Build Lab 04-07 (fetch, AC, ALU, store) | Ohm | ⬜ TODO |
| B-004 | Build Lab 08-10 (branch, jump, Z-flag) | Ohm | ⬜ TODO |
| B-005 | Build Lab 11-14 (SETDP, IRQ, full integration) | Ohm | ⬜ TODO |
| B-006 | Flash test ROM via Programmer board | Bam + Ohm | ⬜ TODO |
| B-007 | Run full ISA test on physical hardware | Fern | ⛔ BLOCKED — non-physical report available; hardware evidence still required |

## 🟠 P1 — Sprint Support

| # | Task | Owner | Status |
|---|------|-------|--------|
| B-010 | Write example .asm programs (blink, counter, echo) | Bam | ✅ DONE — assembler-verified |
| B-011 | Write BASIC interpreter ROM (minimal) | Bam | 🟡 PHASE 1 — `programs/basic_min.asm` runtime smoke + Python regression; interactive interpreter needs I/O/runtime design |
| B-012 | Programmer field test protocol and hardware evidence | Bam + Fern | 🟡 READY FOR FIELD TEST — 51 mock tests pass; physical evidence required |
| B-013 | Gate-level sim: add remaining .bin coverage | Mint + Fern | ✅ DONE — replaced by all-ISA dual Verilog scoreboard plus existing opcode sweep |
| B-014 | Update wiring guide if physical build reveals discrepancies | Ohm + Noon | ⬜ TODO |

## 🟡 P2 — Post-Build / Polish

| # | Task | Owner | Status |
|---|------|-------|--------|
| B-020 | PCB layout (4 MHz version) | Ohm | ⬜ TODO |
| B-021 | RV8-Bus connector finalization | Bank + Ohm | ⬜ TODO |
| B-022 | Video/photo documentation of physical build | Noon | ⬜ TODO |
| B-023 | Student workshop dry run (labs 01-14) | Noon + Pim | ⬜ TODO |
| B-024 | Game ROM (simple Snake or Pong) | Bam | ⬜ TODO |

## 🟢 P3 — Future Projects

| # | Task | Owner | Status |
|---|------|-------|--------|
| B-030 | RV8-R FullHW architecture continuation (49 logic / 53 total packages) | Bank | ⬜ TODO |
| B-031 | RV8-R microcode generator (15-bit direct-control) | Mint + Bank | ⬜ TODO |
| B-032 | RV8-R Verilog model + testbenches | Mint + Fern | ⬜ TODO |
| B-033 | RV8-G architecture exploration (38 chips, no microcode) | Bank | ⬜ TODO |
| B-034 | KiCad schematic for RV8-R | Ohm | ⬜ TODO |

---

## Completed

| # | Task | Completed | By |
|---|------|-----------|-----|
| — | Architecture frozen v1.0 | 2026-06-14 | Bank |
| — | Programmer design finalized | 2026-06-14 | Ohm |
| — | 14 hardware labs written | 2026-06-15 | Noon |
| — | 5 Verilog TBs pass + 512-opcode sweep | 2026-06-14 | Mint + Fern |
| — | Gate-level sim 8/8 pass | 2026-06-14 | Mint |
| — | Assembler (page-safe, 18 opcodes + macros) | 2026-06-14 | Bam |
| — | Memory map swap (ROM $0000, RAM $8000) | 2026-06-15 | Bank |
| B-010 | Example ASM programs: blink, counter, echo | 2026-07-09 | Bam + Fern |
| B-013 | All-ISA dual Verilog scoreboard: behavioral vs TTL chip-level | 2026-07-10 | Mint + Fern |
