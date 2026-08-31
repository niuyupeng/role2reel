from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.audit_humanization import audit_files, draft_body_sha256, file_sha256


SOURCE_REVISION = "source-001"


def codes(findings) -> set[str]:
    return {item.code for item in findings}


def write_fixture(root: Path) -> tuple[Path, Path, Path]:
    source_dir = root / "source"
    humanized_dir = root / "01-humanized"
    source_dir.mkdir()
    humanized_dir.mkdir()
    source = source_dir / "raw.txt"
    ledger_path = humanized_dir / "meaning-ledger.yaml"
    draft_path = humanized_dir / "humanized-draft.md"
    source.write_text("也许他会来。\n", encoding="utf-8")
    source_hash = file_sha256(source)
    ledger = {
        "schema_version": 1,
        "ledger": {
            "ledger_id": "MEAN-001",
            "revision": "ledger-001",
            "source": {
                "path": "../source/raw.txt",
                "revision": SOURCE_REVISION,
                "sha256": source_hash,
                "supplied_by": "author",
            },
            "transformation_mode": "faithful_cleanup",
            "claims": [],
        },
        "approval": {
            "status": "approved",
            "decision_source": "author-review-001",
            "approved_ledger_id": "MEAN-001",
            "approved_ledger_revision": "ledger-001",
            "approved_source_revision": SOURCE_REVISION,
            "approved_source_sha256": source_hash,
            "decided_at": "2026-08-31T12:00:00Z",
        },
    }
    ledger_path.write_text(yaml.safe_dump(ledger, allow_unicode=True, sort_keys=False), encoding="utf-8")
    ledger_hash = file_sha256(ledger_path)
    body = "\n# Humanized draft\n\n也许，他会来。\n"
    body_hash = draft_body_sha256(body.strip("\n"))
    metadata = {
        "schema_version": 1,
        "draft_id": "DRAFT-001",
        "meaning_ledger_id": "MEAN-001",
        "meaning_ledger_revision": "ledger-001",
        "meaning_ledger_sha256": ledger_hash,
        "source_path": "../source/raw.txt",
        "source_revision": SOURCE_REVISION,
        "source_sha256": source_hash,
        "transformation_mode": "faithful_cleanup",
        "draft_revision": "draft-001",
        "status": "approved",
        "body_sha256": body_hash,
        "author_approval": {
            "status": "approved",
            "decision_source": "author-review-002",
            "approved_draft_id": "DRAFT-001",
            "approved_draft_revision": "draft-001",
            "approved_body_sha256": body_hash,
            "approved_meaning_ledger_id": "MEAN-001",
            "approved_meaning_ledger_revision": "ledger-001",
            "approved_meaning_ledger_sha256": ledger_hash,
            "approved_source_revision": SOURCE_REVISION,
            "approved_source_sha256": source_hash,
            "decided_at": "2026-08-31T12:01:00Z",
        },
    }
    rendered = "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---" + body
    draft_path.write_text(rendered, encoding="utf-8")
    return source, ledger_path, draft_path


class HumanizationAuditTests(unittest.TestCase):
    def test_exact_approved_chain_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, ledger, draft = write_fixture(Path(directory))
            self.assertEqual(audit_files(source, ledger, draft, source_revision=SOURCE_REVISION), [])

    def test_changed_source_invalidates_source_and_approval_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, ledger, draft = write_fixture(Path(directory))
            source.write_text("也许他不会来。\n", encoding="utf-8")
            found = codes(audit_files(source, ledger, draft, source_revision=SOURCE_REVISION))
            self.assertIn("source-hash-mismatch", found)
            self.assertIn("ledger-approval-binding-mismatch", found)
            self.assertIn("draft-binding-mismatch", found)
            self.assertIn("draft-approval-binding-mismatch", found)

    def test_changed_ledger_invalidates_draft_and_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, ledger, draft = write_fixture(Path(directory))
            payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
            payload["ledger"]["claims"].append({"claim_id": "C-1", "content": "new"})
            ledger.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            found = codes(audit_files(source, ledger, draft, source_revision=SOURCE_REVISION))
            self.assertIn("draft-binding-mismatch", found)
            self.assertIn("draft-approval-binding-mismatch", found)

    def test_changed_draft_body_invalidates_body_and_approval_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, ledger, draft = write_fixture(Path(directory))
            draft.write_text(draft.read_text(encoding="utf-8") + "又加了一句。\n", encoding="utf-8")
            found = codes(audit_files(source, ledger, draft, source_revision=SOURCE_REVISION))
            self.assertIn("draft-body-hash-mismatch", found)
            self.assertIn("draft-approval-binding-mismatch", found)

    def test_replayed_approval_and_wrong_source_path_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, ledger, draft = write_fixture(Path(directory))
            payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
            payload["ledger"]["source"]["path"] = "../source/another.txt"
            ledger.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            found = codes(audit_files(source, ledger, draft, source_revision=SOURCE_REVISION))
            self.assertIn("source-path-mismatch", found)
            self.assertIn("draft-binding-mismatch", found)


if __name__ == "__main__":
    unittest.main()
