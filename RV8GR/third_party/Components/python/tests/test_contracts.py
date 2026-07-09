"""Contract tests for service-ready example schematic fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from chiplib.design import Design
from chiplib.services import VerilogExportService


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = [
    "nand",
    "counter",
    "bus_transceiver",
    "memory_read",
    "tiny_cpu_slice",
]


def load_example(name: str) -> Design:
    path = ROOT / "Examples" / f"{name}.json"
    return Design.from_dict(json.loads(path.read_text(encoding="utf-8")))


def test_service_ready_examples_validate_snapshot_run_netlist_and_export_verilog():
    service = VerilogExportService()
    for name in EXAMPLES:
        design = load_example(name)
        validation = design.validate()
        assert validation["ok"] is True, (name, validation)

        design = load_example(name)
        design.to_board()
        snapshot = design.snapshot()
        assert snapshot["validate"]["ok"] is True, name
        assert snapshot["board"]["chips"], name
        assert snapshot["board"]["errors"] == [], name

        run = load_example(name).run()
        assert run["ok"] is True, name
        assert run["log"], name

        netlist = load_example(name).to_netlist()
        assert netlist["format"] == "chiplib.netlist", name
        assert netlist["version"] == 1, name
        assert netlist["validation"]["ok"] is True, name
        assert netlist["board_errors"] == [], name

        exported = service.export(load_example(name))
        assert exported["ok"] is True, (name, exported["unsupported"])
        assert exported["warnings"] == [], name
        assert exported["required_files"], name
        assert exported["verilog"].startswith("`timescale 1ns/1ps"), name
        assert f"module {name}();" in exported["verilog"], name
        assert exported["testbench"].startswith("`timescale 1ns/1ps"), name


def test_design_to_verilog_uses_internal_service_boundary():
    design = load_example("nand")
    exported = design.to_verilog()

    assert exported["ok"] is True
    assert exported["warnings"] == []
    assert exported["required_files"] == ["Verilog/74xx/74hc00.v"]
    assert "ttl_74hc00" in exported["verilog"]


def run_all():
    test_service_ready_examples_validate_snapshot_run_netlist_and_export_verilog()
    test_design_to_verilog_uses_internal_service_boundary()


if __name__ == "__main__":
    run_all()
    print("Components contract tests passed")
