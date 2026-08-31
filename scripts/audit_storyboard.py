#!/usr/bin/env python3
"""Validate storyboard timing, upstream bindings, shot states, and visual references.

Schema-v1 row files keep their legacy structural contract. Schema-v2 YAML/JSON files
add exact upstream revision bindings, separate dialogue and sound, stable visual-asset
references, and state handoffs. Modern boards must be checked against the actual
meaning, scene, beat, and visual-bible files. The audit cannot judge shot quality or
meaning fidelity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

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
    "dialogue_sound": ("dialogue_sound", "dialogue_mode", "dialogue", "sound"),
    "continuity": ("continuity",),
}
CONCISE_FIELD_GROUPS = {
    key: REQUIRED_FIELD_GROUPS[key]
    for key in ("shot_id", "start_s", "end_s", "duty", "visual", "dialogue_sound")
}
GENERIC_DUTIES = {"cinematic", "more cinematic", "增强电影感", "更有冲击力", "更高级"}
HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
REQUIRED_SOURCE_ROLES = {"meaning", "scene", "beats"}
DIALOGUE_MODES = {"spoken", "nonverbal", "silent"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    shot_id: str
    message: str


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_has_content(item) for item in value)
    return True


def _valid_revision(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, int):
        return value > 0
    return isinstance(value, str) and bool(value.strip())


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH_PATTERN.fullmatch(value.strip()))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _extract_rows(payload: Any, format_name: str) -> list[dict[str, Any]]:
    rows = payload.get("shots") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
        raise ValueError(f"{format_name} must be an array of shots or an object with a shots array")
    return rows


def load_document(path: Path) -> Any:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc
    raise ValueError("Supported storyboard formats are .csv, .json, .yaml, and .yml")


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_document(path)
    return _extract_rows(payload, path.suffix.lstrip(".").upper() or "input")


def load_bound_document(path: Path) -> Any:
    """Load a bound structured document or Markdown YAML frontmatter."""
    if path.suffix.casefold() != ".md":
        return load_document(path)
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Bound Markdown source requires YAML frontmatter: {path}")
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
    if closing is None:
        raise ValueError(f"Unterminated YAML frontmatter in bound source: {path}")
    if yaml is None:
        raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
    try:
        payload = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid bound Markdown frontmatter: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Bound Markdown frontmatter must be a mapping: {path}")
    return payload


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
    *,
    required_field_groups: Optional[dict[str, tuple[str, ...]]] = None,
) -> list[Finding]:
    """Audit the legacy flat row contract; aliases keep old CSV/JSON/YAML valid."""
    findings: list[Finding] = []
    if not math.isfinite(tolerance) or tolerance < 0:
        return [Finding("invalid-tolerance", "error", "storyboard", "Tolerance must be finite and nonnegative.")]
    if expected_duration is not None and (not math.isfinite(expected_duration) or expected_duration < 0):
        return [Finding("invalid-expected-duration", "error", "storyboard", "Expected duration must be finite and nonnegative.")]
    if not rows:
        return [Finding("no-shots", "error", "storyboard", "Storyboard contains no shots.")]

    groups = required_field_groups or REQUIRED_FIELD_GROUPS
    seen: set[str] = set()
    parsed: list[tuple[str, float, float]] = []
    for index, row in enumerate(rows, start=1):
        shot_id = str(row.get("shot_id") or f"row-{index}").strip()
        for logical_name, aliases in groups.items():
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


def _audit_binding(binding: Any, location: str, findings: list[Finding], *, id_field: str = "source_id") -> None:
    if not isinstance(binding, dict):
        findings.append(Finding("invalid-binding", "error", location, "Binding must be a mapping."))
        return
    if not _has_content(binding.get(id_field)):
        findings.append(Finding("missing-binding-id", "error", location, f"Binding requires {id_field}."))
    if not _valid_revision(binding.get("revision")):
        findings.append(Finding("invalid-binding-revision", "error", location, "Binding revision must be stable and non-empty."))
    if not _is_hash(binding.get("sha256")):
        findings.append(Finding("invalid-binding-hash", "error", location, "Binding requires a 64-hex SHA-256."))


def _bound_source_identity(role: str, document: Any) -> tuple[Any, Any]:
    if not isinstance(document, dict):
        return None, None
    if role == "meaning":
        ledger = document.get("ledger")
        if isinstance(ledger, dict):
            return ledger.get("ledger_id"), ledger.get("revision")
        return (
            document.get("draft_id") or document.get("meaning_id") or document.get("source_id") or document.get("id"),
            document.get("draft_revision") or document.get("revision"),
        )
    if role == "scene":
        scene = document.get("scene")
        if isinstance(scene, dict):
            return scene.get("id"), scene.get("revision")
        return document.get("scene_id") or document.get("id"), document.get("revision")
    if role == "beats":
        return document.get("beat_map_id") or document.get("beats_id") or document.get("id"), document.get("revision")
    return None, None


def _audit_actual_source_binding(
    role: str,
    binding: Mapping[str, Any],
    document: Any,
    actual_sha256: Optional[str],
    findings: list[Finding],
) -> None:
    location = f"source_bindings.{role}"
    if document is None:
        findings.append(
            Finding(
                "missing-bound-source-document",
                "error",
                location,
                f"Supply the actual {role} document; a hash-shaped string is not sufficient.",
            )
        )
        return
    actual_id, actual_revision = _bound_source_identity(role, document)
    if not _has_content(actual_id) or not _valid_revision(actual_revision):
        findings.append(
            Finding(
                "invalid-bound-source-identity",
                "error",
                location,
                f"Supplied {role} document has no supported stable ID and revision.",
            )
        )
    else:
        if binding.get("source_id") != actual_id:
            findings.append(Finding("source-id-mismatch", "error", location, f"Bound {role} source_id does not match the supplied document."))
        if str(binding.get("revision")) != str(actual_revision):
            findings.append(Finding("source-revision-mismatch", "error", location, f"Bound {role} revision does not match the supplied document."))
    if not _is_hash(actual_sha256):
        findings.append(Finding("missing-bound-source-hash", "error", location, f"Actual SHA-256 for the supplied {role} file is required."))
    elif _is_hash(binding.get("sha256")) and str(binding["sha256"]).casefold() != str(actual_sha256).casefold():
        findings.append(Finding("source-hash-mismatch", "error", location, f"Bound {role} hash does not match the supplied file."))


def _visual_asset_index(visual_bible: Any, findings: list[Finding]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(visual_bible, dict):
        findings.append(Finding("invalid-visual-bible", "error", "visual_bible", "Visual bible must be a mapping."))
        return {}
    assets = visual_bible.get("assets")
    if not isinstance(assets, list):
        findings.append(Finding("invalid-visual-assets", "error", "visual_bible", "Visual bible assets must be a list."))
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for position, item in enumerate(assets, start=1):
        location = f"visual_bible.assets[{position}]"
        if not isinstance(item, dict):
            findings.append(Finding("invalid-visual-asset", "error", location, "Visual asset must be a mapping."))
            continue
        asset_id = item.get("asset_id")
        revision = item.get("revision")
        if not _has_content(asset_id) or not _valid_revision(revision):
            findings.append(Finding("invalid-visual-asset-ref", "error", location, "Visual asset requires asset_id and revision."))
            continue
        key = (str(asset_id).strip(), str(revision).strip())
        if key in index:
            findings.append(Finding("duplicate-visual-asset-revision", "error", location, f"Duplicate asset revision: {key[0]}@{key[1]}."))
        index[key] = item
    return index


def audit_document(
    payload: Any,
    tolerance: float = 0.001,
    expected_duration: Optional[float] = None,
    *,
    bound_sources: Optional[Mapping[str, Any]] = None,
    bound_source_sha256: Optional[Mapping[str, str]] = None,
    visual_bible: Any = None,
    visual_bible_sha256: Optional[str] = None,
) -> list[Finding]:
    """Audit a storyboard document, applying schema-v2 contracts when declared."""
    rows = _extract_rows(payload, "storyboard")
    if not isinstance(payload, dict):
        return audit_rows(rows, tolerance, expected_duration)
    modern_contract = payload.get("schema_version") == 2 or (
        payload.get("schema_version", 1) == 1 and payload.get("contract_version") == 2
    )
    if payload.get("schema_version", 1) == 1 and not modern_contract:
        return audit_rows(rows, tolerance, expected_duration)
    if not modern_contract:
        return [Finding("unsupported-schema-version", "error", "storyboard", "Supported schema versions are 1 and 2.")]

    findings: list[Finding] = []
    depth = payload.get("delivery_depth")
    if depth not in {"concise", "professional"}:
        findings.append(Finding("invalid-delivery-depth", "error", "storyboard", "delivery_depth must be concise or professional."))
    groups = REQUIRED_FIELD_GROUPS if depth == "professional" else CONCISE_FIELD_GROUPS

    declared_duration = payload.get("total_duration_s")
    if isinstance(declared_duration, bool) or not isinstance(declared_duration, (int, float)) or not math.isfinite(float(declared_duration)) or float(declared_duration) <= 0:
        findings.append(Finding("invalid-total-duration", "error", "storyboard", "total_duration_s must be a positive finite number."))
        timeline_duration = expected_duration
    else:
        timeline_duration = float(declared_duration)
        if expected_duration is not None and abs(timeline_duration - expected_duration) > tolerance:
            findings.append(Finding("declared-duration-conflict", "error", "storyboard", "total_duration_s conflicts with --expected-duration."))
            timeline_duration = expected_duration
    findings.extend(audit_rows(rows, tolerance, timeline_duration, required_field_groups=groups))

    if not _has_content(payload.get("storyboard_id")):
        findings.append(Finding("missing-storyboard-id", "error", "storyboard", "storyboard_id is required."))
    if not _valid_revision(payload.get("revision")):
        findings.append(Finding("invalid-storyboard-revision", "error", "storyboard", "revision must be stable and non-empty."))
    if not _has_content(payload.get("scene_id")):
        findings.append(Finding("missing-scene-id", "error", "storyboard", "scene_id is required."))

    bindings = payload.get("source_bindings")
    binding_by_role: dict[str, Mapping[str, Any]] = {}
    seen_roles: set[str] = set()
    if not isinstance(bindings, list):
        findings.append(Finding("invalid-source-bindings", "error", "source_bindings", "source_bindings must be a list."))
    else:
        for position, binding in enumerate(bindings, start=1):
            location = f"source_bindings[{position}]"
            if not isinstance(binding, dict):
                findings.append(Finding("invalid-binding", "error", location, "Binding must be a mapping."))
                continue
            role = binding.get("role")
            if role not in REQUIRED_SOURCE_ROLES:
                findings.append(Finding("invalid-source-role", "error", location, f"role must be one of {sorted(REQUIRED_SOURCE_ROLES)}."))
            elif role in seen_roles:
                findings.append(Finding("duplicate-source-role", "error", location, f"Duplicate source role: {role}."))
            else:
                seen_roles.add(role)
                binding_by_role[role] = binding
            _audit_binding(binding, location, findings)
        for role in sorted(REQUIRED_SOURCE_ROLES - seen_roles):
            findings.append(Finding("missing-source-role", "error", "source_bindings", f"Missing upstream source role: {role}."))

    supplied_sources = bound_sources or {}
    supplied_hashes = bound_source_sha256 or {}
    for role in sorted(REQUIRED_SOURCE_ROLES):
        binding = binding_by_role.get(role)
        if binding is not None:
            _audit_actual_source_binding(role, binding, supplied_sources.get(role), supplied_hashes.get(role), findings)

    visual_binding = payload.get("visual_bible_binding")
    _audit_binding(visual_binding, "visual_bible_binding", findings, id_field="visual_bible_id")
    visual_index: dict[tuple[str, str], dict[str, Any]] = {}
    if visual_bible is None:
        findings.append(
            Finding(
                "missing-visual-bible-document",
                "error",
                "visual_bible_binding",
                "Supply the actual visual-bible document; a hash-shaped string is not sufficient.",
            )
        )
    else:
        visual_index = _visual_asset_index(visual_bible, findings)
        if isinstance(visual_binding, dict) and isinstance(visual_bible, dict):
            if visual_binding.get("visual_bible_id") != visual_bible.get("visual_bible_id"):
                findings.append(Finding("visual-bible-id-mismatch", "error", "visual_bible_binding", "Bound visual_bible_id does not match supplied visual bible."))
            if str(visual_binding.get("revision")) != str(visual_bible.get("revision")):
                findings.append(Finding("visual-bible-revision-mismatch", "error", "visual_bible_binding", "Bound visual-bible revision does not match supplied visual bible."))
            if visual_bible_sha256 and _is_hash(visual_binding.get("sha256")) and visual_binding["sha256"].casefold() != visual_bible_sha256.casefold():
                findings.append(Finding("visual-bible-hash-mismatch", "error", "visual_bible_binding", "Bound visual-bible hash does not match supplied file."))
            if not _is_hash(visual_bible_sha256):
                findings.append(Finding("missing-visual-bible-hash", "error", "visual_bible_binding", "Actual SHA-256 for the supplied visual-bible file is required."))

    for position, row in enumerate(rows):
        shot_id = str(row.get("shot_id") or f"row-{position + 1}").strip()
        for field in ("state_in", "state_out"):
            if not _has_content(row.get(field)):
                findings.append(Finding(f"missing-{field.replace('_', '-')}", "error", shot_id, f"{field} is required in schema v2."))

        dialogue = row.get("dialogue")
        if not isinstance(dialogue, dict):
            findings.append(Finding("invalid-dialogue-contract", "error", shot_id, "dialogue must be a mapping separate from sound."))
        else:
            mode = dialogue.get("mode")
            if mode not in DIALOGUE_MODES:
                findings.append(Finding("invalid-dialogue-mode", "error", shot_id, f"dialogue.mode must be one of {sorted(DIALOGUE_MODES)}."))
            lines = dialogue.get("lines")
            if not isinstance(lines, list):
                findings.append(Finding("invalid-dialogue-lines", "error", shot_id, "dialogue.lines must be a list."))
            elif mode == "spoken":
                if not lines:
                    findings.append(Finding("spoken-without-line", "error", shot_id, "spoken mode requires at least one owned line."))
                for line_number, line in enumerate(lines, start=1):
                    if not isinstance(line, dict) or not _has_content(line.get("speaker_id")) or not _has_content(line.get("text")):
                        findings.append(Finding("invalid-spoken-line", "error", shot_id, f"Spoken line {line_number} requires speaker_id and text."))
            elif mode in {"nonverbal", "silent"} and _has_content(lines):
                findings.append(Finding("unspoken-mode-has-line", "error", shot_id, f"{mode} mode cannot contain spoken lines."))

        sound = row.get("sound")
        if not isinstance(sound, dict):
            findings.append(Finding("invalid-sound-contract", "error", shot_id, "sound must be a mapping separate from dialogue."))
        else:
            acoustic_silence = sound.get("acoustic_silence")
            if type(acoustic_silence) is not bool:
                findings.append(Finding("missing-sound-decision", "error", shot_id, "sound.acoustic_silence must be true or false."))
            other_sound = {key: value for key, value in sound.items() if key != "acoustic_silence"}
            if acoustic_silence is False and not _has_content(other_sound):
                findings.append(Finding("empty-sound-contract", "error", shot_id, "Name audible sound or set acoustic_silence: true."))

        asset_refs = row.get("asset_refs")
        if not isinstance(asset_refs, list) or not asset_refs:
            findings.append(Finding("missing-shot-asset-refs", "error", shot_id, "Each schema-v2 shot requires stable asset references."))
        else:
            seen_refs: set[tuple[str, str]] = set()
            for asset_position, reference in enumerate(asset_refs, start=1):
                location = f"{shot_id}.asset_refs[{asset_position}]"
                if not isinstance(reference, dict):
                    findings.append(Finding("invalid-shot-asset-ref", "error", location, "Asset reference must be a mapping."))
                    continue
                asset_id = reference.get("asset_id")
                revision = reference.get("revision")
                if not _has_content(asset_id) or not _valid_revision(revision):
                    findings.append(Finding("invalid-shot-asset-ref", "error", location, "Asset reference requires asset_id and revision."))
                    continue
                key = (str(asset_id).strip(), str(revision).strip())
                if key in seen_refs:
                    findings.append(Finding("duplicate-shot-asset-ref", "error", location, f"Duplicate shot asset reference: {key[0]}@{key[1]}."))
                seen_refs.add(key)
                for field in ("role", "use", "target"):
                    if not _has_content(reference.get(field)):
                        findings.append(Finding("incomplete-shot-asset-ref", "error", location, f"Asset reference requires {field}."))
                if visual_bible is not None and key not in visual_index:
                    findings.append(Finding("unknown-visual-asset-revision", "error", location, f"No visual-bible asset revision {key[0]}@{key[1]}."))

        handoff = row.get("handoff")
        if not isinstance(handoff, dict):
            findings.append(Finding("invalid-handoff", "error", shot_id, "handoff must be a mapping."))
            continue
        if handoff.get("state") != row.get("state_out"):
            findings.append(Finding("handoff-state-mismatch", "error", shot_id, "handoff.state must equal this shot's state_out."))
        expected_next = rows[position + 1].get("shot_id") if position + 1 < len(rows) else None
        if handoff.get("to_shot_id") != expected_next:
            findings.append(Finding("handoff-target-mismatch", "error", shot_id, f"handoff.to_shot_id must be {expected_next!r}."))
        if position + 1 < len(rows) and row.get("state_out") != rows[position + 1].get("state_in"):
            findings.append(Finding("adjacent-state-mismatch", "error", shot_id, "state_out does not match the next shot's state_in."))

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--meaning", type=Path, help="Actual meaning-ledger or approved-draft source")
    parser.add_argument("--scene", type=Path, help="Actual scene-contract source")
    parser.add_argument("--beats", type=Path, help="Actual beat-map source")
    parser.add_argument("--visual-bible", type=Path, help="Actual visual-bible YAML/JSON")
    parser.add_argument("--tolerance", type=float, default=0.001)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_document(args.file)
        source_paths = {"meaning": args.meaning, "scene": args.scene, "beats": args.beats}
        supplied_sources = {
            role: load_bound_document(path)
            for role, path in source_paths.items()
            if path is not None
        }
        supplied_source_hashes = {
            role: _file_sha256(path)
            for role, path in source_paths.items()
            if path is not None
        }
        visual_bible = load_document(args.visual_bible) if args.visual_bible else None
        visual_hash = _file_sha256(args.visual_bible) if args.visual_bible else None
        findings = audit_document(
            payload,
            args.tolerance,
            args.expected_duration,
            bound_sources=supplied_sources,
            bound_source_sha256=supplied_source_hashes,
            visual_bible=visual_bible,
            visual_bible_sha256=visual_hash,
        )
        rows = _extract_rows(payload, "storyboard")
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
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
        print(f"Storyboard structure valid: {len(rows)} shot(s). Artistic and meaning review remains manual.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
