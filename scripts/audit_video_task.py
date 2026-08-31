#!/usr/bin/env python3
"""Audit provider-neutral video-task structure, timing, modes, locks, and borrowing.

This tool checks declared contracts. It cannot verify provider behavior, visual
quality, identity fidelity, physical realism, or whether an external generation ran.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - JSON remains usable without PyYAML.
    yaml = None


HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
PRIMARY_MODES = {"generation", "exact", "long", "extension", "edit", "transition", "multi_panel"}
CONDITIONING_ORIGINS = {"text_only", "image_conditioned", "video_conditioned", "mixed"}
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


def _finite_number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


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
        raise ValueError("Supported task formats are .json, .yaml, and .yml")
    if not isinstance(payload, dict):
        raise ValueError("Video task must be a mapping")
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


def _safe_local_media_path(value: Any, media_root: Optional[Path], location: str, findings: list[Finding]) -> Optional[Path]:
    """Resolve one contract-local media file without accepting path escape or links."""
    if not isinstance(value, str) or not value.strip():
        _error(findings, "invalid-local-media-file", location, "local_file must be a non-empty relative path.")
        return None
    if media_root is None:
        _error(findings, "missing-media-root", location, "Local media binding requires an explicit media root.")
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        _error(findings, "unsafe-local-media-path", location, "local_file must stay below the supplied media root.")
        return None
    try:
        root = media_root.resolve(strict=True)
        resolved = (root / candidate).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        _error(findings, "unsafe-local-media-path", location, "local_file is absent or resolves outside the supplied media root.")
        return None
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            _error(findings, "symlinked-local-media", location, "local_file and its parents must not be symlinks.")
            return None
    try:
        if not stat.S_ISREG(resolved.stat().st_mode):
            _error(findings, "nonregular-local-media", location, "local_file must resolve to a regular file.")
            return None
    except OSError:
        _error(findings, "unreadable-local-media", location, "local_file cannot be stat'ed safely.")
        return None
    return resolved


def _audit_source_asset(
    source: Any,
    location: str,
    findings: list[Finding],
    *,
    media_root: Optional[Path],
) -> Optional[tuple[str, str]]:
    """Return a source ref only if the media itself has an immutable binding."""
    ref = _asset_ref(source, location, findings)
    if ref is None or not isinstance(source, dict):
        return None
    local_present = any(key in source and _has_content(source.get(key)) for key in ("local_file", "sha256"))
    provider_present = any(key in source and _has_content(source.get(key)) for key in ("provider_asset_id", "provider_asset_version"))
    if local_present and provider_present:
        _error(findings, "ambiguous-source-asset-binding", location, "Use either local_file plus sha256 or immutable provider asset ID plus version, not both.")
        return None
    if local_present:
        if not _is_hash(source.get("sha256")):
            _error(findings, "invalid-local-media-hash", location, "Local source asset requires a 64-hex sha256.")
            return None
        path = _safe_local_media_path(source.get("local_file"), media_root, location, findings)
        if path is None:
            return None
        actual = _sha256(path)
        if actual.casefold() != str(source["sha256"]).strip().casefold():
            _error(findings, "local-media-hash-mismatch", location, "local_file SHA-256 does not match the asset-contract binding.")
            return None
        return ref
    if provider_present:
        if not _has_content(source.get("provider_asset_id")) or not _has_content(source.get("provider_asset_version")):
            _error(findings, "incomplete-provider-media-binding", location, "Provider source asset requires both provider_asset_id and immutable provider_asset_version.")
            return None
        return ref
    _error(findings, "missing-immutable-source-binding", location, "Source asset requires local_file plus sha256 or provider_asset_id plus provider_asset_version; file_or_slot alone is not a binding.")
    return None


def _asset_ref(value: Any, location: str, findings: list[Finding]) -> Optional[tuple[str, str]]:
    if not isinstance(value, dict) or not _has_content(value.get("asset_id")) or not _valid_revision(value.get("revision")):
        _error(findings, "invalid-asset-ref", location, "Asset reference requires asset_id and revision.")
        return None
    return str(value["asset_id"]).strip(), str(value["revision"]).strip()


def _interval(value: Any, location: str, findings: list[Finding]) -> Optional[tuple[float, float]]:
    if not isinstance(value, dict):
        _error(findings, "invalid-interval", location, "Interval must be a mapping with start_s and end_s.")
        return None
    start = _finite_number(value.get("start_s"))
    end = _finite_number(value.get("end_s"))
    if start is None or end is None or start < 0 or end <= start:
        _error(findings, "invalid-interval", location, "Interval requires finite 0 <= start_s < end_s.")
        return None
    return start, end


def _interval_values(value: Any) -> Optional[tuple[float, float]]:
    if not isinstance(value, dict):
        return None
    start = _finite_number(value.get("start_s"))
    end = _finite_number(value.get("end_s"))
    if start is None or end is None or start < 0 or end <= start:
        return None
    return start, end


def _visual_index(visual_bible: Any, findings: list[Finding]) -> set[tuple[str, str]]:
    if not isinstance(visual_bible, dict) or not isinstance(visual_bible.get("assets"), list):
        _error(findings, "invalid-visual-bible", "visual_bible", "Visual bible must contain an assets list.")
        return set()
    result: set[tuple[str, str]] = set()
    for position, asset in enumerate(visual_bible["assets"], start=1):
        location = f"visual_bible.assets[{position}]"
        ref = _asset_ref(asset, location, findings)
        if ref is None:
            continue
        if ref in result:
            _error(findings, "duplicate-visual-asset-revision", location, f"Duplicate visual asset revision {ref[0]}@{ref[1]}.")
        result.add(ref)
    return result


def _audit_lock_groups(
    groups: Any,
    findings: list[Finding],
    *,
    visual_assets: Optional[set[tuple[str, str]]] = None,
) -> None:
    if not isinstance(groups, dict):
        _error(findings, "invalid-global-locks", "global_locks", "global_locks must be a mapping.")
        return
    seen_ids: set[str] = set()
    values: dict[tuple[str, str, str, str], Any] = {}
    for category in LOCK_CATEGORIES:
        group = groups.get(category)
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
                _error(findings, "exempt-lock-has-entries", location, "not_applicable must not contain lock entries.")
            continue
        if status == "locked" and not entries:
            _error(findings, "empty-locked-category", location, "locked status requires at least one exact entry.")
        for position, entry in enumerate(entries, start=1):
            entry_location = f"{location}.entries[{position}]"
            if not isinstance(entry, dict):
                _error(findings, "invalid-lock-entry", entry_location, "Lock entry must be a mapping.")
                continue
            lock_id = entry.get("lock_id")
            if not _has_content(lock_id):
                _error(findings, "missing-lock-id", entry_location, "lock_id is required.")
            elif str(lock_id) in seen_ids:
                _error(findings, "duplicate-lock-id", entry_location, f"Duplicate lock_id: {lock_id}.")
            else:
                seen_ids.add(str(lock_id))
            ref = _asset_ref(entry.get("target_ref"), f"{entry_location}.target_ref", findings)
            prop = entry.get("property")
            value = entry.get("value")
            if not _has_content(prop) or not _has_content(value):
                _error(findings, "incomplete-lock-entry", entry_location, "Lock entry requires property and value.")
            if ref is None or not _has_content(prop) or not _has_content(value):
                continue
            if visual_assets is not None and ref not in visual_assets:
                _error(findings, "unknown-lock-asset-revision", entry_location, f"No visual-bible asset revision {ref[0]}@{ref[1]}.")
            key = (category, ref[0], ref[1], str(prop).strip())
            if key in values and values[key] != value:
                _error(findings, "lock-conflict", entry_location, f"Conflicting values for {ref[0]}@{ref[1]} {prop}.")
            else:
                values[key] = value


def _lock_group_signature(groups: Any, category: str) -> Optional[tuple[str, tuple[str, ...]]]:
    if not isinstance(groups, dict) or not isinstance(groups.get(category), dict):
        return None
    group = groups[category]
    status = group.get("status")
    entries = group.get("entries")
    if not isinstance(status, str) or not isinstance(entries, list):
        return None
    normalized = tuple(
        sorted(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
            for item in entries
            if isinstance(item, dict)
        )
    )
    return status, normalized


def _storyboard_shot_intervals(storyboard: Any, findings: list[Finding]) -> Optional[dict[str, tuple[float, float]]]:
    if storyboard is None:
        return None
    if not isinstance(storyboard, dict) or not isinstance(storyboard.get("shots"), list):
        _error(findings, "invalid-storyboard-for-video-task", "storyboard", "Storyboard must provide a shots list for panel validation.")
        return {}
    result: dict[str, tuple[float, float]] = {}
    for position, shot in enumerate(storyboard["shots"], start=1):
        location = f"storyboard.shots[{position}]"
        if not isinstance(shot, dict) or not _has_content(shot.get("shot_id")):
            _error(findings, "invalid-storyboard-shot", location, "Storyboard shot requires shot_id.")
            continue
        shot_id = str(shot["shot_id"]).strip()
        interval = _interval_values({"start_s": shot.get("start_s"), "end_s": shot.get("end_s")})
        if interval is None:
            _error(findings, "invalid-storyboard-shot", location, "Storyboard shot requires a valid interval.")
            continue
        if shot_id in result:
            _error(findings, "duplicate-storyboard-shot-id", location, f"Duplicate storyboard shot_id: {shot_id}.")
            continue
        result[shot_id] = interval
    return result


def _audit_asset_contract(
    contract: Any,
    reference_uses: Any,
    findings: list[Finding],
    *,
    media_root: Optional[Path],
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    uses_present = isinstance(reference_uses, list) and bool(reference_uses)
    if contract is None:
        if uses_present:
            _error(findings, "missing-asset-contract", "reference_uses", "Reference use requires a supplied deny-by-default asset contract.")
        return {}, set()
    if not isinstance(contract, dict):
        _error(findings, "invalid-asset-contract", "asset_contract", "Asset contract must be a mapping.")
        return {}, set()
    modern_contract = contract.get("schema_version") == 2 or (
        contract.get("schema_version", 1) == 1 and contract.get("contract_version") == 2
    )
    if not modern_contract:
        if uses_present:
            _error(findings, "legacy-asset-contract-unscoped", "asset_contract", "Legacy asset contracts cannot authorize schema-v2 reference uses.")
        return {}, set()
    if contract.get("default_borrow_policy") != "deny":
        _error(findings, "borrow-policy-not-deny", "asset_contract.default_borrow_policy", "default_borrow_policy must be deny.")
    source_assets = contract.get("source_assets")
    source_index: set[tuple[str, str]] = set()
    if not isinstance(source_assets, list):
        _error(findings, "invalid-source-assets", "asset_contract.source_assets", "source_assets must be a list.")
    else:
        for position, source in enumerate(source_assets, start=1):
            ref = _audit_source_asset(
                source,
                f"asset_contract.source_assets[{position}]",
                findings,
                media_root=media_root,
            )
            if ref:
                if ref in source_index:
                    _error(findings, "duplicate-source-asset", f"asset_contract.source_assets[{position}]", f"Duplicate source asset {ref[0]}@{ref[1]}.")
                source_index.add(ref)
    authorizations = contract.get("borrow_authorizations")
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(authorizations, list):
        _error(findings, "invalid-borrow-authorizations", "asset_contract.borrow_authorizations", "borrow_authorizations must be a list.")
        return result, source_index
    for position, authorization in enumerate(authorizations, start=1):
        location = f"asset_contract.borrow_authorizations[{position}]"
        if not isinstance(authorization, dict):
            _error(findings, "invalid-borrow-authorization", location, "Borrow authorization must be a mapping.")
            continue
        auth_id = authorization.get("authorization_id")
        if not _has_content(auth_id):
            _error(findings, "missing-authorization-id", location, "authorization_id is required.")
            continue
        auth_key = str(auth_id).strip()
        if auth_key in result:
            _error(findings, "duplicate-authorization-id", location, f"Duplicate authorization_id: {auth_key}.")
        ref = _asset_ref(authorization.get("source_ref"), f"{location}.source_ref", findings)
        if ref and ref not in source_index:
            _error(findings, "authorization-unknown-source", location, f"Authorization source {ref[0]}@{ref[1]} is not registered.")
        for field in ("borrow", "targets", "preserve", "exclude"):
            if not isinstance(authorization.get(field), list):
                _error(findings, "invalid-authorization-field", location, f"{field} must be a list.")
        if isinstance(authorization.get("borrow"), list) and not authorization["borrow"]:
            _error(findings, "empty-borrow-authorization", location, "borrow must name at least one property.")
        if isinstance(authorization.get("targets"), list) and not authorization["targets"]:
            _error(findings, "empty-authorization-targets", location, "targets must name at least one target.")
        _interval(authorization.get("interval"), f"{location}.interval", findings)
        result[auth_key] = authorization
    return result, source_index


def _audit_reference_uses(
    uses: Any,
    authorizations: dict[str, dict[str, Any]],
    findings: list[Finding],
    *,
    output_duration: Optional[float],
) -> None:
    if not isinstance(uses, list):
        _error(findings, "invalid-reference-uses", "reference_uses", "reference_uses must be a list.")
        return
    seen_ids: set[str] = set()
    for position, use in enumerate(uses, start=1):
        location = f"reference_uses[{position}]"
        if not isinstance(use, dict):
            _error(findings, "invalid-reference-use", location, "Reference use must be a mapping.")
            continue
        use_id = use.get("use_id")
        if not _has_content(use_id):
            _error(findings, "missing-reference-use-id", location, "use_id is required.")
        elif str(use_id) in seen_ids:
            _error(findings, "duplicate-reference-use-id", location, f"Duplicate use_id: {use_id}.")
        else:
            seen_ids.add(str(use_id))
        auth_id = use.get("authorization_id")
        authorization = authorizations.get(str(auth_id).strip()) if _has_content(auth_id) else None
        if authorization is None:
            _error(findings, "unauthorized-reference-use", location, "Reference use requires a matching authorization_id.")
        use_ref = _asset_ref(use.get("source_ref"), f"{location}.source_ref", findings)
        borrowed = use.get("borrow")
        targets = use.get("targets")
        if not isinstance(borrowed, list) or not borrowed:
            _error(findings, "empty-reference-borrow", location, "borrow must name at least one property.")
        if not isinstance(targets, list) or not targets:
            _error(findings, "empty-reference-targets", location, "targets must name at least one target.")
        interval = _interval(use.get("interval"), f"{location}.interval", findings)
        if interval and output_duration is not None and interval[1] > output_duration:
            _error(findings, "reference-interval-outside-output", location, "Reference interval exceeds output duration.")
        if authorization is None:
            continue
        auth_ref_value = authorization.get("source_ref")
        auth_ref = None
        if isinstance(auth_ref_value, dict) and _has_content(auth_ref_value.get("asset_id")) and _valid_revision(auth_ref_value.get("revision")):
            auth_ref = (str(auth_ref_value["asset_id"]).strip(), str(auth_ref_value["revision"]).strip())
        if use_ref and auth_ref and use_ref != auth_ref:
            _error(findings, "authorization-source-mismatch", location, "Reference source differs from its authorization.")
        if isinstance(borrowed, list) and not set(map(str, borrowed)).issubset(set(map(str, authorization.get("borrow", [])))):
            _error(findings, "borrow-exceeds-authorization", location, "Reference use borrows properties not named by its authorization.")
        if isinstance(targets, list) and not set(map(str, targets)).issubset(set(map(str, authorization.get("targets", [])))):
            _error(findings, "target-exceeds-authorization", location, "Reference use targets elements not named by its authorization.")
        auth_interval_value = authorization.get("interval")
        if isinstance(auth_interval_value, dict):
            auth_start = _finite_number(auth_interval_value.get("start_s"))
            auth_end = _finite_number(auth_interval_value.get("end_s"))
            if interval and auth_start is not None and auth_end is not None and (interval[0] < auth_start or interval[1] > auth_end):
                _error(findings, "interval-exceeds-authorization", location, "Reference interval exceeds its authorization.")


def _require_fields(mapping: Any, fields: tuple[str, ...], location: str, findings: list[Finding]) -> bool:
    if not isinstance(mapping, dict):
        _error(findings, "invalid-mode-contract", location, "Mode contract must be a mapping.")
        return False
    valid = True
    for field in fields:
        if not _has_content(mapping.get(field)):
            _error(findings, "incomplete-mode-contract", location, f"Mode contract requires {field}.")
            valid = False
    return valid


def _valid_reference_uses(
    uses: Any,
    authorizations: dict[str, dict[str, Any]],
    *,
    output_duration: Optional[float],
) -> dict[str, dict[str, Any]]:
    if not isinstance(uses, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for use in uses:
        if not isinstance(use, dict) or not _has_content(use.get("use_id")) or not _has_content(use.get("authorization_id")):
            continue
        authorization = authorizations.get(str(use["authorization_id"]).strip())
        source = use.get("source_ref")
        if authorization is None or not isinstance(source, dict):
            continue
        auth_source = authorization.get("source_ref")
        if not isinstance(auth_source, dict):
            continue
        if not (_has_content(source.get("asset_id")) and _valid_revision(source.get("revision"))):
            continue
        ref = (str(source["asset_id"]).strip(), str(source["revision"]).strip())
        auth_ref = (
            str(auth_source.get("asset_id", "")).strip(),
            str(auth_source.get("revision", "")).strip(),
        )
        borrowed = use.get("borrow")
        targets = use.get("targets")
        interval = use.get("interval")
        parsed_interval = _interval_values(interval)
        auth_interval = _interval_values(authorization.get("interval"))
        if ref != auth_ref or not isinstance(borrowed, list) or not borrowed or not isinstance(targets, list) or not targets:
            continue
        if not set(map(str, borrowed)).issubset(set(map(str, authorization.get("borrow", [])))):
            continue
        if not set(map(str, targets)).issubset(set(map(str, authorization.get("targets", [])))):
            continue
        if parsed_interval is None or auth_interval is None:
            continue
        if parsed_interval[0] < auth_interval[0] or parsed_interval[1] > auth_interval[1]:
            continue
        if output_duration is not None and parsed_interval[1] > output_duration:
            continue
        result[str(use["use_id"]).strip()] = use
    return result


def _audit_mode_source(
    value: Any,
    location: str,
    findings: list[Finding],
    *,
    registered_sources: set[tuple[str, str]],
    valid_uses: dict[str, dict[str, Any]],
    required_role: str,
    required_interval: Optional[tuple[float, float]],
) -> Optional[tuple[str, str]]:
    ref = _asset_ref(value, location, findings)
    if ref is None:
        return None
    if ref not in registered_sources:
        _error(findings, "mode-source-unregistered", location, f"Mode source {ref[0]}@{ref[1]} is not registered in asset_contract.source_assets.")
    use_id = value.get("use_id") if isinstance(value, dict) else None
    use = valid_uses.get(str(use_id).strip()) if _has_content(use_id) else None
    if use is None:
        _error(findings, "mode-source-unauthorized", location, f"Mode source {ref[0]}@{ref[1]} requires a matching valid use_id and authorization.")
        return ref
    use_ref = use.get("source_ref")
    parsed_use_ref = None
    if isinstance(use_ref, dict) and _has_content(use_ref.get("asset_id")) and _valid_revision(use_ref.get("revision")):
        parsed_use_ref = (str(use_ref["asset_id"]).strip(), str(use_ref["revision"]).strip())
    if parsed_use_ref != ref:
        _error(findings, "mode-source-use-mismatch", location, "Mode source_ref does not match its named reference use.")
    normalized_borrow = {str(item).strip().casefold() for item in use.get("borrow", [])} if isinstance(use.get("borrow"), list) else set()
    if required_role.casefold() not in normalized_borrow:
        _error(findings, "mode-source-role-unauthorized", location, f"Reference use must authorize the mode role {required_role!r}.")
    normalized_targets = {str(item).strip().casefold() for item in use.get("targets", [])} if isinstance(use.get("targets"), list) else set()
    if "output" not in normalized_targets:
        _error(findings, "mode-source-target-unauthorized", location, "Mode source reference use must target OUTPUT.")
    use_interval = _interval_values(use.get("interval"))
    if required_interval is not None and (
        use_interval is None
        or use_interval[0] > required_interval[0]
        or use_interval[1] < required_interval[1]
    ):
        _error(findings, "mode-source-interval-unauthorized", location, "Reference use interval does not cover the mode source's consumed output span.")
    return ref


def _audit_conditioning(
    contract: dict[str, Any],
    location: str,
    findings: list[Finding],
    *,
    registered_sources: set[tuple[str, str]],
    valid_uses: dict[str, dict[str, Any]],
    duration: Optional[float],
) -> None:
    origin = contract.get("conditioning_origin")
    if origin not in CONDITIONING_ORIGINS:
        _error(findings, "invalid-conditioning-origin", location, f"conditioning_origin must be one of {sorted(CONDITIONING_ORIGINS)}.")
    refs = contract.get("conditioning_asset_refs")
    if not isinstance(refs, list):
        _error(findings, "invalid-conditioning-refs", location, "conditioning_asset_refs must be a list.")
        return
    if origin == "text_only" and refs:
        _error(findings, "text-only-has-conditioning-assets", location, "text_only conditioning cannot list media assets.")
    if origin in CONDITIONING_ORIGINS - {"text_only"} and not refs:
        _error(findings, "missing-conditioning-assets", location, f"{origin} requires at least one conditioning asset.")
    for position, ref in enumerate(refs, start=1):
        _audit_mode_source(
            ref,
            f"{location}.conditioning_asset_refs[{position}]",
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            required_role="conditioning",
            required_interval=(0.0, duration) if duration is not None else None,
        )


def _audit_mode_contract(
    mode: Any,
    contract: Any,
    findings: list[Finding],
    *,
    duration: Optional[float],
    tolerance: float,
    output_final_state: Any,
    timeline: list[tuple[str, float, float, Any, Any]],
    registered_sources: set[tuple[str, str]],
    valid_uses: dict[str, dict[str, Any]],
    storyboard_shots: Optional[dict[str, tuple[float, float]]],
) -> None:
    location = f"mode_contracts.{mode}"
    if not isinstance(contract, dict):
        _error(findings, "invalid-mode-contract", location, "Active mode contract must be a mapping.")
        return
    if mode in {"generation", "exact"}:
        _audit_conditioning(
            contract,
            location,
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            duration=duration,
        )
        if not _has_content(contract.get("ending_state")):
            _error(findings, "incomplete-mode-contract", location, "Generation contract requires ending_state.")
        elif _has_content(output_final_state) and contract.get("ending_state") != output_final_state:
            _error(findings, "generation-ending-state-conflict", location, "ending_state must equal output.final_state.")
        if mode == "exact":
            exact_duration = _finite_number(contract.get("exact_duration_s"))
            if exact_duration is None or exact_duration <= 0:
                _error(findings, "invalid-exact-duration", location, "exact_duration_s must be positive and finite.")
            elif duration is not None and abs(exact_duration - duration) > tolerance:
                _error(findings, "exact-duration-conflict", location, "exact_duration_s must equal output.duration_s.")
        return
    if mode == "long":
        if not _has_content(contract.get("continuity_strategy")):
            _error(findings, "incomplete-mode-contract", location, "Long mode requires continuity_strategy.")
        sections = contract.get("sections")
        if not isinstance(sections, list) or len(sections) < 2:
            _error(findings, "invalid-long-sections", location, "Long mode requires at least two ordered sections.")
            return
        parsed: list[tuple[float, float, Any, Any]] = []
        seen: set[str] = set()
        for position, section in enumerate(sections, start=1):
            item_location = f"{location}.sections[{position}]"
            if not isinstance(section, dict):
                _error(findings, "invalid-long-section", item_location, "Section must be a mapping.")
                continue
            section_id = section.get("section_id")
            if not _has_content(section_id) or str(section_id) in seen:
                _error(findings, "invalid-long-section-id", item_location, "section_id must be non-empty and unique.")
            else:
                seen.add(str(section_id))
            start = _finite_number(section.get("start_s"))
            end = _finite_number(section.get("end_s"))
            if start is None or end is None or start < 0 or end <= start:
                _error(findings, "invalid-long-section-time", item_location, "Section requires finite 0 <= start_s < end_s.")
                continue
            if not _has_content(section.get("state_in")) or not _has_content(section.get("state_out")):
                _error(findings, "missing-long-section-state", item_location, "Section requires state_in and state_out.")
            parsed.append((start, end, section.get("state_in"), section.get("state_out")))
        if parsed:
            if abs(parsed[0][0]) > tolerance:
                _error(findings, "long-section-nonzero-start", location, "Long sections must start at 0.")
            for previous, current in zip(parsed, parsed[1:]):
                if abs(previous[1] - current[0]) > tolerance:
                    _error(findings, "long-section-time-conflict", location, "Long sections must be contiguous.")
                if previous[3] != current[2]:
                    _error(findings, "long-section-state-conflict", location, "Adjacent long-section handoff states must match.")
            if duration is not None and abs(parsed[-1][1] - duration) > tolerance:
                _error(findings, "long-section-duration-conflict", location, "Long sections must cover output.duration_s.")
            if timeline and parsed[0][2] != timeline[0][3]:
                _error(findings, "long-section-opening-state-conflict", location, "The first long section state_in must equal the timeline opening state.")
            if _has_content(output_final_state) and parsed[-1][3] != output_final_state:
                _error(findings, "long-section-final-state-conflict", location, "The final long section state_out must equal output.final_state.")
        return
    if mode == "extension":
        _audit_mode_source(
            contract.get("source_clip_ref"),
            f"{location}.source_clip_ref",
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            required_role="extension_source",
            required_interval=(0.0, duration) if duration is not None else None,
        )
        direction = contract.get("direction")
        if direction not in {"before", "after"}:
            _error(findings, "invalid-extension-direction", location, "direction must be before or after.")
        source_boundary = contract.get("source_boundary")
        generated_boundary = contract.get("generated_boundary")
        if not isinstance(source_boundary, dict) or not _has_content(source_boundary.get("state")):
            _error(findings, "missing-extension-source-boundary", location, "source_boundary requires edge and state.")
        if not isinstance(generated_boundary, dict) or not _has_content(generated_boundary.get("state")):
            _error(findings, "missing-extension-generated-boundary", location, "generated_boundary requires edge and state.")
        expected_source_edge = "end" if direction == "after" else "start"
        expected_generated_edge = "start" if direction == "after" else "end"
        if isinstance(source_boundary, dict) and source_boundary.get("edge") != expected_source_edge:
            _error(findings, "extension-source-edge-conflict", location, f"{direction} extension requires source edge {expected_source_edge}.")
        if isinstance(generated_boundary, dict) and generated_boundary.get("edge") != expected_generated_edge:
            _error(findings, "extension-generated-edge-conflict", location, f"{direction} extension requires generated edge {expected_generated_edge}.")
        if isinstance(source_boundary, dict) and isinstance(generated_boundary, dict):
            if _has_content(source_boundary.get("state")) and source_boundary.get("state") != generated_boundary.get("state"):
                _error(findings, "extension-seam-state-conflict", location, "Source and generated boundary states must match at the seam.")
            if timeline and _has_content(generated_boundary.get("state")):
                generated_timeline_state = timeline[0][3] if direction == "after" else timeline[-1][4]
                if generated_boundary.get("state") != generated_timeline_state:
                    _error(findings, "extension-timeline-boundary-conflict", location, "Generated boundary state must equal the corresponding timeline boundary state.")
        seam = contract.get("seam")
        _require_fields(seam, ("causal_bridge_event", "preserve"), f"{location}.seam", findings)
        if isinstance(seam, dict) and (not isinstance(seam.get("preserve"), list) or not seam.get("preserve")):
            _error(findings, "empty-extension-preserve", f"{location}.seam", "Extension seam requires a non-empty preserve list.")
        return
    if mode == "edit":
        _audit_mode_source(
            contract.get("source_clip_ref"),
            f"{location}.source_clip_ref",
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            required_role="edit_source",
            required_interval=(0.0, duration) if duration is not None else None,
        )
        protected = contract.get("protected_elements")
        if not isinstance(protected, list) or not protected:
            _error(findings, "missing-edit-protected-elements", location, "Edit mode requires non-empty protected_elements.")
        targets = contract.get("targets")
        if not isinstance(targets, list) or not targets:
            _error(findings, "missing-edit-targets", location, "Edit mode requires at least one bounded target.")
            return
        for position, target in enumerate(targets, start=1):
            item_location = f"{location}.targets[{position}]"
            if not _require_fields(target, ("target_id", "operation", "interval", "preserve"), item_location, findings):
                continue
            interval = _interval(target.get("interval"), f"{item_location}.interval", findings)
            if interval and duration is not None and interval[1] > duration + tolerance:
                _error(findings, "edit-target-outside-output", item_location, "Edit target interval exceeds output.duration_s.")
            if not isinstance(target.get("preserve"), list) or not target["preserve"]:
                _error(findings, "empty-edit-target-preserve", item_location, "Each edit target requires a non-empty preserve list.")
        return
    if mode == "transition":
        source_a = _audit_mode_source(
            contract.get("source_a_ref"),
            f"{location}.source_a_ref",
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            required_role="transition_source_a",
            required_interval=_interval_values(contract.get("source_a_protected_interval")),
        )
        source_b = _audit_mode_source(
            contract.get("source_b_ref"),
            f"{location}.source_b_ref",
            findings,
            registered_sources=registered_sources,
            valid_uses=valid_uses,
            required_role="transition_source_b",
            required_interval=_interval_values(contract.get("source_b_protected_interval")),
        )
        if source_a and source_b and source_a == source_b:
            _error(findings, "transition-sources-not-distinct", location, "Transition requires distinct A and B source revisions.")
        for field in ("source_a_end_state", "source_b_start_state"):
            if not _has_content(contract.get(field)):
                _error(findings, "incomplete-transition-state", location, f"Transition requires {field}.")
        span_fields = ("source_a_protected_interval", "bridge_window", "source_b_protected_interval")
        spans: list[tuple[str, float, float]] = []
        for field in span_fields:
            interval = contract.get(field)
            _interval(interval, f"{location}.{field}", findings)
            if isinstance(interval, dict):
                start = _finite_number(interval.get("start_s"))
                end = _finite_number(interval.get("end_s"))
                if start is not None and end is not None and start >= 0 and end > start:
                    spans.append((field, start, end))
        if len(spans) == 3:
            if abs(spans[0][1]) > tolerance:
                _error(findings, "transition-span-nonzero-start", location, "The protected A span must start at output time 0.")
            for previous, current in zip(spans, spans[1:]):
                difference = current[1] - previous[2]
                if difference > tolerance:
                    _error(findings, "transition-span-gap", location, f"Gap of {difference:g}s between {previous[0]} and {current[0]}.")
                elif difference < -tolerance:
                    _error(findings, "transition-span-overlap", location, f"Overlap of {-difference:g}s between {previous[0]} and {current[0]}.")
            if duration is not None and abs(spans[-1][2] - duration) > tolerance:
                _error(findings, "transition-span-duration-conflict", location, "The protected B span must end at output.duration_s.")
            if timeline:
                a_boundary_states = [item[4] for item in timeline if abs(item[2] - spans[0][2]) <= tolerance]
                b_boundary_states = [item[3] for item in timeline if abs(item[1] - spans[2][1]) <= tolerance]
                if len(a_boundary_states) != 1 or contract.get("source_a_end_state") != a_boundary_states[0]:
                    _error(findings, "transition-a-state-conflict", location, "source_a_end_state must equal the timeline state at the end of A's protected interval.")
                if len(b_boundary_states) != 1 or contract.get("source_b_start_state") != b_boundary_states[0]:
                    _error(findings, "transition-b-state-conflict", location, "source_b_start_state must equal the timeline state at the start of B's protected interval.")
        bridge = contract.get("bridge")
        _require_fields(bridge, ("observable_cause", "observable_effect", "preserve_a", "preserve_b"), f"{location}.bridge", findings)
        if isinstance(bridge, dict):
            for field in ("preserve_a", "preserve_b"):
                if not isinstance(bridge.get(field), list) or not bridge[field]:
                    _error(findings, "empty-transition-preserve", f"{location}.bridge", f"{field} must be a non-empty list.")
        return
    if mode == "multi_panel":
        panels = contract.get("panels")
        if not isinstance(panels, list) or len(panels) < 2:
            _error(findings, "invalid-panel-mapping", location, "multi_panel requires at least two panel mappings.")
            return
        ids: set[str] = set()
        orders: set[int] = set()
        panel_intervals: list[tuple[str, float, float]] = []
        timeline_boundaries = {value for item in timeline for value in (item[1], item[2])}
        for position, panel in enumerate(panels, start=1):
            item_location = f"{location}.panels[{position}]"
            if not isinstance(panel, dict):
                _error(findings, "invalid-panel", item_location, "Panel mapping must be a mapping.")
                continue
            panel_id = panel.get("panel_id")
            order = panel.get("order")
            if not _has_content(panel_id) or str(panel_id) in ids:
                _error(findings, "invalid-panel-id", item_location, "panel_id must be non-empty and unique.")
            else:
                ids.add(str(panel_id))
            if isinstance(order, bool) or not isinstance(order, int) or order <= 0 or order in orders:
                _error(findings, "invalid-panel-order", item_location, "order must be a unique positive integer.")
            else:
                orders.add(order)
            _audit_mode_source(
                panel.get("source_ref"),
                f"{item_location}.source_ref",
                findings,
                registered_sources=registered_sources,
                valid_uses=valid_uses,
                required_role="panel_source",
                required_interval=_interval_values(panel.get("interval")),
            )
            if not _has_content(panel.get("role")):
                _error(findings, "missing-panel-role", item_location, "Panel requires role.")
            for field in ("binding_properties", "excluded_properties"):
                values = panel.get(field)
                if not isinstance(values, list) or not values:
                    _error(findings, "missing-panel-property-scope", item_location, f"Panel requires non-empty {field}.")
            shot_targets = panel.get("target_shot_ids")
            interval = panel.get("interval")
            if not isinstance(shot_targets, list) or not shot_targets or any(not _has_content(item) for item in shot_targets):
                _error(findings, "invalid-panel-shot-targets", item_location, "Panel requires one or more non-empty target_shot_ids.")
                normalized_shot_targets: list[str] = []
            else:
                normalized_shot_targets = [str(item).strip() for item in shot_targets]
            parsed_interval = _interval(interval, f"{item_location}.interval", findings)
            if parsed_interval:
                panel_intervals.append((str(panel_id), parsed_interval[0], parsed_interval[1]))
                if duration is not None and parsed_interval[1] > duration + tolerance:
                    _error(findings, "panel-interval-outside-output", item_location, "Panel interval exceeds output.duration_s.")
                if timeline_boundaries and not all(any(abs(edge - boundary) <= tolerance for boundary in timeline_boundaries) for edge in parsed_interval):
                    _error(findings, "panel-timeline-boundary-conflict", item_location, "Panel interval edges must align with output timeline boundaries.")
                if storyboard_shots is None:
                    _error(findings, "missing-storyboard-for-panel-validation", item_location, "Supply the bound storyboard to validate panel target_shot_ids.")
                elif normalized_shot_targets:
                    unknown_targets = [shot_id for shot_id in normalized_shot_targets if shot_id not in storyboard_shots]
                    if unknown_targets:
                        _error(findings, "unknown-panel-shot-target", item_location, f"Unknown storyboard shot targets: {unknown_targets}.")
                    else:
                        target_intervals = sorted((storyboard_shots[shot_id] for shot_id in normalized_shot_targets), key=lambda item: item[0])
                        for previous, current in zip(target_intervals, target_intervals[1:]):
                            if abs(previous[1] - current[0]) > tolerance:
                                _error(findings, "noncontiguous-panel-shot-targets", item_location, "A panel's target shots must form one contiguous interval.")
                        target_start = target_intervals[0][0]
                        target_end = target_intervals[-1][1]
                        if abs(parsed_interval[0] - target_start) > tolerance or abs(parsed_interval[1] - target_end) > tolerance:
                            _error(findings, "panel-shot-time-conflict", item_location, "Panel interval must equal the exact span of its target storyboard shots.")
        if orders and orders != set(range(1, len(panels) + 1)):
            _error(findings, "noncontiguous-panel-order", location, "Panel order must be contiguous from 1.")
        if len(panel_intervals) == len(panels):
            ordered_intervals = sorted(panel_intervals, key=lambda item: item[1])
            if abs(ordered_intervals[0][1]) > tolerance:
                _error(findings, "panel-coverage-nonzero-start", location, "Panel intervals must start at output time 0.")
            for previous, current in zip(ordered_intervals, ordered_intervals[1:]):
                difference = current[1] - previous[2]
                if difference > tolerance:
                    _error(findings, "panel-coverage-gap", location, f"Gap of {difference:g}s between panel intervals.")
                elif difference < -tolerance:
                    _error(findings, "panel-coverage-overlap", location, f"Overlap of {-difference:g}s between panel intervals.")
            if duration is not None and abs(ordered_intervals[-1][2] - duration) > tolerance:
                _error(findings, "panel-coverage-duration-conflict", location, "Panel intervals must end at output.duration_s.")
        additions = contract.get("unrequested_additions")
        if not isinstance(additions, dict) or additions.get("policy") != "deny":
            _error(findings, "invalid-panel-additions-policy", location, "multi_panel requires unrequested_additions.policy: deny.")
        else:
            categories = additions.get("categories")
            required = {"cta", "logo", "decorative_effects"}
            normalized = {str(item).strip().casefold() for item in categories} if isinstance(categories, list) else set()
            if not required.issubset(normalized):
                _error(findings, "incomplete-panel-additions-exclusions", location, "Denied unrequested additions must explicitly include cta, logo, and decorative_effects.")


def audit_document(
    payload: dict[str, Any],
    *,
    tolerance: float = 0.001,
    storyboard: Optional[dict[str, Any]] = None,
    storyboard_sha256: Optional[str] = None,
    continuity: Optional[dict[str, Any]] = None,
    continuity_sha256: Optional[str] = None,
    visual_bible: Optional[dict[str, Any]] = None,
    visual_bible_sha256: Optional[str] = None,
    asset_contract: Optional[dict[str, Any]] = None,
    asset_contract_sha256: Optional[str] = None,
    asset_media_root: Optional[Path] = None,
    allow_unbound_structure: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    if payload.get("schema_version") != 1:
        return [Finding("unsupported-schema-version", "error", "schema_version", "Supported video-task schema_version is 1.")]
    if not math.isfinite(tolerance) or tolerance < 0:
        return [Finding("invalid-tolerance", "error", "timeline", "Tolerance must be finite and nonnegative.")]
    if not allow_unbound_structure:
        for role, document in {
            "storyboard": storyboard,
            "continuity": continuity,
            "visual_bible": visual_bible,
            "asset_contract": asset_contract,
        }.items():
            if document is None:
                _error(findings, f"missing-supplied-{role.replace('_', '-')}", role, f"Production video task requires the actual bound {role} document.")
    if not _has_content(payload.get("video_task_id")):
        _error(findings, "missing-video-task-id", "video_task_id", "video_task_id is required.")
    if not _valid_revision(payload.get("revision")):
        _error(findings, "invalid-video-task-revision", "revision", "revision must be stable and non-empty.")
    depth = payload.get("delivery_depth")
    if depth not in {"concise", "professional"}:
        _error(findings, "invalid-delivery-depth", "delivery_depth", "delivery_depth must be concise or professional.")

    mode = payload.get("primary_mode")
    if not isinstance(mode, str) or mode not in PRIMARY_MODES:
        _error(findings, "invalid-primary-mode", "primary_mode", f"primary_mode must be exactly one of {sorted(PRIMARY_MODES)}.")

    provider = payload.get("provider")
    provider_name = None
    if not isinstance(provider, dict) or not _has_content(provider.get("name")):
        _error(findings, "invalid-provider", "provider", "provider requires a name; use provider_neutral before adaptation.")
    else:
        provider_name = str(provider["name"]).strip().casefold()
    verification = payload.get("capability_verification")
    if not isinstance(verification, dict):
        _error(findings, "invalid-capability-verification", "capability_verification", "capability_verification must be a mapping.")
    elif provider_name not in {None, "provider_neutral", "provider-neutral", "neutral"}:
        if verification.get("status") != "verified":
            _error(findings, "provider-capability-unverified", "capability_verification", "Provider-specific tasks require status: verified from the current interface or authoritative source.")
        for field in ("checked_at", "source"):
            if not _has_content(verification.get(field)):
                _error(findings, "incomplete-capability-verification", "capability_verification", f"Provider verification requires {field}.")
        if not _has_content(provider.get("model_version")):
            _error(findings, "missing-provider-model-version", "provider", "Provider-specific task requires the currently verified model_version.")
        supported = verification.get("supported_primary_modes")
        if not isinstance(supported, list) or mode not in supported:
            _error(findings, "primary-mode-not-verified", "capability_verification", "The selected primary mode is not recorded as currently supported.")
    if isinstance(asset_contract, dict):
        contract_provider = asset_contract.get("provider")
        if _has_content(contract_provider) and provider_name is not None and str(contract_provider).strip().casefold() != provider_name:
            _error(findings, "asset-contract-provider-conflict", "provider", "Task provider must match the bound asset-contract provider.")
        contract_model = asset_contract.get("model")
        task_model = provider.get("model_version") if isinstance(provider, dict) else None
        if _has_content(contract_model) and contract_model != task_model:
            _error(findings, "asset-contract-model-conflict", "provider.model_version", "Task model_version must match the bound asset-contract model.")
        contract_verification = asset_contract.get("capability_verification")
        if isinstance(contract_verification, dict) and contract_verification.get("status") == "verified":
            if not isinstance(verification, dict) or verification.get("status") != "verified":
                _error(findings, "asset-contract-capability-conflict", "capability_verification", "A verified provider asset contract requires a verified task capability record.")

    source_bindings = payload.get("source_bindings")
    if not isinstance(source_bindings, dict):
        _error(findings, "invalid-source-bindings", "source_bindings", "source_bindings must be a mapping.")
        source_bindings = {}
    expected_sources = {
        "storyboard": (storyboard, storyboard_sha256, "storyboard_id"),
        "continuity": (continuity, continuity_sha256, "continuity_id"),
        "visual_bible": (visual_bible, visual_bible_sha256, "visual_bible_id"),
        "asset_contract": (asset_contract, asset_contract_sha256, "contract_id"),
    }
    for role, (document, actual_hash, id_field) in expected_sources.items():
        binding = source_bindings.get(role)
        if binding is None:
            _error(findings, "missing-source-binding", "source_bindings", f"Missing {role} binding.")
            continue
        _audit_binding(binding, f"source_bindings.{role}", findings)
        if document is not None and not allow_unbound_structure and not actual_hash:
            _error(findings, f"missing-supplied-{role.replace('_', '-')}-hash", role, f"Production validation requires the actual {role} file SHA-256.")
        if document is not None and isinstance(binding, dict):
            if binding.get("artifact_id") != document.get(id_field):
                _error(findings, f"{role.replace('_', '-')}-id-mismatch", f"source_bindings.{role}", f"Bound {role} ID does not match supplied file.")
            if str(binding.get("revision")) != str(document.get("revision")):
                _error(findings, f"{role.replace('_', '-')}-revision-mismatch", f"source_bindings.{role}", f"Bound {role} revision does not match supplied file.")
            if actual_hash and _is_hash(binding.get("sha256")) and binding["sha256"].casefold() != actual_hash.casefold():
                _error(findings, f"{role.replace('_', '-')}-hash-mismatch", f"source_bindings.{role}", f"Bound {role} hash does not match supplied file.")

    if isinstance(continuity, dict):
        continuity_bindings = continuity.get("source_bindings")
        if not isinstance(continuity_bindings, dict):
            _error(findings, "invalid-continuity-source-bindings", "continuity.source_bindings", "Bound continuity must itself bind its storyboard and visual bible.")
            continuity_bindings = {}
        for role, document, actual_hash, id_field in (
            ("storyboard", storyboard, storyboard_sha256, "storyboard_id"),
            ("visual_bible", visual_bible, visual_bible_sha256, "visual_bible_id"),
        ):
            binding = continuity_bindings.get(role)
            location = f"continuity.source_bindings.{role}"
            if binding is None:
                _error(findings, "missing-continuity-source-binding", "continuity.source_bindings", f"Continuity is missing its {role} binding.")
                continue
            _audit_binding(binding, location, findings)
            if document is not None and isinstance(binding, dict):
                if binding.get("artifact_id") != document.get(id_field):
                    _error(findings, f"continuity-{role.replace('_', '-')}-id-mismatch", location, f"Continuity {role} ID does not match the supplied {role}.")
                if str(binding.get("revision")) != str(document.get("revision")):
                    _error(findings, f"continuity-{role.replace('_', '-')}-revision-mismatch", location, f"Continuity {role} revision does not match the supplied {role}.")
                if actual_hash and _is_hash(binding.get("sha256")) and binding["sha256"].casefold() != actual_hash.casefold():
                    _error(findings, f"continuity-{role.replace('_', '-')}-hash-mismatch", location, f"Continuity {role} hash does not match the supplied {role} file.")

    visual_assets = _visual_index(visual_bible, findings) if visual_bible is not None else None
    _audit_lock_groups(payload.get("global_locks"), findings, visual_assets=visual_assets)
    if isinstance(continuity, dict):
        for category in LOCK_CATEGORIES:
            task_signature = _lock_group_signature(payload.get("global_locks"), category)
            continuity_signature = _lock_group_signature(continuity.get("global_locks"), category)
            if task_signature != continuity_signature:
                _error(findings, "continuity-lock-conflict", f"global_locks.{category}", "Video task lock group must exactly inherit the bound continuity lock group.")

    output = payload.get("output")
    duration: Optional[float] = None
    if not isinstance(output, dict):
        _error(findings, "invalid-output-contract", "output", "output must be a mapping.")
    else:
        duration = _finite_number(output.get("duration_s"))
        if duration is None or duration <= 0:
            _error(findings, "invalid-output-duration", "output.duration_s", "duration_s must be positive and finite.")
            duration = None
        if not _has_content(output.get("aspect_ratio")):
            _error(findings, "missing-output-aspect-ratio", "output", "output requires aspect_ratio.")
        if not _has_content(output.get("final_state")):
            _error(findings, "missing-output-final-state", "output", "output requires final_state.")

    timeline = payload.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        _error(findings, "missing-timeline", "timeline", "An exact non-empty timeline is required.")
        timeline = []
    parsed: list[tuple[str, float, float, Any, Any]] = []
    segment_ids: set[str] = set()
    for position, segment in enumerate(timeline, start=1):
        location = f"timeline[{position}]"
        if not isinstance(segment, dict):
            _error(findings, "invalid-timeline-segment", location, "Timeline segment must be a mapping.")
            continue
        segment_id = segment.get("segment_id")
        if not _has_content(segment_id) or str(segment_id) in segment_ids:
            _error(findings, "invalid-segment-id", location, "segment_id must be non-empty and unique.")
        else:
            segment_ids.add(str(segment_id))
        start = _finite_number(segment.get("start_s"))
        end = _finite_number(segment.get("end_s"))
        if start is None or end is None or start < 0 or end <= start:
            _error(findings, "invalid-segment-time", location, "Timeline segment requires finite 0 <= start_s < end_s.")
            continue
        for field in ("observable_event", "state_in", "state_out"):
            if not _has_content(segment.get(field)):
                _error(findings, "incomplete-timeline-segment", location, f"Timeline segment requires {field}.")
        if depth == "professional":
            for field in ("camera", "performance", "sound"):
                if not _has_content(segment.get(field)):
                    _error(findings, "incomplete-professional-segment", location, f"Professional segment requires {field}.")
            if not isinstance(segment.get("asset_refs"), list):
                _error(findings, "invalid-segment-asset-refs", location, "Professional segment asset_refs must be a list.")
            else:
                for ref_position, ref in enumerate(segment["asset_refs"], start=1):
                    asset_ref = _asset_ref(ref, f"{location}.asset_refs[{ref_position}]", findings)
                    if asset_ref and visual_assets is not None and asset_ref not in visual_assets:
                        _error(findings, "unknown-segment-asset-revision", location, f"No visual-bible asset revision {asset_ref[0]}@{asset_ref[1]}.")
        parsed.append((str(segment_id), start, end, segment.get("state_in"), segment.get("state_out")))
    if parsed:
        if abs(parsed[0][1]) > tolerance:
            _error(findings, "timeline-nonzero-start", "timeline", "Timeline must start at 0.")
        for previous, current in zip(parsed, parsed[1:]):
            difference = current[1] - previous[2]
            if difference > tolerance:
                _error(findings, "timeline-gap", "timeline", f"Gap of {difference:g}s after {previous[0]}.")
            elif difference < -tolerance:
                _error(findings, "timeline-overlap", "timeline", f"Overlap of {-difference:g}s at {current[0]}.")
            if previous[4] != current[3]:
                _error(findings, "timeline-state-conflict", "timeline", f"State handoff from {previous[0]} to {current[0]} does not match.")
        if duration is not None and abs(parsed[-1][2] - duration) > tolerance:
            _error(findings, "timeline-duration-conflict", "timeline", "Timeline endpoint must equal output.duration_s.")
        if isinstance(output, dict) and _has_content(output.get("final_state")) and parsed[-1][4] != output.get("final_state"):
            _error(findings, "timeline-final-state-conflict", "timeline", "Final segment state_out must equal output.final_state.")

    storyboard_shots = _storyboard_shot_intervals(storyboard, findings)
    authorizations, registered_sources = _audit_asset_contract(
        asset_contract,
        payload.get("reference_uses"),
        findings,
        media_root=asset_media_root,
    )
    _audit_reference_uses(payload.get("reference_uses"), authorizations, findings, output_duration=duration)
    valid_uses = _valid_reference_uses(payload.get("reference_uses"), authorizations, output_duration=duration)

    contracts = payload.get("mode_contracts")
    if not isinstance(contracts, dict):
        _error(findings, "invalid-mode-contracts", "mode_contracts", "mode_contracts must be a mapping.")
    else:
        active_keys = [key for key, value in contracts.items() if _has_content(value)]
        if len(active_keys) != 1:
            _error(findings, "multiple-or-missing-mode-contract", "mode_contracts", "Exactly one non-empty mode contract is required.")
        elif active_keys[0] != mode:
            _error(findings, "primary-mode-contract-mismatch", "mode_contracts", "The only active mode contract must match primary_mode.")
        else:
            _audit_mode_contract(
                mode,
                contracts[mode],
                findings,
                duration=duration,
                tolerance=tolerance,
                output_final_state=output.get("final_state") if isinstance(output, dict) else None,
                timeline=parsed,
                registered_sources=registered_sources,
                valid_uses=valid_uses,
                storyboard_shots=storyboard_shots,
            )

    if not _has_content(payload.get("handoff_state")):
        _error(findings, "missing-task-handoff", "handoff_state", "handoff_state is required for the rendered result or next task.")
    elif isinstance(output, dict) and _has_content(output.get("final_state")) and payload.get("handoff_state") != output.get("final_state"):
        _error(findings, "task-handoff-conflict", "handoff_state", "handoff_state must equal output.final_state.")
    if not isinstance(payload.get("targeted_exclusions"), list):
        _error(findings, "invalid-targeted-exclusions", "targeted_exclusions", "targeted_exclusions must be a list.")
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--storyboard", type=Path)
    parser.add_argument("--continuity", type=Path)
    parser.add_argument("--visual-bible", type=Path)
    parser.add_argument("--asset-contract", type=Path)
    parser.add_argument(
        "--asset-media-root",
        type=Path,
        help="Root for relative local_file entries in asset-contract (defaults to asset-contract parent).",
    )
    parser.add_argument(
        "--allow-unbound-structure",
        action="store_true",
        help="Lint a planning draft without real upstream documents; not production validation.",
    )
    parser.add_argument("--tolerance", type=float, default=0.001)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_document(args.file)
        storyboard = load_document(args.storyboard) if args.storyboard else None
        continuity = load_document(args.continuity) if args.continuity else None
        visual_bible = load_document(args.visual_bible) if args.visual_bible else None
        asset_contract = load_document(args.asset_contract) if args.asset_contract else None
        asset_media_root = args.asset_media_root or (args.asset_contract.parent if args.asset_contract else None)
        findings = audit_document(
            payload,
            tolerance=args.tolerance,
            storyboard=storyboard,
            storyboard_sha256=_sha256(args.storyboard) if args.storyboard else None,
            continuity=continuity,
            continuity_sha256=_sha256(args.continuity) if args.continuity else None,
            visual_bible=visual_bible,
            visual_bible_sha256=_sha256(args.visual_bible) if args.visual_bible else None,
            asset_contract=asset_contract,
            asset_contract_sha256=_sha256(args.asset_contract) if args.asset_contract else None,
            asset_media_root=asset_media_root,
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
        print("Video-task structure valid. Provider behavior and rendered quality remain unverified.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
