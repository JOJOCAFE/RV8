"""Pin, net, and event primitives for reusable chip simulation."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Callable

Z = "Z"
X = "X"
Logic = int | str


class BusConflictError(RuntimeError):
    """Raised when two enabled outputs drive a net to different logic levels."""


@dataclass
class LogicSource:
    name: str
    value: Logic
    enabled: bool = True

    def drive(self, value: Logic) -> None:
        self.value = normalize_logic(value)


@dataclass
class Rail:
    name: str
    value: Logic


@dataclass(frozen=True)
class Delay:
    rise_ns: int
    fall_ns: int | None = None

    def for_change(self, old: Logic, new: Logic) -> int:
        if old == new:
            return 0
        if new == 1:
            return self.rise_ns
        if new == 0:
            return self.fall_ns if self.fall_ns is not None else self.rise_ns
        return max(self.rise_ns, self.fall_ns or self.rise_ns)


@dataclass(frozen=True)
class PinSpec:
    number: int
    name: str
    direction: str
    active_low: bool = False


class Pin:
    def __init__(self, chip: "Chip", spec: PinSpec):
        self.chip = chip
        self.spec = spec
        self.value: Logic = Z if spec.direction in ("out", "bidir") else 0
        self.pull: Logic | None = None
        self.external_drive = False
        self.net: Net | None = None

    @property
    def number(self) -> int:
        return self.spec.number

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def direction(self) -> str:
        return self.spec.direction

    def drive(self, value: Logic) -> None:
        self.value = normalize_logic(value)
        if self.net:
            self.net.resolve()

    def sample(self) -> Logic:
        if self.net:
            return self.net.value
        if self.pull is not None and not self.external_drive:
            return self.pull
        return self.value


class Net:
    def __init__(self, name: str):
        self.name = name
        self.pins: list[Pin] = []
        self.pulls: list[tuple[str, Logic]] = []
        self.sources: list[LogicSource] = []
        self.value: Logic = Z

    def connect(self, pin: Pin) -> None:
        if pin.net is not None and pin.net is not self:
            raise ValueError(f"{pin.chip.name}.{pin.name} is already connected to {pin.net.name}")
        if pin not in self.pins:
            self.pins.append(pin)
            pin.net = self
            if pin.pull is not None:
                self.pull(pin.pull, source=f"{pin.chip.name}.{pin.name}")
        self.resolve()

    def pull(self, value: Logic, *, source: str = "pull") -> None:
        value = normalize_logic(value)
        if value not in (0, 1):
            raise ValueError("pull value must be 0 or 1")
        existing = {pull_value for _, pull_value in self.pulls}
        if existing and value not in existing:
            detail = ", ".join(f"{pull_source}:{pull_value}" for pull_source, pull_value in self.pulls)
            raise BusConflictError(f"{self.name} has conflicting pulls: {detail}, {source}:{value}")
        self.pulls.append((source, value))
        self.resolve()

    def connect_source(self, source: LogicSource) -> None:
        if source not in self.sources:
            self.sources.append(source)
        self.resolve()

    def resolve(self) -> Logic:
        pin_drivers = [
            pin for pin in self.pins
            if pin.direction in ("out", "bidir") and pin.value != Z
        ]
        source_drivers = [source for source in self.sources if source.enabled and source.value != Z]
        driver_values = [pin.value for pin in pin_drivers] + [source.value for source in source_drivers]
        driven_values = set(driver_values)
        if len(driven_values) > 1:
            detail = ", ".join(
                [f"{p.chip.name}.{p.number}:{p.value}" for p in pin_drivers]
                + [f"{s.name}:{s.value}" for s in source_drivers]
            )
            raise BusConflictError(f"{self.name} has conflicting drivers: {detail}")
        if driver_values:
            self.value = driver_values[0]
        elif self.pulls:
            self.value = self.pulls[0][1]
        else:
            self.value = Z
        for pin in self.pins:
            if pin.direction in ("in", "power", "nc"):
                pin.value = self.value
        return self.value


class Bus:
    def __init__(self, board: "Board", name: str, width: int = 128):
        if width <= 0 or width > 128:
            raise ValueError("bus width must be between 1 and 128")
        self.board = board
        self.name = name
        self.width = width

    def tag(self, index: int) -> str:
        self._check_index(index)
        return f"bus:{self.name}[{index}]"

    def line(self, index: int) -> Net:
        return self.board.net(self.tag(index))

    def connect(self, index: int, chip: "Chip", pin: int | str) -> None:
        self.line(index).connect(chip.pin(pin))

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "lines": [
                {
                    "index": index,
                    "tag": self.tag(index),
                    "value": self.line(index).value,
                    "pins": [
                        {"chip": pin.chip.name, "pin": pin.name, "number": pin.number}
                        for pin in self.line(index).pins
                    ],
                }
                for index in range(self.width)
            ],
        }

    def _check_index(self, index: int) -> None:
        if index < 0 or index >= self.width:
            raise IndexError(f"bus {self.name} index {index} outside 0..{self.width - 1}")


class Chip:
    part = "GENERIC"

    def __init__(self, name: str, pin_specs: list[PinSpec], delay: Delay | int = 10):
        self.name = name
        self.delay = delay if isinstance(delay, Delay) else Delay(delay)
        self.pins = {spec.number: Pin(self, spec) for spec in pin_specs}
        self.pin_names = {spec.name: spec.number for spec in pin_specs}
        self._pending: list[tuple[int, Logic]] = []

    def pin_number(self, pin: int | str) -> int:
        if isinstance(pin, int):
            return pin
        if pin in self.pin_names:
            return self.pin_names[pin]
        raise KeyError(f"{self.name} has no pin {pin!r}")

    def pin(self, pin: int | str) -> Pin:
        return self.pins[self.pin_number(pin)]

    def read(self, pin: int | str) -> Logic:
        return self.pin(pin).sample()

    def set_input(self, pin: int | str, value: Logic) -> None:
        p = self.pin(pin)
        p.value = normalize_logic(value)
        p.external_drive = True
        if p.net:
            p.net.resolve()

    def drive_output(self, pin: int | str, value: Logic) -> None:
        self.pin(pin).drive(value)

    def output(self, pin: int | str, value: Logic) -> None:
        number = self.pin_number(pin)
        new_value = normalize_logic(value)
        if self.pins[number].value != new_value:
            self._pending.append((number, new_value))

    def commit(self) -> None:
        pending = self._pending
        self._pending = []
        for pin, value in pending:
            self.drive_output(pin, value)

    def update(self) -> None:
        pass

    def clock_edge_for_pin(self, pin: int | str | None = None) -> str:
        return "rising"

    def clock_edge(self, pin: int | str | None = None) -> None:
        pass


class Board:
    def __init__(self):
        self.time_ns = 0
        self.chips: dict[str, Chip] = {}
        self.nets: dict[str, Net] = {}
        self.buses: dict[str, Bus] = {}
        self.rails: dict[str, Rail] = {}
        self.sources: dict[str, LogicSource] = {}
        self._events: list[tuple[int, int, Callable[[], None]]] = []
        self._counter = count()

    def add_chip(self, ref: str, chip: Chip) -> Chip:
        self.chips[ref] = chip
        return chip

    def net(self, name: str) -> Net:
        if name not in self.nets:
            self.nets[name] = Net(name)
        return self.nets[name]

    def bus(self, name: str, width: int = 128) -> Bus:
        if name in self.buses:
            bus = self.buses[name]
            if bus.width != width:
                raise ValueError(f"bus {name} already exists with width {bus.width}")
            return bus
        bus = Bus(self, name, width)
        self.buses[name] = bus
        return bus

    def connect(self, net_name: str, chip: Chip, pin: int | str) -> None:
        self.net(net_name).connect(chip.pin(pin))

    def connect_bus(self, bus_name: str, index: int, chip: Chip, pin: int | str, *, width: int | None = None) -> None:
        bus = self.buses[bus_name] if bus_name in self.buses and width is None else self.bus(bus_name, 128 if width is None else width)
        bus.connect(index, chip, pin)

    def attach(self, tag: str, chip: Chip, pin: int | str) -> None:
        bus_tag = parse_bus_tag(tag)
        if bus_tag is None:
            self.connect(tag, chip, pin)
            return
        bus_name, index = bus_tag
        self.connect_bus(bus_name, index, chip, pin)

    def drive(self, chip: Chip, pin: int | str, value: Logic) -> None:
        chip.set_input(pin, value)

    def pullup(self, target: str) -> None:
        self.pull(target, 1)

    def pulldown(self, target: str) -> None:
        self.pull(target, 0)

    def pull(self, target: str, value: Logic) -> None:
        bus_tag = parse_bus_tag(target)
        if bus_tag is not None:
            bus_name, index = bus_tag
            bus = self.buses[bus_name] if bus_name in self.buses else self.bus(bus_name)
            bus.line(index).pull(value, source=target)
            return
        self.net(target).pull(value, source=target)

    def pullup_pin(self, chip: Chip, pin: int | str) -> None:
        self.pull_pin(chip, pin, 1)

    def pulldown_pin(self, chip: Chip, pin: int | str) -> None:
        self.pull_pin(chip, pin, 0)

    def pull_pin(self, chip: Chip, pin: int | str, value: Logic) -> None:
        value = normalize_logic(value)
        if value not in (0, 1):
            raise ValueError("pull value must be 0 or 1")
        target = chip.pin(pin)
        target.pull = value
        if target.net:
            target.net.pull(value, source=f"{chip.name}.{target.name}")

    def power(self, name: str, value: Logic) -> Rail:
        value = normalize_logic(value)
        if value not in (0, 1):
            raise ValueError("rail value must be 0 or 1")
        if name in self.rails:
            rail = self.rails[name]
            if rail.value != value:
                raise ValueError(f"rail {name} already exists with value {rail.value}")
            return rail
        rail = Rail(name, value)
        self.rails[name] = rail
        return rail

    def attach_rail(self, rail_name: str, target: str) -> LogicSource:
        if rail_name not in self.rails:
            default = 0 if rail_name.upper() in ("GND", "GROUND", "VSS") else 1
            self.power(rail_name, default)
        rail = self.rails[rail_name]
        return self.logic_source(f"rail:{rail.name}->{target}", target, rail.value)

    def vcc(self, target: str, *, rail: str = "VCC") -> LogicSource:
        self.power(rail, 1)
        return self.attach_rail(rail, target)

    def ground(self, target: str, *, rail: str = "GND") -> LogicSource:
        self.power(rail, 0)
        return self.attach_rail(rail, target)

    def logic_source(self, name: str, target: str, value: Logic = 0, *, enabled: bool = True) -> LogicSource:
        if name in self.sources:
            raise ValueError(f"logic source {name} already exists")
        source = LogicSource(name, normalize_logic(value), enabled)
        self.sources[name] = source
        self.net_for_tag(target).connect_source(source)
        return source

    def set_source(self, name: str, value: Logic, *, enabled: bool | None = None) -> Logic:
        source = self.sources[name]
        source.drive(value)
        if enabled is not None:
            source.enabled = enabled
        for net in self.nets.values():
            if source in net.sources:
                net.resolve()
        return source.value

    def net_for_tag(self, tag: str) -> Net:
        bus_tag = parse_bus_tag(tag)
        if bus_tag is not None:
            bus_name, index = bus_tag
            bus = self.buses[bus_name] if bus_name in self.buses else self.bus(bus_name)
            return bus.line(index)
        return self.net(tag)

    def errors(self) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        for net in self.nets.values():
            pin_drivers = [
                pin for pin in net.pins
                if pin.direction in ("out", "bidir") and pin.value != Z
            ]
            source_drivers = [source for source in net.sources if source.enabled and source.value != Z]
            driver_values = {pin.value for pin in pin_drivers} | {source.value for source in source_drivers}
            if len(driver_values) > 1:
                errors.append({
                    "type": "driver_conflict",
                    "net": net.name,
                    "detail": ", ".join(
                        [f"{pin.chip.name}.{pin.name}:{pin.value}" for pin in pin_drivers]
                        + [f"{source.name}:{source.value}" for source in source_drivers]
                    ),
                })
            pull_values = {value for _, value in net.pulls}
            if len(pull_values) > 1:
                errors.append({
                    "type": "pull_conflict",
                    "net": net.name,
                    "detail": ", ".join(f"{source}:{value}" for source, value in net.pulls),
                })
        return errors

    def snapshot(self) -> dict:
        return {
            "time_ns": self.time_ns,
            "chips": [
                {
                    "ref": ref,
                    "name": chip.name,
                    "part": chip.part,
                    "pins": [pin_snapshot(pin) for pin in chip.pins.values()],
                }
                for ref, chip in self.chips.items()
            ],
            "nets": [net_snapshot(net) for net in self.nets.values()],
            "buses": [bus.snapshot() for bus in self.buses.values()],
            "rails": [
                {"name": rail.name, "value": rail.value}
                for rail in self.rails.values()
            ],
            "sources": [
                {"name": source.name, "value": source.value, "enabled": source.enabled}
                for source in self.sources.values()
            ],
            "errors": self.errors(),
        }

    def schedule(self, delay_ns: int, callback: Callable[[], None]) -> None:
        heappush(self._events, (self.time_ns + delay_ns, next(self._counter), callback))

    def evaluate(self) -> None:
        for chip in self.chips.values():
            chip.update()
            for pin, value in chip._pending:
                delay = chip.delay.for_change(chip.pins[pin].value, value)
                self.schedule(delay, lambda c=chip, p=pin, v=value: c.drive_output(p, v))
            chip._pending = []

    def settle(self, max_events: int = 10000) -> None:
        self.evaluate()
        events = 0
        while self._events:
            when, _, callback = heappop(self._events)
            self.time_ns = when
            callback()
            while self._events and self._events[0][0] == when:
                _, _, same_time_callback = heappop(self._events)
                same_time_callback()
            self.evaluate()
            events += 1
            if events > max_events:
                raise RuntimeError("event queue did not settle")

    def clock_edge(self) -> None:
        for chip in self.chips.values():
            chip.clock_edge()
        self.settle()


def normalize_logic(value: Logic) -> Logic:
    if value in (0, 1, Z, X):
        return value
    if value is True:
        return 1
    if value is False:
        return 0
    raise ValueError(f"invalid logic value {value!r}")


def bit(value: Logic) -> int:
    return 1 if value == 1 else 0


def pins_from(defs: dict[int, tuple[str, str]]) -> list[PinSpec]:
    return [
        PinSpec(number, name, direction, name.startswith("/"))
        for number, (name, direction) in sorted(defs.items())
    ]


def parse_bus_tag(tag: str) -> tuple[str, int] | None:
    if not tag.startswith("bus:") or not tag.endswith("]") or "[" not in tag:
        return None
    name, index_text = tag[4:-1].split("[", 1)
    if not name or not index_text.isdigit():
        raise ValueError(f"invalid bus tag {tag!r}")
    return name, int(index_text)


def pin_snapshot(pin: Pin) -> dict:
    return {
        "chip": pin.chip.name,
        "number": pin.number,
        "name": pin.name,
        "direction": pin.direction,
        "active_low": pin.spec.active_low,
        "value": pin.sample(),
        "drive_value": pin.value,
        "pull": pin.pull,
        "net": pin.net.name if pin.net else None,
    }


def net_snapshot(net: Net) -> dict:
    return {
        "name": net.name,
        "value": net.value,
        "pins": [pin_snapshot(pin) for pin in net.pins],
        "pulls": [{"source": source, "value": value} for source, value in net.pulls],
        "sources": [
            {"name": source.name, "value": source.value, "enabled": source.enabled}
            for source in net.sources
        ],
    }
