"""External input and clock stimulus helpers for chip simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .core import Board, Chip, Logic, normalize_logic


class StimulusError(ValueError):
    """Raised when an input or clock stimulus request is invalid."""


@dataclass
class PinTarget:
    chip: Chip
    pin: int | str


@dataclass
class InputChannel:
    index: int
    name: str
    targets: list[PinTarget] = field(default_factory=list)
    value: Logic = 0

    def bind(self, chip: Chip, pin: int | str) -> "InputChannel":
        self.targets.append(PinTarget(chip, pin))
        return self

    def set(self, value: Logic, *, settle: bool = True) -> Logic:
        self.value = normalize_logic(value)
        for target in self.targets:
            target.chip.set_input(target.pin, self.value)
        return self.value


class InputSet:
    """One external input header/set with up to 64 channels."""

    def __init__(self, name: str, *, input_count: int = 64):
        if input_count <= 0 or input_count > 64:
            raise StimulusError("input set input_count must be between 1 and 64")
        self.name = name
        self.inputs = [InputChannel(i, f"{name}.IN{i}") for i in range(input_count)]

    def input(self, index: int) -> InputChannel:
        return self.inputs[index]

    def bind(self, index: int, chip: Chip, pin: int | str, *, initial: Logic = 0) -> InputChannel:
        channel = self.input(index).bind(chip, pin)
        channel.set(initial, settle=False)
        return channel

    def set_values(self, values: int | Iterable[Logic], *, width: int | None = None) -> None:
        if isinstance(values, int):
            width = len(self.inputs) if width is None else width
            for i in range(width):
                self.inputs[i].set((values >> i) & 1, settle=False)
        else:
            for channel, value in zip(self.inputs, values):
                channel.set(value, settle=False)

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "input_count": len(self.inputs),
            "inputs": [
                {"index": ch.index, "name": ch.name, "value": ch.value, "targets": _targets(ch.targets)}
                for ch in self.inputs
            ],
        }


@dataclass
class ClockChannel:
    index: int
    name: str
    controller: "StimulusController"
    targets: list[PinTarget] = field(default_factory=list)
    value: int = 0
    enabled: bool = False
    period_ns: int | None = None
    high_ns: int | None = None
    next_edge_ns: int | None = None

    def bind(self, chip: Chip, pin: int | str) -> "ClockChannel":
        self.targets.append(PinTarget(chip, pin))
        return self

    def configure(self, *, frequency_hz: float | None = None, period_ns: int | None = None, duty: float = 0.5) -> "ClockChannel":
        if period_ns is None:
            if frequency_hz is None or frequency_hz <= 0:
                raise StimulusError("clock needs positive frequency_hz or period_ns")
            period_ns = max(1, round(1_000_000_000 / frequency_hz))
        if period_ns <= 0:
            raise StimulusError("period_ns must be positive")
        if not 0 < duty < 1:
            raise StimulusError("duty must be between 0 and 1")
        self.period_ns = int(period_ns)
        self.high_ns = max(1, min(self.period_ns - 1, round(self.period_ns * duty)))
        return self

    def start(self, *, start_high: bool = False, at_ns: int | None = None) -> "ClockChannel":
        if self.period_ns is None or self.high_ns is None:
            self.configure(period_ns=1_000_000)
        self.enabled = True
        self.value = 1 if start_high else 0
        self._drive(self.value)
        now = self.controller.board.time_ns if at_ns is None else at_ns
        self.next_edge_ns = now + (self.high_ns if self.value else self.period_ns - self.high_ns)
        return self

    def stop(self, *, level: int | None = None) -> "ClockChannel":
        self.enabled = False
        self.next_edge_ns = None
        if level is not None:
            self.value = 1 if level else 0
            self._drive(self.value)
        return self

    def trigger(self, *, width_ns: int | None = None, active: int = 1) -> None:
        if width_ns is None:
            width_ns = self.high_ns or 1
        if width_ns <= 0:
            raise StimulusError("width_ns must be positive")
        idle = 0 if active else 1
        if self.value != idle:
            self.value = idle
            self._drive(self.value)
        self._transition(1 if active else 0)
        self.controller.board.settle()
        self.controller.advance(width_ns)
        self._transition(idle)
        self.controller.board.settle()

    def _due(self, end_ns: int) -> bool:
        return self.enabled and self.next_edge_ns is not None and self.next_edge_ns <= end_ns

    def _toggle_at_next_edge(self) -> None:
        if self.next_edge_ns is None or self.period_ns is None or self.high_ns is None:
            return
        self.controller.board.time_ns = max(self.controller.board.time_ns, self.next_edge_ns)
        self._transition(0 if self.value else 1)
        self.controller.board.settle()
        self.next_edge_ns = self.controller.board.time_ns + (self.high_ns if self.value else self.period_ns - self.high_ns)

    def _transition(self, new_value: int) -> None:
        old_value = self.value
        self.value = 1 if new_value else 0
        self._drive(self.value)
        if old_value == 0 and self.value == 1:
            self._clock_targets("rising")
        elif old_value == 1 and self.value == 0:
            self._clock_targets("falling")

    def _drive(self, value: int) -> None:
        for target in self.targets:
            target.chip.set_input(target.pin, 1 if value else 0)

    def _clock_targets(self, edge: str) -> None:
        seen = set()
        for target in self.targets:
            ident = (id(target.chip), target.pin)
            if ident not in seen:
                trigger_edge = target.chip.clock_edge_for_pin(target.pin)
                if trigger_edge in (edge, "both"):
                    try:
                        target.chip.clock_edge(target.pin)
                    except TypeError:
                        target.chip.clock_edge()
                seen.add(ident)


class StimulusController:
    """External input sets and clocks for first-state and runtime stimulus."""

    def __init__(self, board: Board, *, input_count: int = 64, clock_count: int = 8):
        if input_count <= 0 or clock_count <= 0:
            raise StimulusError("input_count and clock_count must be positive")
        self.board = board
        self.input_sets: dict[str, InputSet] = {}
        self.default_inputs = self.input_set("default", input_count=input_count)
        self.inputs = self.default_inputs.inputs
        self.clocks = [ClockChannel(i, f"CLK{i}", self) for i in range(clock_count)]

    def input_set(self, name: str, *, input_count: int = 64) -> InputSet:
        if name in self.input_sets:
            input_set = self.input_sets[name]
            if len(input_set.inputs) != input_count:
                raise StimulusError(f"input set {name} already exists with {len(input_set.inputs)} channels")
            return input_set
        input_set = InputSet(name, input_count=input_count)
        self.input_sets[name] = input_set
        return input_set

    def input(self, index: int) -> InputChannel:
        return self.default_inputs.input(index)

    def clock(self, index: int) -> ClockChannel:
        return self.clocks[index]

    def bind_input(self, index: int, chip: Chip, pin: int | str, *, initial: Logic = 0) -> InputChannel:
        return self.default_inputs.bind(index, chip, pin, initial=initial)

    def bind_clock(self, index: int, chip: Chip, pin: int | str, *, initial: int = 0) -> ClockChannel:
        channel = self.clock(index).bind(chip, pin)
        channel.value = 1 if initial else 0
        channel._drive(channel.value)
        return channel

    def set_inputs(self, values: int | Iterable[Logic], *, width: int | None = None, settle: bool = True) -> None:
        self.default_inputs.set_values(values, width=width)
        if settle:
            self.board.settle()

    def snapshot(self) -> dict:
        return {
            "time_ns": self.board.time_ns,
            "inputs": [{"index": ch.index, "name": ch.name, "value": ch.value, "targets": _targets(ch.targets)} for ch in self.inputs],
            "input_sets": [input_set.snapshot() for input_set in self.input_sets.values()],
            "clocks": [
                {
                    "index": ch.index,
                    "name": ch.name,
                    "value": ch.value,
                    "enabled": ch.enabled,
                    "period_ns": ch.period_ns,
                    "high_ns": ch.high_ns,
                    "next_edge_ns": ch.next_edge_ns,
                    "targets": _targets(ch.targets),
                }
                for ch in self.clocks
            ],
        }

    def advance(self, duration_ns: int) -> int:
        if duration_ns < 0:
            raise StimulusError("duration_ns must be non-negative")
        end_ns = self.board.time_ns + duration_ns
        while True:
            due = [clk for clk in self.clocks if clk._due(end_ns)]
            if not due:
                break
            next_time = min(clk.next_edge_ns for clk in due if clk.next_edge_ns is not None)
            for clk in [c for c in due if c.next_edge_ns == next_time]:
                clk._toggle_at_next_edge()
        self.board.time_ns = max(self.board.time_ns, end_ns)
        return self.board.time_ns

    def run_for(self, duration_ns: int) -> int:
        return self.advance(duration_ns)


def _targets(targets: list[PinTarget]) -> list[dict[str, int | str]]:
    return [{"chip": target.chip.name, "pin": target.pin} for target in targets]
