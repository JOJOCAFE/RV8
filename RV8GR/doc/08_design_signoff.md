# RV8-GR — Design Sign-off v1.0

**36 packages. 18 instructions. 64KB. No microcode. Hardware Design Frozen.**

---

## Architecture

```
Opcode = Control Word (no decoder, no microcode ROM)
18 instructions, 3 cycles each
333K instructions/sec @ 1 MHz (breadboard)
1.67M instructions/sec @ 5 MHz (PCB future)
64KB code + 64KB data access, IRQ, 40-pin system bus
```

---

## Sign-off Checklist

| Category | Status |
|----------|:------:|
| Datapath (Verilog 127+160 cycles) | ✅ |
| ISA (18 instructions) | ✅ |
| SETDP decode (U33 pin-level) | ✅ |
| IRQ polling latch, no hardware vector | ✅ |
| Memory Map (no address conflicts) | ✅ |
| Store bus safety (ROM /OE=WR_DIR) | ✅ |
| Opcode hazard (256 codes deterministic) | ✅ |
| Timing @ 1 MHz (700ns+ margin) | ✅ |
| RV8-Bus (40-pin defined) | ✅ |
| BOM finalized | ✅ |
| Assembler tools (11 tests) | ✅ |
| Documentation (27 Markdown docs synced) | ✅ |
| Pin-level wiring verified | ✅ |

---

## Metrics

| Metric | Value |
|--------|-------|
| Logic chips | 34 |
| Total packages | 36 (34 logic + ROM + RAM) |
| Instructions | 18 (+NOT free, +$C0 alias) |
| Gate count | ~1,260 |
| Opcode space | 7% used, 68% expansion |
| Data access | 64KB (SETDP) |
| System bus | 40-pin |
| Forbidden opcodes | 64 (guarded) |
| Testbenches | 9 in `run_all_verilog_tb.sh` (behavioral, opcode sweep, SETDP, tasks, IRQ, chip-level, full chip-level, dual compare) |

---

## Memory Map (Final)

```
$0000-$7EFF  ROM 32KB (read only)
$7F00-$7FFF  ROM (available)
$8000-$FEFF  RAM 32KB (read/write)
$FF00-$FF0F  RAM: available; future vector area
$FF10-$FF1F  I/O Slot 1
$FF20-$FF2F  I/O Slot 2
$FF30-$FFFF  RAM (available)
```

---

## Known Risks (from architecture review)

| # | Risk | Severity | Mitigation |
|:-:|------|:--------:|------------|
| 1 | ROM timing after data-access instruction (LB/SB/ADD/SUB/XOR) | 🟡 | Start at 1-2 MHz, step up to 5 MHz. PC stable during T2 ensures correctness. |
| 2 | IRQ return burden on programmer | 🟡 | v1.0 uses software save/restore. v2.0 adds RTI (+2-3 chips). |
| 3 | SB to ROM address ignored | 🟢 | By design: ROM `/WE` stays inactive during CPU runtime; programmer ownership is PROG/reset-only. |

### Timing Verification Plan

After physical build, verify with incremental clock speed:

```
Step 1: 1 MHz   — official target, verify all instructions
Step 2: 2 MHz   — verify timing-critical sequences (LB then ADD)
Step 3: 5 MHz   — experimental (PCB only), verify if achievable
```

Critical sequence to test: **two consecutive data-access instructions**
(e.g., `LB $03` followed by `ADD $04`) where /ADDR_MODE switches back
to PC late. If this works at 5 MHz with 70ns ROM → design is proven.

---

## Open Items (v2.0)

| # | Item | Notes |
|:-:|------|-------|
| 1 | RTI instruction (hardware save-PC on IRQ) | +2-3 chips |
| 2 | NOT instruction in assembler | 0 chips (alias $B0/$B8) |
| 3 | I/O slot decode board | +1 chip (74HC138) |
| 4 | High-speed option (10 MHz) | Needs breadboard timing proof |

---

## Sign-off

```
RV8-GR v1.0: 36-package horizontal-control CPU
- Full 64KB code + data
- All 256 opcodes deterministic
- Electrical hazard eliminated
- Pin-level wiring verified
- Ready for physical build

Hardware Design Frozen.
```

### Status Levels

| Domain | Status | Evidence |
|--------|:------:|----------|
| Architecture | 🔒 FROZEN | Design ISA + Wiring Guide signed off |
| ISA | 🔒 FROZEN | 18 instructions, opcode allocation locked |
| Wiring | 🔒 FROZEN | Pin-level wiring guide, gate-level sim |
| Simulation | ✅ PASS | Python CPU sims, Components-backed CPU sim, 55-checkpoint Python/Verilog equivalence, full Verilog suite, assembler tests |
| Physical Build | ⏳ PENDING | Breadboard bring-up not started |
| 1 MHz | ✅ VERIFIED (analysis) | 700ns+ margin proven by timing calculation |
| 5 MHz | ⏳ PROJECTED | Timing analysis only — needs oscilloscope proof |
| 256 opcodes | ✅ DETERMINISTIC | 512-case opcode sweep (256 opcodes × Z=0/1) |

### Remaining Proof (before "Production Proven")

```
□ Breadboard bring-up (06_debug_plan steps 1-14)
□ Golden Bring-up Program passes at 1 MHz
□ Burn-in 1 hour stable
□ Clock sweep: record actual max frequency
☑ 256-opcode sweep testbench (512 cases)
□ Run 5+ real programs (monitor, blink, counter, game, BASIC stub)
```

*Date: 2026-06-09*
*Chips: U1-U34 (34 logic) + ROM + RAM = 36 packages*
*Store safety: U7 /OE=BUF_OE_N, ROM /OE=WR_DIR*
*Bus: RV8-Bus v2 (40-pin, Slot1=$FF10, Slot2=$FF20)*
*IRQ: v1.0 polling (IRQ_FF latch, cleared by /RST only). Hardware vector is future/unfrozen.*
