from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.audit_staged_eval import audit_file, audit_record, file_sha256, load_record
from tests.test_life_paths_audit import (
    DEFAULT_MINIMUM_CHINESE_CHARACTERS,
    candidate_sha256,
    causal_node,
    enable_compilation,
    locked_manifest,
    varied_body,
    write_and_approve,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
PLANNING_TEMPLATE = ROOT / "assets" / "templates" / "staged-life-path-eval.yaml"
RUN_KINDS = (
    "locked_baseline",
    "branch_swap",
    "occupational_context_swap",
    "causal_node_ablation",
    "dialogue_deletion",
)
EXPECTED_CHANGED_INPUTS = {
    "locked_baseline": [],
    "branch_swap": ["variant_context.workbench_file"],
    "occupational_context_swap": ["variant_context.occupational_context_file"],
    "causal_node_ablation": ["variant_context.ablated_source_ref"],
    "dialogue_deletion": ["variant_context.source_output_sha256"],
}


def finding_codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def write_file(root: Path, name: str, content: str) -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": name, "sha256": file_sha256(path)}


def lock_variant(payload: dict, branch_id: str, *, revision: int, biography_file: str) -> None:
    for candidate in payload["candidates"]:
        candidate["status"] = "locked" if candidate["id"] == branch_id else "rejected"
    selected = next(candidate for candidate in payload["candidates"] if candidate["id"] == branch_id)
    selected_hash = candidate_sha256(selected)
    selection = payload["selection"]
    selection.update(
        {
            "state": "locked",
            "selected_branch_id": branch_id,
            "rejected_branch_ids": [candidate["id"] for candidate in payload["candidates"] if candidate["id"] != branch_id],
            "author_lock": True,
            "lock_revision": revision,
            "locked_candidate_sha256": selected_hash,
        }
    )
    selection["author_decision"].update(
        {
            "decision_text": f"作者为受控评估锁定 {branch_id}",
            "approved_character_id": payload["character_id"],
            "approved_package_context_id": payload["package_context_id"],
            "approved_branch_id": branch_id,
            "approved_fact_boundary_sha256": selection["locked_fact_boundary_sha256"],
            "approved_candidate_sha256": selected_hash,
            "approved_lock_revision": revision,
        }
    )
    biography = payload["deep_biography"]
    biography["status"] = "ready"
    biography["biography_revision"] = revision
    biography["biography_file"] = biography_file
    biography["coverage_stages"][0]["source_node_refs"] = [
        f"life-path:{branch_id}/{node['id']}" for node in selected["causal_spine"]
    ]


def write_variant_package(
    root: Path,
    payload: dict,
    *,
    manifest_name: str,
    biography_name: str,
    runtime_name: str,
    source_refs: list[str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    digest = write_and_approve(
        root,
        payload,
        varied_body(DEFAULT_MINIMUM_CHINESE_CHARACTERS),
        filename=biography_name,
    )
    refs_text = ", ".join(source_refs)
    enable_compilation(root, payload, digest, {runtime_name: f"source_refs: [{refs_text}]\n"})
    workbench = write_file(root, manifest_name, json.dumps(payload, ensure_ascii=False, indent=2))
    biography_path = root / biography_name
    runtime_path = root / runtime_name
    biography = {"path": biography_name, "sha256": file_sha256(biography_path)}
    runtime = {"path": runtime_name, "sha256": file_sha256(runtime_path)}
    return workbench, biography, runtime


def complete_record(root: Path) -> tuple[dict, Path]:
    (root / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    workbench_payload = locked_manifest()
    workbench_payload["candidates"][0]["causal_spine"].append(causal_node("a", "node-2"))
    lock_variant(workbench_payload, "path-a", revision=1, biography_file="biography.md")
    approved_body_sha256 = write_and_approve(
        root,
        workbench_payload,
        varied_body(DEFAULT_MINIMUM_CHINESE_CHARACTERS),
    )
    baseline_refs = ["life-path:path-a/node-1", "life-path:path-a/node-2"]
    enable_compilation(
        root,
        workbench_payload,
        approved_body_sha256,
        {"compiled/character.yaml": f"source_refs: [{', '.join(baseline_refs)}]\n"},
    )
    workbench_path = write_manifest(root, workbench_payload)
    biography_path = root / "biography.md"
    runtime_path = root / "compiled" / "character.yaml"
    workbench = {"path": workbench_path.relative_to(root).as_posix(), "sha256": file_sha256(workbench_path)}
    biography = {"path": biography_path.relative_to(root).as_posix(), "sha256": file_sha256(biography_path)}
    runtime = {"path": runtime_path.relative_to(root).as_posix(), "sha256": file_sha256(runtime_path)}

    branch_payload = locked_manifest()
    lock_variant(branch_payload, "path-b", revision=2, biography_file="branch-biography.md")
    branch_workbench, branch_biography, branch_runtime = write_variant_package(
        root,
        branch_payload,
        manifest_name="branch-workbench.yaml",
        biography_name="branch-biography.md",
        runtime_name="compiled/branch-runtime.yaml",
        source_refs=["life-path:path-b/node-1"],
    )

    ablation_payload = locked_manifest()
    ablation_payload["candidates"][0]["causal_spine"].append(causal_node("a", "node-2"))
    ablation_payload["candidates"][0]["causal_spine"] = [
        node for node in ablation_payload["candidates"][0]["causal_spine"] if node["id"] != "node-1"
    ]
    lock_variant(ablation_payload, "path-a", revision=2, biography_file="ablation-biography.md")
    ablation_workbench, ablation_biography, ablation_runtime = write_variant_package(
        root,
        ablation_payload,
        manifest_name="ablation-workbench.yaml",
        biography_name="ablation-biography.md",
        runtime_name="compiled/ablation-runtime.yaml",
        source_refs=["life-path:path-a/node-2"],
    )

    scene = write_file(root, "outputs/scene.fountain", "INT. ROOM - DAY\n\nA visible choice.\n")
    baseline_occupation = write_file(root, "inputs/occupation-baseline.yaml", "context: baseline-occupation\n")
    variant_occupation = write_file(root, "inputs/occupation-variant.yaml", "context: alternate-occupation\n")

    outputs = {
        kind: write_file(root, f"outputs/{kind}.txt", f"completed output for {kind}\n")
        for kind in RUN_KINDS
    }
    inputs_by_kind = {
        "locked_baseline": [runtime, baseline_occupation],
        "branch_swap": [branch_runtime],
        "occupational_context_swap": [runtime, variant_occupation],
        "causal_node_ablation": [ablation_runtime],
        "dialogue_deletion": [outputs["locked_baseline"]],
    }
    refs_by_kind = {
        "locked_baseline": baseline_refs,
        "branch_swap": ["life-path:path-b/node-1"],
        "occupational_context_swap": baseline_refs,
        "causal_node_ablation": ["life-path:path-a/node-2"],
        "dialogue_deletion": baseline_refs,
    }
    contexts_by_kind = {
        "locked_baseline": {
            "kind": "locked_baseline",
            "occupational_context_file": baseline_occupation,
        },
        "branch_swap": {
            "kind": "branch_swap",
            "workbench_file": branch_workbench,
            "biography_file": branch_biography,
        },
        "occupational_context_swap": {
            "kind": "occupational_context_swap",
            "occupational_context_file": variant_occupation,
            "preserved_candidate_sha256": workbench_payload["selection"]["locked_candidate_sha256"],
        },
        "causal_node_ablation": {
            "kind": "causal_node_ablation",
            "workbench_file": ablation_workbench,
            "biography_file": ablation_biography,
            "ablated_source_ref": "life-path:path-a/node-1",
        },
        "dialogue_deletion": {
            "kind": "dialogue_deletion",
            "source_run_kind": "locked_baseline",
            "source_output_sha256": outputs["locked_baseline"]["sha256"],
            "removed_dialogue_units": 1,
        },
    }

    runs = []
    for index, kind in enumerate(RUN_KINDS, start=1):
        output = outputs[kind]
        runs.append(
            {
                "kind": kind,
                "status": "completed",
                "fresh_task_id": f"run-task-{index}",
                "model_and_version": "test-model/version-1",
                "changed_inputs": EXPECTED_CHANGED_INPUTS[kind],
                "variant_context": contexts_by_kind[kind],
                "input_file_hashes": inputs_by_kind[kind],
                "canonical_source_refs": refs_by_kind[kind],
                "output_file": output["path"],
                "output_hash": output["sha256"],
                "blind_output_id": f"blind-{index}",
            }
        )

    baseline_run = runs[0]
    visible_deltas = [
        {
            "run_kind": kind,
            "observed_delta": f"recorded comparison for {kind}",
            "locked_source_refs": refs_by_kind[kind][:1],
            "baseline_task_id": baseline_run["fresh_task_id"],
            "baseline_output_sha256": baseline_run["output_hash"],
            "variant_task_id": run["fresh_task_id"],
            "variant_output_sha256": run["output_hash"],
            "traceable": True,
        }
        for kind, run in zip(RUN_KINDS, runs)
        if kind != "locked_baseline"
    ]
    record = {
        "schema_version": 1,
        "record_id": "staged-record-1",
        "case_id": "FT-14",
        "status": "completed",
        "artifact_set": {
            "project_root": ".",
            "workbench_file": workbench,
            "biography_file": biography,
            "relationship_ledger_file": None,
            "locked_fact_boundary_sha256": workbench_payload["selection"]["locked_fact_boundary_sha256"],
            "locked_candidate_sha256": workbench_payload["selection"]["locked_candidate_sha256"],
            "life_path_lock_revision": 1,
            "approved_biography_revision": 1,
            "approved_biography_sha256": approved_body_sha256,
            "deep_audit_command": "python scripts/audit_life_paths.py life-path-workbench.yaml --require-locked",
            "deep_audit_passed": True,
        },
        "compile_phase": {
            "fresh_task_id": "compile-task",
            "model_and_version": "test-model/version-1",
            "input_file_hashes": [workbench, biography],
            "output_artifact_files": [runtime],
            "canonical_source_refs": baseline_refs,
            "compile_audit_passed": True,
        },
        "scene_phase": {
            "fresh_task_id": "scene-task",
            "model_and_version": "test-model/version-1",
            "received_compiled_assets_only": True,
            "excluded_inputs": ["long_biography", "rejected_candidates", "prior_generation_transcript"],
            "input_file_hashes": [runtime],
            "scene_output_file": scene["path"],
            "output_hash": scene["sha256"],
        },
        "counterfactual_runs": runs,
        "traceability": {
            "visible_deltas": visible_deltas,
            "explicit_branch_leaks": [],
            "semantic_branch_leak_review": "passed",
        },
        "blind_review": {
            "randomized_output_ids": [run["blind_output_id"] for run in reversed(runs)],
            "reviewer_ids": ["reviewer-1"],
            "actor_playability": [{"output_id": run["blind_output_id"], "status": "passed", "rating": 4} for run in runs],
            "character_identifiability": [{"output_id": run["blind_output_id"], "status": "passed", "rating": 4} for run in runs],
            "nonverbal_replacement": [{"output_id": run["blind_output_id"], "status": "passed", "rating": 4} for run in runs],
            "relationship_truth": [{"output_id": run["blind_output_id"], "status": "passed", "rating": 4} for run in runs],
            "read_aloud_naturalness": [{"output_id": run["blind_output_id"], "status": "passed", "rating": 4} for run in runs],
            "repair_reasons": ["none recorded"],
        },
        "claim_boundary": {
            "behavior_pass": True,
            "reason": "All declared mechanical evidence is present; artistic quality remains a human judgment.",
        },
    }
    return record, root / "staged-eval.yaml"


def rewrite_ablation_variant(root: Path, record: dict, mutation) -> None:
    workbench_path = root / "ablation-workbench.yaml"
    workbench = json.loads(workbench_path.read_text(encoding="utf-8"))
    selected = next(
        candidate
        for candidate in workbench["candidates"]
        if candidate["id"] == workbench["selection"]["selected_branch_id"]
    )
    mutation(selected)
    selected_hash = candidate_sha256(selected)
    workbench["selection"]["locked_candidate_sha256"] = selected_hash
    workbench["selection"]["author_decision"]["approved_candidate_sha256"] = selected_hash
    biography_digest = write_and_approve(
        root,
        workbench,
        varied_body(DEFAULT_MINIMUM_CHINESE_CHARACTERS),
        filename="ablation-biography.md",
    )
    enable_compilation(
        root,
        workbench,
        biography_digest,
        {"compiled/ablation-runtime.yaml": "source_refs: [life-path:path-a/node-2]\n"},
    )
    workbench_path.write_text(json.dumps(workbench, ensure_ascii=False, indent=2), encoding="utf-8")

    run = next(item for item in record["counterfactual_runs"] if item["kind"] == "causal_node_ablation")
    run["variant_context"]["workbench_file"]["sha256"] = file_sha256(workbench_path)
    biography_path = root / "ablation-biography.md"
    run["variant_context"]["biography_file"]["sha256"] = file_sha256(biography_path)
    runtime_path = root / "compiled" / "ablation-runtime.yaml"
    run["input_file_hashes"] = [
        {"path": "compiled/ablation-runtime.yaml", "sha256": file_sha256(runtime_path)}
    ]


class StagedEvaluationAuditTests(unittest.TestCase):
    def test_planning_template_with_false_claim_passes_basic_schema(self) -> None:
        payload = load_record(PLANNING_TEMPLATE)
        self.assertFalse(payload["claim_boundary"]["behavior_pass"])
        self.assertEqual(audit_record(payload, PLANNING_TEMPLATE), [])

    def test_empty_planning_template_cannot_masquerade_as_pass(self) -> None:
        payload = copy.deepcopy(load_record(PLANNING_TEMPLATE))
        payload["claim_boundary"]["behavior_pass"] = True
        payload["claim_boundary"]["reason"] = "claimed complete without evidence"

        codes = finding_codes(audit_record(payload, PLANNING_TEMPLATE))

        self.assertTrue(
            {
                "incomplete-status",
                "missing-record-id",
                "missing-project-root",
                "deep-audit-not-passed",
                "compile-audit-not-passed",
                "incomplete-run",
                "traceability-incomplete",
                "semantic-review-not-passed",
                "empty-blind-review-field",
            }.issubset(codes)
        )

    def test_missing_file_and_wrong_hash_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["scene_phase"]["scene_output_file"] = "outputs/missing.fountain"
            payload["scene_phase"]["output_hash"] = "0" * 64
            self.assertIn("missing-file", finding_codes(audit_record(payload, record_path)))

            payload, record_path = complete_record(root)
            payload["scene_phase"]["output_hash"] = "0" * 64
            self.assertIn("file-hash-mismatch", finding_codes(audit_record(payload, record_path)))

    def test_mechanically_complete_record_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            self.assertEqual(audit_record(payload, record_path), [])

    def test_compile_and_scene_must_use_distinct_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["scene_phase"]["fresh_task_id"] = payload["compile_phase"]["fresh_task_id"]
            self.assertIn("phase-task-reuse", finding_codes(audit_record(payload, record_path)))

    def test_scene_inputs_must_equal_compiled_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["scene_phase"]["input_file_hashes"] = [payload["artifact_set"]["biography_file"]]
            self.assertIn("scene-input-not-compiled", finding_codes(audit_record(payload, record_path)))

    def test_compile_inputs_must_include_audited_deep_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["compile_phase"]["input_file_hashes"] = payload["compile_phase"]["output_artifact_files"]
            self.assertIn("compile-input-binding-mismatch", finding_codes(audit_record(payload, record_path)))

    def test_workbench_declared_relationship_ledger_must_be_staged_and_compiled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            write_file(
                root,
                "relationship-ledger.yaml",
                "schema_version: 1\nrelationships: []\nshared_event_registry: []\nshared_memory_contracts: []\n",
            )
            workbench_path = root / payload["artifact_set"]["workbench_file"]["path"]
            workbench = json.loads(workbench_path.read_text(encoding="utf-8"))
            workbench["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            workbench_path.write_text(json.dumps(workbench, ensure_ascii=False, indent=2), encoding="utf-8")
            payload["artifact_set"]["workbench_file"]["sha256"] = file_sha256(workbench_path)

            codes = finding_codes(audit_record(payload, record_path))

            self.assertIn("missing-staged-relationship-ledger", codes)

    def test_trace_refs_must_come_from_compiled_source_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            for delta in payload["traceability"]["visible_deltas"]:
                delta["locked_source_refs"] = ["life-path:fake/fake"]
            self.assertIn("trace-source-outside-compile", finding_codes(audit_record(payload, record_path)))

    def test_traceability_must_bind_actual_run_task_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            delta = payload["traceability"]["visible_deltas"][0]
            delta["variant_task_id"] = "invented-task"
            delta["variant_output_sha256"] = "0" * 64
            self.assertIn("trace-run-binding-mismatch", finding_codes(audit_record(payload, record_path)))

    def test_byte_identical_counterfactual_outputs_do_not_demonstrate_a_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            baseline = payload["counterfactual_runs"][0]
            variant = payload["counterfactual_runs"][1]
            baseline_path = root / baseline["output_file"]
            variant_path = root / variant["output_file"]
            variant_path.write_bytes(baseline_path.read_bytes())
            variant["output_hash"] = file_sha256(variant_path)
            payload["traceability"]["visible_deltas"][0]["variant_output_sha256"] = variant["output_hash"]
            self.assertIn("identical-run-output", finding_codes(audit_record(payload, record_path)))

    def test_blind_review_ids_must_map_to_every_actual_run_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["blind_review"]["randomized_output_ids"] = ["ghost-output"]
            for field in (
                "actor_playability",
                "character_identifiability",
                "nonverbal_replacement",
                "relationship_truth",
                "read_aloud_naturalness",
            ):
                payload["blind_review"][field] = [{"output_id": "ghost-output", "evidence": False}]
            codes = finding_codes(audit_record(payload, record_path))
            self.assertIn("blind-output-binding-mismatch", codes)
            self.assertIn("empty-blind-review-field", codes)

    def test_five_runs_must_have_independent_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][1]["fresh_task_id"] = payload["counterfactual_runs"][0]["fresh_task_id"]
            self.assertIn("run-task-reuse", finding_codes(audit_record(payload, record_path)))

    def test_counterfactual_run_cannot_reuse_phase_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][0]["fresh_task_id"] = payload["compile_phase"]["fresh_task_id"]
            self.assertIn("run-task-reuse", finding_codes(audit_record(payload, record_path)))

    def test_variant_run_must_name_its_changed_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][1]["changed_inputs"] = []
            self.assertIn("missing-variant-change", finding_codes(audit_record(payload, record_path)))

    def test_changed_inputs_cannot_be_an_arbitrary_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][1]["changed_inputs"] = ["foo"]
            self.assertIn("changed-input-binding-mismatch", finding_codes(audit_record(payload, record_path)))

    def test_branch_swap_requires_an_independently_audited_locked_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            branch = payload["counterfactual_runs"][1]
            branch["variant_context"]["workbench_file"] = payload["artifact_set"]["workbench_file"]
            branch["variant_context"]["biography_file"] = payload["artifact_set"]["biography_file"]
            codes = finding_codes(audit_record(payload, record_path))
            self.assertIn("variant-workbench-reuses-baseline", codes)
            self.assertIn("branch-swap-unchanged", codes)

    def test_node_ablation_must_remove_exactly_the_named_locked_node(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][3]["variant_context"]["ablated_source_ref"] = "life-path:path-a/not-a-node"
            self.assertIn("invalid-ablated-source-ref", finding_codes(audit_record(payload, record_path)))

    def test_node_ablation_rejects_every_nonablated_candidate_change(self) -> None:
        def change_premise(candidate: dict) -> None:
            candidate["premise"] = "confounding premise change"

        def change_surviving_node(candidate: dict) -> None:
            candidate["causal_spine"][0]["situation"] = "confounding surviving-node change"

        def change_other_content(candidate: dict) -> None:
            candidate["creative_consequences"] = ["confounding consequence change"]

        for label, mutation in (
            ("premise", change_premise),
            ("surviving-node", change_surviving_node),
            ("other-content", change_other_content),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload, record_path = complete_record(root)
                rewrite_ablation_variant(root, payload, mutation)

                codes = finding_codes(audit_record(payload, record_path))

                self.assertIn("node-ablation-content-mismatch", codes)

    def test_variant_change_requires_nonempty_labels_and_changed_hashed_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["counterfactual_runs"][1]["changed_inputs"] = [False]
            payload["counterfactual_runs"][1]["input_file_hashes"] = payload["counterfactual_runs"][0]["input_file_hashes"]
            codes = finding_codes(audit_record(payload, record_path))
            self.assertIn("invalid-changed-inputs", codes)
            self.assertIn("missing-variant-change", codes)
            self.assertIn("variant-inputs-unchanged", codes)

    def test_run_output_cannot_be_replaced_by_an_alternate_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            run = payload["counterfactual_runs"][0]
            run["output_file_hashes"] = [{"path": run["output_file"], "sha256": run["output_hash"]}]
            run["output_file"] = None
            codes = finding_codes(audit_record(payload, record_path))
            self.assertIn("missing-run-output", codes)
            self.assertIn("ambiguous-run-output", codes)

    def test_run_output_requires_one_file_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            run = payload["counterfactual_runs"][1]
            extra = write_file(root, "outputs/extra-branch-output.txt", "an extra unreviewed output\n")
            run["output_file"] = {
                run["output_file"]: run["output_hash"],
                extra["path"]: extra["sha256"],
            }

            self.assertIn("invalid-run-output-descriptor", finding_codes(audit_record(payload, record_path)))

    def test_dialogue_deletion_rejects_additional_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            extra = write_file(root, "inputs/undeclared-dialogue-context.txt", "extra uncontrolled context\n")
            dialogue_run = next(
                run for run in payload["counterfactual_runs"] if run["kind"] == "dialogue_deletion"
            )
            dialogue_run["input_file_hashes"].append(extra)

            self.assertIn("dialogue-deletion-input-mismatch", finding_codes(audit_record(payload, record_path)))

    def test_run_output_cannot_reuse_scene_or_upstream_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            run = payload["counterfactual_runs"][0]
            run["output_file"] = payload["scene_phase"]["scene_output_file"]
            run["output_hash"] = payload["scene_phase"]["output_hash"]
            self.assertIn("run-output-reuses-existing-file", finding_codes(audit_record(payload, record_path)))

    def test_duplicate_and_hardlinked_outputs_are_not_independent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            first = root / payload["counterfactual_runs"][0]["output_file"]
            linked = root / "outputs" / "linked-variant.txt"
            try:
                os.link(first, linked)
            except OSError as exc:
                self.skipTest(f"Hard links unavailable: {exc}")
            second = payload["counterfactual_runs"][1]
            second["output_file"] = linked.relative_to(root).as_posix()
            second["output_hash"] = file_sha256(linked)
            self.assertIn("run-output-reuse", finding_codes(audit_record(payload, record_path)))

    def test_duplicate_file_bindings_do_not_collapse_through_sets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["scene_phase"]["input_file_hashes"].append(payload["scene_phase"]["input_file_hashes"][0])
            self.assertIn("duplicate-file-reference", finding_codes(audit_record(payload, record_path)))

    def test_malformed_compile_source_refs_fail_without_exception(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["compile_phase"]["canonical_source_refs"] = [{}]
            self.assertIn("invalid-compile-source-refs", finding_codes(audit_record(payload, record_path)))

    def test_false_like_review_evidence_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            payload["traceability"]["visible_deltas"][0]["observed_delta"] = False
            payload["blind_review"]["reviewer_ids"] = [False]
            codes = finding_codes(audit_record(payload, record_path))
            self.assertIn("missing-observed-delta", codes)
            self.assertIn("empty-blind-review-field", codes)

    def test_semantic_review_mapping_fails_closed_on_conflicting_outcomes(self) -> None:
        cases = (
            ("failed-status", {"passed": True, "status": "failed"}),
            ("failed-result", {"passed": True, "result": "failed"}),
            ("failed-review-status", {"passed": True, "review_status": "failed"}),
            ("false-passed", {"passed": False, "status": "passed"}),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            for label, review in cases:
                with self.subTest(label=label):
                    payload["traceability"]["semantic_branch_leak_review"] = review
                    self.assertIn(
                        "semantic-review-not-passed",
                        finding_codes(audit_record(payload, record_path)),
                    )

    def test_failed_rejected_or_nonpositive_blind_review_cannot_pass(self) -> None:
        cases = (
            ("failed-status", {"status": "failed", "rating": 4, "evidence": "total rewrite required"}),
            ("rejected-verdict", {"verdict": "reject", "evidence": "not usable"}),
            ("negative-verdict", {"verdict": "negative", "evidence": "not usable"}),
            ("zero-rating", {"rating": 0, "evidence": "not usable"}),
            ("negative-rating", {"rating": -1, "evidence": "not usable"}),
            ("positive-rating-only", {"rating": 4, "evidence": "scale threshold was not declared"}),
            ("evidence-only", {"evidence": "detail exists but no outcome was recorded"}),
        )
        for label, outcome in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload, record_path = complete_record(root)
                review = payload["blind_review"]["actor_playability"][0]
                output_id = review["output_id"]
                review.clear()
                review.update({"output_id": output_id, **outcome})

                codes = finding_codes(audit_record(payload, record_path))

                self.assertIn("blind-review-verdict-not-passed", codes)

    def test_positive_blind_review_status_or_verdict_is_parseable(self) -> None:
        for field, value in (("status", "passed"), ("verdict", "approved")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload, record_path = complete_record(root)
                review = payload["blind_review"]["actor_playability"][0]
                output_id = review["output_id"]
                review.clear()
                review.update({"output_id": output_id, field: value})

                self.assertEqual(audit_record(payload, record_path), [])

    def test_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            payload, record_path = complete_record(project)
            outside = root / "outside.fountain"
            outside.write_text("outside\n", encoding="utf-8")
            payload["scene_phase"]["scene_output_file"] = "../outside.fountain"
            payload["scene_phase"]["output_hash"] = file_sha256(outside)
            self.assertIn("file-path-escape", finding_codes(audit_record(payload, record_path)))

    def test_symlink_file_fails_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, record_path = complete_record(root)
            target = root / "outputs" / "scene.fountain"
            link = root / "outputs" / "scene-link.fountain"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            payload["scene_phase"]["scene_output_file"] = "outputs/scene-link.fountain"
            payload["scene_phase"]["output_hash"] = file_sha256(target)
            self.assertIn("file-symlink", finding_codes(audit_record(payload, record_path)))

    def test_audit_file_loads_a_complete_yaml_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            if __import__("scripts.audit_staged_eval", fromlist=["yaml"]).yaml is None:
                self.skipTest("PyYAML unavailable")
            import yaml

            root = Path(directory)
            payload, record_path = complete_record(root)
            record_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertEqual(audit_file(record_path), [])


if __name__ == "__main__":
    unittest.main()
