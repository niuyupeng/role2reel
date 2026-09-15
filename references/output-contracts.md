# Output contracts

Return the narrowest artifact that satisfies the request. Add intermediate ledgers only when they help collaboration, audit, or reuse.

## Deliverable boundary: screenplay versus storyboard

Choose content mode from the user's requested artifact, not from its file extension or the amount of detail requested:

- **剧本 / 完整剧本**: deliver a readable, playable screenplay. Do not substitute a shot table, second-by-second schedule, or generation prompts.
- **分镜 / 镜头表**: translate the screenplay into motivated shots, with framing, camera, action, dialogue/sound, and timing at the requested production depth. Do not turn every second or every line into a separate shot.
- **Word / Excel**: these choose the container only. A request for an Excel screenplay is still a screenplay; changing the container must not silently change the story or turn it into a storyboard.
- A total duration such as “两分钟以内” or “七分钟” is a pacing constraint, not permission to put timestamps throughout a screenplay. “详细” means sufficient dramatic and playable detail, not automatic per-second annotation.
- If both artifacts are requested, separate them into clearly identified documents or sheets. If the user explicitly asks for timed screenplay annotations, keep the timing in a separate companion layer where practical. Do not ask again when the latest request already clearly selects the mode.

## Reader-facing screenplay

Use a title followed by complete scenes. Each scene has a heading identifying interior/exterior, location, and dramatic time (such as 日、夜、连续), then observable action and necessary sound. Follow the author's supplied format for dialogue attribution; do not impose a separate character-cue line. Use short parentheticals only when needed to resolve delivery or action ambiguity. Preserve speaker ownership and narrative order.

For this author's Chinese screenplay deliveries, use the supplied left-aligned reference profile: title, scene headings, action, dialogue, and transition paragraphs share the same left text edge. Set paragraph alignment explicitly to LEFT, and left, right, first-line, and hanging indents to zero; remove inherited indentation, leading tabs, and padding spaces. Left-aligned text inside an indented block does not pass this requirement. Do not center the title or character names. Keep headings with following content and avoid stranded dialogue labels. This is the author's delivery convention, not a claim that every Chinese screenplay follows one national layout standard.

Use `【地点｜日或夜等剧情时间｜内或外】` scene labels when following this reference, preserving known time information rather than inventing day/night. If only alignment is being corrected, retain existing scene labels and dialogue wording. Dialogue may use `人物名：台词` on one line, or the reference's attributed prose with quoted speech when that style is explicitly requested or already present; do not mix in Hollywood-style centered cues and narrow dialogue columns. A screenshot demonstrating alignment does not authorize borrowing its story, adding its characters, or changing dialogue attribution style without need.

For Word delivery, check both rendered pages and effective paragraph/style properties: every screenplay paragraph must have the same left edge and no first-line indent under this profile. If a later author-supplied template explicitly requests another layout, follow that template instead. Keep this screenplay profile separate from storyboard tables and provider prompt contracts.

Without an explicit timed-script request, omit start/end seconds, per-second labels, shot numbers, lens/camera columns, and model-prompt syntax from the screenplay body. This does **not** mean removing action, environment, relevant props, silence, or sound: these are part of the screenplay, not inherently storyboard material. Ordinary punctuation, scene numbering, story-world clock readings, and plot-relevant countdowns are not production timestamps and should not be stripped indiscriminately.

For a format-only correction, preserve the established story and dialogue; do not silently rewrite them. Before delivery, check that the requested content mode and file type are both correct, the full text is present, speakers are preserved, and unwanted timing/shot metadata has not leaked into the body. Verify document pagination separately. Page count or a timing estimate does not prove the finished film's runtime.

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
- `life-paths/<branch-id>.md`: materialized biography of the locked causal path, with character/package identity, fact-boundary hash, branch, candidate hash, path-lock revision, biography revision, and status in frontmatter; a `deep` path is judged by causal and scene-useful coverage, with no default length minimum;
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

For a production-bound repair, pair the board with `assets/templates/source-truth-ledger.yaml` and `assets/templates/shot-readiness-review.yaml`. Run the source-truth and atomic-shot gates before dynamic timing; unresolved `SOURCE_MISMATCH`, `SPLIT_REQUIRED`, unapproved clusters, infeasible hard floors, ungrounded sound carriers, or missing `POST_COMPOSITE_TEXT` overlay plans remain review blockers.

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
