#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '.')
import rv8gr_asm

class AssemblerEncodingTest(unittest.TestCase):
    def assembled_bytes(self, source):
        code, _ = rv8gr_asm.assemble(source, 0x0000)
        return [b for pc, bytes_list, src in code for b in bytes_list]

    def test_base_instruction_encodings(self):
        src = """
            .org $0000
            NOP
            ADDI $10
            SUBI $20
            XORI $30
            LI $40
            BEQ $50
            BNE $60
            J $70
            SETPG $80
        """
        result = self.assembled_bytes(src)
        self.assertEqual(result, [
            0x00, 0x00,  # NOP
            0x10, 0x10,  # ADDI
            0x90, 0x20,  # SUBI
            0x70, 0x30,  # XORI
            0x30, 0x40,  # LI
            0x02, 0x50,  # BEQ
            0x82, 0x60,  # BNE
            0x01, 0x70,  # J
            0x20, 0x80,  # SETPG
        ])

    def test_aliases_and_macros(self):
        src = """
            .org $0000
            MV $00,a0
            MV $01,a1
        """
        result = self.assembled_bytes(src)
        self.assertEqual(result, [
            0x04, 0x00,  # MV $00,a0
            0x04, 0x01,  # MV $01,a1
        ])

if __name__ == "__main__":
    unittest.main()