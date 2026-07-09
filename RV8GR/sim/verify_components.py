#!/usr/bin/env python3
"""Verify RV8GR against the vendored Components runtime.

This does not replace the older RV8GR teaching simulator. It proves that the
shared Components DB/Python/Verilog bundle copied under third_party is usable
for RV8GR verification and chip-level export.
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS_ROOT = Path(os.environ.get("COMPONENTS_ROOT", ROOT / "third_party" / "Components"))
COMPONENTS_PYTHON = Path(os.environ.get("COMPONENTS_PYTHON", COMPONENTS_ROOT / "python"))

RV8GR_PART_COUNTS = {
    "74HC00": 2,
    "74HC04": 1,
    "74HC21": 1,
    "74HC32": 1,
    "74HC74": 2,
    "74HC86": 3,
    "74HC157": 8,
    "74HC161": 4,
    "74HC164": 1,
    "74HC245": 1,
    "74HC283": 2,
    "74HC541": 2,
    "74HC574": 5,
    "74HC688": 1,
    "62256": 1,
    "AT28C256": 1,
}


def main() -> int:
    if not COMPONENTS_PYTHON.exists():
        print(f"ERROR: Components Python path not found: {COMPONENTS_PYTHON}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(COMPONENTS_PYTHON))

    try:
        from chiplib.chips import create_chip
        from chiplib.db import audit_db, component_detail, component_ids, student_component_catalog
    except ImportError as exc:
        print(f"ERROR: cannot import vendored chiplib from {COMPONENTS_PYTHON}: {exc}", file=sys.stderr)
        return 1

    ids = set(component_ids())
    missing = sorted(part for part in RV8GR_PART_COUNTS if part not in ids)
    if missing:
        print(f"ERROR: RV8GR parts missing from Components DB: {', '.join(missing)}", file=sys.stderr)
        return 1

    audit = audit_db()
    if not audit["ok"]:
        print("ERROR: Components DB audit failed", file=sys.stderr)
        for item in audit.get("errors", []):
            print(f"  {item.get('code')}: {item.get('message')}", file=sys.stderr)
        return 1

    for part in sorted(RV8GR_PART_COUNTS):
        detail = component_detail(part)
        chip = create_chip(part, f"CHECK_{part}")
        expected_pins = detail["package"]["pins"]
        if len(chip.pins) != expected_pins:
            print(
                f"ERROR: {part} Python model has {len(chip.pins)} pins, DB expects {expected_pins}",
                file=sys.stderr,
            )
            return 1
        capabilities = detail["capabilities"]
        if not capabilities["python_behavior"]:
            print(f"ERROR: {part} has no Components Python behavior", file=sys.stderr)
            return 1
        if not capabilities["verilog_export"]:
            print(f"ERROR: {part} has no Components Verilog export metadata", file=sys.stderr)
            return 1
        verilog_file = capabilities["verilog_file"]
        if verilog_file and not (COMPONENTS_ROOT / verilog_file).exists():
            print(f"ERROR: {part} Verilog file missing: {verilog_file}", file=sys.stderr)
            return 1

    student_catalog = student_component_catalog(group="74xx")
    ready_parts = {item["part"] for item in student_catalog["components"] if item["readiness"] == "ready"}
    not_ready = sorted(part for part in RV8GR_PART_COUNTS if part.startswith("74HC") and part not in ready_parts)
    if not_ready:
        print(f"ERROR: RV8GR logic parts not ready in student catalog: {', '.join(not_ready)}", file=sys.stderr)
        return 1

    total = sum(RV8GR_PART_COUNTS.values())
    print(f"RV8GR Components verification passed: {len(RV8GR_PART_COUNTS)} part types, {total} packages")
    print(f"Components root: {COMPONENTS_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
