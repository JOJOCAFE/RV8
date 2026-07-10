# RV8GR Future Upgrades Parking Lot (v1.1 / v2.0)

Ideas extracted from the RV8GR-Codex experimental branch (June 2026).
These require additional chips and are **not** part of the v1.0 frozen design (36 packages).

This document is not a build guide and not a pin-level source of truth. Use:

- `00_design_isa.md` for frozen ISA and CPU behavior.
- `01_wiring_guide.md` for exact v1.0 chip wiring.
- `03_bank_switch.md` for the ROM bank-switch expansion contract.
- `07_real_build_timing_log.md` for real-board timing evidence.

Keep future ideas here only when they would distract from the student baseline.
Move an idea into the wiring guide only after it has a complete chip budget,
pin plan, simulation/test coverage, and physical timing evidence.

---

## v1.1: Timing Hardening (+1–2 chips)

### Clock-Qualified /WR Pulse
- **Problem**: Current /WR = direct from /AC_BUF during T2. If propagation delays vary, the write pulse may glitch.
- **Solution**: Gate /WR with CLK to produce a clean half-cycle write pulse: `/WR = NOT(T2 AND STORE AND CLK)`.
- **Cost**: 1 spare gate (may fit in existing U26/U28)
- **Risk**: Low — only affects RAM write timing, easy to verify with scope.

### DS1813-5+ Reset Supervisor
- **Problem**: RC reset is unreliable — slow VCC ramp can leave FFs in unknown states.
- **Solution**: Replace RC circuit with DS1813-5+ (active-low /RST, 150ms hold, 5V threshold).
- **Cost**: 1 component (not a logic chip), replaces RC network.
- **Risk**: None — drop-in, no wiring change.

---

## v1.1: Hardware DI (extra decode logic)

### Background
- Current v1.0: DI ($48) is a NOP — IE can only be cleared by /RST.
- This keeps the 36-package build simple, but limits flexibility.

### Proposal
- Add DI decode: `DI_decode = T2 & SUB & /XOR & /AC_WR & SRC` → fires on $48.
- Wire DI_decode to U31 IE_FF /CLR (active-low clear).
- **Cost**: Requires extra decode resources because U33 gate 2 is already used by EI.
- **Constraint**: Do not fold this into the 36-package baseline without re-checking the wiring guide and BOM.

---

## v2.0: Full Clock Qualification (+1 chip)

### Problem
All control signals (from U5 IR_HIGH) are valid throughout T2, but the RAM /WR and latch clocks fire on raw T-state transitions. A slow ROM could cause a race.

### Solution
- Add U40 (74HC08 AND4): qualify all write-enable signals with CLK.
- `PG_LOAD_Q = PG_LOAD AND CLK`
- `DP_LOAD_Q = DP_LOAD AND CLK`
- `AC_LOAD_Q = AC_WR AND T2 AND CLK`
- `RAM_WR_Q = STORE AND T2 AND CLK`

### Cost
- 1 × 74HC08 (quad AND), uses all 4 gates.
- Outside the frozen 34-logic-chip / 36-package v1.0 baseline.
- Requires a new chip budget and full re-verification before becoming real wiring.

### Risk
- Medium — changes timing of every register load. Requires full re-verification.
- Not needed at 1 MHz (700ns+ margin), may be needed at 5 MHz on PCB.

---

## v2.0: I/O Decode (+2–3 chips)

### Memory-Mapped I/O Ports
- Reserve $FF10-$FF1F for I/O status/data.
- Add address decode: `IO_SEL = A15 & A14 & A13 & A12 & A11 & A10 & A9 & A8 & A4`.
- Requires: 1 × 74HC688 (address compare) + 1 × 74HC138 (device select).
- **Cost**: +2 chips (35 total).

### IRQ Status Register
- Read $FF10 → returns {7'b0, IRQ_FF} so ISR can poll which device interrupted.
- Allows multi-device IRQ without dedicated acknowledge pins.

For the reserved ROM bank register address and expansion-board rules, see
`03_bank_switch.md`. Do not duplicate the bank-switch wiring here.

---

## v2.0: Hardware Save-PC on IRQ (+2 chips)

### Problem
v1.0 requires ISR to save PC via software (read $0E/$0F). This wastes cycles and requires the behavioral model to pre-save.

### Solution
- On IRQ, latch PC into a dedicated 16-bit register before vectoring to $FF00.
- ISR reads the saved-PC register instead of RAM.
- **Cost**: 2 × 74HC574 (16-bit latch), +2 chips.
- **Benefit**: Clean ISR entry without software overhead.

---

## Already Resolved In v1.0: IBUS Buffer Separation

U6 is only the IR_LOW latch. Its outputs remain enabled to feed PC load,
address mux inputs, and U34 inputs. U34 (74HC541) is the controlled
IRL-to-IBUS buffer; `/IRL_OE` enables U34 only for immediate-style T2 cycles.

- **Benefit**: Cleaner bus ownership; U6 never directly drives IBUS.
- **Status**: Already included in the frozen v1.0 36-package baseline.
- **Action**: No future-upgrade work remains here unless a later design changes
  the immediate path again.

---

## Summary

| Upgrade | Chips Added | Priority | When |
|---------|:-----------:|:--------:|:----:|
| DS1813-5+ reset | 0 (component) | HIGH | v1.0 BOM option |
| Clock-qualified /WR | 0 (spare gate) | MEDIUM | v1.1 if glitch seen |
| Hardware DI ($48) | TBD extra decode | LOW | v1.1 |
| Full clock qualification | +1 | LOW | v2.0 / PCB only |
| I/O decode | +2 | MEDIUM | v2.0 |
| Hardware save-PC | +2 | LOW | v2.0 |
| ROM bank switch | +1 on expansion board | MEDIUM | v2.x; see `03_bank_switch.md` |
| IBUS buffer | 0 | DONE | Already in v1.0 as U34 |

**None of these are required for the v1.0 breadboard build.** The current 36-package design is verified and sufficient at 1 MHz.
