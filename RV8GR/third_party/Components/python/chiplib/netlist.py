"""Normalized netlist and Verilog exporters for schematic designs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from .chips import create_chip
from .core import Logic, parse_bus_tag


JsonMap = dict[str, Any]


def design_to_netlist(design: Any) -> JsonMap:
    """Return a serializable netlist derived from a normalized Design."""

    board = design._board if getattr(design, "_board", None) is not None else design.to_board()
    snapshot = board.snapshot()
    pin_index = _pin_index(snapshot)
    nets: list[JsonMap] = []

    for net in sorted(snapshot["nets"], key=lambda item: item["name"]):
        name = str(net["name"])
        bus = _bus_line(name)
        nets.append({
            "name": name,
            "kind": "bus" if bus else "net",
            "bus": bus["bus"] if bus else None,
            "index": bus["index"] if bus else None,
            "value": net["value"],
            "pins": [
                _pin_endpoint(pin)
                for pin in sorted(net["pins"], key=lambda item: (item["chip"], item["number"]))
            ],
            "pulls": deepcopy(net["pulls"]),
            "sources": deepcopy(net["sources"]),
        })

    return {
        "format": "chiplib.netlist",
        "version": 1,
        "name": design.name,
        "description": design.description,
        "design": design.to_dict(),
        "chips": [
            _chip_entry(ref, spec, pin_index.get(ref, {}))
            for ref, spec in sorted(design.chips.items())
        ],
        "buses": [
            {"name": name, "width": _width(spec)}
            for name, spec in sorted(design.buses.items())
        ],
        "rails": [
            {"name": name, "value": value}
            for name, value in sorted(design.rails.items())
        ],
        "nets": nets,
        "connections": [
            {
                "rule": rule,
                "endpoints": [endpoint.snapshot() for endpoint in design._connection_endpoints(rule)],
            }
            for rule in design.connections
        ],
        "pullups": list(design.pullups),
        "pulldowns": list(design.pulldowns),
        "inputs": deepcopy(design.inputs),
        "input_sets": deepcopy(design.input_sets),
        "clocks": deepcopy(design.clocks),
        "probes": deepcopy(design.probes),
        "displays": deepcopy(design.displays),
        "expect": deepcopy(design.expect),
        "steps": list(design.steps),
        "validation": design.validate(),
        "board_errors": snapshot["errors"],
    }


def design_from_netlist(data: JsonMap, design_class: Any) -> Any:
    """Recreate a Design from a chiplib netlist.

    Netlists exported by this module keep the canonical design JSON so the
    beginner-facing script can round-trip without losing UI metadata.
    """

    if not isinstance(data, dict):
        raise ValueError("netlist root must be an object")
    if "design" in data:
        return design_class.from_dict(deepcopy(data["design"]))

    design = design_class(str(data.get("name", "netlist")))
    design.description = str(data.get("description", ""))
    design.chips = {
        str(item["ref"]): {"part": str(item["part"])}
        for item in data.get("chips", [])
        if isinstance(item, dict) and "ref" in item and "part" in item
    }
    design.buses = {
        str(item["name"]): {"width": int(item.get("width", 1))}
        for item in data.get("buses", [])
        if isinstance(item, dict) and "name" in item
    }
    design.rails = {
        str(item["name"]): _logic(item.get("value", 0))
        for item in data.get("rails", [])
        if isinstance(item, dict) and "name" in item
    }
    design.connections = [str(item.get("rule", "")) for item in data.get("connections", []) if item.get("rule")]
    design.pullups = [str(item) for item in data.get("pullups", [])]
    design.pulldowns = [str(item) for item in data.get("pulldowns", [])]
    design.inputs = deepcopy(data.get("inputs", {}))
    design.input_sets = deepcopy(data.get("input_sets", {}))
    design.clocks = deepcopy(data.get("clocks", {}))
    design.probes = deepcopy(data.get("probes", {}))
    design.displays = deepcopy(data.get("displays", {}))
    design.expect = deepcopy(data.get("expect", {}))
    design.steps = [str(item) for item in data.get("steps", [])]
    return design


def design_from_kicad_netlist(path: str | Path, design_class: Any, *, name: str | None = None) -> Any:
    """Create a Design from a KiCad generic S-expression netlist export."""

    source = Path(path)
    text = source.read_text(encoding="utf-8")
    chips = {
        ref: {"part": value}
        for ref, value in re.findall(
            r'\(comp \(ref "([^"]+)"\)\s+\(value "([^"]+)"\)',
            text,
            flags=re.S,
        )
    }
    connections: list[str] = []
    for net_name, block in re.findall(
        r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)(.*?)(?=\n    \(net |\n  \)\n\))',
        text,
        flags=re.S,
    ):
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)\)', block)
        if nodes:
            connections.append(f"{net_name} -> " + ", ".join(f"{ref}:{pin}" for ref, pin in nodes))
    return design_class.from_dict({
        "name": name or source.stem,
        "description": f"Imported from KiCad netlist {source.name}",
        "chips": chips,
        "connect": connections,
    })


def design_to_verilog(design: Any, *, include_testbench: bool = True) -> JsonMap:
    """Export a conservative structural Verilog wrapper from a Design."""

    netlist = design.to_netlist()
    module_name = _verilog_ident(design.name or "design")
    unsupported: list[JsonMap] = []
    lines: list[str] = [
        "`timescale 1ns/1ps",
        "",
        f"module {module_name}();",
    ]

    net_names = [net["name"] for net in netlist["nets"]]
    for name in sorted(net_names):
        lines.append(f"  wire {_net_id(name)};")
    open_wires = _open_output_wires(netlist)
    for name in open_wires:
        lines.append(f"  wire {name};")
    if net_names:
        lines.append("")

    for net in netlist["nets"]:
        for source in net.get("sources", []):
            if source.get("enabled", True):
                lines.append(f"  assign {_net_id(net['name'])} = {_logic_literal(source.get('value', 'Z'))};")
        for pull in net.get("pulls", []):
            lines.append(f"  tri{1 if pull.get('value') == 1 else 0} {_net_id(net['name'])}_pull = {_net_id(net['name'])};")
    if any(net.get("sources") or net.get("pulls") for net in netlist["nets"]):
        lines.append("")

    net_for_pin = _net_for_pin(netlist)
    for chip in netlist["chips"]:
        mapping = _verilog_mapping(str(chip["part"]))
        if mapping is None:
            unsupported.append({"ref": chip["ref"], "part": chip["part"], "reason": "no Verilog port mapping"})
            continue
        ports = mapping["ports"](chip["ref"], net_for_pin)
        port_lines = [f".{port}({expr})" for port, expr in ports]
        joined = ", ".join(port_lines)
        parameters = ""
        if str(mapping["module"]).startswith("ttl_"):
            delay = mapping.get("delay_ns", 1)
            if isinstance(delay, dict):
                delay = delay.get(chip["ref"], delay.get("*", 1))
            delay = int(delay)
            parameter_items = [f".DELAY_RISE({delay})", f".DELAY_FALL({delay})"]
            sample_delay = mapping.get("sample_delay_ns")
            if isinstance(sample_delay, dict):
                sample_delay = sample_delay.get(chip["ref"], sample_delay.get("*"))
            if sample_delay is not None:
                parameter_items.append(f".SAMPLE_DELAY({int(sample_delay)})")
            parameters = " #(" + ", ".join(parameter_items) + ")"
        lines.append(f"  {mapping['module']}{parameters} {chip['ref']} ({joined});")
    lines.append("endmodule")

    result: JsonMap = {
        "ok": not unsupported,
        "format": "verilog",
        "module": module_name,
        "verilog": "\n".join(lines) + "\n",
        "unsupported": unsupported,
        "netlist": netlist,
    }
    if include_testbench:
        tb_name = f"tb_{module_name}"
        result["testbench"] = (
            "`timescale 1ns/1ps\n\n"
            f"module {tb_name}();\n"
            f"  {module_name} dut();\n"
            "  initial begin\n"
            "    #1;\n"
            "    $finish;\n"
            "  end\n"
            "endmodule\n"
        )
    return result


def _chip_entry(ref: str, spec: Any, pins: dict[int, JsonMap]) -> JsonMap:
    part = str(spec.get("part", "")) if isinstance(spec, dict) else str(spec)
    entry: JsonMap = {"ref": ref, "part": part}
    if isinstance(spec, dict):
        for key in ("label", "module", "description"):
            if key in spec:
                entry[key] = deepcopy(spec[key])
    if pins:
        entry["pins"] = [pins[number] for number in sorted(pins)]
    else:
        chip = create_chip(part, ref)
        entry["pins"] = [
            {
                "number": pin.number,
                "name": pin.name,
                "direction": pin.direction,
                "active_low": pin.spec.active_low,
            }
            for pin in chip.pins.values()
        ]
    return entry


def _pin_index(snapshot: JsonMap) -> dict[str, dict[int, JsonMap]]:
    result: dict[str, dict[int, JsonMap]] = {}
    for chip in snapshot["chips"]:
        pins: dict[int, JsonMap] = {}
        for pin in chip["pins"]:
            pins[int(pin["number"])] = {
                "number": pin["number"],
                "name": pin["name"],
                "direction": pin["direction"],
                "active_low": pin["active_low"],
                "net": pin["net"],
                "value": pin["value"],
            }
        result[str(chip["ref"])] = pins
    return result


def _pin_endpoint(pin: JsonMap) -> JsonMap:
    return {
        "chip": pin["chip"],
        "pin": pin["number"],
        "name": pin["name"],
        "direction": pin["direction"],
        "ref": f"{pin['chip']}:{pin['number']}",
    }


def _bus_line(name: str) -> JsonMap | None:
    parsed = parse_bus_tag(name)
    if parsed is None:
        return None
    bus, index = parsed
    return {"bus": bus, "index": index}


def _width(spec: Any) -> int:
    return int(spec.get("width", 1)) if isinstance(spec, dict) else int(spec)


def _logic(value: Any) -> Logic:
    if value in (0, 1, "Z", "X"):
        return value
    return int(value)


def _logic_literal(value: Any) -> str:
    if value == 1:
        return "1'b1"
    if value == 0:
        return "1'b0"
    if value == "X":
        return "1'bx"
    return "1'bz"


def _verilog_ident(text: str) -> str:
    chars = [char if char.isalnum() or char == "_" else "_" for char in str(text)]
    name = "".join(chars).strip("_") or "design"
    if name[0].isdigit():
        name = f"m_{name}"
    return name


def _net_id(name: str) -> str:
    text = (
        str(name)
        .replace("bus:", "bus_")
        .replace("/", "bar_")
        .replace("[", "_")
        .replace("]", "")
        .replace("=", "_eq_")
    )
    return "n_" + _verilog_ident(text)


def _net_for_pin(netlist: JsonMap) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}
    for net in netlist["nets"]:
        for pin in net["pins"]:
            result[(str(pin["chip"]), int(pin["pin"]))] = _net_id(net["name"])
    return result


def _pin(ref: str, number: int, net_for_pin: dict[tuple[str, int], str], *, fallback: str = "1'bz") -> str:
    return net_for_pin.get((ref, number), fallback)


def _vec(ref: str, pins: list[int], net_for_pin: dict[tuple[str, int], str], *, output: bool = False) -> str:
    return "{" + ", ".join(
        _pin(ref, pin, net_for_pin, fallback=_open_wire(ref, pin) if output else "1'bz")
        for pin in reversed(pins)
    ) + "}"


def _open_wire(ref: str, pin: int) -> str:
    return f"open_{_verilog_ident(ref)}_{pin}"


def _open_output_wires(netlist: JsonMap) -> list[str]:
    result: list[str] = []
    net_for_pin = _net_for_pin(netlist)
    for chip in netlist["chips"]:
        mapping = _verilog_mapping(str(chip["part"]))
        if mapping is None:
            continue
        for pin in mapping.get("output_pins", []):
            if (chip["ref"], pin) not in net_for_pin:
                result.append(_open_wire(chip["ref"], pin))
    return sorted(result)


def _verilog_mapping(part: str) -> JsonMap | None:
    part_id = str(part).upper()
    return _db_verilog_mapping(part_id)


def _db_verilog_mapping(part: str) -> JsonMap | None:
    from .db import load_component

    try:
        manifest = load_component(part)
    except (KeyError, ValueError):
        return None
    verilog = manifest.get("verilog", {})
    export = verilog.get("export", {}) if isinstance(verilog, dict) else {}
    ports = export.get("ports", {}) if isinstance(export, dict) else {}
    module = verilog.get("module") if isinstance(verilog, dict) else None
    if not isinstance(module, str) or not isinstance(ports, list):
        return None

    port_specs = deepcopy(ports)

    def db_ports(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
        return _ports_from_db_export(ref, net_for_pin, port_specs)

    mapping = {
        "module": module,
        "ports": db_ports,
        "output_pins": [int(pin) for pin in export.get("output_pins", [])],
        "delay_ns": deepcopy(export.get("delay_ns", 1)),
    }
    if "sample_delay_ns" in export:
        mapping["sample_delay_ns"] = deepcopy(export["sample_delay_ns"])
    return mapping


def _ports_from_db_export(
    ref: str,
    net_for_pin: dict[tuple[str, int], str],
    port_specs: list[JsonMap],
) -> list[tuple[str, str]]:
    ports: list[tuple[str, str]] = []
    for spec in port_specs:
        name = str(spec["name"])
        pins = [int(pin) for pin in spec.get("pins", [])]
        is_output = spec.get("direction") == "output"
        fallback = str(spec.get("fallback", "1'bz"))
        if len(pins) == 1:
            pin_fallback = _open_wire(ref, pins[0]) if is_output else fallback
            ports.append((name, _pin(ref, pins[0], net_for_pin, fallback=pin_fallback)))
        else:
            ports.append((name, _vec(ref, pins, net_for_pin, output=is_output)))
    return ports
