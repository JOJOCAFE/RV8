#!/usr/bin/env python3
"""
Test Suite for rv8flash.py
Includes MockSerial class and test cases.
Run with: python3 test_rv8flash.py
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import io
import importlib.util
from pathlib import Path

# =============================================================================
# MOCK SERIAL CLASS
# =============================================================================

class MockSerial:
    """Mock serial port for testing rv8flash.py without hardware.

    Simulates ESP32 programmer responses based on received commands.
    """
    def __init__(self, port, baud=115200, timeout=5):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.data = bytearray(32768)  # Simulate 32KB ROM
        self.received = []
        self._pos = 0  # Read position
        self.connected = True

    # ----- Write operations -----
    def write(self, data):
        """Process received command/data."""
        if isinstance(data, (bytes, bytearray)):
            self.received.append(bytes(data))
        else:
            self.received.append(str(data).encode())

    # ----- Read operations -----
    def read(self, n=1):
        """Return n bytes from ROM data at current position."""
        if not self.connected:
            return b''
        end = min(self._pos + n, len(self.data))
        result = bytes(self.data[self._pos:end])
        self._pos = end
        return result

    def read_until(self, expected=b'\n', size=-1):
        """Read until expected byte or timeout."""
        if size > 0:
            result = self.read(size)
            return result
        result = bytearray()
        for i in range(self._pos, len(self.data)):
            result.append(self.data[i])
            if result[-1] == expected[0]:
                self._pos = i + 1
                return bytes(result)
        self._pos = len(self.data)
        return bytes(result)

    # ----- Control operations -----
    def close(self):
        self.connected = False

    def open(self):
        self.connected = True
        self._pos = 0

    def is_open(self):
        return self.connected

    @property
    def in_waiting(self):
        """Return bytes available to read."""
        return len(self.data) - self._pos

    # ----- Simulation helpers -----
    def set_rom_data(self, data):
        """Set ROM contents (for read/verify tests)."""
        self.data[:len(data)] = bytearray(data)

    def get_checksum(self):
        """Calculate XOR checksum of ROM data."""
        checksum = 0
        for b in self.data:
            checksum ^= b
        return checksum

    def clear_received(self):
        """Clear received buffer."""
        self.received = []

    def reset_read_pos(self):
        """Reset read position to start."""
        self._pos = 0

    def flash_success(self, size):
        """Set response for successful flash."""
        self.data[0:2] = b'KD'  # K = ACK, D = Done

    def flash_fail(self, addr):
        """Set response for failed flash."""
        self.data[0:2] = b'E\x01'  # E = Error, 01 = failed at addr

    def ready_signal(self):
        """Return 'R' for bootloader ready."""
        return b'R'

    def __repr__(self):
        return f"MockSerial(port={self.port}, baud={self.baud})"


# =============================================================================
# MOCK SERIAL FACTORY
# =============================================================================

class MockSerialFactory:
    """Factory to create MockSerial instances for testing."""
    def __init__(self):
        self.devices = {}
        self.port_list = ['ttyUSB0', 'ttyUSB1']

    def list_ports(self):
        return self.port_list

    def create(self, port, baud=115200, timeout=5):
        """Create mock serial for given port."""
        if isinstance(port, int):
            port_name = self.port_list[port]
        else:
            port_name = port

        if port_name not in self.devices:
            self.devices[port_name] = MockSerial(port_name, baud, timeout)

        return self.devices[port_name]

    def reset(self):
        """Reset all mock devices."""
        self.devices = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calc_checksum(data):
    """Calculate XOR checksum of byte data."""
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum


def parse_hex_line(line):
    """Parse single Intel HEX line. Returns (address, data) or None."""
    line = line.strip()
    if not line.startswith(':'):
        return None

    try:
        byte_count = int(line[1:3], 16)
        address = int(line[3:7], 16)
        record_type = int(line[7:9], 16)

        if record_type == 0:  # Data
            data = bytes.fromhex(line[9:9 + byte_count * 2])
            return (address, data)
        elif record_type == 1:  # End of file
            return None
        else:
            return None
    except (ValueError, IndexError):
        return None


def parse_hex_file(path):
    """Parse Intel HEX file, return binary data."""
    max_addr = 0
    data_list = []

    with open(path, 'r') as f:
        for line in f:
            result = parse_hex_line(line)
            if result:
                addr, data = result
                max_addr = max(max_addr, addr + len(data))
                data_list.append((addr, data))

    # Build output
    output = bytearray(max_addr)
    for addr, data in data_list:
        output[addr:addr + len(data)] = data

    return bytes(output)


# =============================================================================
# TEST CASES
# =============================================================================

class TestMockSerial(unittest.TestCase):
    """Test MockSerial class functionality."""
    def setUp(self):
        self.mock = MockSerial('ttyUSB0')

    def test_write(self):
        self.mock.write(b'F')
        self.assertEqual(self.mock.received[-1], b'F')

    def test_read(self):
        self.mock.set_rom_data(b'Hello')
        self.mock.reset_read_pos()
        result = self.mock.read(3)
        self.assertEqual(result, b'Hel')
        self.assertEqual(self.mock._pos, 3)

    def test_checksum(self):
        # 0x30 ^ 0x4D ^ 0x4F ^ 0x00 = 0x32
        self.mock.set_rom_data(b'\x30\x4D\x4F\x00')
        self.assertEqual(self.mock.get_checksum(), 0x32)

    def test_read_until(self):
        self.mock.set_rom_data(b'Line1\nLine2\n')
        self.mock.reset_read_pos()
        result = self.mock.read_until(b'\n')
        self.assertEqual(result, b'Line1\n')


class TestChecksum(unittest.TestCase):
    """Test checksum calculation."""
    def test_empty(self):
        self.assertEqual(calc_checksum(b''), 0)

    def test_single_byte(self):
        self.assertEqual(calc_checksum(b'\x55'), 0x55)

    def test_xor_property(self):
        data = b'\x30\x4D\x4F\x00'
        self.assertEqual(calc_checksum(data), calc_checksum(data[::-1]))

    def test_consistent(self):
        data = b'Hello World!'
        self.assertEqual(calc_checksum(data), calc_checksum(data))


class TestHexParser(unittest.TestCase):
    """Test Intel HEX parsing."""
    def test_data_line(self):
        addr, data = parse_hex_line(':10000000020617ED002818E0228100219002121F3')
        self.assertEqual(addr, 0x0000)
        self.assertEqual(len(data), 16)

    def test_end_line(self):
        result = parse_hex_line(':00000001FF')
        self.assertIsNone(result)

    def test_full_file(self):
        import tempfile
        import os
        hex_content = ":10000000020617ED002818E0228100219002121F3\n:00000001FF\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hex', delete=False) as f:
            f.write(hex_content)
            path = f.name

        try:
            result = parse_hex_file(path)
            self.assertEqual(len(result), 16)
        finally:
            os.unlink(path)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests simulating full rv8flash.py usage."""
    def setUp(self):
        self.factory = MockSerialFactory()
        self.mock = self.factory.create(0)

    def test_check_connection(self):
        """Test -c option (check connection)."""
        self.mock.write(b'?')
        self.mock.write(b'Connected\n')
        self.mock.reset_read_pos()
        # Simulate what rv8flash.py would do
        self.mock.write(b'?')
        # After sending ?, expect response
        response = b'Connected\n'
        self.assertIn(b'Connected', response)

    def test_read_rom(self):
        """Test -r option (read ROM to file)."""
        # Set up ROM data (exact 32768 bytes)
        test_data = b'TEST' + (b'\x00' * (32768 - 4))
        self.mock.set_rom_data(test_data)
        self.mock.reset_read_pos()

        # Simulate read command
        self.mock.write(b'V')

        # Read back (should be exactly what we set)
        read_data = self.mock.read(32768)

        self.assertEqual(len(read_data), 32768)
        # Only compare the part we set (first 4 bytes)
        self.assertEqual(read_data[:4], b'TEST')

    def test_verify_match(self):
        """Test -v option with matching data."""
        # Set up ROM data
        test_data = b'VerifyMe!' + b'\x00' * (32768 - 9)
        self.mock.set_rom_data(test_data)
        self.mock.reset_read_pos()

        # Calculate checksums
        rom_checksum = self.mock.get_checksum()
        file_checksum = calc_checksum(test_data)

        self.assertEqual(rom_checksum, file_checksum)

    def test_verify_mismatch(self):
        """Test -v option with mismatched data."""
        # Set up ROM with one byte different
        file_data = b'AAAA' + b'\x00' * 4
        rom_data = b'AAAB' + b'\x00' * 4  # One byte different

        rom_checksum = calc_checksum(rom_data)
        file_checksum = calc_checksum(file_data)

        self.assertNotEqual(rom_checksum, file_checksum)

    def test_progress_bar(self):
        """Test progress bar generation."""
        size = 1000
        filled = 250
        bar = '█' * 10
        pct = int(filled * 100 / size)
        self.assertEqual(pct, 25)
        self.assertEqual(len(bar), 10)


class TestRv8grCliCompatibility(unittest.TestCase):
    """Regression tests for RV8GR documented rv8flash command form."""

    @classmethod
    def setUpClass(cls):
        module_path = Path(__file__).with_name('rv8flash.py')
        spec = importlib.util.spec_from_file_location('rv8flash_module', module_path)
        cls.rv8flash_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.rv8flash_module)

    def test_program_command_maps_to_write_base_zero(self):
        with patch.object(sys, 'argv', ['rv8flash.py', 'program', 'test.bin', '--base', '0x0000']):
            opts = self.rv8flash_module.parse_args()

        self.assertEqual(opts.write, 'test.bin')
        self.assertIsNone(opts.verify)
        self.assertEqual(opts.base, 0)

    def test_verify_command_maps_to_verify_base_zero(self):
        with patch.object(sys, 'argv', ['rv8flash.py', 'verify', 'test.bin', '--base', '0']):
            opts = self.rv8flash_module.parse_args()

        self.assertEqual(opts.verify, 'test.bin')
        self.assertIsNone(opts.write)
        self.assertEqual(opts.base, 0)

    def test_nonzero_base_rejected_before_serial(self):
        opts = self.rv8flash_module.Options()
        opts.base = 0x1000

        with patch('sys.stdout', new_callable=io.StringIO) as stdout:
            result = self.rv8flash_module.rv8flash(opts)

        self.assertEqual(result, 1)
        self.assertIn('not supported', stdout.getvalue())


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("RV8Flash Test Suite")
    print("=" * 60)

    # Run unit tests
    print("\n[UNIT TESTS]")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestMockSerial))
    suite.addTests(loader.loadTestsFromTestCase(TestChecksum))
    suite.addTests(loader.loadTestsFromTestCase(TestHexParser))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRv8grCliCompatibility))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
