"""Executable contract tests for the planned schematic Design API."""

from chiplib import Board
from chiplib.design import Design


def small_schematic():
    return {
        "name": "small-nand-schematic",
        "chips": [
            {"ref": "U1", "part": "74HC00"},
        ],
        "buses": [
            {"name": "DATA", "width": 8},
        ],
        "aliases": {
            "A": "U1:1",
            "B": "U1:2",
            "Y": "U1:3",
            "DATA0": "DATA:0",
        },
        "connections": [
            "A -> DATA:1",
            "B -> DATA:2",
            "U1:3 -> DATA:0",
            "VCC -> U1:14",
            "GND -> U1:7",
        ],
        "pullups": [
            "DATA:0",
            "DATA0",
        ],
        "pulldowns": [
            "DATA:7",
        ],
        "inputs": {
            "power_on": {
                "A": 1,
                "B": 0,
            },
        },
        "input_sets": [
            {
                "name": "front_panel",
                "channels": [
                    {"index": 0, "name": "SW_A", "target": "A", "power_on": 1},
                    {"index": 1, "name": "SW_B", "target": "B", "power_on": 0},
                ],
            },
        ],
        "probes": [
            {
                "set": "logic",
                "channels": [
                    {"name": "nand_y_pin", "target": "Y"},
                    {"name": "data0_bus", "target": "DATA:0"},
                ],
            },
        ],
    }


def require_design_io(design):
    """Return optional IO controllers using the planned Design API."""
    if hasattr(design, "to_io"):
        return design.to_io()
    if hasattr(design, "io"):
        return design.io()
    raise AssertionError("Design should expose named input_sets and probes through to_io() or io()")


def assert_snapshot_has_top_level_sections(snapshot):
    for key in ("chips", "buses", "nets", "rails", "sources"):
        assert key in snapshot, f"snapshot missing {key!r}"


def test_from_dict_to_dict_round_trip_preserves_schematic_contract():
    schematic = small_schematic()

    design = Design.from_dict(schematic)
    data = design.to_dict()
    assert data["name"] == schematic["name"]
    assert data["chips"]["U1"]["part"] == "74HC00"
    assert data["buses"]["DATA"]["width"] == 8
    assert data["connect"] == schematic["connections"]
    assert data["inputs"]["power_on"] == ["A = 1", "B = 0"]
    assert data["input_sets"]["front_panel"]["channels"][0]["name"] == "SW_A"
    assert data["probes"]["logic"]["channels"][1]["target"] == "DATA:0"


def test_design_to_board_materializes_aliases_buses_connections_power_and_pulls():
    design = Design.from_dict(small_schematic())

    board = design.to_board()
    assert isinstance(board, Board)

    snapshot = board.snapshot()
    assert_snapshot_has_top_level_sections(snapshot)

    chip_refs = {chip["ref"] for chip in snapshot["chips"]}
    assert chip_refs == {"U1"}

    buses = {bus["name"]: bus for bus in snapshot["buses"]}
    assert buses["DATA"]["width"] == 8

    data0 = buses["DATA"]["lines"][0]
    data1 = buses["DATA"]["lines"][1]
    data2 = buses["DATA"]["lines"][2]
    data7 = buses["DATA"]["lines"][7]

    assert data0["tag"] == "bus:DATA[0]"
    assert data1["tag"] == "bus:DATA[1]"
    assert data2["tag"] == "bus:DATA[2]"
    assert any(pin["chip"] == "U1" and pin["number"] == 3 for pin in data0["pins"])
    assert any(pin["chip"] == "U1" and pin["number"] == 1 for pin in data1["pins"])
    assert any(pin["chip"] == "U1" and pin["number"] == 2 for pin in data2["pins"])
    assert data0["value"] == 1
    assert data7["value"] == 0

    rails = {(rail["name"], rail["value"]) for rail in snapshot["rails"]}
    assert ("VCC", 1) in rails
    assert ("GND", 0) in rails

    source_names = {source["name"] for source in snapshot["sources"]}
    assert "rail:VCC->U1:14" in source_names
    assert "rail:GND->U1:7" in source_names

    net_by_name = {net["name"]: net for net in snapshot["nets"]}
    assert [pull["value"] for pull in net_by_name["bus:DATA[0]"]["pulls"]] == [1, 1]
    assert net_by_name["bus:DATA[7]"]["pulls"] == [{"source": "bus:DATA[7]", "value": 0}]


def test_design_exposes_power_on_inputs_input_sets_and_named_probe_sets():
    design = Design.from_dict(small_schematic())
    board = design.to_board()

    io = require_design_io(design)
    stimulus = io["stimulus"]
    probes = io["probes"]

    board.settle()
    stimulus_snapshot = stimulus.snapshot()
    probe_snapshot = probes.snapshot()

    input_sets = {item["name"]: item for item in stimulus_snapshot["input_sets"]}
    assert "front_panel" in input_sets

    front_panel_inputs = {
        channel["name"]: channel
        for channel in input_sets["front_panel"]["inputs"]
        if channel["name"] in {"SW_A", "SW_B"}
    }
    assert front_panel_inputs["SW_A"]["index"] == 0
    assert front_panel_inputs["SW_A"]["value"] == 1
    assert front_panel_inputs["SW_A"]["targets"] == [{"chip": "U1", "pin": 1}]
    assert front_panel_inputs["SW_B"]["index"] == 1
    assert front_panel_inputs["SW_B"]["value"] == 0
    assert front_panel_inputs["SW_B"]["targets"] == [{"chip": "U1", "pin": 2}]

    probe_sets = {item["name"]: item for item in probe_snapshot["sets"]}
    assert "logic" in probe_sets
    logic_channels = {channel["name"]: channel for channel in probe_sets["logic"]["channels"]}
    assert logic_channels["nand_y_pin"]["target_kind"] == "pin"
    assert logic_channels["nand_y_pin"]["target"] == "U1.1Y"
    assert logic_channels["data0_bus"]["target_kind"] == "bus"
    assert logic_channels["data0_bus"]["target"] == "bus:DATA[0]"


def test_design_adapts_db_virtual_sources_rails_pulls_and_probes():
    design = Design.from_dict({
        "name": "virtual-components",
        "chips": {
            "U1": {"part": "74HC00"},
            "S1": {"part": "InputSource", "initial": 1},
            "V1": {"part": "VCC"},
            "G1": {"part": "GND"},
            "PU1": {"part": "Pullup"},
            "PD1": {"part": "Pulldown"},
            "P1": {"part": "Probe"},
            "BP1": {"part": "BusProbe"},
        },
        "buses": {"DATA": {"width": 2}},
        "connections": [
            "S1:OUT -> U1:1, P1:IN",
            "V1:VCC -> U1:2",
            "VCC -> U1:14",
            "G1:GND -> U1:7",
            "PU1:PULL -> DATA:0, BP1:BUS",
            "PD1:PULL -> DATA:1",
        ],
        "inputs": {"toggle": {"S1:OUT": 0}},
        "steps": ["apply toggle", "probe"],
    })

    assert design.validate()["ok"]

    board = design.to_board()
    snapshot = board.snapshot()
    assert {chip["ref"] for chip in snapshot["chips"]} == {"U1"}

    source_names = {source["name"] for source in snapshot["sources"]}
    assert "input:S1:OUT->net:0" in source_names
    assert "rail:VCC->net:1" in source_names
    assert "rail:GND->net:3" in source_names

    nets = {net["name"]: net for net in snapshot["nets"]}
    assert nets["net:0"]["value"] == 0
    assert nets["net:1"]["value"] == 1
    assert nets["net:3"]["value"] == 0
    assert nets["bus:DATA[0]"]["pulls"] == [{"source": "bus:DATA[0]", "value": 1}]
    assert nets["bus:DATA[1]"]["pulls"] == [{"source": "bus:DATA[1]", "value": 0}]

    probe_sets = {item["name"]: item for item in design.to_io()["probes"].snapshot()["sets"]}
    default_channels = {channel["name"]: channel for channel in probe_sets["default"]["channels"]}
    assert default_channels["P1"]["target_kind"] == "net"
    assert default_channels["P1"]["target"] == "net:0"
    assert default_channels["BP1"]["target_kind"] == "bus"
    assert default_channels["BP1"]["target"] == "bus:DATA[0]"

    result = design.run()
    assert result["ok"]
    run_sources = {
        source["name"]: source
        for source in result["snapshot"]["board"]["sources"]
    }
    assert run_sources["input:S1:OUT->net:0"]["value"] == 0


def test_design_loads_passive_and_discrete_db_components_without_behavior_model():
    design = Design.from_dict({
        "name": "passive-discrete-components",
        "chips": {
            "LED1": {"part": "LED"},
            "R1": {"part": "Resistor"},
            "C1": {"part": "Capacitor"},
            "Q1": {"part": "NPN"},
            "Q2": {"part": "PNP"},
        },
        "connections": [
            "LED1:A -> LED_A",
            "LED1:K -> GND",
            "R1:1 -> R_A",
            "R1:2 -> R_B",
            "C1:1 -> C_A",
            "C1:2 -> C_B",
            "Q1:C -> QC",
            "Q1:B -> QB",
            "Q1:E -> QE",
            "Q2:C -> PC",
            "Q2:B -> PB",
            "Q2:E -> PE",
        ],
        "steps": ["settle"],
    })

    assert design.validate()["ok"]
    board = design.to_board()
    snapshot = board.snapshot()
    assert snapshot["chips"] == []
    assert not snapshot["errors"]
    assert design.run()["ok"]


def test_design_runner_evaluates_expectations_and_probe_history():
    design = Design.from_dict({
        "name": "expectations",
        "chips": {"U1": {"part": "74HC00"}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3"},
        "connections": ["VCC -> U1:14", "GND -> U1:7"],
        "inputs": {
            "both_high": ["A = 1", "B = 1"],
            "a_low": ["A = 0", "B = 1"],
        },
        "probes": {"logic": ["Y"]},
        "expect": {
            "nand_low": ["Y = 0"],
            "nand_changed": ["Y has rising"],
            "wrong": ["Y = 1"],
        },
        "steps": [
            "apply both_high",
            "settle",
            "probe",
            "expect nand_low",
            "apply a_low",
            "probe",
            "expect nand_changed",
        ],
    })

    passed = design.run()
    assert passed["ok"] is True
    assert [item["name"] for item in passed["expectations"]["passed"]] == ["nand_low", "nand_changed"]
    assert passed["expectations"]["failed"] == []
    assert passed["timing"]["steps"] == 7

    failed = Design.from_dict({**design.to_dict(), "steps": ["apply both_high", "expect wrong"]}).run()
    assert failed["ok"] is False
    assert failed["expectations"]["failed"][0]["name"] == "wrong"
    assert failed["expectations"]["failed"][0]["checks"][0]["actual"] == 0


def run_all():
    test_from_dict_to_dict_round_trip_preserves_schematic_contract()
    test_design_to_board_materializes_aliases_buses_connections_power_and_pulls()
    test_design_exposes_power_on_inputs_input_sets_and_named_probe_sets()
    test_design_adapts_db_virtual_sources_rails_pulls_and_probes()
    test_design_loads_passive_and_discrete_db_components_without_behavior_model()
    test_design_runner_evaluates_expectations_and_probe_history()


if __name__ == "__main__":
    run_all()
    print("Components Python design tests passed")
