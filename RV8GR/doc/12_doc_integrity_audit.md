# RV8GR Documentation Integrity Audit

Updated: 2026-07-10

This audit checks every Markdown file under `RV8GR/doc/` against the current
CPU source of truth:

- Python CPU logic: `sim/chip_sim.py`
- Components-backed Python runner: `sim/components_chip_sim.py`
- Behavioral Verilog: `rtl/rv8gr_cpu.v`
- TTL chip-level Verilog: `rtl/rv8gr_chip_level.v`
- Four-model equivalence: `programs/all_isa_equivalence.asm`,
  `tools/check_python_verilog_equivalence.py`,
  `tools/run_dual_verilog_compare.sh`

## Why This File Exists

Keep this file as the maintainer doc-integrity signoff record. It answers:

- which documentation files were checked;
- which files are source of truth and which are derived;
- why derived docs were kept, merged, or removed;
- which verification commands support the current documentation state.

Do not use this as a student lesson or wiring guide. Students should start with
`00_design_isa.md`, `01_wiring_guide.md`, `04_understand_by_module.md`, and the
lab files. This audit is for Pim/Fern/Noon-style review work so future cleanup
does not rediscover the same decisions.

Current verified equivalence marker:

```text
Verilog checkpoint stream: 55 checkpoints
CPUSim matches Verilog checkpoint stream, final state, and RAM checkpoints
ComponentsCPUSim matches Verilog checkpoint stream, final state, and RAM checkpoints
RV8GR Python/Verilog equivalence PASS
```

## Integrity Rules Used

| Rule | Current truth |
|---|---|
| Package count | 34 logic chips + ROM + RAM = 36 packages |
| ISA | 18 frozen instructions |
| Timing model | 3 phases: T0 fetch opcode, T1 fetch operand, T2 execute |
| IRQ | Polling latch only; no hardware vector, no automatic PC save, DI inert |
| Data page | `SETDP` controls data address high byte; DP `$00-$7F` reads ROM, DP `$80-$FF` reads/writes RAM |
| Immediate path | U6 `/OE` tied LOW; U34 drives IRL to IBUS only when `/IRL_OE` is active |
| ROM output | ROM `/OE = WR_DIR`; ROM output disabled during store direction |
| ROM write | ROM `/WE` inactive during CPU runtime; programmer may drive it only in PROG/reset isolation |
| Four-model signoff | Both Python sims and both Verilog models agree on 55 exported checkpoints |

## Fixes Applied In This Pass

| Area | Files updated |
|---|---|
| ROM `/WE` wording changed from CPU `/WR` ownership to runtime-inactive/programmer-only ownership | `00_design_isa.md`, `03_bank_switch.md`, `05_debug_plan.md`, `06_kicad_modules.md`, `build_plan/01_student_incremental_build_plan.md`, `labs/lab05_rom_buffer.md`, `labs/lab12_ram_datapage.md` |
| Chip count corrected from `35` to `36 packages` | `labs/README.md`, `labs/lab13_full_system.md` |
| U6/U34 final wiring corrected | `labs/lab13_full_system.md` |
| Verilog bench count/status updated to include chip-level and dual-compare signoff | `README.md`, `08_cpu_logical_test_protocol.md`, `11_four_model_equivalence.md` |
| Four-model equivalence explained for students | `11_four_model_equivalence.md`, linked from `README.md`, `08_cpu_logical_test_protocol.md`, and `JOJOCAFE-Org/SESSION_HANDOFF.md` |
| Main numbered docs renumbered for readability | `01_wiring_guide.md` through `12_doc_integrity_audit.md`; `B-007_verification_report_2026-07-09.md` remains dated historical evidence |

## File-by-File Audit

| File | Scope | Integrity status |
|---|---|---|
| `00_design_isa.md` | Main ISA and architecture reference | Updated ROM write wording; now matches 36-package, polling IRQ, U34 immediate path, SETDP, and bus-safety truth. |
| `01_wiring_guide.md` | Official pin-level physical source | Matches current simulator truth for U6, U34, U32/U33, ROM `/OE`, ROM `/WE`, IRQ, and 36 packages. |
| `02_instruction_trace.md` | Golden debug traces for single-step student bring-up | Kept as a useful derived doc because `05_debug_plan.md` points students to it for trace comparison. Updated wording to make `00_design_isa.md`/`01_wiring_guide.md` the source of truth and to clarify ACC/DP edge-trigger timing. |
| `03_bank_switch.md` | Future ROM banking and built-in data page | Updated ROM write wording, corrected page `$7F` as ROM-only, fixed 17-bit banked-address examples, and clarified that the +1 bank latch is outside the frozen 36-package v1.0 baseline. |
| `04_understand_by_module.md` | Student module explanation | Updated to clarify that it is a module-understanding guide, not the pin-level wiring source; ring-counter reset wording now points students to the lab/debug convention while preserving the raw 74HC164 clear behavior. Corrected Z flag timing, RV8-Bus `/SLOT` examples, RAM-vs-I/O caveat, 74HC574 `/OE` wording, and gate-budget notes. Consistent with 34 logic chips, U34 immediate path, SETDP, polling IRQ, DI inert behavior, and ROM `/OE=WR_DIR`. |
| `05_debug_plan.md` | Physical debug plan | Updated ROM write wording; remains physical-build protocol, not virtual signoff. |
| `06_kicad_modules.md` | KiCad module split | Kept as a six-sheet/module guide for KiCad and student chunking, not a replacement for `01_wiring_guide.md`; module ownership matches current U1-U34 architecture. |
| `07_real_build_timing_log.md` | Physical timing evidence log template | Kept separate from `05_debug_plan.md`: debug plan tells students what to do; timing log records real-board voltage/frequency, bus-race, edge, propagation-delay, fix, and retest evidence. |
| `08_cpu_logical_test_protocol.md` | CPU logical verification protocol | Kept as the canonical virtual CPU logic regression and signoff protocol; distinct from the student four-model guide and the physical debug/timing docs. |
| `09_future_upgrades.md` | Future-only feature parking lot | Kept separate from `03_bank_switch.md`: bank switching has its own focused expansion contract, while this file parks non-baseline timing, reset, DI, I/O, and vector ideas. Updated stale chip-count and U34/IBUS wording; U34 is already part of v1.0. |
| `10_netlist.md` | Text netlist | Kept as a schematic-capture and breadboard cross-check artifact, derived from `01_wiring_guide.md`. Updated U34 power pins and IBUS driver table so the immediate path is U34-controlled, not U6-direct; remains consistent with 36 packages, U32/U33, ROM `/OE=WR_DIR`, and programmer-only ROM `/WE`. |
| `11_four_model_equivalence.md` | Student four-model guide | Kept separate from `08_cpu_logical_test_protocol.md`: this short guide answers why RV8GR has two Python sims, two Verilog models, and one shared ASM equivalence source, while the protocol doc remains the maintainer signoff checklist. Verified against `tools/check_python_verilog_equivalence.py` and the 55-checkpoint output. |
| `12_doc_integrity_audit.md` | Maintainer doc-integrity signoff record | Kept as the record of which docs were checked, which docs are source-of-truth or derived, and why each derived doc remains separate after cleanup. Not a student lesson or wiring guide. |
| `B-007_verification_report_2026-07-09.md` | Historical B-007 non-physical evidence report | Kept because backlog, sprint, handoff, and project-state files still cite B-007 as physically blocked with non-physical evidence available. Marked as historical and not current signoff; use `08_cpu_logical_test_protocol.md`, `11_four_model_equivalence.md`, `05_debug_plan.md`, and `07_real_build_timing_log.md` for current protocol. |
| `build_plan/01_student_incremental_build_plan.md` | Teacher build plan | Updated ROM `/WE`; matches 36-package baseline, U34, SETDP, IRQ polling, and physical signoff boundary. |
| `build_plan/02_student_worksheet.md` | Student worksheet | Consistent with staged build, U34, WR_DIR, SETDP, IRQ polling, boot tests, and fault map. |
| `labs/README.md` | Lab index | Chip checklist heading corrected to 36 packages. |
| `labs/lab01_power_clock.md` | Power and manual clock | Consistent with rising-edge/manual-clock build assumptions. |
| `labs/lab02_ring_counter.md` | T0/T1/T2 timing | Consistent with one-hot 3-phase model. |
| `labs/lab03_pc_counter.md` | Program counter | Consistent with PC increment/load staging. |
| `labs/lab04_address_mux.md` | Address mux | Consistent with PC vs IRL/DP address selection and `/ADDR_MODE` notes. |
| `labs/lab05_rom_buffer.md` | ROM and U7 buffer | Updated ROM `/WE` programmer-only note; U7 direction remains correct. |
| `labs/lab06_ir_latch.md` | IR high/low latch | Consistent: U6 output differs between isolated lab simplification and final U34-controlled CPU path. |
| `labs/lab07_alu.md` | Adder/subtractor | Consistent with ADD/SUB/XOR building blocks and no overflow flag. |
| `labs/lab08_accumulator.md` | AC, mux, U14 buffer | Consistent with AC feedback, U14 bus isolation, and ALU mux. |
| `labs/lab09_z_flag.md` | Z flag | Consistent with current async preset Z behavior and branch use. |
| `labs/lab10_branch_jump.md` | Branch/jump control | Consistent with absolute page/low-byte branch behavior, `/PC_LD`, and SETDP/EI decode helper gates. |
| `labs/lab11_page_register.md` | Page register | Consistent with SETPG and `{PG, IRL}` jump target formation. |
| `labs/lab12_ram_datapage.md` | RAM and data page | Updated ROM write wording; SETDP, RAM/ROM split, and alias behavior remain consistent. |
| `labs/lab13_full_system.md` | Full-system lab | Corrected final U6/U34 wiring and chip-count heading; full-system tests remain aligned with simulator truth. |
| `labs/lab14_irq_bus.md` | IRQ and RV8-Bus | Consistent with polling IRQ, sticky IRQ_FF, DI inert behavior, and no hardware vector. |

## Non-Markdown Artifact

No packaged doc archive is used for now. Markdown files under `RV8GR/doc/`
remain the editable source of truth.

## Latest Verification Commands

Run from `/home/jo/kiro/RV8`:

```bash
python3 -B RV8GR/tools/check_python_verilog_equivalence.py
python3 -B RV8GR/sim/verify_wiring.py
python3 -B RV8GR/sim/verify_components.py
python3 -B RV8GR/tools/test_rv8gr_asm.py
git diff --check
```

Run from `/home/jo/kiro/RV8/RV8GR` for full HDL regression:

```bash
tools/run_all_verilog_tb.sh
```

Physical build signoff still requires real voltage, clock, edge, bus-ownership,
propagation-delay, and logic-analyzer/scope evidence.
