from __future__ import annotations

import unittest

from scripts.audit_clipboard_prompts import audit_text


VALID = """shot1｜
景别与运镜：中景｜固定
拍摄方式：固定机位
画面与动线：人物抬眼，停住
【00:01-00:01.5】:（固定机位）（抬眼）
【00:01.5-00:03】:（固定机位）（停住，视线落向门外）

shot2｜
景别与运镜：近景｜缓慢推进
拍摄方式：三脚架固定后期裁切
画面与动线：手指松开道具，声音先于切换进入
【00:01-00:02】:（近景）（手指松开）
【00:02-00:04】:（缓慢推进）（道具落下，人物不说话）
"""


class ClipboardPromptAuditTests(unittest.TestCase):
    def test_valid_blocks(self) -> None:
        self.assertEqual(audit_text(VALID), [])

    def test_gap_and_overlap_are_errors(self) -> None:
        gap = VALID.replace("【00:01.5-00:03】", "【00:01.6-00:03】")
        self.assertIn("timeline-gap", {item.code for item in audit_text(gap)})
        overlap = VALID.replace("【00:01.5-00:03】", "【00:01.4-00:03】")
        self.assertIn("timeline-overlap", {item.code for item in audit_text(overlap)})

    def test_missing_field_and_wrong_origin(self) -> None:
        broken = VALID.replace("拍摄方式：固定机位\n", "").replace("【00:01-00:01.5】", "【00:00-00:01.5】")
        codes = {item.code for item in audit_text(broken)}
        self.assertIn("missing-field", codes)
        self.assertIn("wrong-time-origin", codes)

    def test_duplicate_label_and_duration(self) -> None:
        duplicate = VALID.replace("shot2｜", "shot1｜")
        codes = {item.code for item in audit_text(duplicate)}
        self.assertIn("duplicate-shot-label", codes)
        self.assertIn("shot-order", codes)
        self.assertIn("duration-mismatch", {item.code for item in audit_text(VALID, expected_duration=4.5)})

    def test_segment_export_can_restart_local_labels_when_declared(self) -> None:
        restarted = VALID.replace("shot2｜", "shot1｜")
        self.assertIn("duplicate-shot-label", {item.code for item in audit_text(restarted)})
        self.assertEqual(audit_text(restarted, allow_restarts=True), [])
