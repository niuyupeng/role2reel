# Humanization without meaning drift

Humanization is not the addition of filler words, slang, or random verbal tics. It is a controlled transformation from raw expression into text that retains the speaker's thought while becoming clearer, speakable, or playable.

## Select the transformation mode

- **Faithful cleanup:** remove transcription noise and repair syntax while keeping structure and register close to the source.
- **Speakable monologue:** preserve the argument but shape breath, emphasis, self-correction, and oral rhythm.
- **Dramatic adaptation:** preserve the underlying claims and stakes while redistributing them across character action, subtext, and consequence.

Infer the narrowest mode that satisfies the request. Label a change as adaptation when it materially redistributes or dramatizes content.

Faithful cleanup and speakable-monologue modes must not invent temperament, jargon, verbal tics, biography, or certainty from a speaker's occupation, school, region, diagnosis, or status. Dramatic adaptation may use authored prehistory only when that material is already locked; otherwise preserve the source voice or label alternatives as candidate fiction.

## Build a meaning ledger

Before rewriting substantial material, record compactly:

| Field | Question |
|---|---|
| Claim | What is actually being asserted, questioned, or proposed? |
| Owner | Who holds or voices it? |
| Basis | Is it observation, memory, hearsay, inference, hope, or fear? |
| Certainty | Certain, likely, possible, doubtful, or unresolved? |
| Function | Inform, test, defend, accuse, persuade, bond, delay, or think aloud? |
| Must preserve | Which distinction, image, term, or emotional turn cannot be lost? |

Use this ledger as a fidelity check, not as content that must appear in the final answer.

For reusable or downstream production work, persist the ledger with
`assets/templates/meaning-ledger.yaml` and bind it to the exact source revision or
file hash. Save the corresponding rewrite with
`assets/templates/humanized-draft.md`. A storyboard or video task derived directly
from rough material must cite either that approved draft or an explicitly locked
scene meaning; otherwise stop at a reversible draft. The ledger is backstage
evidence, not an extra form the author must read before seeing useful text.

Resolve a relative `source.path` from the directory containing the meaning ledger.
Before downstream use, run
`python scripts/audit_humanization.py <raw-source> <meaning-ledger.yaml> <humanized-draft.md> --source-revision <revision>`.
The ledger approval binds its ID/revision to the source revision/hash; the draft
approval separately binds the draft ID/revision and normalized body hash to that
exact ledger file and source. This is a staleness and replay check, not a semantic
fidelity score or proof that the recorded approver acted.

Keep three layers separate:

1. **Source meaning:** what the supplied material actually says, including its
   uncertainty, ownership, chronology, and contradictions.
2. **Permitted transformation:** cleanup, speakable reshaping, or dramatic
   redistribution explicitly allowed by the author.
3. **Created fiction:** any new action, setting, causal link, or character history.
   Label it as an alternative until the author accepts it; never smuggle it into a
   fidelity rewrite.

## Classify roughness before editing

- Remove accidental ASR duplication, false starts with no semantic function, obvious filler loops, and formatting noise.
- Usually preserve self-repair when it reveals thought, risk, politeness, concealment, or changing certainty.
- Preserve repetition that escalates emotion, establishes rhythm, or changes the target of a claim.
- Compress repeated explanations of the same conclusion when they add no new basis or dramatic pressure.
- Preserve unresolved thinking as unresolved. Do not upgrade “也许” into a confident conclusion.
- Preserve ownership. Do not turn a quoted opinion into the narrator's belief or fuse different speakers into one voice.

## Make language human at the reasoning level

For defensive, over-explained or generic drafts, use [natural-dialogue-repair.md](natural-dialogue-repair.md) alongside this fidelity contract. Do not substitute a generic humanizer's defaults for the source voice or this task's permitted transformation.

Prefer:

- concrete evidence a speaker would notice;
- the speaker's own category system and comparisons;
- selective expression shaped by relationship and risk;
- meaningful omission, interruption, correction, or non-answer;
- sentence length and vocabulary consistent with the situation and person.

Avoid:

- decorative “嗯、啊、就是说” added after the fact;
- generic inspirational conclusions;
- symmetrical paragraphs assigned to different characters;
- replacing ambiguity with neat causal certainty;
- professional jargon the speaker has no reason to know;
- polishing every voice into the same fluent essayist.

## Fidelity pass

After rewriting, compare source and result:

1. Every material claim in the source is retained, intentionally omitted, or marked as changed.
2. No new fact appears as established truth.
3. Claim ownership and epistemic status remain intact.
4. Chronology and cause are not silently reversed.
5. The emotional direction survives even when wording changes.
6. The requested mode is respected: cleanup does not quietly become adaptation.
7. Any downstream scene, storyboard, or video task points to this exact source and
   approved-draft revision rather than an earlier or silently changed version.

When the source is ambiguous, preserve the ambiguity or surface one concise question. Do not solve it by invention.
