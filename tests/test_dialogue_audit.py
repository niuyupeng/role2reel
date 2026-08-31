from __future__ import annotations

import unittest
from pathlib import Path

from scripts.audit_dialogue import audit_text, likely_dialogue_lines


ROOT = Path(__file__).resolve().parents[1]


class FountainDialogueParsingTests(unittest.TestCase):
    def test_forced_and_dual_dialogue_cues_are_recognized(self) -> None:
        text = """@Lin Xia
众所周知，这不是普通动作。

MOTHER (V.O.) ^
总而言之，我们得谈谈。
"""

        self.assertEqual(
            likely_dialogue_lines(text),
            [(2, "众所周知，这不是普通动作。"), (5, "总而言之，我们得谈谈。")],
        )
        self.assertEqual(
            {finding.code for finding in audit_text(text)},
            {"as-you-know", "generic-summary"},
        )

    def test_scene_heading_forms_do_not_open_dialogue_blocks(self) -> None:
        headings = [
            "INT. 会议室 - 日",
            "EXT 河岸 - 夜",
            "EST. 城市天际线 - 黎明",
            "I-E. 行驶中的车 - 日",
            "I/E. 行驶中的车 - 日",
            "INT-EXT. 门廊 - 夜",
            "INT/EXT. 门廊 - 夜",
            "INT./EXT. 门廊 - 夜",
            ".屋顶 - 夜",
        ]

        for heading in headings:
            with self.subTest(heading=heading):
                text = f"{heading}\n总而言之，这是一行动作，不是对白。\n"
                self.assertEqual(likely_dialogue_lines(text), [])
                self.assertEqual(audit_text(text), [])

    def test_private_state_labels_and_backstory_recitals_are_review_warnings(self) -> None:
        text = """角色甲
我的判断是他在试探我，所以我的立场是先拒绝。

角色乙
我之所以从来不求你，是因为当年那件事，所以我才变成现在这样。
"""

        self.assertEqual(
            {finding.code for finding in audit_text(text)},
            {"private-analysis-spill", "backstory-recital"},
        )


class SceneGuidanceContractTests(unittest.TestCase):
    def test_line_cap_is_a_ceiling_and_mute_pass_deletes_redundant_speech(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        scene_guidance = (ROOT / "references" / "scene-dialogue.md").read_text(encoding="utf-8")

        self.assertIn("A line cap is a ceiling, never a quota", skill)
        self.assertIn("Run a **mute pass**", scene_guidance)
        self.assertIn("same state change and next choice remain legible, delete it", skill)
        self.assertIn("evaluation_scope: light behavior fixture; not deep-biography evidence", skill)


if __name__ == "__main__":
    unittest.main()
