"""Internal service interfaces over the Components design backend."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .db import component_catalog, component_detail, student_component_catalog
from .netlist import _verilog_mapping, design_to_verilog


JsonMap = dict[str, Any]
CONTRACT = "components.service.v1"


class SimulationService:
    """Stable internal boundary for simulation-backed Design operations."""

    contract = CONTRACT
    engine = "python"

    def validate(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            validation = design.validate()
            warnings = _as_list(validation.get("warnings"))
            errors = _as_list(validation.get("errors"))
            result = {
                "valid": bool(validation.get("ok")),
                "design_id": getattr(design, "name", None),
                "summary": self._summary(design),
                "errors": errors,
                "warnings": warnings,
                "validation": validation,
            }
            return self._response(
                "validate",
                bool(validation.get("ok")),
                result,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("validate", exc, started=started)

    def snapshot(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            if getattr(design, "_board", None) is None:
                design.to_board()
            payload = design.snapshot()
            validation = payload.get("validate", {}) if isinstance(payload, dict) else {}
            warnings = _as_list(validation.get("warnings")) if isinstance(validation, dict) else []
            errors = _as_list(validation.get("errors")) if isinstance(validation, dict) else []
            return self._response(
                "snapshot",
                not errors,
                payload,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("snapshot", exc, started=started)

    def run(self, design: Any, steps: str | list[str] = "all") -> JsonMap:
        started = perf_counter()
        try:
            payload = design.run(steps)
            warnings = _warnings_from_run(payload)
            errors = _board_errors(payload) + _expectation_errors(payload)
            return self._response(
                "run",
                bool(payload.get("ok")) and not errors,
                payload,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("run", exc, code="simulation.failed", started=started)

    def probe(
        self,
        design: Any,
        *,
        set_name: str | None = None,
        steps: str | list[str] | None = None,
        include_history: bool = True,
    ) -> JsonMap:
        started = perf_counter()
        try:
            if steps is not None:
                run_payload = design.run(steps)
                if not run_payload.get("ok", False):
                    return self._response(
                        "probe",
                        False,
                        {"run": run_payload},
                        warnings=_warnings_from_run(run_payload),
                        errors=_board_errors(run_payload),
                        started=started,
                    )
            if getattr(design, "probe_controller", None) is None:
                design.to_board()
            probes = design.probe_controller
            if probes is None:
                raise RuntimeError("design probes are not available")
            probes.sample()
            snapshot = probes.snapshot()
            sets = snapshot.get("sets", [])
            selected_name = set_name or "default"
            selected = next((item for item in sets if item.get("name") == selected_name), None)
            if selected is None:
                return self._response(
                    "probe",
                    False,
                    {"set": selected_name, "available_sets": [item.get("name") for item in sets]},
                    errors=[{"type": "probe_set_missing", "set": selected_name}],
                    started=started,
                )
            samples = []
            for channel in selected.get("channels", []):
                sample = {
                    "name": channel.get("name"),
                    "target": channel.get("target"),
                    "target_kind": channel.get("target_kind"),
                    "value": channel.get("value"),
                }
                if include_history:
                    sample["history"] = channel.get("history", [])
                samples.append(sample)
            result = {
                "set": selected.get("name"),
                "time_ns": selected.get("time_ns", snapshot.get("time_ns", 0)),
                "samples": samples,
                "probes": snapshot,
            }
            return self._response("probe", True, result, started=started)
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("probe", exc, code="simulation.failed", started=started)

    def frontend_snapshot(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            if getattr(design, "_board", None) is None:
                design.to_board()
            return self._response("frontend-snapshot", True, _frontend_snapshot(design.snapshot()), started=started)
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("frontend-snapshot", exc, started=started)

    def _summary(self, design: Any) -> JsonMap:
        probes = getattr(design, "probes", {})
        return {
            "chips": len(getattr(design, "chips", {})),
            "buses": len(getattr(design, "buses", {})),
            "connections": len(getattr(design, "connections", [])),
            "probes": sum(len(_probe_channels(items)) for items in probes.values()) if isinstance(probes, dict) else 0,
        }

    def _response(
        self,
        command: str,
        ok: bool,
        result: JsonMap,
        *,
        warnings: list[Any] | None = None,
        errors: list[Any] | None = None,
        started: float,
    ) -> JsonMap:
        response: JsonMap = {
            "contract": self.contract,
            "command": command,
            "ok": ok,
            "result": result,
            "warnings": warnings or [],
            "metadata": self._metadata(started),
        }
        if errors:
            response["errors"] = errors
            response["error"] = {
                "code": "validation.failed" if command == "validate" else "simulation.failed",
                "message": f"{command} failed.",
                "severity": "error",
                "details": {"errors": errors},
            }
        return response

    def _exception(self, command: str, exc: Exception, *, started: float, code: str = "internal.error") -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": False,
            "error": {
                "code": code,
                "message": str(exc),
                "severity": "error",
                "details": {"exception": exc.__class__.__name__},
            },
            "warnings": [],
            "metadata": self._metadata(started),
        }

    def _metadata(self, started: float) -> JsonMap:
        return {
            "engine": self.engine,
            "components_version": None,
            "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        }


class DesignCommandService:
    """CLI-compatible service facade over design simulation and exporters."""

    def __init__(
        self,
        *,
        simulation: SimulationService | None = None,
        verilog: "VerilogExportService | None" = None,
    ):
        self.simulation = simulation or SimulationService()
        self.verilog = verilog or VerilogExportService()

    def load_design(self, json_file: str) -> Any:
        from .design import Design

        return Design.load_json(json_file)

    def validate(self, json_file: str) -> JsonMap:
        response = self.simulation.validate(self.load_design(json_file))
        result = response.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("validation"), dict):
            return result["validation"]
        return response

    def snapshot(self, json_file: str) -> JsonMap:
        return self.simulation.snapshot(self.load_design(json_file))["result"]

    def run(self, json_file: str, *, steps: str | list[str] = "all") -> JsonMap:
        return self.simulation.run(self.load_design(json_file), steps=steps)["result"]

    def probe(self, json_file: str) -> JsonMap:
        response = self.simulation.probe(self.load_design(json_file))
        result = response.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("probes"), dict):
            return result["probes"]
        return response

    def export_json(self, json_file: str) -> JsonMap:
        return self.load_design(json_file).to_dict()

    def export_netlist(self, json_file: str) -> JsonMap:
        return self.load_design(json_file).to_netlist()

    def export_verilog(self, json_file: str) -> JsonMap:
        return self.verilog.export(self.load_design(json_file))


class FrontendDesignService:
    """Stateful design editing service for frontend/API adapters."""

    contract = CONTRACT

    def __init__(
        self,
        design: Any | None = None,
        *,
        simulation: SimulationService | None = None,
        verilog: "VerilogExportService | None" = None,
    ):
        self.design = design
        self.simulation = simulation or SimulationService()
        self.verilog = verilog or VerilogExportService()

    def create_design(self, name: str = "untitled", *, description: str = "") -> JsonMap:
        from .design import Design

        self.design = Design(str(name))
        self.design.description = str(description)
        return self.snapshot()

    def load(self, data: JsonMap) -> JsonMap:
        from .design import Design

        self.design = Design.from_dict(data)
        return self.snapshot()

    def export_json(self) -> JsonMap:
        design = self._require_design()
        return self._ok("export-json", design.to_dict())

    def create_chip(self, ref: str, part: str, **properties: Any) -> JsonMap:
        design = self._require_design()
        design.chips[str(ref)] = {"part": str(part), **properties}
        self._clear_runtime()
        return self.frontend_snapshot()

    def delete_chip(self, ref: str) -> JsonMap:
        design = self._require_design()
        ref = str(ref)
        design.chips.pop(ref, None)
        design.connections = [rule for rule in design.connections if not _rule_mentions_ref(rule, ref)]
        self._clear_runtime()
        return self.frontend_snapshot()

    def connect(self, rule: str) -> JsonMap:
        design = self._require_design()
        design.connections.append(str(rule))
        self._clear_runtime()
        return self.frontend_snapshot()

    def disconnect(self, rule: str) -> JsonMap:
        design = self._require_design()
        try:
            design.connections.remove(str(rule))
        except ValueError:
            return self._fail("disconnect", [{"type": "connection_missing", "rule": str(rule)}])
        self._clear_runtime()
        return self.frontend_snapshot()

    def add_bus(self, name: str, width: int = 1, **properties: Any) -> JsonMap:
        design = self._require_design()
        design.buses[str(name)] = {"width": int(width), **properties}
        self._clear_runtime()
        return self.frontend_snapshot()

    def set_inputs(self, name: str, rules: list[str] | dict[str, Any]) -> JsonMap:
        design = self._require_design()
        if isinstance(rules, dict):
            design.inputs[str(name)] = [f"{ref} = {value}" for ref, value in rules.items()]
        else:
            design.inputs[str(name)] = [str(rule) for rule in rules]
        self._clear_runtime()
        return self.frontend_snapshot()

    def step(self, step: str) -> JsonMap:
        design = self._require_design()
        return self.simulation.run(design, steps=[str(step)])

    def run(self, steps: str | list[str] = "all") -> JsonMap:
        return self.simulation.run(self._require_design(), steps=steps)

    def read_probes(self, set_name: str | None = None) -> JsonMap:
        return self.simulation.probe(self._require_design(), set_name=set_name)

    def validate(self) -> JsonMap:
        return self.simulation.validate(self._require_design())

    def snapshot(self) -> JsonMap:
        return self.simulation.snapshot(self._require_design())

    def frontend_snapshot(self) -> JsonMap:
        return self.simulation.frontend_snapshot(self._require_design())

    def export_netlist(self) -> JsonMap:
        return self._ok("export-netlist", self._require_design().to_netlist())

    def export_verilog(self) -> JsonMap:
        return self._ok("export-verilog", self.verilog.export(self._require_design()))

    def component_catalog(self, *, group: str | None = None) -> JsonMap:
        return self._ok("component-catalog", component_catalog(group=group))

    def student_component_catalog(self, *, group: str | None = None) -> JsonMap:
        return self._ok("student-component-catalog", student_component_catalog(group=group))

    def component_detail(self, part: str) -> JsonMap:
        return self._ok("component-detail", component_detail(part))

    def component_metadata(self, part: str) -> JsonMap:
        return self._ok("component-metadata", component_detail(part))

    def _require_design(self) -> Any:
        if self.design is None:
            raise ValueError("no design loaded")
        return self.design

    def _clear_runtime(self) -> None:
        if self.design is None:
            return
        self.design._board = None
        self.design.stimulus = None
        self.design.probe_controller = None

    def _ok(self, command: str, result: JsonMap) -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": True,
            "result": result,
            "warnings": [],
            "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
        }

    def _fail(self, command: str, errors: list[Any]) -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": False,
            "warnings": [],
            "errors": errors,
            "error": {
                "code": "frontend.operation_failed",
                "message": f"{command} failed.",
                "severity": "error",
                "details": {"errors": errors},
            },
            "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
        }


class VerilogExportService:
    """Stable internal boundary for structural Verilog export."""

    contract = CONTRACT

    def export(self, design: Any, *, include_testbench: bool = True) -> JsonMap:
        exported = design_to_verilog(design, include_testbench=include_testbench)
        exported.setdefault("warnings", [])
        exported["required_files"] = self.required_files(exported.get("netlist", {}))
        return exported

    def required_files(self, netlist: JsonMap) -> list[str]:
        files: set[str] = set()
        for chip in netlist.get("chips", []):
            if not isinstance(chip, dict):
                continue
            part = str(chip.get("part", "")).upper()
            mapping = _verilog_mapping(part)
            if mapping is None:
                continue
            path = _verilog_file_for_part(part, str(mapping.get("module", "")))
            if path is not None:
                files.add(path)
        return sorted(files)


def export_verilog(design: Any, *, include_testbench: bool = True) -> JsonMap:
    """Export structural Verilog through the service boundary."""

    return VerilogExportService().export(design, include_testbench=include_testbench)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _probe_channels(items: Any) -> list[Any]:
    if isinstance(items, dict):
        channels = items.get("channels", [])
        return channels if isinstance(channels, list) else []
    return items if isinstance(items, list) else []


def _rule_mentions_ref(rule: str, ref: str) -> bool:
    for token in str(rule).replace("->", ",").replace("<->", ",").split(","):
        endpoint = token.strip()
        if endpoint == ref or endpoint.startswith(f"{ref}:"):
            return True
    return False


def _warnings_from_run(payload: JsonMap) -> list[JsonMap]:
    warnings: list[JsonMap] = []
    for item in payload.get("log", []):
        if isinstance(item, dict) and item.get("warning"):
            warnings.append({"step": item.get("step"), "warning": item.get("warning")})
    return warnings


def _board_errors(payload: JsonMap) -> list[Any]:
    snapshot = payload.get("snapshot", {})
    if not isinstance(snapshot, dict):
        return []
    board = snapshot.get("board", {})
    if not isinstance(board, dict):
        return []
    errors = board.get("errors", [])
    return errors if isinstance(errors, list) else []


def _expectation_errors(payload: JsonMap) -> list[Any]:
    expectations = payload.get("expectations", {})
    if not isinstance(expectations, dict):
        return []
    failed = expectations.get("failed", [])
    if not isinstance(failed, list):
        return []
    return [
        {"type": "expectation_failed", "name": item.get("name"), "checks": item.get("checks", [])}
        for item in failed
        if isinstance(item, dict)
    ]


def _frontend_snapshot(snapshot: JsonMap) -> JsonMap:
    design = snapshot.get("design", {})
    board = snapshot.get("board", {}) or {}
    return {
        "format": "components.frontend.snapshot",
        "version": 1,
        "design": {
            "name": design.get("name"),
            "description": design.get("description", ""),
            "modules": design.get("modules", {}),
            "groups": design.get("groups", {}),
        },
        "time_ns": board.get("time_ns", 0),
        "chips": board.get("chips", []),
        "buses": board.get("buses", []),
        "nets": board.get("nets", []),
        "rails": board.get("rails", []),
        "sources": board.get("sources", []),
        "stimulus": snapshot.get("stimulus"),
        "probes": snapshot.get("probes"),
        "displays": snapshot.get("displays", {}),
        "validation": snapshot.get("validate", {}),
        "errors": board.get("errors", []),
        "warnings": snapshot.get("validate", {}).get("warnings", []) if isinstance(snapshot.get("validate"), dict) else [],
        "layout": design.get("layout", {}),
        "labels": design.get("aliases", {}),
    }


def _verilog_file_for_part(part: str, module: str) -> str | None:
    try:
        manifest = component_detail(part)
        verilog = manifest.get("verilog", {})
        if isinstance(verilog, dict) and isinstance(verilog.get("file"), str):
            return str(verilog["file"])
    except (KeyError, ValueError):
        pass
    if module.startswith("ttl_"):
        return f"Verilog/74xx/{part.lower()}.v"
    if module.startswith("mem_"):
        return f"Verilog/Memory/{module[4:]}.v"
    return None
