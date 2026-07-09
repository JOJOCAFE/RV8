#!/usr/bin/env python3
"""Export RV8GR-V2 KiCad netlist to structural chip-level Verilog."""

from __future__ import annotations

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS_PYTHON = Path(os.environ.get("COMPONENTS_PYTHON", "/home/jo/kiro/Components/python"))
KICAD_NETLIST = ROOT / "Kicad" / "RV8GR-V2.net"
OUTPUT = ROOT / "rtl" / "rv8gr_v2_chip_level.v"


def main() -> int:
    sys.path.insert(0, str(COMPONENTS_PYTHON))
    try:
        from chiplib.design import Design
    except ImportError as exc:
        print(f"ERROR: cannot import chiplib from {COMPONENTS_PYTHON}: {exc}", file=sys.stderr)
        return 1

    design = Design.from_kicad_netlist(KICAD_NETLIST, name="rv8gr_v2_chip_level")
    exported = design.to_verilog(include_testbench=False)
    if not exported["ok"]:
        print("ERROR: unsupported parts in KiCad netlist:", file=sys.stderr)
        for item in exported["unsupported"]:
            print(f"  {item['ref']} {item['part']}: {item['reason']}", file=sys.stderr)
        return 1

    OUTPUT.write_text(exported["verilog"], encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
