#!/usr/bin/env python3
"""Assembler tests and sample-program simulation checks."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from rv4_asm import AssemblerError, assemble_text  # noqa: E402
from rv4_sim import RV4Tiny  # noqa: E402


class AssemblerTests(unittest.TestCase):
    def test_basic_program(self) -> None:
        asm = assemble_text("LI 5\nOUT\nHLT\n")
        self.assertEqual(asm.rom[:3], [0x45, 0x90, 0xF0])
        self.assertEqual(len(asm.rom), 16)

    def test_labels_constants_and_ram(self) -> None:
        asm = assemble_text(
            """
            COUNT = $E
            .RAM $F, 1
            LOOP:
              LW COUNT
              ADD $F
              SW COUNT
              J LOOP
            """
        )
        self.assertEqual(asm.rom[:4], [0x5E, 0x6F, 0x8E, 0xB0])
        self.assertEqual(asm.ram[0xF], 1)

    def test_short_forms(self) -> None:
        asm = assemble_text("ONE = $F\nCLR\nJMP done\nINC $E\ndone:\nHLT\n")
        self.assertEqual(asm.rom[:6], [0x40, 0xB5, 0x5E, 0x6F, 0x8E, 0xF0])

    def test_errors(self) -> None:
        for source in [
            "BAD\n",
            "LI\n",
            "LI $10\n",
            "A=1\nA=2\n",
            ".RAM $1, 0\n.RAM $1, 2\n",
            "\n".join(["NOP"] * 17),
        ]:
            with self.assertRaises(AssemblerError):
                assemble_text(source)


class SampleProgramTests(unittest.TestCase):
    def run_program(self, filename: str, edge_limit: int = 40, inp: int = 0) -> RV4Tiny:
        asm = assemble_text((ROOT / "programs" / filename).read_text(encoding="utf-8"))
        cpu = RV4Tiny()
        cpu.load_rom(asm.rom)
        cpu.load_ram(asm.ram)
        cpu.set_input(inp)
        outcome, _ = cpu.run(edge_limit)
        self.assertEqual(outcome, "halted")
        return cpu

    def test_li_out(self) -> None:
        self.assertEqual(self.run_program("01_li_out.asm").out, 5)

    def test_ram_store_load(self) -> None:
        cpu = self.run_program("02_ram_store_load.asm")
        self.assertEqual(cpu.ram[0xE], 3)
        self.assertEqual(cpu.out, 3)

    def test_add_wrap(self) -> None:
        self.assertEqual(self.run_program("03_add_wrap.asm").out, 1)

    def test_jz_loop(self) -> None:
        self.assertEqual(self.run_program("04_jz_loop.asm").out, 0)

    def test_input_echo(self) -> None:
        self.assertEqual(self.run_program("05_input_echo.asm", inp=0xC).out, 0xC)


if __name__ == "__main__":
    unittest.main()
