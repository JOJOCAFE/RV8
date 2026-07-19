#!/usr/bin/env python3
"""RV4-Tiny simulator.

Models the architectural state transitions from 09_simulator_spec.md. The
interface follows the RV8GR-V2 Python sim style: a small CPU class, explicit
loaders, probeable signals, trace rows, and self-tests that fail loudly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import sys


class IllegalInstruction(Exception):
    """Raised when an EXECUTE step sees a reserved opcode."""


class ImageError(ValueError):
    """Raised when a ROM/RAM image is malformed."""


class Phase(Enum):
    FETCH = 0
    EXECUTE = 1


@dataclass
class RV4Tiny:
    rom: list[int] = field(default_factory=lambda: [0xF0] * 16)
    ram: list[int] = field(default_factory=lambda: [0x0] * 16)
    pc: int = 0
    ir: int = 0
    ac: int = 0
    out: int = 0
    inp: int = 0
    phase: Phase = Phase.FETCH
    halt: int = 0
    edge: int = 0

    def reset(self) -> None:
        self.pc = 0
        self.ir = 0
        self.ac = 0
        self.out = 0
        self.inp = 0
        self.phase = Phase.FETCH
        self.halt = 0
        self.edge = 0

    @property
    def z(self) -> int:
        return 1 if self.ac == 0 else 0

    def load_rom(self, values: list[int]) -> None:
        self.rom = _load_fixed(values, 16, 0xFF, 0xF0, "ROM")

    def load_ram(self, values: list[int]) -> None:
        self.ram = _load_fixed(values, 16, 0x0F, 0x0, "RAM")

    def set_input(self, value: int) -> None:
        if not 0 <= value <= 0xF:
            raise ImageError(f"IN value out of range: {value}")
        self.inp = value

    def probes(self) -> dict[str, int | str]:
        op = (self.ir >> 4) & 0xF
        arg = self.ir & 0xF
        sw_n = 0 if self.phase is Phase.EXECUTE and op == 0x8 else 1
        pc_load_n = 0 if self.phase is Phase.EXECUTE and (
            op == 0xB or (op == 0xA and self.z)
        ) else 1
        return {
            "phase": self.phase.name,
            "PC": self.pc,
            "IR": self.ir,
            "OP": op,
            "ARG": arg,
            "AC": self.ac,
            "OUT": self.out,
            "IN": self.inp,
            "Z": self.z,
            "HALT": self.halt,
            "SW_N": sw_n,
            "PC_LOAD_N": pc_load_n,
        }

    def trace_row(self, before: Phase, after: Phase) -> str:
        return (
            f"{self.edge:03d} {before.name}->{after.name} "
            f"PC={self.pc:X} IR={self.ir:02X} AC={self.ac:X} "
            f"OUT={self.out:X} IN={self.inp:X} Z={self.z} HALT={self.halt}"
        )

    def step(self) -> str:
        """Run one rising CPU clock edge and return a trace row."""
        if self.halt:
            before = self.phase
            self.edge += 1
            return self.trace_row(before, self.phase)

        before_state = self._snapshot()
        before_phase = self.phase

        if self.phase is Phase.FETCH:
            self.ir = self.rom[self.pc]
            self.pc = (self.pc + 1) & 0xF
            self.phase = Phase.EXECUTE
        else:
            try:
                self._execute()
            except IllegalInstruction:
                self._restore(before_state)
                raise
            self.phase = Phase.FETCH

        self._check_invariants()
        self.edge += 1
        return self.trace_row(before_phase, self.phase)

    def run(self, edge_limit: int) -> tuple[str, list[str]]:
        if edge_limit <= 0:
            raise ImageError("edge_limit must be positive")
        trace: list[str] = []
        for _ in range(edge_limit):
            try:
                trace.append(self.step())
            except IllegalInstruction:
                return "illegal instruction", trace
            if self.halt:
                return "halted", trace
        return "edge limit reached", trace

    def _execute(self) -> None:
        op = (self.ir >> 4) & 0xF
        arg = self.ir & 0xF

        if op == 0x0:
            pass
        elif op == 0x4:
            self.ac = arg
        elif op == 0x5:
            self.ac = self.ram[arg]
        elif op == 0x6:
            self.ac = (self.ac + self.ram[arg]) & 0xF
        elif op == 0x7:
            self.ac = self.inp
        elif op == 0x8:
            self.ram[arg] = self.ac
        elif op == 0x9:
            self.out = self.ac
        elif op == 0xA:
            if self.z:
                self.pc = arg
        elif op == 0xB:
            self.pc = arg
        elif op == 0xF:
            self.halt = 1
        else:
            raise IllegalInstruction(f"reserved opcode ${op:X}")

    def _snapshot(self) -> tuple[int, int, int, int, int, Phase, int, list[int]]:
        return (self.pc, self.ir, self.ac, self.out, self.inp, self.phase, self.halt, self.ram.copy())

    def _restore(self, state: tuple[int, int, int, int, int, Phase, int, list[int]]) -> None:
        self.pc, self.ir, self.ac, self.out, self.inp, self.phase, self.halt, ram = state
        self.ram = ram

    def _check_invariants(self) -> None:
        for name, value in [("PC", self.pc), ("AC", self.ac), ("OUT", self.out), ("IN", self.inp)]:
            assert 0 <= value <= 0xF, f"{name} out of range: {value}"
        assert 0 <= self.ir <= 0xFF, f"IR out of range: {self.ir}"
        assert len(self.rom) == 16 and len(self.ram) == 16
        assert all(0 <= x <= 0xFF for x in self.rom)
        assert all(0 <= x <= 0xF for x in self.ram)


def _load_fixed(values: list[int], size: int, mask: int, fill: int, name: str) -> list[int]:
    if len(values) > size:
        raise ImageError(f"{name} image has more than {size} entries")
    out = [fill] * size
    for i, value in enumerate(values):
        if not isinstance(value, int) or value < 0 or value > mask:
            raise ImageError(f"{name}[{i}] out of range: {value}")
        out[i] = value
    return out


def parse_hex_lines(text: str, nibble: bool = False) -> list[int]:
    values: list[int] = []
    limit = 0xF if nibble else 0xFF
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        try:
            value = int(line, 16)
        except ValueError as exc:
            raise ImageError(f"line {lineno}: invalid hex value {line!r}") from exc
        if not 0 <= value <= limit:
            raise ImageError(f"line {lineno}: value out of range {line!r}")
        values.append(value)
    return values


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def self_test() -> None:
    cpu = RV4Tiny()
    cpu.load_rom([0x00] * 16)
    for _ in range(32):
        cpu.step()
    _expect(cpu.pc == 0, "PC wrap failed")

    for value in range(16):
        cpu = RV4Tiny()
        cpu.load_rom([0x40 | value, 0xF0])
        cpu.step(); cpu.step()
        _expect(cpu.ac == value, f"LI {value:X} failed")

    for addr in range(16):
        cpu = RV4Tiny()
        cpu.load_rom([0x4A, 0x80 | addr, 0x50 | addr, 0x90, 0xF0])
        outcome, _ = cpu.run(20)
        _expect(outcome == "halted", "RAM program did not halt")
        _expect(cpu.ram[addr] == 0xA and cpu.out == 0xA, f"RAM addr {addr:X} failed")

    for a in range(16):
        for b in range(16):
            cpu = RV4Tiny()
            cpu.load_ram([b])
            cpu.load_rom([0x40 | a, 0x60, 0x90, 0xF0])
            outcome, _ = cpu.run(20)
            _expect(outcome == "halted", "ADD program did not halt")
            _expect(cpu.out == ((a + b) & 0xF), f"ADD {a:X}+{b:X} failed")

    cpu = RV4Tiny()
    cpu.set_input(0xC)
    cpu.load_rom([0x70, 0x90, 0x40, 0xF0])
    outcome, _ = cpu.run(20)
    _expect(outcome == "halted" and cpu.out == 0xC and cpu.ac == 0, "IN/OUT failed")

    for target in range(16):
        cpu = RV4Tiny()
        cpu.load_rom([0xB0 | target])
        cpu.step(); cpu.step()
        _expect(cpu.pc == target, f"J {target:X} failed")

    cpu = RV4Tiny()
    cpu.load_rom([0x40, 0xA5])
    cpu.step(); cpu.step(); cpu.step(); cpu.step()
    _expect(cpu.pc == 5, "JZ taken failed")
    cpu = RV4Tiny()
    cpu.load_rom([0x41, 0xA5])
    cpu.step(); cpu.step(); cpu.step(); cpu.step()
    _expect(cpu.pc == 2, "JZ not-taken failed")

    cpu = RV4Tiny()
    cpu.load_rom([0xF0, 0x41])
    outcome, _ = cpu.run(10)
    pc, ac, phase = cpu.pc, cpu.ac, cpu.phase
    cpu.step(); cpu.step()
    _expect(outcome == "halted" and (cpu.pc, cpu.ac, cpu.phase) == (pc, ac, phase), "HLT failed")

    for op in (0x1, 0x2, 0x3, 0xC, 0xD, 0xE):
        cpu = RV4Tiny()
        cpu.load_rom([op << 4])
        cpu.step()
        state = cpu._snapshot()
        try:
            cpu.step()
        except IllegalInstruction:
            pass
        else:
            raise AssertionError(f"reserved opcode {op:X} did not fail")
        _expect(cpu._snapshot() == state, f"reserved opcode {op:X} changed state")

    for byte in (0x0F, 0x7A, 0x9B, 0xFE):
        cpu = RV4Tiny()
        cpu.set_input(3)
        cpu.load_rom([byte])
        cpu.step(); cpu.step()
        if byte >> 4 == 0x7:
            _expect(cpu.ac == 3, "noncanonical IN failed")
        elif byte >> 4 == 0x9:
            _expect(cpu.out == 0, "noncanonical OUT failed")
        elif byte >> 4 == 0xF:
            _expect(cpu.halt == 1, "noncanonical HLT failed")

    try:
        RV4Tiny().load_rom([0] * 17)
    except ImageError:
        pass
    else:
        raise AssertionError("oversized ROM image accepted")
    cpu = RV4Tiny()
    outcome, _ = cpu.run(1)
    _expect(outcome == "edge limit reached", "edge limit outcome failed")

    print("RV4-Tiny simulator self-test PASS")


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] == "--self-test":
        self_test()
        return 0
    print("usage: rv4_sim.py [--self-test]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
