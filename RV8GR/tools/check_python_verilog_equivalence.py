#!/usr/bin/env python3
"""Compare RV8GR Python CPU sims against both Verilog CPU models.

The Verilog side is checked by ``run_dual_verilog_compare.sh``, which compares
behavioral ``rv8gr_cpu.v`` with TTL chip-level ``rv8gr_chip_level.v``. This
script runs the same all-ISA program in both Python CPU simulators and compares
their architectural checkpoint stream with the Verilog dual-scoreboard stream.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "sim"))

import rv8gr_asm  # noqa: E402
from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402


FINAL_RE = re.compile(
    r"final pc=(?P<pc>[0-9a-fA-F]+) ac=(?P<ac>[0-9a-fA-F]+) "
    r"z=(?P<z>[01]) ie=(?P<ie>[01]) irq=(?P<irq>[01]) "
    r"pg=(?P<pg>[0-9a-fA-F]+) dp=(?P<dp>[0-9a-fA-F]+)"
)
CHECKPOINT_RE = re.compile(
    r"VERILOG_CHECKPOINT idx=(?P<idx>\d+) pc=(?P<pc>[0-9a-fA-F]+) "
    r"ac=(?P<ac>[0-9a-fA-F]+) z=(?P<z>[01]) ie=(?P<ie>[01]) "
    r"irq=(?P<irq>[01]) pg=(?P<pg>[0-9a-fA-F]+) dp=(?P<dp>[0-9a-fA-F]+)"
)


def load_common_program() -> bytes:
    source = (ROOT / "programs" / "all_isa_equivalence.asm").read_text()
    code, _labels = rv8gr_asm.assemble(source)
    return bytes(rv8gr_asm.make_bin(code))


def _checkpoint_from_match(match: re.Match[str]) -> dict[str, int]:
    return {
        "pc": int(match.group("pc"), 16),
        "ac": int(match.group("ac"), 16),
        "z": int(match.group("z")),
        "ie": int(match.group("ie")),
        "irq": int(match.group("irq")),
        "pg": int(match.group("pg"), 16),
        "dp": int(match.group("dp"), 16),
    }


def run_verilog_dual() -> tuple[dict[str, int], list[dict[str, int]]]:
    result = subprocess.run(
        [str(ROOT / "tools" / "run_dual_verilog_compare.sh")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    match = FINAL_RE.search(result.stdout)
    if not match:
        print(result.stdout)
        raise RuntimeError("Could not parse final state from Verilog dual compare output")
    checkpoints = [_checkpoint_from_match(m) for m in CHECKPOINT_RE.finditer(result.stdout)]
    if not checkpoints:
        print(result.stdout)
        raise RuntimeError("Could not parse Verilog checkpoint stream")
    return _checkpoint_from_match(match), checkpoints


def current_state(sim: CPUSim) -> dict[str, int]:
    return {
        "pc": sim.pc,
        "ac": sim.ac,
        "z": sim.z_flag,
        "ie": sim.ie,
        "irq": sim.irq_ff,
        "pg": sim.page_reg,
        "dp": sim.data_page,
    }


def run_python(sim_class: type[CPUSim]) -> tuple[dict[str, int], list[dict[str, int]], CPUSim]:
    sim = sim_class()
    sim.pulse_irq()
    sim.load_rom(load_common_program())
    checkpoints = []
    seen_pc = set()

    for _ in range(600):
        sim.step()
        if sim.phase == 0 and sim.pc not in seen_pc:
            seen_pc.add(sim.pc)
            checkpoints.append(current_state(sim))
            if sim.pc in (0x0086, 0x0087):
                break

    return current_state(sim), checkpoints, sim


def assert_equal(name: str, got: dict[str, int], expected: dict[str, int]) -> None:
    if got != expected:
        raise AssertionError(f"{name} mismatch: got {got}, expected {expected}")


def assert_checkpoint_stream(name: str, got: list[dict[str, int]], expected: list[dict[str, int]]) -> None:
    if len(got) != len(expected):
        raise AssertionError(f"{name} checkpoint count mismatch: got {len(got)}, expected {len(expected)}")
    for index, (got_item, expected_item) in enumerate(zip(got, expected), 1):
        if got_item != expected_item:
            raise AssertionError(
                f"{name} checkpoint {index} mismatch: got {got_item}, expected {expected_item}"
            )


def main() -> int:
    verilog, verilog_checkpoints = run_verilog_dual()
    print(f"Verilog dual final: {verilog}")
    print(f"Verilog checkpoint stream: {len(verilog_checkpoints)} checkpoints")

    for sim_class in (CPUSim, ComponentsCPUSim):
        state, checkpoints, sim = run_python(sim_class)
        assert_equal(sim_class.__name__, state, verilog)
        assert_checkpoint_stream(sim_class.__name__, checkpoints, verilog_checkpoints)
        ram_checks = {
            0x0000: 0xAA,
            0x0001: 0x55,
            0x0002: 0xFF,
            0x0004: 0x00,
            0x0005: 0x42,
            0x0007: 0x5E,
            0x1000: 0xA5,
        }
        for addr, expected in ram_checks.items():
            got = sim.chips["RAM"]._data[addr]
            if got != expected:
                raise AssertionError(
                    f"{sim_class.__name__} RAM[$8{addr:04X}[14:0]]=${got:02X}, expected ${expected:02X}"
                )
        print(
            f"{sim_class.__name__} matches Verilog checkpoint stream, "
            "final state, and RAM checkpoints"
        )

    print("RV8GR Python/Verilog equivalence PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
