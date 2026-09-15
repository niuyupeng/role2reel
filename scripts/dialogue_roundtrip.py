"""Local Fountain dialogue packets and revision-safe draft reintegration; no model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def turns(text: str) -> list[dict]:
    # Deliberately narrow: explicit @speaker + one or more dialogue lines.
    # Reject ambiguous Fountain instead of guessing speaker/parenthetical ownership.
    result = []
    pattern = re.compile(r"(?m)^@([^\r\n]+)\r?\n([^\r\n]+(?:\r?\n[^\r\n]+)*)")
    for match in pattern.finditer(text):
        speaker, body = match.group(1).strip(), match.group(2)
        if not speaker or any(line.startswith(("@", "(", "[[", "INT.", "EXT.")) for line in body.splitlines()):
            raise ValueError("Ambiguous dialogue block; normalize parentheticals/cues before extraction")
        result.append({"id": f"turn-{len(result)+1:03d}", "speaker": speaker,
                       "original": body, "start": match.start(2), "end": match.end(2)})
    if not result:
        raise ValueError("No explicit @speaker dialogue found")
    return result


def new_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def prepare(source: Path, output: Path, allowed_ids: list[str]) -> dict:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    extracted = turns(text)
    known = {turn["id"] for turn in extracted}
    if not allowed_ids or len(allowed_ids) != len(set(allowed_ids)) or not set(allowed_ids) <= known:
        raise ValueError("Provide unique existing editable turn IDs; use list first")
    packet = {"schema_version": 1, "status": "draft_handoff",
              "source": str(source.resolve()), "source_sha256": digest(raw),
              "allowed_turn_ids": allowed_ids, "turns": [],
              "constraints": {"protected_facts": [], "character_evidence": [],
                              "knowledge_limits": [], "required_next_response": [],
                              "semantic_review": "pending"},
              "adapter": {"mode": "manual_or_current_assistant", "external_execution": "not_run"}}
    for turn in extracted:
        if turn["id"] in allowed_ids:
            packet["turns"].append({**turn,
                "context_before_readonly": text[max(0, turn["start"]-350):turn["start"]],
                "context_after_readonly": text[turn["end"]:turn["end"]+350]})
    new_json(output, packet)
    return packet


def merge(source: Path, packet_path: Path, candidate_path: Path, output: Path) -> dict:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    packet_bytes = packet_path.read_bytes()
    packet = json.loads(packet_bytes)
    candidate_bytes = candidate_path.read_bytes()
    candidate = json.loads(candidate_bytes)
    if packet.get("schema_version") != 1 or candidate.get("schema_version") != 1:
        raise ValueError("Unsupported schema")
    if str(source.resolve()) != packet.get("source") or digest(raw) != packet.get("source_sha256"):
        raise ValueError("Stale or different source: rebase before merging")
    if candidate.get("packet_sha256") != digest(packet_bytes):
        raise ValueError("Candidate is bound to a different/changed packet")
    actual = {turn["id"]: turn for turn in turns(text)}
    allowed = packet.get("allowed_turn_ids", [])
    if not allowed or len(allowed) != len(set(allowed)) or not set(allowed) <= actual.keys():
        raise ValueError("Invalid editable scope")
    supplied = packet.get("turns", [])
    if [t.get("id") for t in supplied] != [t for t in actual if t in allowed]:
        raise ValueError("Packet turns/scope disagree")
    for recorded in supplied:
        current = actual[recorded["id"]]
        if any(recorded.get(k) != current[k] for k in ("speaker", "original", "start", "end")):
            raise ValueError("Packet speaker/text/span changed")
    edits = candidate.get("edits")
    if not isinstance(edits, list) or not edits:
        raise ValueError("Candidate needs selected edits")
    seen, changes = set(), []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"id", "speaker", "text"}:
            raise ValueError("Edits accept only id, fixed speaker, text")
        key, replacement = edit["id"], edit["text"]
        if key not in allowed or key in seen:
            raise ValueError("Duplicate or out-of-scope turn")
        turn = actual[key]
        if edit["speaker"] != turn["speaker"]:
            raise ValueError("Speaker reassignment is not dialogue polishing")
        if (not isinstance(replacement, str) or not replacement.strip()
                or any(char in replacement for char in "\r\n\x00")
                or replacement.startswith(("@", "[[", "/*", "(", ">", "#"))):
            raise ValueError("Use plain single-paragraph dialogue; structural edits require a separate rewrite")
        seen.add(key)
        changes.append({**turn, "replacement": replacement})
    merged = text
    for change in sorted(changes, key=lambda item: item["start"], reverse=True):
        merged = merged[:change["start"]] + change["replacement"] + merged[change["end"]:]
    report_path = output.with_suffix(output.suffix + ".review.json")
    protected_paths = {p.resolve() for p in (source, packet_path, candidate_path)}
    if (output.resolve() in protected_paths or report_path.resolve() in protected_paths
            or output.exists() or report_path.exists()):
        raise ValueError("Output/report must be new files, never an input or existing version")
    encoded = merged.encode("utf-8")
    report = {"schema_version": 1, "status": "merged_draft_not_approved",
              "source_sha256": digest(raw), "packet_sha256": digest(packet_bytes),
              "candidate_sha256": digest(candidate_bytes), "output_sha256": digest(encoded),
              "changes": [{"id": c["id"], "speaker": c["speaker"],
                           "before": c["original"], "after": c["replacement"]} for c in changes],
              "non_target_content": "preserved_by_exact_span_replacement",
              "review": {"meaning_and_knowledge": "pending", "whole_scene": "pending",
                         "read_aloud": "pending", "author_acceptance": "pending"},
              "downstream_action": "Recheck existing scene/shot/audio bindings; no downstream files changed"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(encoded)
    new_json(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("source", type=Path)
    prep = sub.add_parser("prepare")
    prep.add_argument("source", type=Path)
    prep.add_argument("output", type=Path)
    prep.add_argument("--turn", action="append", required=True)
    reintegrate = sub.add_parser("merge")
    for name in ("source", "packet", "candidate", "output"):
        reintegrate.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "list":
            result = turns(args.source.read_bytes().decode("utf-8"))
        elif args.command == "prepare":
            result = prepare(args.source, args.output, args.turn)
        else:
            result = merge(args.source, args.packet, args.candidate, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
