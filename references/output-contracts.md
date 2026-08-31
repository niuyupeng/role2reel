# Output contracts

Return the narrowest artifact that satisfies the request. Add intermediate ledgers only when they help collaboration, audit, or reuse.

## Humanized text

Recommended order:

1. revised text;
2. material assumptions or ambiguities;
3. a short change note only when meaning, structure, or register changed materially.

Do not bury the rewritten text beneath process commentary.

For a persistent or downstream-bound rewrite, save `meaning-ledger.yaml` and
`humanized-draft.md`. Bind the draft to the exact source revision/hash and keep
created fiction separate from faithful transformation. The author-facing response
still leads with the revised text; the ledger remains a backstage fidelity record.

## Character package

Use persistent files only for recurring characters:

- `life-path-reading.md`: author-facing 命线反演 alternatives in `explore` mode; readable lives and the decision menu come before any production appendix, and the file is not canon by itself;
- `life-path-workbench.yaml`: stable character/package identity, versioned fact boundary, candidate branches, identity- and content-bound author selection/lock state, separate biography approval, exact compiled-file records, and conditional outline review;
- `life-paths/<branch-id>.md`: materialized biography of the locked causal path, with character/package identity, fact-boundary hash, branch, candidate hash, path-lock revision, biography revision, and status in frontmatter; a `deep` path defaults to at least 30,000 countable Han characters in Chinese prose;
- `character.yaml`: drives, contradictions, interpretation and decision rules;
- `cognitive-resources.yaml`: the comprehension library—knowledge status, beliefs, expertise, values, analogies, attention and attribution rules, and misconceptions;
- `speech-corpus.yaml`: the expression library—approved, provenance-bearing relationship/register/context/syntax/repair evidence retrieved only after private judgment and social objective exist;
- `memories.yaml`: objective event, subjective perception, belief, trigger, and current force;
- `relationship-ledger.yaml`: directional trust, debt, resentment, leverage, secrets, and boundaries;
- `speech-samples.md`: optional legacy or reader-friendly source evidence; it does not replace the structured corpus in production retrieval.

The relationship ledger also serves as the project-level shared-event registry when biographies overlap; each objective event has a revision, content hash, and exact-hash author approval, and binds every participant to a fact snapshot, locked candidate, path revision, exact approved biography body, causal nodes, and separate perception and memory versions.

Do not require this layer for a minor functional role or a narrow fidelity edit. For an underdetermined consequential character, present compact candidate outlines first. Let the author select or compatibly compose one route, resolve it, and explicitly lock that causal revision and content hash; then expand and mechanically validate its biography, obtain separate author approval for the exact biography revision and body hash, and only then compile the other files. Rejected candidates remain in the workbench and never become runtime facts.

Each `compiled_runtime.artifact_files` entry is a record, not a bare path. It carries the exact character and package identity, artifact type, exact file SHA-256, canonical path source refs, fact-boundary and candidate hashes, path-lock revision, and approved biography revision/body hash. Per-character structured assets repeat the identity and canonical refs internally. Shared structured artifacts from scene contract through video task carry one `character_sources[]` item per contributing package; a workbench audit validates its own item without pretending to validate the others. Relationship-ledger claims use the same per-record participant scoping when more than one life contributes. A compiled relationship ledger must match `deep_biography.relationship_ledger_file`, and shared-event bindings still receive the cross-workbench registry audit.

## Scene package

- `scene-contract.yaml`: dramatic question, facts, knowledge matrix, goals, secrets, start/end state;
- `turn-state.yaml`: backward-compatible surface turns plus `decision_traces` that separate comprehension retrieval, private interpretation, pragmatic attribution, inference/belief update, stance/objective, expression retrieval, suppression, and output;
- `beat-map.yaml`: state changes and turning points;
- `main.fountain`: playable screenplay.

Do not include all turn states in a reader-facing screenplay.

## Storyboard

For a compact review, use Markdown with:

| Shot | Time | Duty | Picture and performance | Camera | Dialogue / sound | Continuity |
|---|---:|---|---|---|---|---|

For production or machine checking, use `assets/templates/storyboard.yaml` as the authoritative nested contract and `storyboard.csv` as a flat review/export view. Bind exact meaning, scene, beat, and visual-bible revisions before shots. Declare `delivery_depth: concise` for an author-review board or `professional` for blocking, camera, performance, continuity, and handoff detail. Keep start and end seconds numeric when automated timing checks are needed.

Keep dialogue and sound separate. Every shot declares `dialogue.mode` as `spoken`, `nonverbal`, or `silent`, plus `state_in`, `state_out`, a handoff, and stable visual asset ID/revision references. Use `assets/templates/visual-bible.yaml` as the asset registry. For a modern board, run `scripts/audit_storyboard.py <board> --meaning <file> --scene <file> --beats <file> --visual-bible <file>` so the audit opens every bound document and compares its actual hash.

## Continuity package

Use `assets/templates/continuity.yaml` to bind the exact storyboard and visual-bible revisions, declare explicit identity/wardrobe/space/voice locks, authorize state changes, and reconcile shot handoffs. A lock category is either populated and `locked` or explicitly `not_applicable` with a reason; an empty ambiguous category is not a continuity decision. Use `scripts/audit_continuity.py` for structural checks.

## Video task and prompt

Create `assets/templates/video-task.yaml` before rendering provider prose. It binds storyboard, continuity, visual-bible, and asset-contract revisions; selects exactly one provider-neutral mode; records a continuous timeline; and carries the matching mode-specific contract. `asset-contract.yaml` denies all borrowing by default and grants only named properties to named targets and intervals.

Render a provider prompt in this order:

1. exact model and primary task mode;
2. verified technical constraints;
3. global identity, environment, camera, and sound locks;
4. continuous timeline;
5. reference-asset role contracts;
6. targeted continuity and leakage exclusions;
7. mode-specific seam, edit, bridge, or panel mapping;
8. intended final frame or handoff state.

Separate creative intent from provider-specific syntax so the prompt can be re-adapted.
Use `scripts/audit_video_task.py` before provider rendering. For a named provider, record a current capability check; bundled provider references contain routing logic, not frozen product limits.

## End-to-end delivery

When the user requests everything, deliver in layers:

```text
01-humanized/
02-characters/
03-scene/
04-screenplay/
05-storyboard/
06-continuity/
07-adapter/
08-calibration/
```

Use `scripts/init_project.py` to create this compatible workspace, including `01-humanized/`. Do not overwrite existing material unless the user explicitly requests it.

For staged deep evaluation, populate `assets/templates/staged-life-path-eval.yaml`; leave `behavior_pass: false` until real files and runs exist, then use `scripts/audit_staged_eval.py` to check the completed record before making any deterministic evidence claim.
