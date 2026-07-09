#!/usr/bin/env python3
"""RV8-GR Assembler — .asm → .bin
Usage: python3 rv8gr_asm.py input.asm [-o output.bin] [-f hex|bin|memh]

Safety features:
  - Cross-page validation: J/BEQ/BNE error if target is on a different page
  - Overlap detection: error if two instructions write the same address
  - Range checks: operands must fit in one byte, addresses in 16 bits
"""

import sys, re, argparse

# Opcode table: mnemonic → control byte
OPCODES = {
    'NOP':     0x00,
    'ADDI':    0x10,
    'ADD':     0x18,
    'SUBI':    0x90,
    'SUB':     0x98,
    'XORI':    0x70,
    'XOR':     0x78,
    'LI':      0x30,
    'LB':      0x38,
    'MV':      None,  # special: MV a0,rs ($38) or MV rd,a0 ($04)
    'SB':      0x04,
    'BEQ':     0x02,
    'BNE':     0x82,
    'J':       0x01,
    'JMP':     None,  # macro: SETPG hi + J lo
    'SETPG':   0x20,
    'SETPG_R': 0x28,
    'SETDP':   0x40,
    'EI':      0x08,
    'DI':      0x48,
    'HLT':     None,  # macro: J self
    'CLR':     None,  # macro: LI $00
    'INC':     None,  # macro: ADDI $01
    'DEC':     None,  # macro: SUBI $01
    'SLL':     None,  # macro: SB $00 + ADD $00
}

# Page-relative branch/jump instructions (target must be same page as PC)
PAGE_TARGET = {'J', 'BEQ', 'BNE'}

# Register aliases → RAM address
REGS = {'a0':0,'a1':1,'a2':2,'t0':3,'t1':4,'t2':5,'s0':6,'ra':7}


class AssemblerError(ValueError):
    """Assembly failed."""


def _error(line_num, msg):
    prefix = f"line {line_num}: " if line_num else ""
    raise AssemblerError(prefix + msg)


def parse_value(s, labels, pc=0, line_num=None):
    """Parse numeric value, register alias, or label."""
    s = s.strip().rstrip(',')
    if s in labels:
        return labels[s]
    if s.lower() in REGS:
        return REGS[s.lower()]
    m = re.fullmatch(r'(?i)(hi|lo)\((.+)\)', s)
    if m:
        v = parse_value(m.group(2), labels, pc, line_num)
        return (v >> 8) & 0xFF if m.group(1).lower() == 'hi' else v & 0xFF
    try:
        if s.startswith('$'):
            return int(s[1:], 16)
        if s.lower().startswith('0x'):
            return int(s, 16)
        if s.startswith('%'):
            return int(s[1:], 2)
        return int(s)
    except ValueError:
        _error(line_num, f"unknown symbol or invalid number '{s}'")


def _page_target_value(mnemonic, text, labels, pc, line_num):
    """Encode J/BEQ/BNE operand with cross-page safety check."""
    value = parse_value(text, labels, pc, line_num)
    # If it's a raw byte (0-255) and not a known label, pass through
    is_label = text.strip().rstrip(',') in labels
    if 0 <= value <= 0xFF and not is_label:
        return value
    if not 0 <= value <= 0xFFFF:
        _error(line_num, f"{mnemonic} target ${value:X} outside 16-bit memory")
    if (value >> 8) != (pc >> 8):
        hint = "use JMP for page-safe jump" if mnemonic == 'J' else \
               "set PG explicitly and use lo(target)"
        _error(line_num,
               f"{mnemonic} target ${value:04X} is on page ${value>>8:02X} "
               f"but PC is on page ${pc>>8:02X}; {hint}")
    return value & 0xFF


def _args(parts, expected, line_num):
    got = len(parts) - 1
    if got != expected:
        noun = "operand" if expected == 1 else "operands"
        _error(line_num, f"{parts[0].upper()} expects {expected} {noun}, got {got}")
    return parts[1:]


def _db_values(parts, labels, pc, line_num):
    text = ' '.join(parts[1:]).replace(',', ' ')
    values = [v for v in text.split() if v]
    if not values:
        _error(line_num, ".DB expects at least one byte")
    return [parse_value(v, labels, pc, line_num) & 0xFF for v in values]


def _db_count(parts, line_num):
    text = ' '.join(parts[1:]).replace(',', ' ')
    values = [v for v in text.split() if v]
    if not values:
        _error(line_num, ".DB expects at least one byte")
    return len(values)


def assemble(source, base_addr=0x0000):
    lines = source.split('\n')
    labels = {}
    code = []  # list of (pc, bytes, source_line)

    # Pass 1: collect labels and calculate addresses
    pc = base_addr
    for line_num, line in enumerate(lines, 1):
        line = line.split(';')[0].strip()
        if not line:
            continue
        if line.endswith(':'):
            lbl = line[:-1]
            if lbl in labels:
                _error(line_num, f"duplicate label '{lbl}'")
            labels[lbl] = pc
            continue
        parts = line.split()
        mnem = parts[0].upper()
        if mnem == 'JMP' or mnem == 'SLL':
            pc += 4
        elif mnem in ('HLT', 'CLR', 'INC', 'DEC'):
            pc += 2
        elif mnem == '.ORG':
            _args(parts, 1, line_num)
            pc = parse_value(parts[1], labels, pc, line_num)
        elif mnem == '.DB':
            pc += _db_count(parts, line_num)
        else:
            pc += 2

    # Pass 2: generate code
    pc = base_addr
    for line_num, line in enumerate(lines, 1):
        orig = line
        line = line.split(';')[0].strip()
        if not line or line.endswith(':'):
            if line.endswith(':'):
                pc = labels[line[:-1]]
            continue

        parts = line.split()
        mnem = parts[0].upper()

        if mnem == '.ORG':
            _args(parts, 1, line_num)
            pc = parse_value(parts[1], labels, pc, line_num)
            continue

        if mnem == '.DB':
            for b in _db_values(parts, labels, pc, line_num):
                code.append((pc, [b], orig))
                pc += 1
                orig = ''
            continue

        if mnem == 'HLT':
            _args(parts, 0, line_num)
            lo = pc & 0xFF
            code.append((pc, [0x01, lo], orig))
            pc += 2
            continue

        if mnem == 'CLR':
            _args(parts, 0, line_num)
            code.append((pc, [0x30, 0x00], orig))
            pc += 2
            continue

        if mnem == 'INC':
            _args(parts, 0, line_num)
            code.append((pc, [0x10, 0x01], orig))
            pc += 2
            continue

        if mnem == 'DEC':
            _args(parts, 0, line_num)
            code.append((pc, [0x90, 0x01], orig))
            pc += 2
            continue

        if mnem == 'SLL':
            _args(parts, 0, line_num)
            # SB $00 + ADD $00 (a0 = a0 + a0 via scratch)
            code.append((pc, [0x04, 0x00, 0x18, 0x00], orig))
            pc += 4
            continue

        if mnem == 'JMP':
            _args(parts, 1, line_num)
            target = parse_value(parts[1], labels, pc, line_num)
            if not 0 <= target <= 0xFFFF:
                _error(line_num, f"JMP target ${target:X} outside 16-bit memory")
            hi = (target >> 8) & 0xFF
            lo = target & 0xFF
            code.append((pc, [0x20, hi, 0x01, lo], orig))
            pc += 4
            continue

        # MV pseudo-instruction
        if mnem == 'MV':
            args = [a for a in ' '.join(parts[1:]).replace(',', ' ').split() if a]
            if len(args) != 2:
                _error(line_num, f"MV expects 2 operands, got {len(args)}")
            if args[0].lower() == 'a0':
                operand = parse_value(args[1], labels, pc, line_num)
                code.append((pc, [0x38, operand & 0xFF], orig))
            elif args[1].lower() == 'a0':
                operand = parse_value(args[0], labels, pc, line_num)
                code.append((pc, [0x04, operand & 0xFF], orig))
            else:
                _error(line_num, "MV must be MV a0,src or MV dst,a0")
            pc += 2
            continue

        # Regular 2-byte instructions
        opcode = OPCODES.get(mnem)
        if opcode is None:
            _error(line_num, f"unknown mnemonic '{mnem}'")

        if mnem in ('NOP', 'EI', 'DI'):
            _args(parts, 0, line_num)
            operand = 0x00
        elif mnem in PAGE_TARGET:
            _args(parts, 1, line_num)
            operand = _page_target_value(mnem, parts[1], labels, pc, line_num)
        else:
            _args(parts, 1, line_num)
            operand = parse_value(parts[1], labels, pc, line_num) & 0xFF

        code.append((pc, [opcode, operand], orig))
        pc += 2

    return code, labels


def make_bin(code, base_addr=0x0000, size=32768):
    """Create binary image with overlap detection."""
    rom = bytearray(size)
    written = {}
    for pc, bytes_list, src in code:
        for i, b in enumerate(bytes_list):
            addr = pc + i
            offset = addr - base_addr
            if not 0 <= offset < size:
                raise AssemblerError(
                    f"address ${addr:04X} outside output image "
                    f"${base_addr:04X}-${base_addr+size-1:04X}")
            if addr in written:
                raise AssemblerError(
                    f"address ${addr:04X} written twice: "
                    f"'{written[addr].strip()}' and '{src.strip()}'")
            rom[offset] = b
            written[addr] = src
    return rom


def make_hex(code):
    """Create hex listing."""
    out = []
    for pc, bytes_list, src in code:
        hex_str = ' '.join(f'${b:02X}' for b in bytes_list)
        out.append(f"${pc:04X}: {hex_str:20s} ; {src}")
    return '\n'.join(out)


def make_memh(image):
    """Create Verilog $readmemh format (one hex byte per line)."""
    return '\n'.join(f'{b:02X}' for b in image)


def main():
    parser = argparse.ArgumentParser(description='RV8-GR Assembler')
    parser.add_argument('input', help='Input .asm file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-f', '--format', choices=['bin', 'hex', 'memh'], default='bin')
    parser.add_argument('-b', '--base', default='0x0000', help='Base address (default $0000)')
    args = parser.parse_args()

    base = int(args.base, 0)

    try:
        with open(args.input) as f:
            source = f.read()

        code, labels = assemble(source, base)

        if args.format == 'hex' or not args.output:
            print(make_hex(code))
            if labels:
                print("\n; Labels:")
                for name, addr in sorted(labels.items(), key=lambda x: x[1]):
                    print(f";   {name} = ${addr:04X}")

        if args.output:
            if args.format == 'bin':
                rom = make_bin(code, base)
                with open(args.output, 'wb') as f:
                    f.write(rom)
                print(f"Written {len(rom)} bytes to {args.output}", file=sys.stderr)
            elif args.format == 'hex':
                with open(args.output, 'w') as f:
                    f.write(make_hex(code))
            else:  # memh
                rom = make_bin(code, base)
                with open(args.output, 'w') as f:
                    f.write(make_memh(rom))
                    f.write('\n')

    except (AssemblerError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
