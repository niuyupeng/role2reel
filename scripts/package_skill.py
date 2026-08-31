#!/usr/bin/env python3
"""Create a deterministic Role2Reel ZIP archive for release or API upload."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_FILES = (
    ".github/ISSUE_TEMPLATE/behavior-failure.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/security-contact.yml",
    ".github/ISSUE_TEMPLATE/tooling-bug.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/validate.yml",
    ".gitattributes",
    ".gitignore",
    "CONTRIBUTING.md",
    "EVALS.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "SKILL.md",
    "THIRD_PARTY_NOTICES.md",
    "agents/openai.yaml",
    "assets/templates/asset-contract.yaml",
    "assets/templates/beat-map.yaml",
    "assets/templates/calibration-record.yaml",
    "assets/templates/character.yaml",
    "assets/templates/cognitive-resources.yaml",
    "assets/templates/continuity.yaml",
    "assets/templates/humanized-draft.md",
    "assets/templates/life-path-reading.md",
    "assets/templates/life-path-biography.md",
    "assets/templates/life-path-workbench.yaml",
    "assets/templates/staged-life-path-eval.yaml",
    "assets/templates/main.fountain",
    "assets/templates/meaning-ledger.yaml",
    "assets/templates/memories.yaml",
    "assets/templates/project.yaml",
    "assets/templates/relationship-ledger.yaml",
    "assets/templates/scene-contract.yaml",
    "assets/templates/speech-corpus.yaml",
    "assets/templates/storyboard.csv",
    "assets/templates/storyboard.yaml",
    "assets/templates/turn-state.yaml",
    "assets/templates/video-task.yaml",
    "assets/templates/video-prompt.md",
    "assets/templates/visual-bible.yaml",
    "docs/role2reel-banner.svg",
    "references/character-engine.md",
    "references/end-to-end-example.md",
    "references/fatecasting.md",
    "references/life-paths.md",
    "references/life-path-staged-example.md",
    "references/humanization.md",
    "references/output-contracts.md",
    "references/providers/seedance.md",
    "references/quality-gates.md",
    "references/scene-dialogue.md",
    "references/storyboard.md",
    "references/video-adapters.md",
    "requirements-dev.txt",
    "scripts/__init__.py",
    "scripts/audit_character_runtime.py",
    "scripts/audit_continuity.py",
    "scripts/audit_dialogue.py",
    "scripts/audit_humanization.py",
    "scripts/audit_life_paths.py",
    "scripts/audit_staged_eval.py",
    "scripts/audit_storyboard.py",
    "scripts/audit_video_task.py",
    "scripts/init_project.py",
    "scripts/package_skill.py",
    "scripts/validate_repo.py",
    "tests/__init__.py",
    "tests/fixtures/clean-dialogue.fountain",
    "tests/fixtures/invalid-storyboard.csv",
    "tests/fixtures/problem-dialogue.fountain",
    "tests/fixtures/valid-storyboard.csv",
    "tests/forward/README.md",
    "tests/forward/cases.json",
    "tests/forward/staged-deep-protocol.md",
    "tests/test_dialogue_audit.py",
    "tests/test_humanization_audit.py",
    "tests/test_character_runtime_audit.py",
    "tests/test_continuity_audit.py",
    "tests/test_fatecasting_contract.py",
    "tests/test_forward_cases.py",
    "tests/test_life_paths_audit.py",
    "tests/test_staged_eval_audit.py",
    "tests/test_scripts.py",
    "tests/test_storyboard_v2_audit.py",
    "tests/test_video_task_audit.py",
)


def _contains_symlink(path: Path, root: Path) -> bool:
    current = path
    while current != root:
        if current.is_symlink():
            return True
        current = current.parent
    return False


def release_paths(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for relative_text in RELEASE_FILES:
        relative = Path(relative_text)
        path = root / relative
        if _contains_symlink(path, root):
            raise ValueError(f"Release member cannot be a symlink: {relative_text}")
        if not path.is_file():
            raise FileNotFoundError(f"Missing release member: {relative_text}")
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Release member escapes repository: {relative_text}") from exc
        files.append(path)
    return files


def package(output: Path, *, root: Path = ROOT) -> tuple[int, Path]:
    root = root.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = release_paths(root)
    if output in {path.resolve() for path in files}:
        raise ValueError("Release output cannot overwrite a release source file")
    if output.exists():
        for path in files:
            try:
                if output.samefile(path):
                    raise ValueError("Release output cannot overwrite a hard-linked release source file")
            except OSError:
                continue
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = Path("role2reel") / path.relative_to(root)
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return len(files), output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "role2reel.zip")
    return parser.parse_args()


def main() -> int:
    count, output = package(parse_args().output)
    print(f"Packaged {count} files: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
