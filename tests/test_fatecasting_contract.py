from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FatecastingContractTests(unittest.TestCase):
    def test_life_paths_separates_exploration_from_production_lock(self) -> None:
        text = (ROOT / "references" / "life-paths.md").read_text(encoding="utf-8")
        self.assertIn("`explore`", text)
        self.assertIn("`production-lock`", text)
        self.assertIn("[fatecasting.md](fatecasting.md)", text)
        self.assertIn("life-path-reading.md", text)

    def test_reading_template_leads_with_lives_before_audit_appendix(self) -> None:
        text = (ROOT / "assets" / "templates" / "life-path-reading.md").read_text(
            encoding="utf-8"
        )
        reading_positions = [text.index(f"## Reading {number}") for number in range(1, 4)]
        appendix_position = text.index("## Production-lock appendix")
        self.assertLess(max(reading_positions), appendix_position)
        self.assertIn("## Reading 3 — counter-reading", text)
        self.assertIn("## Author decision menu", text)
        for operation in ("select", "edit", "splice", "reject", "regenerate", "keep"):
            self.assertRegex(text.casefold(), rf"\b{operation}\w*\b")

    def test_method_requires_causal_divergence_and_author_control(self) -> None:
        text = (ROOT / "references" / "fatecasting.md").read_text(encoding="utf-8")
        required_phrases = (
            "at least three readings",
            "Require a counter-reading",
            "Ordinary years",
            "Mixed causality",
            "Hidden bill",
            "Self-story gap",
            "Opening first impulse",
            "no probability",
            "do not infer a private or sensitive past",
        )
        for phrase in required_phrases:
            self.assertIn(phrase.casefold(), text.casefold())

        numbered_steps = re.findall(r"^\d+\. \*\*", text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(numbered_steps), 8)


if __name__ == "__main__":
    unittest.main()
