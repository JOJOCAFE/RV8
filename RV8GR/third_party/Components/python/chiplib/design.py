"""Scriptable design model for schematic JSON files."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .chips import create_chip
from .core import Board, Logic, normalize_logic
from .db import load_component
from .loader import load_memory
from .netlist import design_from_kicad_netlist, design_from_netlist, design_to_netlist
from .probe import ProbeChannel, ProbeController
from .services import export_verilog
from .stimulus import StimulusController


JsonMap = dict[str, Any]


@dataclass(frozen=True)
class Endpoint:
    """One resolved schematic reference."""

    ref: str
    kind: str
    target: str
    chip: str | None = None
    pin: int | str | None = None
    bus: str | None = None
    index: int | None = None
    rail: str | None = None

    def snapshot(self) -> JsonMap:
        data: JsonMap = {"ref": self.ref, "kind": self.kind, "target": self.target}
        if self.chip is not None:
            data["chip"] = self.chip
            data["pin"] = self.pin
        if self.bus is not None:
            data["bus"] = self.bus
            data["index"] = self.index
        if self.rail is not None:
            data["rail"] = self.rail
        return data


class Design:
    """Normalized, JSON-round-trippable schematic design.

    The class intentionally stays close to the JSON contract. Sections that the
    simulator cannot execute yet are retained and returned by ``to_dict()`` and
    ``snapshot()`` so the UI/CLI can round-trip them without hidden state.
    """

    def __init__(self, name: str):
        self.name = name
        self.description = ""
        self.chips: JsonMap = {}
        self.buses: JsonMap = {}
        self.aliases: dict[str, str] = {}
        self.groups: dict[str, list[str]] = {}
        self.modules: JsonMap = {}
        self.rails: dict[str, Logic] = {"VCC": 1, "GND": 0}
        self.connections: list[str] = []
        self.pullups: list[str] = []
        self.pulldowns: list[str] = []
        self.inputs: dict[str, list[str]] = {}
        self.input_sets: JsonMap = {}
        self.clocks: JsonMap = {}
        self.controls: JsonMap = {}
        self.memory_images: JsonMap = {}
        self.probes: JsonMap = {}
        self.displays: JsonMap = {}
        self.expect: JsonMap = {}
        self.steps: list[str] = []
        self.validate_config: JsonMap = {}
        self.extra: JsonMap = {}
        self._board: Board | None = None
        self.stimulus: StimulusController | None = None
        self.probe_controller: ProbeController | None = None
        self._component_cache: dict[str, JsonMap | None] = {}

    @classmethod
    def from_dict(cls, data: JsonMap) -> "Design":
        design = cls(str(data.get("name", "design")))
        design.description = str(data.get("description", ""))
        design.chips = _named_map(data.get("chips", {}), "ref")
        design.buses = _named_map(data.get("buses", {}), "name")
        design.aliases = {str(k): str(v) for k, v in data.get("aliases", {}).items()}
        design.groups = {str(k): [str(item) for item in v] for k, v in data.get("groups", {}).items()}
        design.modules = _copy_map(data.get("modules", {}))
        design.rails = {str(k): normalize_logic(v) for k, v in data.get("rails", design.rails).items()}
        design.connections = [str(item) for item in data.get("connect", data.get("connections", []))]
        design.pullups = [str(item) for item in data.get("pullups", [])]
        design.pulldowns = [str(item) for item in data.get("pulldowns", [])]
        design.inputs = _input_rules(data.get("inputs", {}))
        design.input_sets = _named_map(data.get("input_sets", {}), "name")
        design.clocks = _copy_map(data.get("clocks", {}))
        design.controls = _copy_map(data.get("controls", {}))
        design.memory_images = _copy_map(data.get("memory_images", {}))
        design.probes = _probe_map(data.get("probes", {}))
        design.displays = _copy_map(data.get("displays", {}))
        design.expect = _copy_map(data.get("expect", {}))
        design.steps = [str(item) for item in data.get("steps", [])]
        design.validate_config = _copy_map(data.get("validate", {}))
        known = {
            "name", "description", "chips", "buses", "aliases", "groups", "modules",
            "rails", "connect", "connections", "pullups", "pulldowns", "inputs", "input_sets",
            "clocks", "controls", "memory_images", "probes", "displays", "expect",
            "steps", "validate",
        }
        design.extra = {str(k): deepcopy(v) for k, v in data.items() if k not in known}
        return design

    @classmethod
    def load_json(cls, path: str | Path) -> "Design":
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("design JSON root must be an object")
        return cls.from_dict(data)

    @classmethod
    def from_netlist(cls, data: JsonMap) -> "Design":
        return design_from_netlist(data, cls)

    @classmethod
    def from_kicad_netlist(cls, path: str | Path, *, name: str | None = None) -> "Design":
        return design_from_kicad_netlist(path, cls, name=name)

    def to_dict(self) -> JsonMap:
        data: JsonMap = {
            "name": self.name,
            "description": self.description,
            "chips": deepcopy(self.chips),
            "buses": deepcopy(self.buses),
            "aliases": deepcopy(self.aliases),
            "groups": deepcopy(self.groups),
            "modules": deepcopy(self.modules),
            "rails": deepcopy(self.rails),
            "connect": list(self.connections),
            "pullups": list(self.pullups),
            "pulldowns": list(self.pulldowns),
            "inputs": deepcopy(self.inputs),
            "input_sets": deepcopy(self.input_sets),
            "clocks": deepcopy(self.clocks),
            "controls": deepcopy(self.controls),
            "memory_images": deepcopy(self.memory_images),
            "probes": deepcopy(self.probes),
            "displays": deepcopy(self.displays),
            "expect": deepcopy(self.expect),
            "steps": list(self.steps),
            "validate": deepcopy(self.validate_config),
        }
        data.update(deepcopy(self.extra))
        return data

    def to_netlist(self) -> JsonMap:
        return design_to_netlist(self)

    def to_verilog(self, *, include_testbench: bool = True) -> JsonMap:
        return export_verilog(self, include_testbench=include_testbench)

    def endpoint(self, ref: str) -> JsonMap:
        return self._endpoint(ref).snapshot()

    def endpoints(self, expr: str) -> list[JsonMap]:
        return [self._endpoint(item).snapshot() for item in _split_refs(expr)]

    def connect(self, rule: str) -> "Design":
        self.connections.append(str(rule))
        self._board = None
        self.stimulus = None
        self.probe_controller = None
        return self

    def to_board(self) -> Board:
        board = Board()
        for rail, value in self.rails.items():
            board.power(rail, value)
        for bus_name, bus_spec in self.buses.items():
            width = _width(bus_spec)
            board.bus(bus_name, width)
        for ref, spec in self.chips.items():
            if not isinstance(spec, dict) or "part" not in spec:
                raise ValueError(f"chip {ref} needs a part")
            if self._component_manifest(ref) is not None:
                continue
            board.add_chip(ref, create_chip(str(spec["part"]), ref))

        component_connections: dict[tuple[str, str], list[str]] = {}
        for index, rule in enumerate(self.connections):
            self._apply_connection(board, rule, index, component_connections)
        for target in self.pullups:
            board.pullup(self._tag(target))
        for target in self.pulldowns:
            board.pulldown(self._tag(target))

        stimulus = StimulusController(board)
        self._apply_component_sources(board, component_connections)
        self._apply_inputs(board)
        self._apply_input_sets(board, stimulus)
        self._apply_clocks(board, stimulus)
        self._apply_memory_images(board)

        probes = ProbeController(board)
        self._apply_probes(board, probes)
        self._apply_component_probes(board, probes, component_connections)

        board.settle()
        self._board = board
        self.stimulus = stimulus
        self.probe_controller = probes
        return board

    def snapshot(self) -> JsonMap:
        board_snapshot = self._board.snapshot() if self._board is not None else None
        return {
            "design": self.to_dict(),
            "normalized": {
                "chips": deepcopy(self.chips),
                "buses": deepcopy(self.buses),
                "aliases": deepcopy(self.aliases),
                "groups": deepcopy(self.groups),
                "modules": deepcopy(self.modules),
                "rails": deepcopy(self.rails),
                "connect": [
                    {"rule": rule, "endpoints": [ep.snapshot() for ep in self._connection_endpoints(rule)]}
                    for rule in self.connections
                ],
            },
            "board": board_snapshot,
            "stimulus": self.stimulus.snapshot() if self.stimulus is not None else None,
            "probes": self.probe_controller.snapshot() if self.probe_controller is not None else None,
            "displays": deepcopy(self.displays),
            "expect": deepcopy(self.expect),
            "steps": list(self.steps),
            "validate": self.validate(),
        }

    def to_io(self) -> JsonMap:
        if self.stimulus is None or self.probe_controller is None:
            self.to_board()
        return {"stimulus": self.stimulus, "probes": self.probe_controller}

    def run(self, steps: str | list[str] = "all") -> JsonMap:
        board = self._board if self._board is not None else self.to_board()
        if self.stimulus is None or self.probe_controller is None:
            self.to_board()
            board = self._board
        selected_steps = self.steps if steps == "all" else steps if isinstance(steps, list) else []
        log: list[JsonMap] = []
        expectations: JsonMap = {"passed": [], "failed": []}
        for step in selected_steps:
            entry = self._run_step(board, str(step))
            log.append(entry)
            result = entry.get("expectation")
            if isinstance(result, dict):
                bucket = "passed" if result.get("ok") else "failed"
                expectations[bucket].append(result)
        if self.probe_controller is not None:
            self.probe_controller.sample()
        board_errors = board.errors() if board is not None else []
        return {
            "ok": not board_errors and not expectations["failed"],
            "log": log,
            "snapshot": self.snapshot(),
            "probes": self.probe_controller.snapshot() if self.probe_controller is not None else None,
            "displays": deepcopy(self.displays),
            "expectations": expectations,
            "timing": {
                "time_ns": board.time_ns if board is not None else 0,
                "steps": len(selected_steps),
                "events": len(log),
            },
        }

    def validate(self) -> JsonMap:
        errors: list[JsonMap] = []
        warnings: list[JsonMap] = []
        for ref, spec in self.chips.items():
            if not isinstance(spec, dict) or not spec.get("part"):
                errors.append({"type": "chip_part_missing", "ref": ref})
                continue
            try:
                self._component_manifest(ref)
            except Exception as exc:
                errors.append({"type": "component_manifest_invalid", "ref": ref, "detail": str(exc)})
        for name, spec in self.buses.items():
            width = _width(spec)
            max_width = int(self.validate_config.get("max_bus_width", 128))
            if width <= 0 or width > max_width:
                errors.append({"type": "bus_width_invalid", "bus": name, "width": width})
        for alias, target in self.aliases.items():
            if alias == target:
                errors.append({"type": "alias_cycle", "alias": alias})
                continue
            try:
                self._endpoint(target)
            except Exception as exc:  # pragma: no cover - defensive reporting
                errors.append({"type": "alias_target_invalid", "alias": alias, "detail": str(exc)})
        for rule in self.connections:
            try:
                self._connection_endpoints(rule)
            except Exception as exc:
                errors.append({"type": "connection_invalid", "rule": rule, "detail": str(exc)})
        for name, spec in self.input_sets.items():
            channels = spec.get("channels", []) if isinstance(spec, dict) else []
            limit = int(self.validate_config.get("max_input_channels_per_set", 64))
            if len(channels) > limit:
                errors.append({"type": "input_set_too_large", "name": name, "count": len(channels)})
        for name, items in self.probes.items():
            channels = _probe_channels(items)
            limit = int(self.validate_config.get("max_probe_channels_per_set", 64))
            if len(channels) > limit:
                errors.append({"type": "probe_set_too_large", "name": name, "count": len(channels)})
        return {"ok": not errors, "errors": errors, "warnings": warnings}

    def _run_step(self, board: Board | None, step: str) -> JsonMap:
        if board is None:
            raise RuntimeError("design board is not built")
        text = step.strip()
        lower = text.lower()
        if not text:
            return {"step": step, "action": "noop"}
        if lower == "settle":
            board.settle()
            return {"step": step, "action": "settle", "time_ns": board.time_ns}
        if lower.startswith("apply "):
            name = text.split(None, 1)[1].strip()
            self._apply_named_inputs(board, name)
            board.settle()
            return {"step": step, "action": "apply", "inputs": name, "time_ns": board.time_ns}
        if lower.startswith("run "):
            duration_ns = parse_duration_ns(text.split(None, 1)[1])
            if self.stimulus is not None:
                self.stimulus.run_for(duration_ns)
            else:
                board.time_ns += duration_ns
            return {"step": step, "action": "run", "duration_ns": duration_ns, "time_ns": board.time_ns}
        if lower.startswith("clock "):
            return self._run_clock_step(board, text)
        if lower.startswith("probe"):
            if self.probe_controller is not None:
                self.probe_controller.sample()
            return {"step": step, "action": "probe", "time_ns": board.time_ns}
        if lower.startswith("expect "):
            name = text.split(None, 1)[1].strip()
            result = self._evaluate_expectation(board, name)
            return {
                "step": step,
                "action": "expect",
                "name": name,
                "status": "passed" if result["ok"] else "failed",
                "expectation": result,
            }
        return {"step": step, "action": "unknown", "warning": "step not implemented"}

    def _run_clock_step(self, board: Board, text: str) -> JsonMap:
        parts = text.split()
        if len(parts) < 3 or self.stimulus is None:
            return {"step": text, "action": "clock", "warning": "invalid clock command"}
        name = parts[1]
        command = parts[2].lower()
        clock = next((item for item in self.stimulus.clocks if item.name == name), None)
        if clock is None:
            return {"step": text, "action": "clock", "warning": f"unknown clock {name}"}
        if command == "start":
            clock.start(start_high=bool(clock.value))
        elif command == "stop":
            clock.stop()
        elif command == "frequency" and len(parts) >= 4:
            clock.configure(frequency_hz=float(parts[3]), duty=0.5)
        elif command == "period_ns" and len(parts) >= 4:
            clock.configure(period_ns=int(parts[3]), duty=0.5)
        elif command == "duty" and len(parts) >= 4:
            clock.configure(period_ns=clock.period_ns, duty=float(parts[3]))
        elif command == "pulse":
            width = parse_duration_ns(" ".join(parts[3:])) if len(parts) >= 4 else None
            clock.trigger(width_ns=width)
        else:
            return {"step": text, "action": "clock", "warning": f"unsupported clock command {command}"}
        board.settle()
        return {"step": text, "action": "clock", "clock": name, "command": command, "time_ns": board.time_ns}

    def _apply_named_inputs(self, board: Board, name: str) -> None:
        for rule in self.inputs.get(name, []):
            ref, value = _split_assignment(rule)
            self._drive_endpoint(board, self._endpoint(ref), value)

    def _apply_connection(
        self,
        board: Board,
        rule: str,
        index: int,
        component_connections: dict[tuple[str, str], list[str]],
    ) -> None:
        endpoints = self._connection_endpoints(rule)
        rails = [ep for ep in endpoints if ep.kind == "rail"]
        non_rails = [ep for ep in endpoints if ep.kind != "rail"]
        if rails:
            for rail in rails:
                for endpoint in non_rails:
                    if endpoint.kind == "pin":
                        board.attach(endpoint.target, board.chips[endpoint.chip or ""], endpoint.pin or 0)
                        board.attach_rail(rail.rail or rail.target, endpoint.target)
                    elif endpoint.kind == "component_pin":
                        board.attach_rail(rail.rail or rail.target, rail.target)
                        self._record_component_connection(component_connections, endpoint, rail.target)
                    else:
                        board.attach_rail(rail.rail or rail.target, endpoint.target)
            return
        net_tag = _preferred_tag(endpoints) or f"net:{index}"
        for endpoint in endpoints:
            if endpoint.kind == "pin":
                board.attach(net_tag, board.chips[endpoint.chip or ""], endpoint.pin or 0)
            elif endpoint.kind == "component_pin":
                board.net_for_tag(net_tag)
                self._record_component_connection(component_connections, endpoint, net_tag)
            elif endpoint.kind in ("bus", "net"):
                if endpoint.target != net_tag:
                    board.net_for_tag(net_tag).connect_source(board.logic_source(f"link:{index}:{endpoint.target}", endpoint.target, 0, enabled=False))

    def _apply_inputs(self, board: Board) -> None:
        for rules in self.inputs.values():
            for rule in rules:
                ref, value = _split_assignment(rule)
                self._drive_endpoint(board, self._endpoint(ref), value)

    def _apply_input_sets(self, board: Board, stimulus: StimulusController) -> None:
        for name, spec in self.input_sets.items():
            if not isinstance(spec, dict):
                continue
            channels = spec.get("channels", [])
            max_index = max([int(ch.get("index", i)) for i, ch in enumerate(channels) if isinstance(ch, dict)] or [0])
            input_set = stimulus.input_set(name, input_count=max(1, min(64, max_index + 1)))
            for fallback_index, channel in enumerate(channels):
                if isinstance(channel, dict) and "to" not in channel and "target" in channel:
                    channel = {**channel, "to": channel["target"]}
                if not isinstance(channel, dict) or "to" not in channel:
                    continue
                index = int(channel.get("index", fallback_index))
                if index >= 64:
                    continue
                endpoint = self._endpoint(str(channel["to"]))
                initial = normalize_logic(channel.get("initial", channel.get("power_on", 0)))
                if endpoint.kind == "pin":
                    bound = input_set.bind(index, board.chips[endpoint.chip or ""], endpoint.pin or 0, initial=initial)
                    if "name" in channel:
                        bound.name = str(channel["name"])
                else:
                    source_name = f"input:{name}:{channel.get('name', index)}"
                    board.logic_source(source_name, endpoint.target, initial)

    def _apply_clocks(self, board: Board, stimulus: StimulusController) -> None:
        for index, (name, spec) in enumerate(self.clocks.items()):
            if not isinstance(spec, dict) or "to" not in spec or index >= len(stimulus.clocks):
                continue
            endpoint = self._endpoint(str(spec["to"]))
            initial = 1 if spec.get("initial", 0) else 0
            clock = stimulus.clock(index)
            clock.name = str(name)
            if endpoint.kind == "pin":
                clock.bind(board.chips[endpoint.chip or ""], endpoint.pin or 0)
                clock.value = initial
                clock._drive(initial)
            else:
                board.logic_source(f"clock:{name}", endpoint.target, initial)
            clock.configure(
                frequency_hz=spec.get("frequency_hz"),
                period_ns=spec.get("period_ns"),
                duty=float(spec.get("duty", 0.5)),
            )
            if spec.get("enabled", False) and endpoint.kind == "pin":
                clock.start(start_high=bool(initial))

    def _apply_memory_images(self, board: Board) -> None:
        for ref, spec in self.memory_images.items():
            if ref not in board.chips or not isinstance(spec, dict) or "file" not in spec:
                continue
            load_memory(
                board.chips[ref],
                spec["file"],
                offset=int(spec.get("offset", 0)),
                fmt=spec.get("format", "auto"),
                clear=spec.get("clear"),
            )

    def _apply_component_sources(self, board: Board, component_connections: dict[tuple[str, str], list[str]]) -> None:
        for ref in self.chips:
            manifest = self._component_manifest(ref)
            if manifest is None:
                continue
            part = str(manifest.get("part", "")).lower()
            simulation = manifest.get("simulation", {})
            sim = simulation if isinstance(simulation, dict) else {}
            for pin_name, tags in self._component_pin_tags(component_connections, ref).items():
                for tag in tags:
                    if part == "inputsource":
                        value = self._component_logic_default(ref, manifest, sim, "default_value", 0)
                        self._ensure_logic_source(board, f"input:{ref}:{pin_name}->{tag}", tag, value)
                    elif part == "clocksource":
                        value = self._component_logic_default(ref, manifest, sim, "initial", 0)
                        self._ensure_logic_source(board, f"clock:{ref}:{pin_name}->{tag}", tag, value)
                    elif part == "vcc":
                        self._ensure_rail_source(board, "VCC", tag)
                    elif part == "gnd":
                        self._ensure_rail_source(board, "GND", tag)
                    elif part == "pullup":
                        board.pullup(tag)
                    elif part == "pulldown":
                        board.pulldown(tag)

    def _apply_probes(self, board: Board, probes: ProbeController) -> None:
        for set_name, entries in self.probes.items():
            probe_set = probes.set(set_name)
            for item in _probe_channels(entries):
                if isinstance(item, dict):
                    signal = str(item.get("target", item.get("to", item.get("signal", item.get("name", "")))))
                    probe_name = str(item.get("name", signal))
                else:
                    signal = str(item)
                    probe_name = signal
                if not signal:
                    continue
                endpoint = self._endpoint(signal)
                if endpoint.kind == "pin":
                    probe_set.pin(probe_name, board.chips[endpoint.chip or ""], endpoint.pin or 0)
                elif endpoint.kind == "bus":
                    probe_set.bus(probe_name, endpoint.bus or "", endpoint.index or 0)
                elif endpoint.kind == "net":
                    probe_set.net(probe_name, endpoint.target)

    def _apply_component_probes(
        self,
        board: Board,
        probes: ProbeController,
        component_connections: dict[tuple[str, str], list[str]],
    ) -> None:
        for ref in self.chips:
            manifest = self._component_manifest(ref)
            if manifest is None:
                continue
            part = str(manifest.get("part", "")).lower()
            if part not in ("probe", "busprobe"):
                continue
            for tags in self._component_pin_tags(component_connections, ref).values():
                for tag in tags:
                    probes.default.tag(ref, tag)

    def _drive_endpoint(self, board: Board, endpoint: Endpoint, value: Logic) -> None:
        value = normalize_logic(value)
        if endpoint.kind == "pin":
            board.drive(board.chips[endpoint.chip or ""], endpoint.pin or 0, value)
            return
        if endpoint.kind == "component_pin":
            prefixes = (f"input:{endpoint.target}->", f"clock:{endpoint.target}->")
            matched = False
            for name in list(board.sources):
                if name.startswith(prefixes):
                    board.set_source(name, value)
                    matched = True
            if matched:
                return
            board.logic_source(f"input:{endpoint.target}", endpoint.target, value)
            return
        source_name = f"input:{endpoint.ref}"
        if source_name in board.sources:
            board.set_source(source_name, value)
            return
        board.logic_source(source_name, endpoint.target, value)

    def _connection_endpoints(self, rule: str) -> list[Endpoint]:
        return [self._endpoint(ref) for ref in _split_refs(_strip_arrow(rule))]

    def _endpoint(self, ref: str) -> Endpoint:
        original = str(ref).strip()
        resolved = self._resolve_alias(original)
        if resolved in self.rails:
            return Endpoint(original, "rail", resolved, rail=resolved)
        if ":" in resolved:
            left, right = resolved.split(":", 1)
            left = left.strip()
            right = right.strip()
            if left in self.chips:
                manifest = self._component_manifest(left)
                if manifest is not None:
                    pin = self._component_pin_name(left, manifest, right)
                    return Endpoint(original, "component_pin", f"{left}:{pin}", chip=left, pin=pin)
                pin: int | str = int(right) if right.isdigit() else right
                return Endpoint(original, "pin", f"{left}:{pin}", chip=left, pin=pin)
            index = int(right)
            return Endpoint(original, "bus", f"bus:{left}[{index}]", bus=left, index=index)
        return Endpoint(original, "net", resolved)

    def _resolve_alias(self, ref: str) -> str:
        seen: set[str] = set()
        current = str(ref).strip()
        while current in self.aliases:
            if current in seen:
                raise ValueError(f"alias cycle at {current}")
            seen.add(current)
            current = self.aliases[current].strip()
        return current

    def _tag(self, ref: str) -> str:
        endpoint = self._endpoint(ref)
        if endpoint.kind == "rail":
            return endpoint.target
        return endpoint.target

    def _component_manifest(self, ref: str) -> JsonMap | None:
        if ref in self._component_cache:
            return self._component_cache[ref]
        spec = self.chips.get(ref)
        if not isinstance(spec, dict) or not spec.get("part"):
            self._component_cache[ref] = None
            return None
        part = str(spec["part"])
        try:
            manifest = load_component(part)
        except KeyError:
            manifest = None
        if manifest is not None and str(manifest.get("group", "")).lower() not in ("virtual", "passive", "discrete"):
            manifest = None
        self._component_cache[ref] = manifest
        return manifest

    def _component_pin_name(self, ref: str, manifest: JsonMap, pin: str) -> str:
        pins = [item for item in manifest.get("pins", []) if isinstance(item, dict)]
        by_number = {
            int(item["number"]): str(item.get("name", item["number"]))
            for item in pins
            if isinstance(item.get("number"), int)
        }
        by_name = {str(item.get("name", "")): str(item.get("name", "")) for item in pins}
        if pin.isdigit() and int(pin) in by_number:
            return by_number[int(pin)]
        if pin in by_name:
            return by_name[pin]
        raise ValueError(f"{ref} has no DB component pin {pin!r}")

    def _record_component_connection(
        self,
        component_connections: dict[tuple[str, str], list[str]],
        endpoint: Endpoint,
        tag: str,
    ) -> None:
        if endpoint.chip is None or endpoint.pin is None:
            return
        key = (endpoint.chip, str(endpoint.pin))
        tags = component_connections.setdefault(key, [])
        if tag not in tags:
            tags.append(tag)

    def _component_pin_tags(self, component_connections: dict[tuple[str, str], list[str]], ref: str) -> dict[str, list[str]]:
        return {
            pin: list(tags)
            for (component_ref, pin), tags in component_connections.items()
            if component_ref == ref
        }

    def _component_logic_default(self, ref: str, manifest: JsonMap, simulation: JsonMap, key: str, default: Logic) -> Logic:
        spec = self.chips.get(ref)
        value: Any = default
        if isinstance(spec, dict):
            value = spec.get("initial", spec.get("value", spec.get("default", simulation.get(key, default))))
        else:
            value = simulation.get(key, default)
        return normalize_logic(value)

    def _ensure_logic_source(self, board: Board, name: str, target: str, value: Logic) -> None:
        if name in board.sources:
            board.set_source(name, value)
            return
        board.logic_source(name, target, value)

    def _ensure_rail_source(self, board: Board, rail: str, target: str) -> None:
        board.power(rail, 1 if rail.upper() != "GND" else 0)
        name = f"rail:{rail}->{target}"
        if name in board.sources:
            return
        board.attach_rail(rail, target)

    def _evaluate_expectation(self, board: Board, name: str) -> JsonMap:
        rules = self.expect.get(name)
        if rules is None:
            return {
                "name": name,
                "ok": False,
                "checks": [],
                "errors": [{"type": "expectation_missing", "name": name}],
            }
        if isinstance(rules, str):
            checks = [rules]
        elif isinstance(rules, list):
            checks = [str(rule) for rule in rules]
        else:
            return {
                "name": name,
                "ok": False,
                "checks": [],
                "errors": [{"type": "expectation_invalid", "name": name, "detail": "expectation must be a string or list"}],
            }
        results = [self._evaluate_expectation_rule(board, rule) for rule in checks]
        return {
            "name": name,
            "ok": all(item.get("ok") for item in results),
            "checks": results,
            "errors": [item for item in results if not item.get("ok")],
        }

    def _evaluate_expectation_rule(self, board: Board, rule: str) -> JsonMap:
        text = str(rule).strip()
        if not text:
            return {"rule": rule, "ok": True, "type": "noop"}
        lowered = text.lower()
        if "=" in text:
            ref, expected_text = text.split("=", 1)
            return self._expect_current_value(board, text, ref.strip(), _logic_text(expected_text.strip()))
        if " is " in lowered:
            before, _, after = text.partition(" is ")
            return self._expect_current_value(board, text, before.strip(), _logic_text(after.strip()))
        if lowered.endswith(" changes"):
            ref = text[: -len(" changes")].strip()
            return self._expect_history_edge(text, ref, None)
        if " has " in lowered:
            ref, _, edge = text.partition(" has ")
            return self._expect_history_edge(text, ref.strip(), edge.strip().lower())
        if " stable " in lowered:
            ref, _, expected = text.partition(" stable ")
            return self._expect_stable(text, ref.strip(), _logic_text(expected.strip()))
        return {
            "rule": rule,
            "ok": False,
            "type": "unsupported_expectation",
            "message": "Use forms like 'Y = 1', 'CLK has rising', 'DATA:0 changes', or 'READY stable 0'.",
        }

    def _expect_current_value(self, board: Board, rule: str, ref: str, expected: Logic) -> JsonMap:
        actual = self._read_endpoint_value(board, ref)
        ok = actual == expected
        return {
            "rule": rule,
            "ok": ok,
            "type": "value",
            "target": ref,
            "expected": expected,
            "actual": actual,
            "message": "" if ok else f"{ref} expected {expected!r}, got {actual!r}",
        }

    def _expect_history_edge(self, rule: str, ref: str, edge: str | None) -> JsonMap:
        channel = self._find_probe_channel(ref)
        if channel is None:
            return {
                "rule": rule,
                "ok": False,
                "type": "transition",
                "target": ref,
                "edge": edge or "change",
                "message": f"{ref} has no probe history; add it to probes and run a probe step first.",
            }
        expected_edge = None if edge in (None, "", "change", "changes") else edge
        count = channel.count_edges(expected_edge)
        ok = count > 0
        return {
            "rule": rule,
            "ok": ok,
            "type": "transition",
            "target": ref,
            "edge": edge or "change",
            "count": count,
            "message": "" if ok else f"{ref} expected {edge or 'change'} transition",
        }

    def _expect_stable(self, rule: str, ref: str, expected: Logic) -> JsonMap:
        channel = self._find_probe_channel(ref)
        if channel is None:
            return {
                "rule": rule,
                "ok": False,
                "type": "stable",
                "target": ref,
                "expected": expected,
                "message": f"{ref} has no probe history; add it to probes and run a probe step first.",
            }
        samples = channel.values()
        bad = [sample for sample in samples if sample.value != expected]
        ok = bool(samples) and not bad
        return {
            "rule": rule,
            "ok": ok,
            "type": "stable",
            "target": ref,
            "expected": expected,
            "samples": len(samples),
            "message": "" if ok else f"{ref} was not stable at {expected!r}",
        }

    def _read_endpoint_value(self, board: Board, ref: str) -> Logic:
        endpoint = self._endpoint(ref)
        if endpoint.kind == "pin":
            return board.chips[endpoint.chip or ""].pin(endpoint.pin or 0).sample()
        if endpoint.kind in ("bus", "net", "component_pin"):
            return board.net_for_tag(endpoint.target).value
        if endpoint.kind == "rail":
            return self.rails[endpoint.rail or endpoint.target]
        raise ValueError(f"unsupported expectation endpoint {ref!r}")

    def _find_probe_channel(self, ref: str) -> ProbeChannel | None:
        if self.probe_controller is None:
            return None
        try:
            endpoint = self._endpoint(ref)
        except Exception:
            endpoint = None
        targets = {ref}
        if endpoint is not None:
            targets.add(endpoint.target)
            if endpoint.kind == "pin" and endpoint.chip is not None:
                chip = self._board.chips.get(endpoint.chip) if self._board is not None else None
                if chip is not None:
                    try:
                        targets.add(f"{endpoint.chip}.{chip.pin(endpoint.pin or 0).name}")
                    except Exception:
                        pass
        for probe_set in self.probe_controller.sets.values():
            for channel in probe_set.probes:
                if channel.name == ref or channel.target_name in targets:
                    return channel
        return None


def _copy_map(value: Any) -> JsonMap:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("expected object")
    return deepcopy(value)


def _named_map(value: Any, key_field: str) -> JsonMap:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, list):
        result: JsonMap = {}
        for item in value:
            if not isinstance(item, dict) or key_field not in item:
                raise ValueError(f"expected list objects with {key_field!r}")
            key = str(item[key_field])
            entry = deepcopy(item)
            entry.pop(key_field, None)
            result[key] = entry
        return result
    raise ValueError("expected object or named list")


def _input_rules(value: Any) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("inputs must be an object")
    result: dict[str, list[str]] = {}
    for name, rules in value.items():
        if isinstance(rules, dict):
            result[str(name)] = [f"{ref} = {logic}" for ref, logic in rules.items()]
        else:
            result[str(name)] = [str(item) for item in rules]
    return result


def _probe_map(value: Any) -> JsonMap:
    if value is None:
        return {}
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, list):
        result: JsonMap = {}
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("probe list entries must be objects")
            name = str(item.get("set", item.get("name", "default")))
            result[name] = {"channels": deepcopy(item.get("channels", item.get("signals", [])))}
        return result
    raise ValueError("probes must be an object or list")


def _probe_channels(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.get("channels", value.get("signals", [])))
    return []


def _width(spec: Any) -> int:
    if isinstance(spec, dict):
        return int(spec.get("width", 1))
    return int(spec)


def _split_refs(expr: str) -> list[str]:
    return [item.strip() for item in str(expr).split(",") if item.strip()]


def _strip_arrow(rule: str) -> str:
    if "<->" in rule:
        return rule.replace("<->", ",")
    if "->" in rule:
        return rule.replace("->", ",")
    return rule


def _split_assignment(rule: str) -> tuple[str, Logic]:
    if "=" not in rule:
        raise ValueError(f"input rule needs '=': {rule!r}")
    ref, value = rule.split("=", 1)
    return ref.strip(), _logic_text(value.strip())


def _logic_text(text: str) -> Logic:
    upper = text.upper()
    if upper in ("Z", "X"):
        return upper
    if upper in ("TRUE", "HIGH"):
        return 1
    if upper in ("FALSE", "LOW"):
        return 0
    return normalize_logic(int(text, 0))


def parse_duration_ns(text: str) -> int:
    parts = str(text).strip().split()
    if not parts:
        raise ValueError("duration is empty")
    if len(parts) == 1:
        raw = parts[0].lower()
        for suffix, scale in (("ns", 1), ("us", 1_000), ("ms", 1_000_000), ("s", 1_000_000_000)):
            if raw.endswith(suffix):
                return int(float(raw[: -len(suffix)]) * scale)
        return int(float(raw))
    value = float(parts[0])
    unit = parts[1].lower()
    if unit in ("ns", "nanosecond", "nanoseconds"):
        return int(value)
    if unit in ("us", "microsecond", "microseconds"):
        return int(value * 1_000)
    if unit in ("ms", "millisecond", "milliseconds"):
        return int(value * 1_000_000)
    if unit in ("s", "sec", "second", "seconds"):
        return int(value * 1_000_000_000)
    raise ValueError(f"unknown duration unit {unit!r}")


def _preferred_tag(endpoints: list[Endpoint]) -> str | None:
    for kind in ("bus", "net"):
        for endpoint in endpoints:
            if endpoint.kind == kind:
                return endpoint.target
    return None
