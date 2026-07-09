"""Probe and assertion helpers for simulator inspection."""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import Board, Bus, Chip, Logic, Net, Pin, parse_bus_tag, normalize_logic


class ProbeError(AssertionError):
    """Raised when a probe assertion fails."""


@dataclass(frozen=True)
class ProbeSample:
    time_ns: int
    value: Logic

    def snapshot(self) -> dict[str, int | str]:
        return {"time_ns": self.time_ns, "value": self.value}


@dataclass
class ProbeChannel:
    index: int
    name: str
    board: Board
    target: Pin | Net
    target_kind: str
    target_name: str
    history: list[ProbeSample] = field(default_factory=list)

    def read(self) -> Logic:
        if isinstance(self.target, Pin):
            return self.target.sample()
        return self.target.value

    def sample(self, *, time_ns: int | None = None) -> Logic:
        sample_time = self.board.time_ns if time_ns is None else time_ns
        value = self.read()
        self.history.append(ProbeSample(sample_time, value))
        return value

    def clear(self) -> None:
        self.history.clear()

    def values(self, *, since_ns: int | None = None, until_ns: int | None = None) -> list[ProbeSample]:
        return [
            sample for sample in self.history
            if (since_ns is None or sample.time_ns >= since_ns)
            and (until_ns is None or sample.time_ns <= until_ns)
        ]

    def transitions(self, *, since_ns: int | None = None, until_ns: int | None = None) -> list[dict[str, int | str]]:
        samples = self.values(since_ns=since_ns, until_ns=until_ns)
        edges: list[dict[str, int | str]] = []
        for old, new in zip(samples, samples[1:]):
            if old.value != new.value:
                edges.append({
                    "time_ns": new.time_ns,
                    "from": old.value,
                    "to": new.value,
                    "edge": edge_name(old.value, new.value),
                })
        return edges

    def count_edges(self, edge: str | None = None, *, since_ns: int | None = None, until_ns: int | None = None) -> int:
        edges = self.transitions(since_ns=since_ns, until_ns=until_ns)
        if edge is None:
            return len(edges)
        return sum(1 for item in edges if item["edge"] == edge)

    def expect(self, expected: Logic, *, at_ns: int | None = None) -> None:
        expected = normalize_logic(expected)
        sample = self._sample_at(at_ns)
        if sample.value != expected:
            where = f" at {sample.time_ns} ns" if at_ns is not None else ""
            raise ProbeError(f"{self.name}{where}: expected {expected!r}, got {sample.value!r}")

    def expect_transition(self, edge: str, *, since_ns: int | None = None, until_ns: int | None = None) -> None:
        if self.count_edges(edge, since_ns=since_ns, until_ns=until_ns) == 0:
            window = format_window(since_ns, until_ns)
            raise ProbeError(f"{self.name}: expected {edge} transition{window}")

    def expect_pulses(self, count: int, *, edge: str = "rising", since_ns: int | None = None, until_ns: int | None = None) -> None:
        actual = self.count_edges(edge, since_ns=since_ns, until_ns=until_ns)
        if actual != count:
            window = format_window(since_ns, until_ns)
            raise ProbeError(f"{self.name}: expected {count} {edge} pulses{window}, got {actual}")

    def expect_stable(self, expected: Logic, *, since_ns: int | None = None, until_ns: int | None = None) -> None:
        expected = normalize_logic(expected)
        samples = self.values(since_ns=since_ns, until_ns=until_ns)
        if not samples:
            raise ProbeError(f"{self.name}: no samples{format_window(since_ns, until_ns)}")
        bad = [sample for sample in samples if sample.value != expected]
        if bad:
            first = bad[0]
            raise ProbeError(f"{self.name}: expected stable {expected!r}, got {first.value!r} at {first.time_ns} ns")

    def snapshot(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "target_kind": self.target_kind,
            "target": self.target_name,
            "value": self.read(),
            "history": [sample.snapshot() for sample in self.history],
        }

    def _sample_at(self, at_ns: int | None) -> ProbeSample:
        if at_ns is None:
            return ProbeSample(self.board.time_ns, self.read())
        candidates = [sample for sample in self.history if sample.time_ns <= at_ns]
        if not candidates:
            raise ProbeError(f"{self.name}: no sample at or before {at_ns} ns")
        return candidates[-1]


class ProbeSet:
    """One probe header/set with up to 64 channels."""

    def __init__(self, board: Board, name: str, *, channel_count: int = 64):
        if channel_count <= 0 or channel_count > 64:
            raise ProbeError("probe set channel_count must be between 1 and 64")
        self.board = board
        self.name = name
        self.channel_count = channel_count
        self.probes: list[ProbeChannel] = []

    def pin(self, name: str, chip: Chip, pin: int | str) -> ProbeChannel:
        target_pin = chip.pin(pin)
        target_name = f"{chip.name}.{target_pin.name}"
        return self._add(name, target_pin, "pin", target_name)

    def net(self, name: str, net: str | Net) -> ProbeChannel:
        target_net = self.board.net(net) if isinstance(net, str) else net
        return self._add(name, target_net, "net", target_net.name)

    def bus(self, name: str, bus: str | Bus, index: int) -> ProbeChannel:
        target_bus = self.board.buses[bus] if isinstance(bus, str) and bus in self.board.buses else self.board.bus(bus) if isinstance(bus, str) else bus
        target_net = target_bus.line(index)
        return self._add(name, target_net, "bus", target_bus.tag(index))

    def tag(self, name: str, tag: str) -> ProbeChannel:
        target_net = self.board.net_for_tag(tag)
        target_kind = "bus" if parse_bus_tag(tag) else "net"
        return self._add(name, target_net, target_kind, tag)

    def sample(self) -> dict[str, Logic]:
        return {probe.name: probe.sample() for probe in self.probes}

    def sample_for(self, duration_ns: int, *, step_ns: int) -> None:
        if duration_ns < 0:
            raise ProbeError("duration_ns must be non-negative")
        if step_ns <= 0:
            raise ProbeError("step_ns must be positive")
        end_ns = self.board.time_ns + duration_ns
        self.sample()
        while self.board.time_ns < end_ns:
            self.board.time_ns = min(end_ns, self.board.time_ns + step_ns)
            self.board.settle()
            self.sample()

    def clear(self) -> None:
        for probe in self.probes:
            probe.clear()

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "channel_count": self.channel_count,
            "time_ns": self.board.time_ns,
            "channels": [probe.snapshot() for probe in self.probes],
        }

    def _add(self, name: str, target: Pin | Net, target_kind: str, target_name: str) -> ProbeChannel:
        if len(self.probes) >= self.channel_count:
            raise ProbeError(f"probe set {self.name} is full ({self.channel_count} channels)")
        probe = ProbeChannel(len(self.probes), name, self.board, target, target_kind, target_name)
        self.probes.append(probe)
        return probe


class ProbeController:
    """Manager for multiple named probe sets."""

    def __init__(self, board: Board):
        self.board = board
        self.sets: dict[str, ProbeSet] = {}
        self.default = self.set("default")

    def set(self, name: str, *, channel_count: int = 64) -> ProbeSet:
        if name in self.sets:
            probe_set = self.sets[name]
            if probe_set.channel_count != channel_count:
                raise ProbeError(f"probe set {name} already exists with {probe_set.channel_count} channels")
            return probe_set
        probe_set = ProbeSet(self.board, name, channel_count=channel_count)
        self.sets[name] = probe_set
        return probe_set

    def pin(self, name: str, chip: Chip, pin: int | str) -> ProbeChannel:
        return self.default.pin(name, chip, pin)

    def net(self, name: str, net: str | Net) -> ProbeChannel:
        return self.default.net(name, net)

    def bus(self, name: str, bus: str | Bus, index: int) -> ProbeChannel:
        return self.default.bus(name, bus, index)

    def tag(self, name: str, tag: str) -> ProbeChannel:
        return self.default.tag(name, tag)

    @property
    def probes(self) -> list[ProbeChannel]:
        return self.default.probes

    def sample(self) -> dict[str, dict[str, Logic]]:
        return {name: probe_set.sample() for name, probe_set in self.sets.items()}

    def sample_for(self, duration_ns: int, *, step_ns: int) -> None:
        if duration_ns < 0:
            raise ProbeError("duration_ns must be non-negative")
        if step_ns <= 0:
            raise ProbeError("step_ns must be positive")
        self.sample()
        end_ns = self.board.time_ns + duration_ns
        while self.board.time_ns < end_ns:
            self.board.time_ns = min(end_ns, self.board.time_ns + step_ns)
            self.board.settle()
            self.sample()

    def clear(self) -> None:
        for probe_set in self.sets.values():
            probe_set.clear()

    def snapshot(self) -> dict:
        return {
            "time_ns": self.board.time_ns,
            "sets": [probe_set.snapshot() for probe_set in self.sets.values()],
        }


def edge_name(old: Logic, new: Logic) -> str:
    if old == 0 and new == 1:
        return "rising"
    if old == 1 and new == 0:
        return "falling"
    return "change"


def format_window(since_ns: int | None, until_ns: int | None) -> str:
    if since_ns is None and until_ns is None:
        return ""
    return f" between {since_ns if since_ns is not None else '-inf'} and {until_ns if until_ns is not None else '+inf'} ns"
