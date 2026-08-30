from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.audit_dialogue import audit_text
from scripts.audit_storyboard import audit_rows, load_rows
from scripts.init_project import initialize
from scripts.package_skill import RELEASE_FILES, package
from scripts.validate_repo import validate


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class InitializerTests(unittest.TestCase):
    def test_initializes_unicode_characters_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            created, skipped = initialize(target, ["江瑟", "牛老师"], "离开", False)
            self.assertGreaterEqual(len(created), 18)
            self.assertEqual(skipped, [])
            self.assertTrue((target / "02-characters" / "江瑟" / "character.yaml").is_file())
            self.assertTrue((target / "02-characters" / "牛老师" / "memories.yaml").is_file())
            self.assertTrue((target / "03-scene" / "离开" / "scene-contract.yaml").is_file())
            self.assertTrue((target / "01-humanized").is_dir())
            first_content = (target / "02-characters" / "江瑟" / "character.yaml").read_text(encoding="utf-8")
            self.assertIn('name: "江瑟"', first_content)
            scene_content = (target / "03-scene" / "离开" / "scene-contract.yaml").read_text(encoding="utf-8")
            turn_content = (target / "03-scene" / "离开" / "turn-state.yaml").read_text(encoding="utf-8")
            relationship_content = (target / "02-characters" / "relationship-ledger.yaml").read_text(encoding="utf-8")
            self.assertIn('  - id: "江瑟"', scene_content)
            self.assertIn('  - id: "牛老师"', scene_content)
            self.assertNotIn("character_id: null", turn_content)
            self.assertIn('from_character: "江瑟"', relationship_content)
            self.assertIn('to_character: "牛老师"', relationship_content)

            created_again, skipped_again = initialize(target, ["江瑟", "牛老师"], "离开", False)
            self.assertEqual(created_again, [])
            self.assertEqual(len(skipped_again), len(created))

    def test_extend_disambiguates_existing_slug_collision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            initialize(target, ["A B"], "scene", False)
            with self.assertRaises(ValueError):
                initialize(target, ["A/B"], "scene", False)
            self.assertFalse((target / "02-characters" / "a-b-2").exists())
            created, _ = initialize(target, ["A/B"], "scene", False, profiles_only=True)
            second_profile = target / "02-characters" / "a-b-2" / "character.yaml"
            self.assertIn(second_profile, created)
            self.assertIn('name: "A/B"', second_profile.read_text(encoding="utf-8"))

    def test_reserved_windows_components_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            initialize(target, ["COM1"], "NUL", False)
            self.assertTrue((target / "02-characters" / "id-com1" / "character.yaml").is_file())
            self.assertTrue((target / "03-scene" / "id-nul" / "scene-contract.yaml").is_file())


class DialogueAuditTests(unittest.TestCase):
    def test_clean_dialogue_has_no_configured_warnings(self) -> None:
        text = (FIXTURES / "clean-dialogue.fountain").read_text(encoding="utf-8")
        self.assertEqual(audit_text(text), [])

    def test_problem_dialogue_flags_exposition_summary_and_duplicate(self) -> None:
        text = (FIXTURES / "problem-dialogue.fountain").read_text(encoding="utf-8")
        codes = {item.code for item in audit_text(text)}
        self.assertTrue({"as-you-know", "generic-summary", "duplicate-line"}.issubset(codes))


class StoryboardAuditTests(unittest.TestCase):
    def test_empty_storyboard_is_an_error(self) -> None:
        findings = audit_rows([])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "no-shots")
        self.assertEqual(findings[0].severity, "error")

    def test_valid_storyboard_passes(self) -> None:
        self.assertEqual(audit_rows(load_rows(FIXTURES / "valid-storyboard.csv")), [])

    def test_invalid_storyboard_reports_hard_and_soft_failures(self) -> None:
        findings = audit_rows(load_rows(FIXTURES / "invalid-storyboard.csv"))
        codes = {item.code for item in findings}
        self.assertTrue({"duplicate-shot-id", "nonpositive-duration", "timeline-overlap", "missing-field", "generic-duty"}.issubset(codes))
        self.assertTrue(any(item.severity == "error" for item in findings))

    def test_nonfinite_time_and_tolerance_are_errors(self) -> None:
        row = {
            "shot_id": "S001",
            "start_s": "nan",
            "end_s": "inf",
            "duty": "Reveal the decision",
            "visual": "She closes the case",
            "framing": "medium",
            "movement": "static",
            "performance": "hand releases",
            "dialogue_sound": "room tone",
            "continuity": [],
        }
        self.assertIn("invalid-time", {item.code for item in audit_rows([row])})
        self.assertEqual(audit_rows([row], tolerance=float("inf"))[0].code, "invalid-tolerance")
        self.assertEqual(audit_rows([row], expected_duration=float("nan"))[0].code, "invalid-expected-duration")

    def test_canonical_storyboard_aliases_pass_json_loading(self) -> None:
        shot = {
            "shot_id": "S001",
            "start_s": 0,
            "end_s": 8,
            "duty": "Let the audience see her decision land",
            "visual_event": "She closes the case",
            "framing_and_angle": "medium eye-level",
            "camera_behavior": "static",
            "movement_motive": None,
            "blocking": [],
            "performance_cause": "doorbell makes her release the handle",
            "dialogue_sound": "doorbell, then room tone",
            "continuity": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "storyboard.json"
            path.write_text(json.dumps({"shots": [shot]}), encoding="utf-8")
            self.assertEqual(audit_rows(load_rows(path), expected_duration=8), [])

    def test_canonical_storyboard_aliases_pass_yaml_loading(self) -> None:
        yaml_text = """shots:
  - shot_id: S001
    start_s: 0
    end_s: 8
    duty: Let the audience see her decision land
    visual_event: She closes the case
    framing_and_angle: medium eye-level
    camera_behavior: static
    movement_motive: null
    blocking: []
    performance_cause: doorbell makes her release the handle
    dialogue_sound: doorbell, then room tone
    continuity: []
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "storyboard.yaml"
            path.write_text(yaml_text, encoding="utf-8")
            self.assertEqual(audit_rows(load_rows(path), expected_duration=8), [])

    def test_exact_duration_mode_escalates_gaps_and_checks_final_end(self) -> None:
        rows = [
            dict(load_rows(FIXTURES / "valid-storyboard.csv")[0]),
            dict(load_rows(FIXTURES / "valid-storyboard.csv")[1]),
        ]
        rows[1]["start_s"] = "9"
        rows[1]["end_s"] = "12"
        findings = audit_rows(rows, expected_duration=14)
        errors = {item.code for item in findings if item.severity == "error"}
        self.assertTrue({"timeline-gap", "duration-mismatch"}.issubset(errors))


class RepositoryTests(unittest.TestCase):
    def test_repository_contract(self) -> None:
        self.assertEqual(validate(ROOT), [])

    def test_package_contains_skill_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            count, archive_path = package(Path(directory) / "role2reel.zip")
            self.assertGreater(count, 20)
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
            expected = {f"role2reel/{name}" for name in RELEASE_FILES}
            self.assertEqual(count, len(RELEASE_FILES))
            self.assertEqual(names, expected)

    def test_package_allowlist_excludes_unlisted_private_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for relative in RELEASE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")
            (root / ".env").write_text("SECRET=value", encoding="utf-8")
            private = root / "test-results" / "private-output.txt"
            private.parent.mkdir(parents=True)
            private.write_text("private", encoding="utf-8")
            archive_path = Path(directory) / "release.zip"
            count, _ = package(archive_path, root=root)
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
            self.assertEqual(count, len(RELEASE_FILES))
            self.assertNotIn("role2reel/.env", names)
            self.assertNotIn("role2reel/test-results/private-output.txt", names)

    def test_package_rejects_source_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for relative in RELEASE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")
            with self.assertRaises(ValueError):
                package(root / "README.md", root=root)

    def test_package_rejects_hard_link_to_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for relative in RELEASE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")
            output = Path(directory) / "release.zip"
            os.link(root / "README.md", output)
            with self.assertRaises(ValueError):
                package(output, root=root)
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "fixture")

    def test_package_rejects_symlinked_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for relative in RELEASE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")
            external = Path(directory) / "external-skill.md"
            external.write_text("private external material", encoding="utf-8")
            member = root / "SKILL.md"
            member.unlink()
            try:
                member.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            with self.assertRaises(ValueError):
                package(Path(directory) / "release.zip", root=root)

    def test_validator_handles_external_root_under_ignored_named_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "dist" / "role2reel"
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            self.assertEqual(validate(clone), [])
            broken = clone / "scripts" / "broken.py"
            broken.write_text("def broken(:\n", encoding="utf-8")
            errors = validate(clone)
            self.assertTrue(any("Python syntax error in scripts" in error for error in errors))

    def test_validator_rejects_malformed_yaml_and_template_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "role2reel"
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            metadata = clone / "agents" / "openai.yaml"
            metadata.write_text(metadata.read_text(encoding="utf-8") + "\nmalformed: [\n", encoding="utf-8")
            template = clone / "assets" / "templates" / "project.yaml"
            template.unlink()
            template.mkdir()
            errors = validate(clone)
            self.assertTrue(any("Invalid YAML in agents" in error for error in errors))
            self.assertIn("Missing regular template file: assets/templates/project.yaml", errors)

    def test_validator_reports_invalid_utf8_yaml_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "role2reel"
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            (clone / "bad.yaml").write_bytes(b"key: \xff\n")
            errors = validate(clone)
            self.assertTrue(any("Unreadable UTF-8 file in bad.yaml" in error for error in errors))

    def test_validator_reports_invalid_utf8_skill_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "role2reel"
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            (clone / "SKILL.md").write_bytes(b"---\nname: \xff\n---\n")
            errors = validate(clone)
            self.assertTrue(any("Unreadable UTF-8 file in SKILL.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
