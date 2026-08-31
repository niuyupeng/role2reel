#!/usr/bin/env python3
"""Verify exact source, ledger, draft-body, and approval bindings.

This audit proves document identity and staleness only. It does not judge whether
the rewrite preserves meaning, whether the ledger is complete, or whether the
recorded approval was genuinely made by the named person.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the CLI dependency check
    yaml = None


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    location: str
    message: str


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_has_content(item) for item in value)
    return True


def _valid_revision(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, int):
        return value > 0
    return isinstance(value, str) and bool(value.strip())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frontmatter_and_body(text: str) -> tuple[dict[str, Any], str]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("humanized draft requires YAML frontmatter")
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
    if closing is None:
        raise ValueError("humanized draft frontmatter is unterminated")
    if yaml is None:
        raise ValueError("PyYAML is required; install requirements-dev.txt")
    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid draft frontmatter YAML: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("humanized draft frontmatter must be a mapping")
    return metadata, "\n".join(lines[closing + 1 :])


def draft_body_sha256(body: str) -> str:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_ledger(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise ValueError("PyYAML is required; install requirements-dev.txt")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid meaning-ledger YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("meaning ledger must be a mapping")
    return payload


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _declared_source_matches(declared: Any, source_path: Path, ledger_path: Path) -> bool:
    if not isinstance(declared, str) or not declared.strip():
        return False
    candidate = Path(declared.strip())
    if not candidate.is_absolute():
        candidate = ledger_path.parent / candidate
    return _path_key(candidate) == _path_key(source_path)


def _require_equal(
    findings: list[Finding],
    *,
    code: str,
    location: str,
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual != expected:
        findings.append(Finding(code, "error", location, message))


def audit_files(
    source_path: Path,
    ledger_path: Path,
    draft_path: Path,
    *,
    source_revision: Any,
) -> list[Finding]:
    """Audit the production-bound humanization chain using supplied real files."""
    findings: list[Finding] = []
    try:
        ledger_doc = _load_ledger(ledger_path)
        draft_metadata, draft_body = _frontmatter_and_body(draft_path.read_text(encoding="utf-8"))
        source_hash = file_sha256(source_path)
        ledger_hash = file_sha256(ledger_path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [Finding("input-error", "error", "input", str(exc))]

    ledger = ledger_doc.get("ledger")
    if not isinstance(ledger, dict):
        return [Finding("invalid-ledger", "error", "ledger", "ledger must be a mapping")]

    ledger_id = ledger.get("ledger_id")
    ledger_revision = ledger.get("revision")
    if not _has_content(ledger_id):
        findings.append(Finding("missing-ledger-id", "error", "ledger.ledger_id", "ledger_id is required"))
    if not _valid_revision(ledger_revision):
        findings.append(Finding("invalid-ledger-revision", "error", "ledger.revision", "ledger revision must be stable and non-empty"))

    source = ledger.get("source")
    if not isinstance(source, dict):
        findings.append(Finding("invalid-source-binding", "error", "ledger.source", "source must be a mapping"))
        source = {}
    if not _declared_source_matches(source.get("path"), source_path, ledger_path):
        findings.append(
            Finding(
                "source-path-mismatch",
                "error",
                "ledger.source.path",
                "Declared source path does not resolve to the supplied raw source relative to the ledger file.",
            )
        )
    _require_equal(
        findings,
        code="source-revision-mismatch",
        location="ledger.source.revision",
        actual=source.get("revision"),
        expected=source_revision,
        message="Ledger source revision does not match --source-revision.",
    )
    _require_equal(
        findings,
        code="source-hash-mismatch",
        location="ledger.source.sha256",
        actual=str(source.get("sha256") or "").casefold(),
        expected=source_hash.casefold(),
        message="Ledger source hash does not match the supplied raw source file.",
    )

    ledger_approval = ledger_doc.get("approval")
    if not isinstance(ledger_approval, dict):
        findings.append(Finding("ledger-approval-required", "error", "approval", "Exact ledger approval is required."))
        ledger_approval = {}
    if ledger_approval.get("status") != "approved":
        findings.append(Finding("ledger-approval-required", "error", "approval.status", "Ledger approval status must be approved."))
    ledger_approval_expected = {
        "approved_ledger_id": ledger_id,
        "approved_ledger_revision": ledger_revision,
        "approved_source_revision": source_revision,
        "approved_source_sha256": source_hash,
    }
    for field, expected in ledger_approval_expected.items():
        actual = ledger_approval.get(field)
        if field.endswith("sha256"):
            actual = str(actual or "").casefold()
            expected = str(expected).casefold()
        _require_equal(
            findings,
            code="ledger-approval-binding-mismatch",
            location=f"approval.{field}",
            actual=actual,
            expected=expected,
            message=f"Ledger approval is not bound to the current {field}.",
        )
    for field in ("decision_source", "decided_at"):
        if not _has_content(ledger_approval.get(field)):
            findings.append(Finding("incomplete-ledger-approval", "error", f"approval.{field}", f"Ledger approval requires {field}."))

    draft_id = draft_metadata.get("draft_id")
    draft_revision = draft_metadata.get("draft_revision")
    if not _has_content(draft_id):
        findings.append(Finding("missing-draft-id", "error", "draft.draft_id", "draft_id is required"))
    if not _valid_revision(draft_revision):
        findings.append(Finding("invalid-draft-revision", "error", "draft.draft_revision", "draft revision must be stable and non-empty"))

    if not _declared_source_matches(draft_metadata.get("source_path"), source_path, ledger_path):
        findings.append(Finding("draft-source-path-mismatch", "error", "draft.source_path", "Draft source path does not resolve to the supplied raw source."))
    draft_expected = {
        "meaning_ledger_id": ledger_id,
        "meaning_ledger_revision": ledger_revision,
        "meaning_ledger_sha256": ledger_hash,
        "source_revision": source_revision,
        "source_sha256": source_hash,
    }
    for field, expected in draft_expected.items():
        actual = draft_metadata.get(field)
        if field.endswith("sha256"):
            actual = str(actual or "").casefold()
            expected = str(expected).casefold()
        _require_equal(
            findings,
            code="draft-binding-mismatch",
            location=f"draft.{field}",
            actual=actual,
            expected=expected,
            message=f"Draft is not bound to the current {field}.",
        )

    body_hash = draft_body_sha256(draft_body)
    _require_equal(
        findings,
        code="draft-body-hash-mismatch",
        location="draft.body_sha256",
        actual=str(draft_metadata.get("body_sha256") or "").casefold(),
        expected=body_hash.casefold(),
        message="Draft body hash does not match the normalized Markdown body.",
    )
    if draft_metadata.get("status") != "approved":
        findings.append(Finding("draft-approval-required", "error", "draft.status", "Draft status must be approved for downstream use."))

    author_approval = draft_metadata.get("author_approval")
    if not isinstance(author_approval, dict):
        findings.append(Finding("draft-approval-required", "error", "draft.author_approval", "Exact draft approval is required."))
        author_approval = {}
    if author_approval.get("status") != "approved":
        findings.append(Finding("draft-approval-required", "error", "draft.author_approval.status", "Draft approval status must be approved."))
    approval_expected = {
        "approved_draft_id": draft_id,
        "approved_draft_revision": draft_revision,
        "approved_body_sha256": body_hash,
        "approved_meaning_ledger_id": ledger_id,
        "approved_meaning_ledger_revision": ledger_revision,
        "approved_meaning_ledger_sha256": ledger_hash,
        "approved_source_revision": source_revision,
        "approved_source_sha256": source_hash,
    }
    for field, expected in approval_expected.items():
        actual = author_approval.get(field)
        if field.endswith("sha256"):
            actual = str(actual or "").casefold()
            expected = str(expected).casefold()
        _require_equal(
            findings,
            code="draft-approval-binding-mismatch",
            location=f"draft.author_approval.{field}",
            actual=actual,
            expected=expected,
            message=f"Draft approval is not bound to the current {field}.",
        )
    for field in ("decision_source", "decided_at"):
        if not _has_content(author_approval.get(field)):
            findings.append(Finding("incomplete-draft-approval", "error", f"draft.author_approval.{field}", f"Draft approval requires {field}."))
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Actual raw source file")
    parser.add_argument("ledger", type=Path, help="Actual meaning-ledger YAML")
    parser.add_argument("draft", type=Path, help="Actual humanized-draft Markdown")
    parser.add_argument("--source-revision", required=True, help="Externally supplied stable source revision")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = audit_files(
        args.source,
        args.ledger,
        args.draft,
        source_revision=args.source_revision,
    )
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
        print(f"Errors: {sum(item.severity == 'error' for item in findings)}")
    else:
        print(
            "Humanization bindings valid. Meaning fidelity, ledger completeness, "
            "and the authenticity of recorded approval remain manual checks."
        )
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
