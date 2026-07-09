"""Reusable pin-level chip models for JOJOCAFE TTL projects."""

from .core import (
    Board,
    Bus,
    BusConflictError,
    Chip,
    Delay,
    LogicSource,
    Net,
    Pin,
    PinSpec,
    Rail,
    X,
    Z,
    parse_bus_tag,
)
from .chips import CHIP_FACTORIES, create_chip
from .db import audit_db, component_ids, component_summary, db_root, db_status_report, legacy_catalog_parts, load_all_components, load_component
from .design import Design, Endpoint
from .loader import ImageLoadError, load_image, load_memory, parse_hex_text, parse_ihex
from .netlist import design_from_kicad_netlist, design_from_netlist, design_to_netlist, design_to_verilog
from .probe import ProbeChannel, ProbeController, ProbeError, ProbeSample, ProbeSet
from .services import DesignCommandService, FrontendDesignService, SimulationService, VerilogExportService, export_verilog
from .stimulus import ClockChannel, InputChannel, InputSet, StimulusController, StimulusError

__all__ = [
    "Board",
    "Bus",
    "BusConflictError",
    "CHIP_FACTORIES",
    "Chip",
    "Delay",
    "LogicSource",
    "Net",
    "Pin",
    "PinSpec",
    "Rail",
    "X",
    "Z",
    "parse_bus_tag",
    "create_chip",
    "audit_db",
    "component_ids",
    "component_summary",
    "db_root",
    "db_status_report",
    "legacy_catalog_parts",
    "load_all_components",
    "load_component",
    "Design",
    "Endpoint",
    "ImageLoadError",
    "load_image",
    "load_memory",
    "parse_hex_text",
    "parse_ihex",
    "design_from_netlist",
    "design_from_kicad_netlist",
    "design_to_netlist",
    "design_to_verilog",
    "DesignCommandService",
    "FrontendDesignService",
    "SimulationService",
    "VerilogExportService",
    "export_verilog",
    "ProbeChannel",
    "ProbeController",
    "ProbeError",
    "ProbeSample",
    "ProbeSet",
    "ClockChannel",
    "InputChannel",
    "InputSet",
    "StimulusController",
    "StimulusError",
]
