from __future__ import annotations

import json
import unittest
from pathlib import Path


CASES_PATH = Path(__file__).resolve().parent / "forward" / "cases.json"


class ForwardCaseContractTests(unittest.TestCase):
    def test_case_schema_and_coverage(self) -> None:
        payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        cases = payload["cases"]
        self.assertGreaterEqual(len(cases), 7)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
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


if __name__ == "__main__":
    unittest.main()
