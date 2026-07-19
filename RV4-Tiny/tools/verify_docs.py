#!/usr/bin/env python3
"""Fast consistency checks for the RV4-Tiny document set."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "00_architecture.md",
    "01_control_and_timing.md",
    "02_signal_assignment.md",
    "03_wiring_guide.md",
    "04_schematic_checklist.md",
    "05_bill_of_materials.md",
    "06_breadboard_layout.md",
    "07_build_plan.md",
    "08_debug_guide.md",
    "09_simulator_spec.md",
    "10_assembler_spec.md",
    "11_chip_pinouts.md",
    "12_hardware_review.md",
    "13_student_probe_header_plan.md",
]

REQUIRED_SNIPPETS = {
    "README.md": [
        "RV4-Tiny v1.3",
        "16 packages total",
    ],
    "00_architecture.md": [
        "16 IC packages total",
        "All state-holding devices use the same rising-edge `CPU_CLK`",
        "clock/control support: U14 and U15",
    ],
    "02_signal_assignment.md": [
        "U3 74HC377",
        "U13 74HC4002",
        "output CLK_GATE_N",
    ],
    "01_control_and_timing.md": [
        "CLK_GATE_N = NOT(CLK_COND AND RUN)",
        "CPU_CLK_N  = NOT(CPU_CLK)",
        "RAM_WE_N = SW_N",
        "Z = NOR(AC0, AC1, AC2, AC3)",
    ],
    "10_assembler_spec.md": [
        "Silent truncation is forbidden",
        ".RAM address, value",
    ],
    "09_simulator_spec.md": [
        "Opcodes `1`, `2`, `3`, `C`, `D`, and `E` raise",
        "state must remain at the start of that EXECUTE",
    ],
    "Project_Context.md": [
        "tools/rv4_sim.py",
        "tools/rv4_asm.py",
        "python3 tools/rv4_sim.py --self-test",
        "python3 tools/test_rv4_asm.py",
    ],
    "05_bill_of_materials.md": [
        "14 logic packages",
        "16 IC packages",
    ],
    "13_student_probe_header_plan.md": [
        "Plug-in LED/probe boards",
        "Probe headers must not drive CPU signals",
    ],
}

FORBIDDEN_SNIPPETS = [
    "AC_CLK = CPU_CLK AND",
    "OUT_CLK = CPU_CLK AND",
    "U13 74HC02",
    "U13 74HC85",
    "v1.1",
    "v1.2",
    "13 Packages",
    "10/10",
    "ได้ครับ",
    "# Patch for",
]


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []

    for name in REQUIRED:
        if not (ROOT / name).is_file():
            fail(f"missing required file: {name}", failures)

    zone_files = sorted(ROOT.glob("*:Zone.Identifier"))
    for path in zone_files:
        fail(f"remove Windows metadata file: {path.name}", failures)

    markdown_files = sorted(ROOT.glob("*.md"))
    numbered_files = [path.name for path in markdown_files if path.name[:2].isdigit()]
    expected_numbered = REQUIRED[1:]
    if numbered_files != expected_numbered:
        fail(
            "numbered documents do not match the required reading order: "
            + ", ".join(numbered_files),
            failures,
        )

    texts = {}
    for path in markdown_files:
        try:
            texts[path.name] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(f"not valid UTF-8: {path.name}", failures)

    for name, snippets in REQUIRED_SNIPPETS.items():
        text = texts.get(name, "")
        for snippet in snippets:
            if snippet not in text:
                fail(f"{name}: missing required text: {snippet!r}", failures)

    for name, text in texts.items():
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                fail(f"{name}: stale or prohibited text: {snippet!r}", failures)
        if "\x00" in text:
            fail(f"{name}: contains NUL byte", failures)
        line_count = len(text.splitlines())
        if line_count > 230:
            fail(f"{name}: too long for the compact guide ({line_count} lines)", failures)

    if failures:
        print("DOC VERIFY FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"DOC VERIFY PASS ({len(markdown_files)} Markdown files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
