import json
from pathlib import Path
import tempfile
import unittest

from scripts.episode_eval import prepare, seal, review


class EpisodeEvalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="episode-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "one.md").write_text("第一集：门关上了。", encoding="utf-8")
        (self.root / "two.md").write_text("保密答案：门后是仓库。", encoding="utf-8")
        self.spec = {"schema_version": 1, "case_id": "unit-only", "task_type": "next_episode",
                     "split": "development", "target_episode": 2, "skill_revision": "unit-v1",
                     "diagnostic_focus": "causality", "max_revision_rounds": 2,
                     "inputs": [{"path": "one.md", "revision": "1", "episode": 1,
                                 "kind": "script", "spoiler_reviewed": True}],
                     "reference": {"path": "two.md", "revision": "1"}}
        self.manifest = self.root / "manifest.json"
        self.run = self.root / "run"

    def prep(self):
        self.manifest.write_text(json.dumps(self.spec), encoding="utf-8")
        return prepare(self.manifest, self.run)

    def freeze(self):
        candidate = self.root / "draft.md"
        candidate.write_text("候选：他敲了敲门。", encoding="utf-8")
        seal(self.run, candidate, "synthetic-unit-fixture", "no model called")

    def test_packet_does_not_disclose_reference(self):
        packet = self.prep().read_text(encoding="utf-8")
        self.assertIn("第一集", packet)
        self.assertNotIn("保密答案", packet)
        self.assertNotIn("two.md", packet)

    def test_roundtrip_keeps_review_pending(self):
        self.prep()
        self.freeze()
        result = review(self.run).read_text(encoding="utf-8")
        self.assertIn("Human review: pending", result)
        self.assertIn("保密答案", result)
        self.assertIn("候选", result)

    def test_future_input_rejected(self):
        self.spec["inputs"][0]["episode"] = 2
        with self.assertRaises(ValueError):
            self.prep()
        self.assertFalse(self.run.exists())

    def test_reference_as_input_rejected(self):
        self.spec["inputs"][0]["path"] = "two.md"
        with self.assertRaises(ValueError):
            self.prep()

    def test_unreviewed_input_rejected(self):
        self.spec["inputs"][0]["spoiler_reviewed"] = False
        with self.assertRaises(ValueError):
            self.prep()

    def test_changed_reference_rejected(self):
        self.prep()
        (self.root / "two.md").write_text("修改了答案", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.freeze()

    def test_changed_candidate_rejected(self):
        self.prep()
        self.freeze()
        (self.run / "candidate.md").write_text("偷偷改了", encoding="utf-8")
        with self.assertRaises(ValueError):
            review(self.run)

    def test_changed_packet_rejected(self):
        self.prep()
        (self.run / "generation-input.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.freeze()

    def test_existing_run_not_overwritten(self):
        packet = self.prep()
        old = packet.read_bytes()
        with self.assertRaises(FileExistsError):
            prepare(self.manifest, self.run)
        self.assertEqual(packet.read_bytes(), old)

    def test_review_requires_sealed_candidate(self):
        self.prep()
        with self.assertRaises(FileNotFoundError):
            review(self.run)

    def test_outline_mode_requires_target_outline(self):
        self.spec["task_type"] = "outline_to_script"
        with self.assertRaises(ValueError):
            self.prep()

    def test_source_path_cannot_escape_project(self):
        with tempfile.TemporaryDirectory(prefix="episode-outside-") as other:
            external = Path(other) / "data.md"
            external.write_text("外部内容", encoding="utf-8")
            self.spec["inputs"][0]["path"] = str(external)
            with self.assertRaises(ValueError):
                self.prep()


if __name__ == "__main__":
    unittest.main()
