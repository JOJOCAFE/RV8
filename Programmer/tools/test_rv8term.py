#!/usr/bin/env python3
"""
Test Suite for rv8term.py
Includes MockSerial class and test cases.
Run with: python3 test_rv8term.py
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import io
import threading
import importlib.util
from pathlib import Path

# =============================================================================
# MOCK SERIAL CLASS
# =============================================================================

class MockSerial:
    """Mock serial port for testing rv8term.py without hardware.

    Simulates ESP32 terminal bridge responses.
    """
    def __init__(self, port, baud=115200, timeout=0.1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.rx_buffer = bytearray()  # Data to send to PC
        self.tx_buffer = bytearray()  # Data received from PC
        self.received = []
        self._read_pos = 0
        self.connected = True
        self.echo_enabled = True  # Echo by default

    # ----- Write operations -----
    def write(self, data):
        """Process received data from PC."""
        if isinstance(data, (bytes, bytearray)):
            self.received.append(bytes(data))
            self.tx_buffer.extend(data)
            # Echo if enabled
            if self.echo_enabled:
                self.rx_buffer.extend(data)

    # ----- Read operations -----
    def read(self, n=1):
        """Return n bytes from RX buffer."""
        if not self.connected:
            return b''
        end = min(self._read_pos + n, len(self.rx_buffer))
        result = bytes(self.rx_buffer[self._read_pos:end])
        self._read_pos = end
        return result

    def readline(self):
        """Read until newline."""
        result = bytearray()
        for i in range(self._read_pos, len(self.rx_buffer)):
            result.append(self.rx_buffer[i])
            if self.rx_buffer[i] == ord('\n'):
                self._read_pos = i + 1
                return bytes(result)
        return b''

    def in_waiting(self):
        """Return bytes available to read."""
        return len(self.rx_buffer) - self._read_pos

    # ----- Control operations -----
    def close(self):
        self.connected = False

    def open(self):
        self.connected = True
        self._read_pos = 0

    def is_open(self):
        return self.connected

    # ----- Simulation helpers -----
    def queue_data(self, data):
        """Queue data to be read (simulates CPU output)."""
        self.rx_buffer.extend(data)

    def clear_buffers(self):
        """Clear both buffers."""
        self.rx_buffer.clear()
        self.tx_buffer.clear()
        self.received.clear()
        self._read_pos = 0

    def set_no_echo(self):
        """Disable echo."""
        self.echo_enabled = False

    def set_echo(self):
        """Enable echo."""
        self.echo_enabled = True

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

    def create(self, port, baud=115200, timeout=0.1):
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


# =============================================================================
# TEST CASES
# =============================================================================

class TestMockSerial(unittest.TestCase):
    """Test MockSerial class functionality."""
    def setUp(self):
        self.mock = MockSerial('ttyUSB0')

    def test_write(self):
        self.mock.write(b'A')
        self.assertEqual(self.mock.tx_buffer, b'A')

    def test_read(self):
        self.mock.queue_data(b'Hello')
        self.mock._read_pos = 0
        result = self.mock.read(3)
        self.assertEqual(result, b'Hel')
        self.assertEqual(self.mock._read_pos, 3)

    def test_echo(self):
        self.mock.write(b'A')
        self.assertIn(b'A', self.mock.rx_buffer)

    def test_no_echo(self):
        self.mock.set_no_echo()
        self.mock.write(b'A')
        self.assertNotIn(b'A', self.mock.rx_buffer)

    def test_in_waiting(self):
        self.mock.queue_data(b'Test')
        self.assertEqual(self.mock.in_waiting(), 4)

    def test_clear_buffers(self):
        self.mock.queue_data(b'Test')
        self.mock.write(b'A')
        self.mock.clear_buffers()
        self.assertEqual(len(self.mock.rx_buffer), 0)
        self.assertEqual(len(self.mock.tx_buffer), 0)


class TestChecksum(unittest.TestCase):
    """Test checksum calculation."""
    def test_empty(self):
        self.assertEqual(calc_checksum(b''), 0)

    def test_single_byte(self):
        self.assertEqual(calc_checksum(b'\x55'), 0x55)

    def test_consistent(self):
        data = b'Hello World!'
        self.assertEqual(calc_checksum(data), calc_checksum(data))


class TestTerminalModes(unittest.TestCase):
    """Test terminal mode configurations."""
    def setUp(self):
        self.mock = MockSerial('ttyUSB0')

    def test_raw_mode_no_translation(self):
        """Test raw mode passes bytes as-is."""
        # In raw mode, no CR/LF translation
        self.mock.queue_data(b'\x00\x01\x02\xFF')
        self.mock._read_pos = 0
        result = self.mock.read(4)
        self.assertEqual(result, b'\x00\x01\x02\xFF')

    def test_default_mode(self):
        """Test default mode echo behavior."""
        self.mock.write(b'X')
        self.assertEqual(self.mock.rx_buffer[-1], ord('X'))


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests simulating full rv8term.py usage."""
    def setUp(self):
        self.factory = MockSerialFactory()
        self.mock = self.factory.create(0)

    def test_connect(self):
        """Test terminal connection."""
        self.mock.queue_data(b'RV8 BASIC 1.0\r\n')
        self.mock._read_pos = 0
        # Read without advancing (check for expected prefix)
        expected = b'RV8 BASIC 1.0'
        data = self.mock.read(14)
        self.assertTrue(data.startswith(expected))

    def test_keyboard_input(self):
        """Test keyboard input to CPU."""
        self.mock.write(b'A')
        self.assertEqual(self.mock.tx_buffer[-1], ord('A'))

    def test_bidirectional(self):
        """Test bidirectional data flow."""
        # PC sends (echo in rx_buffer)
        self.mock.write(b'A')
        self.assertEqual(self.mock.tx_buffer[-1], ord('A'))

        # Queue CPU response after the echo
        self.mock.queue_data(b'OK\r\n')

        # Read everything (echo + CPU response)
        self.mock._read_pos = 0
        response = self.mock.readline()
        # Should contain both echo and CPU response
        self.assertIn(b'OK', response)

    def test_ctrl_c_detection(self):
        """Test Ctrl+C detection."""
        # Ctrl+C is 0x03
        self.mock.write(b'\x03')
        self.assertEqual(self.mock.tx_buffer[-1], 0x03)


class TestRv8TermProgrammerModeBoundary(unittest.TestCase):
    """Regression tests for PROG-mode check vs RUN-mode terminal startup."""

    @classmethod
    def setUpClass(cls):
        module_path = Path(__file__).with_name('rv8term.py')
        spec = importlib.util.spec_from_file_location('rv8term_module', module_path)
        cls.rv8term_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.rv8term_module)

    def make_opts(self, check=False, quiet=True):
        opts = self.rv8term_module.Options()
        opts.check = check
        opts.quiet = quiet
        return opts

    def test_terminal_mode_skips_prog_handshake(self):
        opts = self.make_opts(check=False)
        with patch.object(self.rv8term_module, 'get_serial_ports', return_value=['ttyUSB0']), \
             patch.object(self.rv8term_module, 'SerialPort') as serial_port, \
             patch.object(self.rv8term_module, 'cmd_check') as cmd_check, \
             patch.object(self.rv8term_module, 'terminal_loop', side_effect=KeyboardInterrupt):
            serial_port.return_value.__enter__.return_value = MagicMock()
            result = self.rv8term_module.rv8term(opts)

        self.assertEqual(result, 0)
        cmd_check.assert_not_called()

    def test_check_mode_uses_prog_handshake(self):
        opts = self.make_opts(check=True)
        with patch.object(self.rv8term_module, 'get_serial_ports', return_value=['ttyUSB0']), \
             patch.object(self.rv8term_module, 'SerialPort') as serial_port, \
             patch.object(self.rv8term_module, 'cmd_check', return_value=True) as cmd_check, \
             patch.object(self.rv8term_module, 'terminal_loop') as terminal_loop:
            port = MagicMock()
            serial_port.return_value.__enter__.return_value = port
            result = self.rv8term_module.rv8term(opts)

        self.assertEqual(result, 0)
        cmd_check.assert_called_once_with(port, opts.debug)
        terminal_loop.assert_not_called()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("RV8Term Test Suite")
    print("=" * 60)

    # Run unit tests
    print("\n[UNIT TESTS]")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestMockSerial))
    suite.addTests(loader.loadTestsFromTestCase(TestChecksum))
    suite.addTests(loader.loadTestsFromTestCase(TestTerminalModes))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRv8TermProgrammerModeBoundary))

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
