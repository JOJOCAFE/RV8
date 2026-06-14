#!/usr/bin/env python3
"""
rv8term.py — Terminal program for RV8 CPU

Usage: python3 rv8term.py [options]

Options:
  -h, --help          Show help
  -pl, --portlist     List available serial ports
  -p N, --port N      Use port N (default: 0)
  -b, --baud          Baud rate (default: 115200)
  -t, --timeout       Serial timeout in seconds (default: 0.1)
  -d, --debug         Show serial traffic
  --no-echo           Disable local echo
  --raw               Binary mode (no CR/LF translation)
  -q, --quiet         Minimal output
"""

import sys
import argparse
import os
import select
import serial
import tty
import termios

# =============================================================================
# VIRTUAL ESP32 BOARD DEFINITION
# Edit these values to match your hardware wiring
# =============================================================================

class VirtualESP32:
    """Virtual ESP32 board with configurable pin assignments."""
    NAME = "RV8 Terminal ESP32"

    # Serial port settings
    BAUD_RATE = 115200
    TIMEOUT = 0.1  # Short timeout for terminal mode

    # Data bus D[7:0] — bidirectional
    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7

    # Control signals
    PIN_nRST = 0       # /RST to CPU (active low)

# Create global board instance
ESP32 = VirtualESP32()


# =============================================================================
# OPTIONS CLASS
# =============================================================================

class Options:
    """Parsed command-line options."""
    def __init__(self):
        self.port_index = 0
        self.port_name = None
        self.help = False
        self.port_list = False
        self.baud = 115200
        self.timeout = 0.1
        self.debug = False
        self.no_echo = False
        self.raw = False
        self.quiet = False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hex_dump(data: bytes, prefix: str = "") -> str:
    """Convert bytes to hex string for debug."""
    return ' '.join(f'{b:02X}' for b in data)


def is_data_available() -> bool:
    """Check if keyboard data is available (non-blocking)."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def get_serial_ports():
    """Get list of available serial ports."""
    ports = []
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        import glob
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    elif sys.platform.startswith('win'):
        import glob
        ports = [f'COM{i+1}' for i in range(256) if os.path.exists(f'COM{i+1}')]
    return ports


# =============================================================================
# SERIAL WRAPPER
# =============================================================================

class SerialPort:
    """Wrapper around pyserial."""
    def __init__(self, port: str, baud: int = ESP32.BAUD_RATE, timeout: float = ESP32.TIMEOUT):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None

    def __enter__(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        return self

    def __exit__(self, *args):
        if self.ser:
            self.ser.close()

    def write(self, data: bytes):
        if self.ser:
            self.ser.write(data)

    def read(self, n: int = 1) -> bytes:
        if self.ser:
            return self.ser.read(n)
        return b''

    def available(self) -> int:
        if self.ser:
            return self.ser.in_waiting
        return 0


# =============================================================================
# TERMINAL HANDLING
# =============================================================================

class TerminalHandler:
    """Handle terminal mode for bidirectional communication."""
    def __init__(self, no_echo: bool = False, raw: bool = False):
        self.no_echo = no_echo
        self.raw = raw
        self.old_settings = None

    def __enter__(self):
        """Setup terminal for raw mode."""
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            self.old_settings = termios.tcgetattr(sys.stdin)
            if self.raw:
                # Raw mode - no echo, no line buffering
                tty.setcbreak(sys.stdin.fileno())
            elif not self.no_echo:
                # Cooked mode with echo - just set non-blocking
                pass
        return self

    def __exit__(self, *args):
        """Restore terminal settings."""
        if self.old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def read_keyboard(self) -> bytes:
        """Read single key from keyboard (non-blocking)."""
        if is_data_available():
            char = sys.stdin.read(1)
            if char == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            return char.encode('latin-1')
        return b''

    def write_screen(self, data: bytes):
        """Write data to screen."""
        if data:
            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except:
                pass


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Terminal program for RV8 CPU',
        add_help=False
    )

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-pl', '--portlist', action='store_true')

    # Port selection
    port_group = parser.add_argument_group('Port selection')
    port_group.add_argument('-p', '--port', type=int, default=0, dest='port_index')

    # Serial options
    serial_group = parser.add_argument_group('Serial options')
    serial_group.add_argument('-b', '--baud', type=int, default=115200)
    serial_group.add_argument('-t', '--timeout', type=float, default=0.1)

    # Terminal options
    term_group = parser.add_argument_group('Terminal options')
    term_group.add_argument('-d', '--debug', action='store_true')
    term_group.add_argument('--no-echo', action='store_true')
    term_group.add_argument('--raw', action='store_true')
    term_group.add_argument('-q', '--quiet', action='store_true')

    args = parser.parse_args()

    opts = Options()
    opts.port_index = args.port
    opts.help = args.help
    opts.port_list = args.portlist
    opts.baud = args.baud
    opts.timeout = args.timeout
    opts.debug = args.debug
    opts.no_echo = args.no_echo
    opts.raw = args.raw
    opts.quiet = args.quiet

    return opts


def rv8term(opts: Options) -> int:
    """Main terminal session."""
    # Help
    if opts.help:
        print(__doc__)
        return 0

    # Port list
    if opts.port_list:
        ports = get_serial_ports()
        for i, p in enumerate(ports):
            print(f"[{i}] {p}")
        return 0

    # Get port
    ports = get_serial_ports()
    if not ports:
        print("Error: No serial ports found")
        return 1

    if opts.port_index >= len(ports):
        print(f"Error: Port {opts.port_index} not found (only {len(ports)} ports available)")
        return 1

    port_name = ports[opts.port_index]

    try:
        with SerialPort(port_name, opts.baud, opts.timeout) as port:
            if not opts.quiet:
                print(f"Terminal mode. Press Ctrl+C to exit.")
                print(f"Connected to {port_name} at {opts.baud} baud.")

            with TerminalHandler(opts.no_echo, opts.raw) as term:
                while True:
                    # Check for serial data from CPU
                    if port.available() > 0:
                        data = port.read(port.available())
                        if opts.debug:
                            print(f"[DEBUG] RX: {hex_dump(data)}")
                        term.write_screen(data)

                    # Check for keyboard input
                    key = term.read_keyboard()
                    if key:
                        if opts.debug:
                            print(f"[DEBUG] TX: {hex_dump(key)}")
                        port.write(key)

    except serial.SerialException as e:
        print(f"Error: Serial port error: {e}")
        return 1
    except KeyboardInterrupt:
        if not opts.quiet:
            print("\nExiting...")
        return 0

    return 0


def main():
    """Entry point."""
    opts = parse_args()
    sys.exit(rv8term(opts))


if __name__ == '__main__':
    main()