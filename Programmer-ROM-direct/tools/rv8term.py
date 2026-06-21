#!/usr/bin/env python3
"""
rv8term.py — Terminal program for RV8 CPU

Usage: python3 rv8term.py [options]

Options:
  -h, --help          Show help
  -pl, --portlist     List available serial ports
  -p N, --port N      Use port N (default: 0)
  -b N, --baud N      Baud rate (default: 115200)
  -t N, --timeout N   Serial timeout in seconds (default: 0.1)
  -d, --debug         Show serial traffic
  --no-echo           Disable local echo
  --raw               Binary mode (no CR/LF translation)
  -q, --quiet         Minimal output
"""

import sys
import argparse
import os
import time
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
    NAME = "RV8 Programmer ESP32"

    # Serial port settings
    BAUD_RATE = 115200
    TIMEOUT = 5  # seconds (for connection check)

    # Data bus D[7:0] — bidirectional (via TXS0108E #2 → RV8-Bus pin 17-24)
    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7

    # Address via 74HC595 ×2 shift register (via TXS0108E #1 → RV8-Bus pin 1-15)
    SR_DATA_PIN = 23   # SER
    SR_CLK_PIN = 18    # SRCLK
    SR_LATCH_PIN = 19  # RCLK

    # Control signals (via TXS0108E #1 → RV8-Bus)
    PIN_nRST = 4       # → Bus pin 26 (/RST)
    PIN_nWR = 16       # → Bus pin 27 (/WR)
    PIN_nRD_O = 17     # → Bus pin 28 (/RD, output in PROG mode)

    # Input-only pins (from RV8-Bus)
    PIN_nSLOT = 34     # ← Bus pin 30 (/SLOT1)
    PIN_nRD = 35       # ← Bus pin 28 (/RD sense)
    PIN_nWR_S = 36     # ← Bus pin 27 (/WR sense)
    PIN_MODE = 39      # PROG/RUN switch

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
        self.check = False
        self.baud = 115200
        self.timeout = 0.1
        self.debug = False
        self.no_echo = False
        self.raw = False
        self.quiet = False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hex_dump(data: bytes) -> str:
    """Convert bytes to hex string for debug."""
    return ' '.join(f'{b:02X}' for b in data)


def get_serial_ports():
    """Get list of available serial ports."""
    ports = []
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        import glob
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    elif sys.platform.startswith('win'):
        import glob
        ports = [f'COM{i+1}' for i in range(256) if os.path.exists(f'COM{i+1}')]
    return sorted(ports)


# =============================================================================
# SERIAL WRAPPER (follows rv8flash.py pattern)
# =============================================================================

class SerialPort:
    """Wrapper around pyserial with board configuration."""
    def __init__(self, port: str, baud: int = ESP32.BAUD_RATE, timeout: float = ESP32.TIMEOUT):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None

    def __enter__(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(2)            # ESP32 resets on DTR — wait for boot
        self.ser.reset_input_buffer()  # discard boot messages
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

    def read_until(self, expected: bytes = b'\n') -> bytes:
        if self.ser:
            return self.ser.read_until(expected)
        return b''

    def available(self) -> int:
        if self.ser:
            return self.ser.in_waiting
        return 0

    def set_timeout(self, timeout: float):
        """Change timeout (e.g. switch from check mode to terminal mode)."""
        if self.ser:
            self.ser.timeout = timeout


# =============================================================================
# PROGRAMMER COMMANDS (same protocol as rv8flash.py)
# =============================================================================

def cmd_check(port: SerialPort, debug: bool = False) -> bool:
    """Check programmer connection — sends '?' expects 'Connected'."""
    port.write(b'?')
    if debug:
        print(f"[DEBUG] TX: 3F (?)")
    response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
    if debug:
        print(f"[DEBUG] RX: {response}")
    return response == "Connected"


# =============================================================================
# TERMINAL LOOP
# =============================================================================

def terminal_loop(port: SerialPort, opts: Options):
    """Bidirectional terminal: keyboard → ESP32, ESP32 → screen."""
    # Switch to short timeout for responsive terminal
    port.set_timeout(opts.timeout)

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            # ESP32 → screen
            if port.available() > 0:
                data = port.read(port.available())
                if opts.debug:
                    print(f"\n[DEBUG] RX: {hex_dump(data)}")
                if not opts.raw:
                    # CR/LF translation for display
                    data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # Keyboard → ESP32
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                raw_byte = char.encode('latin-1')
                if not opts.raw and char == '\n':
                    raw_byte = b'\r\n'  # Enter → CR+LF
                if opts.debug:
                    print(f"\n[DEBUG] TX: {hex_dump(raw_byte)}")
                port.write(raw_byte)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Terminal program for RV8 CPU',
        add_help=False
    )
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-pl', '--portlist', action='store_true')
    parser.add_argument('-p', '--port', type=int, default=0, dest='port_index')
    parser.add_argument('-c', '--check', action='store_true')
    parser.add_argument('-b', '--baud', type=int, default=115200)
    parser.add_argument('-t', '--timeout', type=float, default=0.1)
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--no-echo', action='store_true')
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')

    args = parser.parse_args()

    opts = Options()
    opts.port_index = args.port_index
    opts.help = args.help
    opts.port_list = args.portlist
    opts.check = args.check
    opts.baud = args.baud
    opts.timeout = args.timeout
    opts.debug = args.debug
    opts.no_echo = args.no_echo
    opts.raw = args.raw
    opts.quiet = args.quiet
    return opts


def rv8term(opts: Options) -> int:
    """Main terminal session."""
    if opts.help:
        print(__doc__)
        return 0

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
        with SerialPort(port_name, opts.baud) as port:
            if not opts.quiet:
                print(f"Port: {port_name} @ {opts.baud} baud")

            # Check programmer is alive (same as rv8flash.py)
            if not cmd_check(port, opts.debug):
                print("Error: Programmer not responding")
                return 1

            if not opts.quiet:
                print("Programmer: Connected")

            # -c: just check and exit
            if opts.check:
                return 0

            if not opts.quiet:
                print("Terminal mode. Press Ctrl+C to exit.")
                print("---")

            terminal_loop(port, opts)

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
