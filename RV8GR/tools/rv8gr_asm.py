#!/usr/bin/env python3
"""RV8-GR Assembler — .asm → .bin
Usage: python3 rv8gr_asm.py input.asm [-o output.bin] [-f hex|bin]
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
    'EI':      0x08,
    'DI':      0x48,
    'HLT':     None,  # macro: J self
    'SLL':     None,  # macro: MV $00,a0 + ADD $00
    'CALL':    None,  # macro
    'RET':     None,  # macro
}

# Register aliases → RAM address
REGS = {'a0':0,'a1':1,'a2':2,'t0':3,'t1':4,'t2':5,'s0':6,'ra':7}

def parse_value(s, labels, pc):
    """Parse numeric value or label."""
    s = s.strip().rstrip(',')
    if s in labels:
        return labels[s]
    if s.lower() in REGS:
        return REGS[s.lower()]
    if s.startswith('$'):
        return int(s[1:], 16)
    if s.startswith('0x'):
        return int(s, 16)
    if s.startswith('%'):
        return int(s[1:], 2)
    if s.startswith("hi(") and s.endswith(")"):
        v = parse_value(s[3:-1], labels, pc)
        return (v >> 8) & 0xFF
    if s.startswith("lo(") and s.endswith(")"):
        v = parse_value(s[3:-1], labels, pc)
        return v & 0xFF
    return int(s)

def assemble(source, base_addr=0x8000):
    lines = source.split('\n')
    labels = {}
    code = []  # list of (pc, bytes, source_line)

    # Pass 1: collect labels and calculate addresses
    pc = base_addr
    for line in lines:
        line = line.split(';')[0].strip()
        if not line:
            continue
        if line.endswith(':'):
            labels[line[:-1]] = pc
            continue
        # Count bytes this instruction will produce
        parts = line.split()
        mnem = parts[0].upper()
        if mnem == 'JMP':
            pc += 4  # SETPG + J
        elif mnem == 'HLT':
            pc += 2
        elif mnem == 'CALL':
            pc += 8  # LI + SB + SETPG + J
        elif mnem == 'RET':
            pc += 4  # SETPG + J (assembler fills return addr)
        elif mnem == 'SLL':
            pc += 4  # MV $00,a0 + ADD $00
        elif mnem == '.ORG':
            pc = parse_value(parts[1], labels, pc)
        elif mnem == '.DB':
            pc += len(parts) - 1
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
            pc = parse_value(parts[1], labels, pc)
            continue

        if mnem == '.DB':
            for b in parts[1:]:
                code.append((pc, [parse_value(b, labels, pc) & 0xFF], orig))
                pc += 1
                orig = ''
            continue

        if mnem == 'HLT':
            lo = pc & 0xFF
            code.append((pc, [0x01, lo], orig))
            pc += 2
            continue

        if mnem == 'SLL':
            # Shift left logical: MV $00,a0 + ADD $00 (a0 = a0 + a0)
            code.append((pc, [0x04, 0x00, 0x18, 0x00], orig))
            pc += 4
            continue

        if mnem == 'JMP':
            # JMP label → SETPG hi(label) + J lo(label)
            target = parse_value(parts[1], labels, pc)
            hi = (target >> 8) & 0xFF
            lo = target & 0xFF
            code.append((pc, [0x20, hi, 0x01, lo], orig))
            pc += 4
            continue

        if mnem == 'CALL':
            # CALL label → LI lo(ret) + SB $07 + SETPG hi(target) + J lo(target)
            target = parse_value(parts[1], labels, pc)
            ret_addr = pc + 8  # return point is after CALL
            code.append((pc, [
                0x30, ret_addr & 0xFF,       # LI lo(return)
                0x04, 0x07,                   # MV $07, a0
                0x20, (target >> 8) & 0xFF,   # SETPG hi(target)
                0x01, target & 0xFF,          # J lo(target)
            ], orig))
            pc += 8
            continue

        if mnem == 'RET':
            # RET → SETPG ret_page + J ret_lo (caller must set RAM[6]=page, RAM[7]=lo)
            # Simple version: assembler needs return label
            if len(parts) > 1:
                target = parse_value(parts[1], labels, pc)
                code.append((pc, [0x20, (target >> 8) & 0xFF, 0x01, target & 0xFF], orig))
            else:
                # Generic RET using SETPG_R + J (needs indirect — not supported)
                # Fallback: emit placeholder
                code.append((pc, [0x28, 0x06, 0x01, 0x00], orig + " ; WARNING: needs known return"))
            pc += 4
            continue

        # Regular 2-byte instructions
        if mnem == 'MV':
            # MV a0, $xx → LB ($38) or MV $xx, a0 → SB ($04)
            args = ' '.join(parts[1:]).replace(' ', '')
            if args.startswith('a0,') or args.startswith('A0,'):
                # MV a0, rs
                operand = parse_value(args.split(',')[1], labels, pc)
                code.append((pc, [0x38, operand & 0xFF], orig))
            else:
                # MV rd, a0
                operand = parse_value(args.split(',')[0], labels, pc)
                code.append((pc, [0x04, operand & 0xFF], orig))
            pc += 2
            continue

        opcode = OPCODES.get(mnem)
        if opcode is None:
            print(f"ERROR line {line_num}: unknown mnemonic '{mnem}'", file=sys.stderr)
            sys.exit(1)

        if len(parts) > 1:
            operand = parse_value(parts[1], labels, pc) & 0xFF
        else:
            operand = 0x00

        code.append((pc, [opcode, operand], orig))
        pc += 2

    return code, labels

def make_bin(code, base_addr=0x8000, size=32768):
    """Create binary image (32KB ROM at base_addr)."""
    rom = bytearray(size)
    for pc, bytes_list, _ in code:
        for i, b in enumerate(bytes_list):
            offset = (pc + i) - base_addr
            if 0 <= offset < size:
                rom[offset] = b
    return rom

def make_hex(code):
    """Create hex listing."""
    out = []
    for pc, bytes_list, src in code:
        hex_str = ' '.join(f'${b:02X}' for b in bytes_list)
        out.append(f"${pc:04X}: {hex_str:20s} ; {src}")
    return '\n'.join(out)

def main():
    parser = argparse.ArgumentParser(description='RV8-GR Assembler')
    parser.add_argument('input', help='Input .asm file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-f', '--format', choices=['bin', 'hex'], default='bin')
    parser.add_argument('-b', '--base', default='0x8000', help='Base address (default $8000)')
    args = parser.parse_args()

    base = int(args.base, 0)

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
        else:
            with open(args.output, 'w') as f:
                f.write(make_hex(code))

if __name__ == '__main__':
    main()
