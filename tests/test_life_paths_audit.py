from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.audit_life_paths import (
    HAN_PATTERN,
    audit_file,
    audit_shared_event_registry,
    biography_body_sha256,
    biography_stats,
    candidate_sha256,
    fact_boundary_sha256,
    file_sha256,
    shared_event_sha256,
)


# Synthetic fixture size, not a production depth requirement.
FIXTURE_BIOGRAPHY_HAN_COUNT = 30_000

VARIANTS = {
    "a": (
        "长期面对口头承诺反复变动的环境",
        "把含糊承诺理解为尚未形成可靠义务",
        "先核对条件再作公开承诺",
        "被亲近者误解为缺少热情",
        "核对避免了连带损失，也拉开了关系距离",
        "提高承诺阈值，同时保留私下补救渠道",
        "对含糊承诺警觉，又担心自己显得冷漠",
    ),
    "b": (
        "一次迟疑使本可及时回应的求助失去窗口",
        "把含糊表达理解为对方难以直接开口",
        "先承担一小步，再追问真实需要",
        "先付出时间并承担被利用的风险",
        "主动靠近修复了关系，也制造了新的义务",
        "优先确认人的处境，再协商责任边界",
        "担心谨慎再次变成袖手旁观",
    ),
    "c": (
        "公开表扬数次被用来交换额外服从",
        "把公开请求理解为可能包含体面压力",
        "把谈判移到私下并拒绝当场表态",
        "失去即时赞许并被视为不合群",
        "私下协商保住自主权，却留下权力冲突",
        "遇到公开赞许时先检查隐藏义务和退出成本",
        "渴望被认可，又对被塑造成榜样感到不安",
    ),
}


def claim(claim_id: str, content: str) -> dict:
    return {"id": claim_id, "content": content, "source_refs": [f"fixture:{claim_id}"]}


def fact_boundary() -> dict:
    return {
        "author_locked_facts": [claim("fact-1", "已确认的当前事实")],
        "observable_traces": [claim("trace-1", "材料中可直接观察的痕迹")],
        "self_reports_and_testimony": [claim("testimony-1", "带有说话者归属的证言")],
        "rumors_misunderstandings_and_disputes": [claim("dispute-1", "尚未解决的争议说法")],
        "author_preferences": [claim("preference-1", "作者倾向保留普通生活质感")],
        "permitted_changes": [claim("change-1", "允许创作开场前经历")],
        "unknowns": [claim("unknown-1", "关键时期仍未知")],
        "conflicts": [claim("conflict-1", "两份证言不能同时按字面成立")],
    }


def causal_node(variant: str, node_id: str = "node-1") -> dict:
    event, interpretation, choice, cost, feedback, update, residue = VARIANTS[variant]
    return {
        "id": node_id,
        "period": f"人生阶段-{variant}",
        "environment_and_relationships": ["持续现实限制", f"关键关系-{variant}"],
        "event_or_pattern": event,
        "known_then": "当时只能确认局部事实，无法知道后续反馈",
        "constraints_and_options": ["可以回应或延迟", "资源与关系义务排除了一些理想选项"],
        "interpretation": interpretation,
        "choice": choice,
        "cost": cost,
        "feedback": feedback,
        "belief_or_strategy_update": update,
        "unresolved_residue": residue,
        "present_triggers": [f"当前触发-{variant}"],
    }


def candidate(candidate_id: str, status: str, variant: str) -> dict:
    return {
        "id": candidate_id,
        "status": status,
        "derived_from": [],
        "premise": f"候选{variant}通过不同关系学习与反馈到达当前",
        "causal_spine": [causal_node(variant)],
        "feasibility": {
            "supports": ["fact-1", "trace-1"],
            "conflicts": ["conflict-1"],
            "unknowns": ["unknown-1"],
            "real_world_feasibility": "没有违反已知时间与现实约束",
        },
        "creative_consequences": {
            "theme": [f"主题后果-{variant}"],
            "character_arc": [f"人物弧后果-{variant}"],
            "relationships": [f"关系策略后果-{variant}"],
            "present_response": [f"当前反应后果-{variant}"],
        },
    }


def author_decision(text: str = "作者明确锁定候选 A", **bindings) -> dict:
    return {"actor": "author", "source_ref": "user-turn:test-fixture", "decision_text": text, **bindings}


def locked_manifest(character_id: str = "character-1") -> dict:
    boundary = fact_boundary()
    candidates = [
        candidate("path-a", "locked", "a"),
        candidate("path-b", "rejected", "b"),
        candidate("path-c", "rejected", "c"),
    ]
    locked_hash = candidate_sha256(candidates[0])
    boundary_hash = fact_boundary_sha256(boundary)
    package_context_id = f"package-{character_id}"
    return {
        "schema_version": 1,
        "character_id": character_id,
        "package_context_id": package_context_id,
        "fact_boundary": boundary,
        "candidates": candidates,
        "selection": {
            "state": "locked",
            "selected_branch_id": "path-a",
            "rejected_branch_ids": ["path-b", "path-c"],
            "author_lock": True,
            "lock_revision": 1,
            "locked_fact_boundary_sha256": boundary_hash,
            "locked_candidate_sha256": locked_hash,
            "author_decision": author_decision(
                approved_character_id=character_id,
                approved_package_context_id=package_context_id,
                approved_branch_id="path-a",
                approved_fact_boundary_sha256=boundary_hash,
                approved_candidate_sha256=locked_hash,
                approved_lock_revision=1,
            ),
            "unlock_history": [],
        },
        "deep_biography": {
            "mode": "deep",
            "status": "ready",
            "tier_author_decision": None,
            "biography_revision": 1,
            "author_approval": {
                "state": "pending",
                "approved_character_id": None,
                "approved_package_context_id": None,
                "approved_branch_id": None,
                "approved_fact_boundary_sha256": None,
                "approved_candidate_sha256": None,
                "approved_path_lock_revision": None,
                "approved_biography_revision": None,
                "approved_body_sha256": None,
                "decision": {"actor": None, "source_ref": None, "decision_text": None},
            },
            "biography_file": "biography.md",
            "coverage_stages": [
                {
                    "stage_id": "stage-1",
                    "period": "一个主要人生阶段",
                    "source_node_refs": ["life-path:path-a/node-1"],
                    "environment_and_relationships": ["环境条件", "关系条件"],
                    "interpretation_and_choices": ["形成解释", "作出选择"],
                    "cost_feedback_updates": ["承担代价", "接收反馈", "更新策略"],
                    "current_residues": ["留下可被当前线索触发的残余"],
                }
            ],
            "shared_history_refs": [],
            "shared_event_ids": [],
            "relationship_ledger_file": None,
        },
        "compiled_runtime": {
            "compiled_for_character_id": None,
            "compiled_for_package_context_id": None,
            "compiled_from_lock_revision": None,
            "compiled_from_fact_boundary_sha256": None,
            "compiled_from_candidate_sha256": None,
            "compiled_from_biography_revision": None,
            "compiled_from_biography_sha256": None,
            "source_refs": [],
            "artifact_files": [],
            "formal_scene_compilation": False,
        },
        "outline_review": {
            "input_outline_ref": None,
            "input_outline_file": None,
            "input_outline_sha256": None,
            "input_outline_version": None,
            "reviewed_against_lock_revision": None,
            "reviewed_against_fact_boundary_sha256": None,
            "reviewed_against_candidate_sha256": None,
            "status": "not_started",
            "conflicts": [],
        },
    }


def open_manifest() -> dict:
    payload = locked_manifest()
    for item in payload["candidates"]:
        item["status"] = "candidate"
    payload["selection"] = {
        "state": "open",
        "selected_branch_id": None,
        "rejected_branch_ids": [],
        "author_lock": False,
        "lock_revision": 0,
        "locked_fact_boundary_sha256": None,
        "locked_candidate_sha256": None,
        "author_decision": {
            "actor": None,
            "source_ref": None,
            "decision_text": None,
            "approved_character_id": None,
            "approved_package_context_id": None,
            "approved_branch_id": None,
            "approved_fact_boundary_sha256": None,
            "approved_candidate_sha256": None,
            "approved_lock_revision": None,
        },
        "unlock_history": [],
    }
    payload["deep_biography"].update(
        {
            "mode": "unclassified",
            "status": "not_started",
            "biography_revision": 0,
            "biography_file": None,
            "coverage_stages": [],
            "shared_history_refs": [],
            "shared_event_ids": [],
            "relationship_ledger_file": None,
        }
    )
    return payload


CONTEXTS = [
    "家庭收入忽然收紧而照料责任增加",
    "新环境的规则与过去习惯发生冲突",
    "长期日常劳动开始换来有限自主权",
    "一次迁居切断熟悉支持又带来新机会",
    "身体状态改变了可以承担的工作节奏",
    "公共制度的变化重新分配资源与风险",
    "平静生活中积累的小债终于需要处理",
]
RELATIONS = [
    "一位亲近者以沉默保护人物也限制人物",
    "同伴愿意帮忙却要求对等公开承担",
    "长辈把关心表达成对选择的强硬介入",
    "旧友提供机会同时留下难以偿还的人情",
    "竞争者在关键时刻表现出意外的体谅",
    "伴侣支持行动但拒绝继续替人物解释",
    "陌生合作者用明确边界建立了短暂信任",
]
APPRAISALS = [
    "人物当时只知道局部原因于是把风险理解为承诺失控",
    "人物误把对方的迟疑看成拒绝后来才发现是羞耻",
    "人物先注意现实损失没有看见关系正在悄悄改写",
    "人物把帮助理解为债务因而忽略了对方主动选择",
    "人物以为保持沉默能够保护体面却让误解继续生长",
    "人物把公开赞许理解成认可随后发现其中附带义务",
    "人物承认自己无法判断因而选择保留两个竞争解释",
]
CHOICES = [
    "人物先做可撤回的小行动并延迟不可逆承诺",
    "人物承担眼前损失换取私下核实事实的时间",
    "人物拒绝替别人决定转而要求对方明确选择",
    "人物暂时接受安排但保留以后重新谈判的条件",
    "人物公开承认局部责任同时隐藏尚未核实的部分",
    "人物离开熟悉位置以阻止关系继续沿旧模式运行",
    "人物请求第三方见证避免争执只剩彼此指控",
]
UPDATES = [
    "反馈证明谨慎有用却也造成距离于是策略增加主动修复",
    "短期成功掩盖长期代价人物后来降低对赞许的依赖",
    "关系受损后仍得到一次诚实回应人物开始允许有限信任",
    "选择失败没有摧毁能力反而让人物区分失败与羞辱",
    "他人的托举改变结果人物不再把全部成败归给意志",
    "现实惩罚了逃避也保留回头机会人物形成分阶段承担",
    "旧策略在新关系中失效人物学会先确认对方如何理解",
]


def varied_body(han_count: int) -> str:
    paragraphs: list[str] = []
    remaining = han_count
    index = 0
    while remaining:
        source = (
            chr(0x4E00 + index)
            + CONTEXTS[index % len(CONTEXTS)]
            + RELATIONS[(index // 2) % len(RELATIONS)]
            + APPRAISALS[(index // 3) % len(APPRAISALS)]
            + CHOICES[(index // 5) % len(CHOICES)]
            + UPDATES[(index // 7) % len(UPDATES)]
            + "这段经历留下尚未解决的矛盾并在故事开场前被具体线索重新触发"
        )
        paragraph = "".join(HAN_PATTERN.findall(source))
        paragraph = paragraph[:remaining]
        paragraphs.append(paragraph)
        remaining -= len(paragraph)
        index += 1
    body = "\n\n".join(paragraphs)
    assert biography_stats(body).total_han == han_count
    return body


def biography_document(payload: dict, body: str, **overrides) -> str:
    biography = payload["deep_biography"]
    metadata = {
        "schema_version": 1,
        "character_id": payload["character_id"],
        "package_context_id": payload["package_context_id"],
        "life_path_branch_id": payload["selection"]["selected_branch_id"],
        "life_path_lock_revision": payload["selection"]["lock_revision"],
        "fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
        "locked_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
        "biography_revision": biography["biography_revision"],
        "biography_status": biography["status"],
    }
    metadata.update(overrides)
    lines = ["---"]
    lines.extend(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    lines.extend(["---", "", body])
    return "\n".join(lines)


def write_biography(root: Path, payload: dict, body: str, *, filename: str = "biography.md", **overrides) -> str:
    document = biography_document(payload, body, **overrides)
    (root / filename).write_text(document, encoding="utf-8")
    return biography_body_sha256(document)


def approve_biography(payload: dict, digest: str) -> None:
    payload["deep_biography"]["author_approval"] = {
        "state": "approved",
        "approved_character_id": payload["character_id"],
        "approved_package_context_id": payload["package_context_id"],
        "approved_branch_id": payload["selection"]["selected_branch_id"],
        "approved_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
        "approved_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
        "approved_path_lock_revision": payload["selection"]["lock_revision"],
        "approved_biography_revision": payload["deep_biography"]["biography_revision"],
        "approved_body_sha256": digest,
        "decision": author_decision("作者批准该版本长篇人物小传进入运行资产"),
    }


def write_and_approve(root: Path, payload: dict, body: str, **overrides) -> str:
    digest = write_biography(root, payload, body, **overrides)
    approve_biography(payload, digest)
    return digest


def enable_compilation(root: Path, payload: dict, digest: str, files: dict[str, str] | None = None) -> None:
    files = files or {"runtime-artifact.yaml": "source_refs: [life-path:path-a/node-1]\n"}
    records = []
    source_refs = set()
    artifact_types = {
        "character.yaml": "character",
        "cognitive-resources.yaml": "cognitive_resources",
        "speech-corpus.yaml": "speech_corpus",
        "memories.yaml": "memories",
        "relationship-ledger.yaml": "relationship_ledger",
        "scene-contract.yaml": "scene_contract",
        "turn-state.yaml": "turn_state",
        "beat-map.yaml": "beat_map",
        "storyboard.yaml": "storyboard",
        "continuity.yaml": "continuity",
        "visual-bible.yaml": "visual_bible",
        "asset-contract.yaml": "asset_contract",
        "video-task.yaml": "video_task",
        "main.fountain": "screenplay",
    }
    for name, content in files.items():
        artifact_type = artifact_types.get(Path(name).name, "other_structured")
        if artifact_type in {"character", "cognitive_resources", "speech_corpus", "memories"} and "compiled_provenance" not in content:
            identity_header = (
                "compiled_provenance:\n"
                f"  compiled_for_character_id: {payload['character_id']}\n"
                f"  compiled_for_package_context_id: {payload['package_context_id']}\n"
            )
            content = identity_header + content
        if artifact_type == "character" and re.search(r"(?m)^character:\s*", content) is None and '"character"' not in content:
            content += f"character:\n  id: {payload['character_id']}\n"
        elif (
            artifact_type in {"cognitive_resources", "speech_corpus", "memories"}
            and re.search(r"(?m)^character_id:\s*", content) is None
            and '"character_id"' not in content
        ):
            content += f"character_id: {payload['character_id']}\n"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        refs = sorted({f"life-path:{branch}/{node}" for branch, node in re.findall(r"life-path:([\w.-]+)/([\w.-]+)", content)})
        source_refs.update(refs)
        records.append(
            {
                "path": name,
                "artifact_type": artifact_type,
                "sha256": file_sha256(path),
                "source_refs": refs,
                "compiled_for_character_id": payload["character_id"],
                "compiled_for_package_context_id": payload["package_context_id"],
                "compiled_from_lock_revision": payload["selection"]["lock_revision"],
                "compiled_from_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
                "compiled_from_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
                "compiled_from_biography_revision": payload["deep_biography"]["biography_revision"],
                "compiled_from_biography_sha256": digest,
            }
        )
    payload["compiled_runtime"] = {
        "compiled_for_character_id": payload["character_id"],
        "compiled_for_package_context_id": payload["package_context_id"],
        "compiled_from_lock_revision": payload["selection"]["lock_revision"],
        "compiled_from_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
        "compiled_from_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
        "compiled_from_biography_revision": payload["deep_biography"]["biography_revision"],
        "compiled_from_biography_sha256": digest,
        "source_refs": sorted(source_refs),
        "artifact_files": records,
        "formal_scene_compilation": False,
    }


def set_outline_review(
    root: Path,
    payload: dict,
    *,
    status: str = "clear",
    conflicts: list[dict] | None = None,
    content: str = "故事大纲版本一：人物在当前压力下作出可追溯的选择。\n",
) -> Path:
    outline_path = root / "outline.md"
    outline_path.write_text(content, encoding="utf-8")
    payload["outline_review"] = {
        "input_outline_ref": "outline:v1",
        "input_outline_file": "outline.md",
        "input_outline_sha256": file_sha256(outline_path),
        "input_outline_version": "v1",
        "reviewed_against_lock_revision": payload["selection"]["lock_revision"],
        "reviewed_against_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
        "reviewed_against_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
        "status": status,
        "conflicts": conflicts or [],
    }
    return outline_path


def character_artifact_document(payload: dict, digest: str, *, character_id: str | None = None, package_context_id: str | None = None) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "compiled_provenance": {
                "compiled_for_character_id": character_id or payload["character_id"],
                "compiled_for_package_context_id": package_context_id or payload["package_context_id"],
                "life_path_branch_id": payload["selection"]["selected_branch_id"],
                "compiled_from_lock_revision": payload["selection"]["lock_revision"],
                "compiled_from_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
                "compiled_from_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
                "compiled_from_biography_revision": payload["deep_biography"]["biography_revision"],
                "compiled_from_biography_sha256": digest,
                "source_refs": ["life-path:path-a/node-1"],
            },
            "character": {"id": character_id or payload["character_id"]},
        },
        ensure_ascii=False,
        indent=2,
    )


def scene_artifact_document(payload: dict, digest: str) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "character_sources": [
                {
                    "character_id": payload["character_id"],
                    "package_context_id": payload["package_context_id"],
                    "life_path_branch_id": payload["selection"]["selected_branch_id"],
                    "compiled_from_lock_revision": payload["selection"]["lock_revision"],
                    "compiled_from_fact_boundary_sha256": payload["selection"]["locked_fact_boundary_sha256"],
                    "compiled_from_candidate_sha256": payload["selection"]["locked_candidate_sha256"],
                    "compiled_from_biography_revision": payload["deep_biography"]["biography_revision"],
                    "compiled_from_biography_sha256": digest,
                    "source_refs": ["life-path:path-a/node-1"],
                },
                {
                    "character_id": "another-character",
                    "package_context_id": "package-another-character",
                    "source_refs": ["life-path:other-branch/other-node"],
                },
            ],
            "scene": {"id": "scene-1"},
        },
        ensure_ascii=False,
        indent=2,
    )


def write_manifest(root: Path, payload: dict) -> Path:
    path = root / "life-path-workbench.yaml"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def codes(findings) -> set[str]:
    return {item.code for item in findings if item.severity == "error"}


class LifePathAuditTests(unittest.TestCase):
    def ready_fixture(self, root: Path, payload: dict | None = None, count: int = FIXTURE_BIOGRAPHY_HAN_COUNT) -> tuple[dict, Path, str]:
        payload = payload or locked_manifest()
        digest = write_and_approve(root, payload, varied_body(count))
        return payload, write_manifest(root, payload), digest

    def test_mechanically_valid_locked_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload, manifest, _ = self.ready_fixture(Path(directory))
            self.assertEqual(audit_file(manifest, require_locked=True), [])
            self.assertEqual(len(payload["candidates"]), 3)

    def test_no_default_length_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, _ = self.ready_fixture(root, count=2_000)
            self.assertEqual(codes(audit_file(manifest, require_locked=True)), set())
            payload["deep_biography"]["minimum_chinese_characters"] = None
            self.assertEqual(codes(audit_file(write_manifest(root, payload), require_locked=True)), set())

    def test_explicit_length_gate_is_honored_without_universal_floor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["deep_biography"]["minimum_chinese_characters"] = 2_000
            write_and_approve(root, payload, varied_body(1_999))
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("biography-too-short", found)
            write_and_approve(root, payload, varied_body(2_000))
            self.assertEqual(codes(audit_file(write_manifest(root, payload), require_locked=True)), set())

    def test_invalid_explicit_length_gate(self) -> None:
        for value in (0, -1, True, "2000", 2.5):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload, _, _ = self.ready_fixture(root, count=2_000)
                payload["deep_biography"]["minimum_chinese_characters"] = value
                self.assertIn("invalid-biography-threshold", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_no_length_gate_does_not_waive_coverage_or_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, _, _ = self.ready_fixture(root, count=2_000)
            payload["deep_biography"]["coverage_stages"] = []
            payload["deep_biography"]["author_approval"]["state"] = "pending"
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("missing-biography-coverage", found)
            self.assertIn("biography-author-approval-required", found)

    def test_empty_body_is_not_a_completed_biography(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(root, payload, "")
            self.assertIn("empty-biography-body", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_obvious_single_character_padding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(root, payload, "文" * FIXTURE_BIOGRAPHY_HAN_COUNT)
            self.assertIn("repeated-biography-padding", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_repeated_short_paragraph_padding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(root, payload, "\n\n".join(["文" * 79] * 400))
            self.assertIn("repeated-biography-padding", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_open_workbench_does_not_force_life_path_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = write_manifest(Path(directory), open_manifest())
            self.assertEqual(codes(audit_file(manifest)), set())
            self.assertIn("lock-required", codes(audit_file(manifest, require_locked=True)))

    def test_selected_gate_requires_all_fact_boundary_categories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            del payload["fact_boundary"]["observable_traces"]
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("missing-fact-boundary-category", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_candidate_feasibility_must_reference_claim_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["candidates"][0]["feasibility"]["supports"] = ["not-a-claim"]
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("unknown-fact-boundary-reference", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_empty_conflicts_and_unknowns_are_explicitly_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            for item in payload["candidates"]:
                item["feasibility"]["conflicts"] = []
                item["feasibility"]["unknowns"] = []
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertNotIn("missing-field", found)

    def test_author_decision_boolean_is_not_a_lock_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["selection"]["author_decision"] = True
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("missing-author-decision", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_author_path_decision_cannot_be_replayed_for_another_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["selection"]["author_decision"]["approved_branch_id"] = "path-b"
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("author-decision-binding-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_author_path_decision_cannot_be_replayed_for_another_character_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = locked_manifest("character-a")
            payload = locked_manifest("character-b")
            payload["selection"] = copy.deepcopy(source["selection"])
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("author-decision-binding-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_author_path_decision_binds_exact_package_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["selection"]["author_decision"]["approved_package_context_id"] = "another-package-context"
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("author-decision-binding-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_fact_boundary_change_invalidates_path_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["fact_boundary"]["author_locked_facts"][0]["content"] = "锁后被替换的另一项当前事实"
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("locked-fact-boundary-hash-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_editing_locked_candidate_without_relock_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["candidates"][0]["causal_spine"][0]["choice"] = "锁后被静默改写的选择"
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("locked-candidate-hash-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_exact_duplicate_spines_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            duplicate = copy.deepcopy(payload["candidates"][1])
            duplicate["id"] = "path-c"
            payload["candidates"][2] = duplicate
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("duplicate-causal-spine", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_composite_does_not_replace_three_root_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["candidates"][2]["derived_from"] = ["path-a", "path-b"]
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("too-few-root-candidates", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_selection_requires_at_least_three_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["candidates"] = payload["candidates"][:2]
            payload["selection"]["rejected_branch_ids"] = ["path-b"]
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("too-few-candidates", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_biography_requires_separate_author_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_biography(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            self.assertIn("biography-author-approval-required", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_biography_approval_cannot_be_replayed_across_path_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, _ = self.ready_fixture(root)
            payload["deep_biography"]["author_approval"]["approved_branch_id"] = "path-b"
            write_manifest(root, payload)
            self.assertIn("biography-approval-binding-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_biography_approval_cannot_be_replayed_for_another_character_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            target_root = root / "target"
            source_root.mkdir()
            target_root.mkdir()
            source = locked_manifest("character-a")
            target = locked_manifest("character-b")
            write_and_approve(source_root, source, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            write_biography(target_root, target, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            target["deep_biography"]["author_approval"] = copy.deepcopy(source["deep_biography"]["author_approval"])
            self.assertIn(
                "biography-approval-binding-mismatch",
                codes(audit_file(write_manifest(target_root, target), require_locked=True)),
            )

    def test_biography_approval_binds_exact_package_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, _ = self.ready_fixture(root)
            payload["deep_biography"]["author_approval"]["approved_package_context_id"] = "another-package-context"
            write_manifest(root, payload)
            self.assertIn("biography-approval-binding-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_changed_biography_invalidates_author_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, _ = self.ready_fixture(root)
            write_biography(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT + 1))
            self.assertIn("biography-approval-hash-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_biography_frontmatter_binds_locked_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT), life_path_branch_id="path-b")
            self.assertIn("biography-branch-mismatch", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_biography_frontmatter_binds_exact_package_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(
                root,
                payload,
                varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT),
                package_context_id="another-package-context",
            )
            self.assertIn(
                "biography-package-context-mismatch",
                codes(audit_file(write_manifest(root, payload), require_locked=True)),
            )

    def test_biography_scans_rejected_branch_refs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            body = "来源life-path:path-b/node-1。" + varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT)
            write_and_approve(root, payload, body)
            self.assertIn("rejected-branch-reference", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_biography_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbench = root / "workbench"
            workbench.mkdir()
            payload = locked_manifest()
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT), filename="outside.md")
            payload["deep_biography"]["biography_file"] = "../outside.md"
            self.assertIn("biography-path-escape", codes(audit_file(write_manifest(workbench, payload), require_locked=True)))

    def test_biography_symlink_fails_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT), filename="target.md")
            try:
                (root / "biography.md").symlink_to(root / "target.md")
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            self.assertIn("biography-symlink", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_runtime_artifact_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            (root / "runtime-artifact.yaml").unlink()
            write_manifest(root, payload)
            self.assertIn("missing-runtime-artifact", codes(audit_file(manifest, require_locked=True)))

    def test_runtime_artifact_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbench = root / "workbench"
            workbench.mkdir()
            payload = locked_manifest()
            digest = write_and_approve(workbench, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            (root / "outside.yaml").write_text("source_refs: [life-path:path-a/node-1]\n", encoding="utf-8")
            enable_compilation(workbench, payload, digest)
            payload["compiled_runtime"]["artifact_files"][0]["path"] = "../outside.yaml"
            self.assertIn("runtime-artifact-path-escape", codes(audit_file(write_manifest(workbench, payload), require_locked=True)))

    def test_runtime_artifact_symlink_fails_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            target = root / "target.yaml"
            target.write_text("source_refs: [life-path:path-a/node-1]\n", encoding="utf-8")
            link = root / "runtime-artifact.yaml"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            enable_compilation(root, payload, digest)
            write_manifest(root, payload)
            self.assertIn("runtime-artifact-symlink", codes(audit_file(manifest, require_locked=True)))

    def test_real_runtime_asset_types_are_scanned_for_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("character.yaml", "cognitive-resources.yaml", "memories.yaml", "relationship-ledger.yaml"):
                with self.subTest(filename=filename):
                    payload = locked_manifest()
                    digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
                    enable_compilation(root, payload, digest, {filename: "source_refs: [life-path:path-b/node-1]\n"})
                    found = codes(audit_file(write_manifest(root, payload), require_locked=True))
                    self.assertIn("rejected-branch-reference", found)

    def test_compiled_relationship_ledger_scans_ordinary_relationship_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            ledger = {
                "schema_version": 1,
                "relationships": [
                    {
                        "from_character": payload["character_id"],
                        "to_character": "another-character",
                        "history_refs": ["life-path:path-b/node-1"],
                    }
                ],
                "shared_event_registry": [],
                "shared_memory_contracts": [],
            }
            enable_compilation(root, payload, digest, {"relationship-ledger.yaml": json.dumps(ledger, ensure_ascii=False)})
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("rejected-branch-reference", found)

    def test_compiled_relationship_ledger_must_match_workbench_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "declared-ledger.yaml"
            empty_ledger = json.dumps(
                {"schema_version": 1, "relationships": [], "shared_event_registry": [], "shared_memory_contracts": []},
                ensure_ascii=False,
            )
            (root / "declared-ledger.yaml").write_text(empty_ledger, encoding="utf-8")
            compiled_ledger = json.dumps(
                {
                    "schema_version": 1,
                    "source_refs": ["life-path:path-a/node-1"],
                    "relationships": [],
                    "shared_event_registry": [],
                    "shared_memory_contracts": [],
                },
                ensure_ascii=False,
            )
            enable_compilation(root, payload, digest, {"relationship-ledger.yaml": compiled_ledger})
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("compiled-relationship-ledger-binding-mismatch", found)

    def test_relationship_ledger_record_matches_claim_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            ledger = json.dumps(
                {
                    "schema_version": 1,
                    "relationships": [{"history_refs": ["life-path:path-a/node-1"]}],
                    "shared_event_registry": [],
                    "shared_memory_contracts": [],
                },
                ensure_ascii=False,
            )
            enable_compilation(root, payload, digest, {"relationship-ledger.yaml": ledger})
            payload["compiled_runtime"]["artifact_files"][0]["source_refs"] = ["life-path:path-b/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-b/node-1"]
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("artifact-source-closure-mismatch", found)

    def test_common_ground_and_second_order_claims_are_provenance_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            ledger = {
                "schema_version": 1,
                "relationships": [],
                "relationship_claim_records": [],
                "common_ground_propositions": [
                    {"id": "cg-1", "source_refs": ["life-path:path-b/node-1"]}
                ],
                "second_order_beliefs": [
                    {"id": "sob-1", "source_refs": ["life-path:path-a/node-1"]}
                ],
                "shared_event_registry": [],
                "shared_memory_contracts": [],
            }
            enable_compilation(
                root,
                payload,
                digest,
                {"relationship-ledger.yaml": json.dumps(ledger, ensure_ascii=False)},
            )
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("rejected-branch-reference", found)

    def test_structured_runtime_artifact_cannot_omit_claim_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest, {"character.yaml": "schema_version: 1\ncharacter: {id: character-1}\n"})
            record = payload["compiled_runtime"]["artifact_files"][0]
            record["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            write_manifest(root, payload)
            self.assertIn("missing-claim-provenance", codes(audit_file(manifest, require_locked=True)))

    def test_speech_corpus_is_a_character_bound_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(
                root,
                payload,
                digest,
                {
                    "speech-corpus.yaml": (
                        "schema_version: 1\n"
                        "source_refs: [life-path:path-a/node-1]\n"
                        "entries: []\n"
                    )
                },
            )
            write_manifest(root, payload)
            self.assertEqual(audit_file(manifest, require_locked=True), [])

    def test_artifact_internal_biography_hash_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            content = "compiled_from_biography_sha256: " + ("0" * 64) + "\nsource_refs: [life-path:path-a/node-1]\n"
            enable_compilation(root, payload, digest, {"character.yaml": content})
            write_manifest(root, payload)
            self.assertIn("compiled-biography-hash-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_artifact_file_change_invalidates_recorded_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            write_manifest(root, payload)
            (root / "runtime-artifact.yaml").write_text("source_refs: [life-path:path-a/node-1]\nchanged: true\n", encoding="utf-8")
            self.assertIn("runtime-artifact-hash-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_runtime_cannot_be_replayed_for_another_character_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            target_root = root / "target"
            source_root.mkdir()
            target_root.mkdir()
            source = locked_manifest("character-a")
            target = locked_manifest("character-b")
            source_digest = write_and_approve(source_root, source, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            target_digest = write_and_approve(target_root, target, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            enable_compilation(source_root, source, source_digest)
            (target_root / "runtime-artifact.yaml").write_text(
                (source_root / "runtime-artifact.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            target["compiled_runtime"] = copy.deepcopy(source["compiled_runtime"])
            target["compiled_runtime"]["compiled_from_biography_sha256"] = target_digest
            target["compiled_runtime"]["artifact_files"][0]["compiled_from_biography_sha256"] = target_digest
            found = codes(audit_file(write_manifest(target_root, target), require_locked=True))
            self.assertIn("compiled-character-mismatch", found)
            self.assertIn("compiled-package-context-mismatch", found)

    def test_runtime_header_binds_exact_character_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            payload["compiled_runtime"]["compiled_for_package_context_id"] = "another-package-context"
            write_manifest(root, payload)
            self.assertIn("compiled-package-context-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_artifact_record_binds_exact_character_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            record = payload["compiled_runtime"]["artifact_files"][0]
            record["compiled_for_character_id"] = "another-character"
            record["compiled_for_package_context_id"] = "another-package-context"
            write_manifest(root, payload)
            found = codes(audit_file(manifest, require_locked=True))
            self.assertIn("artifact-provenance-binding-mismatch", found)
            self.assertIn("compiled-character-mismatch", found)
            self.assertIn("compiled-package-context-mismatch", found)

    def test_per_character_asset_binds_character_and_package_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest("character-b")
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            copied_content = character_artifact_document(
                payload,
                digest,
                character_id="character-a",
                package_context_id="package-character-a",
            )
            enable_compilation(root, payload, digest, {"character.yaml": copied_content})
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("compiled-character-mismatch", found)
            self.assertIn("compiled-package-context-mismatch", found)
            self.assertIn("character-artifact-identity-mismatch", found)

    def test_identity_bound_per_character_asset_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            enable_compilation(root, payload, digest, {"character.yaml": character_artifact_document(payload, digest)})
            self.assertEqual(audit_file(write_manifest(root, payload), require_locked=True), [])

    def test_multi_character_scene_validates_current_source_without_claiming_other_workbenches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            enable_compilation(root, payload, digest, {"scene-contract.yaml": scene_artifact_document(payload, digest)})
            record = payload["compiled_runtime"]["artifact_files"][0]
            record["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["formal_scene_compilation"] = True
            set_outline_review(root, payload)
            self.assertEqual(audit_file(write_manifest(root, payload), require_locked=True), [])

    def test_shared_production_artifacts_scope_each_character_package(self) -> None:
        filenames = (
            "storyboard.yaml",
            "continuity.yaml",
            "visual-bible.yaml",
            "asset-contract.yaml",
            "video-task.yaml",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in filenames:
                with self.subTest(filename=filename):
                    case_root = root / filename.replace(".", "-")
                    case_root.mkdir()
                    payload = locked_manifest("character-a")
                    digest = write_and_approve(case_root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
                    current_source = json.loads(scene_artifact_document(payload, digest))["character_sources"][0]
                    document = {
                        "schema_version": 1,
                        "character_sources": [
                            current_source,
                            {
                                "character_id": "character-b",
                                "package_context_id": "package-character-b",
                                "source_refs": ["life-path:other-path/other-node"],
                            },
                        ],
                    }
                    enable_compilation(case_root, payload, digest, {filename: json.dumps(document, ensure_ascii=False)})
                    record = payload["compiled_runtime"]["artifact_files"][0]
                    record["source_refs"] = ["life-path:path-a/node-1"]
                    payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
                    payload["compiled_runtime"]["formal_scene_compilation"] = True
                    set_outline_review(case_root, payload)
                    self.assertEqual(audit_file(write_manifest(case_root, payload), require_locked=True), [])

    def test_multi_character_nested_claims_are_scoped_and_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest("character-a")
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            current_source = json.loads(scene_artifact_document(payload, digest))["character_sources"][0]
            document = {
                "schema_version": 1,
                "character_sources": [
                    current_source,
                    {
                        "character_id": "character-b",
                        "package_context_id": "package-character-b",
                        "source_refs": ["life-path:other-path/other-node"],
                    },
                ],
                "scene_id": "scene-shared",
                "character_runtime_scopes": [
                    {
                        "character_id": "character-a",
                        "knowledge_boundary": [{"source_refs": ["life-path:path-a/node-1"]}],
                    },
                    {
                        "character_id": "character-b",
                        "knowledge_boundary": [{"source_refs": ["life-path:other-path/other-node"]}],
                    },
                ],
            }
            enable_compilation(root, payload, digest, {"scene-contract.yaml": json.dumps(document, ensure_ascii=False)})
            payload["compiled_runtime"]["artifact_files"][0]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["formal_scene_compilation"] = True
            set_outline_review(root, payload)
            manifest = write_manifest(root, payload)
            self.assertEqual(audit_file(manifest, require_locked=True), [])

            document["character_runtime_scopes"][0]["knowledge_boundary"][0]["source_refs"] = ["life-path:path-b/node-1"]
            scene_path = root / "scene-contract.yaml"
            scene_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            payload["compiled_runtime"]["artifact_files"][0]["sha256"] = file_sha256(scene_path)
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertTrue({"character-source-nested-closure-mismatch", "rejected-branch-reference"}.issubset(found))

    def test_relationship_claim_character_sources_ignore_other_workbench_refs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest("character-a")
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            current_source = json.loads(scene_artifact_document(payload, digest))["character_sources"][0]
            ledger = {
                "schema_version": 1,
                "relationships": [],
                "relationship_claim_records": [
                    {
                        "id": "claim-shared",
                        "from_character": "character-a",
                        "to_character": "character-b",
                        "claim": "A shared claim with separately scoped origins.",
                        "character_sources": [
                            current_source,
                            {
                                "character_id": "character-b",
                                "package_context_id": "package-character-b",
                                "source_refs": ["life-path:other-path/other-node"],
                            },
                        ],
                    }
                ],
                "common_ground_propositions": [],
                "second_order_beliefs": [],
                "shared_event_registry": [],
                "shared_memory_contracts": [],
            }
            enable_compilation(root, payload, digest, {"relationship-ledger.yaml": json.dumps(ledger, ensure_ascii=False)})
            payload["compiled_runtime"]["artifact_files"][0]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            self.assertEqual(audit_file(write_manifest(root, payload), require_locked=True), [])

    def test_relationship_participant_requires_its_own_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest("character-a")
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            payload["deep_biography"]["relationship_ledger_file"] = "relationship-ledger.yaml"
            ledger = {
                "schema_version": 1,
                "relationships": [],
                "relationship_claim_records": [
                    {
                        "id": "claim-missing-a",
                        "from_character": "character-a",
                        "to_character": "character-b",
                        "character_sources": [
                            {
                                "character_id": "character-b",
                                "package_context_id": "package-character-b",
                                "source_refs": ["life-path:path-a/node-1"],
                            }
                        ],
                    }
                ],
                "common_ground_propositions": [],
                "second_order_beliefs": [],
                "shared_event_registry": [],
                "shared_memory_contracts": [],
            }
            enable_compilation(root, payload, digest, {"relationship-ledger.yaml": json.dumps(ledger, ensure_ascii=False)})
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("relationship-participant-source-mismatch", found)

    def test_scene_participants_require_character_source_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest("character-a")
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            current_source = json.loads(scene_artifact_document(payload, digest))["character_sources"][0]
            document = {
                "schema_version": 1,
                "character_sources": [current_source],
                "scene": {"id": "scene-two"},
                "characters": [{"id": "character-a"}, {"id": "character-b"}],
                "character_runtime_scopes": [{"character_id": "character-a"}, {"character_id": "character-b"}],
            }
            enable_compilation(root, payload, digest, {"scene-contract.yaml": json.dumps(document, ensure_ascii=False)})
            payload["compiled_runtime"]["artifact_files"][0]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["formal_scene_compilation"] = True
            set_outline_review(root, payload)
            self.assertIn(
                "missing-participant-character-source",
                codes(audit_file(write_manifest(root, payload), require_locked=True)),
            )

    def test_multi_character_scene_requires_current_package_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            content = json.loads(scene_artifact_document(payload, digest))
            content["character_sources"][0]["package_context_id"] = "copied-from-another-package"
            enable_compilation(root, payload, digest, {"scene-contract.yaml": json.dumps(content, ensure_ascii=False)})
            found = codes(audit_file(write_manifest(root, payload), require_locked=True))
            self.assertIn("character-source-binding-mismatch", found)

    def test_legacy_structured_provenance_is_also_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            digest = write_and_approve(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
            content = "memories:\n  - source_branch_id: path-b\n    source_node_ids: [node-1]\n"
            enable_compilation(root, payload, digest, {"memories.yaml": content})
            self.assertIn("rejected-branch-reference", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_changed_body_invalidates_compiled_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            write_manifest(root, payload)
            write_biography(root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT + 1))
            self.assertIn("compiled-biography-hash-mismatch", codes(audit_file(manifest, require_locked=True)))

    def test_unresolved_outline_blocks_formal_scene_compilation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest)
            payload["compiled_runtime"]["formal_scene_compilation"] = True
            set_outline_review(
                root,
                payload,
                status="conflict_pending",
                conflicts=[
                    {
                        "id": "outline-conflict-1",
                        "description": "锁定人物机制与既定选择冲突",
                        "options_and_costs": ["补足压力并承担铺垫成本", "由作者修改情节"],
                        "status": "unresolved",
                        "author_decision": None,
                    }
                ],
            )
            write_manifest(root, payload)
            self.assertIn("formal-scene-blocked-by-outline-review", codes(audit_file(manifest, require_locked=True)))

    def test_scene_artifact_cannot_disable_outline_gate_with_false_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(root, payload, digest, {"main.fountain": "INT. ROOM - DAY\n\nA waits.\n"})
            payload["compiled_runtime"]["artifact_files"][0]["source_refs"] = ["life-path:path-a/node-1"]
            payload["compiled_runtime"]["source_refs"] = ["life-path:path-a/node-1"]
            write_manifest(root, payload)
            found = codes(audit_file(manifest, require_locked=True))
            self.assertIn("formal-scene-declaration-mismatch", found)
            self.assertIn("formal-scene-blocked-by-outline-review", found)

    def test_scene_content_mislabeled_other_structured_cannot_bypass_outline_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            content = json.dumps(
                {
                    "schema_version": 1,
                    "source_refs": ["life-path:path-a/node-1"],
                    "scene_id": "scene-1",
                    "turns": [],
                },
                ensure_ascii=False,
            )
            enable_compilation(root, payload, digest, {"runtime-artifact.yaml": content})
            write_manifest(root, payload)
            found = codes(audit_file(manifest, require_locked=True))
            self.assertIn("artifact-type-declaration-mismatch", found)
            self.assertIn("formal-scene-declaration-mismatch", found)
            self.assertIn("formal-scene-blocked-by-outline-review", found)

    def test_outline_file_change_invalidates_formal_scene_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, manifest, digest = self.ready_fixture(root)
            enable_compilation(
                root,
                payload,
                digest,
                {"main.fountain": "INT. ROOM - DAY\n\nA waits.\n\n/* life-path:path-a/node-1 */\n"},
            )
            payload["compiled_runtime"]["formal_scene_compilation"] = True
            outline_path = set_outline_review(root, payload)
            write_manifest(root, payload)
            self.assertEqual(audit_file(manifest, require_locked=True), [])
            outline_path.write_text("故事大纲版本二：未经重新审查的选择已经改变。\n", encoding="utf-8")
            found = codes(audit_file(manifest, require_locked=True))
            self.assertIn("outline-file-hash-mismatch", found)
            self.assertIn("formal-scene-blocked-by-outline-review", found)

    def test_light_tier_requires_author_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = locked_manifest()
            payload["deep_biography"].update(
                {
                    "mode": "light",
                    "status": "not_required",
                    "tier_author_decision": None,
                    "biography_revision": 0,
                    "biography_file": None,
                    "coverage_stages": [],
                    "shared_history_refs": [],
                }
            )
            self.assertIn("missing-tier-author-decision", codes(audit_file(write_manifest(root, payload), require_locked=True)))

    def test_biography_count_excludes_metadata_lists_tables_code_and_quotes(self) -> None:
        excluded = "不应计数" * 30
        body = "应计正文" * 25
        text = (
            f"---\nnotes: {excluded}\n---\n# {excluded}\n\n- {excluded}\n| {excluded} |\n"
            f"```yaml\nnotes: {excluded}\n```\n> {excluded}\n\n{body}\n"
        )
        self.assertEqual(biography_stats(text).total_han, len(body))


class SharedEventAuditTests(unittest.TestCase):
    def create_character(self, project: Path, character_id: str) -> tuple[dict, Path]:
        char_root = project / "02-characters" / character_id
        char_root.mkdir(parents=True)
        payload = locked_manifest(character_id)
        payload["deep_biography"]["shared_history_refs"] = ["life-path:path-a/node-1"]
        payload["deep_biography"]["shared_event_ids"] = ["shared-event-1"]
        payload["deep_biography"]["relationship_ledger_file"] = "02-characters/relationship-ledger.yaml"
        write_and_approve(char_root, payload, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT))
        return payload, write_manifest(char_root, payload)

    def ledger(self, project: Path, a: dict, b: dict) -> Path:
        shared_event = {
            "event_id": "shared-event-1",
            "event_revision": 1,
            "objective_core": "两名人物在同一时间和地点经历了同一件可核验事件",
            "time_window": {"start": "故事前第十年", "end": "故事前第十年", "precision": "approximate"},
            "participants": [
                {
                    "character_id": "character-a",
                    "workbench_file": "02-characters/character-a/life-path-workbench.yaml",
                    "branch_id": "path-a",
                    "life_path_lock_revision": 1,
                    "locked_fact_boundary_sha256": a["selection"]["locked_fact_boundary_sha256"],
                    "locked_candidate_sha256": a["selection"]["locked_candidate_sha256"],
                    "biography_revision": 1,
                    "approved_biography_sha256": a["deep_biography"]["author_approval"]["approved_body_sha256"],
                    "node_refs": ["life-path:path-a/node-1"],
                    "perception_version": "人物甲只看到事件的一部分",
                    "memory_version": "人物甲如今把它记成一次未完成的承诺",
                },
                {
                    "character_id": "character-b",
                    "workbench_file": "02-characters/character-b/life-path-workbench.yaml",
                    "branch_id": "path-a",
                    "life_path_lock_revision": 1,
                    "locked_fact_boundary_sha256": b["selection"]["locked_fact_boundary_sha256"],
                    "locked_candidate_sha256": b["selection"]["locked_candidate_sha256"],
                    "biography_revision": 1,
                    "approved_biography_sha256": b["deep_biography"]["author_approval"]["approved_body_sha256"],
                    "node_refs": ["life-path:path-a/node-1"],
                    "perception_version": "人物乙当时注意到另一处细节",
                    "memory_version": "人物乙如今把它记成一次共同承担",
                },
            ],
        }
        event_hash = shared_event_sha256(shared_event)
        shared_event["event_sha256"] = event_hash
        shared_event["author_approval"] = {
            "state": "approved",
            "approved_event_id": shared_event["event_id"],
            "approved_event_revision": shared_event["event_revision"],
            "approved_event_sha256": event_hash,
            "decision": author_decision("作者批准该版本跨人物客观共同事件"),
        }
        ledger = {
            "schema_version": 1,
            "relationships": [],
            "shared_event_registry": [shared_event],
            "shared_memory_contracts": [
                {"shared_memory_key": "shared-1", "shared_event_id": "shared-event-1", "participants": ["character-a", "character-b"]}
            ],
        }
        path = project / "02-characters" / "relationship-ledger.yaml"
        path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_shared_event_registry_accepts_different_memory_versions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            findings = audit_shared_event_registry(self.ledger(project, a, b))
            self.assertEqual(codes(findings), set())

    def test_declared_shared_event_must_exist_in_bound_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, a_manifest = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["shared_event_registry"] = []
            ledger["shared_memory_contracts"] = []
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

            self.assertIn(
                "declared-shared-event-not-in-registry",
                codes(audit_file(a_manifest, require_locked=True)),
            )
            a["deep_biography"]["shared_event_ids"] = "shared-event-1"
            write_manifest(a_manifest.parent, a)
            self.assertIn(
                "declared-shared-event-not-in-registry",
                codes(audit_file(a_manifest, require_locked=True)),
            )

    def test_declared_shared_ledger_can_be_a_provenance_checked_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, a_manifest = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            enable_compilation(
                project,
                a,
                a["deep_biography"]["author_approval"]["approved_body_sha256"],
                {"02-characters/relationship-ledger.yaml": ledger_path.read_text(encoding="utf-8")},
            )
            write_manifest(a_manifest.parent, a)
            self.assertEqual(audit_file(a_manifest, require_locked=True), [])

    def test_shared_event_objective_edit_invalidates_author_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["shared_event_registry"][0]["objective_core"] = "被原地改写但尚未重新获作者批准的客观核心"
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            found = codes(audit_shared_event_registry(ledger_path))
            self.assertIn("shared-event-hash-mismatch", found)
            self.assertIn("shared-event-approval-binding-mismatch", found)

    def test_shared_event_rejects_reversed_comparable_time_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            event = ledger["shared_event_registry"][0]
            event["time_window"] = {"start": "2020-02-01", "end": "2020-01-01", "precision": "day"}
            digest = shared_event_sha256(event)
            event["event_sha256"] = digest
            event["author_approval"]["approved_event_sha256"] = digest
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertIn("shared-event-time-reversed", codes(audit_shared_event_registry(ledger_path)))

    def test_shared_event_rejects_non_scalar_time_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            event = ledger["shared_event_registry"][0]
            event["time_window"]["start"] = {"year": 2020}
            digest = shared_event_sha256(event)
            event["event_sha256"] = digest
            event["author_approval"]["approved_event_sha256"] = digest
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertIn("invalid-shared-event-time", codes(audit_shared_event_registry(ledger_path)))

    def test_shared_event_rejects_nonfinite_numeric_time_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            base_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            cases = (
                ("nan-start", float("nan"), 0),
                ("positive-infinity-end", 0, float("inf")),
                ("negative-infinity-start", float("-inf"), 0),
            )
            for label, start, end in cases:
                with self.subTest(label=label):
                    ledger = copy.deepcopy(base_ledger)
                    event = ledger["shared_event_registry"][0]
                    event["time_window"] = {"start": start, "end": end, "precision": "number"}
                    digest = shared_event_sha256(event)
                    event["event_sha256"] = digest
                    event["author_approval"]["approved_event_sha256"] = digest
                    ledger_path.write_text(
                        yaml.safe_dump(ledger, allow_unicode=True, sort_keys=False),
                        encoding="utf-8",
                    )
                    self.assertIn(
                        "invalid-shared-event-time",
                        codes(audit_shared_event_registry(ledger_path)),
                    )

    def test_shared_event_registry_rejects_stale_participant_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["shared_event_registry"][0]["participants"][1]["biography_revision"] = 2
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertIn("shared-biography-revision-mismatch", codes(audit_shared_event_registry(ledger_path)))

    def test_shared_event_registry_binds_exact_approved_biography_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, _ = self.create_character(project, "character-a")
            b, b_manifest = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            b_root = b_manifest.parent
            write_and_approve(b_root, b, varied_body(FIXTURE_BIOGRAPHY_HAN_COUNT + 1))
            write_manifest(b_root, b)
            self.assertIn("shared-biography-hash-mismatch", codes(audit_shared_event_registry(ledger_path)))

    def test_workbench_automatically_audits_declared_shared_event_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            a, a_manifest = self.create_character(project, "character-a")
            b, _ = self.create_character(project, "character-b")
            ledger_path = self.ledger(project, a, b)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["shared_event_registry"][0]["participants"][1]["biography_revision"] = 2
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertIn("shared-biography-revision-mismatch", codes(audit_file(a_manifest, require_locked=True)))


if __name__ == "__main__":
    unittest.main()
