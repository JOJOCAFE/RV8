# RV8GR Phase-Trace Alignment Findings

**Status:** observation-only finding for the software differential lane.  This
does not change production RTL, wiring, or physical-timing claims.

## Finding

The apparent IE and DP mismatches in the first settled JSONL trace are a
**trace phase-mapping error**, not a behavioural-versus-chip-level RTL
divergence.

`rv8gr_cpu.state` is the **next phase to execute** after the rising edge.  The
chip-level `n_T0/n_T1/n_T2` lines are the hardware phase asserted after that
edge.  In the current post-edge `#150` observation convention, their raw
labels are therefore offset:

| Behavioural raw `state` | Completed behavioural action | Canonical settled sample |
| --- | --- | --- |
| `T1` | fetched control byte at T0 | `T0-settled` |
| `T2` | fetched operand byte at T1 | `T1-settled` |
| `T0` | executed the instruction at T2 | `T2-settled` |

The canonical trace adapter must retain `raw_next_phase` for debugging, but
must use the last column for cross-model phase comparison.  It compares the
behavioural raw-`T0` record with the chip-level `n_T2=1` record from the same
settled clock sample.  It must not compare raw behavioural `T2` with physical
`T2`.

## IE at records 87/88

At program address `$0044`, the control byte is `$28` (`SETPG_R $04`).  Its
physical bits are `SRC=1`, `XOR_MODE=0`, and `AC_WR=0`.  At T2, U33 gate 2
therefore asserts:

```text
EI_decode = T2 & SRC & /XOR_MODE & /AC_WR = 1
```

This is wired to U31's IE clock.  The behavioural RTL implements the same
equation as `is_ei = source_type & ~xor_mode & ~ac_wr`; the chip RTL wires U33
to U31.  The trace shows the expected committed result at cycle 88:

```text
behavioural raw T2, cycle 87: IE=0   (T2 has not committed yet)
behavioural raw T0, cycle 88: IE=1   (T2 committed)
chip T2,              cycle 88: IE=1
```

Thus this is not an RTL mismatch.  It does expose a separate ISA/documentation
question: `$28` has the physical EI side effect under the declared U33 gate-2
equation, although the opcode table names it `SETPG_R`.  The software lane
must preserve this as observed behaviour unless the architecture explicitly
changes the decode or declares the side effect an ISA bug.

## DP at records 123/124 and 144/145

The two pairs are `SETDP $90` at `$0066` and `SETDP $00` at `$0076`.
For `$40`, T2 produces:

```text
DP_Load = T2 & XOR_MODE & /ADDR_MODE & /AC_WR = 1
```

The behavioural RTL uses the matching `is_setdp` expression; chip U33 gate 1
clocks U32.  The relevant settled results are:

```text
cycle 123: behavioural raw T2, DP=80; chip T1, DP=80
cycle 124: behavioural raw T0, DP=90; chip T2, DP=90

cycle 144: behavioural raw T2, DP=90; chip T1, DP=90
cycle 145: behavioural raw T0, DP=00; chip T2, DP=00
```

Again, the change is visible at the common completed-T2 boundary.  There is no
observed behavioural/chip-level divergence in DP.

## Comparator requirement

For the current `#150` settled post-edge RTL trace:

1. write both raw phase observations and the mapping version into the trace
   manifest;
2. map behavioural raw states `T1/T2/T0` to canonical `T0/T1/T2` respectively;
3. compare architectural fields only after that mapping; and
4. separately flag opcode side effects such as `$28 -> IE=1` as an ISA/decoder
   characterization result, not as a phase mismatch.

Source evidence: `rtl/rv8gr_cpu.v` (state transition, `is_ei`, `is_setdp`),
`rtl/rv8gr_chip_level.v` (U31/U32/U33 connections),
`doc/00_design_isa.md` (U33 equations), and
`programs/all_isa_equivalence.asm` (addresses `$0044`, `$0066`, `$0076`).
