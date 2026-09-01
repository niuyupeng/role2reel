#!/usr/bin/env python3
"""Audit the mechanical contract of paste-ready shot prompt blocks."""

from __future__ import annotations

import argparse
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


HEADER_RE = re.compile(r"(?m)^shot(\d+)｜\s*$")
TIMECODE_RE = re.compile(
    r"^【(?P<start>\d+:\d+(?:\.\d+)?|\d+(?:\.\d+)?)-(?P<end>\d+:\d+(?:\.\d+)?|\d+(?:\.\d+)?)】:")
FIELD_ORDER = ("景别与运镜：", "拍摄方式：", "画面与动线：")
UNFINISHED_RE = re.compile(r"(?:\[(?:TODO|PLACEHOLDER)[^\]]*\]|<local_number>|<shot_scale)", re.I)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    shot: str
    message: str


def _blocks(text: str) -> list[tuple[str, str]]:
    matches = list(HEADER_RE.finditer(text))
    return [(match.group(0).strip(), text[match.start() : matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip()) for i, match in enumerate(matches)]


def _number(value: str) -> float:
    if ":" in value:
        minutes, seconds = value.split(":", 1)
        return float(minutes) * 60.0 + float(seconds)
    return float(value)


def audit_text(
    text: str,
    *,
    expected_duration: float | None = None,
    one_based: bool = True,
    allow_offset: bool = False,
    allow_restarts: bool = False,
    tolerance: float = 0.051,
) -> list[Finding]:
    """Return structural findings; semantic, artistic and provider checks remain manual."""
    findings: list[Finding] = []
    blocks = _blocks(text)
    if not blocks:
        return [Finding("no-shot-blocks", "error", "document", "No shotN｜ blocks were found.")]

    seen_numbers: set[int] = set()
    previous_number: int | None = None
    for header, block in blocks:
        number = int(re.search(r"\d+", header).group(0))
        shot = f"shot{number}"
        if allow_restarts and previous_number is not None and number <= previous_number:
            seen_numbers.clear()
            previous_number = None
        if number in seen_numbers:
            findings.append(Finding("duplicate-shot-label", "error", shot, "The local shot label is repeated."))
        seen_numbers.add(number)
        if previous_number is not None and number <= previous_number:
            findings.append(Finding("shot-order", "error", shot, "Shot labels must increase within a text export."))
        previous_number = number

        positions: list[int] = []
        for field in FIELD_ORDER:
            position = block.find(field)
            positions.append(position)
            if position < 0:
                findings.append(Finding("missing-field", "error", shot, f"Missing required field {field}"))
        if all(position >= 0 for position in positions) and positions != sorted(positions):
            findings.append(Finding("field-order", "error", shot, "The three required fields are out of order."))

        if UNFINISHED_RE.search(block):
            findings.append(Finding("unfinished-text", "error", shot, "The block contains an unfinished placeholder."))

        parsed: list[tuple[float, float]] = []
        for line in block.splitlines():
            match = TIMECODE_RE.match(line.strip())
            if not match:
                continue
            start = _number(match.group("start"))
            end = _number(match.group("end"))
            if end <= start:
                findings.append(Finding("nonpositive-segment", "error", shot, f"Time segment ends at {end:g}s but starts at {start:g}s."))
            parsed.append((start, end))
        if not parsed:
            findings.append(Finding("missing-timecode", "error", shot, "At least one 【start-end】: time line is required."))
            continue
        origin = 1.0 if one_based else 0.0
        if not allow_offset and abs(parsed[0][0] - origin) > tolerance:
            findings.append(Finding("wrong-time-origin", "error", shot, f"First time line starts at {parsed[0][0]:g}s; expected {origin:g}s."))
        for (previous_start, previous_end), (start, end) in zip(parsed, parsed[1:]):
            difference = start - previous_end
            if difference > tolerance:
                findings.append(Finding("timeline-gap", "error", shot, f"Time-code gap of {difference:g}s inside the block."))
            elif difference < -tolerance:
                findings.append(Finding("timeline-overlap", "error", shot, f"Time-code overlap of {-difference:g}s inside the block."))
        if expected_duration is not None:
            expected_end = origin + expected_duration
            if abs(parsed[-1][1] - expected_end) > tolerance:
                findings.append(Finding("duration-mismatch", "error", shot, f"Block ends at {parsed[-1][1]:g}s; expected {expected_end:g}s."))
    return findings


def audit_file(path: Path, **kwargs: object) -> list[Finding]:
    return audit_text(path.read_text(encoding="utf-8"), **kwargs)


def _print_findings(findings: Iterable[Finding], as_json: bool) -> None:
    values = list(findings)
    if as_json:
        import json

        print(json.dumps([asdict(item) for item in values], ensure_ascii=False, indent=2))
    elif values:
        for item in values:
            print(f"{item.severity.upper()} {item.code} {item.shot}: {item.message}")
        errors = sum(item.severity == "error" for item in values)
        print(f"Errors: {errors}; findings: {len(values)}")
    else:
        print("Paste-ready shot blocks are structurally valid. Meaning, playability, and provider review remain manual.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--zero-based", action="store_true", help="Expect the first display time to start at 00:00.")
    parser.add_argument("--allow-offset", action="store_true", help="Preserve source-segment timecodes whose first line is not the display origin.")
    parser.add_argument("--allow-restarts", action="store_true", help="Allow local shot labels to restart at each concatenated generation segment.")
    parser.add_argument("--tolerance", type=float, default=0.051)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        findings = audit_file(
            args.file,
            expected_duration=args.expected_duration,
            one_based=not args.zero_based,
            allow_offset=args.allow_offset,
            allow_restarts=args.allow_restarts,
            tolerance=args.tolerance,
        )
    except (OSError, UnicodeError) as exc:
        print(f"ERROR input: {exc}")
        return 2
    _print_findings(findings, args.as_json)
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
