#!/usr/bin/env python3
"""RV8GR standalone Python simulation using Components chip definitions.

This runner keeps the RV8GR CPU-state test cases from ``chip_sim.py`` but
instantiates the 36-package chip set through the vendored Components
``chiplib`` package. It is a compatibility bridge while the full net-level
Components circuit runner matures.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[0]
COMPONENTS_ROOT = Path(os.environ.get("COMPONENTS_ROOT", ROOT / "third_party" / "Components"))
COMPONENTS_PYTHON = Path(os.environ.get("COMPONENTS_PYTHON", COMPONENTS_ROOT / "python"))

sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(COMPONENTS_PYTHON))

from chip_sim import CPUSim, analyze_timing  # noqa: E402
from chiplib.chips import create_chip  # noqa: E402
from chiplib.core import X, Z  # noqa: E402


def _logic_to_bit(value: int | str) -> int:
    if value in (Z, X):
        return 0
    return int(value) & 1


class ComponentChipAdapter:
    """Small adapter from Components ``Chip`` API to legacy RV8GR sim API."""

    def __init__(self, part: str, name: str):
        self.part = part
        self.name = name
        self.chip = create_chip(part, name)

    @property
    def prop_delay(self) -> int:
        return max(self.chip.delay.rise_ns, self.chip.delay.fall_ns or self.chip.delay.rise_ns)

    @property
    def _data(self) -> bytearray:
        return self.chip.data

    @_data.setter
    def _data(self, value: bytearray) -> None:
        self.chip.data = value

    def get(self, pin: int | str) -> int:
        return _logic_to_bit(self.chip.read(pin))

    def set(self, pin: int | str, value: int) -> None:
        self.chip.set_input(pin, value)

    def update(self) -> None:
        self.chip.update()
        self.chip.commit()

    def clock_edge(self, pin: int | str | None = None) -> None:
        self.chip.clock_edge(pin)
        self.chip.commit()

    def __getattr__(self, name: str):
        if name in {"_reg", "_count", "_q", "_sr"}:
            return getattr(self.chip, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        if name in {"_reg", "_count", "_q", "_sr"} and "chip" in self.__dict__:
            setattr(self.chip, name, value)
            return
        super().__setattr__(name, value)


def create_components_cpu() -> dict[str, ComponentChipAdapter]:
    parts = {
        "U1": "74HC161", "U2": "74HC161", "U3": "74HC161", "U4": "74HC161",
        "U5": "74HC574", "U6": "74HC574", "U7": "74HC245", "U8": "74HC164",
        "U9": "74HC574", "U10": "74HC283", "U11": "74HC283",
        "U12": "74HC86", "U13": "74HC86", "U14": "74HC541",
        "U15": "74HC157", "U16": "74HC157", "U17": "74HC157", "U18": "74HC157",
        "U19": "74HC157", "U20": "74HC157", "U21": "74HC74", "U22": "74HC688",
        "U23": "74HC574", "U24": "74HC04", "U25": "74HC32",
        "U26": "74HC00", "U27": "74HC00", "U28": "74HC86",
        "U29": "74HC157", "U30": "74HC157", "U31": "74HC74",
        "U32": "74HC574", "U33": "74HC21", "U34": "74HC541",
        "ROM": "AT28C256", "RAM": "62256",
    }
    return {ref: ComponentChipAdapter(part, ref) for ref, part in parts.items()}


class ComponentsCPUSim(CPUSim):
    """RV8GR CPU runner backed by Components Python chip definitions."""

    def __init__(self):
        self.chips = create_components_cpu()
        self.clock = 0
        self.phase = 0

        self.pc = 0x0000
        self.ir_high = 0x00
        self.ir_low = 0x00
        self.ac = 0x00
        self.page_reg = 0x00
        self.data_page = 0x80
        self.z_flag = 1
        self.ie = 0
        self.irq_ff = 0
        self.irq_n = 1

        self.chips["ROM"]._data = bytearray(32768)
        self.chips["RAM"]._data = bytearray(32768)


def run_acceptance_tests() -> ComponentsCPUSim:
    print("=" * 64)
    print("RV8-GR Components-Backed Python Chip Simulation")
    print("=" * 64)

    sim = ComponentsCPUSim()
    sim.run(bytes([0x30, 0x42, 0x01, 0x02]))
    assert sim.ac == 0x42, f"LI $42: AC=${sim.ac:02X}"
    print(f"  PASS: LI $42 -> AC=${sim.ac:02X}")

    sim = ComponentsCPUSim()
    sim.run(bytes([0x30, 0x10, 0x10, 0x05, 0x01, 0x04]))
    assert sim.ac == 0x15, f"ADDI: AC=${sim.ac:02X}"
    print(f"  PASS: LI $10, ADDI $05 -> AC=${sim.ac:02X}")

    sim = ComponentsCPUSim()
    sim.run(bytes([0x30, 0x05, 0x90, 0x05, 0x01, 0x04]))
    assert sim.ac == 0x00 and sim.z_flag == 1
    print("  PASS: LI $05, SUBI $05 -> AC=$00, Z=1")

    sim = ComponentsCPUSim()
    sim.run(bytes([0x30, 0xAA, 0x04, 0x10, 0x30, 0x00, 0x38, 0x10, 0x01, 0x08]))
    assert sim.ac == 0xAA, f"SB/LB: AC=${sim.ac:02X}"
    print("  PASS: SB $10, LB $10 -> AC=$AA")

    sim = ComponentsCPUSim()
    sim.run(bytes([0x30, 0x00, 0x02, 0x06, 0x30, 0xFF, 0x01, 0x06]))
    assert sim.ac == 0x00
    print("  PASS: BEQ taken skips LI $FF")

    sim = ComponentsCPUSim()
    sim.chips["RAM"]._data[0x1000] = 0x77
    sim.run(bytes([0x40, 0x90, 0x38, 0x00, 0x01, 0x04]))
    assert sim.ac == 0x77, f"SETDP+LB: AC=${sim.ac:02X}"
    print("  PASS: SETDP $90, LB $00 -> AC=$77")

    sim = ComponentsCPUSim()
    rom = bytearray(32768)
    rom[0] = 0x20; rom[1] = 0x10
    rom[2] = 0x01; rom[3] = 0x00
    rom[0x1000] = 0x30; rom[0x1001] = 0x77
    rom[0x1002] = 0x01; rom[0x1003] = 0x02
    sim.run(bytes(rom))
    assert sim.ac == 0x77, f"Jump: AC=${sim.ac:02X}"
    print("  PASS: SETPG $10, J $00 -> AC=$77")

    sim = ComponentsCPUSim()
    sim.run(bytes([0x40, 0x00, 0x38, 0x00, 0x01, 0x04]))
    assert sim.ac == 0x40, f"ROM read: AC=${sim.ac:02X}"
    print("  PASS: SETDP $00, LB $00 -> AC=$40")

    print()
    analyze_timing(sim.chips)
    print()
    print("=" * 64)
    print("ALL 8 COMPONENTS-BACKED CPU TESTS PASSED")
    print("=" * 64)
    return sim


if __name__ == "__main__":
    run_acceptance_tests()
