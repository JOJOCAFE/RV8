"""Tests for frontend editing service and local JSON API adapter."""

from __future__ import annotations

from chiplib.api import handle_request
from chiplib.services import FrontendDesignService


def test_frontend_design_service_edits_and_exports_design():
    service = FrontendDesignService()
    service.create_design("api-small")
    service.create_chip("U1", "74HC00", label="NAND")
    service.add_bus("DATA", 2)
    service.connect("DATA:0 -> U1:1")
    service.connect("DATA:1 -> U1:2")
    service.connect("VCC -> U1:14")
    service.connect("GND -> U1:7")
    service.set_inputs("power_on", {"DATA:0": 1, "DATA:1": 1})

    run = service.run(["apply power_on", "settle"])
    assert run["ok"] is True
    snapshot = service.frontend_snapshot()["result"]
    assert snapshot["format"] == "components.frontend.snapshot"
    assert snapshot["chips"][0]["ref"] == "U1"
    assert snapshot["buses"][0]["name"] == "DATA"

    exported = service.export_json()["result"]
    assert exported["chips"]["U1"]["part"] == "74HC00"
    assert exported["inputs"]["power_on"] == ["DATA:0 = 1", "DATA:1 = 1"]

    service.disconnect("DATA:1 -> U1:2")
    assert "DATA:1 -> U1:2" not in service.export_json()["result"]["connect"]
    service.delete_chip("U1")
    assert service.export_json()["result"]["chips"] == {}


def test_json_api_adapter_dispatches_stateful_frontend_commands():
    service = FrontendDesignService()

    created = handle_request({"command": "create-design", "options": {"name": "api-session"}}, service)
    assert created["ok"] is True

    chip = handle_request({"command": "create-chip", "options": {"ref": "U1", "part": "74HC04"}}, service)
    assert chip["ok"] is True

    connected = handle_request({"command": "connect", "options": {"rule": "A -> U1:1"}}, service)
    assert connected["ok"] is True

    exported = handle_request({"command": "export-json"}, service)
    assert exported["result"]["name"] == "api-session"
    assert exported["result"]["chips"]["U1"]["part"] == "74HC04"
    assert exported["result"]["connect"] == ["A -> U1:1"]

    unknown = handle_request({"command": "missing-command"}, service)
    assert unknown["ok"] is False
    assert unknown["error"]["code"] == "api.unknown_command"


def test_json_api_adapter_exposes_component_metadata_without_design():
    service = FrontendDesignService()

    catalog = handle_request({"command": "component-catalog", "options": {"group": "memory"}}, service)
    assert catalog["ok"] is True
    assert catalog["result"]["format"] == "components.db.catalog"
    assert catalog["result"]["group"] == "memory"
    assert {item["part"] for item in catalog["result"]["components"]} == {"62256", "AS6C62256", "AT28C256", "CY7C199", "SST39SF010A"}

    student_catalog = handle_request({"command": "student-component-catalog", "options": {"group": "virtual"}}, service)
    assert student_catalog["ok"] is True
    assert student_catalog["result"]["format"] == "components.db.student_catalog"
    probe = next(item for item in student_catalog["result"]["components"] if item["part"] == "Probe")
    assert probe["readiness"] == "usable"
    assert probe["capabilities"]["can_simulate"] is True

    detail = handle_request({"command": "component-detail", "options": {"part": "74HC00"}}, service)
    assert detail["ok"] is True
    assert detail["result"]["format"] == "components.db.component"
    assert detail["result"]["db_path"] == "DB/74xx/74HC00/chip.json"
    assert detail["result"]["capabilities"]["physical_pinout"] is True


def run_all():
    test_frontend_design_service_edits_and_exports_design()
    test_json_api_adapter_dispatches_stateful_frontend_commands()
    test_json_api_adapter_exposes_component_metadata_without_design()


if __name__ == "__main__":
    run_all()
    print("Components API tests passed")
