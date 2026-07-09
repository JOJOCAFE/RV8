"""Local JSON API adapter for Components services."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from typing import Any

from .services import CONTRACT, FrontendDesignService


JsonMap = dict[str, Any]


def handle_request(request: JsonMap, service: FrontendDesignService | None = None) -> JsonMap:
    """Handle one service request for stdio or HTTP adapters."""

    service = service or FrontendDesignService()
    try:
        command = str(request.get("command", ""))
        input_data = request.get("input", {})
        options = request.get("options", {})
        if not isinstance(input_data, dict):
            input_data = {}
        if not isinstance(options, dict):
            options = {}
        schematic = input_data.get("schematic")
        if isinstance(schematic, dict):
            service.load(schematic)

        if command == "create-design":
            return service.create_design(
                str(options.get("name", input_data.get("name", "untitled"))),
                description=str(options.get("description", input_data.get("description", ""))),
            )
        if command == "load":
            return service.load(_required_map(input_data, "schematic"))
        if command == "create-chip":
            properties = dict(options.get("properties", {})) if isinstance(options.get("properties"), dict) else {}
            return service.create_chip(str(options.get("ref", input_data.get("ref"))), str(options.get("part", input_data.get("part"))), **properties)
        if command == "delete-chip":
            return service.delete_chip(str(options.get("ref", input_data.get("ref"))))
        if command == "connect":
            return service.connect(str(options.get("rule", input_data.get("rule"))))
        if command == "disconnect":
            return service.disconnect(str(options.get("rule", input_data.get("rule"))))
        if command == "add-bus":
            return service.add_bus(str(options.get("name", input_data.get("name"))), int(options.get("width", input_data.get("width", 1))))
        if command == "set-inputs":
            return service.set_inputs(str(options.get("name", input_data.get("name"))), options.get("rules", input_data.get("rules", [])))
        if command == "step":
            return service.step(str(options.get("step", input_data.get("step"))))
        if command == "validate":
            return service.validate()
        if command == "snapshot":
            return service.snapshot()
        if command == "frontend-snapshot":
            return service.frontend_snapshot()
        if command == "component-catalog":
            group = options.get("group", input_data.get("group"))
            return service.component_catalog(group=str(group) if group is not None else None)
        if command == "student-component-catalog":
            group = options.get("group", input_data.get("group"))
            return service.student_component_catalog(group=str(group) if group is not None else None)
        if command == "component-detail":
            return service.component_detail(str(options.get("part", input_data.get("part"))))
        if command == "component-metadata":
            return service.component_metadata(str(options.get("part", input_data.get("part"))))
        if command == "run":
            return service.run(options.get("steps", input_data.get("steps", "all")))
        if command == "probe":
            set_name = options.get("set", input_data.get("set"))
            return service.read_probes(str(set_name) if set_name is not None else None)
        if command == "export-json":
            return service.export_json()
        if command == "export-netlist":
            return service.export_netlist()
        if command == "export-verilog":
            return service.export_verilog()
        return _error(command or "unknown", "api.unknown_command", f"unknown command {command!r}")
    except Exception as exc:  # pragma: no cover - defensive adapter boundary
        return _error(str(request.get("command", "unknown")), "api.request_failed", str(exc), exception=exc.__class__.__name__)


def run_stdio(service: FrontendDesignService | None = None) -> int:
    service = service or FrontendDesignService()
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle_request(json.loads(line), service)
        sys.stdout.write(json.dumps(response, sort_keys=True) + "\n")
        sys.stdout.flush()
    return 0


def run_http(host: str = "127.0.0.1", port: int = 8765, service: FrontendDesignService | None = None) -> int:
    service = service or FrontendDesignService()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib API name
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                request = json.loads(raw.decode("utf-8"))
                response = handle_request(request, service)
                status = 200 if response.get("ok", False) else 400
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                response = _error("http", "api.bad_request", str(exc), exception=exc.__class__.__name__)
                status = 400
            body = json.dumps(response, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib API name
            return

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m chiplib.api")
    parser.add_argument("--stdio", action="store_true", help="read newline-delimited JSON requests from stdin")
    parser.add_argument("--http", action="store_true", help="serve local HTTP POST requests")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    if args.http:
        return run_http(args.host, args.port)
    return run_stdio()


def _required_map(data: JsonMap, key: str) -> JsonMap:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"input.{key} must be an object")
    return value


def _error(command: str, code: str, message: str, *, exception: str | None = None) -> JsonMap:
    details: JsonMap = {}
    if exception is not None:
        details["exception"] = exception
    return {
        "contract": CONTRACT,
        "command": command,
        "ok": False,
        "warnings": [],
        "error": {"code": code, "message": message, "severity": "error", "details": details},
        "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
    }


if __name__ == "__main__":
    raise SystemExit(main())
