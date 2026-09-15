#!/usr/bin/env python3
"""Audit life-path workbench structure, biography depth, locks, and downstream use."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the CLI dependency check
    yaml = None


DEFAULT_MINIMUM_CHINESE_CHARACTERS = None  # Depth is content-based; length is opt-in.
INTERNAL_REPEAT_CHUNK_HAN = 40
MAX_REPEATED_HAN_RATIO = 0.05

TOP_LEVEL_FIELDS = {
    "schema_version",
    "character_id",
    "package_context_id",
    "fact_boundary",
    "candidates",
    "selection",
    "deep_biography",
    "compiled_runtime",
}
FACT_BOUNDARY_FIELDS = {
    "author_locked_facts",
    "observable_traces",
    "self_reports_and_testimony",
    "rumors_misunderstandings_and_disputes",
    "author_preferences",
    "permitted_changes",
    "unknowns",
    "conflicts",
}
CANDIDATE_FIELDS = {
    "id",
    "status",
    "derived_from",
    "premise",
    "causal_spine",
    "feasibility",
    "creative_consequences",
}
NODE_FIELDS = {
    "id",
    "period",
    "environment_and_relationships",
    "event_or_pattern",
    "known_then",
    "constraints_and_options",
    "interpretation",
    "choice",
    "cost",
    "feedback",
    "belief_or_strategy_update",
    "unresolved_residue",
    "present_triggers",
}
COVERAGE_FIELDS = {
    "stage_id",
    "period",
    "source_node_refs",
    "environment_and_relationships",
    "interpretation_and_choices",
    "cost_feedback_updates",
    "current_residues",
}
CANDIDATE_STATUSES = {"candidate", "rejected", "selected", "locked"}
SELECTION_STATES = {"open", "selected", "locked"}
BIOGRAPHY_MODES = {"unclassified", "deep", "light", "off"}
BIOGRAPHY_STATUSES = {"not_started", "drafting", "ready", "not_required"}
BIOGRAPHY_APPROVAL_STATES = {"pending", "approved", "rejected", "not_required"}
SELECTION_FIELDS = {
    "state",
    "selected_branch_id",
    "rejected_branch_ids",
    "author_lock",
    "lock_revision",
    "locked_fact_boundary_sha256",
    "locked_candidate_sha256",
    "author_decision",
    "unlock_history",
}
BIOGRAPHY_FIELDS = {
    "mode",
    "status",
    "tier_author_decision",
    "biography_revision",
    "author_approval",
    "biography_file",
    "coverage_stages",
    "shared_history_refs",
    "shared_event_ids",
    "relationship_ledger_file",
}
RUNTIME_FIELDS = {
    "compiled_for_character_id",
    "compiled_for_package_context_id",
    "compiled_from_lock_revision",
    "compiled_from_fact_boundary_sha256",
    "compiled_from_candidate_sha256",
    "compiled_from_biography_revision",
    "compiled_from_biography_sha256",
    "source_refs",
    "artifact_files",
    "formal_scene_compilation",
}
OUTLINE_REVIEW_STATUSES = {"not_started", "clear", "conflict_pending", "resolved", "not_required"}
ARTIFACT_TYPES = {
    "character",
    "cognitive_resources",
    "speech_corpus",
    "memories",
    "relationship_ledger",
    "scene_contract",
    "turn_state",
    "beat_map",
    "screenplay",
    "storyboard",
    "continuity",
    "visual_bible",
    "asset_contract",
    "video_task",
    "video_prompt",
    "other_structured",
}
FORMAL_SCENE_ARTIFACT_TYPES = {
    "scene_contract",
    "turn_state",
    "beat_map",
    "screenplay",
    "storyboard",
    "continuity",
    "asset_contract",
    "video_task",
    "video_prompt",
}
STRUCTURED_ARTIFACT_TYPES = ARTIFACT_TYPES - {"screenplay", "video_prompt"}
PER_CHARACTER_ARTIFACT_TYPES = {"character", "cognitive_resources", "speech_corpus", "memories"}
MULTI_CHARACTER_ARTIFACT_TYPES = {
    "scene_contract",
    "turn_state",
    "beat_map",
    "storyboard",
    "continuity",
    "visual_bible",
    "asset_contract",
    "video_task",
}
ID_PATTERN = re.compile(r"^[\w.-]+$", re.UNICODE)
REFERENCE_PATTERN = re.compile(r"life-path:([\w.-]+)/([\w.-]+)", re.UNICODE)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")
HAN_PATTERN = re.compile(
    "[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    "\U00020000-\U0002a6df\U0002a700-\U0002b73f"
    "\U0002b740-\U0002b81f\U0002b820-\U0002ceaf"
    "\U0002ceb0-\U0002ebef\U00030000-\U0003134f]"
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    location: str
    message: str


@dataclass(frozen=True)
class BiographyStats:
    total_han: int
    effective_han: int
    repeated_han: int
    repeated_ratio: float
    repeated_paragraphs: int


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


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _string_list(value: Any) -> Optional[list[str]]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value):
        return [item.strip() for item in value]
    return None


def _missing(
    findings: list[Finding],
    mapping: dict[str, Any],
    field: str,
    location: str,
    *,
    strict: bool,
    require_content: bool = True,
) -> None:
    absent = field not in mapping or (require_content and not _has_content(mapping.get(field)))
    if absent:
        findings.append(
            Finding(
                "missing-field",
                "error" if strict else "warning",
                location,
                f"Missing or empty required field: {field}.",
            )
        )


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise ValueError("YAML input requires PyYAML; install requirements-dev.txt")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return payload


def _strip_inline_markdown(value: str) -> str:
    value = re.sub(r"`[^`]*`", "", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    return value


def biography_paragraphs(text: str) -> list[str]:
    """Return Markdown body paragraphs after excluding metadata, code, and quotations."""
    lines = text.lstrip("\ufeff").splitlines()
    if lines and lines[0].strip() == "---":
        closing = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
        if closing is not None:
            lines = lines[closing + 1 :]

    paragraphs: list[str] = []
    current: list[str] = []
    fence_marker: Optional[str] = None

    def flush() -> None:
        if current:
            paragraphs.append(" ".join(current).strip())
            current.clear()

    for raw_line in lines:
        fence = FENCE_PATTERN.match(raw_line)
        if fence:
            marker = fence.group(1)[0]
            if fence_marker is None:
                flush()
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue
        if re.match(r"^\s*>", raw_line):
            flush()
            continue
        if re.match(r"^\s{0,3}#{1,6}\s+", raw_line):
            flush()
            continue
        if re.match(r"^\s*(?:[-+*]|\d+[.)])\s+", raw_line):
            flush()
            continue
        if re.match(r"^\s*\|", raw_line):
            flush()
            continue
        if not raw_line.strip():
            flush()
            continue
        current.append(_strip_inline_markdown(raw_line.strip()))
    flush()
    return [paragraph for paragraph in paragraphs if paragraph]


def biography_stats(text: str) -> BiographyStats:
    total_han = 0
    paragraphs: list[str] = []
    for paragraph in biography_paragraphs(text):
        normalized = unicodedata.normalize("NFC", paragraph)
        han_only = "".join(HAN_PATTERN.findall(normalized))
        total_han += len(han_only)
        if han_only:
            paragraphs.append(unicodedata.normalize("NFKC", han_only))
    counts = Counter(paragraphs)
    repeated_han = sum(len(paragraph) * (count - 1) for paragraph, count in counts.items() if count > 1)
    repeated_paragraphs = sum(count - 1 for count in counts.values() if count > 1)
    for paragraph in counts:
        chunks = [
            paragraph[index : index + INTERNAL_REPEAT_CHUNK_HAN]
            for index in range(0, len(paragraph), INTERNAL_REPEAT_CHUNK_HAN)
            if len(paragraph[index : index + INTERNAL_REPEAT_CHUNK_HAN]) == INTERNAL_REPEAT_CHUNK_HAN
        ]
        chunk_counts = Counter(chunks)
        repeated_han += INTERNAL_REPEAT_CHUNK_HAN * sum(
            count - 1 for count in chunk_counts.values() if count > 1
        )
    repeated_han = min(total_han, repeated_han)
    effective_han = max(0, total_han - repeated_han)
    repeated_ratio = repeated_han / total_han if total_han else 0.0
    return BiographyStats(total_han, effective_han, repeated_han, repeated_ratio, repeated_paragraphs)


def biography_frontmatter(text: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing"
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
    if closing is None:
        return None, "unterminated"
    if yaml is None:
        return None, "PyYAML is unavailable"
    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        return None, str(exc)
    if not isinstance(metadata, dict):
        return None, "frontmatter must be a YAML mapping"
    return metadata, None


def biography_body_sha256(text: str) -> str:
    lines = text.lstrip("\ufeff").splitlines()
    if lines and lines[0].strip() == "---":
        closing = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
        if closing is not None:
            lines = lines[closing + 1 :]
    normalized = "\n".join(lines).replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _normalized_structure(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_normalized_structure(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalized_structure(value[key]) for key in sorted(value)}
    return value


def candidate_sha256(candidate: dict[str, Any]) -> str:
    locked_content = {
        key: value
        for key, value in candidate.items()
        if key not in {"status"}
    }
    canonical = json.dumps(
        _normalized_structure(locked_content),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fact_boundary_sha256(fact_boundary: dict[str, Any]) -> str:
    canonical = json.dumps(
        _normalized_structure(fact_boundary),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def shared_event_sha256(event: dict[str, Any]) -> str:
    """Hash the author-controlled event content without its self-hash or approval envelope."""
    bound_content = {
        key: value
        for key, value in event.items()
        if key not in {"event_sha256", "author_approval"}
    }
    canonical = json.dumps(
        _normalized_structure(bound_content),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _project_root_for(manifest_path: Path) -> Path:
    for candidate in (manifest_path.parent, *manifest_path.parents):
        if (candidate / "project.yaml").is_file():
            return candidate.resolve()
    return manifest_path.parent.resolve()


def _valid_author_decision(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        value.get("actor") == "author"
        and isinstance(value.get("source_ref"), str)
        and bool(value["source_ref"].strip())
        and isinstance(value.get("decision_text"), str)
        and bool(value["decision_text"].strip())
    )


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(str(path)))


def _uses_symlink(path: Path, root: Path) -> bool:
    lexical_path = _lexical_absolute(path)
    lexical_root = _lexical_absolute(root)
    if not _path_is_within(lexical_path, lexical_root):
        return False
    current = lexical_root
    for part in lexical_path.relative_to(lexical_root).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _references(text: str) -> list[tuple[str, str]]:
    return [(match.group(1), match.group(2)) for match in REFERENCE_PATTERN.finditer(text)]


def _structured_artifact_kind(value: Any) -> Optional[str]:
    """Infer only high-confidence artifact kinds that carry additional hard gates."""
    if not isinstance(value, dict):
        return None
    discriminator = value.get("artifact_type") or value.get("document_type") or value.get("kind")
    if isinstance(discriminator, str):
        normalized = discriminator.strip().lower().replace("-", "_")
        aliases = {
            "scene": "scene_contract",
            "scene_contract": "scene_contract",
            "turn_state": "turn_state",
            "beat_map": "beat_map",
            "storyboard": "storyboard",
            "continuity": "continuity",
            "visual_bible": "visual_bible",
            "asset_contract": "asset_contract",
            "video_task": "video_task",
            "video_prompt": "video_prompt",
            "relationship_ledger": "relationship_ledger",
            "speech_corpus": "speech_corpus",
        }
        if normalized in aliases:
            return aliases[normalized]
    keys = set(value)
    if "shared_event_registry" in keys or ({"relationships", "shared_memory_contracts"} <= keys):
        return "relationship_ledger"
    if isinstance(value.get("scene"), dict) and len(keys & {"start_state", "end_state", "characters", "continuity_in", "continuity_out"}) >= 2:
        return "scene_contract"
    if "scene_id" in keys and isinstance(value.get("turns"), list):
        return "turn_state"
    if "scene_id" in keys and isinstance(value.get("beats"), list):
        return "beat_map"
    if isinstance(value.get("shots"), list) and len(keys & {"scene_id", "duration", "continuity", "audio"}) >= 1:
        return "storyboard"
    if "video_task_id" in keys and "primary_mode" in keys:
        return "video_task"
    if "continuity_id" in keys and "shot_handoffs" in keys:
        return "continuity"
    if "visual_bible_id" in keys and isinstance(value.get("assets"), list):
        return "visual_bible"
    if "contract_id" in keys and "default_borrow_policy" in keys:
        return "asset_contract"
    return None


def _relationship_ledger_claim_scope(
    value: Any,
    character_id: Any,
    *,
    findings: Optional[list[Finding]] = None,
    location: str = "relationship_ledger",
) -> dict[str, Any]:
    """Return claim-bearing ledger sections scoped to the workbench being compiled."""
    if not isinstance(value, dict):
        return {}
    scope = {
        key: value[key]
        for key in (
            "compiled_provenance",
            "source_refs",
        )
        if key in value
    }

    participant_fields = {
        "relationships": ("from_character", "to_character"),
        "relationship_claim_records": ("from_character", "to_character"),
        "common_ground_propositions": ("participants",),
        "second_order_beliefs": ("holder_character_id", "about_character_id"),
        "shared_memory_contracts": ("participants",),
    }
    for section, fields in participant_fields.items():
        records = value.get(section)
        if not isinstance(records, list):
            continue
        scoped_records: list[dict[str, Any]] = []
        for record_index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue
            involved = False
            has_participant_field = any(field in record for field in fields)
            for field in fields:
                candidate = record.get(field)
                if candidate == character_id or (isinstance(candidate, list) and character_id in candidate):
                    involved = True
            character_sources = record.get("character_sources")
            if isinstance(character_sources, list):
                matching_sources = [
                    item
                    for item in character_sources
                    if isinstance(item, dict) and item.get("character_id") == character_id
                ]
                if findings is not None and (
                    (involved and len(matching_sources) != 1)
                    or (not involved and bool(matching_sources))
                ):
                    findings.append(
                        Finding(
                            "relationship-participant-source-mismatch",
                            "error",
                            f"{location}.{section}[{record_index}]",
                            "Record participants and per-character provenance sources must cover each other exactly for the audited character.",
                        )
                    )
                if not involved and not matching_sources:
                    continue
                scoped_record = dict(record)
                scoped_record["character_sources"] = matching_sources if matching_sources else character_sources
                scoped_records.append(scoped_record)
                continue
            if involved or not has_participant_field:
                scoped_records.append(record)
        if scoped_records:
            scope[section] = scoped_records
    scoped_events: list[dict[str, Any]] = []
    events = value.get("shared_event_registry")
    if isinstance(events, list):
        for event in events:
            if not isinstance(event, dict):
                continue
            participants = event.get("participants")
            matching = [
                participant
                for participant in participants
                if isinstance(participant, dict) and participant.get("character_id") == character_id
            ] if isinstance(participants, list) else []
            if matching:
                scoped_event = {
                    key: item
                    for key, item in event.items()
                    if key not in {"participants", "author_approval"}
                }
                scoped_event["participants"] = matching
                scoped_events.append(scoped_event)
    if scoped_events:
        scope["shared_event_registry"] = scoped_events
    return scope


def _scoped_nested_life_path_refs(value: Any, character_id: Any) -> set[str]:
    """Collect nested refs owned by one character, excluding aggregate character_sources declarations."""
    refs: set[str] = set()
    if isinstance(value, list):
        for item in value:
            refs.update(_scoped_nested_life_path_refs(item, character_id))
        return refs
    if not isinstance(value, dict):
        if isinstance(value, str):
            refs.update(f"life-path:{branch}/{node}" for branch, node in _references(value))
        return refs
    owner = value.get("character_id")
    if _has_content(owner) and owner != character_id:
        return refs
    for key, item in value.items():
        if key == "character_sources":
            continue
        refs.update(_scoped_nested_life_path_refs(item, character_id))
    return refs


def _artifact_participant_ids(artifact_type: str, value: Any) -> set[str]:
    """Extract only high-confidence character IDs from shared artifact structures."""
    if not isinstance(value, dict):
        return set()
    result: set[str] = set()
    if artifact_type == "scene_contract":
        for item in value.get("characters", []) if isinstance(value.get("characters"), list) else []:
            if isinstance(item, dict) and _has_content(item.get("id")):
                result.add(str(item["id"]))
        for item in value.get("character_runtime_scopes", []) if isinstance(value.get("character_runtime_scopes"), list) else []:
            if isinstance(item, dict) and _has_content(item.get("character_id")):
                result.add(str(item["character_id"]))
    elif artifact_type == "turn_state":
        for section in ("turns", "decision_traces"):
            for item in value.get(section, []) if isinstance(value.get(section), list) else []:
                if isinstance(item, dict) and _has_content(item.get("character_id")):
                    result.add(str(item["character_id"]))
    elif artifact_type == "storyboard":
        for shot in value.get("shots", []) if isinstance(value.get("shots"), list) else []:
            dialogue = shot.get("dialogue") if isinstance(shot, dict) else None
            for line in dialogue.get("lines", []) if isinstance(dialogue, dict) and isinstance(dialogue.get("lines"), list) else []:
                if isinstance(line, dict) and _has_content(line.get("speaker_id")):
                    result.add(str(line["speaker_id"]))
    return result


def _time_scalar_kind(value: Any) -> Optional[str]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return "number"
    if isinstance(value, float):
        return "number" if math.isfinite(value) else None
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, date):
        return "date"
    if isinstance(value, str) and value.strip():
        return "string"
    return None


def _comparable_time(value: Any) -> Optional[tuple[str, Any]]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return ("number", value)
    if isinstance(value, float):
        return ("number", value) if math.isfinite(value) else None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return ("datetime-aware", value.timestamp())
        return ("datetime-naive", (value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond))
    if isinstance(value, date):
        return ("date", value.toordinal())
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        parsed_date = date.fromisoformat(candidate)
    except ValueError:
        parsed_date = None
    if parsed_date is not None:
        return ("date", parsed_date.toordinal())
    try:
        parsed_datetime = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed_datetime.tzinfo is not None:
        return ("datetime-aware", parsed_datetime.timestamp())
    return (
        "datetime-naive",
        (
            parsed_datetime.year,
            parsed_datetime.month,
            parsed_datetime.day,
            parsed_datetime.hour,
            parsed_datetime.minute,
            parsed_datetime.second,
            parsed_datetime.microsecond,
        ),
    )


def _validate_reference(
    findings: list[Finding],
    branch_id: str,
    node_id: str,
    location: str,
    candidates: dict[str, dict[str, Any]],
    *,
    locked_branch_id: Optional[str],
    downstream: bool,
) -> None:
    if branch_id not in candidates:
        findings.append(Finding("unknown-reference-branch", "error", location, f"Unknown life-path branch: {branch_id}."))
        return
    candidate = candidates[branch_id]
    if node_id not in candidate["node_ids"]:
        findings.append(Finding("unknown-reference-node", "error", location, f"Unknown life-path node: {branch_id}/{node_id}."))
        return
    if not downstream:
        return
    if candidate["status"] == "rejected":
        findings.append(Finding("rejected-branch-reference", "error", location, f"Downstream content references rejected branch {branch_id}."))
    elif locked_branch_id is None or branch_id != locked_branch_id or candidate["status"] != "locked":
        findings.append(Finding("unlocked-branch-reference", "error", location, f"Only the locked branch may be referenced downstream: {branch_id}."))


def _audit_structured_downstream(
    value: Any,
    location: str,
    findings: list[Finding],
    candidates: dict[str, dict[str, Any]],
    *,
    character_id: Any,
    package_context_id: Any,
    locked_branch_id: Optional[str],
    lock_revision: Any,
    fact_boundary_hash: Any,
    locked_candidate_hash: Any,
    biography_revision: Any,
    biography_sha256: Any,
) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict) and _has_content(item.get("character_id")) and item.get("character_id") != character_id:
                continue
            _audit_structured_downstream(
                item,
                f"{location}[{index}]",
                findings,
                candidates,
                character_id=character_id,
                package_context_id=package_context_id,
                locked_branch_id=locked_branch_id,
                lock_revision=lock_revision,
                fact_boundary_hash=fact_boundary_hash,
                locked_candidate_hash=locked_candidate_hash,
                biography_revision=biography_revision,
                biography_sha256=biography_sha256,
            )
        return
    if not isinstance(value, dict):
        if isinstance(value, str):
            for branch_id, node_id in _references(value):
                _validate_reference(
                    findings,
                    branch_id,
                    node_id,
                    location,
                    candidates,
                    locked_branch_id=locked_branch_id,
                    downstream=True,
                )
        return

    owner_character_id = value.get("character_id")
    if _has_content(owner_character_id) and owner_character_id != character_id:
        return

    character_sources = value.get("character_sources")
    if "character_sources" in value:
        if not isinstance(character_sources, list):
            findings.append(
                Finding(
                    "invalid-character-sources",
                    "error",
                    f"{location}.character_sources",
                    "character_sources must be a list of per-character provenance records.",
                )
            )
        else:
            matching_sources = [
                item
                for item in character_sources
                if isinstance(item, dict)
                and item.get("character_id") == character_id
                and item.get("package_context_id") == package_context_id
            ]
            if len(matching_sources) != 1:
                findings.append(
                    Finding(
                        "character-source-binding-mismatch",
                        "error",
                        f"{location}.character_sources",
                        "A multi-character artifact must contain exactly one source record for the audited character and package context.",
                    )
                )
            for index, item in enumerate(character_sources, start=1):
                item_location = f"{location}.character_sources[{index}]"
                if not isinstance(item, dict):
                    findings.append(Finding("invalid-character-source", "error", item_location, "Each character source must be a mapping."))
                    continue
                required_source_fields = (
                    "character_id",
                    "package_context_id",
                    "source_refs",
                    "life_path_branch_id",
                    "compiled_from_lock_revision",
                    "compiled_from_fact_boundary_sha256",
                    "compiled_from_candidate_sha256",
                    "compiled_from_biography_revision",
                    "compiled_from_biography_sha256",
                ) if item in matching_sources else ("character_id", "package_context_id", "source_refs")
                for field in required_source_fields:
                    _missing(findings, item, field, item_location, strict=True)
                if item in matching_sources:
                    _audit_structured_downstream(
                        {key: child for key, child in item.items() if key != "character_sources"},
                        item_location,
                        findings,
                        candidates,
                        character_id=character_id,
                        package_context_id=package_context_id,
                        locked_branch_id=locked_branch_id,
                        lock_revision=lock_revision,
                        fact_boundary_hash=fact_boundary_hash,
                        locked_candidate_hash=locked_candidate_hash,
                        biography_revision=biography_revision,
                        biography_sha256=biography_sha256,
                    )
                else:
                    other_refs = _string_list(item.get("source_refs"))
                    if other_refs is None:
                        findings.append(
                            Finding(
                                "invalid-character-source-refs",
                                "error",
                                item_location,
                                "Other-character source_refs must be a list of canonical references; cross-workbench truth is audited separately.",
                            )
                        )
                    elif any(REFERENCE_PATTERN.fullmatch(reference) is None for reference in other_refs):
                        findings.append(
                            Finding(
                                "invalid-character-source-refs",
                                "error",
                                item_location,
                                "Other-character source_refs contain a malformed canonical reference.",
                            )
                        )

    canonical_pairs: set[tuple[str, str]] = set()
    if "source_refs" in value:
        source_refs = value.get("source_refs")
        if not isinstance(source_refs, list):
            findings.append(Finding("invalid-runtime-source-refs", "error", location, "source_refs must be a list."))
        else:
            for reference in source_refs:
                if not isinstance(reference, str) or not reference.startswith("life-path:"):
                    continue
                match = REFERENCE_PATTERN.fullmatch(reference)
                if not match:
                    findings.append(Finding("invalid-life-path-reference", "error", location, f"Invalid reference: {reference!r}."))
                    continue
                branch_id, node_id = match.groups()
                canonical_pairs.add((branch_id, node_id))
                _validate_reference(
                    findings,
                    branch_id,
                    node_id,
                    location,
                    candidates,
                    locked_branch_id=locked_branch_id,
                    downstream=True,
                )

    legacy_pairs: set[tuple[str, str]] = set()
    if _has_content(value.get("source_branch_id")):
        branch_id = value.get("source_branch_id")
        node_ids = value.get("source_node_ids", [])
        if not isinstance(branch_id, str) or not isinstance(node_ids, list) or not all(
            isinstance(item, str) and item.strip() for item in node_ids
        ):
            findings.append(
                Finding("invalid-legacy-provenance", "error", location, "source_branch_id/source_node_ids provenance is malformed.")
            )
        elif not node_ids and branch_id != locked_branch_id:
            findings.append(
                Finding("unlocked-branch-reference", "error", location, f"Only the locked branch may be referenced downstream: {branch_id}.")
            )
        else:
            for node_id in node_ids:
                legacy_pairs.add((branch_id, node_id))
                _validate_reference(
                    findings,
                    branch_id,
                    node_id,
                    location,
                    candidates,
                    locked_branch_id=locked_branch_id,
                    downstream=True,
                )
    if canonical_pairs and legacy_pairs and canonical_pairs != legacy_pairs:
        findings.append(
            Finding(
                "conflicting-provenance-fields",
                "error",
                location,
                "Canonical source_refs disagree with legacy source_branch_id/source_node_ids.",
            )
        )

    if _has_content(value.get("life_path_branch_id")) and value.get("life_path_branch_id") != locked_branch_id:
        findings.append(
            Finding(
                "unlocked-branch-reference",
                "error",
                location,
                f"life_path_branch_id must match the locked branch: {value.get('life_path_branch_id')!r}.",
            )
        )
    for field in ("life_path_lock_revision", "compiled_from_lock_revision"):
        if _has_content(value.get(field)) and value.get(field) != lock_revision:
            findings.append(
                Finding("compiled-revision-mismatch", "error", location, f"{field} does not match lock_revision {lock_revision!r}.")
            )
    for field in ("compiled_for_character_id", "approved_character_id"):
        if _has_content(value.get(field)) and value.get(field) != character_id:
            findings.append(
                Finding("compiled-character-mismatch", "error", location, f"{field} does not match character_id {character_id!r}.")
            )
    for field in ("compiled_for_package_context_id", "approved_package_context_id"):
        if _has_content(value.get(field)) and value.get(field) != package_context_id:
            findings.append(
                Finding(
                    "compiled-package-context-mismatch",
                    "error",
                    location,
                    f"{field} does not match package_context_id {package_context_id!r}.",
                )
            )
    for field in ("fact_boundary_sha256", "compiled_from_fact_boundary_sha256"):
        if _has_content(value.get(field)) and value.get(field) != fact_boundary_hash:
            findings.append(
                Finding("compiled-fact-boundary-hash-mismatch", "error", location, f"{field} does not match the locked fact boundary.")
            )
    for field in ("biography_revision", "compiled_from_biography_revision"):
        if _has_content(value.get(field)) and value.get(field) != biography_revision:
            findings.append(
                Finding("compiled-biography-revision-mismatch", "error", location, f"{field} does not match biography_revision {biography_revision!r}.")
            )
    for field in ("locked_candidate_sha256", "compiled_from_candidate_sha256"):
        if _has_content(value.get(field)) and value.get(field) != locked_candidate_hash:
            findings.append(
                Finding("compiled-candidate-hash-mismatch", "error", location, f"{field} does not match the locked candidate content.")
            )
    for field in ("biography_sha256", "approved_biography_sha256", "compiled_from_biography_sha256"):
        if _has_content(value.get(field)) and value.get(field) != biography_sha256:
            findings.append(
                Finding("compiled-biography-hash-mismatch", "error", location, f"{field} does not match the approved biography body.")
            )

    for key, item in value.items():
        if key == "character_sources":
            continue
        _audit_structured_downstream(
            item,
            f"{location}.{key}",
            findings,
            candidates,
            character_id=character_id,
            package_context_id=package_context_id,
            locked_branch_id=locked_branch_id,
            lock_revision=lock_revision,
            fact_boundary_hash=fact_boundary_hash,
            locked_candidate_hash=locked_candidate_hash,
            biography_revision=biography_revision,
            biography_sha256=biography_sha256,
        )


def audit_manifest(
    payload: dict[str, Any],
    manifest_path: Path,
    *,
    require_locked: bool = False,
    downstream_documents: Iterable[tuple[str, str]] = (),
) -> list[Finding]:
    findings: list[Finding] = []
    manifest_path = manifest_path.resolve()
    manifest_dir = manifest_path.parent

    selection_raw = payload.get("selection")
    selection = selection_raw if isinstance(selection_raw, dict) else {}
    state = selection.get("state")
    preparing_selection = require_locked or state in {"selected", "locked"}

    for field in TOP_LEVEL_FIELDS:
        _missing(findings, payload, field, "manifest", strict=preparing_selection, require_content=False)
    if "schema_version" in payload and not _positive_int(payload.get("schema_version")):
        findings.append(Finding("invalid-schema-version", "error", "manifest", "schema_version must be a positive integer."))
    if "character_id" in payload and (not isinstance(payload.get("character_id"), str) or not payload["character_id"].strip()):
        findings.append(Finding("invalid-character-id", "error", "manifest", "character_id must be a non-empty string."))
    character_id = payload.get("character_id")
    package_context_id = payload.get("package_context_id")
    if preparing_selection and (not isinstance(package_context_id, str) or not package_context_id.strip()):
        findings.append(
            Finding(
                "missing-package-context-id",
                "error",
                "manifest",
                "Selected or locked work requires a stable non-empty package_context_id.",
            )
        )
    elif package_context_id is not None and (
        not isinstance(package_context_id, str) or not package_context_id.strip() or not ID_PATTERN.fullmatch(package_context_id.strip())
    ):
        findings.append(
            Finding(
                "invalid-package-context-id",
                "error",
                "manifest",
                "package_context_id must be a stable non-empty ID when present.",
            )
        )
    fact_boundary_raw = payload.get("fact_boundary")
    fact_boundary = fact_boundary_raw if isinstance(fact_boundary_raw, dict) else {}
    if "fact_boundary" in payload and not isinstance(fact_boundary_raw, dict):
        findings.append(Finding("invalid-fact-boundary", "error", "fact_boundary", "fact_boundary must be a mapping."))
    boundary_claim_ids: set[str] = set()
    for field in FACT_BOUNDARY_FIELDS:
        if field not in fact_boundary:
            findings.append(
                Finding(
                    "missing-fact-boundary-category",
                    "error" if preparing_selection else "warning",
                    "fact_boundary",
                    f"Missing epistemic category: {field}.",
                )
            )
            continue
        entries = fact_boundary.get(field)
        if not isinstance(entries, list):
            findings.append(
                Finding(
                    "invalid-fact-boundary-category",
                    "error",
                    f"fact_boundary.{field}",
                    f"{field} must be a list of claim records.",
                )
            )
            continue
        for index, entry in enumerate(entries, start=1):
            location = f"fact_boundary.{field}[{index}]"
            if not isinstance(entry, dict):
                findings.append(
                    Finding(
                        "invalid-fact-boundary-claim",
                        "error" if preparing_selection else "warning",
                        location,
                        "Each epistemic claim must be a mapping with id, content, and source_refs.",
                    )
                )
                continue
            claim_id = entry.get("id")
            if not isinstance(claim_id, str) or not claim_id.strip() or not ID_PATTERN.fullmatch(claim_id.strip()):
                findings.append(
                    Finding(
                        "invalid-fact-boundary-claim-id",
                        "error" if preparing_selection else "warning",
                        location,
                        "Each epistemic claim requires a stable ID.",
                    )
                )
                continue
            claim_id = claim_id.strip()
            if claim_id in boundary_claim_ids:
                findings.append(Finding("duplicate-id", "error", location, f"Fact-boundary claim ID is repeated: {claim_id}."))
            boundary_claim_ids.add(claim_id)
            if preparing_selection and not _has_content(entry.get("content")):
                findings.append(Finding("missing-field", "error", location, "Missing or empty required field: content."))
            source_refs = entry.get("source_refs")
            if not isinstance(source_refs, list) or not all(
                isinstance(item, str) and item.strip() for item in source_refs
            ):
                findings.append(
                    Finding(
                        "invalid-evidence-source-refs",
                        "error" if preparing_selection else "warning",
                        location,
                        "source_refs must be a list of stable, non-empty evidence references.",
                    )
                )
            elif preparing_selection and not source_refs:
                findings.append(
                    Finding(
                        "missing-evidence-source-ref",
                        "error",
                        location,
                        "Selected or locked work requires at least one evidence source reference per declared claim.",
                    )
                )

    current_fact_boundary_hash = fact_boundary_sha256(fact_boundary)

    candidates_raw = payload.get("candidates")
    if candidates_raw is None:
        candidate_items: list[Any] = []
    elif not isinstance(candidates_raw, list):
        findings.append(Finding("invalid-candidates", "error", "candidates", "candidates must be a list."))
        candidate_items = []
    else:
        candidate_items = candidates_raw

    candidates: dict[str, dict[str, Any]] = {}
    for index, candidate_raw in enumerate(candidate_items, start=1):
        location = f"candidates[{index}]"
        if not isinstance(candidate_raw, dict):
            findings.append(Finding("invalid-candidate", "error", location, "Each candidate must be a mapping."))
            continue
        candidate = candidate_raw
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            findings.append(Finding("missing-candidate-id", "error", location, "Each candidate requires a non-empty id."))
            continue
        candidate_id = candidate_id.strip()
        location = f"candidate:{candidate_id}"
        if not ID_PATTERN.fullmatch(candidate_id):
            findings.append(Finding("invalid-id", "error", location, f"Invalid candidate id: {candidate_id!r}."))
        if candidate_id in candidates:
            findings.append(Finding("duplicate-id", "error", location, "Candidate id is not unique."))
            continue
        for field in CANDIDATE_FIELDS:
            _missing(
                findings,
                candidate,
                field,
                location,
                strict=preparing_selection,
                require_content=field != "derived_from",
            )
        status = candidate.get("status")
        if status is not None and status not in CANDIDATE_STATUSES:
            findings.append(Finding("invalid-candidate-status", "error", location, f"Unsupported candidate status: {status!r}."))

        derived_from = candidate.get("derived_from", [])
        if not isinstance(derived_from, list) or not all(isinstance(item, str) and item.strip() for item in derived_from):
            findings.append(Finding("invalid-derived-from", "error", f"{location}.derived_from", "derived_from must be a list of candidate IDs."))
            derived_ids: list[str] = []
        else:
            derived_ids = [item.strip() for item in derived_from]
            if len(derived_ids) != len(set(derived_ids)):
                findings.append(Finding("duplicate-reference", "error", f"{location}.derived_from", "derived_from repeats a candidate ID."))

        feasibility_raw = candidate.get("feasibility")
        feasibility = feasibility_raw if isinstance(feasibility_raw, dict) else {}
        if feasibility_raw is not None and not isinstance(feasibility_raw, dict):
            findings.append(Finding("invalid-feasibility", "error", f"{location}.feasibility", "feasibility must be a mapping."))
        for field in ("supports", "conflicts", "unknowns"):
            _missing(
                findings,
                feasibility,
                field,
                f"{location}.feasibility",
                strict=preparing_selection,
                require_content=field == "supports",
            )
            if field in feasibility and not isinstance(feasibility.get(field), list):
                findings.append(
                    Finding("invalid-feasibility-field", "error", f"{location}.feasibility.{field}", f"{field} must be a list.")
                )
            elif isinstance(feasibility.get(field), list):
                for claim_ref in feasibility[field]:
                    if not isinstance(claim_ref, str) or claim_ref not in boundary_claim_ids:
                        findings.append(
                            Finding(
                                "unknown-fact-boundary-reference",
                                "error" if preparing_selection else "warning",
                                f"{location}.feasibility.{field}",
                                f"Candidate feasibility must reference a declared fact-boundary claim ID: {claim_ref!r}.",
                            )
                        )
        _missing(
            findings,
            feasibility,
            "real_world_feasibility",
            f"{location}.feasibility",
            strict=preparing_selection,
        )
        if "creative_consequences" in candidate and not isinstance(candidate.get("creative_consequences"), (list, dict)):
            findings.append(
                Finding(
                    "invalid-creative-consequences",
                    "error",
                    f"{location}.creative_consequences",
                    "creative_consequences must be a list or mapping.",
                )
            )

        spine_raw = candidate.get("causal_spine")
        if spine_raw is None:
            spine: list[Any] = []
        elif not isinstance(spine_raw, list):
            findings.append(Finding("invalid-causal-spine", "error", f"{location}.causal_spine", "causal_spine must be a list."))
            spine = []
        else:
            spine = spine_raw
        node_ids: set[str] = set()
        nodes: list[dict[str, Any]] = []
        for node_index, node_raw in enumerate(spine, start=1):
            node_location = f"{location}.causal_spine[{node_index}]"
            if not isinstance(node_raw, dict):
                findings.append(Finding("invalid-node", "error", node_location, "Each causal node must be a mapping."))
                continue
            node = node_raw
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id.strip():
                findings.append(Finding("missing-node-id", "error", node_location, "Each causal node requires a non-empty id."))
            else:
                node_id = node_id.strip()
                if not ID_PATTERN.fullmatch(node_id):
                    findings.append(Finding("invalid-id", "error", node_location, f"Invalid node id: {node_id!r}."))
                if node_id in node_ids:
                    findings.append(Finding("duplicate-id", "error", node_location, f"Node id is repeated within {candidate_id}: {node_id}."))
                node_ids.add(node_id)
            for field in NODE_FIELDS:
                _missing(findings, node, field, node_location, strict=preparing_selection)
            nodes.append(node)

        candidates[candidate_id] = {
            "raw": candidate,
            "status": status,
            "derived_from": derived_ids,
            "nodes": nodes,
            "node_ids": node_ids,
        }

    for candidate_id, meta in candidates.items():
        for source_id in meta["derived_from"]:
            if source_id == candidate_id:
                findings.append(Finding("self-derived-candidate", "error", f"candidate:{candidate_id}.derived_from", "A candidate cannot derive from itself."))
            elif source_id not in candidates:
                findings.append(Finding("unknown-derived-candidate", "error", f"candidate:{candidate_id}.derived_from", f"Unknown candidate: {source_id}."))

    visited: set[str] = set()
    active: set[str] = set()

    def visit(candidate_id: str) -> None:
        if candidate_id in active:
            findings.append(
                Finding(
                    "cyclic-candidate-composition",
                    "error",
                    f"candidate:{candidate_id}.derived_from",
                    "Candidate composition provenance contains a cycle.",
                )
            )
            return
        if candidate_id in visited:
            return
        active.add(candidate_id)
        for source_id in candidates[candidate_id]["derived_from"]:
            if source_id in candidates:
                visit(source_id)
        active.remove(candidate_id)
        visited.add(candidate_id)

    for candidate_id in candidates:
        visit(candidate_id)

    if preparing_selection and len(candidates) < 3:
        findings.append(Finding("too-few-candidates", "error", "candidates", f"Selection requires at least 3 candidates; found {len(candidates)}."))
    if preparing_selection:
        root_candidate_count = sum(not meta["derived_from"] for meta in candidates.values())
        if root_candidate_count < 3:
            findings.append(
                Finding(
                    "too-few-root-candidates",
                    "error",
                    "candidates",
                    f"Selection requires at least 3 independently proposed root candidates before composition; found {root_candidate_count}.",
                )
            )
        spine_fingerprints: dict[str, str] = {}
        for candidate_id, meta in candidates.items():
            normalized_spine = [
                _normalized_structure({field: node.get(field) for field in NODE_FIELDS if field != "id"})
                for node in meta["nodes"]
            ]
            fingerprint = json.dumps(normalized_spine, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if fingerprint in spine_fingerprints:
                findings.append(
                    Finding(
                        "duplicate-causal-spine",
                        "error",
                        f"candidate:{candidate_id}",
                        f"Causal spine duplicates candidate {spine_fingerprints[fingerprint]}; surface metadata does not create a distinct path.",
                    )
                )
            else:
                spine_fingerprints[fingerprint] = candidate_id

    if selection_raw is not None and not isinstance(selection_raw, dict):
        findings.append(Finding("invalid-selection", "error", "selection", "selection must be a mapping."))
    for field in SELECTION_FIELDS:
        _missing(findings, selection, field, "selection", strict=preparing_selection, require_content=False)
    if state is not None and state not in SELECTION_STATES:
        findings.append(Finding("invalid-selection-state", "error", "selection.state", f"Unsupported selection state: {state!r}."))
    selected_id = selection.get("selected_branch_id")
    selected_exists = isinstance(selected_id, str) and selected_id in candidates
    author_lock = selection.get("author_lock")
    lock_revision = selection.get("lock_revision")
    locked_fact_boundary_hash = selection.get("locked_fact_boundary_sha256")
    locked_candidate_hash = selection.get("locked_candidate_sha256")
    if "author_lock" in selection and not isinstance(author_lock, bool):
        findings.append(Finding("invalid-author-lock", "error", "selection.author_lock", "author_lock must be boolean."))
    if _has_content(lock_revision) and not _nonnegative_int(lock_revision):
        findings.append(Finding("invalid-lock-revision", "error", "selection.lock_revision", "lock_revision must be a nonnegative integer."))
    if "unlock_history" in selection and not isinstance(selection.get("unlock_history"), list):
        findings.append(Finding("invalid-unlock-history", "error", "selection.unlock_history", "unlock_history must be a list."))

    if state == "open":
        if _has_content(selected_id):
            findings.append(Finding("open-selection-has-branch", "error", "selection", "Open selection cannot name a selected branch."))
        if author_lock is True:
            findings.append(Finding("open-selection-is-locked", "error", "selection", "Open selection cannot have author_lock=true."))
    elif state in {"selected", "locked"}:
        if not isinstance(selected_id, str) or not selected_id.strip():
            findings.append(Finding("missing-selected-branch", "error", "selection", "Selection requires selected_branch_id."))
        elif not selected_exists:
            findings.append(Finding("unknown-selected-branch", "error", "selection", f"Unknown selected_branch_id: {selected_id}."))
        elif candidates[selected_id]["status"] != state:
            findings.append(
                Finding("selection-status-mismatch", "error", "selection", f"Selected candidate must have status {state!r}.")
            )
        author_decision = selection.get("author_decision")
        if not _valid_author_decision(author_decision):
            findings.append(
                Finding(
                    "missing-author-decision",
                    "error",
                    "selection",
                    "Selected or locked state requires an author decision record with actor, source_ref, and decision_text.",
                )
            )
        elif selected_exists:
            expected_candidate_hash = candidate_sha256(candidates[selected_id]["raw"])
            expected_lock_revision = lock_revision if _nonnegative_int(lock_revision) else None
            decision_bindings = {
                "approved_character_id": character_id,
                "approved_package_context_id": package_context_id,
                "approved_branch_id": selected_id,
                "approved_candidate_sha256": expected_candidate_hash,
                "approved_fact_boundary_sha256": current_fact_boundary_hash,
                "approved_lock_revision": expected_lock_revision,
            }
            for field, expected in decision_bindings.items():
                if author_decision.get(field) != expected:
                    findings.append(
                        Finding(
                            "author-decision-binding-mismatch",
                            "error",
                            "selection.author_decision",
                            f"{field} must bind the current selection value {expected!r}.",
                        )
                    )
    if state == "selected" and author_lock is True:
        findings.append(Finding("selected-is-author-locked", "error", "selection", "Selected state is not locked; author_lock must not be true."))
    if state == "locked":
        if author_lock is not True:
            findings.append(Finding("missing-author-lock", "error", "selection", "Locked state requires author_lock=true."))
        if not _positive_int(lock_revision):
            findings.append(Finding("invalid-lock-revision", "error", "selection", "Locked state requires lock_revision > 0."))
        if selected_exists:
            expected_candidate_hash = candidate_sha256(candidates[selected_id]["raw"])
            if locked_fact_boundary_hash != current_fact_boundary_hash:
                findings.append(
                    Finding(
                        "locked-fact-boundary-hash-mismatch",
                        "error",
                        "selection.locked_fact_boundary_sha256",
                        "locked_fact_boundary_sha256 does not match the current epistemic boundary; changing facts requires a new author lock revision.",
                    )
                )
            if locked_candidate_hash != expected_candidate_hash:
                findings.append(
                    Finding(
                        "locked-candidate-hash-mismatch",
                        "error",
                        "selection.locked_candidate_sha256",
                        "locked_candidate_sha256 does not match the current selected causal candidate; editing a locked spine requires a new author lock revision.",
                    )
                )
    if require_locked and state != "locked":
        findings.append(Finding("lock-required", "error", "selection", "This audit requires a locked selection."))

    active_ids = [candidate_id for candidate_id, meta in candidates.items() if meta["status"] in {"selected", "locked"}]
    if len(active_ids) > 1:
        findings.append(Finding("multiple-active-candidates", "error", "candidates", f"Multiple candidates are active: {', '.join(active_ids)}."))
    for active_id in active_ids:
        if active_id != selected_id:
            findings.append(Finding("unselected-active-candidate", "error", f"candidate:{active_id}", "Only selected_branch_id may be selected or locked."))

    rejected_raw = selection.get("rejected_branch_ids", [])
    rejected_ids = _string_list(rejected_raw) if _has_content(rejected_raw) else []
    if rejected_ids is None:
        findings.append(Finding("invalid-rejected-branches", "error", "selection.rejected_branch_ids", "rejected_branch_ids must be a list of IDs."))
        rejected_ids = []
    if len(rejected_ids) != len(set(rejected_ids)):
        findings.append(Finding("duplicate-reference", "error", "selection.rejected_branch_ids", "Rejected candidate IDs are repeated."))
    for rejected_id in rejected_ids:
        if rejected_id not in candidates:
            findings.append(Finding("unknown-rejected-candidate", "error", "selection.rejected_branch_ids", f"Unknown candidate: {rejected_id}."))
        elif rejected_id == selected_id:
            findings.append(Finding("selected-candidate-rejected", "error", "selection", "Selected candidate cannot also be rejected."))
        elif candidates[rejected_id]["status"] != "rejected":
            findings.append(Finding("rejected-status-mismatch", "error", f"candidate:{rejected_id}", "Rejected candidate must have status 'rejected'."))
    if preparing_selection:
        rejected_status_ids = {candidate_id for candidate_id, meta in candidates.items() if meta["status"] == "rejected"}
        if rejected_status_ids != set(rejected_ids):
            findings.append(
                Finding("rejection-ledger-mismatch", "error", "selection", "rejected_branch_ids must match candidates whose status is rejected.")
            )

    locked_branch_id = selected_id if state == "locked" and selected_exists and author_lock is True else None

    biography_raw = payload.get("deep_biography")
    biography = biography_raw if isinstance(biography_raw, dict) else {}
    if biography_raw is not None and not isinstance(biography_raw, dict):
        findings.append(Finding("invalid-deep-biography", "error", "deep_biography", "deep_biography must be a mapping."))
    for field in BIOGRAPHY_FIELDS:
        _missing(
            findings,
            biography,
            field,
            "deep_biography",
            strict=preparing_selection,
            require_content=field in {"mode", "status"},
        )
    mode = biography.get("mode")
    if mode is not None and mode not in BIOGRAPHY_MODES:
        findings.append(Finding("invalid-biography-mode", "error", "deep_biography.mode", f"Unsupported mode: {mode!r}."))
    biography_status = biography.get("status")
    if biography_status is not None and biography_status not in BIOGRAPHY_STATUSES:
        findings.append(
            Finding(
                "invalid-biography-status",
                "error",
                "deep_biography.status",
                f"Unsupported status: {biography_status!r}.",
            )
        )
    tier_author_decision = biography.get("tier_author_decision")
    if mode == "unclassified" and preparing_selection:
        findings.append(
            Finding(
                "unclassified-biography-tier",
                "error",
                "deep_biography.mode",
                "The author must classify the character depth before selecting or locking a path.",
            )
        )
    if mode == "deep" and biography_status == "not_required":
        findings.append(
            Finding(
                "invalid-biography-status-for-mode",
                "error",
                "deep_biography.status",
                "Deep mode cannot use status 'not_required'.",
            )
        )
    if mode == "off" and biography_status not in {None, "not_required"}:
        findings.append(
            Finding(
                "invalid-biography-status-for-mode",
                "error",
                "deep_biography.status",
                "Off mode must use status 'not_required'.",
            )
        )
    if mode in {"light", "off"} and preparing_selection:
        if not _valid_author_decision(tier_author_decision):
            findings.append(
                Finding(
                    "missing-tier-author-decision",
                    "error",
                    "deep_biography.tier_author_decision",
                    "A light or off tier requires an author decision record; important characters cannot be silently downgraded.",
                )
            )
    biography_revision = biography.get("biography_revision")
    if biography_status == "ready" and not _positive_int(biography_revision):
        findings.append(
            Finding(
                "invalid-biography-revision",
                "error",
                "deep_biography.biography_revision",
                "A ready biography requires biography_revision > 0.",
            )
        )
    elif biography_status in {"not_started", "not_required"} and biography_revision not in {None, 0}:
        findings.append(
            Finding(
                "invalid-biography-revision",
                "error",
                "deep_biography.biography_revision",
                "A biography that has not started or is not required must use revision 0 or null.",
            )
        )
    minimum_characters = biography.get("minimum_chinese_characters", DEFAULT_MINIMUM_CHINESE_CHARACTERS)
    if minimum_characters is not None and not _positive_int(minimum_characters):
        findings.append(
            Finding(
                "invalid-biography-threshold",
                "error",
                "deep_biography.minimum_chinese_characters",
                "minimum_chinese_characters must be null (no length gate) or an explicitly requested positive integer.",
            )
        )
        minimum_characters = DEFAULT_MINIMUM_CHINESE_CHARACTERS

    runtime_preview = payload.get("compiled_runtime")
    preview_artifact_files = runtime_preview.get("artifact_files", []) if isinstance(runtime_preview, dict) else []
    has_compiled_artifacts = isinstance(preview_artifact_files, list) and bool(preview_artifact_files)
    deep_completion_gate = mode == "deep" and (
        require_locked or biography_status == "ready" or has_compiled_artifacts
    )
    biography_approval_required = mode == "deep" and (require_locked or has_compiled_artifacts)
    approval_raw = biography.get("author_approval")
    approval = approval_raw if isinstance(approval_raw, dict) else {}
    if approval_raw is not None and not isinstance(approval_raw, dict):
        findings.append(
            Finding(
                "invalid-biography-author-approval",
                "error",
                "deep_biography.author_approval",
                "author_approval must be a mapping.",
            )
        )
    approval_state = approval.get("state")
    if approval_state is not None and approval_state not in BIOGRAPHY_APPROVAL_STATES:
        findings.append(
            Finding(
                "invalid-biography-approval-state",
                "error",
                "deep_biography.author_approval",
                f"Unsupported approval state: {approval_state!r}.",
            )
        )
    if biography_approval_required:
        if approval_state != "approved" or not _valid_author_decision(approval.get("decision")):
            findings.append(
                Finding(
                    "biography-author-approval-required",
                    "error",
                    "deep_biography.author_approval",
                    "Compilation requires explicit author approval of this exact biography revision and body hash.",
                )
            )
        else:
            approval_bindings = {
                "approved_character_id": character_id,
                "approved_package_context_id": package_context_id,
                "approved_branch_id": locked_branch_id,
                "approved_fact_boundary_sha256": current_fact_boundary_hash,
                "approved_candidate_sha256": locked_candidate_hash,
                "approved_path_lock_revision": lock_revision,
                "approved_biography_revision": biography_revision,
            }
            for field, expected in approval_bindings.items():
                if approval.get(field) != expected:
                    findings.append(
                        Finding(
                            "biography-approval-binding-mismatch",
                            "error",
                            "deep_biography.author_approval",
                            f"{field} must bind the current approved biography context {expected!r}.",
                        )
                    )

    if biography_status in {"drafting", "ready"} and state != "locked":
        findings.append(
            Finding(
                "biography-before-path-lock",
                "error",
                "deep_biography.status",
                "A long biography may be drafted only from an author-locked life-path revision.",
            )
        )
    if require_locked and mode == "deep" and biography_status != "ready":
        findings.append(
            Finding(
                "deep-biography-not-ready",
                "error",
                "deep_biography.status",
                "A locked deep package requires a completed biography with status 'ready'.",
            )
        )
    if has_compiled_artifacts and mode == "deep" and biography_status != "ready":
        findings.append(
            Finding(
                "compiled-before-biography-ready",
                "error",
                "compiled_runtime",
                "Deep runtime artifacts cannot be compiled before the locked biography passes its completion gate.",
            )
        )

    coverage_raw = biography.get("coverage_stages")
    if coverage_raw is None:
        coverage: list[Any] = []
    elif not isinstance(coverage_raw, list):
        findings.append(Finding("invalid-coverage-stages", "error", "deep_biography.coverage_stages", "coverage_stages must be a list."))
        coverage = []
    else:
        coverage = coverage_raw
    if deep_completion_gate:
        if not coverage:
            findings.append(Finding("missing-biography-coverage", "error", "deep_biography.coverage_stages", "Deep locked biography requires at least one major coverage stage."))
        for index, stage_raw in enumerate(coverage, start=1):
            location = f"deep_biography.coverage_stages[{index}]"
            if not isinstance(stage_raw, dict):
                findings.append(Finding("invalid-coverage-stage", "error", location, "Coverage stage must be a mapping."))
                continue
            for field in COVERAGE_FIELDS:
                _missing(findings, stage_raw, field, location, strict=True)
            source_node_refs = stage_raw.get("source_node_refs")
            if isinstance(source_node_refs, list):
                for reference in source_node_refs:
                    match = REFERENCE_PATTERN.fullmatch(reference) if isinstance(reference, str) else None
                    if not match:
                        findings.append(Finding("invalid-life-path-reference", "error", location, f"Invalid stage source ref: {reference!r}."))
                        continue
                    branch_id, node_id = match.groups()
                    _validate_reference(
                        findings,
                        branch_id,
                        node_id,
                        location,
                        candidates,
                        locked_branch_id=locked_branch_id,
                        downstream=True,
                    )

    biography_value = biography.get("biography_file")
    biography_path: Optional[Path] = None
    biography_content: Optional[str] = None
    biography_sha256: Optional[str] = None
    if _has_content(biography_value):
        if not isinstance(biography_value, str):
            findings.append(Finding("invalid-biography-path", "error", "deep_biography.biography_file", "biography_file must be a path string."))
        else:
            supplied_path = Path(biography_value)
            lexical_path = supplied_path if supplied_path.is_absolute() else manifest_dir / supplied_path
            if _uses_symlink(lexical_path, manifest_dir):
                findings.append(Finding("biography-symlink", "error", "deep_biography.biography_file", "biography_file cannot traverse a symbolic link."))
            resolved_path = lexical_path.resolve()
            if not _path_is_within(resolved_path, manifest_dir):
                findings.append(Finding("biography-path-escape", "error", "deep_biography.biography_file", "biography_file must resolve inside the manifest directory."))
            elif not _uses_symlink(lexical_path, manifest_dir):
                biography_path = resolved_path
    if deep_completion_gate:
        if biography_path is None:
            if not _has_content(biography_value):
                findings.append(Finding("missing-biography-file", "error", "deep_biography", "Deep locked biography requires biography_file."))
        elif not biography_path.is_file():
            findings.append(Finding("missing-biography-file", "error", "deep_biography", f"Biography file does not exist: {biography_path}."))
        else:
            try:
                text = biography_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                findings.append(Finding("unreadable-biography", "error", "deep_biography", f"Cannot read biography as UTF-8: {exc}"))
            else:
                biography_content = text
                biography_sha256 = biography_body_sha256(text)
                stats = biography_stats(text)
                metadata, metadata_error = biography_frontmatter(text)
                if metadata_error is not None:
                    findings.append(
                        Finding(
                            "invalid-biography-provenance",
                            "error",
                            "deep_biography",
                            f"Biography requires valid YAML frontmatter recording the locked branch and revision: {metadata_error}.",
                        )
                    )
                elif metadata is not None:
                    if metadata.get("character_id") != payload.get("character_id"):
                        findings.append(
                            Finding(
                                "biography-character-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter character_id does not match the workbench.",
                            )
                        )
                    if metadata.get("package_context_id") != package_context_id:
                        findings.append(
                            Finding(
                                "biography-package-context-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter package_context_id does not match the workbench package.",
                            )
                        )
                    if metadata.get("life_path_branch_id") != locked_branch_id:
                        findings.append(
                            Finding(
                                "biography-branch-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter life_path_branch_id does not match the locked branch.",
                            )
                        )
                    if metadata.get("life_path_lock_revision") != lock_revision:
                        findings.append(
                            Finding(
                                "biography-revision-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter life_path_lock_revision does not match the current lock revision.",
                            )
                        )
                    if metadata.get("fact_boundary_sha256") != current_fact_boundary_hash:
                        findings.append(
                            Finding(
                                "biography-fact-boundary-hash-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter is not bound to the current fact boundary.",
                            )
                        )
                    if metadata.get("locked_candidate_sha256") != locked_candidate_hash:
                        findings.append(
                            Finding(
                                "biography-candidate-hash-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter is not bound to the current locked candidate content.",
                            )
                        )
                    if metadata.get("biography_revision") != biography_revision:
                        findings.append(
                            Finding(
                                "biography-revision-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter biography_revision does not match the workbench.",
                            )
                        )
                    if metadata.get("biography_status") != biography_status:
                        findings.append(
                            Finding(
                                "biography-status-mismatch",
                                "error",
                                "deep_biography",
                                "Biography frontmatter biography_status does not match the workbench.",
                            )
                        )
                if approval_state == "approved":
                    if approval.get("approved_biography_revision") != biography_revision:
                        findings.append(
                            Finding(
                                "biography-approval-revision-mismatch",
                                "error",
                                "deep_biography.author_approval",
                                "Author approval does not name the current biography revision.",
                            )
                        )
                    if approval.get("approved_body_sha256") != biography_sha256:
                        findings.append(
                            Finding(
                                "biography-approval-hash-mismatch",
                                "error",
                                "deep_biography.author_approval",
                                "Author approval does not match the current biography body; changed prose requires renewed approval.",
                            )
                        )
                for branch_id, node_id in _references(text):
                    _validate_reference(
                        findings,
                        branch_id,
                        node_id,
                        "deep_biography",
                        candidates,
                        locked_branch_id=locked_branch_id,
                        downstream=True,
                    )
                if stats.repeated_ratio > MAX_REPEATED_HAN_RATIO:
                    findings.append(
                        Finding(
                            "repeated-biography-padding",
                            "error",
                            "deep_biography",
                            f"Repeated normalized paragraphs or fixed-size chunks contribute {stats.repeated_ratio:.1%} of body Han characters; maximum is {MAX_REPEATED_HAN_RATIO:.0%}.",
                        )
                    )
                if not text.split("---", 2)[-1].strip():
                    findings.append(Finding("empty-biography-body", "error", "deep_biography", "A biography needs an actual narrative body, not metadata alone."))
                if minimum_characters is not None and stats.effective_han < minimum_characters:
                    findings.append(
                        Finding(
                            "biography-too-short",
                            "error",
                            "deep_biography",
                            f"Counted {stats.effective_han} non-repeated body Han characters; requires at least {minimum_characters}.",
                        )
                    )

    shared_refs_raw = biography.get("shared_history_refs", [])
    shared_refs = _string_list(shared_refs_raw) if _has_content(shared_refs_raw) else []
    if shared_refs is None:
        findings.append(Finding("invalid-shared-history-refs", "error", "deep_biography.shared_history_refs", "shared_history_refs must be a list of life-path references."))
        shared_refs = []
    if len(shared_refs) != len(set(shared_refs)):
        findings.append(Finding("duplicate-reference", "error", "deep_biography.shared_history_refs", "Shared history references are repeated."))

    for reference in shared_refs:
        match = REFERENCE_PATTERN.fullmatch(reference)
        if not match:
            findings.append(Finding("invalid-life-path-reference", "error", "deep_biography.shared_history_refs", f"Invalid reference: {reference}."))
            continue
        branch_id, node_id = match.groups()
        _validate_reference(
            findings,
            branch_id,
            node_id,
            "deep_biography.shared_history_refs",
            candidates,
            locked_branch_id=locked_branch_id,
            downstream=state == "locked",
        )

    shared_event_ids_raw = biography.get("shared_event_ids", [])
    shared_event_ids = _string_list(shared_event_ids_raw) if _has_content(shared_event_ids_raw) else []
    if shared_event_ids is None:
        findings.append(
            Finding("invalid-shared-event-ids", "error", "deep_biography.shared_event_ids", "shared_event_ids must be a list of stable event IDs.")
        )
        shared_event_ids = []
    elif len(shared_event_ids) != len(set(shared_event_ids)):
        findings.append(Finding("duplicate-reference", "error", "deep_biography.shared_event_ids", "Shared event IDs are repeated."))
    relationship_ledger_file = biography.get("relationship_ledger_file")
    has_shared_history = bool(shared_refs or shared_event_ids)
    if has_shared_history:
        if not shared_refs or not shared_event_ids:
            findings.append(
                Finding(
                    "incomplete-shared-event-declaration",
                    "error",
                    "deep_biography",
                    "Shared history requires both locked node references and stable shared_event_ids.",
                )
            )
        if not isinstance(relationship_ledger_file, str) or not relationship_ledger_file.strip():
            findings.append(
                Finding(
                    "missing-relationship-ledger",
                    "error",
                    "deep_biography.relationship_ledger_file",
                    "Shared history requires a project relationship ledger that can be audited automatically.",
                )
            )
    elif _has_content(relationship_ledger_file) and not isinstance(relationship_ledger_file, str):
        findings.append(
            Finding("invalid-relationship-ledger-path", "error", "deep_biography.relationship_ledger_file", "relationship_ledger_file must be a path string or null.")
        )

    runtime_raw = payload.get("compiled_runtime")
    runtime = runtime_raw if isinstance(runtime_raw, dict) else {}
    if runtime_raw is not None and not isinstance(runtime_raw, dict):
        findings.append(Finding("invalid-compiled-runtime", "error", "compiled_runtime", "compiled_runtime must be a mapping."))
    for field in RUNTIME_FIELDS:
        _missing(findings, runtime, field, "compiled_runtime", strict=preparing_selection, require_content=False)
    source_refs_raw = runtime.get("source_refs", [])
    source_refs = _string_list(source_refs_raw) if _has_content(source_refs_raw) else []
    if source_refs is None:
        findings.append(
            Finding(
                "invalid-runtime-source-refs",
                "error",
                "compiled_runtime.source_refs",
                "source_refs must contain only non-empty life-path references.",
            )
        )
        source_refs = []
    for reference in source_refs:
        match = REFERENCE_PATTERN.fullmatch(reference)
        if not match:
            findings.append(
                Finding(
                    "invalid-life-path-reference",
                    "error",
                    "compiled_runtime.source_refs",
                    f"Invalid reference: {reference}.",
                )
            )
            continue
        branch_id, node_id = match.groups()
        _validate_reference(
            findings,
            branch_id,
            node_id,
            "compiled_runtime.source_refs",
            candidates,
            locked_branch_id=locked_branch_id,
            downstream=True,
        )

    artifact_files_raw = runtime.get("artifact_files", [])
    if artifact_files_raw is None:
        artifact_files_raw = []
    if not isinstance(artifact_files_raw, list):
        findings.append(Finding("invalid-artifact-files", "error", "compiled_runtime.artifact_files", "artifact_files must be a list of provenance-bound file records."))
        artifact_files: list[dict[str, Any]] = []
    else:
        artifact_files = []
        for index, record in enumerate(artifact_files_raw, start=1):
            if not isinstance(record, dict):
                findings.append(
                    Finding(
                        "invalid-artifact-record",
                        "error",
                        f"compiled_runtime.artifact_files[{index}]",
                        "Each compiled artifact must be a mapping with path, artifact_type, sha256, source_refs, and upstream revision/hash bindings.",
                    )
                )
                continue
            artifact_files.append(record)
    artifact_root = _project_root_for(manifest_path)
    artifact_documents: list[tuple[str, str]] = []
    artifact_paths_seen: set[str] = set()
    artifact_source_refs: set[str] = set()
    inferred_formal_scene_artifact = False
    compiled_relationship_ledger_seen = False
    declared_relationship_ledger_path: Optional[Path] = None
    if isinstance(relationship_ledger_file, str) and relationship_ledger_file.strip():
        supplied_ledger = Path(relationship_ledger_file.strip())
        lexical_ledger = supplied_ledger if supplied_ledger.is_absolute() else artifact_root / supplied_ledger
        if _path_is_within(_lexical_absolute(lexical_ledger), _lexical_absolute(artifact_root)) and not _uses_symlink(
            lexical_ledger, artifact_root
        ):
            declared_relationship_ledger_path = lexical_ledger.resolve()
    for index, artifact_record in enumerate(artifact_files, start=1):
        location = f"compiled_runtime.artifact_files[{index}]"
        for field in (
            "path",
            "artifact_type",
            "sha256",
            "source_refs",
            "compiled_for_character_id",
            "compiled_for_package_context_id",
            "compiled_from_lock_revision",
            "compiled_from_fact_boundary_sha256",
            "compiled_from_candidate_sha256",
            "compiled_from_biography_revision",
            "compiled_from_biography_sha256",
        ):
            _missing(
                findings,
                artifact_record,
                field,
                location,
                strict=True,
                require_content=field not in {"compiled_from_biography_revision", "compiled_from_biography_sha256"} or mode == "deep",
            )
        artifact_file = artifact_record.get("path")
        artifact_type = artifact_record.get("artifact_type")
        declared_sha256 = artifact_record.get("sha256")
        record_refs_raw = artifact_record.get("source_refs")
        record_refs = _string_list(record_refs_raw) if _has_content(record_refs_raw) else []
        if not isinstance(artifact_file, str) or not artifact_file.strip():
            findings.append(Finding("invalid-artifact-path", "error", location, "Artifact path must be a non-empty string."))
            continue
        artifact_file = artifact_file.strip()
        if artifact_file in artifact_paths_seen:
            findings.append(Finding("duplicate-reference", "error", location, f"Compiled artifact path is repeated: {artifact_file}."))
        artifact_paths_seen.add(artifact_file)
        if artifact_type not in ARTIFACT_TYPES:
            findings.append(Finding("invalid-artifact-type", "error", location, f"Unsupported artifact_type: {artifact_type!r}."))
        if not isinstance(declared_sha256, str) or not SHA256_PATTERN.fullmatch(declared_sha256):
            findings.append(Finding("invalid-artifact-sha256", "error", location, "sha256 must be a lowercase 64-character digest."))
        if record_refs is None or not record_refs:
            findings.append(Finding("missing-artifact-source-refs", "error", location, "Every compiled artifact record requires canonical locked life-path source_refs."))
            record_refs = []
        for reference in record_refs:
            match = REFERENCE_PATTERN.fullmatch(reference)
            if not match:
                findings.append(Finding("invalid-life-path-reference", "error", location, f"Invalid artifact source ref: {reference!r}."))
                continue
            artifact_source_refs.add(reference)
            branch_id, node_id = match.groups()
            _validate_reference(
                findings,
                branch_id,
                node_id,
                location,
                candidates,
                locked_branch_id=locked_branch_id,
                downstream=True,
            )
        record_bindings = {
            "compiled_for_character_id": character_id,
            "compiled_for_package_context_id": package_context_id,
            "compiled_from_lock_revision": lock_revision,
            "compiled_from_fact_boundary_sha256": current_fact_boundary_hash,
            "compiled_from_candidate_sha256": locked_candidate_hash,
        }
        if mode == "deep":
            record_bindings.update(
                {
                    "compiled_from_biography_revision": biography_revision,
                    "compiled_from_biography_sha256": biography_sha256,
                }
            )
        for field, expected in record_bindings.items():
            if artifact_record.get(field) != expected:
                findings.append(Finding("artifact-provenance-binding-mismatch", "error", location, f"{field} must equal {expected!r}."))

        normalized_artifact_path = artifact_file.replace("\\", "/").lower()
        basename = Path(artifact_file).name.lower()
        if (
            artifact_type in FORMAL_SCENE_ARTIFACT_TYPES
            or Path(artifact_file).suffix.lower() == ".fountain"
            or basename in {
                "scene-contract.yaml",
                "turn-state.yaml",
                "beat-map.yaml",
                "storyboard.yaml",
                "storyboard.json",
                "storyboard.csv",
                "continuity.yaml",
                "asset-contract.yaml",
                "video-task.yaml",
            }
            or any(
                segment in normalized_artifact_path.split("/")
                for segment in {"03-scene", "04-screenplay", "05-storyboard", "06-continuity", "07-adapter"}
            )
        ):
            inferred_formal_scene_artifact = True

        supplied_path = Path(artifact_file)
        lexical_path = supplied_path if supplied_path.is_absolute() else artifact_root / supplied_path
        if _uses_symlink(lexical_path, artifact_root):
            findings.append(
                Finding(
                    "runtime-artifact-symlink",
                    "error",
                    location,
                    f"Compiled runtime artifact cannot traverse a symbolic link: {lexical_path}.",
                )
            )
            continue
        resolved_path = lexical_path.resolve()
        if not _path_is_within(resolved_path, artifact_root):
            findings.append(
                Finding(
                    "runtime-artifact-path-escape",
                    "error",
                    location,
                    f"Compiled runtime artifact must remain within project root {artifact_root}: {resolved_path}.",
                )
            )
            continue
        if not resolved_path.is_file():
            findings.append(
                Finding(
                    "missing-runtime-artifact",
                    "error",
                    location,
                    f"Compiled runtime artifact does not exist: {resolved_path}.",
                )
            )
            continue
        try:
            text = resolved_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(
                Finding(
                    "unreadable-runtime-artifact",
                    "error",
                    location,
                    f"Compiled runtime artifact must be a readable UTF-8 regular file: {exc}.",
                )
            )
            continue
        actual_sha256 = file_sha256(resolved_path)
        if declared_sha256 != actual_sha256:
            findings.append(
                Finding("runtime-artifact-hash-mismatch", "error", location, f"Declared artifact sha256 does not match {resolved_path}.")
            )
        file_refs = {f"life-path:{branch}/{node}" for branch, node in _references(text)}
        if artifact_type in STRUCTURED_ARTIFACT_TYPES:
            structured_artifact: Any = None
            if yaml is None:
                findings.append(Finding("unparsed-structured-artifact", "error", location, "PyYAML is required to audit structured runtime artifacts."))
            else:
                try:
                    structured_artifact = yaml.safe_load(text)
                except yaml.YAMLError as exc:
                    findings.append(Finding("unparsed-structured-artifact", "error", location, f"Structured artifact is invalid YAML/JSON: {exc}."))
                else:
                    if not isinstance(structured_artifact, (dict, list)):
                        findings.append(Finding("unparsed-structured-artifact", "error", location, "Structured artifact must contain a mapping or list."))
                    elif artifact_type == "other_structured":
                        inferred_kind = _structured_artifact_kind(structured_artifact)
                        if inferred_kind is not None:
                            findings.append(
                                Finding(
                                    "artifact-type-declaration-mismatch",
                                    "error",
                                    location,
                                    f"Artifact content identifies {inferred_kind!r}; declaring it as other_structured cannot bypass its gates.",
                                )
                            )
                            artifact_type = inferred_kind
                            if artifact_type in FORMAL_SCENE_ARTIFACT_TYPES:
                                inferred_formal_scene_artifact = True
                    if artifact_type == "relationship_ledger" and isinstance(structured_artifact, dict):
                        compiled_relationship_ledger_seen = True
                        if declared_relationship_ledger_path is None:
                            findings.append(
                                Finding(
                                    "compiled-relationship-ledger-not-declared",
                                    "error",
                                    location,
                                    "A compiled relationship ledger must be explicitly bound by deep_biography.relationship_ledger_file.",
                                )
                            )
                        elif resolved_path != declared_relationship_ledger_path:
                            findings.append(
                                Finding(
                                    "compiled-relationship-ledger-binding-mismatch",
                                    "error",
                                    location,
                                    "Compiled relationship-ledger artifact does not match the exact ledger declared by the workbench.",
                                )
                            )
                        ledger_claim_scope = _relationship_ledger_claim_scope(
                            structured_artifact,
                            character_id,
                            findings=findings,
                            location=f"{location}.relationship_claims",
                        )
                        scope_text = json.dumps(ledger_claim_scope, ensure_ascii=False, default=str)
                        file_refs = {f"life-path:{branch}/{node}" for branch, node in _references(scope_text)}
                        _audit_structured_downstream(
                            ledger_claim_scope,
                            f"{location}.relationship_claims",
                            findings,
                            candidates,
                            locked_branch_id=locked_branch_id,
                            lock_revision=lock_revision,
                            fact_boundary_hash=current_fact_boundary_hash,
                            locked_candidate_hash=locked_candidate_hash,
                            biography_revision=biography_revision,
                            biography_sha256=biography_sha256,
                            character_id=character_id,
                            package_context_id=package_context_id,
                        )
                        for branch_id, node_id in _references(scope_text):
                            _validate_reference(
                                findings,
                                branch_id,
                                node_id,
                                f"{location}.relationship_claims",
                                candidates,
                                locked_branch_id=locked_branch_id,
                                downstream=True,
                            )
                    elif artifact_type in PER_CHARACTER_ARTIFACT_TYPES:
                        if not isinstance(structured_artifact, dict):
                            findings.append(
                                Finding("invalid-character-artifact", "error", location, "A per-character artifact must be a mapping.")
                            )
                        else:
                            provenance = structured_artifact.get("compiled_provenance")
                            if not isinstance(provenance, dict):
                                findings.append(
                                    Finding(
                                        "missing-character-artifact-identity",
                                        "error",
                                        location,
                                        "A per-character artifact requires compiled_provenance bound to character_id and package_context_id.",
                                    )
                                )
                            else:
                                if provenance.get("compiled_for_character_id") != character_id:
                                    findings.append(
                                        Finding(
                                            "compiled-character-mismatch",
                                            "error",
                                            f"{location}.compiled_provenance",
                                            "Per-character artifact provenance does not match the audited character.",
                                        )
                                    )
                                if provenance.get("compiled_for_package_context_id") != package_context_id:
                                    findings.append(
                                        Finding(
                                            "compiled-package-context-mismatch",
                                            "error",
                                            f"{location}.compiled_provenance",
                                            "Per-character artifact provenance does not match the audited package context.",
                                        )
                                    )
                            if artifact_type == "character":
                                character_record = structured_artifact.get("character")
                                asset_character_id = character_record.get("id") if isinstance(character_record, dict) else None
                            else:
                                asset_character_id = structured_artifact.get("character_id")
                            if asset_character_id != character_id:
                                findings.append(
                                    Finding(
                                        "character-artifact-identity-mismatch",
                                        "error",
                                        location,
                                        "Per-character artifact identity does not match the audited workbench character_id.",
                                    )
                                )
                    elif artifact_type in MULTI_CHARACTER_ARTIFACT_TYPES:
                        if not isinstance(structured_artifact, dict):
                            findings.append(
                                Finding("invalid-multi-character-artifact", "error", location, "A multi-character artifact must be a mapping.")
                            )
                        else:
                            character_sources = structured_artifact.get("character_sources")
                            if not isinstance(character_sources, list):
                                findings.append(
                                    Finding(
                                        "missing-character-sources",
                                        "error",
                                        location,
                                        "Shared scene-to-video artifacts require character_sources provenance for every participating character package.",
                                    )
                                )
                            else:
                                source_character_ids = {
                                    str(item.get("character_id"))
                                    for item in character_sources
                                    if isinstance(item, dict) and _has_content(item.get("character_id"))
                                }
                                participant_ids = _artifact_participant_ids(artifact_type, structured_artifact)
                                missing_participant_sources = participant_ids - source_character_ids
                                if missing_participant_sources:
                                    findings.append(
                                        Finding(
                                            "missing-participant-character-source",
                                            "error",
                                            location,
                                            f"Shared artifact participants lack character_sources provenance: {sorted(missing_participant_sources)}.",
                                        )
                                    )
                                matching_sources = [
                                    item
                                    for item in character_sources
                                    if isinstance(item, dict)
                                    and item.get("character_id") == character_id
                                    and item.get("package_context_id") == package_context_id
                                ]
                                if len(matching_sources) == 1:
                                    current_refs = _string_list(matching_sources[0].get("source_refs"))
                                    file_refs = set(current_refs or [])
                                    nested_refs = _scoped_nested_life_path_refs(structured_artifact, character_id)
                                    if nested_refs and nested_refs != file_refs:
                                        findings.append(
                                            Finding(
                                                "character-source-nested-closure-mismatch",
                                                "error",
                                                location,
                                                "The current character_sources source_refs must exactly match canonical refs used by current-character nested claims when such claims are present.",
                                            )
                                        )
                                else:
                                    file_refs = set()
            if not file_refs:
                findings.append(
                    Finding(
                        "missing-claim-provenance",
                        "error",
                        location,
                        "A formal structured runtime artifact must contain canonical life-path source_refs; omitting provenance cannot hide derived claims.",
                    )
                )
            elif file_refs != set(record_refs):
                findings.append(
                    Finding(
                        "artifact-source-closure-mismatch",
                        "error",
                        location,
                        "Artifact-record source_refs must exactly match canonical life-path references present in the structured artifact.",
                    )
                )
        if artifact_type != "relationship_ledger":
            artifact_documents.append((str(resolved_path), text))
    if declared_relationship_ledger_path is not None and str(declared_relationship_ledger_path) in {
        str((Path(path) if Path(path).is_absolute() else artifact_root / path).resolve())
        for path in artifact_paths_seen
    } and not compiled_relationship_ledger_seen:
        findings.append(
            Finding(
                "relationship-ledger-artifact-type-mismatch",
                "error",
                "compiled_runtime.artifact_files",
                "The artifact at deep_biography.relationship_ledger_file must be declared or structurally identified as relationship_ledger.",
            )
        )
    if artifact_files and artifact_source_refs != set(source_refs):
        findings.append(
            Finding(
                "runtime-source-closure-mismatch",
                "error",
                "compiled_runtime.source_refs",
                "Runtime source_refs must equal the union of provenance refs bound to its exact artifact files.",
            )
        )
    compiled_revision = runtime.get("compiled_from_lock_revision")
    compiled_for_character_id = runtime.get("compiled_for_character_id")
    compiled_for_package_context_id = runtime.get("compiled_for_package_context_id")
    compiled_fact_boundary_sha256 = runtime.get("compiled_from_fact_boundary_sha256")
    compiled_candidate_sha256 = runtime.get("compiled_from_candidate_sha256")
    compiled_biography_revision = runtime.get("compiled_from_biography_revision")
    compiled_biography_sha256 = runtime.get("compiled_from_biography_sha256")
    if artifact_files and locked_branch_id is None:
        findings.append(Finding("unlocked-compiled-runtime", "error", "compiled_runtime", "Only a locked selection may have compiled artifact files."))
    if artifact_files and not source_refs:
        findings.append(
            Finding(
                "missing-runtime-source-refs",
                "error",
                "compiled_runtime",
                "Compiled artifact files require locked life-path source_refs.",
            )
        )
    if artifact_files and not _has_content(compiled_revision):
        findings.append(
            Finding("missing-compiled-revision", "error", "compiled_runtime", "Compiled artifact files require compiled_from_lock_revision.")
        )
    if artifact_files and compiled_for_character_id != character_id:
        findings.append(
            Finding(
                "compiled-character-mismatch",
                "error",
                "compiled_runtime",
                "compiled_for_character_id does not match the workbench character_id.",
            )
        )
    if artifact_files and compiled_for_package_context_id != package_context_id:
        findings.append(
            Finding(
                "compiled-package-context-mismatch",
                "error",
                "compiled_runtime",
                "compiled_for_package_context_id does not match the workbench package_context_id.",
            )
        )
    if _has_content(compiled_revision) and compiled_revision != lock_revision:
        findings.append(
            Finding(
                "compiled-revision-mismatch",
                "error",
                "compiled_runtime",
                f"compiled_from_lock_revision {compiled_revision!r} does not equal lock_revision {lock_revision!r}.",
            )
        )
    if artifact_files and compiled_fact_boundary_sha256 != current_fact_boundary_hash:
        findings.append(
            Finding(
                "compiled-fact-boundary-hash-mismatch",
                "error",
                "compiled_runtime",
                "compiled_from_fact_boundary_sha256 does not match the current epistemic boundary.",
            )
        )
    if artifact_files and compiled_candidate_sha256 != locked_candidate_hash:
        findings.append(
            Finding(
                "compiled-candidate-hash-mismatch",
                "error",
                "compiled_runtime",
                "compiled_from_candidate_sha256 does not match the current locked candidate content.",
            )
        )
    if artifact_files and mode == "deep":
        if compiled_biography_revision != biography_revision:
            findings.append(
                Finding(
                    "compiled-biography-revision-mismatch",
                    "error",
                    "compiled_runtime",
                    f"compiled_from_biography_revision {compiled_biography_revision!r} does not equal biography_revision {biography_revision!r}.",
                )
            )
        if not isinstance(compiled_biography_sha256, str) or compiled_biography_sha256 != biography_sha256:
            findings.append(
                Finding(
                    "compiled-biography-hash-mismatch",
                    "error",
                    "compiled_runtime",
                    "compiled_from_biography_sha256 does not match the current locked biography body.",
                )
            )

    formal_scene_compilation = runtime.get("formal_scene_compilation", False)
    if not isinstance(formal_scene_compilation, bool):
        findings.append(
            Finding(
                "invalid-formal-scene-compilation",
                "error",
                "compiled_runtime.formal_scene_compilation",
                "formal_scene_compilation must be boolean.",
            )
        )
    if inferred_formal_scene_artifact and formal_scene_compilation is not True:
        findings.append(
            Finding(
                "formal-scene-declaration-mismatch",
                "error",
                "compiled_runtime.formal_scene_compilation",
                "Scene, screenplay, storyboard, or adapter artifacts require formal_scene_compilation=true; the outline gate cannot be disabled by a false declaration.",
            )
        )
    effective_formal_scene_compilation = formal_scene_compilation is True or inferred_formal_scene_artifact
    if effective_formal_scene_compilation:
        outline_raw = payload.get("outline_review")
        outline = outline_raw if isinstance(outline_raw, dict) else {}
        if not isinstance(outline_raw, dict):
            findings.append(Finding("invalid-outline-review", "error", "outline_review", "Formal scene compilation requires outline_review."))
        for field in (
            "input_outline_ref",
            "input_outline_file",
            "input_outline_sha256",
            "input_outline_version",
            "reviewed_against_lock_revision",
            "reviewed_against_fact_boundary_sha256",
            "reviewed_against_candidate_sha256",
            "status",
            "conflicts",
        ):
            _missing(
                findings,
                outline,
                field,
                "outline_review",
                strict=True,
                require_content=field != "conflicts",
            )
        outline_source_valid = True
        outline_file_value = outline.get("input_outline_file")
        declared_outline_sha256 = outline.get("input_outline_sha256")
        if not isinstance(declared_outline_sha256, str) or not SHA256_PATTERN.fullmatch(declared_outline_sha256):
            findings.append(
                Finding(
                    "invalid-outline-sha256",
                    "error",
                    "outline_review.input_outline_sha256",
                    "input_outline_sha256 must be a lowercase 64-character digest of the reviewed outline file.",
                )
            )
            outline_source_valid = False
        if not isinstance(outline_file_value, str) or not outline_file_value.strip():
            outline_source_valid = False
        else:
            supplied_outline = Path(outline_file_value.strip())
            lexical_outline = supplied_outline if supplied_outline.is_absolute() else artifact_root / supplied_outline
            if _uses_symlink(lexical_outline, artifact_root):
                findings.append(
                    Finding(
                        "outline-file-symlink",
                        "error",
                        "outline_review.input_outline_file",
                        "The reviewed outline file cannot traverse a symbolic link.",
                    )
                )
                outline_source_valid = False
            else:
                resolved_outline = lexical_outline.resolve()
                if not _path_is_within(resolved_outline, artifact_root):
                    findings.append(
                        Finding(
                            "outline-file-path-escape",
                            "error",
                            "outline_review.input_outline_file",
                            "The reviewed outline file must remain inside the project root.",
                        )
                    )
                    outline_source_valid = False
                elif not resolved_outline.is_file():
                    findings.append(
                        Finding(
                            "missing-outline-file",
                            "error",
                            "outline_review.input_outline_file",
                            f"Reviewed outline file does not exist: {resolved_outline}.",
                        )
                    )
                    outline_source_valid = False
                else:
                    try:
                        resolved_outline.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as exc:
                        findings.append(
                            Finding(
                                "unreadable-outline-file",
                                "error",
                                "outline_review.input_outline_file",
                                f"Reviewed outline must be a readable UTF-8 regular file: {exc}.",
                            )
                        )
                        outline_source_valid = False
                    else:
                        if declared_outline_sha256 != file_sha256(resolved_outline):
                            findings.append(
                                Finding(
                                    "outline-file-hash-mismatch",
                                    "error",
                                    "outline_review.input_outline_sha256",
                                    "The outline changed after review; formal scene compilation requires a new outline review.",
                                )
                            )
                            outline_source_valid = False
        review_status = outline.get("status")
        if review_status not in OUTLINE_REVIEW_STATUSES:
            findings.append(Finding("invalid-outline-review-status", "error", "outline_review", f"Unsupported status: {review_status!r}."))
        if outline.get("reviewed_against_lock_revision") != lock_revision:
            findings.append(Finding("outline-review-lock-mismatch", "error", "outline_review", "Outline review does not match the current path lock revision."))
        if outline.get("reviewed_against_fact_boundary_sha256") != current_fact_boundary_hash:
            findings.append(Finding("outline-review-fact-boundary-mismatch", "error", "outline_review", "Outline review does not match the current fact boundary."))
        if outline.get("reviewed_against_candidate_sha256") != locked_candidate_hash:
            findings.append(Finding("outline-review-candidate-mismatch", "error", "outline_review", "Outline review does not match the current locked candidate content."))
        conflicts = outline.get("conflicts")
        if not isinstance(conflicts, list):
            findings.append(Finding("invalid-outline-conflicts", "error", "outline_review.conflicts", "conflicts must be a list."))
            conflicts = []
        unresolved = not outline_source_valid
        for index, conflict in enumerate(conflicts, start=1):
            location = f"outline_review.conflicts[{index}]"
            if not isinstance(conflict, dict):
                findings.append(Finding("invalid-outline-conflict", "error", location, "Each outline conflict must be a mapping."))
                unresolved = True
                continue
            for field in ("id", "description", "options_and_costs", "status", "author_decision"):
                _missing(findings, conflict, field, location, strict=True, require_content=field != "author_decision")
            if conflict.get("status") != "resolved" or not _valid_author_decision(conflict.get("author_decision")):
                unresolved = True
        if review_status not in {"clear", "resolved"} or unresolved:
            findings.append(
                Finding(
                    "formal-scene-blocked-by-outline-review",
                    "error",
                    "outline_review",
                    "Formal scene compilation is blocked until the current locked life has a clear review or every hard conflict has an author-approved resolution.",
                )
            )

    downstream_items: list[tuple[str, str]] = []
    if runtime:
        downstream_items.append(("compiled_runtime", json.dumps(runtime, ensure_ascii=False)))
    downstream_items.extend(artifact_documents)
    downstream_items.extend(downstream_documents)
    for location, text in downstream_items:
        parsed_structured = False
        if yaml is not None:
            try:
                structured = yaml.safe_load(text)
            except yaml.YAMLError:
                structured = None
            if isinstance(structured, (dict, list)):
                parsed_structured = True
                _audit_structured_downstream(
                    structured,
                    location,
                    findings,
                    candidates,
                    character_id=character_id,
                    package_context_id=package_context_id,
                    locked_branch_id=locked_branch_id,
                    lock_revision=lock_revision,
                    fact_boundary_hash=current_fact_boundary_hash,
                    locked_candidate_hash=locked_candidate_hash,
                    biography_revision=biography_revision,
                    biography_sha256=biography_sha256,
                )
        if not parsed_structured:
            for branch_id, node_id in _references(text):
                _validate_reference(
                    findings,
                    branch_id,
                    node_id,
                    location,
                    candidates,
                    locked_branch_id=locked_branch_id,
                    downstream=True,
                )

    return list(dict.fromkeys(findings))


def audit_shared_event_registry(
    ledger_path: Path,
    *,
    required_event_ids: Iterable[str] = (),
    required_character_id: Optional[str] = None,
    required_workbench_path: Optional[Path] = None,
) -> list[Finding]:
    findings: list[Finding] = []
    lexical_ledger_path = _lexical_absolute(ledger_path)
    project_root = _project_root_for(lexical_ledger_path)
    if _uses_symlink(lexical_ledger_path, project_root):
        return [
            Finding(
                "relationship-ledger-symlink",
                "error",
                str(lexical_ledger_path),
                "Relationship ledger cannot traverse a symbolic link.",
            )
        ]
    ledger_path = lexical_ledger_path.resolve()
    if not _path_is_within(ledger_path, project_root):
        return [
            Finding(
                "relationship-ledger-path-escape",
                "error",
                str(ledger_path),
                "Relationship ledger must remain inside the project root.",
            )
        ]
    ledger = load_yaml_mapping(ledger_path)
    events_raw = ledger.get("shared_event_registry")
    if not isinstance(events_raw, list):
        return [
            Finding(
                "invalid-shared-event-registry",
                "error",
                str(ledger_path),
                "shared_event_registry must be a list.",
            )
        ]

    event_ids: set[str] = set()
    registry_participants: dict[str, set[str]] = {}
    registry_workbench_bindings: dict[str, set[tuple[str, Path]]] = {}
    audited_workbenches: set[Path] = set()
    for event_index, event_raw in enumerate(events_raw, start=1):
        location = f"shared_event_registry[{event_index}]"
        if not isinstance(event_raw, dict):
            findings.append(Finding("invalid-shared-event", "error", location, "Each shared event must be a mapping."))
            continue
        event_id = event_raw.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip() or not ID_PATTERN.fullmatch(event_id.strip()):
            findings.append(Finding("invalid-shared-event-id", "error", location, "Each shared event requires a stable event_id."))
            continue
        event_id = event_id.strip()
        location = f"shared_event:{event_id}"
        if event_id in event_ids:
            findings.append(Finding("duplicate-id", "error", location, f"Shared event ID is repeated: {event_id}."))
            continue
        event_ids.add(event_id)
        event_revision = event_raw.get("event_revision")
        if not _positive_int(event_revision):
            findings.append(
                Finding(
                    "invalid-shared-event-revision",
                    "error",
                    location,
                    "An approved shared event requires event_revision > 0.",
                )
            )
        current_event_hash = shared_event_sha256(event_raw)
        declared_event_hash = event_raw.get("event_sha256")
        if not isinstance(declared_event_hash, str) or not SHA256_PATTERN.fullmatch(declared_event_hash):
            findings.append(
                Finding(
                    "invalid-shared-event-sha256",
                    "error",
                    location,
                    "event_sha256 must be a lowercase 64-character digest of the event content.",
                )
            )
        elif declared_event_hash != current_event_hash:
            findings.append(
                Finding(
                    "shared-event-hash-mismatch",
                    "error",
                    location,
                    "Shared-event content changed without a matching content hash and renewed author approval.",
                )
            )
        event_approval_raw = event_raw.get("author_approval")
        event_approval = event_approval_raw if isinstance(event_approval_raw, dict) else {}
        if not isinstance(event_approval_raw, dict) or event_approval.get("state") != "approved" or not _valid_author_decision(
            event_approval.get("decision")
        ):
            findings.append(
                Finding(
                    "shared-event-author-approval-required",
                    "error",
                    location,
                    "A shared event requires explicit author approval of its exact event ID, revision, and content hash.",
                )
            )
        else:
            approval_bindings = {
                "approved_event_id": event_id,
                "approved_event_revision": event_revision,
                "approved_event_sha256": current_event_hash,
            }
            for field, expected in approval_bindings.items():
                if event_approval.get(field) != expected:
                    findings.append(
                        Finding(
                            "shared-event-approval-binding-mismatch",
                            "error",
                            location,
                            f"{field} must bind the current shared event value {expected!r}.",
                        )
                    )
        if not _has_content(event_raw.get("objective_core")):
            findings.append(Finding("missing-field", "error", location, "Missing or empty required field: objective_core."))
        time_window = event_raw.get("time_window")
        if not isinstance(time_window, dict):
            findings.append(Finding("invalid-shared-event-time", "error", location, "time_window must be a mapping."))
        else:
            for field in ("start", "end", "precision"):
                _missing(findings, time_window, field, f"{location}.time_window", strict=True)
            start = time_window.get("start")
            end = time_window.get("end")
            start_kind = _time_scalar_kind(start)
            end_kind = _time_scalar_kind(end)
            if start_kind is None or end_kind is None:
                findings.append(
                    Finding(
                        "invalid-shared-event-time",
                        "error",
                        f"{location}.time_window",
                        "start and end must be non-empty temporal scalars; numeric values must be finite.",
                    )
                )
            elif start_kind != end_kind:
                findings.append(
                    Finding(
                        "incompatible-shared-event-time-types",
                        "error",
                        f"{location}.time_window",
                        "start and end must use the same temporal representation type.",
                    )
                )
            start_comparable = _comparable_time(start)
            end_comparable = _comparable_time(end)
            if (
                start_comparable is not None
                and end_comparable is not None
                and start_comparable[0] == end_comparable[0]
                and start_comparable[1] > end_comparable[1]
            ):
                findings.append(
                    Finding(
                        "shared-event-time-reversed",
                        "error",
                        f"{location}.time_window",
                        "Comparable shared-event time windows require start <= end.",
                    )
                )
            if not isinstance(time_window.get("precision"), str) or not time_window["precision"].strip():
                findings.append(
                    Finding(
                        "invalid-shared-event-time-precision",
                        "error",
                        f"{location}.time_window.precision",
                        "precision must be a non-empty string describing temporal certainty.",
                    )
                )

        participants_raw = event_raw.get("participants")
        if not isinstance(participants_raw, list) or len(participants_raw) < 2:
            findings.append(
                Finding(
                    "too-few-shared-event-participants",
                    "error",
                    location,
                    "A shared event requires at least two participant bindings.",
                )
            )
            participants_raw = participants_raw if isinstance(participants_raw, list) else []
        participant_ids: set[str] = set()
        participant_workbench_bindings: set[tuple[str, Path]] = set()
        for participant_index, participant_raw in enumerate(participants_raw, start=1):
            participant_location = f"{location}.participants[{participant_index}]"
            if not isinstance(participant_raw, dict):
                findings.append(
                    Finding("invalid-shared-event-participant", "error", participant_location, "Participant binding must be a mapping.")
                )
                continue
            for field in (
                "character_id",
                "workbench_file",
                "branch_id",
                "life_path_lock_revision",
                "locked_fact_boundary_sha256",
                "locked_candidate_sha256",
                "biography_revision",
                "approved_biography_sha256",
                "node_refs",
                "perception_version",
                "memory_version",
            ):
                _missing(findings, participant_raw, field, participant_location, strict=True)
            character_id = participant_raw.get("character_id")
            if not isinstance(character_id, str) or not character_id.strip():
                continue
            character_id = character_id.strip()
            if character_id in participant_ids:
                findings.append(
                    Finding("duplicate-shared-event-participant", "error", participant_location, f"Character is repeated: {character_id}.")
                )
            participant_ids.add(character_id)

            workbench_file = participant_raw.get("workbench_file")
            if not isinstance(workbench_file, str) or not workbench_file.strip():
                continue
            supplied_path = Path(workbench_file)
            lexical_path = supplied_path if supplied_path.is_absolute() else project_root / supplied_path
            if _uses_symlink(lexical_path, project_root):
                findings.append(
                    Finding("shared-workbench-symlink", "error", participant_location, f"Workbench cannot traverse a symbolic link: {lexical_path}.")
                )
                continue
            workbench_path = lexical_path.resolve()
            if not _path_is_within(workbench_path, project_root):
                findings.append(
                    Finding("shared-workbench-path-escape", "error", participant_location, f"Workbench escapes project root: {workbench_path}.")
                )
                continue
            if not workbench_path.is_file():
                findings.append(
                    Finding("missing-shared-workbench", "error", participant_location, f"Workbench does not exist: {workbench_path}.")
                )
                continue
            participant_workbench_bindings.add((character_id, workbench_path))
            try:
                workbench = load_yaml_mapping(workbench_path)
            except (OSError, UnicodeError, ValueError) as exc:
                findings.append(Finding("invalid-shared-workbench", "error", participant_location, str(exc)))
                continue
            if workbench_path not in audited_workbenches:
                for item in audit_manifest(workbench, workbench_path, require_locked=True):
                    findings.append(
                        Finding(item.code, item.severity, f"{workbench_path}:{item.location}", item.message)
                    )
                audited_workbenches.add(workbench_path)

            if workbench.get("character_id") != character_id:
                findings.append(
                    Finding("shared-character-mismatch", "error", participant_location, "Participant character_id does not match workbench character_id.")
                )
            selection = workbench.get("selection") if isinstance(workbench.get("selection"), dict) else {}
            biography = workbench.get("deep_biography") if isinstance(workbench.get("deep_biography"), dict) else {}
            branch_id = participant_raw.get("branch_id")
            if (
                selection.get("state") != "locked"
                or selection.get("author_lock") is not True
                or branch_id != selection.get("selected_branch_id")
            ):
                findings.append(
                    Finding("shared-branch-not-locked", "error", participant_location, "Participant branch must equal the author-locked workbench branch.")
                )
            if participant_raw.get("life_path_lock_revision") != selection.get("lock_revision"):
                findings.append(
                    Finding("shared-lock-revision-mismatch", "error", participant_location, "Participant path-lock revision does not match its workbench.")
                )
            if participant_raw.get("locked_fact_boundary_sha256") != selection.get("locked_fact_boundary_sha256"):
                findings.append(
                    Finding("shared-fact-boundary-hash-mismatch", "error", participant_location, "Participant fact-boundary hash does not match its workbench lock.")
                )
            if participant_raw.get("locked_candidate_sha256") != selection.get("locked_candidate_sha256"):
                findings.append(
                    Finding("shared-candidate-hash-mismatch", "error", participant_location, "Participant candidate hash does not match its workbench lock.")
                )
            biography_approval = biography.get("author_approval") if isinstance(biography.get("author_approval"), dict) else {}
            if biography.get("status") != "ready" or biography_approval.get("state") != "approved":
                findings.append(
                    Finding("shared-biography-not-approved", "error", participant_location, "Participant biography must be ready and author-approved.")
                )
            if participant_raw.get("biography_revision") != biography.get("biography_revision"):
                findings.append(
                    Finding("shared-biography-revision-mismatch", "error", participant_location, "Participant biography revision does not match its workbench.")
                )
            if participant_raw.get("approved_biography_sha256") != biography_approval.get("approved_body_sha256"):
                findings.append(
                    Finding("shared-biography-hash-mismatch", "error", participant_location, "Participant approved biography hash does not match its workbench approval.")
                )

            declared_event_ids = biography.get("shared_event_ids") if isinstance(biography.get("shared_event_ids"), list) else []
            if event_id not in declared_event_ids:
                findings.append(
                    Finding("shared-event-not-declared-by-biography", "error", participant_location, f"Participant workbench does not declare shared event {event_id!r}.")
                )
            declared_ledger = biography.get("relationship_ledger_file")
            declared_ledger_path = None
            if isinstance(declared_ledger, str) and declared_ledger.strip():
                supplied_ledger = Path(declared_ledger)
                declared_ledger_path = (supplied_ledger if supplied_ledger.is_absolute() else project_root / supplied_ledger).resolve()
            if declared_ledger_path != ledger_path:
                findings.append(
                    Finding("shared-ledger-binding-mismatch", "error", participant_location, "Participant workbench does not bind this exact project relationship ledger.")
                )

            candidates_raw = workbench.get("candidates") if isinstance(workbench.get("candidates"), list) else []
            selected_candidate = next(
                (item for item in candidates_raw if isinstance(item, dict) and item.get("id") == branch_id),
                None,
            )
            node_ids = {
                item.get("id")
                for item in (selected_candidate or {}).get("causal_spine", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            node_refs = participant_raw.get("node_refs")
            if not isinstance(node_refs, list) or not node_refs:
                continue
            biography_shared_refs = biography.get("shared_history_refs")
            biography_shared_refs = biography_shared_refs if isinstance(biography_shared_refs, list) else []
            for reference in node_refs:
                match = REFERENCE_PATTERN.fullmatch(reference) if isinstance(reference, str) else None
                if not match:
                    findings.append(Finding("invalid-life-path-reference", "error", participant_location, f"Invalid node ref: {reference!r}."))
                    continue
                reference_branch, node_id = match.groups()
                if reference_branch != branch_id or node_id not in node_ids:
                    findings.append(
                        Finding("shared-node-reference-mismatch", "error", participant_location, f"Shared event node is not in the locked branch: {reference}.")
                    )
                if reference not in biography_shared_refs:
                    findings.append(
                        Finding("shared-node-not-in-biography", "error", participant_location, f"Approved biography does not declare shared history ref: {reference}.")
                    )
        registry_participants[event_id] = participant_ids
        registry_workbench_bindings[event_id] = participant_workbench_bindings

    contracts_raw = ledger.get("shared_memory_contracts", [])
    if contracts_raw is not None and not isinstance(contracts_raw, list):
        findings.append(Finding("invalid-shared-memory-contracts", "error", "shared_memory_contracts", "shared_memory_contracts must be a list."))
    elif isinstance(contracts_raw, list):
        for index, contract in enumerate(contracts_raw, start=1):
            if not isinstance(contract, dict):
                continue
            event_id = contract.get("shared_event_id")
            location = f"shared_memory_contracts[{index}]"
            if event_id not in event_ids:
                findings.append(Finding("unknown-shared-event", "error", location, f"Unknown shared_event_id: {event_id!r}."))
                continue
            participants = contract.get("participants", [])
            if (
                not isinstance(participants, list)
                or not all(isinstance(item, str) for item in participants)
                or not set(participants).issubset(registry_participants[event_id])
            ):
                findings.append(
                    Finding("shared-contract-participant-mismatch", "error", location, "Contract participants must belong to the referenced shared event.")
                )

    normalized_required_event_ids = {
        event_id.strip()
        for event_id in required_event_ids
        if isinstance(event_id, str) and event_id.strip()
    }
    required_workbench = required_workbench_path.resolve() if required_workbench_path is not None else None
    for event_id in sorted(normalized_required_event_ids):
        if event_id not in event_ids:
            findings.append(
                Finding(
                    "declared-shared-event-not-in-registry",
                    "error",
                    "deep_biography.shared_event_ids",
                    f"Declared shared event {event_id!r} does not exist in the bound relationship-ledger registry.",
                )
            )
        elif required_character_id is not None and required_workbench is not None and (
            required_character_id,
            required_workbench,
        ) not in registry_workbench_bindings.get(event_id, set()):
            findings.append(
                Finding(
                    "declared-shared-event-participant-mismatch",
                    "error",
                    "deep_biography.shared_event_ids",
                    f"Declared shared event {event_id!r} does not bind this character and exact workbench as a participant.",
                )
            )

    return list(dict.fromkeys(findings))


def audit_file(
    manifest_path: Path,
    *,
    require_locked: bool = False,
    downstream_paths: Iterable[Path] = (),
    relationship_ledger_path: Optional[Path] = None,
) -> list[Finding]:
    manifest_path = manifest_path.resolve()
    payload = load_yaml_mapping(manifest_path)
    downstream_documents: list[tuple[str, str]] = []
    for path_value in downstream_paths:
        path = path_value.resolve()
        downstream_documents.append((str(path), path.read_text(encoding="utf-8")))
    findings = audit_manifest(
        payload,
        manifest_path,
        require_locked=require_locked,
        downstream_documents=downstream_documents,
    )
    biography = payload.get("deep_biography") if isinstance(payload.get("deep_biography"), dict) else {}
    declared_ledger = biography.get("relationship_ledger_file")
    declared_ledger_path: Optional[Path] = None
    if isinstance(declared_ledger, str) and declared_ledger.strip():
        project_root = _project_root_for(manifest_path)
        supplied_path = Path(declared_ledger)
        lexical_path = supplied_path if supplied_path.is_absolute() else project_root / supplied_path
        if _uses_symlink(lexical_path, project_root):
            findings.append(
                Finding("relationship-ledger-symlink", "error", "deep_biography.relationship_ledger_file", "Relationship ledger cannot traverse a symbolic link.")
            )
        else:
            resolved_path = lexical_path.resolve()
            if not _path_is_within(resolved_path, project_root):
                findings.append(
                    Finding("relationship-ledger-path-escape", "error", "deep_biography.relationship_ledger_file", "Relationship ledger must remain inside the project root.")
                )
            elif not resolved_path.is_file():
                findings.append(
                    Finding("missing-relationship-ledger", "error", "deep_biography.relationship_ledger_file", f"Relationship ledger does not exist: {resolved_path}.")
                )
            else:
                declared_ledger_path = resolved_path
    explicit_ledger_lexical = _lexical_absolute(relationship_ledger_path) if relationship_ledger_path is not None else None
    explicit_ledger_resolved = explicit_ledger_lexical.resolve() if explicit_ledger_lexical is not None else None
    if explicit_ledger_resolved is not None and declared_ledger_path is not None and explicit_ledger_resolved != declared_ledger_path:
        findings.append(
            Finding("relationship-ledger-binding-mismatch", "error", "deep_biography.relationship_ledger_file", "CLI relationship ledger does not match the ledger bound by the workbench.")
        )
    ledger_to_audit = declared_ledger_path or explicit_ledger_lexical
    if ledger_to_audit is not None:
        declared_event_ids = biography.get("shared_event_ids")
        normalized_declared_event_ids = _string_list(declared_event_ids) if _has_content(declared_event_ids) else []
        required_event_ids = normalized_declared_event_ids or []
        required_character_id = payload.get("character_id")
        findings.extend(
            audit_shared_event_registry(
                ledger_to_audit,
                required_event_ids=required_event_ids,
                required_character_id=required_character_id.strip() if isinstance(required_character_id, str) else None,
                required_workbench_path=manifest_path,
            )
        )
    return list(dict.fromkeys(findings))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-locked", action="store_true")
    parser.add_argument("--downstream", action="append", type=Path, default=[])
    parser.add_argument("--relationship-ledger", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        findings = audit_file(
            args.manifest,
            require_locked=args.require_locked,
            downstream_paths=args.downstream,
            relationship_ledger_path=args.relationship_ledger,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR input: {exc}")
        return 2
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
        errors = sum(item.severity == "error" for item in findings)
        warnings = len(findings) - errors
        print(f"Errors: {errors}; warnings: {warnings}")
    else:
        print("Life-path workbench valid: no configured findings.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
