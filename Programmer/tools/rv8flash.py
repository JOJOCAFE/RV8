#!/usr/bin/env python3
"""
rv8flash.py — Flash, read, and verify ROM images for RV8 family CPUs

Usage: python3 rv8flash.py [options]

Options:
  -h, --help          Show help
  -pl, --portlist     List available serial ports
  -p N, --port N      Use port N (default: 0)
  -c, --check         Check programmer connection
  -w FILE, --write FILE   Write binary file to ROM
  -r FILE, --read FILE    Read ROM to binary file
  -v FILE, --verify FILE  Verify ROM against file
  -f, --force         Overwrite existing file (for read)
  -d, --debug         Show serial traffic
  -t N, --retry N     Retry N times (default: 3)
  -R, --reset         Pulse /RST after flash
  --format FORMAT     File format: bin or hex (default: bin)
  --base ADDR         Base address for RV8GR docs compatibility (only 0 supported)
  -q, --quiet         Minimal output

Compatibility:
  python3 tools/rv8flash.py program FILE --base 0x0000
  python3 tools/rv8flash.py verify  FILE --base 0x0000
"""

import sys
import argparse
import os
import serial

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

    # Data bus D[7:0] — bidirectional (via TXS0108E #2 → RV8-Bus pin 17-24)
    DATA_PINS = [13, 12, 14, 27, 26, 25, 33, 32]  # D0-D7

    # Address shift register (74HC595 ×2, via TXS0108E #1 → RV8-Bus pin 1-15)
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
        self.check = False
        self.write = None
        self.read = None
        self.verify = None
        self.help = False
        self.port_list = False
        self.force = False
        self.debug = False
        self.retry = 3
        self.auto_reset = False
        self.format = 'bin'
        self.quiet = False
        self.base = 0


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

            # Parse Intel HEX line
            byte_count = int(line[1:3], 16)
            addr = int(line[3:7], 16) + base_addr
            rec_type = int(line[7:9], 16)

            if rec_type == 0x00:  # Data
                # Extend data array if needed
                while len(data) < addr:
                    data.append(0)
                # Add data bytes
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


def save_file(path: str, data: bytes):
    """Save data to file."""
    mode = 'wb' if not os.path.exists(path) or os.path.exists(path) else 'wb'
    with open(path, 'wb') as f:
        f.write(data)


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
        import time
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
# PROGRAMMER COMMANDS
# =============================================================================

def cmd_check(port: SerialPort, debug: bool = False) -> bool:
    """Check programmer connection."""
    port.write(b'?')
    if debug:
        print(f"[DEBUG] TX: 3F")
    response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
    if debug:
        print(f"[DEBUG] RX: {hex_dump(response.encode())}")
    return response == "Connected"


def cmd_flash(port: SerialPort, data: bytes, retry: int = 3, debug: bool = False, quiet: bool = False) -> bool:
    """Flash data to ROM."""
    length = len(data)

    for attempt in range(retry):
        # Send flash command with length (NOT data yet)
        header = b'F' + bytes([(length >> 8) & 0xFF, length & 0xFF])
        port.write(header)
        if debug:
            print(f"[DEBUG] TX: {hex_dump(header)}")

        # Wait for ACK
        response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
        if debug:
            print(f"[DEBUG] RX: {response}")

        if response == "K":
            break
        elif attempt < retry - 1:
            if not quiet:
                print(f"Retry {attempt + 1}/{retry}...")
            continue
        else:
            if not quiet:
                print(f"Error: Flash failed ({response})")
            return False

    # Send data in chunks
    chunk_size = 256
    addr = 0
    total = len(data)

    while addr < total:
        chunk = data[addr:addr + chunk_size]
        port.write(chunk)
        addr += len(chunk)

        if debug:
            print(f"[DEBUG] TX: {hex_dump(chunk[:8])}... ({len(chunk)} bytes)")

        # Progress
        if not quiet:
            print(f"\r{progress_bar(addr, total, quiet=quiet)}", end='', flush=True)

    # Wait for completion
    response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
    if debug:
        print(f"\n[DEBUG] RX: {response}")

    if not quiet:
        print()  # New line after progress
    return response == "D"


def cmd_read(port: SerialPort, size: int = 32768, debug: bool = False) -> bytes:
    """Read ROM data."""
    port.write(b'V')
    if debug:
        print(f"[DEBUG] TX: 56")

    # Read all data
    data = b''
    while len(data) < size:
        chunk = port.read(size - len(data))
        if not chunk:
            break
        data += chunk
        print(f"\r{progress_bar(len(data), size, quiet=True)}", end='', flush=True)

    print()  # New line
    return data


def cmd_reset(port: SerialPort, debug: bool = False) -> bool:
    """Pulse /RST."""
    port.write(b'R')
    if debug:
        print(f"[DEBUG] TX: 52")
    response = port.read_until(b'\n').decode('utf-8', errors='replace').strip()
    if debug:
        print(f"[DEBUG] RX: {response}")
    return response == "K" or response == "OK"


def cmd_verify(port: SerialPort, file_data: bytes, debug: bool = False) -> bool:
    """Verify ROM against file (Option A: PC reads ROM, calculates checksum, compares)."""
    # Read ROM
    rom_data = cmd_read(port, len(file_data), debug=debug)

    # Compare byte by byte
    for i, (r, f) in enumerate(zip(rom_data, file_data)):
        if r != f:
            if not debug:
                print(f"Mismatched at address 0x{i:04X}: ROM=0x{r:02X} File=0x{f:02X}")
            else:
                print(f"[DEBUG] Mismatch at 0x{i:04X}: ROM={r:02X} File={f:02X}")
            return False

    # File might be smaller than ROM (32KB)
    if len(rom_data) != len(file_data):
        print(f"Warning: ROM size ({len(rom_data)}) != file size ({len(file_data)})")

    return True


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
        description='Flash, read, and verify ROM images for RV8 family CPUs',
        add_help=False
    )

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-pl', '--portlist', action='store_true')

    # Port selection
    port_group = parser.add_argument_group('Port selection')
    port_group.add_argument('-p', '--port', type=int, default=0, dest='port_index')

    # Operations (mutually exclusive)
    op_group = parser.add_argument_group('Operations')
    op_group.add_argument('-c', '--check', action='store_true')
    op_group.add_argument('-w', '--write', metavar='FILE', dest='write')
    op_group.add_argument('-r', '--read', metavar='FILE', dest='read')
    op_group.add_argument('-v', '--verify', metavar='FILE', dest='verify')

    # Options
    opt_group = parser.add_argument_group('Options')
    opt_group.add_argument('-f', '--force', action='store_true')
    opt_group.add_argument('-d', '--debug', action='store_true')
    opt_group.add_argument('-t', '--retry', type=int, default=3)
    opt_group.add_argument('-R', '--reset', action='store_true', dest='auto_reset')
    opt_group.add_argument('--format', choices=['bin', 'hex', 'auto'], default='bin')
    opt_group.add_argument('--base', default='0x0000',
                           help='Base address for RV8GR docs compatibility; only 0x0000 is supported')
    opt_group.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('command', nargs='?', choices=['program', 'write', 'verify', 'read', 'check'],
                        help='Compatibility command: program/write/verify/read/check')
    parser.add_argument('file', nargs='?', help='File for compatibility command')

    args = parser.parse_args()

    opts = Options()
    opts.port_index = args.port_index
    opts.check = args.check
    opts.write = args.write
    opts.read = args.read
    opts.verify = args.verify
    opts.help = args.help
    opts.port_list = args.portlist
    opts.force = args.force
    opts.debug = args.debug
    opts.retry = args.retry
    opts.auto_reset = args.auto_reset
    opts.format = args.format
    opts.quiet = args.quiet
    try:
        opts.base = int(str(args.base), 0)
    except ValueError:
        parser.error(f"invalid --base address: {args.base}")

    if args.command:
        if args.command == 'check':
            opts.check = True
        elif not args.file:
            parser.error(f"{args.command} requires FILE")
        elif args.command in ('program', 'write'):
            opts.write = args.file
        elif args.command == 'verify':
            opts.verify = args.file
        elif args.command == 'read':
            opts.read = args.file

    return opts


def rv8flash(opts: Options) -> int:
    """Main flash operation."""
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

    if opts.base != 0:
        print("Error: --base other than 0x0000 is not supported by the current programmer firmware")
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
            # Check connection
            if not opts.port_list:
                if not opts.quiet:
                    print(f"Port: {port_name} @ {ESP32.BAUD_RATE} baud")
                if not cmd_check(port, opts.debug):
                    print("Error: Programmer not responding")
                    return 1
                if not opts.quiet:
                    print("Programmer: Connected")

            # Check
            if opts.check:
                if cmd_check(port, opts.debug):
                    print("Connected")
                else:
                    print("Not Connected")
                return 0

            # Write
            if opts.write:
                if not os.path.exists(opts.write):
                    print(f"Error: File not found: {opts.write}")
                    return 1

                data = load_file(opts.write, opts.format)
                size = len(data)
                max_size = 32768  # AT28C256

                if size > max_size:
                    print(f"Error: File too large ({size} > {max_size})")
                    return 1

                if not opts.quiet:
                    print(f"Flashing {opts.write} ({size} bytes)...")

                if cmd_flash(port, data, opts.retry, opts.debug, opts.quiet):
                    if not opts.quiet:
                        print(f"Done. {size} bytes written.")

                    if opts.auto_reset:
                        if not opts.quiet:
                            print("Auto-resetting CPU...")
                        cmd_reset(port, opts.debug)
                else:
                    print("Flash failed")
                    return 1

            # Read
            if opts.read:
                if os.path.exists(opts.read) and not opts.force:
                    print(f"Error: File exists (use -f to overwrite): {opts.read}")
                    return 1

                if not opts.quiet:
                    print(f"Reading ROM (32768 bytes)...")

                data = cmd_read(port, 32768, opts.debug)

                if len(data) == 0:
                    print("Error: Read failed (no data received)")
                    return 1

                save_file(opts.read, data)

                if not opts.quiet:
                    print(f"Done. {len(data)} bytes saved to {opts.read}")

            # Verify
            if opts.verify:
                if not os.path.exists(opts.verify):
                    print(f"Error: File not found: {opts.verify}")
                    return 1

                file_data = load_file(opts.verify, opts.format)

                if not opts.quiet:
                    print(f"Verifying...")

                if cmd_verify(port, file_data, opts.debug):
                    if not opts.quiet:
                        print("Verified")
                    return 0
                else:
                    print("Verification failed")
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
    sys.exit(rv8flash(opts))


if __name__ == '__main__':
    main()
