#!/usr/bin/env python3
"""Executable tests for ``doc/08_cpu_logical_test_protocol.md``."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "sim"))

import rv8gr_asm  # noqa: E402
from chip_sim import CPUSim  # noqa: E402
from components_chip_sim import ComponentsCPUSim  # noqa: E402


SIMULATORS = (CPUSim, ComponentsCPUSim)


def assemble_image(source: str) -> tuple[bytes, dict[str, int]]:
    code, labels = rv8gr_asm.assemble(source)
    return bytes(rv8gr_asm.make_bin(code)), labels


def run_program(sim_class: type[CPUSim], source: str, max_clocks: int = 500) -> tuple[CPUSim, dict[str, int]]:
    image, labels = assemble_image(source)
    sim = sim_class()
    sim.run(image, max_clocks=max_clocks)
    return sim, labels


class CpuLogicalProtocolTest(unittest.TestCase):
    def assert_program_state(
        self,
        source: str,
        *,
        ac: int,
        z: int,
        pc_label: str,
        ram: dict[int, int] | None = None,
        pg: int | None = None,
        dp: int | None = None,
        max_clocks: int = 500,
    ) -> None:
        for sim_class in SIMULATORS:
            with self.subTest(simulator=sim_class.__name__):
                sim, labels = run_program(sim_class, source, max_clocks=max_clocks)
                self.assertEqual(sim.ac, ac)
                self.assertEqual(sim.z_flag, z)
                self.assertEqual(sim.pc, labels[pc_label])
                if pg is not None:
                    self.assertEqual(sim.page_reg, pg)
                if dp is not None:
                    self.assertEqual(sim.data_page, dp)
                for offset, value in (ram or {}).items():
                    self.assertEqual(sim.chips["RAM"]._data[offset], value)

    def test_boot_contract_initial_state(self):
        for sim_class in SIMULATORS:
            with self.subTest(simulator=sim_class.__name__):
                sim = sim_class()
                self.assertEqual(sim.pc, 0x0000)
                self.assertEqual(sim.phase, 0)
                self.assertEqual(sim.clock, 0)

    def test_alu_boundary_values_and_branch_scoreboard(self):
        self.assert_program_state(
            """
            .org $0000
            SETDP $80
            SETPG $00
            LI $FF
            ADDI $01       ; overflow to zero
            BEQ add_ok
            LI $EE
            HLT
        add_ok:
            LI $80
            SUBI $80       ; zero again
            BEQ sub_ok
            LI $DD
            HLT
        sub_ok:
            LI $AA
            XORI $AA       ; zero by XOR
            BEQ pass
            LI $CC
        pass:
            HLT
            """,
            ac=0x00,
            z=1,
            pc_label="pass",
            pg=0x00,
            dp=0x80,
        )

    def test_ram_load_store_and_register_arithmetic(self):
        self.assert_program_state(
            """
            .org $0000
            SETDP $80
            SETPG $00
            LI $5A
            SB $10
            LI $06
            ADD $10        ; $06 + $5A = $60
            SB $11
            SUB $11        ; zero
            BEQ pass
            LI $FF
        pass:
            HLT
            """,
            ac=0x00,
            z=1,
            pc_label="pass",
            ram={0x10: 0x5A, 0x11: 0x60},
            pg=0x00,
            dp=0x80,
        )

    def test_rom_read_with_setdp_zero(self):
        self.assert_program_state(
            """
            .org $0000
            SETDP $00
            LB $00         ; reads opcode byte at ROM[$0000] = SETDP = $40
            SUBI $40
            BEQ pass
            LI $FF
        pass:
            HLT
            """,
            ac=0x00,
            z=1,
            pc_label="pass",
            dp=0x00,
        )

    def test_cross_page_jump_and_return_path(self):
        self.assert_program_state(
            """
            .org $0000
            SETDP $80
            SETPG $10
            J $00
        fail:
            LI $FF
            HLT

            .org $1000
        page10:
            LI $77
            SETPG $00
            J lo(done)

            .org $000A
        done:
            SUBI $77
            BEQ pass
            LI $EE
        pass:
            HLT
            """,
            ac=0x00,
            z=1,
            pc_label="pass",
            pg=0x00,
            dp=0x80,
        )

    def test_bne_taken_and_not_taken(self):
        self.assert_program_state(
            """
            .org $0000
            SETDP $80
            SETPG $00
            LI $01
            BNE nonzero
            LI $EE
            HLT
        nonzero:
            LI $00
            BNE fail
            BEQ pass
        fail:
            LI $FF
        pass:
            HLT
            """,
            ac=0x00,
            z=1,
            pc_label="pass",
            pg=0x00,
            dp=0x80,
        )


if __name__ == "__main__":
    unittest.main()
