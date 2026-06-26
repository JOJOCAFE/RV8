#!/usr/bin/env python3
import unittest

import rv8gr_asm


class AssemblerEncodingTest(unittest.TestCase):
    def assembled_bytes(self, source, base=0x0000):
        code, _ = rv8gr_asm.assemble(source, base)
        return [b for _, bytes_list, _ in code for b in bytes_list]

    def assert_asm_error(self, source, text, base=0x0000):
        with self.assertRaises(rv8gr_asm.AssemblerError) as cm:
            code, _ = rv8gr_asm.assemble(source, base)
            rv8gr_asm.make_bin(code, base)
        self.assertIn(text, str(cm.exception))

    def test_all_frozen_instruction_encodings(self):
        src = """
            .org $0000
            NOP
            J $02
            BEQ $04
            SB $05
            EI
            ADDI $10
            ADD $11
            SETPG $12
            SETPG_R $13
            LI $14
            LB $15
            SETDP $80
            DI
            XORI $20
            XOR $21
            BNE $22
            SUBI $30
            SUB $31
        """
        self.assertEqual(self.assembled_bytes(src), [
            0x00, 0x00,
            0x01, 0x02,
            0x02, 0x04,
            0x04, 0x05,
            0x08, 0x00,
            0x10, 0x10,
            0x18, 0x11,
            0x20, 0x12,
            0x28, 0x13,
            0x30, 0x14,
            0x38, 0x15,
            0x40, 0x80,
            0x48, 0x00,
            0x70, 0x20,
            0x78, 0x21,
            0x82, 0x22,
            0x90, 0x30,
            0x98, 0x31,
        ])

    def test_documented_aliases_and_macros(self):
        src = """
            .org $0000
            MV $03,a0
            MV a0,$03
            HLT
            CLR
            INC
            DEC
            SLL
        """
        self.assertEqual(self.assembled_bytes(src), [
            0x04, 0x03,          # MV dst,a0 -> SB dst
            0x38, 0x03,          # MV a0,src -> LB src
            0x01, 0x04,          # HLT at $0004 -> J $04
            0x30, 0x00,          # CLR -> LI $00
            0x10, 0x01,          # INC -> ADDI $01
            0x90, 0x01,          # DEC -> SUBI $01
            0x04, 0x00, 0x18, 0x00,  # SLL -> SB $00 + ADD $00
        ])

    def test_jmp_macro_is_page_safe(self):
        src = """
            .org $0000
            JMP $1234
        """
        self.assertEqual(self.assembled_bytes(src), [0x20, 0x12, 0x01, 0x34])

    def test_org_db_labels_and_hi_lo(self):
        src = """
            .org $0010
        here:
            .db $12, 0x34 %01010110
            LI lo(here)
            SETPG hi(here)
        """
        code, labels = rv8gr_asm.assemble(src)
        self.assertEqual(labels["here"], 0x0010)
        self.assertEqual(
            [(pc, bytes_list) for pc, bytes_list, _ in code],
            [
                (0x0010, [0x12]),
                (0x0011, [0x34]),
                (0x0012, [0x56]),
                (0x0013, [0x30, 0x10]),
                (0x0015, [0x20, 0x00]),
            ],
        )

    def test_db_can_use_later_label(self):
        src = """
            .org $0000
            .db lo(later), hi(later)
            HLT
        later:
            NOP
        """
        self.assertEqual(self.assembled_bytes(src), [
            0x04, 0x00,
            0x01, 0x02,
            0x00, 0x00,
        ])

    def test_page_relative_branch_rejects_cross_page_label(self):
        self.assert_asm_error("""
            .org $00FE
            J target
            .org $0100
        target:
            NOP
        """, "target $0100 is on page $01")

    def test_raw_byte_jump_operand_is_allowed(self):
        self.assertEqual(self.assembled_bytes("J $80"), [0x01, 0x80])

    def test_overlap_detection(self):
        self.assert_asm_error("""
            .org $0000
            LI $12
            .org $0001
            NOP
        """, "written twice")

    def test_output_bounds_detection(self):
        self.assert_asm_error("""
            .org $8000
            NOP
        """, "outside output image")

    def test_unsupported_macros_are_rejected(self):
        self.assert_asm_error("CALL $1000", "unknown mnemonic 'CALL'")
        self.assert_asm_error("RET", "unknown mnemonic 'RET'")

    def test_operand_validation(self):
        self.assert_asm_error("LI", "LI expects 1 operand")
        self.assert_asm_error("NOP $00", "NOP expects 0 operands")
        self.assert_asm_error("MV a1,t0", "MV must be MV a0,src or MV dst,a0")
        self.assert_asm_error(".DB", ".DB expects at least one byte")


if __name__ == "__main__":
    unittest.main()
