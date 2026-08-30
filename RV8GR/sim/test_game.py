#!/usr/bin/env python3
"""B-024: RV8-GR Deterministic Game ROM regression.

Runs programs/game.asm on both the gate-level Python CPU (CPUSim) and the
Components-backed CPU (ComponentsCPUSim) and asserts the deterministic end
state. The game is a fixed "reaction countdown": the timer always runs 10->0,
the win is latched exactly once at count == 7, and the program always halts at
game_over. No randomness, no external device, no uninitialized-state reliance.
"""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "sim"))

import rv8gr_asm  # noqa: E402
from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402


def assemble_game_rom() -> tuple[bytes, dict[str, int]]:
    source = (ROOT / "programs" / "game.asm").read_text()
    code, labels = rv8gr_asm.assemble(source)
    return bytes(rv8gr_asm.make_bin(code)), labels


class GameRomTest(unittest.TestCase):
    def test_game_rom_runs_on_python_cpu_paths(self):
        image, labels = assemble_game_rom()
        for sim_class in (CPUSim, ComponentsCPUSim):
            with self.subTest(simulator=sim_class.__name__):
                sim = sim_class()
                sim.run(image, max_clocks=600)

                ram = sim.chips["RAM"]._data

                # Program halts in the game_over block. HLT is "J self", so
                # the PC parks on the HLT instruction's own address, which is
                # the last instruction of the game_over block.
                self.assertGreaterEqual(sim.pc, labels["game_over"])
                self.assertEqual(sim.pc, 0x38)  # address of the HLT (J self)
                # CPU is left on the RAM data page at halt.
                self.assertEqual(sim.data_page, 0x80)
                # Countdown ran all the way to zero.
                self.assertEqual(ram[0x10], 0x00)
                # Win latched exactly once at count == 7.
                self.assertEqual(ram[0x20], 0x01)   # RAM[$8020] = win
                self.assertEqual(ram[0x11], 0x01)   # RAM[$8011] = final result
                # I/O mirrors (data page $FF -> $FFxx window).
                self.assertEqual(ram[0x7F10], 0x01)  # $FF10 final result mirror
                self.assertEqual(ram[0x7F20], 0x01)  # $FF20 win pulse mirror


if __name__ == "__main__":
    unittest.main()
