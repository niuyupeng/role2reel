# Source truth gate

Before timing or beautifying a storyboard, compare it with the actual screenplay, outline, approved dialogue source, and meaning ledger that own the story. The gate protects authorship; it does not require every visual detail to have been written upstream.

## What to compare

For every scene and shot, keep the stable upstream reference and record:

- source scene and shot or beat IDs;
- dialogue text, speaker, order, and any purposeful repetition;
- observable plot action and its cause/result;
- characters present and their knowledge boundary;
- the state change the shot is meant to hand to the next shot;
- any creative addition, omission, paraphrase, or unresolved ambiguity.

Use the actual source file and revision, not a copied hash-shaped note. Preserve the source wording beside an adapted wording when dialogue or action is changed. A close paraphrase can still alter a joke, a speaker, a fact, a power relation, or a later setup.

## Findings and release boundary

Use visible statuses such as `MATCHED`, `AUTHOR_ADDED`, `SOURCE_DRIFT`, `SOURCE_MISMATCH`, and `UNKNOWN_REQUIRES_REVIEW`. A speaker swap, changed plot fact, reversed action, or removed causal setup is a P0 mismatch until the author repairs or approves it. A meaningful paraphrase, missing reaction, or unexplained added detail is P1 drift. A deliberately new visual detail may be `AUTHOR_ADDED` when its creative provenance and approval are recorded.

Do not mark a production board locked while a P0 mismatch, unresolved source drift, or unapproved author addition remains. If the task is faithful cleanup or typo-only correction, preserve the narrow compatibility route and do not invent a screenplay rewrite.

This gate checks traceability and release readiness; it cannot decide whether a new image is artistically better. After the gate, read [atomic-shot-gate.md](atomic-shot-gate.md) before assigning seconds.
