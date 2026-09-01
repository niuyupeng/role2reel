from __future__ import annotations

import copy
import unittest

from scripts.audit_shot_readiness import audit_document


VALID = {
    "schema_version": 1,
    "production_lock": "review",
    "shots": [
        {
            "shot_id": "S001",
            "source_shot_id": "S001",
            "source_truth": {"status": "MATCHED", "speaker_match": True, "plot_fact_match": True, "author_addition_approved": False},
            "atomicity": {"status": "ATOMIC_PASS", "dominant_duty": "reveal", "beat_count": 2, "camera_continuity": True, "author_decision": "pending"},
            "timing": {"editorial_duration_s": 4.0, "provider_duration_s": 5.0, "hard_floor_s": 2.0},
            "physical_sound": {"environment": "interior", "sound_carrier": "room", "force_source": "hand", "continuity_state_in": "closed", "continuity_state_out": "open"},
            "text": {"status": "none"},
            "release_decision": "pending",
        }
    ],
}


class ShotReadinessAuditTests(unittest.TestCase):
    def test_valid_review_record_passes(self) -> None:
        self.assertEqual(audit_document(VALID), [])

    def test_unresolved_split_and_source_drift_block_lock(self) -> None:
        payload = copy.deepcopy(VALID)
        payload["production_lock"] = "locked"
        payload["shots"][0]["source_truth"]["status"] = "SOURCE_MISMATCH"
        payload["shots"][0]["atomicity"]["status"] = "SPLIT_REQUIRED"
        payload["shots"][0]["release_decision"] = "approved"
        codes = {item.code for item in audit_document(payload)}
        self.assertIn("source-drift-blocks-lock", codes)
        self.assertIn("split-required-blocks-lock", codes)

    def test_duration_and_vacuum_sound_fail(self) -> None:
        payload = copy.deepcopy(VALID)
        shot = payload["shots"][0]
        shot["timing"] = {"editorial_duration_s": 1.0, "provider_duration_s": 5.0, "hard_floor_s": 2.0}
        shot["physical_sound"] = {"environment": "outer-space vacuum", "sound_carrier": "wind", "force_source": "", "continuity_state_in": "a", "continuity_state_out": "b"}
        codes = {item.code for item in audit_document(payload)}
        self.assertIn("duration-infeasible", codes)
        self.assertIn("vacuum-air-sound", codes)

    def test_post_composite_text_requires_plan(self) -> None:
        payload = copy.deepcopy(VALID)
        payload["shots"][0]["text"] = {"status": "post_composite_text"}
        self.assertIn("missing-overlay-plan", {item.code for item in audit_document(payload)})
