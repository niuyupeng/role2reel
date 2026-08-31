from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.audit_storyboard import audit_document, _file_sha256


HASH = "a" * 64
ROOT = Path(__file__).resolve().parents[1]


def visual_bible() -> dict:
    return {
        "schema_version": 1,
        "visual_bible_id": "VB-001",
        "revision": 3,
        "assets": [
            {"asset_id": "CHAR-A", "revision": 2, "asset_type": "character"},
            {"asset_id": "LOC-ROOM", "revision": 1, "asset_type": "location"},
        ],
    }


def bound_sources() -> dict:
    return {
        "meaning": {"schema_version": 1, "ledger": {"ledger_id": "MEAN-001", "revision": 2}},
        "scene": {"schema_version": 1, "scene": {"id": "SC-001", "revision": 5}},
        "beats": {"schema_version": 1, "beat_map_id": "BEAT-001", "revision": 3},
    }


def audit_modern(payload: dict, *, include_sources: bool = True, include_visual: bool = True):
    return audit_document(
        payload,
        bound_sources=bound_sources() if include_sources else None,
        bound_source_sha256={role: HASH for role in ("meaning", "scene", "beats")} if include_sources else None,
        visual_bible=visual_bible() if include_visual else None,
        visual_bible_sha256=HASH if include_visual else None,
    )


def shot(shot_id: str, start: float, end: float, state_in: str, state_out: str, next_id: str | None) -> dict:
    return {
        "shot_id": shot_id,
        "start_s": start,
        "end_s": end,
        "duty": "Let the audience see the decision register",
        "state_in": state_in,
        "state_out": state_out,
        "visual_event": "The hand stops above the latch",
        "framing_and_angle": "medium eye-level",
        "camera_behavior": "static",
        "movement_motive": None,
        "blocking": ["A remains at the doorway"],
        "performance_cause": "The off-screen key turn reaches A before the hand stops",
        "dialogue": {"mode": "nonverbal", "lines": []},
        "sound": {
            "ambience": ["room tone"],
            "effects": ["key turns"],
            "music_function": None,
            "acoustic_silence": False,
        },
        "asset_refs": [
            {
                "asset_id": "CHAR-A",
                "revision": 2,
                "role": "performer",
                "use": ["identity", "blocking"],
                "target": "A",
            },
            {
                "asset_id": "LOC-ROOM",
                "revision": 1,
                "role": "location",
                "use": ["geometry"],
                "target": "set",
            },
        ],
        "continuity": ["hand remains above latch"],
        "transition": "cut",
        "handoff": {"to_shot_id": next_id, "state": state_out},
    }


def storyboard(depth: str = "professional") -> dict:
    return {
        "schema_version": 2,
        "storyboard_id": "SB-001",
        "revision": 4,
        "delivery_depth": depth,
        "scene_id": "SC-001",
        "source_bindings": [
            {"role": "meaning", "source_id": "MEAN-001", "revision": 2, "sha256": HASH},
            {"role": "scene", "source_id": "SC-001", "revision": 5, "sha256": HASH},
            {"role": "beats", "source_id": "BEAT-001", "revision": 3, "sha256": HASH},
        ],
        "visual_bible_binding": {"visual_bible_id": "VB-001", "revision": 3, "sha256": HASH},
        "total_duration_s": 6,
        "aspect_ratio": "16:9",
        "shots": [
            shot("S001", 0, 3, "ST-0", "ST-1", "S002"),
            shot("S002", 3, 6, "ST-1", "ST-2", None),
        ],
    }


class StoryboardV2AuditTests(unittest.TestCase):
    def test_professional_board_with_bound_assets_passes(self) -> None:
        self.assertEqual(audit_modern(storyboard()), [])

    def test_concise_depth_can_omit_professional_camera_fields(self) -> None:
        payload = storyboard("concise")
        for item in payload["shots"]:
            for field in ("framing_and_angle", "camera_behavior", "movement_motive", "blocking", "performance_cause", "continuity"):
                item.pop(field)
        self.assertEqual(audit_modern(payload), [])

    def test_detects_source_asset_dialogue_and_handoff_conflicts(self) -> None:
        payload = storyboard()
        payload["source_bindings"][0]["sha256"] = "bad"
        payload["shots"][0]["dialogue"] = {
            "mode": "nonverbal",
            "lines": [{"speaker_id": "A", "text": "I explain it."}],
        }
        payload["shots"][0]["asset_refs"][0]["revision"] = 99
        payload["shots"][1]["state_in"] = "BROKEN"
        findings = audit_modern(payload)
        codes = {finding.code for finding in findings}
        self.assertTrue(
            {
                "invalid-binding-hash",
                "unspoken-mode-has-line",
                "unknown-visual-asset-revision",
                "adjacent-state-mismatch",
            }.issubset(codes)
        )

    def test_spoken_mode_requires_speaker_ownership(self) -> None:
        payload = copy.deepcopy(storyboard())
        payload["shots"][0]["dialogue"] = {"mode": "spoken", "lines": [{"text": "Wait."}]}
        self.assertIn("invalid-spoken-line", {item.code for item in audit_modern(payload)})

    def test_modern_board_requires_actual_upstream_and_visual_documents(self) -> None:
        codes = {item.code for item in audit_modern(storyboard(), include_sources=False, include_visual=False)}
        self.assertIn("missing-bound-source-document", codes)
        self.assertIn("missing-visual-bible-document", codes)

    def test_actual_source_identity_revision_and_hash_are_verified(self) -> None:
        sources = bound_sources()
        sources["scene"]["scene"]["revision"] = 6
        hashes = {role: HASH for role in ("meaning", "scene", "beats")}
        hashes["beats"] = "b" * 64
        codes = {
            item.code
            for item in audit_document(
                storyboard(),
                bound_sources=sources,
                bound_source_sha256=hashes,
                visual_bible=visual_bible(),
                visual_bible_sha256=HASH,
            )
        }
        self.assertIn("source-revision-mismatch", codes)
        self.assertIn("source-hash-mismatch", codes)

    def test_actual_visual_bible_hash_is_required_and_verified(self) -> None:
        kwargs = {
            "bound_sources": bound_sources(),
            "bound_source_sha256": {role: HASH for role in ("meaning", "scene", "beats")},
            "visual_bible": visual_bible(),
        }
        self.assertIn("missing-visual-bible-hash", {item.code for item in audit_document(storyboard(), **kwargs)})
        kwargs["visual_bible_sha256"] = "b" * 64
        self.assertIn("visual-bible-hash-mismatch", {item.code for item in audit_document(storyboard(), **kwargs)})

    def test_cli_opens_and_verifies_all_four_bound_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = bound_sources()
            paths = {}
            for role, document in documents.items():
                path = root / f"{role}.yaml"
                path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
                paths[role] = path
            visual_path = root / "visual-bible.yaml"
            visual_path.write_text(yaml.safe_dump(visual_bible(), sort_keys=False), encoding="utf-8")
            payload = storyboard()
            for binding in payload["source_bindings"]:
                binding["sha256"] = _file_sha256(paths[binding["role"]])
            payload["visual_bible_binding"]["sha256"] = _file_sha256(visual_path)
            storyboard_path = root / "storyboard.yaml"
            storyboard_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_storyboard.py"),
                    str(storyboard_path),
                    "--meaning",
                    str(paths["meaning"]),
                    "--scene",
                    str(paths["scene"]),
                    "--beats",
                    str(paths["beats"]),
                    "--visual-bible",
                    str(visual_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
