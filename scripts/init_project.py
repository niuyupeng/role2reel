#!/usr/bin/env python3
"""Initialize a Role2Reel production workspace without silent overwrites."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
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
    recent_changes: []"""

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
    attribution: null
    judgment_or_question: null
    stance: null
    confidence: null
    social_objective: null
    strategy: null
    surface:
      dialogue: null
      action: null
      silence: false
    observable_by_others: []
    consequence: []
    residual_state: null"""


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


def materialize(
    template_name: str,
    destination: Path,
    replacements: dict[str, str],
    *,
    force: bool,
    created: list[Path],
    skipped: list[Path],
) -> None:
    source = TEMPLATES / template_name
    if not source.is_file():
        raise FileNotFoundError(f"Missing template: {source}")
    if destination.is_symlink():
        raise ValueError(f"Refusing to write through a symbolic link: {destination}")
    if destination.exists() and not destination.is_file():
        raise IsADirectoryError(f"Expected a file destination: {destination}")
    if destination.exists() and not force:
        skipped.append(destination)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
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
                "    attribution: null",
                "    judgment_or_question: null",
                "    stance: null",
                "    confidence: null",
                "    social_objective: null",
                "    strategy: null",
                "    surface:",
                "      dialogue: null",
                "      action: null",
                "      silence: false",
                "    observable_by_others: []",
                "    consequence: []",
                "    residual_state: null",
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
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    skipped: list[Path] = []

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
        (target / "01-humanized").mkdir(parents=True, exist_ok=True)
        materialize("project.yaml", target / "project.yaml", {}, force=force, created=created, skipped=skipped)

    for char_id, name in assigned:
        char_dir = target / "02-characters" / char_id
        materialize(
            "character.yaml",
            char_dir / "character.yaml",
            {"  id: null": f"  id: {yaml_string(char_id)}", "  name: null": f"  name: {yaml_string(name)}"},
            force=force,
            created=created,
            skipped=skipped,
        )
        for template_name, filename in (
            ("cognitive-resources.yaml", "cognitive-resources.yaml"),
            ("memories.yaml", "memories.yaml"),
        ):
            materialize(
                template_name,
                char_dir / filename,
                {"character_id: null": f"character_id: {yaml_string(char_id)}"},
                force=force,
                created=created,
                skipped=skipped,
        )
        speech_path = char_dir / "speech-samples.md"
        if speech_path.is_symlink():
            raise ValueError(f"Refusing to write through a symbolic link: {speech_path}")
        if speech_path.exists() and not speech_path.is_file():
            raise IsADirectoryError(f"Expected a file destination: {speech_path}")
        if speech_path.exists() and not force:
            skipped.append(speech_path)
        else:
            speech_path.parent.mkdir(parents=True, exist_ok=True)
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
            "  id: null": f"  id: {yaml_string(scene_id)}",
            SCENE_CHARACTERS_PLACEHOLDER: _render_scene_characters(character_ids),
        },
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize(
        "turn-state.yaml",
        scene_dir / "turn-state.yaml",
        {**scene_replacement, TURN_PLACEHOLDER: _render_turns(character_ids)},
        force=force,
        created=created,
        skipped=skipped,
    )
    materialize("beat-map.yaml", scene_dir / "beat-map.yaml", scene_replacement, force=force, created=created, skipped=skipped)
    materialize("main.fountain", target / "04-screenplay" / "main.fountain", {}, force=force, created=created, skipped=skipped)
    materialize("storyboard.yaml", target / "05-storyboard" / "storyboard.yaml", scene_replacement, force=force, created=created, skipped=skipped)
    materialize("storyboard.csv", target / "05-storyboard" / "storyboard.csv", {}, force=force, created=created, skipped=skipped)
    materialize("continuity.yaml", target / "06-continuity" / "continuity.yaml", {}, force=force, created=created, skipped=skipped)
    materialize("asset-contract.yaml", target / "07-adapter" / "asset-contract.yaml", {}, force=force, created=created, skipped=skipped)
    materialize("video-prompt.md", target / "07-adapter" / "video-prompt.md", {}, force=force, created=created, skipped=skipped)
    materialize("calibration-record.yaml", target / "08-calibration" / "calibration-record.yaml", {}, force=force, created=created, skipped=skipped)
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
