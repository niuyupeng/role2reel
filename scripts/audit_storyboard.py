#!/usr/bin/env python3
"""Validate structural and timeline invariants in storyboard CSV, JSON, or YAML files."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # YAML input remains optional for CSV/JSON users.
    yaml = None


REQUIRED_FIELD_GROUPS = {
    "shot_id": ("shot_id",),
    "start_s": ("start_s",),
    "end_s": ("end_s",),
    "duty": ("duty",),
    "visual": ("visual", "visual_event"),
    "framing": ("framing", "framing_and_angle"),
    "movement": ("movement", "camera_behavior", "movement_motive"),
    "performance": ("performance", "performance_cause", "blocking"),
    "dialogue_sound": ("dialogue_sound",),
    "continuity": ("continuity",),
}
GENERIC_DUTIES = {"cinematic", "more cinematic", "增强电影感", "更有冲击力", "更高级"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    shot_id: str
    message: str


def _extract_rows(payload: Any, format_name: str) -> list[dict[str, Any]]:
    rows = payload.get("shots") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
        raise ValueError(f"{format_name} must be an array of shots or an object with a shots array")
    return rows


def load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        return _extract_rows(json.loads(path.read_text(encoding="utf-8")), "JSON")
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc
        return _extract_rows(payload, "YAML")
    raise ValueError("Supported storyboard formats are .csv, .json, .yaml, and .yml")


def _has_value(row: dict[str, Any], aliases: tuple[str, ...]) -> bool:
    for alias in aliases:
        if alias not in row or row[alias] is None:
            continue
        value = row[alias]
        if not isinstance(value, str) or value.strip():
            return True
    return False


def audit_rows(
    rows: list[dict[str, Any]],
    tolerance: float = 0.001,
    expected_duration: Optional[float] = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not math.isfinite(tolerance) or tolerance < 0:
        return [Finding("invalid-tolerance", "error", "storyboard", "Tolerance must be finite and nonnegative.")]
    if expected_duration is not None and (not math.isfinite(expected_duration) or expected_duration < 0):
        return [Finding("invalid-expected-duration", "error", "storyboard", "Expected duration must be finite and nonnegative.")]
    if not rows:
        return [Finding("no-shots", "error", "storyboard", "Storyboard contains no shots.")]

    seen: set[str] = set()
    parsed: list[tuple[str, float, float]] = []
    for index, row in enumerate(rows, start=1):
        shot_id = str(row.get("shot_id") or f"row-{index}").strip()
        for logical_name, aliases in REQUIRED_FIELD_GROUPS.items():
            if not _has_value(row, aliases):
                accepted = ", ".join(aliases)
                findings.append(Finding("missing-field", "error", shot_id, f"Missing required field: {logical_name} ({accepted})"))
        if shot_id in seen:
            findings.append(Finding("duplicate-shot-id", "error", shot_id, "Shot ID is not unique."))
        seen.add(shot_id)
        try:
            start = float(row.get("start_s"))
            end = float(row.get("end_s"))
        except (TypeError, ValueError):
            findings.append(Finding("invalid-time", "error", shot_id, "start_s and end_s must be numeric."))
            continue
        if not math.isfinite(start) or not math.isfinite(end):
            findings.append(Finding("invalid-time", "error", shot_id, "start_s and end_s must be finite."))
            continue
        if start < 0:
            findings.append(Finding("negative-time", "error", shot_id, "start_s cannot be negative."))
        if end <= start:
            findings.append(Finding("nonpositive-duration", "error", shot_id, "end_s must be greater than start_s."))
        parsed.append((shot_id, start, end))
        duty = str(row.get("duty") or "").strip().casefold()
        if duty in GENERIC_DUTIES:
            findings.append(Finding("generic-duty", "warning", shot_id, "Duty does not explain the audience need or state change."))

    exact_mode = expected_duration is not None
    if parsed and abs(parsed[0][1]) > tolerance:
        severity = "error" if exact_mode else "warning"
        findings.append(Finding("nonzero-start", severity, parsed[0][0], f"Timeline begins at {parsed[0][1]:g}s, not 0s."))
    for previous, current in zip(parsed, parsed[1:]):
        prev_id, _, prev_end = previous
        current_id, current_start, _ = current
        difference = current_start - prev_end
        if difference > tolerance:
            severity = "error" if exact_mode else "warning"
            findings.append(Finding("timeline-gap", severity, current_id, f"Gap of {difference:g}s after {prev_id}."))
        elif difference < -tolerance:
            findings.append(Finding("timeline-overlap", "error", current_id, f"Overlap of {-difference:g}s with {prev_id}."))
    if exact_mode and len(parsed) == len(rows):
        difference = parsed[-1][2] - expected_duration
        if abs(difference) > tolerance:
            findings.append(
                Finding(
                    "duration-mismatch",
                    "error",
                    parsed[-1][0],
                    f"Timeline ends at {parsed[-1][2]:g}s; expected {expected_duration:g}s.",
                )
            )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.001)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows(args.file)
        findings = audit_rows(rows, args.tolerance, args.expected_duration)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR input: {exc}")
        return 2
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.shot_id}: {item.message}")
        errors = sum(item.severity == "error" for item in findings)
        warnings = len(findings) - errors
        print(f"Errors: {errors}; warnings: {warnings}")
    else:
        print(f"Storyboard structure valid: {len(rows)} shot(s), no configured warnings.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
