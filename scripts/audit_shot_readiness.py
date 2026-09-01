#!/usr/bin/env python3
"""Audit source-truth, atomicity, timing, physical-sound, and release fields."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SOURCE_STATUSES = {"MATCHED", "AUTHOR_ADDED", "SOURCE_DRIFT", "SOURCE_MISMATCH", "UNKNOWN_REQUIRES_REVIEW"}
ATOMIC_STATUSES = {"ATOMIC_PASS", "SPLIT_REQUIRED", "SPLIT_RECOMMENDED", "CLUSTER_APPROVAL_REQUIRED"}
TEXT_STATUSES = {"none", "post_composite_text", "in_world_generated", "approved"}
LOCKED_DECISIONS = {"approved", "adopt", "locked"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    shot: str
    message: str


def load_document(path: Path) -> Any:
    suffix = path.suffix.casefold()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
        return yaml.safe_load(text)
    raise ValueError("Input must be JSON or YAML")


def _finite_number(value: Any) -> bool:
    return type(value) is not bool and isinstance(value, (int, float)) and math.isfinite(float(value))


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def audit_document(payload: Any, *, production_lock: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(payload, dict):
        return [Finding("invalid-document", "error", "document", "The readiness record must be a mapping.")]
    if payload.get("schema_version") != 1:
        findings.append(Finding("invalid-schema-version", "error", "document", "schema_version must be 1."))
    shots = payload.get("shots")
    if not isinstance(shots, list) or not shots:
        findings.append(Finding("missing-shots", "error", "document", "shots must be a non-empty list."))
        return findings
    lock = production_lock or _text(payload.get("production_lock")) or "draft"
    if lock not in {"draft", "review", "locked"}:
        findings.append(Finding("invalid-production-lock", "error", "document", "production_lock must be draft, review, or locked."))

    seen: set[str] = set()
    for index, shot_payload in enumerate(shots, start=1):
        if not isinstance(shot_payload, dict):
            findings.append(Finding("invalid-shot", "error", f"row-{index}", "Each shot must be a mapping."))
            continue
        shot = _text(shot_payload.get("shot_id")) or f"row-{index}"
        if shot in seen:
            findings.append(Finding("duplicate-shot-id", "error", shot, "shot_id must be unique."))
        seen.add(shot)
        if not _text(shot_payload.get("source_shot_id")):
            findings.append(Finding("missing-source-shot-id", "error", shot, "source_shot_id is required."))

        truth = shot_payload.get("source_truth")
        if not isinstance(truth, dict):
            findings.append(Finding("missing-source-truth", "error", shot, "source_truth must be a mapping."))
        else:
            status = _text(truth.get("status")).upper()
            if status not in SOURCE_STATUSES:
                findings.append(Finding("invalid-source-status", "error", shot, f"source_truth.status must be one of {sorted(SOURCE_STATUSES)}."))
            for field in ("speaker_match", "plot_fact_match"):
                if type(truth.get(field)) is not bool:
                    findings.append(Finding("missing-source-comparison", "error", shot, f"source_truth.{field} must be true or false."))
            additions = truth.get("additions")
            approved_addition = truth.get("author_addition_approved")
            if additions is not None and not isinstance(additions, list):
                findings.append(Finding("invalid-additions", "error", shot, "source_truth.additions must be a list when present."))
            if type(approved_addition) is not bool:
                findings.append(Finding("missing-addition-approval", "error", shot, "author_addition_approved must be true or false."))
            if status in {"SOURCE_DRIFT", "SOURCE_MISMATCH", "UNKNOWN_REQUIRES_REVIEW"} and lock == "locked":
                findings.append(Finding("source-drift-blocks-lock", "error", shot, "Unresolved source drift or mismatch cannot enter a locked board."))
            if status == "AUTHOR_ADDED" and approved_addition is not True:
                severity = "error" if lock == "locked" else "warning"
                findings.append(Finding("unapproved-author-addition", severity, shot, "AUTHOR_ADDED content needs explicit author approval."))
            if status == "SOURCE_MISMATCH" and truth.get("speaker_match") is True and truth.get("plot_fact_match") is True:
                findings.append(Finding("contradictory-source-status", "warning", shot, "SOURCE_MISMATCH is declared while speaker and plot comparisons both pass."))

        atomicity = shot_payload.get("atomicity")
        if not isinstance(atomicity, dict):
            findings.append(Finding("missing-atomicity", "error", shot, "atomicity must be a mapping."))
        else:
            atomic_status = _text(atomicity.get("status")).upper()
            if atomic_status not in ATOMIC_STATUSES:
                findings.append(Finding("invalid-atomicity-status", "error", shot, f"atomicity.status must be one of {sorted(ATOMIC_STATUSES)}."))
            beats = atomicity.get("beat_count")
            if type(beats) is not int or beats < 1:
                findings.append(Finding("invalid-beat-count", "error", shot, "atomicity.beat_count must be a positive integer."))
            if type(atomicity.get("camera_continuity")) is not bool:
                findings.append(Finding("missing-camera-continuity", "error", shot, "atomicity.camera_continuity must be true or false."))
            if atomic_status == "SPLIT_REQUIRED" and lock == "locked":
                findings.append(Finding("split-required-blocks-lock", "error", shot, "A SPLIT_REQUIRED row cannot be production locked."))
            if atomic_status == "CLUSTER_APPROVAL_REQUIRED" and _text(atomicity.get("author_decision")).lower() not in LOCKED_DECISIONS:
                severity = "error" if lock == "locked" else "warning"
                findings.append(Finding("cluster-needs-approval", severity, shot, "A shot cluster needs an explicit author decision before lock."))
            if atomic_status == "ATOMIC_PASS" and beats == 1 and _text(atomicity.get("cluster_rationale")):
                findings.append(Finding("unneeded-cluster-rationale", "warning", shot, "ATOMIC_PASS has a cluster rationale; review the classification."))

        timing = shot_payload.get("timing")
        if not isinstance(timing, dict):
            findings.append(Finding("missing-timing", "error", shot, "timing must be a mapping."))
        else:
            editorial = timing.get("editorial_duration_s")
            provider = timing.get("provider_duration_s")
            floor = timing.get("hard_floor_s")
            for field, value in (("editorial_duration_s", editorial), ("provider_duration_s", provider), ("hard_floor_s", floor)):
                if not _finite_number(value) or float(value) <= 0:
                    findings.append(Finding("invalid-timing", "error", shot, f"timing.{field} must be a positive finite number."))
            if _finite_number(editorial) and _finite_number(floor) and float(editorial) + 0.001 < float(floor):
                findings.append(Finding("duration-infeasible", "error", shot, "Editorial duration is below the hard floor."))
            if _finite_number(editorial) and _finite_number(provider) and float(provider) + 0.001 < float(editorial):
                findings.append(Finding("provider-shorter-than-editorial", "warning", shot, "Provider duration is shorter than the editorial clock; declare a split or extension."))

        physical = shot_payload.get("physical_sound")
        if not isinstance(physical, dict):
            findings.append(Finding("missing-physical-sound", "error", shot, "physical_sound must be a mapping."))
        else:
            environment = _text(physical.get("environment")).casefold()
            carrier = _text(physical.get("sound_carrier")).casefold()
            if any(token in environment for token in ("vacuum", "outer-space", "outer space", "月面", "真空")):
                if any(token in carrier for token in ("wind", "air", "空气", "ambient")):
                    findings.append(Finding("vacuum-air-sound", "error", shot, "Vacuum/exterior sound needs a declared structural, radio, cabin, subjective, or non-diegetic carrier."))
            if _text(physical.get("force_source")) == "" and _text(physical.get("continuity_state_in")) != _text(physical.get("continuity_state_out")):
                findings.append(Finding("missing-force-source", "warning", shot, "A changed physical state should name its force or trigger."))
            for field in ("continuity_state_in", "continuity_state_out"):
                if not _text(physical.get(field)):
                    findings.append(Finding("missing-continuity-state", "error", shot, f"physical_sound.{field} is required."))

        text_layer = shot_payload.get("text")
        if not isinstance(text_layer, dict):
            findings.append(Finding("missing-text-layer", "error", shot, "text must be a mapping."))
        else:
            text_status = _text(text_layer.get("status")).casefold()
            if text_status not in TEXT_STATUSES:
                findings.append(Finding("invalid-text-status", "error", shot, f"text.status must be one of {sorted(TEXT_STATUSES)}."))
            if text_status == "post_composite_text" and not _text(text_layer.get("overlay_plan")):
                findings.append(Finding("missing-overlay-plan", "error", shot, "POST_COMPOSITE_TEXT requires an overlay_plan."))

        if lock == "locked" and _text(shot_payload.get("release_decision")).casefold() not in LOCKED_DECISIONS:
            findings.append(Finding("missing-release-decision", "error", shot, "A locked board requires an explicit release_decision."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--production-lock", choices=("draft", "review", "locked"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        findings = audit_document(load_document(args.file), production_lock=args.production_lock)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR input: {exc}")
        return 2
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.shot}: {item.message}")
        errors = sum(item.severity == "error" for item in findings)
        print(f"Errors: {errors}; findings: {len(findings)}")
    else:
        print("Shot readiness record is mechanically valid. Source fidelity, playability, and cinematic review remain manual.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
