#!/usr/bin/env python3
"""Deterministically compare the two RV8GR Python CPU simulation entry points.

This is a *compatibility* differential runner, not independent ISA proof:
``ComponentsCPUSim`` inherits the CPU-level execution model from ``CPUSim``
and replaces its chip instances with Components definitions.  The runner proves
that this integration path preserves the observed state transition stream.

All output is intentionally written below ``/tmp`` (or ``--out-dir``).  A
failure leaves a replayable ROM image and JSONL pair trace behind.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))

from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402


PAIR_KIND = "non_independent_cpu_model_vs_components_chip_adapter"
STATE_FIELDS = ("clock", "phase", "pc", "ir_high", "ir_low", "ac", "z", "pg", "dp", "ie", "irq", "irq_n")


def state(sim: CPUSim) -> dict[str, int]:
    """Return the architectural and fetch state observable after each edge."""
    return {
        "clock": sim.clock,
        "phase": sim.phase,
        "pc": sim.pc,
        "ir_high": sim.ir_high,
        "ir_low": sim.ir_low,
        "ac": sim.ac,
        "z": sim.z_flag,
        "pg": sim.page_reg,
        "dp": sim.data_page,
        "ie": sim.ie,
        "irq": sim.irq_ff,
        "irq_n": sim.irq_n,
    }


def seeded_rom(seed: int, size: int) -> bytes:
    """Generate a fixed arbitrary instruction byte stream for a seed."""
    if not 1 <= size <= 32768:
        raise ValueError("rom size must be in 1..32768")
    return random.Random(seed).randbytes(size)


def seed_same_start_state(sim: CPUSim, seed: int) -> None:
    """Seed extra start state identically without claiming power-on realism."""
    rng = random.Random(seed ^ 0x52563847)
    sim.pc = rng.randrange(0x10000)
    sim.ir_high = rng.randrange(0x100)
    sim.ir_low = rng.randrange(0x100)
    sim.ac = rng.randrange(0x100)
    sim.page_reg = rng.randrange(0x100)
    sim.data_page = rng.randrange(0x100)
    sim.z_flag = rng.randrange(2)
    sim.ie = rng.randrange(2)
    sim.irq_ff = rng.randrange(2)
    sim.irq_n = rng.randrange(2)
    # The existing model exposes a 32 KiB RAM array.  A sparse deterministic
    # initialization catches data-path differences without a large artifact.
    for _ in range(128):
        sim.chips["RAM"]._data[rng.randrange(32768)] = rng.randrange(0x100)


def json_line(handle, value: dict[str, Any]) -> None:
    handle.write(json.dumps(value, sort_keys=True) + "\n")


def run_pair(*, seed: int, steps: int, rom: bytes, out_dir: Path) -> dict[str, Any]:
    if steps < 1:
        raise ValueError("steps must be positive")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "program.bin").write_bytes(rom)

    baseline = CPUSim()
    components = ComponentsCPUSim()
    for sim in (baseline, components):
        sim.load_rom(rom)
        seed_same_start_state(sim, seed)

    trace_path = out_dir / "pair-trace.jsonl"
    mismatch: dict[str, Any] | None = None
    with trace_path.open("w", encoding="utf-8") as trace:
        json_line(trace, {
            "record": "metadata", "pair_kind": PAIR_KIND, "seed": seed,
            "requested_steps": steps, "rom_bytes": len(rom),
            "warning": "This pair shares CPUSim execution semantics; it is not independent ISA proof.",
        })
        for index in range(steps + 1):
            left = state(baseline)
            right = state(components)
            equal = left == right
            record = {"record": "state", "index": index, "equal": equal,
                      "cpusim": left, "components_cpusim": right}
            json_line(trace, record)
            if not equal:
                mismatch = record
                break
            if index != steps:
                baseline.step()
                components.step()

    result = {
        "pair_kind": PAIR_KIND,
        "independent_isa_proof": False,
        "seed": seed,
        "requested_steps": steps,
        "executed_states": (mismatch or {"index": steps})["index"] + 1,
        "rom_bytes": len(rom),
        "result": "PASS" if mismatch is None else "FAIL",
        "trace": str(trace_path),
        "program": str(out_dir / "program.bin"),
    }
    if mismatch is not None:
        result["first_mismatch"] = mismatch
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=lambda text: int(text, 0), default=0x52563847)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--rom-bytes", type=int, default=256)
    parser.add_argument("--rom-file", type=Path, help="Use this ROM image instead of generated bytes.")
    parser.add_argument("--out-dir", type=Path, help="Artifact directory (default: /tmp/rv8gr-python-pair/seed-<seed>).")
    args = parser.parse_args()
    rom = args.rom_file.read_bytes() if args.rom_file else seeded_rom(args.seed, args.rom_bytes)
    out_dir = args.out_dir or Path("/tmp/rv8gr-python-pair") / f"seed-{args.seed:08x}"
    result = run_pair(seed=args.seed, steps=args.steps, rom=rom, out_dir=out_dir)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
