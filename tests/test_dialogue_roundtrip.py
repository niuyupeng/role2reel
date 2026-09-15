import json
import tempfile
import unittest
from pathlib import Path

from scripts.dialogue_roundtrip import digest, merge, prepare, turns


class DialogueRoundtripTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.fountain"
        self.raw = "Title: 测试\r\n\r\n@工程师\r\n门没有开。\r\n\r\n他看着门。\r\n\r\n@呆呆鸟\r\n别丢下我。\r\n"
        self.source.write_bytes(self.raw.encode())
        self.packet = self.root / "packet.json"
        prepare(self.source, self.packet, ["turn-001"])
        self.candidate = self.root / "candidate.json"
        self.output = self.root / "result.fountain"
        self.data = {"schema_version": 1, "packet_sha256": digest(self.packet.read_bytes()),
                     "edits": [{"id": "turn-001", "speaker": "工程师", "text": "门还没开。"}]}

    def run_merge(self):
        self.candidate.write_text(json.dumps(self.data), encoding="utf-8")
        return merge(self.source, self.packet, self.candidate, self.output)

    def test_exact_spans_preserve_everything_else_and_crlf(self):
        result = self.run_merge()
        self.assertEqual(self.output.read_bytes(), self.raw.replace("门没有开。", "门还没开。").encode())
        self.assertEqual(self.source.read_bytes(), self.raw.encode())
        self.assertEqual(result["review"]["author_acceptance"], "pending")

    def test_stale_source_rejected(self):
        self.source.write_bytes((self.raw + "新动作").encode())
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.run_merge()

    def test_speaker_change_rejected(self):
        self.data["edits"][0]["speaker"] = "呆呆鸟"
        with self.assertRaisesRegex(ValueError, "Speaker"):
            self.run_merge()

    def test_non_target_turn_rejected(self):
        self.data["edits"][0].update(id="turn-002", speaker="呆呆鸟")
        with self.assertRaisesRegex(ValueError, "scope"):
            self.run_merge()

    def test_duplicate_rejected(self):
        self.data["edits"] *= 2
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.run_merge()

    def test_packet_tampering_rejected(self):
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        packet["turns"][0]["start"] += 1
        self.packet.write_text(json.dumps(packet), encoding="utf-8")
        self.data["packet_sha256"] = digest(self.packet.read_bytes())
        with self.assertRaisesRegex(ValueError, "span"):
            self.run_merge()

    def test_changed_packet_hash_rejected(self):
        self.data["packet_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "packet"):
            self.run_merge()

    def test_structural_injection_rejected(self):
        for value in ("好。\n\n@另一个人\n走吧", "[[新场景]]", "", "@另一个人"):
            with self.subTest(value=value):
                self.data["edits"][0]["text"] = value
                with self.assertRaises(ValueError):
                    self.run_merge()

    def test_existing_output_preserved(self):
        self.output.write_bytes(b"keep")
        with self.assertRaisesRegex(ValueError, "new files"):
            self.run_merge()
        self.assertEqual(self.output.read_bytes(), b"keep")

    def test_prepare_refuses_missing_scope_and_overwrite(self):
        with self.assertRaises(ValueError):
            prepare(self.source, self.root / "bad.json", ["turn-999"])
        with self.assertRaises(FileExistsError):
            prepare(self.source, self.packet, ["turn-001"])

    def test_ambiguous_parenthetical_rejected(self):
        with self.assertRaises(ValueError):
            turns("@角色\n(低声)\n台词")


if __name__ == "__main__":
    unittest.main()
