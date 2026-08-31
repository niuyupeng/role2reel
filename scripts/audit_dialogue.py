#!/usr/bin/env python3
"""Flag review-worthy dialogue patterns without pretending to judge artistic quality."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


EXPOSITION_PATTERNS = {
    "as-you-know": re.compile(r"众所周知|你(?:也)?知道的|你应该知道|as you (?:already )?know", re.I),
    "let-me-explain": re.compile(r"让我(?:来)?解释|简单来说|换句话说|let me explain", re.I),
    "private-analysis-spill": re.compile(
        r"我的(?:判断|推断|立场|第一反应|社交目标)是|这(?:就)?(?:说明|意味着).{0,16}(?:所以|因此)|"
        r"my (?:judgment|inference|stance|first impulse|social objective) is",
        re.I,
    ),
    "backstory-recital": re.compile(
        r"我之所以.{1,30}是因为.{1,30}(?:所以|才)|自从.{1,30}以后[，,]?.{0,20}(?:我就|所以我)|"
        r"the reason I .{1,40} is because",
        re.I,
    ),
}
GENERIC_PATTERNS = {
    "generic-summary": re.compile(r"总而言之|综上所述|in conclusion", re.I),
    "generic-emphasis": re.compile(r"值得注意的是|不可否认的是|在这个过程中", re.I),
    "generic-empathy": re.compile(r"我(?:完全)?理解你的感受|我能理解你现在的心情|I (?:completely )?understand how you feel", re.I),
}

SCENE_HEADING_PATTERN = re.compile(
    r"^(?:(?:INT|EXT)(?:\.?\s*[/\-]\s*\.?(?:INT|EXT))?|EST|I\s*[/\-]\s*E)\.?(?=\s|$)",
    re.I,
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    line: int
    message: str


def normalized_line(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def is_scene_heading(line: str) -> bool:
    """Return whether a stripped Fountain line is a scene heading."""
    if line.startswith(".") and not line.startswith(".."):
        return True
    if re.match(r"^(?:内景|外景|内\s*[/\-]\s*外景|外\s*[/\-]\s*内景)", line):
        return True
    return bool(SCENE_HEADING_PATTERN.match(line))


def is_character_cue(line: str) -> bool:
    """Recognize ordinary and forced Fountain character cues."""
    forced = line.startswith("@")
    candidate = line[1:].strip() if forced else line
    candidate = re.sub(r"\s*\^\s*$", "", candidate).strip()
    if not candidate or len(candidate) > 40:
        return False
    if re.search(r"[。！？!?，,；;：:]$", candidate):
        return False
    if forced:
        return not bool(re.search(r"[:：\r\n]", candidate))
    return bool(re.fullmatch(r"[A-Z0-9 _.'()\-\u3400-\u9fff]+", candidate))


def likely_dialogue_lines(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    result: list[tuple[int, str]] = []
    fountain_cue = False
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            fountain_cue = False
            continue
        inline = re.match(r"^[^:：]{1,20}[:：]\s*(.+)$", line)
        if inline:
            result.append((number, inline.group(1).strip()))
            fountain_cue = False
            continue
        if fountain_cue:
            result.append((number, line))
            continue
        fountain_cue = not is_scene_heading(line) and is_character_cue(line)
    return result


def audit_text(text: str, max_chars: int = 60) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, int] = {}
    dialogue = likely_dialogue_lines(text)
    for line_number, line in dialogue:
        for code, pattern in {**EXPOSITION_PATTERNS, **GENERIC_PATTERNS}.items():
            if pattern.search(line):
                findings.append(Finding(code, "warning", line_number, f"Review phrasing: {line}"))
        compact_length = len(re.sub(r"\s+", "", line))
        if compact_length > max_chars:
            findings.append(
                Finding("long-line", "warning", line_number, f"Dialogue has {compact_length} non-space characters; test actor breath.")
            )
        normalized = normalized_line(line)
        if len(normalized) >= 4:
            if normalized in seen:
                findings.append(
                    Finding("duplicate-line", "warning", line_number, f"Duplicates dialogue on line {seen[normalized]}.")
                )
            else:
                seen[normalized] = line_number
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--max-chars", type=int, default=60)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = args.file.read_text(encoding="utf-8")
    findings = audit_text(text, args.max_chars)
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} line {item.line}: {item.message}")
        print(f"Findings: {len(findings)} (review warnings, not automatic failures)")
    else:
        print("No configured dialogue warnings found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
