from __future__ import annotations

import copy
import unittest

from scripts.audit_continuity import audit_document


HASH = "b" * 64


def visual_bible() -> dict:
    return {
        "schema_version": 1,
        "visual_bible_id": "VB-001",
        "revision": 1,
        "assets": [
            {"asset_id": "CHAR-A", "revision": 1},
            {"asset_id": "LOC-1", "revision": 1},
        ],
    }


def lock(lock_id: str, asset_id: str, prop: str, value: str) -> dict:
    return {
        "lock_id": lock_id,
        "target_ref": {"asset_id": asset_id, "revision": 1},
        "property": prop,
        "value": value,
    }


def continuity() -> dict:
    return {
        "schema_version": 2,
        "continuity_id": "CONT-001",
        "revision": 2,
        "source_bindings": {
            "storyboard": {"artifact_id": "SB-001", "revision": 4, "sha256": HASH},
            "visual_bible": {"artifact_id": "VB-001", "revision": 1, "sha256": HASH},
        },
        "global_locks": {
            "identity": {"status": "locked", "reason": None, "entries": [lock("L-ID", "CHAR-A", "identity", "canonical face")]},
            "wardrobe": {"status": "locked", "reason": None, "entries": [lock("L-W", "CHAR-A", "wardrobe", "blue coat")]},
            "space": {"status": "locked", "reason": None, "entries": [lock("L-S", "LOC-1", "geometry", "door east of table")]},
            "voice": {"status": "not_applicable", "reason": "No spoken voice.", "entries": []},
        },
        "state_changes": [],
        "shot_handoffs": [
            {"from_shot_id": "S001", "to_shot_id": "S002", "state_out": "ST-1", "next_state_in": "ST-1", "match_points": ["raised hand"]},
            {"from_shot_id": "S002", "to_shot_id": None, "state_out": "ST-2", "next_state_in": "ST-2", "match_points": []},
        ],
    }


def storyboard() -> dict:
    return {
        "storyboard_id": "SB-001",
        "revision": 4,
        "shots": [
            {"shot_id": "S001", "state_out": "ST-1", "handoff": {"to_shot_id": "S002"}},
            {"shot_id": "S002", "state_out": "ST-2", "handoff": {"to_shot_id": None}},
        ],
    }


class ContinuityAuditTests(unittest.TestCase):
    def test_exact_locks_and_handoffs_pass(self) -> None:
        self.assertEqual(audit_document(continuity(), storyboard=storyboard(), visual_bible=visual_bible()), [])

    def test_legacy_shape_remains_accepted(self) -> None:
        legacy = {"schema_version": 1, "global_locks": {}, "state_changes": [], "shot_handoffs": []}
        self.assertEqual(audit_document(legacy), [])

    def test_reports_lock_and_handoff_conflicts_without_rewriting(self) -> None:
        payload = copy.deepcopy(continuity())
        payload["global_locks"]["identity"]["entries"].append(lock("L-ID-2", "CHAR-A", "identity", "different face"))
        payload["shot_handoffs"][0]["next_state_in"] = "BROKEN"
        findings = audit_document(payload, storyboard=storyboard(), visual_bible=visual_bible())
        codes = {finding.code for finding in findings}
        self.assertTrue({"lock-conflict", "handoff-state-conflict"}.issubset(codes))

    def test_not_applicable_lock_needs_reason(self) -> None:
        payload = continuity()
        payload["global_locks"]["voice"]["reason"] = None
        self.assertIn("missing-lock-exemption-reason", {item.code for item in audit_document(payload, storyboard=storyboard(), visual_bible=visual_bible())})

    def test_modern_contract_fails_closed_without_actual_bound_files(self) -> None:
        codes = {item.code for item in audit_document(continuity())}
        self.assertTrue({"missing-supplied-storyboard", "missing-supplied-visual-bible"}.issubset(codes))

    def test_static_draft_lint_is_explicit_opt_in(self) -> None:
        self.assertEqual(audit_document(continuity(), allow_unbound_structure=True), [])


if __name__ == "__main__":
    unittest.main()
