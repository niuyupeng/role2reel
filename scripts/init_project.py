#!/usr/bin/env python3
"""Initialize a Role2Reel production workspace without silent overwrites."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import unicodedata
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_ROOT / "assets" / "templates"
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", "clock$"} | {
    f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)
}
MAX_COMPONENT_LENGTH = 80

RELATIONSHIP_PLACEHOLDER = """relationships:
  - from_character: null
    to_character: null
    character_sources:
      - character_id: null
        package_context_id: null
        life_path_branch_id: null
        compiled_from_lock_revision: null
        compiled_from_fact_boundary_sha256: null
        compiled_from_candidate_sha256: null
        compiled_from_biography_revision: null
        compiled_from_biography_sha256: null
        source_refs: []
    public_relationship: null
    trust: null
    intimacy: null
    power: null
    debt_and_obligation: []
    resentment: []
    leverage: []
    promises: []
    secrets_held: []
    prohibited_topics: []
    believes_other_knows: []
    history_refs: []
    recent_changes: []"""

CHARACTER_SOURCES_PLACEHOLDER = """character_sources:
  - character_id: null
    package_context_id: null
    life_path_branch_id: null
    compiled_from_lock_revision: null
    compiled_from_fact_boundary_sha256: null
    compiled_from_candidate_sha256: null
    compiled_from_biography_revision: null
    compiled_from_biography_sha256: null
    source_refs: []"""

SCENE_CHARACTERS_PLACEHOLDER = """characters:
  - id: null
    private_goal: null
    acceptable_loss: null
    feared_exposure: null
    knows: []
    suspects: []
    misunderstands: []
    believes_others_know: []
    available_strategies: []"""

TURN_PLACEHOLDER = """turns:
  - turn: 1
    character_id: null
    perceived_cue: null
    literal_read: null
    retrieved_factors: []
    activated_shared_memory_keys: []
    attribution: null
    judgment_or_question: null
    first_impulse: null
    impulse_modulation: null
    respond_or_withhold: null
    stance: null
    confidence: null
    social_objective: null
    strategy: null
    surface:
      action: null
      spatial_relation: null
      gaze: null
      expression: null
      silence: false
      dialogue: null
    observable_by_others: []
    consequence: []
    residual_state: null"""

CHARACTER_RUNTIME_SCOPES_PLACEHOLDER = """character_runtime_scopes:
  - character_id: null
    knowledge_boundary:
      - proposition_id: null
        proposition: null
        knowledge_status: null
        confidence: null
        confidence_basis: []
        source_refs: []
        last_update_ref: null
    common_ground_proposition_ids: []
    second_order_belief_ids: []
    cognitive_resource_ids: []
    memory_ids: []
    relationship_claim_ids: []
    speech_corpus_entry_ids: []
    forbidden_generic_phrasing_ids: []
    relationship_register: null"""

DECISION_TRACES_PLACEHOLDER = """decision_traces:
  - turn: 1
    character_id: null
    comprehension_retrieval:
      cognitive_resource_ids: []
      memory_ids: []
      relationship_claim_ids: []
      common_ground_proposition_ids: []
      second_order_belief_ids: []
      checked_unknown_or_excluded_resource_ids: []
    private_interpretation: null
    pragmatic_attribution: null
    inferences:
      - status: null
        proposition: null
        knowledge_status: null
        confidence: null
        evidence_refs: []
        competing_explanations: []
    belief_delta:
      - status: null
        proposition: null
        prior_knowledge_status: null
        new_knowledge_status: null
        prior_confidence: null
        new_confidence: null
        evidence_refs: []
        update_reason: null
    first_impulse: null
    stance: null
    confidence: null
    confidence_boundary: null
    social_objective: null
    strategy: null
    expression_retrieval:
      retrieval_status: null
      speech_corpus_entry_ids: []
      relationship_register: null
      action_or_silence_options: []
      wording_options: []
    suppressed_expression_options:
      - option_ref: null
        suppression_reason: null
    impulse_modulation: null
    respond_or_withhold: null
    output:
      legacy_turn_surface_ref: 1
      selected_expression_option_ref: null"""


def slugify(value: str, fallback: str) -> str:
    normalized_source = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^\w-]+", "-", normalized_source, flags=re.UNICODE)
    normalized = normalized.strip("-_. ") or fallback
    if normalized.casefold() in WINDOWS_RESERVED:
        normalized = f"id-{normalized}"
    if len(normalized) > MAX_COMPONENT_LENGTH:
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
        stem = normalized[: MAX_COMPONENT_LENGTH - len(digest) - 1].rstrip("-_. ")
        normalized = f"{stem}-{digest}"
    return normalized


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _absolute_without_resolving(path: Path) -> Path:
    """Return a normalized absolute path without following filesystem links."""

    return Path(os.path.abspath(os.fspath(path)))


def _path_prefixes(path: Path):
    current = Path(path.anchor)
    yield current
    for part in path.parts[1:]:
        current = current / part
        yield current


def _is_reparse_point(path: Path) -> bool:
    try:
        metadata = os.lstat(os.fspath(path))
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_attribute)


def _assert_no_link_components(path: Path) -> None:
    for component in _path_prefixes(path):
        if _is_reparse_point(component):
            raise ValueError(
                "Refusing to traverse a symbolic link, junction, or reparse point: "
                f"{component}"
            )


def _safe_destination(project_root: Path, destination: Path) -> Path:
    """Validate a destination lexically and canonically against its project root."""

    root = _absolute_without_resolving(project_root)
    candidate = _absolute_without_resolving(destination)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Destination escapes the requested project root: {candidate}") from exc

    # Check the whole existing chain before resolving it so a link cannot silently
    # redefine either the requested root or a destination parent.
    _assert_no_link_components(root)
    _assert_no_link_components(candidate)
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"Resolved destination escapes the requested project root: {candidate}"
        ) from exc
    return candidate


def _reject_force_through_hard_link(destination: Path, *, force: bool) -> None:
    if not force or not destination.exists():
        return
    metadata = destination.stat()
    if metadata.st_nlink > 1:
        raise ValueError(f"Refusing to replace a multiply linked file: {destination}")


def materialize(
    template_name: str,
    destination: Path,
    replacements: dict[str, str],
    *,
    project_root: Path,
    force: bool,
    created: list[Path],
    skipped: list[Path],
) -> None:
    destination = _safe_destination(project_root, destination)
    source = TEMPLATES / template_name
    if not source.is_file():
        raise FileNotFoundError(f"Missing template: {source}")
    if destination.exists() and not destination.is_file():
        raise IsADirectoryError(f"Expected a file destination: {destination}")
    if destination.exists() and not force:
        skipped.append(destination)
        return
    _reject_force_through_hard_link(destination, force=force)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination = _safe_destination(project_root, destination)
    _reject_force_through_hard_link(destination, force=force)
    if replacements:
        content = source.read_text(encoding="utf-8")
        for old, new in replacements.items():
            if old not in content:
                raise ValueError(f"Template marker not found in {template_name}: {old.splitlines()[0]}")
            content = content.replace(old, new, 1)
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    else:
        shutil.copyfile(source, destination)
    created.append(destination)


def _name_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _existing_characters(target: Path) -> tuple[set[str], dict[str, str]]:
    used_ids: set[str] = set()
    names: dict[str, str] = {}
    character_root = target / "02-characters"
    if not character_root.is_dir():
        return used_ids, names
    for directory in character_root.iterdir():
        if not directory.is_dir():
            continue
        char_id = directory.name
        used_ids.add(char_id)
        profile = directory / "character.yaml"
        if not profile.is_file():
            continue
        match = re.search(r"(?m)^  name:\s*(.+?)\s*$", profile.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            display_name = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(display_name, str):
            names.setdefault(_name_key(display_name), char_id)
    return used_ids, names


def _assign_character_ids(target: Path, characters: list[str]) -> list[tuple[str, str]]:
    used_ids, names = _existing_characters(target)
    assigned: list[tuple[str, str]] = []
    requested: dict[str, str] = {}
    for index, name in enumerate(characters, start=1):
        key = _name_key(name)
        if key in requested:
            continue
        if key in names:
            char_id = names[key]
        else:
            base = slugify(name, f"character-{index}")
            char_id = base
            suffix = 2
            while char_id in used_ids:
                char_id = f"{base}-{suffix}"
                suffix += 1
            used_ids.add(char_id)
            names[key] = char_id
        requested[key] = char_id
        assigned.append((char_id, name))
    return assigned


def _render_relationships(character_ids: list[str]) -> str:
    pairs = [(source, target) for source in character_ids for target in character_ids if source != target]
    if not pairs:
        return "relationships: []"
    lines = ["relationships:"]
    for source, target in pairs:
        lines.extend(
            [
                f"  - from_character: {yaml_string(source)}",
                f"    to_character: {yaml_string(target)}",
                "    character_sources:",
            ]
        )
        for participant in (source, target):
            lines.extend(
                [
                    f"      - character_id: {yaml_string(participant)}",
                    f"        package_context_id: {yaml_string(f'character-package-{participant}')}",
                    "        life_path_branch_id: null",
                    "        compiled_from_lock_revision: null",
                    "        compiled_from_fact_boundary_sha256: null",
                    "        compiled_from_candidate_sha256: null",
                    "        compiled_from_biography_revision: null",
                    "        compiled_from_biography_sha256: null",
                    "        source_refs: []",
                ]
            )
        lines.extend(
            [
                "    public_relationship: null",
                "    trust: null",
                "    intimacy: null",
                "    power: null",
                "    debt_and_obligation: []",
                "    resentment: []",
                "    leverage: []",
                "    promises: []",
                "    secrets_held: []",
                "    prohibited_topics: []",
                "    believes_other_knows: []",
                "    history_refs: []",
                "    recent_changes: []",
            ]
        )
    return "\n".join(lines)


def _render_scene_characters(character_ids: list[str]) -> str:
    if not character_ids:
        return "characters: []"
    lines = ["characters:"]
    for char_id in character_ids:
        lines.extend(
            [
                f"  - id: {yaml_string(char_id)}",
                "    private_goal: null",
                "    acceptable_loss: null",
                "    feared_exposure: null",
                "    knows: []",
                "    suspects: []",
                "    misunderstands: []",
                "    believes_others_know: []",
                "    available_strategies: []",
            ]
        )
    return "\n".join(lines)


def _render_character_sources(character_ids: list[str]) -> str:
    if not character_ids:
        return "character_sources: []"
    lines = ["character_sources:"]
    for char_id in character_ids:
        lines.extend(
            [
                f"  - character_id: {yaml_string(char_id)}",
                f"    package_context_id: {yaml_string(f'character-package-{char_id}')}",
                "    life_path_branch_id: null",
                "    compiled_from_lock_revision: null",
                "    compiled_from_fact_boundary_sha256: null",
                "    compiled_from_candidate_sha256: null",
                "    compiled_from_biography_revision: null",
                "    compiled_from_biography_sha256: null",
                "    source_refs: []",
            ]
        )
    return "\n".join(lines)


def _render_turns(character_ids: list[str]) -> str:
    if not character_ids:
        return "turns: []"
    lines = ["turns:"]
    for number, char_id in enumerate(character_ids, start=1):
        lines.extend(
            [
                f"  - turn: {number}",
                f"    character_id: {yaml_string(char_id)}",
                "    perceived_cue: null",
                "    literal_read: null",
                "    retrieved_factors: []",
                "    activated_shared_memory_keys: []",
                "    attribution: null",
                "    judgment_or_question: null",
                "    first_impulse: null",
                "    impulse_modulation: null",
                "    respond_or_withhold: null",
                "    stance: null",
                "    confidence: null",
                "    social_objective: null",
                "    strategy: null",
                "    surface:",
                "      action: null",
                "      spatial_relation: null",
                "      gaze: null",
                "      expression: null",
                "      silence: false",
                "      dialogue: null",
                "    observable_by_others: []",
                "    consequence: []",
                "    residual_state: null",
            ]
        )
    return "\n".join(lines)


def _render_character_runtime_scopes(character_ids: list[str]) -> str:
    if not character_ids:
        return "character_runtime_scopes: []"
    lines = ["character_runtime_scopes:"]
    for char_id in character_ids:
        lines.extend(
            [
                f"  - character_id: {yaml_string(char_id)}",
                "    knowledge_boundary: []",
                "    common_ground_proposition_ids: []",
                "    second_order_belief_ids: []",
                "    cognitive_resource_ids: []",
                "    memory_ids: []",
                "    relationship_claim_ids: []",
                "    speech_corpus_entry_ids: []",
                "    forbidden_generic_phrasing_ids: []",
                "    relationship_register: null",
            ]
        )
    return "\n".join(lines)


def _render_decision_traces(character_ids: list[str]) -> str:
    if not character_ids:
        return "decision_traces: []"
    lines = ["decision_traces:"]
    for number, char_id in enumerate(character_ids, start=1):
        lines.extend(
            [
                f"  - turn: {number}",
                f"    character_id: {yaml_string(char_id)}",
                "    comprehension_retrieval:",
                "      cognitive_resource_ids: []",
                "      memory_ids: []",
                "      relationship_claim_ids: []",
                "      common_ground_proposition_ids: []",
                "      second_order_belief_ids: []",
                "      checked_unknown_or_excluded_resource_ids: []",
                "    private_interpretation: null",
                "    pragmatic_attribution: null",
                "    inferences:",
                "      - status: null",
                "        proposition: null",
                "        knowledge_status: null",
                "        confidence: null",
                "        evidence_refs: []",
                "        competing_explanations: []",
                "    belief_delta:",
                "      - status: null",
                "        proposition: null",
                "        prior_knowledge_status: null",
                "        new_knowledge_status: null",
                "        prior_confidence: null",
                "        new_confidence: null",
                "        evidence_refs: []",
                "        update_reason: null",
                "    first_impulse: null",
                "    stance: null",
                "    confidence: null",
                "    confidence_boundary: null",
                "    social_objective: null",
                "    strategy: null",
                "    expression_retrieval:",
                "      retrieval_status: null",
                "      speech_corpus_entry_ids: []",
                "      relationship_register: null",
                "      action_or_silence_options: []",
                "      wording_options: []",
                "    suppressed_expression_options: []",
                "    impulse_modulation: null",
                "    respond_or_withhold: null",
                "    output:",
                f"      legacy_turn_surface_ref: {number}",
                "      selected_expression_option_ref: null",
            ]
        )
    return "\n".join(lines)


def initialize(
    target: Path,
    characters: list[str],
    scene: str,
    force: bool,
    profiles_only: bool = False,
) -> tuple[list[Path], list[Path]]:
    target = _absolute_without_resolving(target)
    _assert_no_link_components(target)
    target.mkdir(parents=True, exist_ok=True)
    _assert_no_link_components(target)
    created: list[Path] = []
    skipped: list[Path] = []

    _safe_destination(target, target / "02-characters")
    existing_ids, _ = _existing_characters(target)
    assigned = _assign_character_ids(target, characters)
    character_ids = [char_id for char_id, _ in assigned]
    new_character_ids = [char_id for char_id in character_ids if char_id not in existing_ids]
    graph_exists = (target / "02-characters" / "relationship-ledger.yaml").exists()
    if profiles_only and not (target / "project.yaml").is_file():
        raise ValueError("--profiles-only requires an already initialized Role2Reel workspace")
    if new_character_ids and graph_exists and not force and not profiles_only:
        raise ValueError(
            "New characters would not be linked into existing scene contracts. "
            "Use --profiles-only for deliberately standalone profiles, or rerun with --force "
            "and the complete initial-scene participant list."
        )

    if not profiles_only:
        materialize(
            "project.yaml",
            target / "project.yaml",
            {},
            project_root=target,
            force=force,
            created=created,
            skipped=skipped,
        )
        materialize(
            "meaning-ledger.yaml",
            target / "01-humanized" / "meaning-ledger.yaml",
            {},
            project_root=target,
            force=force,
            created=created,
            skipped=skipped,
        )
        materialize(
            "humanized-draft.md",
            target / "01-humanized" / "humanized-draft.md",
            {},
            project_root=target,
            force=force,
            created=created,
            skipped=skipped,
        )

    for char_id, name in assigned:
        char_dir = target / "02-characters" / char_id
        materialize(
            "character.yaml",
            char_dir / "character.yaml",
            {"  id: null": f"  id: {yaml_string(char_id)}", "  name: null": f"  name: {yaml_string(name)}"},
            project_root=target,
            force=force,
            created=created,
            skipped=skipped,
        )
        for template_name, filename in (
            ("cognitive-resources.yaml", "cognitive-resources.yaml"),
            ("life-path-workbench.yaml", "life-path-workbench.yaml"),
            ("memories.yaml", "memories.yaml"),
            ("speech-corpus.yaml", "speech-corpus.yaml"),
        ):
            if template_name == "life-path-workbench.yaml":
                replacements = {"character_id: null": f"character_id: {yaml_string(char_id)}"}
            else:
                replacements = {"\ncharacter_id: null\n": f"\ncharacter_id: {yaml_string(char_id)}\n"}
            if template_name == "life-path-workbench.yaml":
                replacements["package_context_id: null"] = (
                    f"package_context_id: {yaml_string(f'character-package-{char_id}')}"
                )
            materialize(
                template_name,
                char_dir / filename,
                replacements,
                project_root=target,
                force=force,
                created=created,
                skipped=skipped,
            )
        materialize(
            "life-path-reading.md",
            char_dir / "life-path-reading.md",
            {},
            project_root=target,
            force=force,
            created=created,
            skipped=skipped,
        )
        speech_path = _safe_destination(target, char_dir / "speech-samples.md")
        if speech_path.exists() and not speech_path.is_file():
            raise IsADirectoryError(f"Expected a file destination: {speech_path}")
        if speech_path.exists() and not force:
            skipped.append(speech_path)
        else:
            _reject_force_through_hard_link(speech_path, force=force)
            speech_path.parent.mkdir(parents=True, exist_ok=True)
            speech_path = _safe_destination(target, speech_path)
            _reject_force_through_hard_link(speech_path, force=force)
            with speech_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    f"# {name}: approved speech evidence\n\n"
                    "Add only source-backed or human-approved samples. Record context and add no invented catchphrases.\n"
                )
            created.append(speech_path)

    if profiles_only:
        return created, skipped

    materialize(
        "relationship-ledger.yaml",
        target / "02-characters" / "relationship-ledger.yaml",
        {RELATIONSHIP_PLACEHOLDER: _render_relationships(character_ids)},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )

    scene_id = slugify(scene, "scene-001")
    scene_dir = target / "03-scene" / scene_id
    scene_replacement = {"scene_id: null": f"scene_id: {yaml_string(scene_id)}"}
    materialize(
        "scene-contract.yaml",
        scene_dir / "scene-contract.yaml",
        {
            CHARACTER_SOURCES_PLACEHOLDER: _render_character_sources(character_ids),
            "  id: null": f"  id: {yaml_string(scene_id)}",
            SCENE_CHARACTERS_PLACEHOLDER: _render_scene_characters(character_ids),
            CHARACTER_RUNTIME_SCOPES_PLACEHOLDER: _render_character_runtime_scopes(character_ids),
        },
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "turn-state.yaml",
        scene_dir / "turn-state.yaml",
        {
            **scene_replacement,
            CHARACTER_SOURCES_PLACEHOLDER: _render_character_sources(character_ids),
            TURN_PLACEHOLDER: _render_turns(character_ids),
            DECISION_TRACES_PLACEHOLDER: _render_decision_traces(character_ids),
        },
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "beat-map.yaml",
        scene_dir / "beat-map.yaml",
        {
            **scene_replacement,
            "beat_map_id: null": f"beat_map_id: {yaml_string(f'{scene_id}-beats')}",
            CHARACTER_SOURCES_PLACEHOLDER: _render_character_sources(character_ids),
        },
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "main.fountain",
        target / "04-screenplay" / "main.fountain",
        {},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    project_character_sources = {CHARACTER_SOURCES_PLACEHOLDER: _render_character_sources(character_ids)}
    materialize(
        "storyboard.yaml",
        target / "05-storyboard" / "storyboard.yaml",
        {**scene_replacement, **project_character_sources},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "storyboard.csv",
        target / "05-storyboard" / "storyboard.csv",
        {},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "continuity.yaml",
        target / "06-continuity" / "continuity.yaml",
        project_character_sources,
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "visual-bible.yaml",
        target / "06-continuity" / "visual-bible.yaml",
        project_character_sources,
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "asset-contract.yaml",
        target / "07-adapter" / "asset-contract.yaml",
        project_character_sources,
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "video-task.yaml",
        target / "07-adapter" / "video-task.yaml",
        project_character_sources,
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "video-prompt.md",
        target / "07-adapter" / "video-prompt.md",
        {},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "calibration-record.yaml",
        target / "08-calibration" / "calibration-record.yaml",
        {},
        project_root=target,
        force=force,
        created=created,
        skipped=skipped,
    )
    return created, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Project directory to initialize or add profiles to")
    parser.add_argument("--characters", default="", help="Comma-separated participants for the initial scene")
    parser.add_argument("--scene", default="scene-001", help="Initial scene name or ID")
    parser.add_argument(
        "--profiles-only",
        action="store_true",
        help="Add standalone character profiles without changing existing scene or relationship contracts",
    )
    parser.add_argument("--force", action="store_true", help="Replace files that already exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    characters = [item.strip() for item in args.characters.split(",") if item.strip()]
    created, skipped = initialize(args.target, characters, args.scene, args.force, args.profiles_only)
    print(f"Role2Reel workspace: {args.target.resolve()}")
    print(f"Created: {len(created)}")
    for path in created:
        print(f"  + {path}")
    print(f"Skipped existing: {len(skipped)}")
    for path in skipped:
        print(f"  = {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
