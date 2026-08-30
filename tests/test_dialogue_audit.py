from __future__ import annotations

import unittest

from scripts.audit_dialogue import audit_text, likely_dialogue_lines


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


if __name__ == "__main__":
    unittest.main()
