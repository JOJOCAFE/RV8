#!/usr/bin/env python3
"""B-011 minimal BASIC-style ROM regression."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "sim"))

import rv8gr_asm  # noqa: E402
from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402


def assemble_basic_rom() -> tuple[bytes, dict[str, int]]:
    source = (ROOT / "programs" / "basic_min.asm").read_text()
    code, labels = rv8gr_asm.assemble(source)
    return bytes(rv8gr_asm.make_bin(code)), labels


class BasicMinRomTest(unittest.TestCase):
    def test_basic_min_rom_runs_on_python_cpu_paths(self):
        image, labels = assemble_basic_rom()
        for sim_class in (CPUSim, ComponentsCPUSim):
            with self.subTest(simulator=sim_class.__name__):
                sim = sim_class()
                sim.run(image, max_clocks=300)

                ram = sim.chips["RAM"]._data
                self.assertEqual(sim.pc, labels["pass"])
                self.assertEqual(sim.data_page, 0x80)
                self.assertEqual(ram[0x20], 0x03)
                self.assertEqual(ram[0x40:0x44], bytes([0x01, 0x02, 0x03, 0x42]))
                self.assertEqual(ram[0x7F10], 0x03)


if __name__ == "__main__":
    unittest.main()
