# RV8GR Reserved / Non-ISA Opcode Characterization

`tools/characterize_reserved_opcodes.py` is the executable record for the
horizontal control bytes not allocated to the v1.0 ISA.  It does **not** call
them NOPs and does not turn their deterministic implementation behavior into
an architectural promise.

For each non-ISA control byte and each selected operand it:

1. initializes a defined CPU state with `DP=$80`, `AC=$A5`, `PG=$3C`, and a
   known RAM byte at the actual data address `$80<operand>`;
2. loads the actual two-byte program at ROM `$0000`;
3. advances through T0 fetch, T1 operand fetch, and T2 execute;
4. records PC, AC, Z, PG, DP, IE, IRQ, and the RAM target before/after;
5. compares CPUSim with the Components-backed chip adapter; and
6. writes a replayable `.bin` image and JSONL record below `/tmp`.

Run the full current corpus:

```bash
python3 tools/characterize_reserved_opcodes.py
```

The shell exit status fails on a CPUSim/ComponentsCPUSim disagreement.  This
is adapter compatibility evidence only: the two paths share the CPUSim
execution semantics, so it is not independent ISA or physical-hardware proof.
The separate RTL phase-trace and dual-RTL benches remain required evidence.

The default operands `$00` and `$5A` deliberately exercise both a neutral and
a data-page RAM-addressable operand.  The generated `summary.json` reports
the exact corpus counts, including store-dominant `SRC+STR` control bytes.
