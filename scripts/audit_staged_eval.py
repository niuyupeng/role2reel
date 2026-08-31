#!/usr/bin/env python3
"""Audit staged-deep evaluation records and the integrity of their declared files.

This auditor checks only record completeness, path containment, regular-file status,
and SHA-256 agreement.  It cannot establish that a task really ran, that inputs were
actually isolated, that a review was independent, or that an output has artistic
quality.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the CLI dependency check
    yaml = None

try:
    from scripts.audit_life_paths import audit_file as audit_life_path_file
    from scripts.audit_life_paths import candidate_sha256
    from scripts.audit_life_paths import load_yaml_mapping as load_life_path_workbench
except ModuleNotFoundError:  # pragma: no cover - direct execution from scripts/
    from audit_life_paths import audit_file as audit_life_path_file
    from audit_life_paths import candidate_sha256
    from audit_life_paths import load_yaml_mapping as load_life_path_workbench


TOP_LEVEL_FIELDS = {
    "schema_version",
    "record_id",
    "case_id",
    "status",
    "artifact_set",
    "compile_phase",
    "scene_phase",
    "counterfactual_runs",
    "traceability",
    "blind_review",
    "claim_boundary",
}
ARTIFACT_FIELDS = {
    "project_root",
    "workbench_file",
    "biography_file",
    "relationship_ledger_file",
    "locked_fact_boundary_sha256",
    "locked_candidate_sha256",
    "life_path_lock_revision",
    "approved_biography_revision",
    "approved_biography_sha256",
    "deep_audit_command",
    "deep_audit_passed",
}
COMPILE_FIELDS = {
    "fresh_task_id",
    "model_and_version",
    "input_file_hashes",
    "output_artifact_files",
    "canonical_source_refs",
    "compile_audit_passed",
}
SCENE_FIELDS = {
    "fresh_task_id",
    "model_and_version",
    "received_compiled_assets_only",
    "excluded_inputs",
    "input_file_hashes",
    "scene_output_file",
    "output_hash",
}
TRACEABILITY_FIELDS = {
    "visible_deltas",
    "explicit_branch_leaks",
    "semantic_branch_leak_review",
}
BLIND_REVIEW_FIELDS = {
    "randomized_output_ids",
    "reviewer_ids",
    "actor_playability",
    "character_identifiability",
    "nonverbal_replacement",
    "relationship_truth",
    "read_aloud_naturalness",
    "repair_reasons",
}
CLAIM_FIELDS = {"behavior_pass", "reason"}

RECORD_STATUSES = {"planned", "pending", "in_progress", "completed", "failed"}
RUN_KINDS = (
    "locked_baseline",
    "branch_swap",
    "occupational_context_swap",
    "causal_node_ablation",
    "dialogue_deletion",
)
VARIANT_RUN_KINDS = set(RUN_KINDS) - {"locked_baseline"}
EXPECTED_CHANGED_INPUTS = {
    "locked_baseline": [],
    "branch_swap": ["variant_context.workbench_file"],
    "occupational_context_swap": ["variant_context.occupational_context_file"],
    "causal_node_ablation": ["variant_context.ablated_source_ref"],
    "dialogue_deletion": ["variant_context.source_output_sha256"],
}
PASS_STATUSES = {"pass", "passed", "complete", "completed", "approved", "clear"}
POSITIVE_REVIEW_VERDICTS = {
    "accept",
    "accepted",
    "approve",
    "approved",
    "clear",
    "ok",
    "pass",
    "passed",
    "positive",
    "合格",
    "接受",
    "通过",
}
NEGATIVE_REVIEW_VERDICTS = {
    "blocked",
    "fail",
    "failed",
    "failure",
    "invalid",
    "negative",
    "no",
    "poor",
    "reject",
    "rejected",
    "unacceptable",
    "不合格",
    "不通过",
    "否",
    "拒绝",
    "负面",
}
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
SOURCE_REF_PATTERN = re.compile(r"^life-path:[\w.-]+/[\w.-]+$", re.UNICODE)


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
    if isinstance(value, dict):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_has_content(item) for item in value)
    return True


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_PATTERN.fullmatch(value.strip()))


def _error(findings: list[Finding], code: str, location: str, message: str) -> None:
    findings.append(Finding(code, "error", location, message))


def _require_fields(
    findings: list[Finding], mapping: dict[str, Any], fields: Iterable[str], location: str
) -> None:
    for field in fields:
        if field not in mapping:
            _error(findings, "missing-field", location, f"Missing required field: {field}.")


def load_record(path: Path) -> dict[str, Any]:
    """Load one UTF-8 YAML staged-evaluation record."""
    if yaml is None:
        raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return payload


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _contains_symlink(path: Path) -> bool:
    """Return true when any existing component, including the leaf, is a symlink."""
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return False
    return False


def _contains_symlink_below(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return False
    return False


def _same_file(first: Path, second: Path) -> bool:
    """Compare filesystem identity so hard links cannot masquerade as independent files."""
    try:
        return os.path.samefile(first, second)
    except OSError:
        return first == second


def _project_root(
    artifact_set: dict[str, Any], record_path: Path, findings: list[Finding]
) -> Optional[tuple[Path, Path]]:
    raw_root = artifact_set.get("project_root")
    if not isinstance(raw_root, str) or not raw_root.strip():
        _error(findings, "missing-project-root", "artifact_set.project_root", "A passing record requires project_root.")
        return None
    supplied = Path(raw_root.strip())
    lexical = _lexical_absolute(supplied if supplied.is_absolute() else record_path.parent / supplied)
    if _contains_symlink(lexical):
        _error(
            findings,
            "project-root-symlink",
            "artifact_set.project_root",
            f"project_root cannot traverse a symbolic link: {lexical}.",
        )
        return None
    if not lexical.exists():
        _error(findings, "missing-project-root", "artifact_set.project_root", f"project_root does not exist: {lexical}.")
        return None
    if not lexical.is_dir():
        _error(findings, "invalid-project-root", "artifact_set.project_root", f"project_root is not a directory: {lexical}.")
        return None
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        _error(findings, "invalid-project-root", "artifact_set.project_root", f"Cannot resolve project_root: {exc}.")
        return None
    return lexical, resolved


def _descriptor_parts(value: Any) -> tuple[Any, Any]:
    if isinstance(value, dict):
        return value.get("path", value.get("file")), value.get("sha256", value.get("hash"))
    return value, None


def _companion_hash(companion: Any, path_value: Any, index: int) -> Any:
    if companion is None:
        return None
    if isinstance(companion, str):
        return companion
    if isinstance(companion, dict):
        if "path" in companion or "file" in companion:
            companion_path, companion_digest = _descriptor_parts(companion)
            return companion_digest if companion_path == path_value else None
        if isinstance(path_value, str):
            return companion.get(path_value)
        return None
    if isinstance(companion, list):
        for item in companion:
            if isinstance(item, dict):
                item_path, item_digest = _descriptor_parts(item)
                if item_path == path_value:
                    return item_digest
        if index < len(companion):
            item = companion[index]
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                _, item_digest = _descriptor_parts(item)
                return item_digest
    return None


def _bindings(value: Any, companion: Any = None) -> list[tuple[Any, Any, int]]:
    if isinstance(value, dict) and "path" not in value and "file" not in value:
        return [(path_value, digest, index) for index, (path_value, digest) in enumerate(value.items())]
    values = value if isinstance(value, list) else [value]
    result: list[tuple[Any, Any, int]] = []
    for index, item in enumerate(values):
        path_value, digest = _descriptor_parts(item)
        if digest is None:
            digest = _companion_hash(companion, path_value, index)
        result.append((path_value, digest, index))
    return result


def _validate_file_binding(
    path_value: Any,
    digest: Any,
    location: str,
    roots: tuple[Path, Path],
    findings: list[Finding],
) -> Optional[Path]:
    lexical_root, resolved_root = roots
    if not isinstance(path_value, str) or not path_value.strip():
        _error(findings, "missing-file-reference", location, "A non-empty file path is required.")
        return None
    if not _is_sha256(digest):
        code = "missing-file-hash" if digest is None or digest == "" else "invalid-file-hash"
        _error(findings, code, location, "A 64-hex SHA-256 digest is required for every referenced file.")

    supplied = Path(path_value.strip())
    lexical = _lexical_absolute(supplied if supplied.is_absolute() else lexical_root / supplied)
    if not _is_within(lexical, lexical_root):
        _error(findings, "file-path-escape", location, f"Referenced file escapes project_root: {lexical}.")
        return None
    if _contains_symlink_below(lexical, lexical_root):
        _error(findings, "file-symlink", location, f"Referenced file cannot traverse a symbolic link: {lexical}.")
        return None
    if not lexical.exists():
        _error(findings, "missing-file", location, f"Referenced file does not exist: {lexical}.")
        return None
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        _error(findings, "invalid-file", location, f"Cannot resolve referenced file: {exc}.")
        return None
    if not _is_within(resolved, resolved_root):
        _error(findings, "file-path-escape", location, f"Resolved file escapes project_root: {resolved}.")
        return None
    try:
        mode = resolved.stat().st_mode
    except OSError as exc:
        _error(findings, "invalid-file", location, f"Cannot stat referenced file: {exc}.")
        return None
    if not stat.S_ISREG(mode):
        _error(findings, "nonregular-file", location, f"Referenced path is not a regular file: {resolved}.")
        return None
    if _is_sha256(digest):
        try:
            actual = file_sha256(resolved)
        except OSError as exc:
            _error(findings, "unreadable-file", location, f"Cannot hash referenced file: {exc}.")
            return resolved
        if actual.casefold() != str(digest).strip().casefold():
            _error(
                findings,
                "file-hash-mismatch",
                location,
                f"SHA-256 mismatch for {resolved}; declared {digest}, actual {actual}.",
            )
    return resolved


def _validate_file_collection(
    value: Any,
    location: str,
    roots: tuple[Path, Path],
    findings: list[Finding],
    *,
    companion: Any = None,
    required: bool = True,
) -> list[Path]:
    if value is None or value == [] or value == {}:
        if required:
            _error(findings, "missing-file-collection", location, "At least one hashed file reference is required.")
        return []
    if not isinstance(value, (str, list, dict)):
        _error(findings, "invalid-file-collection", location, "File references must be a path, list, or path-to-hash mapping.")
        return []
    resolved: list[Path] = []
    for path_value, digest, index in _bindings(value, companion):
        item_location = f"{location}[{index + 1}]"
        path = _validate_file_binding(path_value, digest, item_location, roots, findings)
        if path is not None:
            if any(_same_file(path, previous) for previous in resolved):
                _error(
                    findings,
                    "duplicate-file-reference",
                    item_location,
                    f"A file collection cannot repeat the same path or filesystem object: {path}.",
                )
            resolved.append(path)
    return resolved


def _artifact_hash(artifact_set: dict[str, Any], path_value: Any, names: Iterable[str]) -> Any:
    embedded_path, embedded_hash = _descriptor_parts(path_value)
    if embedded_hash is not None:
        return embedded_hash
    for name in names:
        if artifact_set.get(name) is not None:
            return artifact_set.get(name)
    return _companion_hash(artifact_set.get("file_hashes"), embedded_path, 0)


def _validate_artifact_file(
    artifact_set: dict[str, Any],
    field: str,
    hash_fields: Iterable[str],
    roots: tuple[Path, Path],
    findings: list[Finding],
    *,
    required: bool,
) -> Optional[Path]:
    value = artifact_set.get(field)
    if not _has_content(value):
        if required:
            _error(findings, "missing-artifact-file", f"artifact_set.{field}", f"A passing record requires {field}.")
        return None
    path_value, embedded_hash = _descriptor_parts(value)
    digest = embedded_hash if embedded_hash is not None else _artifact_hash(artifact_set, value, hash_fields)
    return _validate_file_binding(path_value, digest, f"artifact_set.{field}", roots, findings)


def _review_passed(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in PASS_STATUSES
    if isinstance(value, dict):
        saw_positive_verdict = False
        for field in ("passed", "status", "result", "review_status"):
            if field not in value:
                continue
            verdict = _parse_review_verdict(value[field])
            if verdict is not True:
                return False
            saw_positive_verdict = True
        return saw_positive_verdict
    return False


def _parse_review_verdict(value: Any) -> Optional[bool]:
    if type(value) is bool:
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if normalized in POSITIVE_REVIEW_VERDICTS:
        return True
    if normalized in NEGATIVE_REVIEW_VERDICTS:
        return False
    return None


def _parse_positive_rating(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        rating = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            rating = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(rating):
        return None
    return rating > 0


def _review_item_passed(value: Any) -> bool:
    """Require an explicit positive outcome; any declared failure wins."""
    if not isinstance(value, dict):
        return False
    saw_positive = False
    for field in ("verdict", "status", "result", "review_status", "passed"):
        if field not in value:
            continue
        outcome = _parse_review_verdict(value.get(field))
        if outcome is not True:
            return False
        saw_positive = True
    if "rating" in value:
        rating_passed = _parse_positive_rating(value.get("rating"))
        if rating_passed is not True:
            return False
        # A numeric scale has no universal pass threshold.  It may support an
        # explicit verdict, but cannot declare a behavioral pass by itself.
    return saw_positive


def _audit_basic_schema(payload: dict[str, Any], findings: list[Finding]) -> bool:
    _require_fields(findings, payload, TOP_LEVEL_FIELDS, "record")
    if not _positive_int(payload.get("schema_version")):
        _error(findings, "invalid-schema-version", "schema_version", "schema_version must be a positive integer.")
    if payload.get("record_id") is not None and not (
        isinstance(payload.get("record_id"), str) and payload["record_id"].strip()
    ):
        _error(findings, "invalid-record-id", "record_id", "record_id must be null or a non-empty string.")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"].strip():
        _error(findings, "invalid-case-id", "case_id", "case_id must be a non-empty string.")
    if payload.get("status") not in RECORD_STATUSES:
        _error(findings, "invalid-status", "status", f"status must be one of {sorted(RECORD_STATUSES)}.")

    section_specs = (
        ("artifact_set", ARTIFACT_FIELDS),
        ("compile_phase", COMPILE_FIELDS),
        ("scene_phase", SCENE_FIELDS),
        ("traceability", TRACEABILITY_FIELDS),
        ("blind_review", BLIND_REVIEW_FIELDS),
        ("claim_boundary", CLAIM_FIELDS),
    )
    sections: dict[str, dict[str, Any]] = {}
    for name, fields in section_specs:
        value = payload.get(name)
        if not isinstance(value, dict):
            _error(findings, "invalid-section", name, f"{name} must be a mapping.")
            sections[name] = {}
            continue
        sections[name] = value
        _require_fields(findings, value, fields, name)

    artifact_set = sections.get("artifact_set", {})
    for field in ("deep_audit_passed",):
        if field in artifact_set and type(artifact_set.get(field)) is not bool:
            _error(findings, "invalid-boolean", f"artifact_set.{field}", f"{field} must be true or false.")
    compile_phase = sections.get("compile_phase", {})
    if "compile_audit_passed" in compile_phase and type(compile_phase.get("compile_audit_passed")) is not bool:
        _error(findings, "invalid-boolean", "compile_phase.compile_audit_passed", "compile_audit_passed must be true or false.")
    for field in ("input_file_hashes", "output_artifact_files"):
        if field in compile_phase and not isinstance(compile_phase.get(field), (list, dict)):
            _error(findings, "invalid-list", f"compile_phase.{field}", f"{field} must be a list or mapping.")
    if "canonical_source_refs" in compile_phase and not isinstance(compile_phase.get("canonical_source_refs"), list):
        _error(findings, "invalid-list", "compile_phase.canonical_source_refs", "canonical_source_refs must be a list.")

    scene_phase = sections.get("scene_phase", {})
    if "received_compiled_assets_only" in scene_phase and type(scene_phase.get("received_compiled_assets_only")) is not bool:
        _error(
            findings,
            "invalid-boolean",
            "scene_phase.received_compiled_assets_only",
            "received_compiled_assets_only must be true or false.",
        )
    if "excluded_inputs" in scene_phase and not isinstance(scene_phase.get("excluded_inputs"), list):
        _error(findings, "invalid-list", "scene_phase.excluded_inputs", "excluded_inputs must be a list.")
    if "input_file_hashes" in scene_phase and not isinstance(scene_phase.get("input_file_hashes"), (list, dict)):
        _error(findings, "invalid-list", "scene_phase.input_file_hashes", "input_file_hashes must be a list or mapping.")

    traceability = sections.get("traceability", {})
    for field in ("visible_deltas", "explicit_branch_leaks"):
        if field in traceability and not isinstance(traceability.get(field), list):
            _error(findings, "invalid-list", f"traceability.{field}", f"{field} must be a list.")
    blind_review = sections.get("blind_review", {})
    for field in BLIND_REVIEW_FIELDS:
        if field in blind_review and not isinstance(blind_review.get(field), list):
            _error(findings, "invalid-list", f"blind_review.{field}", f"{field} must be a list.")
    claim_boundary = sections.get("claim_boundary", {})
    if "behavior_pass" in claim_boundary and type(claim_boundary.get("behavior_pass")) is not bool:
        _error(findings, "invalid-behavior-pass", "claim_boundary.behavior_pass", "behavior_pass must be true or false.")
    if "reason" in claim_boundary and not (
        isinstance(claim_boundary.get("reason"), str) and claim_boundary["reason"].strip()
    ):
        _error(findings, "invalid-claim-reason", "claim_boundary.reason", "claim_boundary.reason must be non-empty.")

    runs = payload.get("counterfactual_runs")
    if not isinstance(runs, list):
        _error(findings, "invalid-runs", "counterfactual_runs", "counterfactual_runs must be a list.")
        return claim_boundary.get("behavior_pass") is True
    seen: set[str] = set()
    for index, run in enumerate(runs, start=1):
        location = f"counterfactual_runs[{index}]"
        if not isinstance(run, dict):
            _error(findings, "invalid-run", location, "Each run must be a mapping.")
            continue
        kind = run.get("kind")
        if kind not in RUN_KINDS:
            _error(findings, "invalid-run-kind", location, f"Run kind must be one of {list(RUN_KINDS)}.")
            continue
        if kind in seen:
            _error(findings, "duplicate-run-kind", location, f"Run kind is repeated: {kind}.")
        seen.add(kind)
        changed_inputs = run.get("changed_inputs")
        if not isinstance(changed_inputs, list) or not all(_nonempty_string(item) for item in changed_inputs):
            _error(
                findings,
                "invalid-changed-inputs",
                location,
                "Each run requires a changed_inputs list containing only non-empty labels.",
            )
        if "output_file" not in run:
            _error(findings, "missing-field", location, "Missing required field: output_file.")
        if _has_content(run.get("output_file_hashes")):
            _error(
                findings,
                "ambiguous-run-output",
                location,
                "Use output_file plus output_hash; an alternate output_file_hashes collection cannot replace it.",
            )
    missing_kinds = set(RUN_KINDS) - seen
    if missing_kinds:
        _error(
            findings,
            "missing-run-kinds",
            "counterfactual_runs",
            f"Missing staged run kinds: {sorted(missing_kinds)}.",
        )
    if len(runs) != len(RUN_KINDS):
        _error(findings, "invalid-run-count", "counterfactual_runs", "Exactly five staged run records are required.")
    return claim_boundary.get("behavior_pass") is True


def _audit_passing_record(payload: dict[str, Any], record_path: Path, findings: list[Finding]) -> None:
    if payload.get("status") != "completed":
        _error(findings, "incomplete-status", "status", "behavior_pass=true requires status=completed.")
    if not _has_content(payload.get("record_id")):
        _error(findings, "missing-record-id", "record_id", "A passing record requires a stable record_id.")

    artifact_set = payload.get("artifact_set") if isinstance(payload.get("artifact_set"), dict) else {}
    roots = _project_root(artifact_set, record_path, findings)
    if roots is not None:
        workbench_path = _validate_artifact_file(
            artifact_set,
            "workbench_file",
            ("workbench_sha256",),
            roots,
            findings,
            required=True,
        )
        biography_path = _validate_artifact_file(
            artifact_set,
            "biography_file",
            ("biography_file_sha256", "approved_biography_sha256"),
            roots,
            findings,
            required=True,
        )
        relationship_ledger_path = _validate_artifact_file(
            artifact_set,
            "relationship_ledger_file",
            ("relationship_ledger_sha256",),
            roots,
            findings,
            required=False,
        )
    else:
        workbench_path = None
        biography_path = None
        relationship_ledger_path = None
    if not _is_sha256(artifact_set.get("locked_fact_boundary_sha256")):
        _error(
            findings,
            "invalid-locked-fact-boundary-hash",
            "artifact_set.locked_fact_boundary_sha256",
            "A passing record requires the 64-hex locked fact-boundary hash.",
        )
    if not _is_sha256(artifact_set.get("locked_candidate_sha256")):
        _error(
            findings,
            "invalid-locked-candidate-hash",
            "artifact_set.locked_candidate_sha256",
            "A passing record requires the 64-hex locked candidate hash.",
        )
    if not _positive_int(artifact_set.get("life_path_lock_revision")):
        _error(
            findings,
            "invalid-lock-revision",
            "artifact_set.life_path_lock_revision",
            "A passing record requires a positive life-path lock revision.",
        )
    if not _positive_int(artifact_set.get("approved_biography_revision")):
        _error(
            findings,
            "invalid-biography-revision",
            "artifact_set.approved_biography_revision",
            "A passing record requires a positive approved biography revision.",
        )
    if not _is_sha256(artifact_set.get("approved_biography_sha256")):
        _error(
            findings,
            "invalid-approved-biography-hash",
            "artifact_set.approved_biography_sha256",
            "A passing record requires the approved biography SHA-256 declaration.",
        )
    if not _nonempty_string(artifact_set.get("deep_audit_command")):
        _error(findings, "missing-deep-audit-command", "artifact_set.deep_audit_command", "Record the deep-audit command.")
    if artifact_set.get("deep_audit_passed") is not True:
        _error(findings, "deep-audit-not-passed", "artifact_set.deep_audit_passed", "The deep audit must be recorded as passed.")

    workbench_payload: dict[str, Any] = {}
    if workbench_path is not None:
        try:
            life_findings = audit_life_path_file(
                workbench_path,
                require_locked=True,
                relationship_ledger_path=relationship_ledger_path,
            )
        except (OSError, UnicodeError, ValueError) as exc:
            _error(findings, "life-path-audit-failed", "artifact_set.workbench_file", f"Cannot audit staged deep workbench: {exc}.")
        else:
            for item in life_findings:
                if item.severity == "error":
                    _error(
                        findings,
                        "life-path-audit-failed",
                        f"artifact_set.workbench_file:{item.location}",
                        f"{item.code}: {item.message}",
                    )
            try:
                workbench_payload = load_life_path_workbench(workbench_path)
            except (OSError, UnicodeError, ValueError) as exc:
                _error(findings, "invalid-workbench", "artifact_set.workbench_file", str(exc))
    if workbench_payload:
        selection = workbench_payload.get("selection") if isinstance(workbench_payload.get("selection"), dict) else {}
        biography = workbench_payload.get("deep_biography") if isinstance(workbench_payload.get("deep_biography"), dict) else {}
        approval = biography.get("author_approval") if isinstance(biography.get("author_approval"), dict) else {}
        recorded_bindings = {
            "locked_fact_boundary_sha256": selection.get("locked_fact_boundary_sha256"),
            "locked_candidate_sha256": selection.get("locked_candidate_sha256"),
            "life_path_lock_revision": selection.get("lock_revision"),
            "approved_biography_revision": approval.get("approved_biography_revision"),
            "approved_biography_sha256": approval.get("approved_body_sha256"),
        }
        for field, expected in recorded_bindings.items():
            if artifact_set.get(field) != expected:
                _error(
                    findings,
                    "staged-upstream-binding-mismatch",
                    f"artifact_set.{field}",
                    f"Recorded staged value does not match the audited workbench value {expected!r}.",
                )
        declared_biography = biography.get("biography_file")
        if biography_path is not None and isinstance(declared_biography, str):
            declared_path = (workbench_path.parent / declared_biography).resolve()
            if declared_path != biography_path:
                _error(
                    findings,
                    "staged-biography-binding-mismatch",
                    "artifact_set.biography_file",
                    "Staged biography file does not match the biography audited through the workbench.",
                )
        declared_ledger = biography.get("relationship_ledger_file")
        if isinstance(declared_ledger, str) and declared_ledger.strip():
            project_root = roots[1] if roots is not None else workbench_path.parent.resolve()
            supplied_ledger = Path(declared_ledger)
            declared_ledger_path = (
                supplied_ledger if supplied_ledger.is_absolute() else project_root / supplied_ledger
            ).resolve()
            if relationship_ledger_path is None:
                _error(
                    findings,
                    "missing-staged-relationship-ledger",
                    "artifact_set.relationship_ledger_file",
                    "A relationship ledger declared by the audited workbench must be bound as a staged artifact and compile input.",
                )
            elif declared_ledger_path != relationship_ledger_path:
                _error(
                    findings,
                    "staged-relationship-ledger-binding-mismatch",
                    "artifact_set.relationship_ledger_file",
                    "The staged relationship ledger must be the exact ledger declared and audited by the workbench.",
                )

    compile_phase = payload.get("compile_phase") if isinstance(payload.get("compile_phase"), dict) else {}
    compile_task_raw = compile_phase.get("fresh_task_id")
    compile_task = compile_task_raw.strip() if _nonempty_string(compile_task_raw) else None
    if compile_task is None:
        _error(findings, "missing-compile-task", "compile_phase.fresh_task_id", "Compilation requires a fresh_task_id.")
    if not _nonempty_string(compile_phase.get("model_and_version")):
        _error(findings, "missing-compile-model", "compile_phase.model_and_version", "Compilation requires model_and_version.")
    if compile_phase.get("compile_audit_passed") is not True:
        _error(findings, "compile-audit-not-passed", "compile_phase.compile_audit_passed", "The compile audit must be recorded as passed.")
    compile_refs_raw = compile_phase.get("canonical_source_refs")
    if not isinstance(compile_refs_raw, list) or not compile_refs_raw or not all(
        isinstance(ref, str) and SOURCE_REF_PATTERN.fullmatch(ref.strip()) for ref in compile_refs_raw
    ):
        _error(
            findings,
            "invalid-compile-source-refs",
            "compile_phase.canonical_source_refs",
            "A passing compile record requires non-empty canonical life-path source refs.",
        )
        compile_source_refs: set[str] = set()
    else:
        compile_source_refs = {ref.strip() for ref in compile_refs_raw}
        if len(compile_source_refs) != len(compile_refs_raw):
            _error(
                findings,
                "duplicate-compile-source-ref",
                "compile_phase.canonical_source_refs",
                "Canonical compile source refs must be unique.",
            )
    if roots is not None:
        compile_input_paths = _validate_file_collection(
            compile_phase.get("input_file_hashes"),
            "compile_phase.input_file_hashes",
            roots,
            findings,
        )
        compile_output_paths = _validate_file_collection(
            compile_phase.get("output_artifact_files"),
            "compile_phase.output_artifact_files",
            roots,
            findings,
            companion=compile_phase.get("output_file_hashes"),
        )
    else:
        compile_input_paths = []
        compile_output_paths = []
    required_compile_inputs = {
        path
        for path in (workbench_path, biography_path, relationship_ledger_path)
        if path is not None
    }
    if roots is not None and not required_compile_inputs.issubset(set(compile_input_paths)):
        _error(
            findings,
            "compile-input-binding-mismatch",
            "compile_phase.input_file_hashes",
            "The compile task must declare the exact audited workbench, approved biography, and any bound relationship ledger as hashed inputs.",
        )
    for output_path in compile_output_paths:
        if any(_same_file(output_path, input_path) for input_path in compile_input_paths):
            _error(
                findings,
                "compile-output-reuses-input",
                "compile_phase.output_artifact_files",
                f"A compiled output must be a distinct file, not an input path or hard link: {output_path}.",
            )
    if workbench_payload:
        runtime = workbench_payload.get("compiled_runtime") if isinstance(workbench_payload.get("compiled_runtime"), dict) else {}
        artifact_records = runtime.get("artifact_files") if isinstance(runtime.get("artifact_files"), list) else []
        expected_outputs: set[Path] = set()
        if roots is not None:
            _, resolved_root = roots
            for record in artifact_records:
                if isinstance(record, dict) and isinstance(record.get("path"), str):
                    supplied = Path(record["path"])
                    expected_outputs.add((supplied if supplied.is_absolute() else resolved_root / supplied).resolve())
        if expected_outputs != set(compile_output_paths):
            _error(
                findings,
                "compile-output-binding-mismatch",
                "compile_phase.output_artifact_files",
                "Staged compile outputs must equal the exact artifact files audited through the workbench.",
            )
        runtime_refs_raw = runtime.get("source_refs")
        runtime_source_refs = (
            {ref.strip() for ref in runtime_refs_raw if isinstance(ref, str)}
            if isinstance(runtime_refs_raw, list)
            else set()
        )
        if compile_source_refs != runtime_source_refs:
            _error(
                findings,
                "compile-source-closure-mismatch",
                "compile_phase.canonical_source_refs",
                "Staged canonical source refs must match the audited workbench runtime source closure.",
            )

    scene_phase = payload.get("scene_phase") if isinstance(payload.get("scene_phase"), dict) else {}
    scene_task_raw = scene_phase.get("fresh_task_id")
    scene_task = scene_task_raw.strip() if _nonempty_string(scene_task_raw) else None
    if scene_task is None:
        _error(findings, "missing-scene-task", "scene_phase.fresh_task_id", "Scene generation requires a fresh_task_id.")
    if compile_task is not None and scene_task is not None and compile_task == scene_task:
        _error(
            findings,
            "phase-task-reuse",
            "scene_phase.fresh_task_id",
            "Compile and scene phases must use different fresh_task_id values.",
        )
    if not _nonempty_string(scene_phase.get("model_and_version")):
        _error(findings, "missing-scene-model", "scene_phase.model_and_version", "Scene generation requires model_and_version.")
    if scene_phase.get("received_compiled_assets_only") is not True:
        _error(
            findings,
            "scene-input-isolation-not-recorded",
            "scene_phase.received_compiled_assets_only",
            "A passing scene must record received_compiled_assets_only=true.",
        )
    excluded_inputs = scene_phase.get("excluded_inputs")
    required_exclusions = {"long_biography", "rejected_candidates", "prior_generation_transcript"}
    recorded_exclusions = (
        {item.strip() for item in excluded_inputs if isinstance(item, str)}
        if isinstance(excluded_inputs, list)
        else set()
    )
    if not required_exclusions.issubset(recorded_exclusions):
        _error(
            findings,
            "scene-input-isolation-incomplete",
            "scene_phase.excluded_inputs",
            f"A passing scene must explicitly exclude {sorted(required_exclusions)}.",
        )
    scene_output_path: Optional[Path] = None
    scene_input_paths: list[Path] = []
    if roots is not None:
        scene_output, embedded_hash = _descriptor_parts(scene_phase.get("scene_output_file"))
        scene_hash = embedded_hash if embedded_hash is not None else scene_phase.get("output_hash")
        scene_output_path = _validate_file_binding(
            scene_output,
            scene_hash,
            "scene_phase.scene_output_file",
            roots,
            findings,
        )
        scene_input_paths = _validate_file_collection(
            scene_phase.get("input_file_hashes"),
            "scene_phase.input_file_hashes",
            roots,
            findings,
        )
        if set(scene_input_paths) != set(compile_output_paths):
            _error(
                findings,
                "scene-input-not-compiled",
                "scene_phase.input_file_hashes",
                "The fresh scene task must receive exactly the audited compile outputs, not biography or candidate-source files.",
            )
        if scene_output_path is not None and any(
            _same_file(scene_output_path, input_path)
            for input_path in (*compile_input_paths, *compile_output_paths)
        ):
            _error(
                findings,
                "scene-output-reuses-input",
                "scene_phase.scene_output_file",
                "The scene output must be a distinct file, not an upstream input, compiled asset, or hard link to either.",
            )

    runs = payload.get("counterfactual_runs") if isinstance(payload.get("counterfactual_runs"), list) else []
    task_ids: set[str] = {task_id for task_id in (compile_task, scene_task) if task_id is not None}
    output_paths: set[Path] = set()
    output_digests: dict[str, str] = {}
    run_input_sets: dict[str, frozenset[Path]] = {}
    run_evidence: dict[str, dict[str, Any]] = {}
    reserved_paths = [
        path
        for path in (
            workbench_path,
            biography_path,
            relationship_ledger_path,
            scene_output_path,
            *compile_input_paths,
            *compile_output_paths,
        )
        if path is not None
    ]
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict) or run.get("kind") not in RUN_KINDS:
            continue
        location = f"counterfactual_runs[{index}]"
        if run.get("status") != "completed":
            _error(findings, "incomplete-run", f"{location}.status", "Every staged run must have status=completed.")
        if not _has_content(run.get("output_file")):
            _error(findings, "missing-run-output", location, "Every completed run requires one explicit output_file.")
        changed_inputs = run.get("changed_inputs")
        if run.get("kind") in VARIANT_RUN_KINDS and (
            not isinstance(changed_inputs, list)
            or not changed_inputs
            or not all(_nonempty_string(item) for item in changed_inputs)
        ):
            _error(findings, "missing-variant-change", f"{location}.changed_inputs", "Every non-baseline variant must record the input it changed.")
        if changed_inputs != EXPECTED_CHANGED_INPUTS[run["kind"]]:
            _error(
                findings,
                "changed-input-binding-mismatch",
                f"{location}.changed_inputs",
                f"changed_inputs must name the audited variant-context binding {EXPECTED_CHANGED_INPUTS[run['kind']]!r}.",
            )
        task_id = run.get("fresh_task_id", run.get("task_id"))
        if not _nonempty_string(task_id):
            _error(findings, "missing-run-task", location, "Every staged run requires a non-empty task_id or fresh_task_id.")
        else:
            normalized_task_id = task_id.strip()
            if normalized_task_id in task_ids:
                _error(findings, "run-task-reuse", location, f"Staged run task ID is not independent: {normalized_task_id}.")
            else:
                task_ids.add(normalized_task_id)
        model = run.get("model_and_version", run.get("model"))
        if not _nonempty_string(model):
            _error(findings, "missing-run-model", location, "Every staged run requires model_and_version or model.")
        variant_context = run.get("variant_context")
        if not isinstance(variant_context, dict) or variant_context.get("kind") != run.get("kind"):
            _error(
                findings,
                "invalid-variant-context",
                f"{location}.variant_context",
                "Every staged run requires a kind-matched structured variant_context.",
            )
        run_refs_raw = run.get("canonical_source_refs")
        if not isinstance(run_refs_raw, list) or not run_refs_raw or not all(
            isinstance(ref, str) and SOURCE_REF_PATTERN.fullmatch(ref.strip()) for ref in run_refs_raw
        ):
            _error(
                findings,
                "invalid-run-source-refs",
                f"{location}.canonical_source_refs",
                "Every staged run requires non-empty canonical life-path source refs for its exact runtime closure.",
            )
            run_refs: set[str] = set()
        else:
            run_refs = {ref.strip() for ref in run_refs_raw}
            if len(run_refs) != len(run_refs_raw):
                _error(findings, "duplicate-run-source-ref", f"{location}.canonical_source_refs", "Run source refs must be unique.")
        blind_output_id = run.get("blind_output_id")
        if not _nonempty_string(blind_output_id):
            _error(findings, "missing-blind-output-id", location, "Every staged run requires a stable blind_output_id.")
            normalized_blind_output_id = None
        else:
            normalized_blind_output_id = blind_output_id.strip()
            if any(item.get("blind_output_id") == normalized_blind_output_id for item in run_evidence.values()):
                _error(findings, "duplicate-blind-output-id", location, f"blind_output_id is repeated: {normalized_blind_output_id}.")
        actual_output_digest: Optional[str] = None
        if roots is not None:
            run_input_paths = _validate_file_collection(
                run.get("input_file_hashes"),
                f"{location}.input_file_hashes",
                roots,
                findings,
            )
            run_input_sets[run["kind"]] = frozenset(run_input_paths)
            output_value = run.get("output_file")
            if isinstance(output_value, list) or (
                isinstance(output_value, dict) and "path" not in output_value and "file" not in output_value
            ):
                _error(
                    findings,
                    "invalid-run-output-descriptor",
                    f"{location}.output_file",
                    "Each staged run requires exactly one output path or one {path, sha256} descriptor.",
                )
                validated = []
            else:
                output_path_value, embedded_output_hash = _descriptor_parts(output_value)
                output_digest = embedded_output_hash if embedded_output_hash is not None else run.get("output_hash")
                validated_output = _validate_file_binding(
                    output_path_value,
                    output_digest,
                    f"{location}.output_file",
                    roots,
                    findings,
                )
                validated = [validated_output] if validated_output is not None else []
            for path in validated:
                if any(_same_file(path, reserved) for reserved in (*reserved_paths, *run_input_paths)):
                    _error(
                        findings,
                        "run-output-reuses-existing-file",
                        location,
                        f"A staged run output cannot reuse an upstream, scene, or input file or hard link: {path}.",
                    )
                if any(_same_file(path, previous) for previous in output_paths):
                    _error(findings, "run-output-reuse", location, f"Independent runs cannot share a path or filesystem object: {path}.")
                output_paths.add(path)
                actual_output_digest = file_sha256(path)
                previous_kind = output_digests.get(actual_output_digest)
                if previous_kind is not None:
                    _error(
                        findings,
                        "identical-run-output",
                        location,
                        f"Controlled run output is byte-identical to {previous_kind}; no behavioral delta has been demonstrated.",
                    )
                else:
                    output_digests[actual_output_digest] = run["kind"]
        run_evidence[run["kind"]] = {
            "task_id": task_id.strip() if _nonempty_string(task_id) else None,
            "output_sha256": actual_output_digest,
            "source_refs": run_refs,
            "blind_output_id": normalized_blind_output_id,
        }

    baseline_inputs = run_input_sets.get("locked_baseline")
    if baseline_inputs is not None:
        for kind in VARIANT_RUN_KINDS:
            if run_input_sets.get(kind) == baseline_inputs:
                _error(
                    findings,
                    "variant-inputs-unchanged",
                    f"counterfactual_runs:{kind}.input_file_hashes",
                    "A controlled variant must bind at least one different hashed input from the locked baseline.",
                )
    baseline_run = run_evidence.get("locked_baseline", {})
    if baseline_run.get("source_refs") != compile_source_refs:
        _error(
            findings,
            "baseline-source-closure-mismatch",
            "counterfactual_runs:locked_baseline.canonical_source_refs",
            "The locked baseline run source closure must equal the audited baseline compile closure.",
        )

    runs_by_kind = {
        run.get("kind"): run
        for run in runs
        if isinstance(run, dict) and run.get("kind") in RUN_KINDS
    }
    baseline_context = runs_by_kind.get("locked_baseline", {}).get("variant_context")
    baseline_occupation_path: Optional[Path] = None
    if roots is not None and isinstance(baseline_context, dict):
        occupation_value = baseline_context.get("occupational_context_file")
        occupation_path_value, occupation_hash = _descriptor_parts(occupation_value)
        baseline_occupation_path = _validate_file_binding(
            occupation_path_value,
            occupation_hash,
            "counterfactual_runs:locked_baseline.variant_context.occupational_context_file",
            roots,
            findings,
        )
        if baseline_occupation_path is not None and baseline_occupation_path not in run_input_sets.get("locked_baseline", frozenset()):
            _error(
                findings,
                "baseline-context-not-input",
                "counterfactual_runs:locked_baseline.variant_context",
                "The baseline occupational-context file must be one of the baseline run's hashed inputs.",
            )

    baseline_selection = workbench_payload.get("selection") if isinstance(workbench_payload.get("selection"), dict) else {}
    baseline_candidate_id = baseline_selection.get("selected_branch_id")
    baseline_candidates = workbench_payload.get("candidates") if isinstance(workbench_payload.get("candidates"), list) else []
    baseline_candidate = next(
        (candidate for candidate in baseline_candidates if isinstance(candidate, dict) and candidate.get("id") == baseline_candidate_id),
        {},
    )
    baseline_node_ids = {
        node.get("id")
        for node in baseline_candidate.get("causal_spine", [])
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    }

    for variant_kind in ("branch_swap", "causal_node_ablation"):
        run = runs_by_kind.get(variant_kind, {})
        context = run.get("variant_context") if isinstance(run.get("variant_context"), dict) else {}
        if roots is None:
            continue
        workbench_value = context.get("workbench_file")
        workbench_ref, workbench_hash = _descriptor_parts(workbench_value)
        variant_workbench_path = _validate_file_binding(
            workbench_ref,
            workbench_hash,
            f"counterfactual_runs:{variant_kind}.variant_context.workbench_file",
            roots,
            findings,
        )
        biography_value = context.get("biography_file")
        biography_ref, biography_hash = _descriptor_parts(biography_value)
        variant_biography_path = _validate_file_binding(
            biography_ref,
            biography_hash,
            f"counterfactual_runs:{variant_kind}.variant_context.biography_file",
            roots,
            findings,
        )
        if variant_workbench_path is None:
            continue
        if workbench_path is not None and _same_file(variant_workbench_path, workbench_path):
            _error(
                findings,
                "variant-workbench-reuses-baseline",
                f"counterfactual_runs:{variant_kind}.variant_context.workbench_file",
                "A branch or node variant requires its own author-locked workbench revision.",
            )
        try:
            variant_findings = audit_life_path_file(variant_workbench_path, require_locked=True)
            variant_workbench = load_life_path_workbench(variant_workbench_path)
        except (OSError, UnicodeError, ValueError) as exc:
            _error(
                findings,
                "variant-life-path-audit-failed",
                f"counterfactual_runs:{variant_kind}.variant_context.workbench_file",
                f"Cannot audit variant workbench: {exc}.",
            )
            continue
        for item in variant_findings:
            if item.severity == "error":
                _error(
                    findings,
                    "variant-life-path-audit-failed",
                    f"{variant_workbench_path}:{item.location}",
                    f"{item.code}: {item.message}",
                )
        variant_biography = (
            variant_workbench.get("deep_biography")
            if isinstance(variant_workbench.get("deep_biography"), dict)
            else {}
        )
        declared_biography = variant_biography.get("biography_file")
        if isinstance(declared_biography, str) and variant_biography_path is not None:
            declared_biography_path = (variant_workbench_path.parent / declared_biography).resolve()
            if declared_biography_path != variant_biography_path:
                _error(
                    findings,
                    "variant-biography-binding-mismatch",
                    f"counterfactual_runs:{variant_kind}.variant_context.biography_file",
                    "The variant record must bind the exact biography audited through its workbench.",
                )
        if variant_workbench.get("character_id") != workbench_payload.get("character_id"):
            _error(findings, "variant-character-mismatch", f"counterfactual_runs:{variant_kind}", "A controlled life-path variant must preserve character_id.")
        if (
            workbench_payload.get("package_context_id") is not None
            and variant_workbench.get("package_context_id") != workbench_payload.get("package_context_id")
        ):
            _error(findings, "variant-package-context-mismatch", f"counterfactual_runs:{variant_kind}", "A controlled life-path variant must preserve package_context_id.")
        variant_selection = variant_workbench.get("selection") if isinstance(variant_workbench.get("selection"), dict) else {}
        if variant_selection.get("locked_fact_boundary_sha256") != baseline_selection.get("locked_fact_boundary_sha256"):
            _error(findings, "variant-fact-boundary-mismatch", f"counterfactual_runs:{variant_kind}", "The present fact boundary must remain fixed across the controlled path variant.")
        if variant_selection.get("locked_candidate_sha256") == baseline_selection.get("locked_candidate_sha256"):
            _error(findings, "variant-candidate-unchanged", f"counterfactual_runs:{variant_kind}", "A branch or node variant must bind different candidate content.")

        variant_runtime = variant_workbench.get("compiled_runtime") if isinstance(variant_workbench.get("compiled_runtime"), dict) else {}
        variant_refs_raw = variant_runtime.get("source_refs")
        variant_refs = {ref.strip() for ref in variant_refs_raw if isinstance(ref, str)} if isinstance(variant_refs_raw, list) else set()
        if variant_refs != set(run_evidence.get(variant_kind, {}).get("source_refs") or set()):
            _error(findings, "variant-source-closure-mismatch", f"counterfactual_runs:{variant_kind}.canonical_source_refs", "Run source refs must equal the exact audited variant runtime closure.")
        variant_artifacts = variant_runtime.get("artifact_files") if isinstance(variant_runtime.get("artifact_files"), list) else []
        expected_variant_inputs: set[Path] = set()
        _, resolved_root = roots
        for artifact in variant_artifacts:
            if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                supplied = Path(artifact["path"])
                expected_variant_inputs.add((supplied if supplied.is_absolute() else resolved_root / supplied).resolve())
        if expected_variant_inputs != set(run_input_sets.get(variant_kind, frozenset())):
            _error(findings, "variant-runtime-input-mismatch", f"counterfactual_runs:{variant_kind}.input_file_hashes", "Branch and node variants must consume exactly their own audited compiled runtime artifacts.")

        variant_candidate_id = variant_selection.get("selected_branch_id")
        variant_candidates = variant_workbench.get("candidates") if isinstance(variant_workbench.get("candidates"), list) else []
        variant_candidate = next(
            (candidate for candidate in variant_candidates if isinstance(candidate, dict) and candidate.get("id") == variant_candidate_id),
            {},
        )
        variant_node_ids = {
            node.get("id")
            for node in variant_candidate.get("causal_spine", [])
            if isinstance(node, dict) and isinstance(node.get("id"), str)
        }
        if variant_kind == "branch_swap":
            if variant_candidate_id == baseline_candidate_id:
                _error(findings, "branch-swap-unchanged", f"counterfactual_runs:{variant_kind}", "branch_swap must select a different author-locked candidate branch.")
        else:
            ablated_ref = context.get("ablated_source_ref")
            match = SOURCE_REF_PATTERN.fullmatch(ablated_ref.strip()) if isinstance(ablated_ref, str) else None
            expected_prefix = f"life-path:{baseline_candidate_id}/"
            if match is None or not ablated_ref.startswith(expected_prefix):
                _error(findings, "invalid-ablated-source-ref", f"counterfactual_runs:{variant_kind}.variant_context", "causal_node_ablation must name one node in the baseline locked branch.")
            else:
                ablated_node_id = ablated_ref.rsplit("/", 1)[1]
                expected_ablation_candidate = copy.deepcopy(baseline_candidate)
                expected_ablation_candidate["causal_spine"] = [
                    node
                    for node in expected_ablation_candidate.get("causal_spine", [])
                    if not (isinstance(node, dict) and node.get("id") == ablated_node_id)
                ]
                if ablated_node_id not in baseline_node_ids or variant_candidate_id != baseline_candidate_id:
                    _error(findings, "invalid-ablated-source-ref", f"counterfactual_runs:{variant_kind}.variant_context", "The ablated node must exist in, and preserve the identity of, the baseline locked branch.")
                elif variant_node_ids != baseline_node_ids - {ablated_node_id}:
                    _error(findings, "node-ablation-shape-mismatch", f"counterfactual_runs:{variant_kind}", "The ablation variant must remove exactly the named causal node ID without adding or dropping other node IDs.")
                elif candidate_sha256(variant_candidate) != candidate_sha256(expected_ablation_candidate):
                    _error(
                        findings,
                        "node-ablation-content-mismatch",
                        f"counterfactual_runs:{variant_kind}",
                        "The ablation candidate must equal the baseline candidate with only the declared causal node removed; premise, surviving nodes, and all other candidate content must remain unchanged.",
                    )

    occupation_run = runs_by_kind.get("occupational_context_swap", {})
    occupation_context = occupation_run.get("variant_context") if isinstance(occupation_run.get("variant_context"), dict) else {}
    if roots is not None:
        variant_context_value = occupation_context.get("occupational_context_file")
        variant_context_ref, variant_context_hash = _descriptor_parts(variant_context_value)
        variant_occupation_path = _validate_file_binding(
            variant_context_ref,
            variant_context_hash,
            "counterfactual_runs:occupational_context_swap.variant_context.occupational_context_file",
            roots,
            findings,
        )
        expected_occupation_inputs = set(compile_output_paths)
        if variant_occupation_path is not None:
            expected_occupation_inputs.add(variant_occupation_path)
        if set(run_input_sets.get("occupational_context_swap", frozenset())) != expected_occupation_inputs:
            _error(findings, "occupation-runtime-input-mismatch", "counterfactual_runs:occupational_context_swap.input_file_hashes", "The occupation swap must preserve baseline compiled life assets and replace only the hashed occupational-context input.")
        expected_baseline_inputs = set(compile_output_paths)
        if baseline_occupation_path is not None:
            expected_baseline_inputs.add(baseline_occupation_path)
        if set(run_input_sets.get("locked_baseline", frozenset())) != expected_baseline_inputs:
            _error(findings, "baseline-runtime-input-mismatch", "counterfactual_runs:locked_baseline.input_file_hashes", "The baseline must consume the audited compile outputs plus its hashed occupational context.")
        if variant_occupation_path is not None and baseline_occupation_path is not None and _same_file(variant_occupation_path, baseline_occupation_path):
            _error(findings, "occupation-context-unchanged", "counterfactual_runs:occupational_context_swap.variant_context", "The occupational-context swap requires a different file, not a hard link to baseline context.")
    if occupation_context.get("preserved_candidate_sha256") != baseline_selection.get("locked_candidate_sha256"):
        _error(findings, "occupation-candidate-not-preserved", "counterfactual_runs:occupational_context_swap.variant_context", "The occupation-only variant must preserve the locked life-path candidate hash.")
    if run_evidence.get("occupational_context_swap", {}).get("source_refs") != compile_source_refs:
        _error(findings, "occupation-source-closure-mismatch", "counterfactual_runs:occupational_context_swap.canonical_source_refs", "The occupation-only variant must preserve the baseline life-path source closure.")

    dialogue_run = runs_by_kind.get("dialogue_deletion", {})
    dialogue_context = dialogue_run.get("variant_context") if isinstance(dialogue_run.get("variant_context"), dict) else {}
    if dialogue_context.get("source_run_kind") != "locked_baseline" or dialogue_context.get("source_output_sha256") != baseline_run.get("output_sha256"):
        _error(findings, "dialogue-deletion-source-mismatch", "counterfactual_runs:dialogue_deletion.variant_context", "Dialogue deletion must bind the actual locked-baseline run and output hash.")
    if not _positive_int(dialogue_context.get("removed_dialogue_units")):
        _error(findings, "missing-dialogue-deletion-count", "counterfactual_runs:dialogue_deletion.variant_context", "Record a positive count of removed or nonverbally replaced dialogue units.")
    baseline_output_path = next(
        (
            path
            for path in output_paths
            if baseline_run.get("output_sha256") is not None and file_sha256(path) == baseline_run.get("output_sha256")
        ),
        None,
    )
    if baseline_output_path is not None and set(run_input_sets.get("dialogue_deletion", frozenset())) != {baseline_output_path}:
        _error(
            findings,
            "dialogue-deletion-input-mismatch",
            "counterfactual_runs:dialogue_deletion.input_file_hashes",
            "The deletion pass must consume only the exact baseline run output as its hashed input.",
        )
    if run_evidence.get("dialogue_deletion", {}).get("source_refs") != baseline_run.get("source_refs"):
        _error(findings, "dialogue-source-closure-mismatch", "counterfactual_runs:dialogue_deletion.canonical_source_refs", "Dialogue deletion must preserve the baseline life-path source closure.")

    traceability = payload.get("traceability") if isinstance(payload.get("traceability"), dict) else {}
    visible_deltas = traceability.get("visible_deltas")
    covered_variants: set[str] = set()
    if not isinstance(visible_deltas, list) or not visible_deltas:
        _error(findings, "traceability-incomplete", "traceability.visible_deltas", "A passing record requires completed visible-delta traceability.")
    else:
        for index, delta in enumerate(visible_deltas, start=1):
            location = f"traceability.visible_deltas[{index}]"
            if not isinstance(delta, dict):
                _error(findings, "invalid-visible-delta", location, "Each visible delta must be a mapping.")
                continue
            run_kind = delta.get("run_kind")
            if run_kind not in RUN_KINDS:
                _error(findings, "invalid-delta-run-kind", location, "visible delta must name a staged run kind.")
            elif run_kind in VARIANT_RUN_KINDS:
                covered_variants.add(run_kind)
            if not _nonempty_string(delta.get("observed_delta")):
                _error(findings, "missing-observed-delta", location, "Each traceability entry requires an observed_delta.")
            variant_run = run_evidence.get(run_kind, {})
            trace_bindings = {
                "baseline_task_id": baseline_run.get("task_id"),
                "baseline_output_sha256": baseline_run.get("output_sha256"),
                "variant_task_id": variant_run.get("task_id"),
                "variant_output_sha256": variant_run.get("output_sha256"),
            }
            for field, expected in trace_bindings.items():
                if delta.get(field) != expected:
                    _error(
                        findings,
                        "trace-run-binding-mismatch",
                        location,
                        f"{field} must bind the actual staged run value {expected!r}.",
                    )
            refs = delta.get("locked_source_refs")
            if not isinstance(refs, list) or not refs or not all(
                isinstance(ref, str) and SOURCE_REF_PATTERN.fullmatch(ref.strip()) for ref in refs
            ):
                _error(
                    findings,
                    "invalid-locked-source-refs",
                    location,
                    "Each traceability entry requires canonical locked life-path source refs.",
                )
            else:
                allowed_trace_refs = set(baseline_run.get("source_refs") or set()) | set(
                    variant_run.get("source_refs") or set()
                )
            if (
                isinstance(refs, list)
                and refs
                and all(isinstance(ref, str) and SOURCE_REF_PATTERN.fullmatch(ref.strip()) for ref in refs)
                and not {ref.strip() for ref in refs}.issubset(allowed_trace_refs)
            ):
                _error(
                    findings,
                    "trace-source-outside-compile",
                    location,
                    "A visible delta may cite only source refs present in its baseline or exact variant runtime closure.",
                )
            if delta.get("traceable") is not True:
                _error(findings, "untraceable-delta", location, "Every claimed visible delta must be recorded as traceable.")
    missing_variants = VARIANT_RUN_KINDS - covered_variants
    if missing_variants:
        _error(
            findings,
            "traceability-incomplete",
            "traceability.visible_deltas",
            f"Missing completed traceability for variant runs: {sorted(missing_variants)}.",
        )
    explicit_leaks = traceability.get("explicit_branch_leaks")
    if explicit_leaks != []:
        _error(
            findings,
            "explicit-branch-leak",
            "traceability.explicit_branch_leaks",
            "behavior_pass=true requires an explicitly recorded empty leak list.",
        )
    if not _review_passed(traceability.get("semantic_branch_leak_review")):
        _error(
            findings,
            "semantic-review-not-passed",
            "traceability.semantic_branch_leak_review",
            "The semantic branch-leak review must be recorded as passed.",
        )

    blind_review = payload.get("blind_review") if isinstance(payload.get("blind_review"), dict) else {}
    for field in ("randomized_output_ids", "reviewer_ids", "repair_reasons"):
        value = blind_review.get(field)
        if not isinstance(value, list) or not value or not all(_nonempty_string(item) for item in value):
            _error(
                findings,
                "empty-blind-review-field",
                f"blind_review.{field}",
                f"A passing record requires non-empty string evidence in {field}.",
            )
    randomized_output_ids_raw = blind_review.get("randomized_output_ids")
    randomized_output_ids = (
        [item.strip() for item in randomized_output_ids_raw if _nonempty_string(item)]
        if isinstance(randomized_output_ids_raw, list)
        else []
    )
    expected_blind_output_ids = {
        item.get("blind_output_id")
        for item in run_evidence.values()
        if _nonempty_string(item.get("blind_output_id"))
    }
    if len(randomized_output_ids) != len(set(randomized_output_ids)):
        _error(findings, "duplicate-randomized-output-id", "blind_review.randomized_output_ids", "Randomized output IDs must be unique.")
    if set(randomized_output_ids) != expected_blind_output_ids:
        _error(
            findings,
            "blind-output-binding-mismatch",
            "blind_review.randomized_output_ids",
            "Randomized blind IDs must map one-to-one to the five actual staged run outputs.",
        )
    for field in (
        "actor_playability",
        "character_identifiability",
        "nonverbal_replacement",
        "relationship_truth",
        "read_aloud_naturalness",
    ):
        value = blind_review.get(field)
        records_are_structured = isinstance(value, list) and bool(value) and all(
            isinstance(item, dict) and _nonempty_string(item.get("output_id")) for item in value
        )
        reviewed_ids = {
            item["output_id"].strip()
            for item in value
            if isinstance(item, dict) and _nonempty_string(item.get("output_id"))
        } if isinstance(value, list) else set()
        evidence_present = records_are_structured and all(
            any(
                (candidate is True if isinstance(candidate, bool) else _has_content(candidate))
                for key, candidate in item.items()
                if key != "output_id"
            )
            for item in value
        )
        review_outcomes_passed = records_are_structured and all(
            _review_item_passed(item) for item in value
        )
        if not records_are_structured or reviewed_ids != expected_blind_output_ids or not evidence_present:
            _error(
                findings,
                "empty-blind-review-field",
                f"blind_review.{field}",
                f"A passing record requires evidence-bearing review mappings covering every actual blind output ID in {field}.",
            )
        elif not review_outcomes_passed:
            _error(
                findings,
                "blind-review-verdict-not-passed",
                f"blind_review.{field}",
                "behavior_pass=true requires every reviewed output to carry an explicit positive verdict/status; a numeric rating may accompany that verdict but cannot define its own pass threshold. Failures, rejections, nonpositive ratings, and unparseable outcomes fail the hard gate.",
            )


def audit_record(payload: dict[str, Any], record_path: Path) -> list[Finding]:
    """Audit a loaded record relative to the YAML record's location."""
    findings: list[Finding] = []
    if not isinstance(payload, dict):
        return [Finding("invalid-record", "error", "record", "The record must be a mapping.")]
    behavior_pass = _audit_basic_schema(payload, findings)
    if behavior_pass:
        _audit_passing_record(payload, _lexical_absolute(record_path), findings)
    return findings


def audit_file(path: Path) -> list[Finding]:
    return audit_record(load_record(path), path)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Staged evaluation result YAML file")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        findings = audit_file(args.record)
    except (OSError, UnicodeError, ValueError) as exc:
        if args.as_json:
            print(json.dumps({"input_error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR input: {exc}")
        return 2
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
        print(f"Errors: {sum(item.severity == 'error' for item in findings)}")
    else:
        print(
            "Staged evaluation record integrity valid. "
            "This does not verify execution truth, review independence, or artistic quality."
        )
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
