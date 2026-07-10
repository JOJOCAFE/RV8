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
| ROM `/WE` wording changed from CPU `/WR` ownership to runtime-inactive/programmer-only ownership | `00_design_isa.md`, `04_bank_switch.md`, `06_debug_plan.md`, `08_design_signoff.md`, `10_kicad_modules.md`, `build_plan/01_student_incremental_build_plan.md`, `labs/lab05_rom_buffer.md`, `labs/lab12_ram_datapage.md` |
| Chip count corrected from `35` to `36 packages` | `labs/README.md`, `labs/lab13_full_system.md` |
| U6/U34 final wiring corrected | `labs/lab13_full_system.md` |
| Verilog bench count/status updated to include chip-level and dual-compare signoff | `08_design_signoff.md` |
| Four-model equivalence explained for students | `13_four_model_equivalence.md`, linked from `README.md`, `11_cpu_logical_test_protocol.md`, and `JOJOCAFE-Org/SESSION_HANDOFF.md` |

## File-by-File Audit

| File | Scope | Integrity status |
|---|---|---|
| `00_design_isa.md` | Main ISA and architecture reference | Updated ROM write wording; now matches 36-package, polling IRQ, U34 immediate path, SETDP, and bus-safety truth. |
| `02_wiring_guide.md` | Official pin-level physical source | Matches current simulator truth for U6, U34, U32/U33, ROM `/OE`, ROM `/WE`, IRQ, and 36 packages. |
| `03_instruction_trace.md` | Golden debug traces for single-step student bring-up | Kept as a useful derived doc because `06_debug_plan.md` points students to it for trace comparison. Updated wording to make `00_design_isa.md`/`02_wiring_guide.md` the source of truth and to clarify ACC/DP edge-trigger timing. |
| `04_bank_switch.md` | Future ROM banking and built-in data page | Updated ROM write wording, corrected page `$7F` as ROM-only, fixed 17-bit banked-address examples, and clarified that the +1 bank latch is outside the frozen 36-package v1.0 baseline. |
| `05_understand_by_module.md` | Student module explanation | Updated to clarify that it is a module-understanding guide, not the pin-level wiring source; ring-counter reset wording now points students to the lab/debug convention while preserving the raw 74HC164 clear behavior. Corrected Z flag timing, RV8-Bus `/SLOT` examples, RAM-vs-I/O caveat, 74HC574 `/OE` wording, and gate-budget notes. Consistent with 34 logic chips, U34 immediate path, SETDP, polling IRQ, DI inert behavior, and ROM `/OE=WR_DIR`. |
| `06_debug_plan.md` | Physical debug plan | Updated ROM write wording; remains physical-build protocol, not virtual signoff. |
| `07_risk_analysis.md` | Risk and mitigation notes | Consistent with store bus contention fix, SETDP/SETPG separation, IRQ polling, and future-vector boundary. |
| `08_design_signoff.md` | Design signoff snapshot | Updated current simulation status and bench count to include four-model equivalence and chip-level dual compare. |
| `09_task_test_plan.md` | Task-by-task test plan | Consistent with current Components verification count, boot sequence, SETDP, IRQ, and opcode sweep. |
| `10_kicad_modules.md` | KiCad module split | Updated ROM `/WE`; module ownership still matches current U1-U34 architecture. |
| `10_real_build_timing_log.md` | Physical timing evidence log template | Reviewed as physical-test planning; left untouched because it is untracked user/build evidence. |
| `11_cpu_logical_test_protocol.md` | CPU logical verification protocol | Current four-model 55-checkpoint equivalence documented. |
| `11_future_upgrades.md` | Future-only features | Consistent: hardware DI, vectoring, reset supervisor, and I/O decode remain outside v1.0. |
| `12_netlist.md` | Text netlist | Consistent with 36 packages, U34, U32/U33, ROM `/OE=WR_DIR`, and programmer-only ROM `/WE`. |
| `13_four_model_equivalence.md` | Student four-model guide | New; explains two Python sims, two Verilog models, shared ASM source, and 55-checkpoint equivalence. |
| `B-007_verification_report_2026-07-09.md` | Historical non-physical report | Kept as historical. Some command/status details are older than the current four-model checkpoint work; do not use it as latest signoff without the newer protocol docs. |
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

| File | Status |
|---|---|
| `RV8GR-Doc.zip` | Regenerated from the current Markdown set on 2026-07-10. Archive contains 34 Markdown files including the CPU logical protocol, four-model equivalence guide, integrity audit, and updated student/module docs. Markdown files remain the editable source of truth. |

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
