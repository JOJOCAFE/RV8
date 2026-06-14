#!/usr/bin/env python3
"""
rv8ram-boot.py — Upload program to RV8 CPU RAM via bootloader

Usage: python3 rv8ram-boot.py [options] file.bin

Options:
  -h, --help          Show help
  -pl, --portlist     List available serial ports
  -p N, --port N      Use port N (default: 0)
  -d, --debug         Show serial traffic
  -t N, --retry N     Retry N times (default: 3)
  -q, --quiet         Minimal output
  --format FORMAT     File format: bin or hex (default: bin)
  -f, --force         Overwrite existing file
  -R, --reset         Pulse /RST after upload
"""

import sys
import argparse
import os
import serial
import time

# =============================================================================
# VIRTUAL ESP32 BOARD DEFINITION
# Edit these values to match your hardware wiring
# =============================================================================

class VirtualESP32:
    """Virtual ESP32 board with configurable pin assignments."""
    NAME = "RV8 Programmer ESP32"

    # Serial port settings
    BAUD_RATE = 115200
    TIMEOUT = 5  # seconds

    # Data bus D[7:0] — bidirectional
    # Data bus D[7:0] — bidirectional (via TXS0108E #2)
    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7

    # Control signals (via TXS0108E #1 → RV8-Bus)
    PIN_nRST = 4       # → Bus pin 26 (/RST)
    PIN_nWR = 16       # → Bus pin 27 (/WR)
    PIN_nRD_O = 17     # → Bus pin 28 (/RD)

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
        self.file = None
        self.debug = False
        self.retry = 3
        self.quiet = False
        self.force = False
        self.format = 'bin'
        self.auto_reset = False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calc_checksum(data: bytes) -> int:
    """Calculate XOR checksum of data."""
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum


def parse_intel_hex(file_path: str) -> bytes:
    """Parse Intel HEX file, return binary data."""
    data = bytearray()
    base_addr = 0

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith(':'):
                continue

            byte_count = int(line[1:3], 16)
            addr = int(line[3:7], 16) + base_addr
            rec_type = int(line[7:9], 16)

            if rec_type == 0x00:  # Data
                while len(data) < addr:
                    data.append(0)
                for i in range(byte_count):
                    data.append(int(line[9 + i*2:11 + i*2], 16))

            elif rec_type == 0x01:  # End of file
                break

            elif rec_type == 0x04:  # Extended linear address
                base_addr = int(line[9:13], 16) * 65536

    return bytes(data)


def load_file(path: str, fmt: str = 'bin') -> bytes:
    """Load file, auto-detect format if not specified."""
    if fmt == 'auto':
        if path.endswith('.hex'):
            fmt = 'hex'
        else:
            fmt = 'bin'

    if fmt == 'hex':
        return parse_intel_hex(path)
    else:
        with open(path, 'rb') as f:
            return f.read()


def progress_bar(current: int, total: int, width: int = 40, quiet: bool = False) -> str:
    """Generate progress bar string."""
    if total == 0:
        percent = 100
    else:
        percent = min(100, int((current / total) * 100))

    filled = int(width * percent / 100)
    bar = '█' * filled + '░' * (width - filled)

    if quiet:
        return f"{percent}%"
    else:
        return f"[{bar}] {percent:3d}%"


def hex_dump(data: bytes, prefix: str = "") -> str:
    """Convert bytes to hex string for debug."""
    return ' '.join(f'{b:02X}' for b in data)


# =============================================================================
# SERIAL WRAPPER
# =============================================================================

class SerialPort:
    """Wrapper around pyserial with board configuration."""
    def __init__(self, port: str, baud: int = ESP32.BAUD_RATE, timeout: int = ESP32.TIMEOUT):
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

    def read_until(self, expected: bytes = b'\n') -> bytes:
        """Read until delimiter."""
        if self.ser:
            return self.ser.read_until(expected)
        return b''

    def read_all(self) -> bytes:
        """Read all available data."""
        if self.ser:
            return self.ser.read_all()
        return b''

    def available(self) -> int:
        """Check if data is available."""
        if self.ser:
            return self.ser.in_waiting
        return 0


# =============================================================================
# BOOTLOADER PROTOCOL
# =============================================================================

def wait_for_ready(port: SerialPort, timeout: float = 10.0, debug: bool = False) -> bool:
    """Wait for bootloader ready signal 'R'."""
    start = time.time()
    while time.time() - start < timeout:
        if port.available() > 0:
            byte = port.read(1)
            if byte == b'R':
                if debug:
                    print(f"[DEBUG] RX: 52")
                return True
        time.sleep(0.01)
    return False


def upload_data(port: SerialPort, data: bytes, delay: float = 0.006,
                retry: int = 3, debug: bool = False, quiet: bool = False) -> bool:
    """Upload data to RAM via bootloader."""
    length = len(data)

    for attempt in range(retry):
        # Send length (hi + lo)
        port.write(bytes([(length >> 8) & 0xFF, length & 0xFF]))
        if debug:
            print(f"[DEBUG] TX: {hex_dump(bytes([(length >> 8) & 0xFF, length & 0xFF]))}")

        # Wait for ACK
        response = port.read_until(b'\n')
        if debug:
            print(f"[DEBUG] RX: {response}")
        response = response.strip()

        if response == b'K' or response == b'OK':
            break
        elif attempt < retry - 1:
            if not quiet:
                print(f"Retry {attempt + 1}/{retry}...")
            continue
        else:
            if not quiet:
                print(f"Error: Bootloader not ready")
            return False

    # Send data byte by byte with delay
    addr = 0
    total = len(data)

    for byte in data:
        port.write(bytes([byte]))
        if debug and (addr % 16 == 0):
            print(f"[DEBUG] TX: {hex_dump(bytes([byte]))}")
        time.sleep(delay)  # 6ms per byte
        addr += 1

        # Progress
        print(f"\r{progress_bar(addr, total, quiet=quiet)}", end='', flush=True)

    print()  # New line

    # Wait for done signal
    response = port.read_until(b'\n')
    if debug:
        print(f"[DEBUG] RX: {response}")

    return response.strip() == b'D' or response.strip() == b'Done'


def cmd_reset(port: SerialPort, debug: bool = False) -> bool:
    """Pulse /RST."""
    port.write(b'R')
    if debug:
        print(f"[DEBUG] TX: 52")
    response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
    if debug:
        print(f"[DEBUG] RX: {response}")
    return response == "K" or response == "OK"


# =============================================================================
# MAIN FUNCTION
# =============================================================================

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


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Upload program to RV8 CPU RAM via bootloader',
        add_help=False
    )

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-pl', '--portlist', action='store_true')

    # Port selection
    port_group = parser.add_argument_group('Port selection')
    port_group.add_argument('-p', '--port', type=int, default=0, dest='port_index')

    # Options
    opt_group = parser.add_argument_group('Options')
    opt_group.add_argument('-d', '--debug', action='store_true')
    opt_group.add_argument('-t', '--retry', type=int, default=3)
    opt_group.add_argument('-q', '--quiet', action='store_true')
    opt_group.add_argument('--format', choices=['bin', 'hex', 'auto'], default='bin')
    opt_group.add_argument('-f', '--force', action='store_true')
    opt_group.add_argument('-R', '--reset', action='store_true', dest='auto_reset')

    # Positional argument
    parser.add_argument('file', nargs='?', default=None)

    args = parser.parse_args()

    opts = Options()
    opts.port_index = args.port
    opts.help = args.help
    opts.port_list = args.portlist
    opts.file = args.file
    opts.debug = args.debug
    opts.retry = args.retry
    opts.quiet = args.quiet
    opts.format = args.format
    opts.force = args.force
    opts.auto_reset = args.auto_reset

    return opts


def rv8ram_boot(opts: Options) -> int:
    """Main bootloader upload operation."""
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

    # Check file argument
    if not opts.file:
        print("Error: No file specified")
        print("Usage: python3 rv8ram-boot.py [options] file.bin")
        return 1

    if not os.path.exists(opts.file):
        print(f"Error: File not found: {opts.file}")
        return 1

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
        with SerialPort(port_name) as port:
            if opts.debug:
                print(f"Using port: {port_name}")

            # Load file
            data = load_file(opts.file, opts.format)
            size = len(data)
            max_size = 15871  # $C000 - $FDFF

            if size > max_size:
                print(f"Error: max {max_size} bytes (RAM $C000-$FDFF)")
                return 1

            if not opts.quiet:
                print(f"Uploading {opts.file} ({size} bytes)...")
                print("Waiting for bootloader ready signal...")

            # Wait for ready signal
            if not wait_for_ready(port, debug=opts.debug):
                print("Error: Timeout waiting for bootloader (send 'B' to enter boot mode)")
                return 1

            if not opts.quiet:
                print("Got 'R'. Sending data...")

            # Upload data
            if upload_data(port, data, retry=opts.retry, debug=opts.debug, quiet=opts.quiet):
                if not opts.quiet:
                    print(f"Done. {size} bytes uploaded.")

                if opts.auto_reset:
                    if not opts.quiet:
                        print("Auto-resetting CPU...")
                    cmd_reset(port, opts.debug)
            else:
                print("Upload failed")
                return 1

    except serial.SerialException as e:
        print(f"Error: Serial port error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 1

    return 0


def main():
    """Entry point."""
    opts = parse_args()
    sys.exit(rv8ram_boot(opts))


if __name__ == '__main__':
    main()