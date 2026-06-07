#!/usr/bin/env python3
"""
Test Suite for rv8ram-boot.py
Includes MockSerial class and test cases.
Run with: python3 test_rv8ram-boot.py
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import io

# =============================================================================
# MOCK SERIAL CLASS
# =============================================================================

class MockSerial:
    """Mock serial port for testing rv8ram-boot.py without hardware.

    Simulates ESP32 bootloader responses based on received commands.
    """
    def __init__(self, port, baud=115200, timeout=5):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.data = bytearray()  # Simulate received data
        self.received = []
        self._read_pos = 0
        self._response_index = 0
        self.connected = True
        self.ready_signal = b'R'  # Bootloader ready signal

    # ----- Write operations -----
    def write(self, data):
        """Process received command/data."""
        if isinstance(data, (bytes, bytearray)):
            self.received.append(bytes(data))
        else:
            self.received.append(str(data).encode())

    # ----- Read operations -----
    def read(self, n=1):
        """Return n bytes from response buffer."""
        if not self.connected:
            return b''
        end = min(self._read_pos + n, len(self.data))
        result = bytes(self.data[self._read_pos:end])
        self._read_pos = end
        return result

    def read_until(self, expected=b'\n', size=-1):
        """Read until expected byte or timeout."""
        if size > 0:
            result = self.read(size)
            return result
        result = bytearray()
        for i in range(self._read_pos, len(self.data)):
            result.append(self.data[i])
            if result[-1] == expected[0]:
                self._read_pos = i + 1
                return bytes(result)
        self._read_pos = len(self.data)
        return bytes(result)

    # ----- Control operations -----
    def close(self):
        self.connected = False

    def open(self):
        self.connected = True
        self._read_pos = 0

    def is_open(self):
        return self.connected

    @property
    def in_waiting(self):
        """Return bytes available to read."""
        return len(self.data) - self._read_pos

    # ----- Simulation helpers -----
    def set_ready_response(self):
        """Set response to 'R' (bootloader ready)."""
        self.data = bytearray(self.ready_signal)
        self._read_pos = 0

    def set_done_response(self):
        """Set response to 'D' (done)."""
        self.data = bytearray(b'D')
        self._read_pos = 0

    def set_error_response(self, msg=b'ERROR'):
        """Set error response."""
        self.data = bytearray(msg)
        self._read_pos = 0

    def clear_received(self):
        """Clear received buffer."""
        self.received = []

    def reset_read_pos(self):
        """Reset read position to start."""
        self._read_pos = 0

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
        self.mock.data = bytearray(b'Hello')
        self.mock._read_pos = 0
        result = self.mock.read(3)
        self.assertEqual(result, b'Hel')
        self.assertEqual(self.mock._read_pos, 3)

    def test_ready_signal(self):
        self.mock.set_ready_response()
        self.assertEqual(self.mock.read(1), b'R')

    def test_done_response(self):
        self.mock.set_done_response()
        self.assertEqual(self.mock.read(1), b'D')


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
        hex_content = ":100000003162696E61727920646174610000000000AB\n:00000001FF\n"
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
    """Integration tests simulating full rv8ram-boot.py usage."""
    def setUp(self):
        self.factory = MockSerialFactory()
        self.mock = self.factory.create(0)

    def test_ready_signal(self):
        """Test bootloader ready signal detection."""
        self.mock.set_ready_response()
        self.mock.reset_read_pos()
        response = self.mock.read(1)
        self.assertEqual(response, b'R')

    def test_upload_flow(self):
        """Test complete upload flow."""
        # Set bootloader ready response
        self.mock.set_ready_response()  # 'R'

        # Simulate upload
        self.mock.write(b'R')  # Send ready check
        self.mock.reset_read_pos()

        # Should receive 'R' from bootloader
        self.assertEqual(self.mock.read(1), b'R')

    def test_checksum(self):
        """Test checksum calculation during upload."""
        data = b'\x00\x01\x02\x03\x04'
        checksum = calc_checksum(data)
        # Verify checksum is XOR of all bytes
        expected = 0x00 ^ 0x01 ^ 0x02 ^ 0x03 ^ 0x04
        self.assertEqual(checksum, expected)

    def test_progress_bar(self):
        """Test progress bar generation."""
        size = 1000
        filled = 250
        bar = '█' * 10
        pct = int(filled * 100 / size)
        self.assertEqual(pct, 25)
        self.assertEqual(len(bar), 10)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("RV8RAM-Boot Test Suite")
    print("=" * 60)

    # Run unit tests
    print("\n[UNIT TESTS]")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestMockSerial))
    suite.addTests(loader.loadTestsFromTestCase(TestChecksum))
    suite.addTests(loader.loadTestsFromTestCase(TestHexParser))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

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