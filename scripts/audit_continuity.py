#!/usr/bin/env python3
"""Audit continuity source bindings, global locks, state changes, and shot handoffs.

The auditor reports structural conflicts only. It cannot determine whether a visual
choice is attractive, whether an actor is recognizably the same person, or whether
an authorized story change is dramatically sound.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - JSON remains usable without PyYAML.
    yaml = None


HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
LOCK_CATEGORIES = ("identity", "wardrobe", "space", "voice")


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    location: str
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_document(path: Path) -> dict[str, Any]:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc
    else:
        raise ValueError("Supported continuity formats are .json, .yaml, and .yml")
    if not isinstance(payload, dict):
        raise ValueError("Continuity document must be a mapping")
    return payload


def _error(findings: list[Finding], code: str, location: str, message: str) -> None:
    findings.append(Finding(code, "error", location, message))


def _audit_binding(binding: Any, location: str, findings: list[Finding]) -> None:
    if not isinstance(binding, dict):
        _error(findings, "invalid-source-binding", location, "Source binding must be a mapping.")
        return
    if not _has_content(binding.get("artifact_id")):
        _error(findings, "missing-source-id", location, "Source binding requires artifact_id.")
    if not _valid_revision(binding.get("revision")):
        _error(findings, "invalid-source-revision", location, "Source binding requires a stable revision.")
    if not _is_hash(binding.get("sha256")):
        _error(findings, "invalid-source-hash", location, "Source binding requires a 64-hex SHA-256.")


def _visual_index(visual_bible: Any, findings: list[Finding]) -> set[tuple[str, str]]:
    if not isinstance(visual_bible, dict) or not isinstance(visual_bible.get("assets"), list):
        _error(findings, "invalid-visual-bible", "visual_bible", "Visual bible must contain an assets list.")
        return set()
    result: set[tuple[str, str]] = set()
    for index, asset in enumerate(visual_bible["assets"], start=1):
        location = f"visual_bible.assets[{index}]"
        if not isinstance(asset, dict) or not _has_content(asset.get("asset_id")) or not _valid_revision(asset.get("revision")):
            _error(findings, "invalid-visual-asset", location, "Visual asset requires asset_id and revision.")
            continue
        key = (str(asset["asset_id"]).strip(), str(asset["revision"]).strip())
        if key in result:
            _error(findings, "duplicate-visual-asset-revision", location, f"Duplicate visual asset revision {key[0]}@{key[1]}.")
        result.add(key)
    return result


def _legacy_audit(payload: dict[str, Any]) -> list[Finding]:
    """Accept the v1 shape while still rejecting malformed container types."""
    findings: list[Finding] = []
    if not isinstance(payload.get("global_locks"), dict):
        _error(findings, "invalid-global-locks", "global_locks", "Legacy global_locks must be a mapping.")
    if not isinstance(payload.get("state_changes"), list):
        _error(findings, "invalid-state-changes", "state_changes", "Legacy state_changes must be a list.")
    if not isinstance(payload.get("shot_handoffs"), list):
        _error(findings, "invalid-shot-handoffs", "shot_handoffs", "Legacy shot_handoffs must be a list.")
    return findings


def audit_document(
    payload: dict[str, Any],
    *,
    storyboard: Optional[dict[str, Any]] = None,
    storyboard_sha256: Optional[str] = None,
    visual_bible: Optional[dict[str, Any]] = None,
    visual_bible_sha256: Optional[str] = None,
    allow_unbound_structure: bool = False,
) -> list[Finding]:
    """Audit one continuity mapping.

    Schema-v2 continuity is production-bound by default: callers must provide the
    actual storyboard and visual-bible documents.  A tool that only wants to lint
    an in-memory draft has to opt in explicitly with ``allow_unbound_structure``;
    that path is not a production validation result.
    """
    schema = payload.get("schema_version", 1)
    modern_contract = schema == 2 or (schema == 1 and payload.get("contract_version") == 2)
    if schema == 1 and not modern_contract:
        return _legacy_audit(payload)
    if not modern_contract:
        return [Finding("unsupported-schema-version", "error", "schema_version", "Supported schema versions are 1 and 2.")]

    findings: list[Finding] = []
    if not allow_unbound_structure:
        if storyboard is None:
            _error(findings, "missing-supplied-storyboard", "storyboard", "Modern continuity requires the actual bound storyboard document.")
        if visual_bible is None:
            _error(findings, "missing-supplied-visual-bible", "visual_bible", "Modern continuity requires the actual bound visual-bible document.")
    if not _has_content(payload.get("continuity_id")):
        _error(findings, "missing-continuity-id", "continuity_id", "continuity_id is required.")
    if not _valid_revision(payload.get("revision")):
        _error(findings, "invalid-continuity-revision", "revision", "revision must be stable and non-empty.")

    source_bindings = payload.get("source_bindings")
    if not isinstance(source_bindings, dict):
        _error(findings, "invalid-source-bindings", "source_bindings", "source_bindings must be a mapping.")
        source_bindings = {}
    for role in ("storyboard", "visual_bible"):
        if role not in source_bindings:
            _error(findings, "missing-source-binding", "source_bindings", f"Missing {role} binding.")
        else:
            _audit_binding(source_bindings[role], f"source_bindings.{role}", findings)

    storyboard_binding = source_bindings.get("storyboard") if isinstance(source_bindings, dict) else None
    if storyboard is not None and isinstance(storyboard_binding, dict):
        if storyboard_binding.get("artifact_id") != storyboard.get("storyboard_id"):
            _error(findings, "storyboard-id-mismatch", "source_bindings.storyboard", "Bound storyboard ID does not match supplied storyboard.")
        if str(storyboard_binding.get("revision")) != str(storyboard.get("revision")):
            _error(findings, "storyboard-revision-mismatch", "source_bindings.storyboard", "Bound storyboard revision does not match supplied storyboard.")
        if storyboard_sha256 and _is_hash(storyboard_binding.get("sha256")) and storyboard_binding["sha256"].casefold() != storyboard_sha256.casefold():
            _error(findings, "storyboard-hash-mismatch", "source_bindings.storyboard", "Bound storyboard hash does not match supplied file.")

    visual_binding = source_bindings.get("visual_bible") if isinstance(source_bindings, dict) else None
    visual_assets: set[tuple[str, str]] = set()
    if visual_bible is not None:
        visual_assets = _visual_index(visual_bible, findings)
        if isinstance(visual_binding, dict):
            if visual_binding.get("artifact_id") != visual_bible.get("visual_bible_id"):
                _error(findings, "visual-bible-id-mismatch", "source_bindings.visual_bible", "Bound visual-bible ID does not match supplied visual bible.")
            if str(visual_binding.get("revision")) != str(visual_bible.get("revision")):
                _error(findings, "visual-bible-revision-mismatch", "source_bindings.visual_bible", "Bound visual-bible revision does not match supplied visual bible.")
            if visual_bible_sha256 and _is_hash(visual_binding.get("sha256")) and visual_binding["sha256"].casefold() != visual_bible_sha256.casefold():
                _error(findings, "visual-bible-hash-mismatch", "source_bindings.visual_bible", "Bound visual-bible hash does not match supplied file.")

    global_locks = payload.get("global_locks")
    if not isinstance(global_locks, dict):
        _error(findings, "invalid-global-locks", "global_locks", "global_locks must be a mapping.")
        global_locks = {}
    seen_lock_ids: set[str] = set()
    locked_values: dict[tuple[str, str, str, str], Any] = {}
    for category in LOCK_CATEGORIES:
        group = global_locks.get(category)
        location = f"global_locks.{category}"
        if not isinstance(group, dict):
            _error(findings, "missing-lock-category", location, f"{category} requires an explicit lock decision.")
            continue
        status = group.get("status")
        entries = group.get("entries")
        if status not in {"locked", "not_applicable"}:
            _error(findings, "invalid-lock-status", location, "status must be locked or not_applicable.")
        if not isinstance(entries, list):
            _error(findings, "invalid-lock-entries", location, "entries must be a list.")
            entries = []
        if status == "not_applicable":
            if not _has_content(group.get("reason")):
                _error(findings, "missing-lock-exemption-reason", location, "not_applicable requires a reason.")
            if entries:
                _error(findings, "exempt-lock-has-entries", location, "not_applicable lock category must not contain entries.")
            continue
        if status == "locked" and not entries:
            _error(findings, "empty-locked-category", location, "locked status requires at least one exact entry.")
        for position, entry in enumerate(entries, start=1):
            entry_location = f"{location}.entries[{position}]"
            if not isinstance(entry, dict):
                _error(findings, "invalid-lock-entry", entry_location, "Lock entry must be a mapping.")
                continue
            lock_id = entry.get("lock_id")
            target = entry.get("target_ref")
            prop = entry.get("property")
            value = entry.get("value")
            if not _has_content(lock_id):
                _error(findings, "missing-lock-id", entry_location, "lock_id is required.")
            elif str(lock_id) in seen_lock_ids:
                _error(findings, "duplicate-lock-id", entry_location, f"Duplicate lock_id: {lock_id}.")
            else:
                seen_lock_ids.add(str(lock_id))
            if not isinstance(target, dict) or not _has_content(target.get("asset_id")) or not _valid_revision(target.get("revision")):
                _error(findings, "invalid-lock-target", entry_location, "target_ref requires asset_id and revision.")
                continue
            if not _has_content(prop) or not _has_content(value):
                _error(findings, "incomplete-lock-entry", entry_location, "Lock entry requires property and value.")
                continue
            asset_key = (str(target["asset_id"]).strip(), str(target["revision"]).strip())
            if visual_bible is not None and asset_key not in visual_assets:
                _error(findings, "unknown-lock-asset-revision", entry_location, f"No visual-bible asset revision {asset_key[0]}@{asset_key[1]}.")
            conflict_key = (category, asset_key[0], asset_key[1], str(prop).strip())
            if conflict_key in locked_values and locked_values[conflict_key] != value:
                _error(findings, "lock-conflict", entry_location, f"Conflicting values for {asset_key[0]}@{asset_key[1]} {prop}.")
            else:
                locked_values[conflict_key] = value

    state_changes = payload.get("state_changes")
    if not isinstance(state_changes, list):
        _error(findings, "invalid-state-changes", "state_changes", "state_changes must be a list.")
        state_changes = []
    seen_changes: set[str] = set()
    for position, change in enumerate(state_changes, start=1):
        location = f"state_changes[{position}]"
        if not isinstance(change, dict):
            _error(findings, "invalid-state-change", location, "State change must be a mapping.")
            continue
        change_id = change.get("change_id")
        if not _has_content(change_id):
            _error(findings, "missing-change-id", location, "change_id is required.")
        elif str(change_id) in seen_changes:
            _error(findings, "duplicate-change-id", location, f"Duplicate change_id: {change_id}.")
        else:
            seen_changes.add(str(change_id))
        for field in ("item_ref", "before", "trigger_shot_id", "trigger_event", "after"):
            if not _has_content(change.get(field)):
                _error(findings, "incomplete-state-change", location, f"State change requires {field}.")
        if _has_content(change.get("before")) and change.get("before") == change.get("after"):
            _error(findings, "no-op-state-change", location, "before and after must differ.")

    handoffs = payload.get("shot_handoffs")
    if not isinstance(handoffs, list) or not handoffs:
        _error(findings, "missing-shot-handoffs", "shot_handoffs", "At least one shot handoff is required.")
        handoffs = []
    seen_from: set[str] = set()
    for position, handoff in enumerate(handoffs):
        location = f"shot_handoffs[{position + 1}]"
        if not isinstance(handoff, dict):
            _error(findings, "invalid-shot-handoff", location, "Shot handoff must be a mapping.")
            continue
        from_id = handoff.get("from_shot_id")
        to_id = handoff.get("to_shot_id")
        if not _has_content(from_id):
            _error(findings, "missing-handoff-source", location, "from_shot_id is required.")
        elif str(from_id) in seen_from:
            _error(findings, "duplicate-handoff-source", location, f"Duplicate handoff source: {from_id}.")
        else:
            seen_from.add(str(from_id))
        if not _has_content(handoff.get("state_out")) or not _has_content(handoff.get("next_state_in")):
            _error(findings, "missing-handoff-state", location, "state_out and next_state_in are required.")
        elif handoff.get("state_out") != handoff.get("next_state_in"):
            _error(findings, "handoff-state-conflict", location, "state_out must equal next_state_in.")
        if not isinstance(handoff.get("match_points"), list):
            _error(findings, "invalid-match-points", location, "match_points must be a list.")
        expected_next = handoffs[position + 1].get("from_shot_id") if position + 1 < len(handoffs) and isinstance(handoffs[position + 1], dict) else None
        if to_id != expected_next:
            _error(findings, "handoff-chain-conflict", location, f"to_shot_id must be {expected_next!r} for this ordered chain.")

    if storyboard is not None and isinstance(storyboard.get("shots"), list):
        shots = storyboard["shots"]
        board_ids = [shot.get("shot_id") for shot in shots if isinstance(shot, dict)]
        ledger_ids = [handoff.get("from_shot_id") for handoff in handoffs if isinstance(handoff, dict)]
        if ledger_ids != board_ids:
            _error(findings, "storyboard-handoff-coverage-mismatch", "shot_handoffs", "Handoff sources must match storyboard shot order exactly.")
        for index, (shot, handoff) in enumerate(zip(shots, handoffs), start=1):
            if not isinstance(shot, dict) or not isinstance(handoff, dict):
                continue
            if shot.get("state_out") != handoff.get("state_out"):
                _error(findings, "storyboard-state-out-mismatch", f"shot_handoffs[{index}]", "Ledger state_out does not match storyboard state_out.")
            board_handoff = shot.get("handoff")
            if isinstance(board_handoff, dict) and board_handoff.get("to_shot_id") != handoff.get("to_shot_id"):
                _error(findings, "storyboard-handoff-target-mismatch", f"shot_handoffs[{index}]", "Ledger target does not match storyboard handoff target.")

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--storyboard", type=Path)
    parser.add_argument("--visual-bible", type=Path)
    parser.add_argument(
        "--allow-unbound-structure",
        action="store_true",
        help="Lint a schema-v2 draft without opening its bound files; not production validation.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_document(args.file)
        storyboard = load_document(args.storyboard) if args.storyboard else None
        visual_bible = load_document(args.visual_bible) if args.visual_bible else None
        findings = audit_document(
            payload,
            storyboard=storyboard,
            storyboard_sha256=_sha256(args.storyboard) if args.storyboard else None,
            visual_bible=visual_bible,
            visual_bible_sha256=_sha256(args.visual_bible) if args.visual_bible else None,
            allow_unbound_structure=args.allow_unbound_structure,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR input: {exc}")
        return 2
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
        print(f"Errors: {sum(item.severity == 'error' for item in findings)}")
    else:
        print("Continuity structure valid. Visual fidelity and dramatic continuity remain manual reviews.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
