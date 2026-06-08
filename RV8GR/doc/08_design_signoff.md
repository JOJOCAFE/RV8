# RV8-GR — Design Sign-off v1.0

**32 chips. 18 instructions. 64KB. No microcode. Hardware Design Frozen.**

---

## Architecture

```
Opcode = Control Word (no decoder, no microcode ROM)
18 instructions, 3 cycles each, 3.3 MIPS @ 10 MHz
64KB code + 64KB data access, IRQ, 40-pin system bus
```

---

## Sign-off Checklist

| Category | Status |
|----------|:------:|
| Datapath (Verilog 127+160 cycles) | ✅ |
| ISA (18 instructions) | ✅ |
| SETDP decode (U33 pin-level) | ✅ |
| IRQ entry ($FF00, software save-PC) | ✅ |
| Memory Map (no address conflicts) | ✅ |
| Bus guard SRC+STR (U25-8) | ✅ |
| Opcode hazard (256 codes deterministic) | ✅ |
| Timing @ 10 MHz | ✅ |
| RV8-Bus (40-pin defined) | ✅ |
| BOM finalized | ✅ |
| Programmer tools (46 tests) | ✅ |
| Documentation (10 docs synced) | ✅ |
| Pin-level wiring verified | ✅ |

---

## Metrics

| Metric | Value |
|--------|-------|
| Logic chips | 32 |
| Total packages | 34 (+ ROM + RAM) |
| Instructions | 18 (+NOT free, +$C0 alias) |
| Gate count | ~1,260 |
| Opcode space | 7% used, 68% expansion |
| Data access | 64KB (SETDP) |
| System bus | 40-pin |
| Forbidden opcodes | 64 (guarded) |
| Testbenches | 4 (full, IRQ, tasks, SETDP) |

---

## Memory Map (Final)

```
$0000-$7FFF  RAM 32KB (read/write)
$8000-$FEFF  ROM 32KB
$FF00-$FF0F  ROM: IRQ vector
$FF10-$FF1F  I/O Slot 1
$FF20-$FF2F  I/O Slot 2
$FF30-$FFFF  ROM: ISR code
```

---

## Open Items (v2.0)

| # | Item | Notes |
|:-:|------|-------|
| 1 | IRQ hardware save-PC | +2-3 chips |
| 2 | NOT instruction in assembler | 0 chips |
| 3 | I/O slot decode board | +1 chip (74HC138) |
| 4 | RTI instruction | Design TBD |

---

## Sign-off

```
RV8-GR v1.0: 32-chip horizontal-control CPU
- Full 64KB code + data
- All 256 opcodes deterministic
- Electrical hazard eliminated
- Pin-level wiring verified
- Ready for physical build

Hardware Design Frozen.
```

*Date: 2026-06-09*
*Chips: U1-U33 (32 logic + ROM + RAM)*
*Guard: BUF_OE_SAFE (U25-8 → U7-19)*
*Bus: RV8-Bus v2 (40-pin, Slot1=$FF10, Slot2=$FF20)*
*IRQ: $FF00 (software save-PC for v1.0)*
