from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.audit_video_task import PRIMARY_MODES, audit_document as _audit_document


HASH = "c" * 64


def asset_ref(asset_id: str) -> dict:
    return {"asset_id": asset_id, "revision": 1}


def mode_ref(asset_id: str) -> dict:
    return {**asset_ref(asset_id), "use_id": f"USE-{asset_id}"}


def lock(lock_id: str, asset_id: str, prop: str, value: str) -> dict:
    return {
        "lock_id": lock_id,
        "target_ref": asset_ref(asset_id),
        "property": prop,
        "value": value,
    }


def asset_contract() -> dict:
    refs = [asset_ref(value) for value in ("CLIP-A", "CLIP-B", "PANEL-1", "PANEL-2")]
    return {
        "schema_version": 2,
        "contract_id": "AC-001",
        "revision": 1,
        "default_borrow_policy": "deny",
        "source_assets": [
            {**ref, "media_type": "video", "provider_asset_id": f"IMMUTABLE-{ref['asset_id']}", "provider_asset_version": "v1"}
            for ref in refs
        ],
        "borrow_authorizations": [
            {
                "authorization_id": f"AUTH-{ref['asset_id']}",
                "source_ref": ref,
                "borrow": ["conditioning", "extension_source", "edit_source", "transition_source_a", "transition_source_b", "panel_source"],
                "targets": ["OUTPUT", "UNRELATED"],
                "interval": {"start_s": 0, "end_s": 4},
                "preserve": ["declared source role"],
                "exclude": ["unlisted properties"],
            }
            for ref in refs
        ],
    }


def mode_source_refs(mode: str) -> list[tuple[str, str]]:
    if mode in {"extension", "edit"}:
        return [("CLIP-A", "extension_source" if mode == "extension" else "edit_source")]
    if mode == "transition":
        return [("CLIP-A", "transition_source_a"), ("CLIP-B", "transition_source_b")]
    if mode == "multi_panel":
        return [("PANEL-1", "panel_source"), ("PANEL-2", "panel_source")]
    return []


def storyboard() -> dict:
    return {
        "storyboard_id": "SB-001",
        "revision": 1,
        "shots": [
            {"shot_id": "S001", "start_s": 0, "end_s": 2},
            {"shot_id": "S002", "start_s": 2, "end_s": 4},
        ],
    }


def visual_bible() -> dict:
    return {
        "visual_bible_id": "VB-001",
        "revision": 1,
        "assets": [{**asset_ref("CHAR-A")}, {**asset_ref("LOC-1")}],
    }


def continuity() -> dict:
    return {
        "continuity_id": "CONT-001",
        "revision": 1,
        "source_bindings": {
            "storyboard": {"artifact_id": "SB-001", "revision": 1, "sha256": HASH},
            "visual_bible": {"artifact_id": "VB-001", "revision": 1, "sha256": HASH},
        },
        "global_locks": copy.deepcopy(task()["global_locks"]),
    }


def audit_document(payload: dict, **kwargs: object) -> list:
    """Production-mode test harness: every upstream artifact is really supplied."""
    supplied_storyboard = kwargs.pop("storyboard", storyboard())
    supplied_continuity = kwargs.pop("continuity", continuity())
    supplied_visual = kwargs.pop("visual_bible", visual_bible())
    supplied_contract = kwargs.pop("asset_contract", asset_contract())
    return _audit_document(
        payload,
        storyboard=supplied_storyboard,
        storyboard_sha256=HASH,
        continuity=supplied_continuity,
        continuity_sha256=HASH,
        visual_bible=supplied_visual,
        visual_bible_sha256=HASH,
        asset_contract=supplied_contract,
        asset_contract_sha256=HASH,
        **kwargs,
    )


def mode_contract(mode: str) -> dict:
    if mode == "generation":
        return {"conditioning_origin": "text_only", "conditioning_asset_refs": [], "ending_state": "ST-1"}
    if mode == "exact":
        return {
            "conditioning_origin": "text_only",
            "conditioning_asset_refs": [],
            "ending_state": "ST-1",
            "exact_duration_s": 4,
        }
    if mode == "long":
        return {
            "continuity_strategy": "Carry the exact boundary state into the next section.",
            "sections": [
                {"section_id": "L1", "start_s": 0, "end_s": 2, "state_in": "ST-0", "state_out": "ST-M"},
                {"section_id": "L2", "start_s": 2, "end_s": 4, "state_in": "ST-M", "state_out": "ST-1"},
            ],
        }
    if mode == "extension":
        return {
            "source_clip_ref": mode_ref("CLIP-A"),
            "direction": "after",
            "source_boundary": {"edge": "end", "state": "ST-0"},
            "generated_boundary": {"edge": "start", "state": "ST-0"},
            "seam": {"causal_bridge_event": "The same door continues closing", "preserve": ["identity", "motion", "room tone"]},
        }
    if mode == "edit":
        return {
            "source_clip_ref": mode_ref("CLIP-A"),
            "protected_elements": ["face", "background", "voice"],
            "targets": [
                {
                    "target_id": "coat",
                    "operation": "change color to blue",
                    "interval": {"start_s": 0, "end_s": 4},
                    "preserve": ["shape", "motion", "occlusion"],
                }
            ],
        }
    if mode == "transition":
        return {
            "source_a_ref": mode_ref("CLIP-A"),
            "source_b_ref": mode_ref("CLIP-B"),
            "source_a_protected_interval": {"start_s": 0, "end_s": 1.5},
            "bridge_window": {"start_s": 1.5, "end_s": 2.5},
            "source_b_protected_interval": {"start_s": 2.5, "end_s": 4},
            "source_a_end_state": "A-END",
            "source_b_start_state": "B-START",
            "bridge": {
                "observable_cause": "the first door crosses frame",
                "observable_effect": "its edge resolves as the train door",
                "preserve_a": ["A identity", "A room"],
                "preserve_b": ["B identity", "station"],
            },
        }
    if mode == "multi_panel":
        return {
            "panels": [
                {
                    "panel_id": "P1", "source_ref": mode_ref("PANEL-1"), "order": 1,
                    "role": "opening composition", "target_shot_ids": ["S001"], "interval": {"start_s": 0, "end_s": 2},
                    "binding_properties": ["composition", "identity"],
                    "excluded_properties": ["text", "camera move"],
                },
                {
                    "panel_id": "P2", "source_ref": mode_ref("PANEL-2"), "order": 2,
                    "role": "ending composition", "target_shot_ids": ["S002"], "interval": {"start_s": 2, "end_s": 4},
                    "binding_properties": ["ending pose", "prop state"],
                    "excluded_properties": ["wardrobe", "sound"],
                },
            ],
            "unrequested_additions": {
                "policy": "deny",
                "categories": ["cta", "logo", "decorative_effects"],
            },
        }
    raise AssertionError(mode)


def task(mode: str = "generation") -> dict:
    timeline = [
        {
            "segment_id": "T001",
            "start_s": 0,
            "end_s": 4,
            "observable_event": "A hears the key, understands, then releases the latch",
            "state_in": "ST-0",
            "state_out": "ST-1",
            "camera": "static medium",
            "performance": "cue, comprehension, hand release, residue",
            "sound": "key, breath, room tone",
            "asset_refs": [],
        }
    ]
    if mode == "transition":
        timeline = [
            {"segment_id": "T-A", "start_s": 0, "end_s": 1.5, "observable_event": "A protected", "state_in": "ST-0", "state_out": "A-END", "camera": "static", "performance": "source A", "sound": "source A", "asset_refs": []},
            {"segment_id": "T-BRIDGE", "start_s": 1.5, "end_s": 2.5, "observable_event": "bridge", "state_in": "A-END", "state_out": "B-START", "camera": "static", "performance": "bridge", "sound": "bridge", "asset_refs": []},
            {"segment_id": "T-B", "start_s": 2.5, "end_s": 4, "observable_event": "B protected", "state_in": "B-START", "state_out": "ST-1", "camera": "static", "performance": "source B", "sound": "source B", "asset_refs": []},
        ]
    elif mode == "multi_panel":
        timeline = [
            {"segment_id": "T001", "start_s": 0, "end_s": 2, "observable_event": "panel one", "state_in": "ST-0", "state_out": "ST-M", "camera": "static", "performance": "opening", "sound": "room tone", "asset_refs": []},
            {"segment_id": "T002", "start_s": 2, "end_s": 4, "observable_event": "panel two", "state_in": "ST-M", "state_out": "ST-1", "camera": "static", "performance": "ending", "sound": "room tone", "asset_refs": []},
        ]
    refs = mode_source_refs(mode)
    return {
        "schema_version": 1,
        "video_task_id": f"VT-{mode}",
        "revision": 1,
        "delivery_depth": "professional",
        "provider": {"name": "provider_neutral", "interface": None, "model_version": None},
        "capability_verification": {
            "status": "not_required",
            "checked_at": None,
            "source": None,
            "supported_primary_modes": [],
        },
        "primary_mode": mode,
        "source_bindings": {
            "storyboard": {"artifact_id": "SB-001", "revision": 1, "sha256": HASH},
            "continuity": {"artifact_id": "CONT-001", "revision": 1, "sha256": HASH},
            "visual_bible": {"artifact_id": "VB-001", "revision": 1, "sha256": HASH},
            "asset_contract": {"artifact_id": "AC-001", "revision": 1, "sha256": HASH},
        },
        "output": {"duration_s": 4, "aspect_ratio": "16:9", "final_state": "ST-1"},
        "global_locks": {
            "identity": {"status": "locked", "reason": None, "entries": [lock("ID-1", "CHAR-A", "identity", "canonical face")]},
            "wardrobe": {"status": "locked", "reason": None, "entries": [lock("W-1", "CHAR-A", "wardrobe", "blue coat")]},
            "space": {"status": "locked", "reason": None, "entries": [lock("S-1", "LOC-1", "geometry", "door east of table")]},
            "voice": {"status": "not_applicable", "reason": "No spoken voice.", "entries": []},
        },
        "reference_uses": [
            {
                "use_id": f"USE-{asset_id}",
                "authorization_id": f"AUTH-{asset_id}",
                "source_ref": asset_ref(asset_id),
                "borrow": [role],
                "targets": ["OUTPUT"],
                "interval": {"start_s": 0, "end_s": 4},
            }
            for asset_id, role in refs
        ],
        "timeline": timeline,
        "mode_contracts": {mode: mode_contract(mode)},
        "targeted_exclusions": [],
        "handoff_state": "ST-1",
    }


class VideoTaskAuditTests(unittest.TestCase):
    def test_all_provider_neutral_modes_have_executable_contracts(self) -> None:
        self.assertEqual(PRIMARY_MODES, {"generation", "exact", "long", "extension", "edit", "transition", "multi_panel"})
        for mode in sorted(PRIMARY_MODES):
            with self.subTest(mode=mode):
                self.assertEqual(audit_document(task(mode)), [])

    def test_provider_specific_task_requires_current_capability_evidence(self) -> None:
        payload = task()
        payload["provider"] = {"name": "seedance", "interface": "host UI", "model_version": None}
        codes = {item.code for item in audit_document(payload, asset_contract=asset_contract())}
        self.assertTrue({"provider-capability-unverified", "missing-provider-model-version", "primary-mode-not-verified"}.issubset(codes))

        payload["provider"]["model_version"] = "version shown in current UI"
        payload["capability_verification"] = {
            "status": "verified",
            "checked_at": "2026-08-31",
            "source": "current provider interface",
            "supported_primary_modes": ["generation"],
        }
        self.assertEqual(audit_document(payload, asset_contract=asset_contract()), [])

    def test_reference_cannot_borrow_beyond_authorization(self) -> None:
        contract = asset_contract()
        contract["source_assets"] = [{"asset_id": "REF-1", "revision": 1, "media_type": "video", "provider_asset_id": "IMMUTABLE-REF-1", "provider_asset_version": "v1"}]
        contract["borrow_authorizations"] = [
            {
                "authorization_id": "AUTH-1",
                "source_ref": asset_ref("REF-1"),
                "borrow": ["motion"],
                "targets": ["CHAR-A"],
                "interval": {"start_s": 0, "end_s": 4},
                "preserve": ["target identity"],
                "exclude": ["source identity", "source wardrobe"],
            }
        ]
        payload = task()
        payload["reference_uses"] = [
            {
                "use_id": "USE-1",
                "authorization_id": "AUTH-1",
                "source_ref": asset_ref("REF-1"),
                "borrow": ["motion", "identity"],
                "targets": ["CHAR-A"],
                "interval": {"start_s": 0, "end_s": 4},
            }
        ]
        self.assertIn("borrow-exceeds-authorization", {item.code for item in audit_document(payload, asset_contract=contract)})

    def test_mode_timeline_and_handoff_conflicts_are_local(self) -> None:
        payload = task("extension")
        payload["mode_contracts"]["generation"] = mode_contract("generation")
        payload["timeline"][0]["end_s"] = 3
        payload["handoff_state"] = "BROKEN"
        codes = {item.code for item in audit_document(payload, asset_contract=asset_contract())}
        self.assertTrue({"multiple-or-missing-mode-contract", "timeline-duration-conflict", "task-handoff-conflict"}.issubset(codes))

    def test_specialized_modes_reject_missing_seam_target_bridge_and_mapping(self) -> None:
        broken_cases = []
        extension = task("extension")
        extension["mode_contracts"]["extension"]["seam"] = {}
        broken_cases.append((extension, "incomplete-mode-contract"))
        edit = task("edit")
        edit["mode_contracts"]["edit"]["protected_elements"] = []
        broken_cases.append((edit, "missing-edit-protected-elements"))
        transition = task("transition")
        transition["mode_contracts"]["transition"]["source_b_ref"] = mode_ref("CLIP-A")
        broken_cases.append((transition, "transition-sources-not-distinct"))
        transition_span = task("transition")
        transition_span["mode_contracts"]["transition"].pop("source_a_protected_interval")
        broken_cases.append((transition_span, "invalid-interval"))
        panels = task("multi_panel")
        panels["mode_contracts"]["multi_panel"]["panels"][0]["target_shot_ids"] = [None]
        broken_cases.append((panels, "invalid-panel-shot-targets"))
        panel_scope = task("multi_panel")
        panel_scope["mode_contracts"]["multi_panel"]["panels"][0]["binding_properties"] = []
        broken_cases.append((panel_scope, "missing-panel-property-scope"))
        panel_additions = task("multi_panel")
        panel_additions["mode_contracts"]["multi_panel"]["unrequested_additions"]["categories"] = ["logo"]
        broken_cases.append((panel_additions, "incomplete-panel-additions-exclusions"))
        for payload, expected in broken_cases:
            with self.subTest(code=expected):
                self.assertIn(expected, {item.code for item in audit_document(payload, asset_contract=asset_contract())})

    def test_mode_contracts_are_bound_to_output_timeline_and_authorized_sources(self) -> None:
        generation = task("generation")
        generation["mode_contracts"]["generation"]["ending_state"] = "OTHER"
        self.assertIn("generation-ending-state-conflict", {item.code for item in audit_document(generation, asset_contract=asset_contract())})

        extension = task("extension")
        extension["mode_contracts"]["extension"]["generated_boundary"]["state"] = "OTHER"
        extension_codes = {item.code for item in audit_document(extension, asset_contract=asset_contract())}
        self.assertTrue({"extension-seam-state-conflict", "extension-timeline-boundary-conflict"}.issubset(extension_codes))

        edit = task("edit")
        edit["mode_contracts"]["edit"]["targets"][0]["interval"]["end_s"] = 5
        self.assertIn("edit-target-outside-output", {item.code for item in audit_document(edit, asset_contract=asset_contract())})

        panels = task("multi_panel")
        panels["mode_contracts"]["multi_panel"]["panels"][1]["interval"] = {"start_s": 3, "end_s": 5}
        panel_codes = {item.code for item in audit_document(panels, asset_contract=asset_contract())}
        self.assertTrue({"panel-interval-outside-output", "panel-coverage-gap", "panel-coverage-duration-conflict"}.issubset(panel_codes))

        unauthorized = task("transition")
        unauthorized["reference_uses"] = []
        unauthorized_codes = {item.code for item in audit_document(unauthorized, asset_contract=asset_contract())}
        self.assertIn("mode-source-unauthorized", unauthorized_codes)

        unregistered_contract = asset_contract()
        unregistered_contract["source_assets"] = []
        unregistered_codes = {item.code for item in audit_document(task("edit"), asset_contract=unregistered_contract)}
        self.assertIn("mode-source-unregistered", unregistered_codes)

        wrong_role = task("edit")
        wrong_role["reference_uses"][0]["borrow"] = ["transition_source_a"]
        self.assertIn("mode-source-role-unauthorized", {item.code for item in audit_document(wrong_role, asset_contract=asset_contract())})

        wrong_target = task("edit")
        wrong_target["reference_uses"][0]["targets"] = ["UNRELATED"]
        self.assertIn("mode-source-target-unauthorized", {item.code for item in audit_document(wrong_target, asset_contract=asset_contract())})

        short_use = task("edit")
        short_use["reference_uses"][0]["interval"] = {"start_s": 0, "end_s": 1}
        self.assertIn("mode-source-interval-unauthorized", {item.code for item in audit_document(short_use, asset_contract=asset_contract())})

    def test_panel_shot_ids_and_times_bind_the_supplied_storyboard(self) -> None:
        unknown = task("multi_panel")
        unknown["mode_contracts"]["multi_panel"]["panels"][0]["target_shot_ids"] = ["DOES-NOT-EXIST"]
        self.assertIn(
            "unknown-panel-shot-target",
            {item.code for item in audit_document(unknown, asset_contract=asset_contract(), storyboard=storyboard())},
        )

        wrong_time = task("multi_panel")
        wrong_time["mode_contracts"]["multi_panel"]["panels"][0]["interval"] = {"start_s": 0, "end_s": 4}
        self.assertIn(
            "panel-shot-time-conflict",
            {item.code for item in audit_document(wrong_time, asset_contract=asset_contract(), storyboard=storyboard())},
        )

    def test_video_locks_exactly_inherit_bound_continuity(self) -> None:
        payload = task("generation")
        continuity = {
            "continuity_id": "CONT-001",
            "revision": 1,
            "source_bindings": {
                "storyboard": {"artifact_id": "SB-001", "revision": 1, "sha256": HASH},
                "visual_bible": {"artifact_id": "VB-001", "revision": 1, "sha256": HASH},
            },
            "global_locks": copy.deepcopy(payload["global_locks"]),
        }
        self.assertEqual(audit_document(payload, asset_contract=asset_contract(), continuity=continuity), [])
        payload["global_locks"]["identity"]["entries"][0]["value"] = "different face"
        self.assertIn(
            "continuity-lock-conflict",
            {item.code for item in audit_document(payload, asset_contract=asset_contract(), continuity=continuity)},
        )

    def test_production_mode_requires_every_actual_upstream_document_and_continuity_chain(self) -> None:
        codes = {item.code for item in _audit_document(task())}
        self.assertTrue(
            {
                "missing-supplied-storyboard",
                "missing-supplied-continuity",
                "missing-supplied-visual-bible",
                "missing-supplied-asset-contract",
            }.issubset(codes)
        )
        mismatched = continuity()
        mismatched["source_bindings"]["visual_bible"]["artifact_id"] = "VB-OTHER"
        self.assertIn(
            "continuity-visual-bible-id-mismatch",
            {item.code for item in audit_document(task(), continuity=mismatched)},
        )

    def test_mode_source_requires_immutable_asset_binding(self) -> None:
        contract = asset_contract()
        contract["source_assets"][0] = {**asset_ref("CLIP-A"), "media_type": "video", "file_or_slot": "slot-1"}
        codes = {item.code for item in audit_document(task("edit"), asset_contract=contract)}
        self.assertTrue({"missing-immutable-source-binding", "mode-source-unregistered"}.issubset(codes))

    def test_local_media_binding_checks_bytes_and_safe_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clip = root / "clip.bin"
            clip.write_bytes(b"locked media bytes")
            contract = asset_contract()
            contract["source_assets"][0] = {
                **asset_ref("CLIP-A"),
                "media_type": "video",
                "local_file": "clip.bin",
                "sha256": hashlib.sha256(clip.read_bytes()).hexdigest(),
            }
            self.assertEqual(audit_document(task("edit"), asset_contract=contract, asset_media_root=root), [])
            clip.write_bytes(b"replaced bytes")
            self.assertIn(
                "local-media-hash-mismatch",
                {item.code for item in audit_document(task("edit"), asset_contract=contract, asset_media_root=root)},
            )


if __name__ == "__main__":
    unittest.main()
