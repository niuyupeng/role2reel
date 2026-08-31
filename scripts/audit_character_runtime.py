#!/usr/bin/env python3
"""Audit Role2Reel's two-stage CharacterOS turn contract.

This checker validates explicit resource separation and references. It cannot decide
whether an interpretation is psychologically true or whether dialogue is good.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - CLI dependency boundary
    yaml = None


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    location: str
    message: str


@dataclass
class _LibraryIndex:
    """Character-scoped view of one or more runtime resource libraries."""

    provided: bool
    documents_by_character: dict[str, list[tuple[str, dict[str, Any]]]]
    entries_by_character: dict[str, dict[str, list[tuple[str, dict[str, Any]]]]]
    entry_owners: dict[str, set[str]]


@dataclass
class _RelationshipIndex:
    provided: bool
    records: dict[str, dict[str, list[tuple[str, dict[str, Any]]]]]
    owners: dict[str, dict[str, set[str]]]


def _nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _specified(value: Any) -> bool:
    """Whether a projection carries a value, including an explicit false boolean."""

    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _ids(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {
        item.get("id")
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
    }


def _normalized(value: Any) -> str:
    return re.sub(r"[\W_]+", "", value if isinstance(value, str) else "", flags=re.UNICODE).casefold()


def _equivalent_projection(left: Any, right: Any) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return _normalized(left) == _normalized(right)
    return left == right


def _reference_list(
    container: dict[str, Any],
    field: str,
    *,
    location: str,
    findings: list[Finding],
    list_code: str,
    item_code: str,
) -> list[str]:
    """Return only stable string references and report malformed items."""

    value = container.get(field)
    if value is None:
        return []
    if not isinstance(value, list):
        findings.append(Finding(list_code, "error", f"{location}.{field}", f"{field} must be a list."))
        return []
    refs: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            findings.append(
                Finding(
                    item_code,
                    "error",
                    f"{location}.{field}[{index}]",
                    f"{field} references must be non-empty strings.",
                )
            )
            continue
        refs.append(item)
    return refs


def _index_relationship_ledgers(value: Any) -> tuple[_RelationshipIndex, list[Finding]]:
    """Index relationship records by reference namespace and eligible character."""

    findings: list[Finding] = []
    namespaces = {
        "relationship_claim_ids": ("relationship_claim_records", "from_character"),
        "common_ground_proposition_ids": ("common_ground_propositions", "participants"),
        "second_order_belief_ids": ("second_order_beliefs", "holder_character_id"),
    }
    records: dict[str, dict[str, list[tuple[str, dict[str, Any]]]]] = {
        field: defaultdict(list) for field in namespaces
    }
    owners: dict[str, dict[str, set[str]]] = {field: defaultdict(set) for field in namespaces}

    if value is None:
        return _RelationshipIndex(False, {}, {}), findings
    if isinstance(value, dict):
        documents: list[tuple[str, Any]] = [("relationship_ledgers", value)]
    elif isinstance(value, (list, tuple)):
        documents = [(f"relationship_ledgers[{index}]", item) for index, item in enumerate(value)]
    else:
        findings.append(
            Finding(
                "invalid-relationship-ledgers",
                "error",
                "relationship_ledgers",
                "Relationship-ledger input must be a mapping or a list of mappings.",
            )
        )
        return _RelationshipIndex(True, {}, {}), findings

    for document_location, document in documents:
        if not isinstance(document, dict):
            findings.append(
                Finding(
                    "invalid-relationship-ledger-document",
                    "error",
                    document_location,
                    "Each relationship ledger must be a mapping.",
                )
            )
            continue
        for reference_field, (records_field, owner_field) in namespaces.items():
            items = document.get(records_field, [])
            if not isinstance(items, list):
                findings.append(
                    Finding(
                        "invalid-relationship-record-list",
                        "error",
                        f"{document_location}.{records_field}",
                        f"{records_field} must be a list.",
                    )
                )
                continue
            for item_index, item in enumerate(items):
                item_location = f"{document_location}.{records_field}[{item_index}]"
                if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                    findings.append(
                        Finding(
                            "invalid-relationship-record",
                            "error",
                            item_location,
                            f"Each {records_field} record requires a non-empty string id.",
                        )
                    )
                    continue
                item_id = item["id"]
                records[reference_field][item_id].append((item_location, item))
                raw_owner = item.get(owner_field)
                if owner_field == "participants":
                    if not isinstance(raw_owner, list) or any(
                        not isinstance(participant, str) or not participant.strip() for participant in raw_owner
                    ):
                        findings.append(
                            Finding(
                                "invalid-common-ground-participants",
                                "error",
                                f"{item_location}.participants",
                                "Common-ground participants must be a list of non-empty character IDs.",
                            )
                        )
                        continue
                    owners[reference_field][item_id].update(raw_owner)
                elif not isinstance(raw_owner, str) or not raw_owner.strip():
                    findings.append(
                        Finding(
                            "missing-relationship-record-character-id",
                            "error",
                            f"{item_location}.{owner_field}",
                            f"{owner_field} must identify the character who can retrieve this record.",
                        )
                    )
                else:
                    owners[reference_field][item_id].add(raw_owner)

    for reference_field, records_by_id in records.items():
        for item_id, matches in records_by_id.items():
            if len(matches) > 1:
                findings.append(
                    Finding(
                        "duplicate-relationship-reference-id",
                        "error",
                        "relationship_ledgers",
                        f"{reference_field} ID {item_id!r} appears more than once.",
                    )
                )
    return (
        _RelationshipIndex(
            True,
            {field: dict(items) for field, items in records.items()},
            {field: dict(items) for field, items in owners.items()},
        ),
        findings,
    )


def _index_libraries(
    value: Any,
    *,
    root: str,
    expected_purpose: str | None,
    entries_field: str,
    contract_code: str,
    missing_character_code: str,
    duplicate_character_code: str,
    invalid_entries_code: str,
    invalid_entry_code: str,
    duplicate_entry_code: str,
    entry_character_code: str,
    library_label: str,
    entry_label: str,
) -> tuple[_LibraryIndex, list[Finding]]:
    """Normalize a legacy single library or a per-character library list.

    Entry IDs are intentionally indexed inside their owning character namespace.
    The global owner index exists only to diagnose a reference that resolves for a
    different character; it is never used as a successful fallback.
    """

    findings: list[Finding] = []
    documents_by_character: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    entries_by_character: dict[str, dict[str, list[tuple[str, dict[str, Any]]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    entry_owners: dict[str, set[str]] = defaultdict(set)

    if value is None:
        return _LibraryIndex(False, {}, {}, {}), findings
    if isinstance(value, dict):
        raw_documents: list[tuple[str, Any]] = [(root, value)]
    elif isinstance(value, (list, tuple)):
        raw_documents = [(f"{root}[{index}]", item) for index, item in enumerate(value)]
    else:
        findings.append(
            Finding(
                f"invalid-{root.replace('_', '-')}",
                "error",
                root,
                f"{library_label} input must be a mapping or a list of per-character mappings.",
            )
        )
        return _LibraryIndex(True, {}, {}, {}), findings

    for document_location, document in raw_documents:
        if not isinstance(document, dict):
            findings.append(
                Finding(
                    f"invalid-{root.replace('_', '-')}-document",
                    "error",
                    document_location,
                    f"Each {library_label.lower()} document must be a mapping.",
                )
            )
            continue
        purpose = document.get("contract", {}).get("purpose") if isinstance(document.get("contract"), dict) else None
        if expected_purpose is not None and purpose != expected_purpose:
            findings.append(
                Finding(
                    contract_code,
                    "error",
                    f"{document_location}.contract.purpose",
                    f"{library_label} must declare {expected_purpose}.",
                )
            )
        character_id = document.get("character_id")
        valid_character_id = character_id.strip() if isinstance(character_id, str) else ""
        if not valid_character_id:
            findings.append(
                Finding(
                    missing_character_code,
                    "error",
                    f"{document_location}.character_id",
                    f"{library_label} requires character_id.",
                )
            )
        else:
            documents_by_character[valid_character_id].append((document_location, document))

        entries = document.get(entries_field, [])
        if not isinstance(entries, list):
            findings.append(
                Finding(
                    invalid_entries_code,
                    "error",
                    f"{document_location}.{entries_field}",
                    f"{entries_field} must be a list.",
                )
            )
            continue
        for entry_index, entry in enumerate(entries):
            entry_location = f"{document_location}.{entries_field}[{entry_index}]"
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"].strip():
                findings.append(
                    Finding(
                        invalid_entry_code,
                        "error",
                        entry_location,
                        f"Each {entry_label.lower()} requires a non-empty string id.",
                    )
                )
                continue
            entry_id = entry["id"]
            explicit_entry_character = entry.get("character_id")
            entry_character = (
                explicit_entry_character.strip()
                if isinstance(explicit_entry_character, str) and explicit_entry_character.strip()
                else valid_character_id
            )
            if entry_character:
                entry_owners[entry_id].add(entry_character)
            if valid_character_id:
                entries_by_character[valid_character_id][entry_id].append((entry_location, entry))
            if (
                valid_character_id
                and isinstance(explicit_entry_character, str)
                and explicit_entry_character.strip()
                and explicit_entry_character != valid_character_id
            ):
                findings.append(
                    Finding(
                        entry_character_code,
                        "error",
                        f"{entry_location}.character_id",
                        f"{entry_label} {entry_id!r} belongs to another character than its enclosing library.",
                    )
                )

    for character_id, documents in documents_by_character.items():
        if len(documents) > 1:
            findings.append(
                Finding(
                    duplicate_character_code,
                    "error",
                    root,
                    f"Provide exactly one {library_label.lower()} document for character_id {character_id!r}.",
                )
            )
    for character_id, entries in entries_by_character.items():
        for entry_id, matches in entries.items():
            if len(matches) > 1:
                findings.append(
                    Finding(
                        duplicate_entry_code,
                        "error",
                        root,
                        f"{entry_label} ID {entry_id!r} is duplicated inside character_id {character_id!r}.",
                    )
                )

    return (
        _LibraryIndex(
            True,
            dict(documents_by_character),
            {character_id: dict(entries) for character_id, entries in entries_by_character.items()},
            dict(entry_owners),
        ),
        findings,
    )


def audit_runtime(
    turn_state: Any,
    *,
    cognitive_resources: Any = None,
    speech_corpus: Any = None,
    memories: Any = None,
    relationship_ledgers: Any = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(turn_state, dict):
        return [Finding("invalid-turn-state", "error", "$", "Turn-state document must be a mapping.")]

    cognitive_index, cognitive_findings = _index_libraries(
        cognitive_resources,
        root="cognitive_resources",
        expected_purpose="comprehension_and_private_judgment",
        entries_field="resources",
        contract_code="invalid-cognitive-contract",
        missing_character_code="missing-cognitive-character-id",
        duplicate_character_code="duplicate-cognitive-character-library",
        invalid_entries_code="invalid-cognitive-resources-list",
        invalid_entry_code="invalid-cognitive-resource",
        duplicate_entry_code="duplicate-cognitive-resource-id",
        entry_character_code="cognitive-entry-character-mismatch",
        library_label="Cognitive resources",
        entry_label="Cognitive resource",
    )
    speech_index, speech_findings = _index_libraries(
        speech_corpus,
        root="speech_corpus",
        expected_purpose="expression_retrieval_after_private_judgment",
        entries_field="entries",
        contract_code="invalid-speech-contract",
        missing_character_code="missing-speech-character-id",
        duplicate_character_code="duplicate-speech-character-library",
        invalid_entries_code="invalid-speech-entries-list",
        invalid_entry_code="invalid-speech-corpus-entry",
        duplicate_entry_code="duplicate-speech-corpus-entry-id",
        entry_character_code="speech-entry-character-mismatch",
        library_label="Speech corpus",
        entry_label="Speech corpus entry",
    )
    memory_index, memory_findings = _index_libraries(
        memories,
        root="memories",
        expected_purpose=None,
        entries_field="memories",
        contract_code="invalid-memory-contract",
        missing_character_code="missing-memory-character-id",
        duplicate_character_code="duplicate-memory-character-library",
        invalid_entries_code="invalid-memories-list",
        invalid_entry_code="invalid-memory-entry",
        duplicate_entry_code="duplicate-memory-id",
        entry_character_code="memory-entry-character-mismatch",
        library_label="Memory library",
        entry_label="Memory",
    )
    relationship_index, relationship_findings = _index_relationship_ledgers(relationship_ledgers)
    findings.extend(cognitive_findings)
    findings.extend(speech_findings)
    findings.extend(memory_findings)
    findings.extend(relationship_findings)

    turns = turn_state.get("turns")
    if not isinstance(turns, list) or not turns:
        return findings + [Finding("no-turns", "error", "turns", "At least one consequential turn is required.")]

    trace_items = turn_state.get("decision_traces")
    if trace_items is not None and not isinstance(trace_items, list):
        findings.append(Finding("invalid-decision-traces", "error", "decision_traces", "decision_traces must be a list."))
        trace_items = []
    trace_items = trace_items or []

    turn_keys: dict[tuple[str | int, str], int] = {}
    for item_index, item in enumerate(turns):
        if not isinstance(item, dict):
            continue
        turn_id = item.get("turn")
        character = item.get("character_id")
        if not isinstance(turn_id, (str, int)) or isinstance(turn_id, bool) or not _nonempty(turn_id):
            findings.append(
                Finding(
                    "invalid-turn-id",
                    "error",
                    f"turns[{item_index}].turn",
                    "turn must be a non-empty string or integer stable ID.",
                )
            )
            continue
        if not isinstance(character, str) or not character.strip():
            continue
        key = (turn_id, character)
        if key in turn_keys:
            findings.append(
                Finding(
                    "duplicate-turn-identity",
                    "error",
                    f"turns[{item_index}]",
                    f"turn and character_id duplicate turns[{turn_keys[key]}].",
                )
            )
        else:
            turn_keys[key] = item_index

    trace_keys: dict[tuple[str | int, str], int] = {}
    for item_index, item in enumerate(trace_items):
        if not isinstance(item, dict):
            findings.append(
                Finding(
                    "invalid-decision-trace",
                    "error",
                    f"decision_traces[{item_index}]",
                    "Decision trace must be a mapping.",
                )
            )
            continue
        trace_turn = item.get("turn")
        trace_character = item.get("character_id")
        if (
            not isinstance(trace_turn, (str, int))
            or isinstance(trace_turn, bool)
            or not _nonempty(trace_turn)
            or not isinstance(trace_character, str)
            or not trace_character.strip()
        ):
            findings.append(
                Finding(
                    "invalid-decision-trace-identity",
                    "error",
                    f"decision_traces[{item_index}]",
                    "Decision trace requires a string/integer turn ID and non-empty string character_id.",
                )
            )
            continue
        key = (trace_turn, trace_character)
        if key in trace_keys:
            findings.append(
                Finding(
                    "duplicate-decision-trace",
                    "error",
                    f"decision_traces[{item_index}]",
                    f"Decision trace duplicates decision_traces[{trace_keys[key]}].",
                )
            )
        else:
            trace_keys[key] = item_index
        if key not in turn_keys:
            findings.append(
                Finding(
                    "orphan-decision-trace",
                    "error",
                    f"decision_traces[{item_index}]",
                    "Decision trace does not bind an existing turn with the same turn and character_id.",
                )
            )

    def matching_traces(turn: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            item
            for item in trace_items
            if isinstance(item, dict)
            and item.get("turn") == turn.get("turn")
            and item.get("character_id") == turn.get("character_id")
        ]

    for index, turn in enumerate(turns):
        location = f"turns[{index}]"
        if not isinstance(turn, dict):
            findings.append(Finding("invalid-turn", "error", location, "Turn must be a mapping."))
            continue
        raw_character_id = turn.get("character_id")
        character_id = raw_character_id.strip() if isinstance(raw_character_id, str) else ""
        if not character_id:
            findings.append(Finding("missing-turn-character-id", "error", f"{location}.character_id", "Turn character_id must be a non-empty string."))
        matches = matching_traces(turn) if trace_items else []
        trace = matches[0] if len(matches) == 1 else turn if not trace_items else {}
        if trace_items and not matches:
            findings.append(
                Finding(
                    "missing-decision-trace",
                    "error",
                    location,
                    "Every legacy surface turn needs exactly one decision trace with the same turn and character_id.",
                )
            )
        for field in ("perceived_cue", "literal_read", "judgment_or_question"):
            if not _nonempty(turn.get(field)):
                findings.append(Finding(f"missing-{field.replace('_', '-')}", "error", f"{location}.{field}", f"{field} is required."))
        for field in ("private_interpretation", "stance", "social_objective"):
            if not _nonempty(trace.get(field)):
                findings.append(Finding(f"missing-{field.replace('_', '-')}", "error", f"{location}.decision_trace.{field}", f"{field} is required."))

        for legacy_field, trace_field in (
            ("first_impulse", "first_impulse"),
            ("stance", "stance"),
            ("social_objective", "social_objective"),
            ("strategy", "strategy"),
            ("impulse_modulation", "impulse_modulation"),
            ("respond_or_withhold", "respond_or_withhold"),
        ):
            legacy_value = turn.get(legacy_field)
            trace_value = trace.get(trace_field)
            if _nonempty(legacy_value) and _nonempty(trace_value) and not _equivalent_projection(legacy_value, trace_value):
                findings.append(
                    Finding(
                        "legacy-decision-trace-mismatch",
                        "error",
                        f"{location}.{legacy_field}",
                        f"Legacy {legacy_field} contradicts decision_trace.{trace_field}.",
                    )
                )

        if not _nonempty(trace.get("pragmatic_attribution")) and not _nonempty(turn.get("attribution")):
            findings.append(
                Finding(
                    "missing-pragmatic-attribution",
                    "error",
                    location,
                    "Record a compact pragmatic attribution before judgment.",
                )
            )
        for field in ("inferences", "belief_delta"):
            if field not in trace or not isinstance(trace[field], list):
                findings.append(Finding(f"missing-{field.replace('_', '-')}", "error", f"{location}.decision_trace.{field}", f"{field} must be a list with an explicit update or no-change record."))
            elif not trace[field]:
                findings.append(
                    Finding(
                        f"empty-{field.replace('_', '-')}-record",
                        "error",
                        f"{location}.decision_trace.{field}",
                        f"Record an explicit no-change/no-new-{field.replace('_', '-')} item instead of an empty list.",
                    )
                )
        inferences = trace.get("inferences") if isinstance(trace.get("inferences"), list) else []
        for item_index, item in enumerate(inferences):
            item_location = f"{location}.decision_trace.inferences[{item_index}]"
            if not isinstance(item, dict) or not _nonempty(item.get("proposition")):
                findings.append(Finding("invalid-inference-record", "error", item_location, "Inference records require a proposition."))
            elif item.get("status") != "no_new_inference" and not _nonempty(item.get("knowledge_status")):
                findings.append(Finding("invalid-inference-record", "error", item_location, "Record knowledge_status or status: no_new_inference."))
        belief_items = trace.get("belief_delta") if isinstance(trace.get("belief_delta"), list) else []
        for item_index, item in enumerate(belief_items):
            item_location = f"{location}.decision_trace.belief_delta[{item_index}]"
            if not isinstance(item, dict) or not _nonempty(item.get("proposition")):
                findings.append(Finding("invalid-belief-delta-record", "error", item_location, "Belief-delta records require a proposition."))
            elif item.get("status") != "no_change" and not any(
                _nonempty(item.get(field))
                for field in ("new_knowledge_status", "new_confidence", "update_reason")
            ):
                findings.append(Finding("invalid-belief-delta-record", "error", item_location, "Record a changed status/confidence/reason or status: no_change."))

        comprehension = trace.get("comprehension_retrieval")
        if not isinstance(comprehension, dict):
            findings.append(
                Finding(
                    "missing-comprehension-retrieval",
                    "error",
                    f"{location}.comprehension_retrieval",
                    "Comprehension retrieval must precede interpretation.",
                )
            )
            comprehension = {}
        comprehension_refs: dict[str, list[str]] = {}
        for field in (
            "cognitive_resource_ids",
            "memory_ids",
            "relationship_claim_ids",
            "common_ground_proposition_ids",
            "second_order_belief_ids",
            "checked_unknown_or_excluded_resource_ids",
        ):
            comprehension_refs[field] = _reference_list(
                comprehension,
                field,
                location=f"{location}.comprehension_retrieval",
                findings=findings,
                list_code="invalid-comprehension-reference-list",
                item_code="invalid-comprehension-reference",
            )
        comp_refs = [item for refs in comprehension_refs.values() for item in refs]
        if not comp_refs:
            findings.append(
                Finding(
                    "empty-comprehension-retrieval",
                    "error",
                    f"{location}.comprehension_retrieval",
                    "Record at least one comprehension resource or explicitly checked unknown; an empty appraisal is not auditable.",
                )
            )
        cognitive_refs = comprehension_refs["cognitive_resource_ids"]
        if cognitive_refs and not cognitive_index.provided:
            findings.append(
                Finding(
                    "unverifiable-cognitive-resource-reference",
                    "error",
                    f"{location}.comprehension_retrieval.cognitive_resource_ids",
                    "Cognitive resource references require the same character's cognitive-resources document.",
                )
            )
        if cognitive_index.provided and _nonempty(character_id):
            matching_documents = cognitive_index.documents_by_character.get(character_id, [])
            if len(matching_documents) != 1:
                findings.append(
                    Finding(
                        "cognitive-character-mismatch",
                        "error",
                        f"{location}.comprehension_retrieval",
                        "Provide exactly one cognitive-resources document whose character_id matches this turn.",
                    )
                )
            matching_entries = cognitive_index.entries_by_character.get(character_id, {})
            for resource_id in cognitive_refs:
                matches = matching_entries.get(resource_id, [])
                if not matches:
                    if cognitive_index.entry_owners.get(resource_id):
                        findings.append(
                            Finding(
                                "cognitive-entry-character-mismatch",
                                "error",
                                f"{location}.comprehension_retrieval.cognitive_resource_ids",
                                f"Cognitive resource {resource_id!r} exists only in another character's library.",
                            )
                        )
                    else:
                        findings.append(
                            Finding(
                                "unknown-cognitive-resource",
                                "error",
                                f"{location}.comprehension_retrieval.cognitive_resource_ids",
                                f"Unknown same-character cognitive resource ID: {resource_id!r}.",
                            )
                        )
                    continue
                for _, entry in matches:
                    entry_character_id = entry.get("character_id")
                    if _nonempty(entry_character_id) and entry_character_id != character_id:
                        findings.append(
                            Finding(
                                "cognitive-entry-character-mismatch",
                                "error",
                                f"{location}.comprehension_retrieval.cognitive_resource_ids",
                                f"Cognitive resource {resource_id!r} belongs to another character.",
                            )
                        )

        memory_refs = comprehension_refs["memory_ids"]
        if memory_refs and not memory_index.provided:
            findings.append(
                Finding(
                    "unverifiable-memory-reference",
                    "error",
                    f"{location}.comprehension_retrieval.memory_ids",
                    "Memory references require the same character's memories document.",
                )
            )
        if memory_index.provided and _nonempty(character_id):
            matching_documents = memory_index.documents_by_character.get(character_id, [])
            if len(matching_documents) != 1:
                findings.append(
                    Finding(
                        "memory-character-mismatch",
                        "error",
                        f"{location}.comprehension_retrieval",
                        "Provide exactly one memories document whose character_id matches this turn.",
                    )
                )
            matching_entries = memory_index.entries_by_character.get(character_id, {})
            for memory_id in memory_refs:
                matches = matching_entries.get(memory_id, [])
                if not matches:
                    if memory_index.entry_owners.get(memory_id):
                        findings.append(
                            Finding(
                                "memory-entry-character-mismatch",
                                "error",
                                f"{location}.comprehension_retrieval.memory_ids",
                                f"Memory {memory_id!r} exists only in another character's library.",
                            )
                        )
                    else:
                        findings.append(
                            Finding(
                                "unknown-memory",
                                "error",
                                f"{location}.comprehension_retrieval.memory_ids",
                                f"Unknown same-character memory ID: {memory_id!r}.",
                            )
                        )

        for reference_field in (
            "relationship_claim_ids",
            "common_ground_proposition_ids",
            "second_order_belief_ids",
        ):
            refs = comprehension_refs[reference_field]
            if refs and not relationship_index.provided:
                findings.append(
                    Finding(
                        "unverifiable-relationship-reference",
                        "error",
                        f"{location}.comprehension_retrieval.{reference_field}",
                        "Relationship, common-ground, and second-order references require a relationship ledger.",
                    )
                )
                continue
            if not relationship_index.provided or not _nonempty(character_id):
                continue
            records = relationship_index.records.get(reference_field, {})
            owners = relationship_index.owners.get(reference_field, {})
            for reference_id in refs:
                if reference_id not in records:
                    findings.append(
                        Finding(
                            "unknown-relationship-reference",
                            "error",
                            f"{location}.comprehension_retrieval.{reference_field}",
                            f"Unknown {reference_field} ID: {reference_id!r}.",
                        )
                    )
                elif character_id not in owners.get(reference_id, set()):
                    findings.append(
                        Finding(
                            "relationship-reference-character-mismatch",
                            "error",
                            f"{location}.comprehension_retrieval.{reference_field}",
                            f"{reference_field} ID {reference_id!r} is not retrievable by character_id {character_id!r}.",
                        )
                    )

        expression = trace.get("expression_retrieval")
        if not isinstance(expression, dict):
            findings.append(
                Finding(
                    "missing-expression-retrieval",
                    "error",
                    f"{location}.expression_retrieval",
                    "Expression retrieval must follow judgment and social objective.",
                )
            )
            expression = {}
        corpus_refs = _reference_list(
            expression,
            "speech_corpus_entry_ids",
            location=f"{location}.expression_retrieval",
            findings=findings,
            list_code="invalid-speech-reference-list",
            item_code="invalid-speech-reference",
        )
        if corpus_refs and not speech_index.provided:
            findings.append(
                Finding(
                    "unverifiable-speech-corpus-reference",
                    "error",
                    f"{location}.expression_retrieval.speech_corpus_entry_ids",
                    "Speech-corpus references require the same character's speech-corpus document.",
                )
            )
        if speech_index.provided and _nonempty(character_id):
            matching_documents = speech_index.documents_by_character.get(character_id, [])
            if len(matching_documents) != 1:
                findings.append(
                    Finding(
                        "speech-character-mismatch",
                        "error",
                        f"{location}.expression_retrieval",
                        "Provide exactly one speech-corpus document whose character_id matches this turn.",
                    )
                )
            matching_entries = speech_index.entries_by_character.get(character_id, {})
            for entry_id in corpus_refs:
                matches = matching_entries.get(entry_id, [])
                if not matches:
                    if speech_index.entry_owners.get(entry_id):
                        findings.append(
                            Finding(
                                "speech-entry-character-mismatch",
                                "error",
                                f"{location}.expression_retrieval.speech_corpus_entry_ids",
                                f"Speech corpus entry {entry_id!r} exists only in another character's library.",
                            )
                        )
                    else:
                        findings.append(
                            Finding(
                                "unknown-speech-corpus-entry",
                                "error",
                                f"{location}.expression_retrieval.speech_corpus_entry_ids",
                                f"Unknown same-character speech corpus entry ID: {entry_id!r}.",
                            )
                        )
                    continue
                for _, entry in matches:
                    if entry.get("approval_state") != "approved":
                        findings.append(
                            Finding(
                                "unapproved-speech-corpus-entry",
                                "error",
                                f"{location}.expression_retrieval.speech_corpus_entry_ids",
                                f"Speech corpus entry {entry_id!r} is not approved.",
                            )
                        )
                    if _nonempty(entry.get("character_id")) and entry.get("character_id") != character_id:
                        findings.append(
                            Finding(
                                "speech-entry-character-mismatch",
                                "error",
                                f"{location}.expression_retrieval.speech_corpus_entry_ids",
                                f"Speech corpus entry {entry_id!r} belongs to another character.",
                            )
                        )

        surface = turn.get("surface")
        if not isinstance(surface, dict):
            findings.append(Finding("missing-surface", "error", f"{location}.surface", "Surface must be a mapping."))
            surface = {}
        output = trace.get("output")
        if output is not None:
            if not isinstance(output, dict):
                findings.append(
                    Finding(
                        "invalid-decision-trace-output",
                        "error",
                        f"{location}.decision_trace.output",
                        "decision_trace.output must be a mapping when present.",
                    )
                )
                output = {}
            output_ref = output.get("legacy_turn_surface_ref")
            if not _nonempty(output_ref):
                findings.append(
                    Finding(
                        "missing-legacy-turn-surface-ref",
                        "error",
                        f"{location}.decision_trace.output.legacy_turn_surface_ref",
                        "A decision-trace output must point to its legacy turn surface.",
                    )
                )
            elif output_ref != turn.get("turn"):
                findings.append(
                    Finding(
                        "legacy-turn-surface-ref-mismatch",
                        "error",
                        f"{location}.decision_trace.output.legacy_turn_surface_ref",
                        "decision_trace.output points to a different legacy turn surface.",
                    )
                )
        trace_surface = trace.get("surface")
        if isinstance(output, dict) and output.get("surface") is not None:
            if trace_surface is not None and trace_surface != output.get("surface"):
                findings.append(
                    Finding(
                        "decision-trace-surface-mismatch",
                        "error",
                        f"{location}.decision_trace.output.surface",
                        "decision_trace.surface and decision_trace.output.surface contradict each other.",
                    )
                )
            trace_surface = output.get("surface")
        if trace_surface is not None:
            if not isinstance(trace_surface, dict):
                findings.append(
                    Finding(
                        "invalid-decision-trace-surface",
                        "error",
                        f"{location}.decision_trace.surface",
                        "A projected decision-trace surface must be a mapping.",
                    )
                )
            else:
                for surface_field in ("action", "spatial_relation", "gaze", "expression", "silence", "dialogue"):
                    legacy_value = surface.get(surface_field)
                    trace_value = trace_surface.get(surface_field)
                    if (
                        _specified(legacy_value)
                        and _specified(trace_value)
                        and not _equivalent_projection(legacy_value, trace_value)
                    ):
                        findings.append(
                            Finding(
                                "legacy-decision-trace-surface-mismatch",
                                "error",
                                f"{location}.surface.{surface_field}",
                                f"Legacy surface.{surface_field} contradicts the decision-trace surface projection.",
                            )
                        )
        visible_fields = ("action", "spatial_relation", "gaze", "expression", "silence", "dialogue")
        if not any(_nonempty(surface.get(field)) for field in visible_fields):
            findings.append(Finding("empty-surface", "error", f"{location}.surface", "Choose an observable action, spatial move, gaze, expression, silence, or line."))
        dialogue = surface.get("dialogue")
        if _nonempty(dialogue) and not corpus_refs:
            findings.append(
                Finding(
                    "dialogue-without-expression-evidence",
                    "error",
                    f"{location}.surface.dialogue",
                    "Spoken wording requires approved same-character speech-corpus evidence.",
                )
            )
        retrieval_status = expression.get("retrieval_status")
        if corpus_refs and retrieval_status != "matched":
            findings.append(Finding("invalid-expression-retrieval-status", "error", f"{location}.expression_retrieval.retrieval_status", "Referenced speech evidence requires retrieval_status: matched."))
        if not corpus_refs:
            if retrieval_status not in {"no_compatible_entry", "not_applicable_nonverbal"}:
                findings.append(Finding("empty-expression-retrieval", "error", f"{location}.expression_retrieval", "No speech reference requires an explicit no_compatible_entry or not_applicable_nonverbal status."))
            options = expression.get("action_or_silence_options")
            if not isinstance(options, list) or not options:
                findings.append(Finding("empty-nonverbal-expression-options", "error", f"{location}.expression_retrieval.action_or_silence_options", "A no-match expression retrieval requires an explicit action or silence option."))
        private_text = _normalized(trace.get("private_interpretation"))
        public_text = _normalized(dialogue)
        if len(public_text) >= 8 and public_text == private_text:
            findings.append(
                Finding(
                    "private-analysis-spill",
                    "warning",
                    f"{location}.surface.dialogue",
                    "The public line duplicates the private interpretation; test suppression, action, or a tactical line.",
                )
            )
        if not isinstance(turn.get("consequence"), list) or not turn.get("consequence"):
            findings.append(
                Finding(
                    "missing-turn-consequence",
                    "error",
                    f"{location}.consequence",
                    "A consequential exchange must change a next condition or explicitly record the residual pressure.",
                )
            )
    return findings


def _load(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required; install requirements-dev.txt")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("turn_state", type=Path)
    parser.add_argument(
        "--cognitive-resources",
        action="append",
        type=Path,
        default=[],
        help="Per-character cognitive-resources file; repeat for multi-character scenes.",
    )
    parser.add_argument(
        "--speech-corpus",
        action="append",
        type=Path,
        default=[],
        help="Per-character speech-corpus file; repeat for multi-character scenes.",
    )
    parser.add_argument(
        "--memories",
        action="append",
        type=Path,
        default=[],
        help="Per-character memories file; repeat for multi-character scenes.",
    )
    parser.add_argument(
        "--relationship-ledger",
        action="append",
        type=Path,
        default=[],
        help="Relationship-ledger file; repeat only when records are split across files.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def load_many(paths: list[Path]) -> list[Any] | None:
        return [_load(path) for path in paths] if paths else None

    findings = audit_runtime(
        _load(args.turn_state),
        cognitive_resources=load_many(args.cognitive_resources),
        speech_corpus=load_many(args.speech_corpus),
        memories=load_many(args.memories),
        relationship_ledgers=load_many(args.relationship_ledger),
    )
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
        print(f"Findings: {len(findings)}")
    else:
        print("Character runtime contract passed.")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
