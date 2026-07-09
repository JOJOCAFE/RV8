"""DB manifest tests."""

import json

from chiplib.db import audit_db, component_catalog, component_detail, component_ids, component_summary, db_root, db_status_report, legacy_catalog_parts, load_all_components, load_component, student_component_catalog
from chiplib.db import _pinout_mismatches


ALLOWED_STATUS = {
    "verified",
    "modeled",
    "tested",
    "missing",
    "blocked",
    "unknown",
    "not_applicable",
}
ALLOWED_DIRECTIONS = {"input", "output", "bidirectional", "passive", "power", "nc", "unknown"}
SEED_PARTS = {
    "62256",
    "74HC00",
    "74HC04",
    "74HC74",
    "74HC138",
    "74HC161",
    "74HC245",
    "74HC574",
    "AT28C256",
    "SST39SF010A",
}
GROUPED_PARTS = {
    "InputSource",
    "ClockSource",
    "Probe",
    "BusProbe",
    "VCC",
    "GND",
    "Pullup",
    "Pulldown",
    "LED",
    "Resistor",
    "Capacitor",
    "NPN",
    "PNP",
}


def test_db_seed_entries_are_loadable():
    assert db_root().name == "DB"
    assert SEED_PARTS.issubset(set(component_ids()))
    assert GROUPED_PARTS.issubset(set(component_ids()))
    assert "74HC147" in component_ids()

    hc00 = load_component("74HC00")
    assert hc00["part"] == "74HC00"
    assert hc00["package"]["pins"] == 14
    assert hc00["verilog"]["module"] == "ttl_74hc00"
    assert hc00["verilog"]["export"]["ports"] == [
        {"name": "A", "pins": [1, 4, 9, 12], "direction": "input"},
        {"name": "B", "pins": [2, 5, 10, 13], "direction": "input"},
        {"name": "Y", "pins": [3, 6, 8, 11], "direction": "output"},
    ]
    assert hc00["verilog"]["export"]["output_pins"] == [3, 6, 8, 11]
    assert hc00["verilog"]["export"]["delay_ns"] == {"U26": 8, "*": 1}
    assert hc00["missing_properties"] == []
    assert hc00["missing_files"] == []
    assert hc00["pins"][0] == {"number": 1, "name": "1A", "direction": "input"}

    ram = load_component("62256")
    assert ram["family"] == "Memory"
    assert ram["pins"][10]["direction"] == "bidirectional"
    assert ram["pins"][19]["active_low"] is True

    transceiver = load_component("74HC245")
    assert transceiver["package"]["pins"] == 20
    assert transceiver["pins"][1]["direction"] == "bidirectional"
    assert transceiver["pins"][18]["active_low"] is True
    assert transceiver["verilog"]["export"]["ports"] == [
        {"name": "OE_bar", "pins": [19], "direction": "input"},
        {"name": "DIR", "pins": [1], "direction": "input"},
        {"name": "A", "pins": [2, 3, 4, 5, 6, 7, 8, 9], "direction": "output"},
        {"name": "B", "pins": [18, 17, 16, 15, 14, 13, 12, 11], "direction": "output"},
    ]

    counter = load_component("74HC161")
    assert counter["pins"][0]["name"] == "/CLR"
    assert counter["pins"][14] == {"number": 15, "name": "RCO", "direction": "output"}
    assert counter["verilog"]["export"]["ports"] == [
        {"name": "Clear_bar", "pins": [1], "direction": "input"},
        {"name": "Load_bar", "pins": [9], "direction": "input"},
        {"name": "ENT", "pins": [10], "direction": "input"},
        {"name": "ENP", "pins": [7], "direction": "input"},
        {"name": "D", "pins": [3, 4, 5, 6], "direction": "input"},
        {"name": "Clk", "pins": [2], "direction": "input"},
        {"name": "RCO", "pins": [15], "direction": "output"},
        {"name": "Q", "pins": [14, 13, 12, 11], "direction": "output"},
    ]

    inverter = load_component("74HC04")
    assert inverter["verilog"]["export"]["ports"] == [
        {"name": "A", "pins": [1, 3, 5, 9, 11, 13], "direction": "input"},
        {"name": "Y", "pins": [2, 4, 6, 8, 10, 12], "direction": "output"},
    ]

    eeprom = load_component("AT28C256")
    assert eeprom["family"] == "Memory"
    assert eeprom["verilog"]["module"] == "mem_at28c256"

    dff = load_component("74HC74")
    assert dff["package"]["pins"] == 14
    assert dff["pins"][0]["name"] == "/1CLR"
    assert dff["pins"][5]["active_low"] is True

    register = load_component("74HC574")
    assert register["verilog"]["module"] == "ttl_74hc574"
    assert register["pins"][0]["active_low"] is True
    assert register["pins"][11] == {"number": 12, "name": "8Q", "direction": "output"}

    decoder = load_component("74HC138")
    assert decoder["verilog"]["module"] == "ttl_74hc138"
    assert decoder["pins"][3]["name"] == "/G2A"
    assert decoder["pins"][14]["active_low"] is True

    encoder = load_component("74HC147")
    assert encoder["status"]["verilog_export"] == "tested"
    assert encoder["verilog"]["export"]["ports"][0] == {"name": "I0_bar", "pins": [9], "direction": "input"}
    assert encoder["pins"][8] == {"number": 9, "name": "/I0", "direction": "input", "active_low": True}
    assert encoder["pins"][14] == {"number": 15, "name": "NC", "direction": "nc"}

    flash = load_component("SST39SF010A")
    assert flash["family"] == "Memory"
    assert flash["package"]["pins"] == 32
    assert flash["pins"][0]["direction"] == "nc"
    assert flash["verilog"]["module"] == "mem_sst39sf010a"

    source = load_component("InputSource")
    assert source["group"] == "virtual"
    assert source["kind"] == "virtual"
    assert source["role"] == "stimulus"
    assert source["pins"] == [{"number": 1, "name": "OUT", "direction": "output"}]
    assert source["simulation"]["service"] == "sim.input_source"

    led = load_component("LED")
    assert led["group"] == "passive"
    assert led["pins"][0]["direction"] == "passive"
    assert led["ui"]["symbol"] == "led"

    npn = load_component("NPN")
    assert npn["group"] == "discrete"
    assert [pin["name"] for pin in npn["pins"]] == ["C", "B", "E"]


def test_db_summary_reports_status_and_gaps():
    summary = component_summary()
    assert summary["format"] == "db.summary"
    assert summary["count"] >= 3
    parts = [item["part"] for item in summary["components"]]
    assert SEED_PARTS.issubset(set(parts))
    assert GROUPED_PARTS.issubset(set(parts))
    assert all(item["missing_properties"] == [] for item in summary["components"])
    assert all(item["missing_files"] == [] for item in summary["components"])


def test_db_component_catalog_is_frontend_ready_and_grouped():
    catalog = component_catalog()
    assert catalog["format"] == "components.db.catalog"
    assert catalog["count"] >= 75
    groups = {item["id"]: item for item in catalog["groups"]}
    assert groups["74xx"]["count"] >= 57
    assert groups["memory"]["count"] == 5
    assert groups["virtual"]["count"] >= 8

    hc00 = next(item for item in catalog["components"] if item["part"] == "74HC00")
    assert hc00["group"] == "74xx"
    assert hc00["db_path"] == "DB/74xx/74HC00/chip.json"
    assert hc00["capabilities"]["physical_pinout"] is True
    assert hc00["capabilities"]["verilog_file"] == "Verilog/74xx/74hc00.v"
    assert hc00["warnings"] == []

    memory = component_catalog(group="memory")
    assert memory["group"] == "memory"
    assert {item["part"] for item in memory["components"]} == {"62256", "AS6C62256", "AT28C256", "CY7C199", "SST39SF010A"}


def test_student_component_catalog_is_learner_facing_and_status_visible():
    catalog = student_component_catalog(group="virtual")
    assert catalog["format"] == "components.db.student_catalog"
    assert catalog["audience"] == "students ages 10-15, still useful for older learners"
    assert catalog["legend"]["ready"].startswith("Good for building")
    probe = next(item for item in catalog["components"] if item["part"] == "Probe")
    assert probe["readiness"] == "usable"
    assert probe["capabilities"]["can_simulate"] is True
    assert probe["capabilities"]["can_export_verilog"] is False
    assert probe["pins"]["preview"] == [{"number": 1, "name": "IN", "direction": "input"}]
    assert probe["warnings"] == []

    hc00 = next(item for item in student_component_catalog(group="74xx")["components"] if item["part"] == "74HC00")
    assert hc00["readiness"] == "ready"
    assert hc00["capabilities"]["can_export_verilog"] is True
    assert hc00["files"]["verilog"] == "Verilog/74xx/74hc00.v"


def test_db_component_detail_exposes_pins_and_capabilities():
    detail = component_detail("AT28C256")
    assert detail["format"] == "components.db.component"
    assert detail["part"] == "AT28C256"
    assert detail["group"] == "memory"
    assert detail["db_path"] == "DB/Memory/AT28C256/chip.json"
    assert detail["pins"][0] == {"number": 1, "name": "A14", "direction": "input"}
    assert detail["capabilities"]["verilog_model"] is True
    assert detail["capabilities"]["verilog_file"] == "Verilog/Memory/at28c256.v"


def test_db_manifests_match_schema_contract():
    schema = json.loads((db_root() / "chip.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "db.chip"
    assert "passive" in schema["properties"]["pins"]["items"]["properties"]["direction"]["enum"]

    for manifest in load_all_components():
        for key in schema["required"]:
            assert key in manifest, (manifest.get("part"), key)
        assert manifest["schema"] == "db.chip"
        assert isinstance(manifest["version"], int)
        assert manifest["version"] >= 1
        assert manifest["package"]["pins"] == len(manifest["pins"])
        assert set(manifest["status"]).issuperset(set(schema["properties"]["status"]["required"]))
        assert set(manifest["status"].values()).issubset(ALLOWED_STATUS)
        for pin in manifest["pins"]:
            assert {"number", "name", "direction"}.issubset(pin)
            assert isinstance(pin["number"], int)
            assert pin["number"] >= 1
            assert pin["direction"] in ALLOWED_DIRECTIONS


def test_db_audit_reports_partial_legacy_coverage_without_hard_errors():
    audit = audit_db()
    assert audit["format"] == "db.audit"
    assert audit["ok"] is True
    assert audit["errors"] == []
    assert SEED_PARTS.issubset(set(audit["coverage"]["db_parts"]))
    assert "74HC147" in audit["coverage"]["db_parts"]
    assert "LED" not in audit["coverage"]["db_parts"]
    assert SEED_PARTS.issubset(set(audit["coverage"]["legacy_model_parts"]))
    assert "74HC147" not in audit["coverage"]["legacy_parts_missing_db"]
    assert audit["chip_status"]["format"] == "db.status"
    assert audit["chip_status"]["ok"] is True


def test_db_legacy_coverage_lists_models_and_pinouts():
    legacy = legacy_catalog_parts()
    assert "74HC00" in legacy["verilog_models"]
    assert "74HC00" in legacy["pinouts"]
    assert "AT28C256" in legacy["verilog_models"]
    assert "SST39SF010A" in legacy["pinouts"]
    legacy_backed = set(component_ids()) - GROUPED_PARTS
    assert legacy_backed.issubset(set(legacy["verilog_models"]))
    assert legacy_backed.issubset(set(legacy["pinouts"]))


def test_db_status_report_checks_chip_status_snapshot():
    report = db_status_report()
    tested_seed_parts = SEED_PARTS - {"74HC147"}
    assert report["format"] == "db.status"
    assert report["ok"] is True
    assert report["errors"] == []
    assert SEED_PARTS.issubset(set(report["generated"]["verified"]))
    assert SEED_PARTS.issubset(set(report["generated"]["modeled"]))
    assert tested_seed_parts.issubset(set(report["generated"]["tested"]))
    assert SEED_PARTS.issubset(set(report["chip_status"]["verified"]))
    assert SEED_PARTS.issubset(set(report["chip_status"]["modeled"]))
    assert tested_seed_parts.issubset(set(report["chip_status"]["tested"]))
    assert {"74HC150", "74HC260"}.issubset(set(report["chip_status"]["missing_datasheet"]))
    assert "74HC150" not in report["chip_status"]["tested"]
    assert "74HC260" not in report["chip_status"]["tested"]
    assert not any(item["code"] == "chip_status_parts_missing_db" and item.get("category") == "missing_datasheet" for item in report["warnings"])


def test_embedded_pinout_matches_grouped_db_manifest_pins():
    assert _pinout_mismatches(load_component("74HC00")) == []
    assert _pinout_mismatches(load_component("74HC147")) == []

    broken = load_component("74HC00")
    broken["pins"][0]["name"] = "BROKEN"
    issues = _pinout_mismatches(broken)
    assert issues == [{
        "code": "pinout_name_mismatch",
        "message": "pin 1 embedded pinout='1A' DB='BROKEN'",
    }]


def run_all():
    test_db_seed_entries_are_loadable()
    test_db_summary_reports_status_and_gaps()
    test_db_component_catalog_is_frontend_ready_and_grouped()
    test_db_component_detail_exposes_pins_and_capabilities()
    test_db_manifests_match_schema_contract()
    test_db_audit_reports_partial_legacy_coverage_without_hard_errors()
    test_db_legacy_coverage_lists_models_and_pinouts()
    test_db_status_report_checks_chip_status_snapshot()
    test_embedded_pinout_matches_grouped_db_manifest_pins()


if __name__ == "__main__":
    run_all()
    print("Components DB tests passed")
