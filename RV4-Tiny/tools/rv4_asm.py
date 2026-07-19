#!/usr/bin/env python3
"""RV4-Tiny assembler.

Implements 10_assembler_spec.md. Produces 16-byte ROM images and 16-nibble RAM
images, with strict range checks and no silent truncation.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import re
import sys
from pathlib import Path


class AssemblerError(Exception):
    """Assembly failed."""


NO_OPERAND = {
    "NOP": 0x00,
    "IN": 0x70,
    "OUT": 0x90,
    "HLT": 0xF0,
}

WITH_OPERAND = {
    "LI": 0x40,
    "LW": 0x50,
    "ADD": 0x60,
    "SW": 0x80,
    "JZ": 0xA0,
    "J": 0xB0,
}

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class SourceLine:
    number: int
    text: str


@dataclass
class ExpandedLine:
    source: SourceLine
    mnemonic: str
    operand: str | None = None


@dataclass
class Assembly:
    rom: list[int]
    ram: list[int]
    listing: list[str]


def assemble_text(text: str) -> Assembly:
    lines = _preprocess(text)
    constants: dict[str, int] = {}
    labels: dict[str, int] = {}
    ram_items: dict[int, int] = {}
    expanded: list[ExpandedLine] = []

    pc = 0
    for line in lines:
        statement = line.text
        if "=" in statement and not statement.startswith(".RAM"):
            name, expr = [part.strip() for part in statement.split("=", 1)]
            _check_name(name, line)
            if name in constants or name in labels:
                raise AssemblerError(f"line {line.number}: duplicate name {name}")
            constants[name] = _eval_expr(expr, constants, labels, line)
            continue

        if statement.endswith(":"):
            name = statement[:-1].strip()
            _check_name(name, line)
            if name in constants or name in labels:
                raise AssemblerError(f"line {line.number}: duplicate name {name}")
            labels[name] = pc
            continue

        if statement.upper().startswith(".RAM"):
            parts = _split_operands(statement[4:].strip(), line, expected=2)
            addr = _eval_expr(parts[0], constants, labels, line)
            value = _eval_expr(parts[1], constants, labels, line)
            _check_nibble(addr, line, "RAM address")
            _check_nibble(value, line, "RAM value")
            if addr in ram_items:
                raise AssemblerError(f"line {line.number}: duplicate RAM address ${addr:X}")
            ram_items[addr] = value
            continue

        insts = _expand_instruction(statement, line)
        if pc + len(insts) > 16:
            raise AssemblerError(f"line {line.number}: program longer than 16 bytes")
        expanded.extend(insts)
        pc += len(insts)

    rom = [0xF0] * 16
    listing: list[str] = []
    for addr, inst in enumerate(expanded):
        byte = _encode(inst, constants, labels)
        rom[addr] = byte
        op_text = f" {inst.operand}" if inst.operand is not None else ""
        listing.append(f"${addr:X}: ${byte:02X} ; line {inst.source.number}: {inst.mnemonic}{op_text}")

    ram = [0x0] * 16
    for addr, value in ram_items.items():
        ram[addr] = value

    return Assembly(rom=rom, ram=ram, listing=listing)


def _preprocess(text: str) -> list[SourceLine]:
    out: list[SourceLine] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if line:
            out.append(SourceLine(number, line))
    return out


def _check_name(name: str, line: SourceLine) -> None:
    if not NAME_RE.match(name):
        raise AssemblerError(f"line {line.number}: invalid name {name!r}")


def _split_operands(text: str, line: SourceLine, expected: int) -> list[str]:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != expected or any(not part for part in parts):
        raise AssemblerError(f"line {line.number}: expected {expected} operands")
    return parts


def _expand_instruction(statement: str, line: SourceLine) -> list[ExpandedLine]:
    parts = statement.replace(",", " ").split()
    if not parts:
        return []
    mnemonic = parts[0].upper()
    operands = parts[1:]

    if mnemonic == "CLR":
        if operands:
            raise AssemblerError(f"line {line.number}: CLR takes no operand")
        return [ExpandedLine(line, "LI", "0")]

    if mnemonic == "JMP":
        if len(operands) != 1:
            raise AssemblerError(f"line {line.number}: JMP requires one operand")
        return [ExpandedLine(line, "J", operands[0])]

    if mnemonic == "INC":
        if len(operands) != 1:
            raise AssemblerError(f"line {line.number}: INC requires one operand")
        return [
            ExpandedLine(line, "LW", operands[0]),
            ExpandedLine(line, "ADD", "ONE"),
            ExpandedLine(line, "SW", operands[0]),
        ]

    if mnemonic in NO_OPERAND:
        if operands:
            raise AssemblerError(f"line {line.number}: {mnemonic} takes no operand")
        return [ExpandedLine(line, mnemonic)]

    if mnemonic in WITH_OPERAND:
        if len(operands) != 1:
            raise AssemblerError(f"line {line.number}: {mnemonic} requires one operand")
        return [ExpandedLine(line, mnemonic, operands[0])]

    raise AssemblerError(f"line {line.number}: unknown instruction {mnemonic}")


def _encode(inst: ExpandedLine, constants: dict[str, int], labels: dict[str, int]) -> int:
    if inst.mnemonic in NO_OPERAND:
        return NO_OPERAND[inst.mnemonic]
    if inst.mnemonic not in WITH_OPERAND or inst.operand is None:
        raise AssemblerError(f"line {inst.source.number}: internal assembler error")
    value = _eval_expr(inst.operand, constants, labels, inst.source)
    _check_nibble(value, inst.source, "operand")
    return WITH_OPERAND[inst.mnemonic] | value


def _eval_expr(expr: str, constants: dict[str, int], labels: dict[str, int], line: SourceLine) -> int:
    expr = expr.strip()
    if not expr:
        raise AssemblerError(f"line {line.number}: missing expression")
    if expr in constants:
        return constants[expr]
    if expr in labels:
        return labels[expr]
    try:
        if expr.startswith("$"):
            return int(expr[1:], 16)
        if expr.lower().startswith("0x"):
            return int(expr, 16)
        if expr.lower().startswith("0b"):
            return int(expr, 2)
        return int(expr, 10)
    except ValueError as exc:
        raise AssemblerError(f"line {line.number}: invalid number or name {expr!r}") from exc


def _check_nibble(value: int, line: SourceLine, what: str) -> None:
    if not 0 <= value <= 0xF:
        raise AssemblerError(f"line {line.number}: {what} out of range: {value}")


def format_rom(rom: list[int]) -> str:
    return "\n".join(f"{byte:02X}" for byte in rom) + "\n"


def format_ram(ram: list[int]) -> str:
    return "\n".join(f"{value:X}" for value in ram) + "\n"


def format_listing(listing: list[str]) -> str:
    return "\n".join(listing) + ("\n" if listing else "")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Assemble RV4-Tiny source")
    parser.add_argument("source", type=Path)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--ram", type=Path)
    parser.add_argument("--lst", type=Path)
    args = parser.parse_args(argv[1:])

    try:
        assembly = assemble_text(args.source.read_text(encoding="utf-8"))
    except (OSError, AssemblerError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.rom:
        args.rom.write_text(format_rom(assembly.rom), encoding="utf-8")
    else:
        print(format_rom(assembly.rom), end="")
    if args.ram:
        args.ram.write_text(format_ram(assembly.ram), encoding="utf-8")
    if args.lst:
        args.lst.write_text(format_listing(assembly.listing), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
