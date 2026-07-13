#!/usr/bin/env python3
"""Validate and compare RV8GR dual-RTL settled phase-trace JSONL records.

The behavioural RTL publishes a raw next-phase value at the settled sample.
Its raw T1/T2/T0 sequence maps to canonical settled T0/T1/T2.  This tool
preserves and reports that raw offset as diagnostics, then compares canonical
same-cycle observations.

It never turns an offset into an equivalence pass: malformed phase sequences,
an unexpected canonical phase relation, or a later shared-state mismatch all
fail.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "rv8gr.phase-trace@1"
CHIP_PHASE = {"001": 0, "010": 1, "100": 2}
PHASE_NAMES = ("T0", "T1", "T2")
BEHAVIORAL_RAW_TO_CANONICAL = {1: 0, 2: 1, 0: 2}
# PC/AC/Z/PG are still covered by the existing instruction-boundary dual
# scoreboard.  This first phase trace compares the state fields whose values
# have the same settled-cycle meaning in both models.
SAME_CYCLE_SHARED_STATE_FIELDS = ("ie", "irq_ff", "dp")


class TraceError(ValueError):
    """A trace is malformed or cannot be safely aligned."""


@dataclass(frozen=True)
class Alignment:
    """A constant record offset derived solely from phase observations."""

    behavioral_index: int
    chip_index: int
    records: int

    @property
    def chip_minus_behavioral(self) -> int:
        return self.chip_index - self.behavioral_index


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceError(f"line {line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise TraceError(f"line {line_number}: record must be an object")
        records.append(value)
    if not records:
        raise TraceError("trace has no records")
    return records


def _require_mapping(value: Any, *, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TraceError(f"{location}: expected object")
    return value


def behavioral_phase(record: dict[str, Any], *, index: int) -> int:
    behavioral = _require_mapping(record.get("behavioral"), location=f"record {index}.behavioral")
    phase = behavioral.get("phase")
    if type(phase) is not int or phase not in (0, 1, 2):
        raise TraceError(f"record {index}.behavioral.phase: expected 0, 1, or 2; got {phase!r}")
    return phase


def chip_phase(record: dict[str, Any], *, index: int) -> int:
    chip = _require_mapping(record.get("chip"), location=f"record {index}.chip")
    phase = chip.get("phase")
    if phase not in CHIP_PHASE:
        raise TraceError(
            f"record {index}.chip.phase: expected one-hot 001, 010, or 100; got {phase!r}"
        )
    return CHIP_PHASE[phase]


def validate_schema_and_sequences(records: list[dict[str, Any]]) -> tuple[list[int], list[int], list[int]]:
    behavioral_raw: list[int] = []
    behavioral_canonical: list[int] = []
    chip: list[int] = []
    previous_cycle: int | None = None
    for index, record in enumerate(records):
        if record.get("schema") != SCHEMA:
            raise TraceError(f"record {index}.schema: expected {SCHEMA!r}; got {record.get('schema')!r}")
        cycle = record.get("cycle")
        if type(cycle) is not int or cycle < 0:
            raise TraceError(f"record {index}.cycle: expected non-negative integer; got {cycle!r}")
        if previous_cycle is not None and cycle != previous_cycle + 1:
            raise TraceError(f"record {index}.cycle: expected {previous_cycle + 1}, got {cycle}")
        previous_cycle = cycle
        raw_phase = behavioral_phase(record, index=index)
        behavioral_raw.append(raw_phase)
        behavioral_canonical.append(BEHAVIORAL_RAW_TO_CANONICAL[raw_phase])
        chip.append(chip_phase(record, index=index))

    for name, phases in (("behavioral raw", behavioral_raw), ("behavioral canonical", behavioral_canonical), ("chip", chip)):
        for index in range(1, len(phases)):
            expected = (phases[index - 1] + 1) % 3
            if phases[index] != expected:
                raise TraceError(
                    f"record {index}.{name}.phase: expected {PHASE_NAMES[expected]} after "
                    f"{PHASE_NAMES[phases[index - 1]]}; got {PHASE_NAMES[phases[index]]}"
                )
    for index, (behavioral, structural) in enumerate(zip(behavioral_canonical, chip)):
        if behavioral != structural:
            raise TraceError(
                f"record {index}: canonical behavioral phase {PHASE_NAMES[behavioral]} does not match chip phase {PHASE_NAMES[structural]}"
            )
    return behavioral_raw, behavioral_canonical, chip


def find_alignment(behavioral: list[int], chip: list[int]) -> Alignment:
    """Find the maximal constant record offset with matching phase samples.

    A three-state cycle naturally permits shorter offsets separated by three
    records.  The maximal overlap is the only useful alignment for comparing
    the complete trace; a tie at that maximal length is genuinely ambiguous.
    """
    candidates: list[Alignment] = []
    for offset in range(-(len(behavioral) - 1), len(chip)):
        pairs = [
            (behavior_index, behavior_index + offset)
            for behavior_index in range(len(behavioral))
            if 0 <= behavior_index + offset < len(chip)
        ]
        if len(pairs) < 2:
            continue
        if all(behavioral[left] == chip[right] for left, right in pairs):
            candidates.append(Alignment(pairs[0][0], pairs[0][1], len(pairs)))
    if not candidates:
        raise TraceError("phase alignment is absent")
    max_records = max(item.records for item in candidates)
    best = [item for item in candidates if item.records == max_records]
    if len(best) != 1:
        detail = ", ".join(str(item.chip_minus_behavioral) for item in best)
        raise TraceError(f"phase alignment is ambiguous or absent; matching offsets: {detail}")
    return best[0]


def compare_shared_state(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for behavioral_index, record in enumerate(records):
        chip_index = behavioral_index
        behavioral = _require_mapping(record["behavioral"], location=f"record {behavioral_index}.behavioral")
        chip = _require_mapping(records[chip_index]["chip"], location=f"record {chip_index}.chip")
        differences = {
            field: {"behavioral": behavioral.get(field), "chip": chip.get(field)}
            for field in SAME_CYCLE_SHARED_STATE_FIELDS
            if behavioral.get(field) != chip.get(field)
        }
        if differences:
            mismatches.append(
                {
                    "behavioral_record": behavioral_index,
                    "chip_record": chip_index,
                    "phase": PHASE_NAMES[behavioral_phase(record, index=behavioral_index)],
                    "behavioral_cycle": record["cycle"],
                    "chip_cycle": records[chip_index]["cycle"],
                    "differences": differences,
                }
            )
    return mismatches


def report(records: list[dict[str, Any]]) -> dict[str, Any]:
    behavioral_raw, _behavioral_canonical, chip = validate_schema_and_sequences(records)
    alignment = find_alignment(behavioral_raw, chip)
    mismatches = compare_shared_state(records)
    return {
        "schema": "rv8gr.phase-trace-comparison@1",
        "records": len(records),
        "alignment": {
            "raw_behavioral_to_chip_record_offset": alignment.chip_minus_behavioral,
            "finding": "raw behavioral state is one record ahead of chip phase; raw T1/T2/T0 maps to canonical T0/T1/T2 at the same settled cycle",
            "raw_phase_alignment_records": alignment.records,
            "comparison": "canonical same-cycle phase and stable state fields",
        },
        "raw_behavioral_phase_map": {str(key): PHASE_NAMES[value] for key, value in BEHAVIORAL_RAW_TO_CANONICAL.items()},
        "shared_fields": list(SAME_CYCLE_SHARED_STATE_FIELDS),
        "deferred_raw_state_fields": ["pc", "ac", "z", "pg"],
        "first_mismatch": mismatches[0] if mismatches else None,
        "mismatch_count": len(mismatches),
        "result": "PASS" if not mismatches else "FAIL",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="JSONL trace emitted by tb_rv8gr_dual_trace_jsonl")
    parser.add_argument("--report", type=Path, help="write machine-readable report (for example under /tmp)")
    args = parser.parse_args(argv)
    try:
        result = report(load_records(args.trace))
    except TraceError as exc:
        result = {"schema": "rv8gr.phase-trace-comparison@1", "result": "INVALID", "error": str(exc)}
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
