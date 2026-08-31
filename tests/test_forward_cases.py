from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml


CASES_PATH = Path(__file__).resolve().parent / "forward" / "cases.json"


class ForwardCaseContractTests(unittest.TestCase):
    def test_case_schema_and_coverage(self) -> None:
        payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        cases = payload["cases"]
        self.assertGreaterEqual(len(cases), 22)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(
            {
                "FT-08",
                "FT-09",
                "FT-10",
                "FT-11",
                "FT-12",
                "FT-13",
                "FT-14",
                "FT-15",
                "FT-16",
                "FT-17",
                "FT-18",
                "FT-19",
                "FT-20",
                "FT-21",
                "FT-22",
            }.issubset(ids)
        )
        routing_should_trigger = {case["should_invoke"] for case in cases}
        self.assertEqual(routing_should_trigger, {True, False})
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertIsInstance(case["id"], str)
                self.assertTrue(case["id"].strip())
                self.assertIsInstance(case["title"], str)
                self.assertTrue(case["title"].strip())
                self.assertIs(type(case["should_invoke"]), bool)
                self.assertTrue(case["request"].strip())
                self.assertTrue(case["input"].strip())
                self.assertGreaterEqual(len(case["hard_invariants"]), 2)
                self.assertGreaterEqual(len(case["human_rubric"]), 1)
                for invariant in case["hard_invariants"]:
                    self.assertIsInstance(invariant, str)
                    self.assertTrue(invariant.strip())
                for rubric_item in case["human_rubric"]:
                    self.assertIsInstance(rubric_item, str)
                    self.assertTrue(rubric_item.strip())

        staged = next(case for case in cases if case["id"] == "FT-14")
        self.assertEqual(staged["execution_mode"], "staged_external_artifacts")
        self.assertIn("pending", staged["request"])
        fused = next(case for case in cases if case["id"] == "FT-18")
        self.assertEqual(fused["execution_mode"], "staged_external_artifacts")
        self.assertIn("pending", fused["request"])

    def test_staged_deep_record_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        record = yaml.safe_load((root / "assets/templates/staged-life-path-eval.yaml").read_text(encoding="utf-8"))
        self.assertEqual(record["case_id"], "FT-14")
        self.assertFalse(record["claim_boundary"]["behavior_pass"])
        self.assertIn("compile_phase", record)
        self.assertIn("scene_phase", record)
        self.assertEqual(len(record["counterfactual_runs"]), 5)
        protocol = (root / "tests/forward/staged-deep-protocol.md").read_text(encoding="utf-8")
        self.assertIn("fresh task", protocol)
        self.assertIn("behavior_pass: false", protocol)


if __name__ == "__main__":
    unittest.main()
