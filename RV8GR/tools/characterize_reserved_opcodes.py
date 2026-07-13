#!/usr/bin/env python3
"""Characterize every RV8GR non-ISA control byte by executing a real fetch.

This is deliberately a *characterization* tool, not an ISA extension or a
NOP test.  Each case loads ``opcode, operand`` at address zero and advances
the CPU through T0, T1, and T2.  It records the resulting architectural state
and RAM changes for CPUSim and its Components-backed chip adapter.  A mismatch
is a failing test; matching results establish only adapter compatibility, not
independent ISA proof.

Artifacts are replayable and default to ``/tmp/rv8gr-reserved-opcodes``:

* ``cases.jsonl`` -- one complete end-to-end record per opcode/operand case;
* ``summary.json`` -- exact coverage and result; and
* ``programs/<opcode>-<operand>.bin`` -- each two-byte instruction image.

Undefined opcodes are never called NOPs.  The report records *all observed*
PC, AC, Z, PG, DP, IE, IRQ, and RAM effects, including no-change cases.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))

from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402
from rv8gr_asm import OPCODES  # noqa: E402


SCHEMA = "rv8gr.reserved-opcode-characterization@1"
ARCHITECTURAL_FIELDS = ("pc", "ac", "z", "pg", "dp", "ie", "irq", "irq_n")
def isa_control_bytes() -> set[int]:
    """Return actual one-byte ISA encodings, excluding assembler-only macros."""
    return {opcode for opcode in OPCODES.values() if isinstance(opcode, int)}


def reserved_control_bytes() -> list[int]:
    defined = isa_control_bytes()
    return [opcode for opcode in range(256) if opcode not in defined]


def state(sim: CPUSim) -> dict[str, int]:
    return {
        "pc": sim.pc,
        "ac": sim.ac,
        "z": sim.z_flag,
        "pg": sim.page_reg,
        "dp": sim.data_page,
        "ie": sim.ie,
        "irq": sim.irq_ff,
        "irq_n": sim.irq_n,
    }


def initialise(sim: CPUSim, opcode: int, operand: int) -> bytes:
    """Set a defined, data-page RAM-visible start state for one instruction."""
    program = bytes((opcode, operand))
    sim.load_rom(program)
    sim.pc = 0
    sim.phase = 0
    sim.clock = 0
    sim.ir_high = 0
    sim.ir_low = 0
    sim.ac = 0xA5
    sim.z_flag = 0
    sim.page_reg = 0x3C
    sim.data_page = 0x80
    sim.ie = 0
    sim.irq_ff = 0
    sim.irq_n = 1
    # `DP=$80` makes the selected data address `$80<operand>`.  Seeding that
    # exact byte makes store effects observable for every operand, including
    # `$00`; a single fixed RAM probe would miss half the default corpus.
    sim.chips["RAM"]._data[operand] = 0x5E
    return program


def changes(before: dict[str, int], after: dict[str, int]) -> dict[str, dict[str, int]]:
    return {
        name: {"before": before[name], "after": after[name]}
        for name in ARCHITECTURAL_FIELDS
        if before[name] != after[name]
    }


def execute_case(opcode: int, operand: int) -> dict[str, Any]:
    baseline = CPUSim()
    components = ComponentsCPUSim()
    program = b""
    starts: dict[str, dict[str, int]] = {}
    finishes: dict[str, dict[str, int]] = {}
    ram_before: dict[str, int] = {}
    ram_after: dict[str, int] = {}
    ram_address = 0x8000 | operand
    phase_trace: dict[str, list[dict[str, int]]] = {}

    for name, sim in (("cpusim", baseline), ("components_cpusim", components)):
        program = initialise(sim, opcode, operand)
        starts[name] = state(sim)
        ram_before[name] = sim.chips["RAM"]._data[operand]
        trace = [{"clock": sim.clock, "phase": sim.phase, **state(sim)}]
        # This is real fetch/execute: T0 latches opcode, T1 latches operand,
        # T2 executes decoded control bits.  Do not shortcut to T2.
        for _ in range(3):
            sim.step()
            trace.append({"clock": sim.clock, "phase": sim.phase, **state(sim)})
        phase_trace[name] = trace
        finishes[name] = state(sim)
        ram_after[name] = sim.chips["RAM"]._data[operand]

    equal = finishes["cpusim"] == finishes["components_cpusim"] and ram_after["cpusim"] == ram_after["components_cpusim"]
    control = {
        "sub": (opcode >> 7) & 1, "xor": (opcode >> 6) & 1,
        "mux": (opcode >> 5) & 1, "ac_wr": (opcode >> 4) & 1,
        "src": (opcode >> 3) & 1, "str": (opcode >> 2) & 1,
        "br": (opcode >> 1) & 1, "jmp": opcode & 1,
    }
    return {
        "schema": SCHEMA,
        "kind": "reserved_non_isa_control_byte",
        "opcode": f"{opcode:02X}",
        "operand": f"{operand:02X}",
        "program_bytes": [opcode, operand],
        "full_fetch_execute_steps": 3,
        "classification": "store_dominant_mixed" if opcode & 0x0C == 0x0C else "undefined_safe",
        "control_bits": control,
        "no_nop_claim": True,
        "independent_isa_proof": False,
        "comparison": "CPUSim versus ComponentsCPUSim adapter compatibility",
        "equal": equal,
        "cpusim": {
            "start": starts["cpusim"], "end": finishes["cpusim"],
            "state_changes": changes(starts["cpusim"], finishes["cpusim"]),
            "ram": {"address": f"{ram_address:04X}", "before": ram_before["cpusim"], "after": ram_after["cpusim"]},
            "phase_trace": phase_trace["cpusim"],
        },
        "components_cpusim": {
            "start": starts["components_cpusim"], "end": finishes["components_cpusim"],
            "state_changes": changes(starts["components_cpusim"], finishes["components_cpusim"]),
            "ram": {"address": f"{ram_address:04X}", "before": ram_before["components_cpusim"], "after": ram_after["components_cpusim"]},
            "phase_trace": phase_trace["components_cpusim"],
        },
        "replay_program": list(program),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operands", default="00,5A", help="Comma-separated byte values (default: 00,5A).")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/rv8gr-reserved-opcodes"))
    args = parser.parse_args()
    try:
        operands = [int(value.strip(), 16) for value in args.operands.split(",") if value.strip()]
    except ValueError as exc:
        parser.error(f"--operands expects hexadecimal bytes: {exc}")
    if not operands or any(not 0 <= value <= 0xFF for value in operands):
        parser.error("--operands must contain one or more bytes in 00..FF")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    programs = args.out_dir / "programs"
    programs.mkdir(exist_ok=True)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with (args.out_dir / "cases.jsonl").open("w", encoding="utf-8") as handle:
        for opcode in reserved_control_bytes():
            for operand in operands:
                record = execute_case(opcode, operand)
                records.append(record)
                (programs / f"{opcode:02X}-{operand:02X}.bin").write_bytes(bytes(record["replay_program"]))
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                if not record["equal"]:
                    failures.append(record)

    store_dominant = sum(1 for value in reserved_control_bytes() if value & 0x0C == 0x0C)
    summary = {
        "schema": SCHEMA,
        "result": "PASS" if not failures else "FAIL",
        "defined_isa_control_bytes": len(isa_control_bytes()),
        "reserved_control_bytes": len(reserved_control_bytes()),
        "operands": [f"{value:02X}" for value in operands],
        "cases": len(records),
        "undefined_safe_control_bytes": len(reserved_control_bytes()) - store_dominant,
        "store_dominant_mixed_control_bytes": store_dominant,
        "full_fetch_execute_steps_per_case": 3,
        "no_nop_claim": True,
        "independent_isa_proof": False,
        "failures": len(failures),
        "artifacts": {"cases": str(args.out_dir / "cases.jsonl"), "programs": str(programs)},
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
