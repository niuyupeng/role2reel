#!/usr/bin/env python3
"""Validate Role2Reel's skill metadata, links, templates, and Python scripts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the CLI dependency check
    yaml = None


REQUIRED_TEMPLATES = {
    "project.yaml",
    "character.yaml",
    "cognitive-resources.yaml",
    "speech-corpus.yaml",
    "life-path-reading.md",
    "life-path-workbench.yaml",
    "life-path-biography.md",
    "staged-life-path-eval.yaml",
    "memories.yaml",
    "relationship-ledger.yaml",
    "scene-contract.yaml",
    "turn-state.yaml",
    "beat-map.yaml",
    "storyboard.yaml",
    "storyboard.csv",
    "continuity.yaml",
    "visual-bible.yaml",
    "asset-contract.yaml",
    "video-task.yaml",
    "video-prompt.md",
    "meaning-ledger.yaml",
    "humanized-draft.md",
    "calibration-record.yaml",
    "main.fountain",
}
IGNORED_DIRS = {".git", "dist", "test-results", "__pycache__", ".pytest_cache", ".venv"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_file() or path.is_symlink():
            yield path


def load_yaml(path: Path, root: Path, errors: list[str]) -> Any:
    relative = path.relative_to(root)
    if yaml is None:
        errors.append("PyYAML is required for validation; install requirements-dev.txt")
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"Invalid YAML in {relative}: {exc}")
        return None


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    skill_path = root / "SKILL.md"
    metadata_path = root / "agents" / "openai.yaml"
    if not skill_path.is_file():
        errors.append("Missing SKILL.md")
        return errors
    if not metadata_path.is_file():
        errors.append("Missing agents/openai.yaml")

    try:
        skill_text = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"Unreadable UTF-8 file in SKILL.md: {exc}")
        skill_text = None
    if skill_text is not None:
        frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*\n", skill_text, re.S)
        if not frontmatter:
            errors.append("SKILL.md has no valid YAML frontmatter block")
        else:
            header = frontmatter.group(1)
            if yaml is None:
                errors.append("PyYAML is required for validation; install requirements-dev.txt")
                skill_header = None
            else:
                try:
                    skill_header = yaml.safe_load(header)
                except yaml.YAMLError as exc:
                    errors.append(f"Invalid YAML in SKILL.md frontmatter: {exc}")
                    skill_header = None
            if not isinstance(skill_header, dict) or skill_header.get("name") != "role2reel":
                errors.append("SKILL.md name must be role2reel")
            description = skill_header.get("description") if isinstance(skill_header, dict) else None
            if not isinstance(description, str) or len(description.strip()) < 40:
                errors.append("SKILL.md description is missing or not discriminating")

    if metadata_path.is_file():
        metadata = load_yaml(metadata_path, root, errors)
        interface = metadata.get("interface") if isinstance(metadata, dict) else None
        if not isinstance(interface, dict):
            errors.append("agents/openai.yaml must contain an interface mapping")
            interface = {}
        if "$role2reel" not in str(interface.get("default_prompt") or ""):
            errors.append("agents/openai.yaml default_prompt must mention $role2reel")
        if interface.get("display_name") != "Role2Reel":
            errors.append("agents/openai.yaml display_name is inconsistent")

    placeholder_pattern = re.compile(r"\[(?:TODO|PLACEHOLDER)[^\]]*\]|TODO:", re.I)
    for path in iter_files(root):
        relative = path.relative_to(root)
        if path.is_symlink():
            errors.append(f"Symbolic links are not release-safe: {relative}")
            continue
        if path.suffix.casefold() in {".md", ".yaml", ".yml", ".py", ".txt"}:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errors.append(f"Unreadable UTF-8 file in {relative}: {exc}")
                continue
            if relative.as_posix() != "scripts/validate_repo.py" and placeholder_pattern.search(text):
                errors.append(f"Unfinished placeholder in {relative}")
        if path.suffix.casefold() in {".yaml", ".yml"} and path != metadata_path:
            payload = load_yaml(path, root, errors)
            if relative.parts[:2] == ("assets", "templates"):
                if not isinstance(payload, dict) or payload.get("schema_version") != 1:
                    errors.append(f"Template YAML must be a schema_version 1 mapping: {relative}")
        if path.suffix.casefold() == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {relative}:{exc.lineno}: {exc.msg}")
        if path.suffix.casefold() == ".md":
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                clean = unquote(target.split("#", 1)[0].strip().strip("<>"))
                if not clean or re.match(r"^(?:https?://|mailto:)", clean, re.I):
                    continue
                linked = (path.parent / clean).resolve()
                try:
                    linked.relative_to(root)
                except ValueError:
                    errors.append(f"Local link escapes repository in {relative}: {target}")
                    continue
                if not linked.exists():
                    errors.append(f"Broken local link in {relative}: {target}")

    template_dir = root / "assets" / "templates"
    for name in sorted(REQUIRED_TEMPLATES):
        template = template_dir / name
        if not template.is_file() or template.is_symlink():
            errors.append(f"Missing regular template file: assets/templates/{name}")
    return list(dict.fromkeys(errors))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def main() -> int:
    root = parse_args().root.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"Validation failed: {len(errors)} error(s).")
        return 1
    count = sum(1 for _ in iter_files(root))
    print(f"Role2Reel validation passed: {count} files checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
