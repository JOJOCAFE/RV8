# RV8-GR — Design Sign-off v1.0

**Horizontal-control 8-bit CPU. 31 chips. 32KB RAM. Deterministic. Ready for build.**

---

## Architecture

```
Opcode = Control Word (no decoder)
18 instructions, 3 cycles each, 3.3 MIPS @ 10 MHz
64KB address, 32KB data RAM, IRQ, 40-pin system bus
```

---

## Sign-off Checklist

| Category | Status |
|----------|:------:|
| Datapath correctness | ✅ Verilog 127 cycles |
| ISA (17 instructions) | ✅ All verified |
| IRQ | ✅ 6 tests pass |
| Memory Map | ✅ ROM $8000+, RAM $0000+ |
| Timing @ 10 MHz | ✅ All paths safe |
| Bus guard (SRC+STR) | ✅ Applied |
| Opcode hazard (256 codes) | ✅ All deterministic |
| SETDP decode | ✅ No conflict with SETPG/DI |
| ALU modes (8 modes) | ✅ All deterministic |
| RV8-Bus (40-pin) | ✅ Defined |
| Signal integrity | ✅ Cable <30cm |
| BOM | ✅ Finalized |
| Programmer tools | ✅ 46 tests pass |
| Documentation | ✅ 9 docs complete |

---

## Action Items

| # | Action | Status |
|:-:|--------|:------:|
| 1 | SRC+STR guard | ✅ Done |
| 2 | Route CLK + /IRQ to bus | ⬜ At build time |
| 3 | I/O slot decode | ⬜ Optional (1× 74HC138) |
| 4 | Add NOT to assembler | ⬜ Optional |

---

## Metrics

| Metric | Value |
|--------|-------|
| Logic chips | 31 |
| Instructions | 18 (+ NOT free) |
| Opcode space used | 6.6% |
| Expansion room | 68.4% |
| System bus | 40-pin (A16+D8+CLK+ctrl) |
| Max cable | 30cm @ 10MHz |
| Forbidden opcodes | 64 (blocked by guard) |
| Hardware changes | 1 wire (done) |

---

## Opcode Space

```
     0 1 2 3 4 5 6 7 8 9 A B C D E F
$0x [N J B . S . . . E . . . ⛔⛔⛔⛔]
$1x [A A . . . . . . . . . . ⛔⛔⛔⛔]
$2x [P P . . . . . . . . . . ⛔⛔⛔⛔]
$3x [L L . . . . . . . . . . ⛔⛔⛔⛔]
$4x [. D . . . . . . . . . . ⛔⛔⛔⛔]
$7x [X X . . . . . . . . . . ⛔⛔⛔⛔]
$8x [. . B . . . . . . . . . ⛔⛔⛔⛔]
$9x [S S . . . . . . . . . . ⛔⛔⛔⛔]
$Bx [★ ★ . . . . . . . . . . ⛔⛔⛔⛔]  ★=NOT (free)
```

---

## Final Statement

```
RV8-GR: 30-chip horizontal-control CPU
- All 256 opcodes produce deterministic behavior
- Single electrical hazard eliminated by spare gate
- 68% opcode space available for expansion at 0 cost
- 40-pin bus enables full computer system

Signed off for physical build.
```

*Date: 2026-06-09*
*Design: RV8-GR v1.0*
*Guard: BUF_OE_SAFE = BUF_OE_N OR STR (U25-8 → U7-19)*
*Bus: RV8-Bus v2 (40-pin)*
