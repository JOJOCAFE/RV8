# Docs Writer Memory

## Labs Written

| # | Title | Status |
|---|-------|--------|
| 01-14 | Hardware labs (Thai, มัธยมต้น level) | ✅ done |

## Document Inventory

| Doc | Purpose |
|-----|---------|
| `00_design_isa.md` | Design + ISA reference |
| `02_instruction_trace.md` | Step-by-step execution trace |
| `03_wiring_guide.md` | Pin-level wiring (SOURCE OF TRUTH) |
| `04_bank_switch.md` | Data page / bank switching |
| `05_understand_by_module.md` | Thai tutorial by module |
| `06_debug_plan.md` | 14-step physical build plan |
| `07_risk_analysis.md` | 11 hazards analyzed |
| `08_design_signoff.md` | Architecture frozen |
| `09_task_test_plan.md` | Test milestones |

## Style Reminders

- Thai primary, English for tech terms
- Pin numbers in EVERY wire reference
- Full chip name on first mention: "U7 (74HC86, Quad XOR)"
- One concept per lab
- Lab structure: เป้าหมาย → ความรู้พื้นฐาน → อุปกรณ์ → ผังวงจร → ขั้นตอน → ทดสอบ → เช็คลิสต์

## Pending

- Update labs if physical build reveals wiring issues
- RV8-R documentation (when design starts)
- Example program walkthroughs for students
- Keep future Components simulator docs aligned with the backend contract: 64 inputs (`IN0..IN63`), 8 clocks (`CLK0..CLK7`), pin-number/name access, edge-aware clocks, ROM/RAM image loading, and deferred probes.
