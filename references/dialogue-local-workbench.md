# Local dialogue workbench

This is a reusable local prototype for the meeting's extract → polish → reinsert loop. It performs file mechanics, not text generation. The current assistant can polish a packet; an external adapter is optional and must only receive material the user authorized sharing. Never report a CLI run as a separate model or human review.

For a naturalness repair, read [natural-dialogue-repair.md](natural-dialogue-repair.md) before preparing candidate text. Keep the incoming cue and downstream reply visible; an attractive isolated line may break the exchange.

Supported source: UTF-8 Fountain with explicit `@speaker` cues and dialogue separated from actions by blank lines. Parentheticals, dual dialogue and ambiguous cue blocks need deliberate normalization in a new draft first; do not silently guess ownership.

```text
python scripts/dialogue_roundtrip.py list source.fountain
python scripts/dialogue_roundtrip.py prepare source.fountain packet.json --turn turn-003 --turn turn-009
python scripts/dialogue_roundtrip.py merge source.fountain packet.json candidate.json revised.fountain
```

1. Select only the turns the current task permits. `prepare` binds source bytes, original speaker/text/span, and neighboring read-only context. Fill packet constraints with relevant facts, knowledge boundaries, approved character evidence and required next responses before polishing. Record who/model actually performed the wording pass separately.
2. Once the packet is complete, calculate its SHA-256. Return selected edits using this JSON shape:

```json
{"schema_version":1,"packet_sha256":"actual hash of complete packet bytes","edits":[{"id":"turn-003","speaker":"original speaker","text":"one paragraph of candidate dialogue"}]}
```

3. `merge` refuses a changed source or packet, reassigned speakers, unknown/duplicate IDs, ambiguous structural text and existing output paths. It replaces exact dialogue spans, preserving non-target content and source line endings; the source is never overwritten. It returns the entire screenplay, not isolated lines.
4. The `.review.json` sidecar records inputs, output hashes and a before/after map. Semantic fidelity, whole-scene reading and author acceptance remain pending. A meaningful but wrong line can pass structural checks: review facts, certainty, recipient, motivation, knowledge, response, spatial chronology and protected jokes in the entire scene.
5. Update downstream revisions only after the relevant acceptance. Never silently mix this draft into audio/video. For a formal fidelity-bound rewrite, retain the existing humanization and source-truth approval contracts.

This helper is not a fully automated multi-model plugin, GUI, installed cloud skill, or commercial product. It has no credentials, network calls, model fallback or autonomous approval. Byte-level tests prove mechanical behavior only.
