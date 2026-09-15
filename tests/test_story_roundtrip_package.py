"""Check the shipped round-trip contract, not model behavior or artistic quality."""

from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from scripts.package_skill import RELEASE_FILES
from scripts.validate_repo import validate


ROOT = Path(__file__).resolve().parents[1]


class RoundtripPackageTests(unittest.TestCase):
    def test_roundtrip_resources_ship_and_release_links_resolve(self):
        required = {
            "references/natural-dialogue-repair.md",
            "scripts/dialogue_roundtrip.py",
            "references/dialogue-local-workbench.md",
            "references/reference-comedy.md",
            "references/previs-experiments.md",
            "references/story-character-roundtrip.md",
            "references/world-grounding.md",
            "assets/templates/story-workflow.yaml",
            "assets/templates/dialogue-handoff.yaml",
        }
        self.assertTrue(required.issubset(RELEASE_FILES))
        # Copy only the release allowlist, never the user's films or voice models.
        with tempfile.TemporaryDirectory(prefix="role2reel-contract-") as directory:
            clone = Path(directory) / "role2reel"
            for relative in RELEASE_FILES:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            self.assertEqual(validate(clone), [])

    def test_templates_do_not_preclaim_execution_or_acceptance(self):
        handoff = yaml.safe_load(
            (ROOT / "assets/templates/dialogue-handoff.yaml").read_text(encoding="utf-8")
        )
        workflow = yaml.safe_load(
            (ROOT / "assets/templates/story-workflow.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(handoff["adapter"]["execution_status"], "not_run")
        self.assertFalse(handoff["reintegration"]["source_rechecked"])
        self.assertEqual(handoff["review"]["human_decision"], "pending")
        self.assertIsNone(handoff["review"]["decision_source"])
        self.assertEqual(workflow["review"]["human_review"], "pending")
        self.assertIsNone(workflow["review"]["approved_revision"])


if __name__ == "__main__":
    unittest.main()
